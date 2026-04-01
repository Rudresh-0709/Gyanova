import json
from typing import Any, Dict, List

try:
    from app.services.llm.model_loader import load_openai
except ImportError:
    from ..llm.model_loader import load_openai


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
        },
    ]


def teacher_slide_planning_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Create teacher-first semantic slide blueprints for one unplanned subtopic."""
    sub_topics = state.get("sub_topics", [])
    learning_depth = state.get("learning_depth", "Normal")
    difficulty = state.get("difficulty", "Beginner")

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

    prompt = f"""
You are a master teacher and curriculum planner building a teaching blueprint for exactly ONE subtopic.

Subtopic: {subtopic_name}
Difficulty: {difficulty}
Learning Depth: {learning_depth}

Your mission:
Design a high-quality teaching sequence of 4-8 slides that fully teaches this subtopic from a teacher perspective.
Focus on pedagogical substance only. Do not make visual/layout decisions.

How to think before writing slides:
1. Identify the most important concepts, terms, mechanisms, and formulas for THIS subtopic.
2. Decide a clear teaching progression (foundation -> mechanism -> example/application -> reinforcement).
3. Remove overlap: each slide should add unique learning value, not repeat earlier coverage.
4. Include common misconceptions where students typically get confused.
5. Keep facts accurate and concise.

Quality requirements:
1. Each slide objective must be measurable and specific.
2. must_cover should contain key concepts/fields to teach on that slide.
3. key_facts should contain concrete factual statements relevant to objective.
4. formulas should be included only when pedagogically necessary.
5. examples should be practical and student-friendly.
6. assessment_prompt should check understanding of that slide's objective.
7. Include at least one application-oriented slide and one misconception-oriented slide.

Output rules:
- Return JSON only (no prose, no markdown).
- Keep arrays compact and high-signal.

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
            "coverage_scope": "foundation|mechanism|comparison|application|reinforcement"
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
        normalized.append(
            {
                "slide_id": f"{sub_id}_t{i + 1}",
                "sequence_index": i,
                "title": str(slide.get("title", f"{subtopic_name} - Slide {i + 1}")).strip(),
                "objective": str(slide.get("objective", "Explain the concept clearly.")).strip(),
                "teaching_intent": str(slide.get("teaching_intent", "explain")).strip().lower(),
                "must_cover": _to_list(slide.get("must_cover")),
                "key_facts": _to_list(slide.get("key_facts")),
                "formulas": _to_list(slide.get("formulas")),
                "examples": _to_list(slide.get("examples")),
                "misconceptions": _to_list(slide.get("misconceptions")),
                "assessment_prompt": str(slide.get("assessment_prompt", "")).strip(),
                "coverage_scope": str(slide.get("coverage_scope", "foundation")).strip().lower(),
            }
        )

    if not normalized:
        normalized = _fallback_teacher_slides(subtopic_name)
        for i, slide in enumerate(normalized):
            slide["slide_id"] = f"{sub_id}_t{i + 1}"
            slide["sequence_index"] = i

    # Store temporary teacher draft in existing `plans` field so state keys remain unchanged.
    plans[sub_id] = [
        {
            "_teacher_blueprint": normalized,
            "_teacher_subtopic_name": subtopic_name,
        }
    ]
    return {"plans": plans}
