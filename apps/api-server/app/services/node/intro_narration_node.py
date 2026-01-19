import json
from typing import Dict, Any

try:
    from ..llm.model_loader import load_groq
    from ..state import TutorState
except ImportError:
    import sys
    import os

    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from llm.model_loader import load_groq
    from state import TutorState


def generate_lesson_opening(topic: str, difficulty: str, narration_style: str) -> str:
    """Generates the opening narration for the entire lesson."""
    llm = load_groq()

    SYSTEM_PROMPT = f"""
    You are an expert teacher welcoming students to a new lesson.
    
    🎯 CONTEXT:
    - Topic: {topic}
    - Difficulty: {difficulty}
    - Narration Style (User Preference): {narration_style}
    
    🧩 REQUIREMENTS:
    1. **Spoken Narration**: Write exactly what the teacher would say.
    2. **Tone**: Set a friendly, welcoming, and professional educational tone.
    3. **Content**:
       - Greet the learners warmly.
       - Introduce the topic: {topic}.
       - Briefly explain what they will learn and why it matters.
    4. **Constraints**:
       - 3–5 natural sentences.
       - No slide references (do NOT say "In this slide" or "Look at the screen").
       - No bullet points or markdown.
    5. **Style Match**: Strongly reflect the user's requested style: '{narration_style}'.
    """

    USER_PROMPT = f"Generate a lesson opening for the topic: '{topic}'."

    response = llm.invoke(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_PROMPT},
        ]
    )

    return response.content.strip()


def generate_subtopic_intro(
    subtopic_name: str,
    topic: str,
    difficulty: str,
    narration_style: str,
    lesson_opening: str = "",
) -> str:
    """Generates a concise transition narration for a specific subtopic."""
    llm = load_groq()

    SYSTEM_PROMPT = f"""
    You are an expert teacher transitioning to a specific section of a lesson.
    
    🎯 CONTEXT:
    - Main Topic: {topic}
    - Subtopic: {subtopic_name}
    - Difficulty: {difficulty}
    - Style: {narration_style}
    
    PREVIOUS CONTEXT (Do NOT repeat anything from here):
    "{lesson_opening}"
    
    🧩 REQUIREMENTS:
    1. **Conciseness (CRITICAL)**: Strictly 1–2 sentences. Be very brief.
    2. **Role**: This is a bridge. Connect the broad topic to this specific subtopic's detail.
    3. **Tone**: Focused and transitionary.
    4. **Constraints**:
       - NO Greetings (No 'Hello', 'Welcome', or 'Hi').
       - NO repetition of the main lesson hook.
       - Focus strictly on the value of '{subtopic_name}'.
    """

    USER_PROMPT = (
        f"Provide a 1-sentence transition into the subtopic '{subtopic_name}'."
    )

    response = llm.invoke(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_PROMPT},
        ]
    )

    return response.content.strip()


def intro_narration_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """LangGraph node to generate unique lesson and subtopic transition narrations."""
    topic = state.get("topic", "General Topic")
    difficulty = state.get("difficulty", "Beginner")
    narration_style = state.get(
        "narration_style", "Clear and engaging educational style"
    )

    # 1. Generate Lesson Opening (Once)
    if "lesson_intro_narration" not in state or state["lesson_intro_narration"] is None:
        print("Generating lesson opening narration...")
        lesson_intro = generate_lesson_opening(topic, difficulty, narration_style)
        state["lesson_intro_narration"] = {"narration_text": lesson_intro}
    else:
        lesson_intro = state["lesson_intro_narration"].get("narration_text", "")

    # 2. Generate Subtopic Intros (Transitionary)
    if (
        "subtopic_intro_narrations" not in state
        or state["subtopic_intro_narrations"] is None
    ):
        state["subtopic_intro_narrations"] = {}

    slide_plan = state.get("slide_plan", {})

    for sub_id, sub_data in slide_plan.items():
        sub_name = sub_data.get("subtopic_name")
        if sub_id and sub_id not in state["subtopic_intro_narrations"]:
            print(f"Generating transition for subtopic: {sub_name}...")
            # Pass lesson_intro to ensure subtopic intro is unique and doesn't repeat the hook
            sub_intro = generate_subtopic_intro(
                sub_name,
                topic,
                difficulty,
                narration_style,
                lesson_opening=lesson_intro,
            )
            state["subtopic_intro_narrations"][sub_id] = {"narration_text": sub_intro}

    return state


if __name__ == "__main__":
    SampleState = {
        "topic": "Computer generations",
        "difficulty": "Intermediate",
        "narration_style": "Friendly and analogies-heavy teacher style",
        "slide_plan": {
            "sub_1_2b67b6": {
                "subtopic_name": "Introduction to Computer Generations",
                "slides": [
                    {
                        "slide_title": "Introduction to Computer Generations",
                        "slide_purpose": "definition",
                        "selected_template": "Title card",
                        "narration_role": "Introduce",
                        "narration_goal": "Understand what computer generations are and why they matter.",
                        "reasoning": "Standard intro style.",
                        "slide_id": "sub_1_2b67b6_s1",
                    }
                ],
            }
        },
        "slides": {
            "sub_1_2b67b6": [
                {
                    "slide_title": "Introduction to Computer Generations",
                    "slide_purpose": "definition",
                    "selected_template": "Title card",
                    "narration_role": "Introduce",
                    "narration_goal": "Understand what computer generations are and why they matter.",
                    "reasoning": "Standard intro style.",
                    "slide_id": "sub_1_2b67b6_s1",
                    "narration_text": "Think of computer generations like chapters in a book, each marking a leap in technology and capability. Just as cars evolved from steam engines to electric models, computers have progressed through distinct stages, each defined by breakthroughs in hardware and design. Understanding these generations helps us appreciate how far computing has come and why today\u2019s devices are so powerful and efficient.",
                }
            ]
        },
    }

    result = intro_narration_node(SampleState)
    print(json.dumps(result, indent=2))
