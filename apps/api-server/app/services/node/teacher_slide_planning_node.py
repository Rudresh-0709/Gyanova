import json
from typing import Any, Dict, List, Optional, Set, Tuple

try:
    from app.services.llm.model_loader import load_openai
except ImportError:
    from ..llm.model_loader import load_openai

try:
    from app.services.fact_retrieval import format_for_llm, retrieve_facts
except ImportError:
    try:
        from ..fact_retrieval import format_for_llm, retrieve_facts
    except ImportError:
        format_for_llm = None
        retrieve_facts = None


VALID_INTENTS = {"introduce", "explain", "teach", "compare", "demo", "prove", "summarize"}
VALID_SCOPES = {"foundation", "mechanism", "comparison", "application", "reinforcement"}
VALID_DENSITIES = {"ultra_sparse", "sparse", "balanced", "standard", "dense", "super_dense"}


def _to_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return bool(value)
    text = str(value).strip().lower()
    if text in {"true", "yes", "1", "y"}:
        return True
    if text in {"false", "no", "0", "n"}:
        return False
    return default


def _detect_subject_domain(topic: str, subtopic_name: str) -> str:
    text = f"{topic} {subtopic_name}".lower()

    math_keys = {
        "algebra", "calculus", "geometry", "trigonometry", "equation", "integral",
        "derivative", "matrix", "probability", "statistics", "theorem", "formula",
    }
    science_keys = {
        "physics", "chemistry", "biology", "atom", "molecule", "cell", "energy",
        "force", "reaction", "ecosystem", "genetics", "electricity", "science",
    }
    history_keys = {
        "history", "civilization", "empire", "war", "revolution", "timeline", "era",
        "dynasty", "colonial", "independence", "constitution", "treaty",
    }
    language_keys = {
        "grammar", "vocabulary", "literature", "poetry", "language", "essay", "prose",
        "phonetics", "syntax", "semantics", "comprehension",
    }

    if any(k in text for k in math_keys):
        return "math"
    if any(k in text for k in science_keys):
        return "science"
    if any(k in text for k in history_keys):
        return "history"
    if any(k in text for k in language_keys):
        return "language"
    return "general"


def _collect_prior_coverage(plans: Dict[str, Any], current_sub_id: str) -> List[str]:
    prior: List[str] = []
    for sub_id, entry in plans.items():
        if sub_id == current_sub_id:
            continue
        if not isinstance(entry, list):
            continue

        for slide in entry:
            if not isinstance(slide, dict):
                continue

            if "_teacher_blueprint" in slide and isinstance(slide.get("_teacher_blueprint"), list):
                for ts in slide["_teacher_blueprint"]:
                    if not isinstance(ts, dict):
                        continue
                    title = str(ts.get("title", "")).strip()
                    objective = str(ts.get("objective", "")).strip()
                    must_cover = _to_list(ts.get("must_cover"))
                    chunks = [x for x in [title, objective, ", ".join(must_cover[:3])] if x]
                    if chunks:
                        prior.append(" | ".join(chunks))
            else:
                title = str(slide.get("title", "")).strip()
                goal = str(slide.get("goal", "")).strip()
                chunks = [x for x in [title, goal] if x]
                if chunks:
                    prior.append(" | ".join(chunks))

    return prior[:18]


def _should_research(
    subtopic_name: str,
    domain: str,
    learning_depth: str,
    difficulty: str,
    prior_coverage: List[str],
    state: Dict[str, Any],
) -> bool:
    if _to_bool(state.get("force_teacher_research"), default=False):
        return True

    ld = str(learning_depth).strip().lower()
    diff = str(difficulty).strip().lower()
    has_overlap_risk = len(prior_coverage) > 0

    if domain in {"math", "science", "history"}:
        return True
    if diff in {"intermediate", "advanced"}:
        return True
    if ld in {"detailed", "normal"} and has_overlap_risk:
        return True

    tokens = len(subtopic_name.split())
    if tokens >= 4:
        return True

    return False


def _build_research_query(
    topic: str,
    subtopic_name: str,
    domain: str,
    difficulty: str,
    learning_depth: str,
) -> str:
    domain_hint_map = {
        "math": "definitions, prerequisite concepts, formulas, worked examples, common mistakes",
        "science": "definitions, mechanism/process, scientific laws, examples, common misconceptions",
        "history": "timeline anchors, causes/effects, key events, evidence-backed facts, misconceptions",
        "language": "definitions, rules, examples, exceptions, common mistakes",
        "general": "core concepts, mechanisms, practical examples, common misconceptions",
    }
    hint = domain_hint_map.get(domain, domain_hint_map["general"])

    return (
        f"Create curriculum-ready notes for subtopic '{subtopic_name}' within topic '{topic}'. "
        f"Difficulty: {difficulty}. Learning depth: {learning_depth}. "
        f"Need: {hint}. Include what is essential vs optional and avoid overlap with adjacent subtopics."
    )


def _compact_research_for_prompt(result: Any) -> Tuple[str, List[str], str]:
    if not result or not getattr(result, "success", False):
        return "", [], "low"

    confidence = str(getattr(result, "confidence", "medium") or "medium").strip().lower()
    data = getattr(result, "data", {}) or {}
    evidence: List[str] = []

    if isinstance(data, dict):
        primary = data.get("primary") if isinstance(data.get("primary"), dict) else None
        synthesis = data.get("synthesis") if isinstance(data.get("synthesis"), dict) else None

        if primary:
            p_title = str(primary.get("title", "")).strip()
            p_url = str(primary.get("url", "")).strip()
            if p_title or p_url:
                evidence.append(f"Wikipedia: {p_title} {p_url}".strip())

        if synthesis:
            for r in synthesis.get("results", [])[:5]:
                if not isinstance(r, dict):
                    continue
                title = str(r.get("title", "")).strip()
                url = str(r.get("url", "")).strip()
                if title or url:
                    evidence.append(f"{title} {url}".strip())
        elif "results" in data:
            for r in data.get("results", [])[:5]:
                if not isinstance(r, dict):
                    continue
                title = str(r.get("title", "")).strip()
                url = str(r.get("url", "")).strip()
                if title or url:
                    evidence.append(f"{title} {url}".strip())
        elif data.get("url"):
            evidence.append(str(data.get("url", "")).strip())

    formatted = ""
    if format_for_llm:
        try:
            formatted = format_for_llm(result)
        except Exception:
            formatted = ""

    compact = "\n".join([line for line in formatted.splitlines() if line.strip()][:18]).strip()
    return compact, evidence[:8], confidence


def _infer_high_end_image_required(domain: str, coverage_scope: str, teaching_intent: str) -> bool:
    if domain in {"science", "history"} and coverage_scope in {"mechanism", "application", "comparison"}:
        return True
    if domain == "math" and teaching_intent in {"compare", "prove", "demo"}:
        return True
    return False


def _enforce_domain_requirements(slides: List[Dict[str, Any]], domain: str) -> List[Dict[str, Any]]:
    if not slides:
        return slides

    has_example = any(_to_bool(s.get("example_slide_candidate"), default=False) for s in slides)
    if not has_example:
        target = next((s for s in slides if s.get("coverage_scope") == "application"), slides[min(1, len(slides) - 1)])
        target["example_slide_candidate"] = True
        if "examples" not in target or not target["examples"]:
            target["examples"] = ["One practical student-friendly example."]

    if domain in {"math", "science"}:
        has_formula = any(_to_bool(s.get("formula_slide_candidate"), default=False) for s in slides)
        if not has_formula:
            target = next(
                (s for s in slides if s.get("coverage_scope") in {"mechanism", "comparison"}),
                slides[0],
            )
            target["formula_slide_candidate"] = True
            formulas = _to_list(target.get("formulas"))
            if not formulas:
                target["formulas"] = ["Include one key formula or symbolic relation when applicable."]

    return slides


def _clean_json(raw: str) -> str:
    return raw.replace("```json", "").replace("```", "").strip()


def _to_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    text = str(value).strip()
    return [text] if text else []


def _fallback_teacher_slides(subtopic_name: str) -> List[Dict[str, Any]]:
    return [
        {
            "title": f"{subtopic_name}: Core Idea",
            "objective": "Define the core idea and why it matters.",
            "teaching_intent": "explain",
            "must_cover": ["definition", "key term"],
            "key_facts": ["Introduce one foundational fact."],
            "formulas": [],
            "examples": ["One relatable real-world example."],
            "misconceptions": ["Common confusion and correction."],
            "assessment_prompt": "In one sentence, explain the core idea.",
            "coverage_scope": "foundation",
            "slide_density": "balanced",
            "high_end_image_required": False,
            "image_requirement_reason": "Concept-first foundation slide.",
            "formula_slide_candidate": False,
            "example_slide_candidate": False,
        },
        {
            "title": f"{subtopic_name}: How It Works",
            "objective": "Explain the mechanism or process clearly.",
            "teaching_intent": "teach",
            "must_cover": ["mechanism", "step order"],
            "key_facts": ["Important causal relationship."],
            "formulas": [],
            "examples": ["A simple worked example."],
            "misconceptions": ["Order-of-steps confusion."],
            "assessment_prompt": "What happens first and why?",
            "coverage_scope": "mechanism",
            "slide_density": "standard",
            "high_end_image_required": True,
            "image_requirement_reason": "Mechanism understanding benefits from strong visual support.",
            "formula_slide_candidate": False,
            "example_slide_candidate": False,
        },
        {
            "title": f"{subtopic_name}: Applied Example",
            "objective": "Apply the concept to a practical scenario.",
            "teaching_intent": "demo",
            "must_cover": ["application", "decision rule"],
            "key_facts": ["Practical condition or rule of thumb."],
            "formulas": [],
            "examples": ["A contextual scenario from daily life."],
            "misconceptions": ["Overgeneralization in application."],
            "assessment_prompt": "How would you apply this in a new context?",
            "coverage_scope": "application",
            "slide_density": "dense",
            "high_end_image_required": True,
            "image_requirement_reason": "Application slides benefit from realistic, high-quality visuals.",
            "formula_slide_candidate": False,
            "example_slide_candidate": True,
        },
        {
            "title": f"{subtopic_name}: Recap",
            "objective": "Summarize and reinforce retention.",
            "teaching_intent": "summarize",
            "must_cover": ["summary", "retention"],
            "key_facts": ["One high-value takeaway."],
            "formulas": [],
            "examples": [],
            "misconceptions": [],
            "assessment_prompt": "Name the most important takeaway and why.",
            "coverage_scope": "reinforcement",
            "slide_density": "sparse",
            "high_end_image_required": False,
            "image_requirement_reason": "Recap should stay focused and uncluttered.",
            "formula_slide_candidate": False,
            "example_slide_candidate": False,
        },
    ]


def teacher_slide_planning_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Create teacher-first semantic slide blueprints for one unplanned subtopic."""
    sub_topics = state.get("sub_topics", [])
    learning_depth = state.get("learning_depth", "Normal")
    difficulty = state.get("difficulty", "Beginner")
    topic = str(state.get("topic", "")).strip()

    plans = state.get("plans", {})

    next_subtopic = None
    for sub in sub_topics:
        sub_id = sub.get("id")
        if sub_id not in plans:
            next_subtopic = sub
            break

    if not next_subtopic:
        return {"plans": plans}

    sub_id = next_subtopic.get("id")
    subtopic_name = next_subtopic.get("name", "Subtopic")
    subject_domain = _detect_subject_domain(topic, subtopic_name)

    prior_coverage = _collect_prior_coverage(plans, current_sub_id=sub_id)
    should_research = _should_research(
        subtopic_name=subtopic_name,
        domain=subject_domain,
        learning_depth=str(learning_depth),
        difficulty=str(difficulty),
        prior_coverage=prior_coverage,
        state=state,
    )

    research_query = ""
    research_context_for_prompt = ""
    research_evidence: List[str] = []
    factual_confidence = "low"
    retrieval_layer = "none"

    if should_research and retrieve_facts is not None:
        research_query = _build_research_query(
            topic=topic,
            subtopic_name=subtopic_name,
            domain=subject_domain,
            difficulty=str(difficulty),
            learning_depth=str(learning_depth),
        )
        try:
            result = retrieve_facts(
                query=research_query,
                context={
                    "topic": topic,
                    "subtopic": subtopic_name,
                    "subject_domain": subject_domain,
                    "difficulty": difficulty,
                    "learning_depth": learning_depth,
                },
            )
            retrieval_layer = getattr(getattr(result, "layer_used", None), "value", "none")
            research_context_for_prompt, research_evidence, factual_confidence = _compact_research_for_prompt(result)
        except Exception:
            research_context_for_prompt = ""
            research_evidence = []
            factual_confidence = "low"
            retrieval_layer = "none"

    prior_coverage_text = "\n".join(f"- {item}" for item in prior_coverage[:12])
    if not prior_coverage_text:
        prior_coverage_text = "- No prior planned subtopic slides available."

    prompt = f"""
ROLE
You are a master teacher-curriculum architect building a rigorous, student-first blueprint for exactly ONE subtopic.

CONTEXT
Topic: {topic or 'General Topic'}
Subtopic: {subtopic_name}
Subject Domain: {subject_domain}
Difficulty: {difficulty}
Learning Depth: {learning_depth}
Research Enabled: {str(should_research).lower()}
Research Layer Used: {retrieval_layer}

PRIOR COVERAGE (avoid overlap with these prior planned slides)
{prior_coverage_text}

RESEARCH CONTEXT (if provided, ground decisions in this)
{research_context_for_prompt or 'No external research context used for this subtopic.'}

MISSION
Design a 4-8 slide teaching sequence that is pedagogically coherent, non-overlapping with prior subtopics, and curriculum-aligned.
Focus on instructional logic, depth, and student understanding; do not choose visual templates.

REASONING CHECKLIST
1. Identify the most important concepts, terms, mechanisms, and formulas for THIS subtopic.
2. Build progression: foundation -> mechanism -> example/application -> reinforcement.
3. Avoid overlap with prior subtopics; prioritize subtopic-specific depth and delta learning.
4. Include misconceptions where students typically get confused.
5. Keep facts accurate and concise.

QUALITY REQUIREMENTS
1. Each slide objective must be measurable and specific.
2. must_cover must list key concepts/fields for that slide.
3. key_facts must provide concrete factual statements.
4. formulas only when pedagogically necessary.
5. examples should be practical and student-friendly.
6. assessment_prompt must test that slide's objective.
7. Include at least one application-oriented slide and one misconception-oriented slide.
8. For math/science, decide if a formula-focused slide is needed and if a worked-example slide is needed.
9. Decide slide_density per slide and whether high-end dedicated image support is required.

ANTI-OVERLAP REQUIREMENT
- For each slide, explicitly set non_overlap_focus to explain what this slide contributes that prior subtopics did not.
- Do not repeat an already-covered objective unless this subtopic adds a different mechanism, constraint, or application context.

OUTPUT RULES
- Return JSON only (no prose, no markdown).
- Keep arrays compact and high-signal.
- If research context is available, include short source notes in research_evidence per slide.

Output JSON schema:
{{
    "slides": [
        {{
            "title": "...",
            "objective": "...",
            "teaching_intent": "introduce|explain|teach|compare|demo|prove|summarize",
            "must_cover": ["..."],
            "key_facts": ["..."],
            "formulas": ["..."],
            "examples": ["..."],
            "misconceptions": ["..."],
            "assessment_prompt": "...",
            "coverage_scope": "foundation|mechanism|comparison|application|reinforcement",
            "slide_density": "ultra_sparse|sparse|balanced|standard|dense|super_dense",
            "high_end_image_required": true,
            "image_requirement_reason": "short reason",
            "formula_slide_candidate": false,
            "example_slide_candidate": true,
            "non_overlap_focus": "what this slide uniquely adds",
            "research_evidence": ["optional source title or url"],
            "factual_confidence": "high|medium|low"
        }}
    ]
}}
"""

    slides = []
    try:
        llm = load_openai()
        resp = llm.invoke([{"role": "user", "content": prompt}])
        data = json.loads(_clean_json(resp.content))
        slides = data.get("slides", [])
    except Exception:
        slides = _fallback_teacher_slides(subtopic_name)

    normalized = []
    for i, slide in enumerate(slides):
        teaching_intent = str(slide.get("teaching_intent", "explain")).strip().lower()
        if teaching_intent not in VALID_INTENTS:
            teaching_intent = "explain"

        coverage_scope = str(slide.get("coverage_scope", "foundation")).strip().lower()
        if coverage_scope not in VALID_SCOPES:
            coverage_scope = "foundation"

        slide_density = str(slide.get("slide_density", "standard")).strip().lower()
        if slide_density not in VALID_DENSITIES:
            slide_density = "standard"

        formulas = _to_list(slide.get("formulas"))
        examples = _to_list(slide.get("examples"))
        high_end_required = _to_bool(
            slide.get("high_end_image_required"),
            default=_infer_high_end_image_required(subject_domain, coverage_scope, teaching_intent),
        )
        formula_candidate = _to_bool(
            slide.get("formula_slide_candidate"),
            default=bool(formulas) or (subject_domain in {"math", "science"} and coverage_scope in {"mechanism", "comparison"}),
        )
        example_candidate = _to_bool(
            slide.get("example_slide_candidate"),
            default=bool(examples) or coverage_scope == "application",
        )

        evidence = _to_list(slide.get("research_evidence"))
        if not evidence and research_evidence:
            evidence = research_evidence[:3]

        confidence = str(slide.get("factual_confidence", factual_confidence or "medium")).strip().lower()
        if confidence not in {"high", "medium", "low"}:
            confidence = "medium"

        normalized.append(
            {
                "slide_id": f"{sub_id}_t{i + 1}",
                "sequence_index": i,
                "title": str(slide.get("title", f"{subtopic_name} - Slide {i + 1}")).strip(),
                "objective": str(slide.get("objective", "Explain the concept clearly.")).strip(),
                "teaching_intent": teaching_intent,
                "must_cover": _to_list(slide.get("must_cover")),
                "key_facts": _to_list(slide.get("key_facts")),
                "formulas": formulas,
                "examples": examples,
                "misconceptions": _to_list(slide.get("misconceptions")),
                "assessment_prompt": str(slide.get("assessment_prompt", "")).strip(),
                "coverage_scope": coverage_scope,
                "subject_domain": subject_domain,
                "slide_density": slide_density,
                "high_end_image_required": high_end_required,
                "image_requirement_reason": str(
                    slide.get("image_requirement_reason", "Visual support selected based on pedagogy and complexity.")
                ).strip(),
                "formula_slide_candidate": formula_candidate,
                "example_slide_candidate": example_candidate,
                "non_overlap_focus": str(
                    slide.get("non_overlap_focus", "Adds new depth without repeating previous subtopics.")
                ).strip(),
                "research_evidence": evidence,
                "factual_confidence": confidence,
            }
        )

    if not normalized:
        normalized = _fallback_teacher_slides(subtopic_name)
        for i, slide in enumerate(normalized):
            slide["slide_id"] = f"{sub_id}_t{i + 1}"
            slide["sequence_index"] = i

    normalized = _enforce_domain_requirements(normalized, subject_domain)

    # Store temporary teacher draft in existing `plans` field so state keys remain unchanged.
    plans[sub_id] = [
        {
            "_teacher_blueprint": normalized,
            "_teacher_subtopic_name": subtopic_name,
            "_teacher_subject_domain": subject_domain,
            "_teacher_research_used": should_research,
            "_teacher_research_query": research_query,
            "_teacher_research_layer": retrieval_layer,
            "_teacher_research_confidence": factual_confidence,
            "_teacher_prior_coverage_hints": prior_coverage[:12],
        }
    ]
    return {"plans": plans}
