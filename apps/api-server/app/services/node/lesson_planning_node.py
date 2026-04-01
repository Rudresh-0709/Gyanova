import json
from typing import Dict, Any, List
from ..state import TutorState
from .new_slide_planner import plan_slides_for_subtopic
import uuid


def lesson_planning_node(state: TutorState) -> TutorState:
    """
    Planning Node: Brainstorms the structure of the lesson before content is generated.
    Now refactored to handle ONE subtopic at a time for incremental updates.
    """
    sub_topics = state.get("sub_topics", [])
    difficulty = state.get("difficulty", "Beginner")
    learning_depth = state.get("learning_depth", "Normal")

    if state.get("unsupported_topic"):
        return {
            "plans": {},
            "sub_topics": [],
            "unsupported_topic": True,
            "unsupported_subject": state.get("unsupported_subject", "math"),
            "unsupported_message": state.get(
                "unsupported_message",
                "Math-related slides are currently under working. Please try a non-math topic for now.",
            ),
        }

    if "plans" not in state:
        state["plans"] = {}

    # Find the next sub-topic that hasn't been planned yet
    next_subtopic = None
    for sub in sub_topics:
        sub_id = sub.get("id")
        if sub_id not in state["plans"]:
            next_subtopic = sub
            break

    if next_subtopic:
        sub_id = next_subtopic.get("id")
        subtopic_name = next_subtopic.get("name")
        print(f"\n🧠 Planning subtopic: {subtopic_name}")

        plan_data = plan_slides_for_subtopic(
            next_subtopic,
            learning_depth=learning_depth,
        )
        slide_plans = plan_data.get("slides", [])

        # Assign unique slide_id and sequence
        for i, slide in enumerate(slide_plans):
            slide["slide_id"] = f"{sub_id}_s{i + 1}"
            slide["sequence_index"] = i

        state["plans"][sub_id] = slide_plans

    # Return only modified fields for clean state management
    return {"plans": state["plans"]}
