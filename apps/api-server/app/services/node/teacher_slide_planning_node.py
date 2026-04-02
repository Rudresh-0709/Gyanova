import json
from typing import Any, Dict, List, Tuple

try:
    from app.services.llm.model_loader import load_openai
except ImportError:
    from ..llm.model_loader import load_openai

try:
    from app.services.llm.model_loader import load_groq
except ImportError:
    try:
        from ..llm.model_loader import load_groq
    except ImportError:
        load_groq = None

try:
    from app.services.fact_retrieval import RetrievalLayer, format_for_llm, retrieve_facts
except ImportError:
    try:
        from ..fact_retrieval import RetrievalLayer, format_for_llm, retrieve_facts
    except ImportError:
        RetrievalLayer = None
        format_for_llm = None
        retrieve_facts = None


VALID_INTENTS = {"introduce", "explain", "teach", "compare", "demo", "prove", "summarize"}
VALID_SCOPES = {"foundation", "mechanism", "comparison", "application", "reinforcement"}
VALID_DENSITIES = {"ultra_sparse", "sparse", "balanced", "standard", "dense", "super_dense"}
VALID_FACT_RETRIEVERS = {"wiki", "tavily", "none"}


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


def _normalize_fact_retriever(value: Any) -> str:
    text = str(value or "none").strip().lower()
    if text in {"wikipedia", "wiki"}:
        return "wiki"
    if text in {"tavily"}:
        return "tavily"
    return "none"


def _confidence_rank(value: str) -> int:
    key = str(value or "low").strip().lower()
    if key == "high":
        return 3
    if key == "medium":
        return 2
    return 1


def _pick_best_confidence(values: List[str]) -> str:
    if not values:
        return "low"
    best = max(values, key=_confidence_rank)
    return best if best in {"high", "medium", "low"} else "low"


def _normalize_retrieval_plan(raw: Any) -> Dict[str, Any]:
    """Normalize retrieval-plan JSON from Groq planner LLM."""
    fallback = {
        "fact_check": "none",
        "queries": [],
        "reason": "No retrieval plan generated.",
    }
    if not isinstance(raw, dict):
        return fallback

    fact_check = _normalize_fact_retriever(raw.get("fact_check", "none"))
    reason = str(raw.get("reason", "")).strip() or "No reason provided."

    normalized_queries: List[Dict[str, str]] = []
    queries = raw.get("queries", [])
    if isinstance(queries, list):
        for q in queries[:2]:
            if not isinstance(q, dict):
                continue
            text = str(q.get("query", "")).strip()
            source = _normalize_fact_retriever(q.get("source", "none"))
            if text and source in {"wiki", "tavily"}:
                normalized_queries.append({"query": text, "source": source})

    if fact_check == "none":
        normalized_queries = []

    if fact_check in {"wiki", "tavily"} and not normalized_queries:
        normalized_queries = [{"query": "", "source": fact_check}]

    return {
        "fact_check": fact_check,
        "queries": normalized_queries,
        "reason": reason,
    }


def _plan_fact_retrieval_with_groq(
    topic: str,
    subtopic_name: str,
    domain: str,
    difficulty: str,
    learning_depth: str,
    should_research: bool,
) -> Dict[str, Any]:
    """
    Groq planner decides whether to retrieve and generates up to 2 short source-specific queries.
    Output schema:
    {
      fact_check: "none|wiki|tavily",
      queries: [{query: "...", source: "wiki|tavily"}],
      reason: "..."
    }
    """
    if not should_research:
        return {
            "fact_check": "none",
            "queries": [],
            "reason": "Research skipped by heuristic.",
        }

    if not load_groq:
        return {
            "fact_check": "wiki" if domain in {"history", "language", "general"} else "tavily",
            "queries": [
                {
                    "query": _build_research_query(topic, subtopic_name, domain, difficulty, learning_depth),
                    "source": "wiki" if domain in {"history", "language", "general"} else "tavily",
                }
            ],
            "reason": "Groq unavailable; fallback retrieval plan used.",
        }

    prompt = f"""
ROLE
You are a retrieval strategist for an educational slide planner.

GOAL
Given one subtopic, decide if factual retrieval is needed and produce at most two short search queries.

INPUT
Topic: {topic}
Subtopic: {subtopic_name}
Detected Domain: {domain}
Difficulty: {difficulty}
Learning Depth: {learning_depth}

RULES
1. If the subtopic is very generic and common-sense, set fact_check to "none".
2. Else choose one of: "wiki" or "tavily" as primary fact_check.
3. Generate 1-2 concise queries (max ~14 words each).
4. Each query must include a source field: wiki or tavily.
5. Prefer wiki for stable factual/historical/definition lookups.
6. Prefer tavily for multi-source synthesis or nuanced modern topics.

OUTPUT
Return JSON only:
{{
  "fact_check": "none|wiki|tavily",
  "queries": [
    {{"query": "...", "source": "wiki|tavily"}}
  ],
  "reason": "short reason"
}}
"""

    try:
        llm = load_groq()
        resp = llm.invoke([{"role": "user", "content": prompt}])
        raw = str(resp.content or "").replace("```json", "").replace("```", "").strip()
        plan = json.loads(raw)
        normalized = _normalize_retrieval_plan(plan)
        if normalized["fact_check"] in {"wiki", "tavily"} and normalized["queries"]:
            for q in normalized["queries"]:
                if not q.get("query"):
                    q["query"] = _build_research_query(topic, subtopic_name, domain, difficulty, learning_depth)
        return normalized
    except Exception:
        default_source = "wiki" if domain in {"history", "language", "general"} else "tavily"
        return {
            "fact_check": default_source,
            "queries": [
                {
                    "query": _build_research_query(topic, subtopic_name, domain, difficulty, learning_depth),
                    "source": default_source,
                }
            ],
            "reason": "Groq planning failed; fallback retrieval plan used.",
        }


def _retrieval_layer_from_source(source: str):
    if not RetrievalLayer:
        return None
    src = _normalize_fact_retriever(source)
    if src == "wiki":
        return RetrievalLayer.WIKIPEDIA
    if src == "tavily":
        return RetrievalLayer.TAVILY
    return None


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


def _should_research(
    subtopic_name: str,
    domain: str,
    learning_depth: str,
    difficulty: str,
    state: Dict[str, Any],
) -> bool:
    if _to_bool(state.get("force_teacher_research"), default=False):
        return True

    ld = str(learning_depth).strip().lower()
    diff = str(difficulty).strip().lower()
    if domain in {"math", "science", "history"}:
        return True
    if diff in {"intermediate", "advanced"}:
        return True
    if ld in {"detailed", "normal"}:
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
    search_focus_map = {
        "math": ["definition", "formula", "worked problem", "step by step"],
        "science": ["definition", "process", "mechanism", "key facts"],
        "history": ["timeline", "causes", "effects", "key events"],
        "language": ["definition", "rules", "structure", "core usage"],
        "general": ["definition", "core concept", "key facts", "overview"],
    }
    focus = search_focus_map.get(domain, search_focus_map["general"])
    search_terms = [topic, subtopic_name, domain, difficulty, learning_depth] + focus
    return " ".join(part for part in search_terms if part)


def _compact_research_for_prompt(result: Any) -> Tuple[str, List[str], str, str]:
    if not result or not getattr(result, "success", False):
        return "", [], "low", ""

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
    raw_text = formatted.strip()
    return compact, evidence[:8], confidence, raw_text


def _infer_high_end_image_required(domain: str, coverage_scope: str, teaching_intent: str) -> bool:
    if domain in {"science", "history"} and coverage_scope in {"mechanism", "application", "comparison"}:
        return True
    if domain == "math" and teaching_intent in {"compare", "prove", "demo"}:
        return True
    return False


def _enforce_domain_requirements(slides: List[Dict[str, Any]], domain: str) -> List[Dict[str, Any]]:
    if not slides:
        return slides

    has_example_candidate = any(_to_bool(s.get("example_slide_candidate"), default=False) for s in slides)
    if not has_example_candidate:
        target = next((s for s in slides if s.get("coverage_scope") == "application"), slides[min(1, len(slides) - 1)])
        target["example_slide_candidate"] = True

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
    refactor_instructions_map = state.get("coverage_regeneration_instructions", {})
    subtopic_refactor_instructions = refactor_instructions_map.get(sub_id, []) if isinstance(refactor_instructions_map, dict) else []
    is_refactor_mode = bool(subtopic_refactor_instructions)

    should_research = _should_research(
        subtopic_name=subtopic_name,
        domain=subject_domain,
        learning_depth=str(learning_depth),
        difficulty=str(difficulty),
        state=state,
    )

    research_query = ""
    research_plan_reason = ""
    research_context_for_prompt = ""
    research_evidence: List[str] = []
    research_raw_text = ""
    factual_confidence = "low"
    retrieval_layer = "none"
    fact_retriever = "none"

    retrieval_plan = _plan_fact_retrieval_with_groq(
        topic=topic,
        subtopic_name=subtopic_name,
        domain=subject_domain,
        difficulty=str(difficulty),
        learning_depth=str(learning_depth),
        should_research=should_research,
    )
    research_plan_reason = str(retrieval_plan.get("reason", "")).strip()

    confidence_values: List[str] = []
    layer_values: List[str] = []
    context_chunks: List[str] = []
    combined_evidence: List[str] = []
    raw_text_chunks: List[str] = []
    query_values: List[str] = []

    if retrieve_facts is not None:
        for q in retrieval_plan.get("queries", []):
            if not isinstance(q, dict):
                continue
            q_text = str(q.get("query", "")).strip()
            source = _normalize_fact_retriever(q.get("source", "none"))
            if not q_text or source == "none":
                continue

            query_values.append(f"[{source}] {q_text}")
            force_layer = _retrieval_layer_from_source(source)
            try:
                result = retrieve_facts(
                    query=q_text,
                    context={
                        "topic": topic,
                        "subtopic": subtopic_name,
                        "subject_domain": subject_domain,
                        "difficulty": difficulty,
                        "learning_depth": learning_depth,
                        "source": source,
                    },
                    force_layer=force_layer,
                )

                layer = getattr(getattr(result, "layer_used", None), "value", source)
                layer_values.append(str(layer))

                chunk, evidence, conf, raw_text = _compact_research_for_prompt(result)
                if chunk:
                    context_chunks.append(chunk)
                if evidence:
                    combined_evidence.extend(evidence)
                if raw_text:
                    raw_text_chunks.append(raw_text)
                confidence_values.append(conf)
            except Exception:
                continue

    if query_values:
        research_query = " || ".join(query_values)

    if context_chunks:
        research_context_for_prompt = "\n\n".join(context_chunks[:2]).strip()
    if combined_evidence:
        # de-duplicate while preserving order
        deduped: List[str] = []
        seen = set()
        for e in combined_evidence:
            if e not in seen:
                seen.add(e)
                deduped.append(e)
        research_evidence = deduped[:8]

    if raw_text_chunks:
        research_raw_text = "\n\n".join(raw_text_chunks).strip()

    factual_confidence = _pick_best_confidence(confidence_values)

    normalized_layers = [_normalize_fact_retriever(x) for x in layer_values]
    if "tavily" in normalized_layers:
        fact_retriever = "tavily"
        retrieval_layer = "tavily"
    elif "wiki" in normalized_layers:
        fact_retriever = "wiki"
        retrieval_layer = "wikipedia"
    else:
        fact_retriever = "none"
        retrieval_layer = "none"

    refactor_text = "\n".join(f"- {item}" for item in subtopic_refactor_instructions[:12])
    if not refactor_text:
        refactor_text = "- No regeneration instructions provided."

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
Retriever Plan Reason: {research_plan_reason or 'n/a'}

REFACTOR INSTRUCTIONS (only when regenerating overlap-marked slides)
{refactor_text}

RESEARCH CONTEXT (if provided, ground decisions in this)
{research_context_for_prompt or 'No external research context used for this subtopic.'}

SEARCH INTERPRETATION NOTE
The retrieval layer returns raw source snippets and summaries. Do not assume it provides structured curriculum output.
Use it only as factual evidence to decide slide scope, depth, and examples.

MODE
Refactor Mode: {str(is_refactor_mode).lower()}

MISSION
Design a 4-8 slide teaching sequence that is pedagogically coherent and curriculum-aligned for this subtopic only.
If Refactor Mode is true, regenerate the slide intent/coverage based on refactor instructions while still focusing only on this subtopic.
Do not choose visual templates.

DOMAIN CLASSIFICATION
- If the heuristic domain above is general or uncertain, infer the most likely domain inside this same response and set `subject_domain` to one of: math, science, history, language, general.
- Use that classified domain to decide when formulas, worked examples, diagrams, timelines, or rule-based explanation slides are needed.

REASONING CHECKLIST
1. Identify the most important concepts, terms, mechanisms, and formulas for THIS subtopic.
2. Build progression: foundation -> mechanism -> example/application -> reinforcement.
3. Keep facts accurate and concise.
4. In refactor mode, re-angle scope/objectives according to instructions.

QUALITY REQUIREMENTS
1. Each slide objective must be measurable and specific.
2. must_cover must list key concepts/fields for that slide.
3. key_facts must provide concrete factual statements.
4. formulas only when pedagogically necessary.
5. assessment_prompt must test that slide's objective.
6. Include at least one application-oriented slide.
7. For math/science, decide if a formula-focused slide is needed.
8. Decide slide_density per slide and whether high-end dedicated image support is required.

OUTPUT RULES
- Return JSON only (no prose, no markdown).
- Keep arrays compact and high-signal.
- If research context is available, include short source notes in research_evidence per slide.

Output JSON schema:
{{
    "subject_domain": "math|science|history|language|general",
    "slides": [
        {{
            "title": "...",
            "objective": "...",
            "teaching_intent": "introduce|explain|teach|compare|demo|prove|summarize",
            "must_cover": ["..."],
            "key_facts": ["..."],
            "formulas": ["..."],
            "assessment_prompt": "...",
            "coverage_scope": "foundation|mechanism|comparison|application|reinforcement",
            "slide_density": "ultra_sparse|sparse|balanced|standard|dense|super_dense",
            "high_end_image_required": true,
            "image_requirement_reason": "short reason",
            "formula_slide_candidate": false,
            "example_slide_candidate": true,
            "research_evidence": ["optional source title or url"],
            "factual_confidence": "high|medium|low"
        }}
    ]
}}
"""

    slides = []
    generated_subject_domain = subject_domain
    try:
        llm = load_openai()
        resp = llm.invoke([{"role": "user", "content": prompt}])
        data = json.loads(_clean_json(resp.content))
        generated_subject_domain = str(data.get("subject_domain", subject_domain)).strip().lower()
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
            default=coverage_scope == "application",
        )

        evidence = _to_list(slide.get("research_evidence"))
        if not evidence and research_evidence:
            evidence = research_evidence[:3]

        slide_raw_text = str(slide.get("research_raw_text", research_raw_text or "")).strip()

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
                "research_evidence": evidence,
                "research_raw_text": slide_raw_text,
                "factual_confidence": confidence,
            }
        )

    if not normalized:
        normalized = _fallback_teacher_slides(subtopic_name)
        for i, slide in enumerate(normalized):
            slide["slide_id"] = f"{sub_id}_t{i + 1}"
            slide["sequence_index"] = i

    normalized = _enforce_domain_requirements(normalized, subject_domain)

    prompt_domain = generated_subject_domain or subject_domain
    if prompt_domain not in {"math", "science", "history", "language", "general"}:
        prompt_domain = "general"

    if fact_retriever not in VALID_FACT_RETRIEVERS:
        fact_retriever = "none"

    # Store temporary teacher draft in existing `plans` field so state keys remain unchanged.
    plans[sub_id] = [
        {
            "_teacher_blueprint": normalized,
            "_teacher_subtopic_name": subtopic_name,
            "_teacher_subject_domain": prompt_domain,
            "_teacher_research_used": should_research,
            "_teacher_research_query": research_query,
            "_teacher_research_layer": retrieval_layer,
            "_teacher_fact_retriever": fact_retriever,
            "_teacher_research_raw_text": research_raw_text,
            "_teacher_research_confidence": factual_confidence,
            "_teacher_refactor_mode": is_refactor_mode,
            "_teacher_refactor_instruction_count": len(subtopic_refactor_instructions),
        }
    ]
    return {"plans": plans, "fact_retriever": fact_retriever, "teacher_research_raw_text": research_raw_text}
