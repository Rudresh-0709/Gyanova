"""
State Definition for AI Teaching System

Using TypedDict for LangGraph compatibility - allows dictionary-style access
while maintaining type hints and IDE support.
"""

from typing import TypedDict, Optional, List, Dict, Any, Annotated


def merge_dict_updates(left: Dict, right: Dict) -> Dict:
    """
    Reducer function for merging concurrent dictionary updates.
    
    Used for fields that can be updated by multiple parallel nodes.
    Right dict's values overwrite left dict's values for matching keys.
    """
    if not left:
        return right if right else {}
    if not right:
        return left if left else {}
    merged = left.copy()
    merged.update(right)
    return merged


class TutorState(TypedDict, total=False):
    """
    State for the AI teaching workflow.

    TypedDict allows:
    - Dictionary-style access: state.get("key"), state["key"]
    - Type hints for IDE support
    - LangGraph compatibility

    Fields are marked total=False so all keys are optional.
    """

    # User Input
    user_input: str

    # Topic Extraction
    topic: str
    granularity: str
    topic_granularity: str
    learning_depth: str

    # Subtopics
    sub_topics: List[Dict[str, Any]]
    subtopic_target_count: int
    subtopic_available_count: int

    # Slide Planning & Content
    slide_plan: Dict[str, Any]
    plans: Dict[
        str, List[Dict[str, Any]]
    ]  # subtopic_id -> list of slide concepts (Phase 1)
    slides: Annotated[
        Dict[str, List[Dict[str, Any]]], merge_dict_updates
    ]  # subtopic_id -> list of full slides (Phase 2); uses reducer to merge concurrent updates

    # Narration
    intro_text: str
    lesson_intro_narration: Dict[str, Any]
    subtopic_intro_narrations: Dict[str, Any]

    # Audio
    audio_output_dir: str

    # Teacher Info
    teacher_id: int
    teacher_voice_id: int
    teacher_gender: str

    # Preferences
    preferred_method: str

    # State Management
    current_slide: int
    last_completed_node: str
    processed_subtopic_ids: List[str]  # IDs of subtopics fully processed

    # Interaction
    user_interruption: str
    ai_response: str
    messages: List[Dict[str, str]]

    # Error Handling
    error: str

    # Unsupported topic handling
    unsupported_topic: bool
    unsupported_subject: str
    unsupported_message: str

    # Flags
    is_paused: bool
    timestamp: str
