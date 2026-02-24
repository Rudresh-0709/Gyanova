import json
from typing import Dict, Any, List
from ..state import TutorState
from .new_slide_planner import plan_slides_for_subtopic
import uuid


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
        plan_data = plan_slides_for_subtopic(subtopic)
        slide_plans = plan_data.get("slides", [])

        # Assign unique slide_id and sequence
        for i, slide in enumerate(slide_plans):
            slide["slide_id"] = f"{sub_id}_s{i + 1}"
            slide["sequence_index"] = i

        state["plans"][sub_id] = slide_plans

    return state
