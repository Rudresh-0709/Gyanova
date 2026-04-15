from ..llm.model_loader import load_groq, load_groq_fast, load_openai
from ..state import TutorState
import uuid
import json
import ast
import re


def _clamp(value: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(value, maximum))


def _dedupe_subtopics(subtopics):
    seen = set()
    unique = []
    for sub in subtopics:
        if not isinstance(sub, dict):
            continue
        name = str(sub.get("name", "")).strip().lower()
        if not name or name in seen:
            continue
        seen.add(name)
        unique.append(sub)
    return unique


def _compute_target_subtopic_count(
    learning_depth: str, analyzer_granularity: str, available_count: int
) -> int:
    """
    Compute final subtopic count from user depth + analyzer granularity.

    Summary and Overview are fixed expectations.
    Normal and Detailed adapt to available coverage while staying within safe bounds.
    """
    if available_count <= 0:
        return 0

    depth_key = (learning_depth or "Normal").strip().lower()
    granularity_key = (analyzer_granularity or "Focused").strip().lower()

    if depth_key == "summary":
        base_target = 1
        min_count, max_count = 1, 1
    elif depth_key == "overview":
        base_target = 3
        min_count, max_count = 2, 4
    elif depth_key == "detailed":
        # Adaptive upper baseline: maximize coverage without forcing unnecessary repetition.
        base_target = round(available_count * 0.85)
        min_count, max_count = 5, 8
    else:
        # Normal mode: adaptive middle baseline.
        base_target = round(available_count * 0.65)
        min_count, max_count = 3, 6

    adjustment_by_granularity = {
        "too broad": 1,
        "focused": 0,
        "too narrow": -1,
    }
    adjusted_target = base_target + adjustment_by_granularity.get(granularity_key, 0)
    bounded_target = _clamp(adjusted_target, min_count, max_count)

    # Never request more subtopics than we actually have.
    return _clamp(bounded_target, 1, available_count)


def extract_sub_topic(state: TutorState) -> TutorState:
    topic_str = state.get("topic", "")
    current_knowledge = state.get("currentKnowledge", "Intermediate")
    goal = state.get("goal", "Understand Core Concepts")
    curriculum_depth = state.get("curriculumDepth", "Normal")

    system_prompt = f"""You are an AI-powered educational assistant that helps design structured learning content.
Your goal is to break down a topic into logical, technical sub-topics tailored to the user's needs.

=== INPUTS ===
- topic: {topic_str}
- currentKnowledge: {current_knowledge}
- goal: {goal}
- curriculumDepth: {curriculum_depth}

=== SYSTEM/INSTRUCTION ===
1. Break down the topic into logical, technical sub-topics.
2. STICK EXACTLY to the user's topic. Do NOT rephrase it or change its scope.
3. Subtopics must be ordered progressively from fundamentals to advanced, adjusted to the learner's 'currentKnowledge' level (e.g. advanced learners can skip absolute basics).
4. Emphasize concepts and frame descriptions based on the user's 'goal' (e.g. Exam Prep => key points, Conceptual Mastery => strong intuition).
5. SUBTOPIC COUNT RULES based on 'curriculumDepth':
   - If curriculumDepth == "Summary" or "summary": generate EXACTLY 1 subtopic, written as a summarized/broad "single module" version of the topic.
   - Otherwise, generate more subtopics proportionally (e.g. Overview = ~3, Normal = ~4-6, Detailed = ~6-8).
   - You MUST comply with the exact count rules above even if you think more or fewer subtopics would be better.

=== OUTPUT SCHEMA ===
Format the output as a valid JSON object exactly like this:
{{
    "topic": "<EXACT original topic provided>",
    "sub_topics": [
        {{
            "name": "Sub-topic 1 name (Must be unique)",
            "difficulty": "Beginner/Intermediate/Advanced",
            "description": "Short objective or description of what this covers."
        }}
    ]
}}

If the topic is too vague or invalid (like "No clear topic detected"), respond with: {{"sub_topics": []}}

=== VALIDATION RULES ===
- If curriculumDepth is "Summary" or "summary" and you output more than 1 subtopic, that is invalid.
- If any subtopic title repeats, invalid.
- Each subtopic must include a short objective/description.
- If output is not valid JSON with no extra markdown or prose outside the JSON block, invalid.
"""
    user_prompt = state.get("topic", "")

    # Guard: If sub_topics already exists and has data, don't re-run expensive extraction
    # This ensures ID stability across graph loops/retries.
    if state.get("sub_topics") and len(state["sub_topics"]) > 0:
        print("\n✅ [INFO] Sub-topics already exist in state. Skipping extraction to maintain ID stability.")
        return {
            "sub_topics": state["sub_topics"],
            "subtopic_target_count": state.get("subtopic_target_count", len(state["sub_topics"])),
            "subtopic_available_count": state.get("subtopic_available_count", len(state["sub_topics"])),
            "topic_granularity": state.get("topic_granularity"),
        }

    if state.get("unsupported_topic"):
        print("\n⚠️  [WARNING] Skipping sub-topic extraction - topic is currently unsupported")
        return {
            "sub_topics": [],
            "unsupported_topic": True,
            "unsupported_subject": state.get("unsupported_subject", "math"),
            "unsupported_message": state.get(
                "unsupported_message",
                "Math-related slides are currently under working. Please try a non-math topic for now.",
            ),
        }
    
    # Guard: if topic extraction failed, skip sub-topic extraction
    if not user_prompt or user_prompt == "No clear topic detected":
        print("\n⚠️  [WARNING] Skipping sub-topic extraction - topic is invalid")
        state["sub_topics"] = []
        return state
    
    llm = load_groq()
    topic = llm.invoke(system_prompt + " " + user_prompt)

    # DEBUG: Show raw sub-topic output
    print("\n--- [DEBUG] SUB-TOPIC EXTRACTION LLM OUTPUT ---")
    print(topic.content)
    print("------------------------------------------------\n")

    json_match = re.search(r"```json\s*([\s\S]*?)\s*```", topic.content)
    if json_match:
        json_string = json_match.group(1).strip()
    else:
        # Assume the whole content is the JSON string
        json_string = topic.content.strip()
    try:
        data = json.loads(json_string)
    except json.JSONDecodeError:
        print("Error: Model did not return valid JSON")
        print(topic.content)
        state["sub_topics"] = []
        return state

    raw_sub_topics = data.get("sub_topics", [])
    unique_sub_topics = _dedupe_subtopics(raw_sub_topics)

    learning_depth = state.get("learning_depth", "Normal")
    analyzer_granularity = state.get("topic_granularity") or state.get("granularity", "Focused")
    available_count = len(unique_sub_topics)
    target_count = _compute_target_subtopic_count(
        learning_depth=learning_depth,
        analyzer_granularity=analyzer_granularity,
        available_count=available_count,
    )

    sub_topics = unique_sub_topics[:target_count]

    for i, sub in enumerate(sub_topics, start=1):
        sub["id"] = f"sub_{i}_{uuid.uuid4().hex[:6]}"

    state["sub_topics"] = sub_topics
    state["subtopic_target_count"] = target_count
    state["subtopic_available_count"] = available_count
    state["topic_granularity"] = analyzer_granularity
    
    # Return only modified fields for clean state management
    return {
        "sub_topics": state["sub_topics"],
        "subtopic_target_count": state["subtopic_target_count"],
        "subtopic_available_count": state["subtopic_available_count"],
        "topic_granularity": state["topic_granularity"],
    }


if __name__ == "__main__":
    State = {"topic": "Computer generations"}
    print(extract_sub_topic(State))
