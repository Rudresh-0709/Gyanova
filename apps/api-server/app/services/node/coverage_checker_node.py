import json
import os
from typing import Any, Dict, List, Set, Tuple

try:
    from app.services.llm.model_loader import load_groq
except ImportError:
    try:
        from ..llm.model_loader import load_groq
    except ImportError:
        load_groq = None

STOPWORDS = {
    "the", "and", "for", "with", "from", "that", "this", "into", "about", "topic",
    "subtopic", "what", "how", "why", "when", "where", "which", "their", "your",
    "lesson", "chapter", "section", "a", "an", "to", "of", "in", "on", "by", "is",
}


def _normalize_text(value: Any) -> str:
    text = str(value or "").lower()
    filtered = []
    for ch in text:
        if ch.isalnum() or ch.isspace():
            filtered.append(ch)
        else:
            filtered.append(" ")
    return " ".join("".join(filtered).split())


def _tokenize(value: Any) -> Set[str]:
    tokens = set()
    for token in _normalize_text(value).split():
        if len(token) > 2 and token not in STOPWORDS:
            tokens.add(token)
    return tokens


def _jaccard_score(left: Any, right: Any) -> float:
    left_tokens = _tokenize(left)
    right_tokens = _tokenize(right)
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)


def _slide_text(slide: Dict[str, Any]) -> str:
    title = str(slide.get("title", "")).strip()
    goal = str(slide.get("goal", slide.get("objective", ""))).strip()
    return " | ".join(part for part in [title, goal] if part)


def _as_slide_payload(subtopic_id: str, slide: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "subtopic_id": subtopic_id,
        "slide_id": str(slide.get("slide_id", "")),
        "title": str(slide.get("title", "")).strip(),
        "goal": str(slide.get("goal", slide.get("objective", ""))).strip(),
        "text": _slide_text(slide),
    }


def _llm_verify_overlaps_with_groq(
    latest_sub_id: str,
    latest_slides: List[Dict[str, Any]],
    prior_slides_pool: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    if not load_groq:
        return []
    if not os.getenv("GROQ_API_KEY"):
        return []

    if not latest_slides or not prior_slides_pool:
        return []

    prompt = f"""
You are a strict curriculum overlap auditor.

Task:
Compare latest-subtopic slides against prior-subtopic slides and detect semantic overlap/redundancy.
Mark overlap when slides teach substantially the same idea/outcome, even if wording differs.

Latest subtopic id: {latest_sub_id}

Latest slides JSON:
{json.dumps(latest_slides, ensure_ascii=True, indent=2)}

Prior slides JSON:
{json.dumps(prior_slides_pool, ensure_ascii=True, indent=2)}

Return JSON only in this format:
{{
  "overlaps": [
    {{
      "latest_slide_id": "...",
      "prior_subtopic_id": "...",
      "prior_slide_id": "...",
      "score": 0.0,
      "reason": "short reason"
    }}
  ]
}}

Scoring guidance:
- 0.0 to 1.0 confidence
- Use >= 0.6 for clear overlaps
"""

    try:
        llm = load_groq()
        resp = llm.invoke([{"role": "user", "content": prompt}])
        raw = str(resp.content or "").replace("```json", "").replace("```", "").strip()
        data = json.loads(raw)
        overlaps = data.get("overlaps", [])
        clean: List[Dict[str, Any]] = []
        for item in overlaps:
            if not isinstance(item, dict):
                continue
            latest_slide_id = str(item.get("latest_slide_id", "")).strip()
            prior_subtopic_id = str(item.get("prior_subtopic_id", "")).strip()
            prior_slide_id = str(item.get("prior_slide_id", "")).strip()
            reason = str(item.get("reason", "semantic overlap")).strip()
            try:
                score = float(item.get("score", 0.0))
            except Exception:
                score = 0.0
            if latest_slide_id and prior_subtopic_id and prior_slide_id and score >= 0.6:
                clean.append(
                    {
                        "latest_slide_id": latest_slide_id,
                        "prior_subtopic_id": prior_subtopic_id,
                        "prior_slide_id": prior_slide_id,
                        "score": round(score, 3),
                        "reason": reason,
                    }
                )
        return clean
    except Exception:
        return []


def _latest_planned_subtopic(sub_topics: List[Dict[str, Any]], plans: Dict[str, Any]) -> str:
    latest = ""
    for sub in sub_topics:
        sub_id = sub.get("id")
        if sub_id in plans and isinstance(plans.get(sub_id), list) and plans.get(sub_id):
            latest = sub_id
    return latest


def coverage_checker_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Check overlap only after at least two subtopics have plans and request targeted regeneration."""
    sub_topics = state.get("sub_topics", [])
    plans = dict(state.get("plans", {}))

    planned_sub_ids = [
        sub.get("id")
        for sub in sub_topics
        if sub.get("id") in plans and isinstance(plans.get(sub.get("id")), list) and plans.get(sub.get("id"))
    ]

    if len(planned_sub_ids) < 2:
        return {
            "plans": plans,
            "coverage_overlap_report": [],
        }

    latest_sub_id = _latest_planned_subtopic(sub_topics, plans)
    if not latest_sub_id:
        return {
            "plans": plans,
            "coverage_overlap_report": [],
        }

    latest_slides = plans.get(latest_sub_id, [])
    if not isinstance(latest_slides, list) or not latest_slides:
        return {
            "plans": plans,
            "coverage_overlap_report": [],
        }

    overlap_report: List[Dict[str, Any]] = []
    instructions: List[str] = []

    latest_payload: List[Dict[str, Any]] = []
    prior_payload: List[Dict[str, Any]] = []

    for prior_sub_id in planned_sub_ids:
        if prior_sub_id == latest_sub_id:
            continue
        prior_slides = plans.get(prior_sub_id, [])
        if not isinstance(prior_slides, list):
            continue

        for prior_slide in prior_slides:
            if isinstance(prior_slide, dict):
                prior_payload.append(_as_slide_payload(prior_sub_id, prior_slide))

        for latest_slide in latest_slides:
            if not isinstance(latest_slide, dict):
                continue
            latest_payload.append(_as_slide_payload(latest_sub_id, latest_slide))
            latest_text = _slide_text(latest_slide)

            best_score = 0.0
            best_prior_text = ""
            best_prior_slide_id = ""

            for prior_slide in prior_slides:
                if not isinstance(prior_slide, dict):
                    continue
                prior_text = _slide_text(prior_slide)
                score = _jaccard_score(latest_text, prior_text)
                if score > best_score:
                    best_score = score
                    best_prior_text = prior_text
                    best_prior_slide_id = str(prior_slide.get("slide_id", ""))

            if best_score >= 0.55:
                overlap_report.append(
                    {
                        "latest_subtopic_id": latest_sub_id,
                        "latest_slide_id": latest_slide.get("slide_id"),
                        "prior_subtopic_id": prior_sub_id,
                        "prior_slide_id": best_prior_slide_id,
                        "score": round(best_score, 3),
                        "latest_text": latest_text,
                        "prior_text": best_prior_text,
                        "method": "deterministic",
                    }
                )
                instructions.append(
                    f"Slide '{latest_slide.get('title', '')}' overlaps with subtopic '{prior_sub_id}'. "
                    f"Regenerate with a different objective angle and non-redundant coverage."
                )

    # Optional semantic verification with Groq using full latest/prior slide payloads.
    llm_overlaps = _llm_verify_overlaps_with_groq(
        latest_sub_id=latest_sub_id,
        latest_slides=latest_payload,
        prior_slides_pool=prior_payload,
    )

    if llm_overlaps:
        seen = {
            (
                str(item.get("latest_slide_id")),
                str(item.get("prior_subtopic_id")),
                str(item.get("prior_slide_id")),
            )
            for item in overlap_report
        }
        prior_by_key = {
            (x["subtopic_id"], x["slide_id"]): x for x in prior_payload
        }
        latest_by_id = {x["slide_id"]: x for x in latest_payload}

        for item in llm_overlaps:
            key = (
                str(item.get("latest_slide_id")),
                str(item.get("prior_subtopic_id")),
                str(item.get("prior_slide_id")),
            )
            if key in seen:
                continue
            latest_slide = latest_by_id.get(key[0], {})
            prior_slide = prior_by_key.get((key[1], key[2]), {})
            overlap_report.append(
                {
                    "latest_subtopic_id": latest_sub_id,
                    "latest_slide_id": key[0],
                    "prior_subtopic_id": key[1],
                    "prior_slide_id": key[2],
                    "score": float(item.get("score", 0.6)),
                    "latest_text": latest_slide.get("text", ""),
                    "prior_text": prior_slide.get("text", ""),
                    "method": "groq",
                    "reason": item.get("reason", "semantic overlap"),
                }
            )
            instructions.append(
                f"Slide '{latest_slide.get('title', key[0])}' semantically overlaps with subtopic '{key[1]}' (reason: {item.get('reason', 'semantic overlap')}). "
                f"Regenerate with a distinct learning objective and different instructional angle."
            )

    print(f"\n🔍 [COVERLAP] Checking subtopic {latest_sub_id} against prior content ({len(planned_sub_ids)-1} subtopics)...")

    if not overlap_report:
        print(f"✅ [COVERLAP] No overlaps detected for subtopic {latest_sub_id}.")
        return {
            "plans": plans,
            "coverage_overlap_report": [],
        }

    regen_attempts = dict(state.get("coverage_regen_attempts", {}))
    attempt_count = int(regen_attempts.get(latest_sub_id, 0))

    if attempt_count >= 2:
        print(f"⚠️ [REGEN] Max overlap attempts (2) reached for {latest_sub_id}. Stopping regeneration to prevent loop.")
        return {
            "plans": plans,
            "coverage_overlap_report": overlap_report,
            "coverage_regeneration_instructions": state.get("coverage_regeneration_instructions", {}),
            "coverage_regen_attempts": regen_attempts,
        }

    regen_attempts[latest_sub_id] = attempt_count + 1

    regen_instructions = dict(state.get("coverage_regeneration_instructions", {}))
    regen_instructions[latest_sub_id] = instructions[:10]

    print(f"🔄 [REGEN] Overlap detected in {latest_sub_id}! Attempt {attempt_count + 1}/2. Removing plan to trigger regeneration.")
    for report in overlap_report:
        print(f"   - Overlap: '{report['latest_text'][:50]}...' matches prior content (Score: {report['score']}, Method: {report['method']})")
    
    plans.pop(latest_sub_id, None)

    return {
        "plans": plans,
        "coverage_overlap_report": overlap_report,
        "coverage_regeneration_instructions": regen_instructions,
        "coverage_regen_attempts": regen_attempts,
    }
