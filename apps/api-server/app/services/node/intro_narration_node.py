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


def generate_lesson_opening(topic: str, difficulty: str) -> str:
    """Generates the opening narration for the entire lesson with a standard professional persona."""
    llm = load_groq()

    SYSTEM_PROMPT = f"""
    You are an expert teacher welcoming students to a new comprehensive lesson.
    
    🎯 CONTEXT:
    - Topic: {topic}
    - Difficulty: {difficulty}
    
    🧩 REQUIREMENTS:
    1. **Persona**: Professional, warm, and highly motivational. Do NOT use extreme styling or analogies (no space analogies, no "teen talk"). Just clear, high-quality teaching.
    2. **Content**:
       - Greet the learners warmly.
       - Introduce the topic: {topic}.
       - Explain the "Big Picture" — why this topic is vital to master and what the ultimate learning goal is.
    3. **Constraints**:
       - 3–5 natural sentences.
       - No slide references.
       - Focus on the **Journey** and **Motivation**.
    """

    USER_PROMPT = f"Generate a motivational lesson opening for the topic: '{topic}'."

    response = llm.invoke(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_PROMPT},
        ]
    )

    return response.content.strip()


def generate_subtopic_intro(
    subtopic_name: str, topic: str, difficulty: str, lesson_opening: str = ""
) -> str:
    """Generates a concise transition narration focusing on specific utility, avoiding lesson-level hooks."""
    llm = load_groq()

    SYSTEM_PROMPT = f"""
    You are an expert teacher bridging to a specific technical section of a lesson.
    
    🎯 CONTEXT:
    - Main Topic: {topic}
    - Subtopic: {subtopic_name}
    - Difficulty: {difficulty}
    
    PREVIOUS CONTEXT (Do NOT repeat the "Big Picture" or "GREETINGS" from here):
    "{lesson_opening}"
    
    🧩 REQUIREMENTS:
    1. **Strictly Unique**: Even if the subtopic name is similar to the topic name, focus on the **Practical Application** or **Specific Building Block** of this section. 
    2. **Conciseness**: 1–2 transitionary sentences.
    3. **Tone**: Direct, operational, and bridging. Explaining how this specific block fits into the puzzle.
    4. **Constraints**:
       - NO Greetings (No 'Hello', 'Welcome').
       - NO motivational hooks (those were for the lesson intro).
       - Focus strictly on the "Next Step" logic of '{subtopic_name}'.
    """

    USER_PROMPT = (
        f"Provide a practical 1-sentence bridge into the subtopic '{subtopic_name}'."
    )

    response = llm.invoke(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_PROMPT},
        ]
    )

    return response.content.strip()


def intro_narration_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """LangGraph node to generate unique, style-independent lesson and subtopic intros."""
    topic = state.get("topic", "General Topic")
    difficulty = state.get("difficulty", "Beginner")

    # 1. Generate Lesson Opening (Once) - Now independent of narration_style
    if "lesson_intro_narration" not in state or state["lesson_intro_narration"] is None:
        print("Generating lesson opening narration...")
        lesson_intro = generate_lesson_opening(topic, difficulty)
        state["lesson_intro_narration"] = {"narration_text": lesson_intro}
    else:
        lesson_intro = state["lesson_intro_narration"].get("narration_text", "")

    # 2. Generate Subtopic Intros (Transitionary) - Now independent of narration_style
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
            # Pass lesson_intro to explicitly force uniqueness
            sub_intro = generate_subtopic_intro(
                sub_name, topic, difficulty, lesson_opening=lesson_intro
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
