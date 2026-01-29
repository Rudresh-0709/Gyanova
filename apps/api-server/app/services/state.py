"""
State Definition for AI Teaching System

Using TypedDict for LangGraph compatibility - allows dictionary-style access
while maintaining type hints and IDE support.
"""

from typing import TypedDict, Optional, List, Dict, Any


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

    # Subtopics
    sub_topics: List[Dict[str, Any]]

    # Slide Planning & Content
    slide_plan: Dict[str, Any]
    slides: Dict[str, List[Dict[str, Any]]]  # subtopic_id -> list of slides

    # Narration
    intro_text: str
    lesson_intro_narration: Dict[str, Any]
    subtopic_intro_narrations: Dict[str, Any]

    # Teacher Info
    teacher_id: int
    teacher_voice_id: int
    teacher_gender: str

    # Preferences
    preferred_method: str
    topic_granularity: str

    # State Management
    current_slide: int
    last_completed_node: str

    # Interaction
    user_interruption: str
    ai_response: str
    messages: List[Dict[str, str]]

    # Error Handling
    error: str

    # Flags
    is_paused: bool
    timestamp: str
