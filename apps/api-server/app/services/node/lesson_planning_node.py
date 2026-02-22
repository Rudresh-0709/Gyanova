import json
from typing import Dict, Any, List
from ..llm.model_loader import load_openai
from ..state import TutorState


def plan_slides_for_subtopic(
    subtopic_name: str, difficulty: str
) -> List[Dict[str, str]]:
    """Plans 3-5 slide concepts (titles/goals) for a subtopic."""
    llm = load_openai()

    prompt = f"""
    You are an AI Curriculum Planner. Plan a series of 3-5 slides for the subtopic: '{subtopic_name}'.
    Difficulty: {difficulty}
    
    For each slide, provide a 'title' and a 'goal' (what the student should learn).
    Ensure logical progression and high educational value.
    DO NOT mention layouts or templates.

    Output ONLY valid JSON:
    {{
        "slides": [
            {{"title": "...", "goal": "..."}},
            ...
        ]
    }}
    """

    resp = llm.invoke([{"role": "user", "content": prompt}])
    try:
        content = resp.content.replace("```json", "").replace("```", "").strip()
        return json.loads(content).get("slides", [])
    except Exception as e:
        print(f"Error parsing slide plans: {e}")
        return [
            {"title": subtopic_name, "goal": f"Master the basics of {subtopic_name}."}
        ]


def lesson_planning_node(state: TutorState) -> TutorState:
    """
    Planning Node: Brainstorms the structure of the lesson before content is generated.
    """
    sub_topics = state.get("sub_topics", [])
    difficulty = state.get("difficulty", "Beginner")

    if "plans" not in state:
        state["plans"] = {}

    print(f"\n🧠 Planning Lesson Structure...")

    for subtopic in sub_topics:
        sub_id = subtopic.get("id")
        subtopic_name = subtopic.get("name")
        sub_difficulty = subtopic.get("difficulty", difficulty)

        print(f"  📍 Planning subtopic: {subtopic_name}")
        slide_plans = plan_slides_for_subtopic(subtopic_name, sub_difficulty)
        state["plans"][sub_id] = slide_plans

    return state
