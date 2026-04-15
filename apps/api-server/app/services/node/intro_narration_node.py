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


def generate_intro_image_prompt(intro_type: str, title: str, context: str = "") -> str:
    """
    Generate an optimized image prompt for intro slides.
    
    Args:
        intro_type: "lesson" or "subtopic"
        title: Title of the lesson/subtopic
        context: Additional context for the image
    
    Returns:
        Image prompt suitable for Leonardo AI FLUX Schnell
    """
    if intro_type == "lesson":
        # Blueprint-forward visual language for lesson intros.
        return (
            f"Blueprint-style educational hero illustration for '{title}'. "
            f"Create a topic-resonant symbolic scene that clearly reflects the lesson concept. "
            f"Technical drawing aesthetic, glowing cyan line art, dark navy gradient background, "
            f"schematic overlays, geometric precision, minimal modern composition. "
            f"Wide cinematic landscape framing with central focus and generous negative space for title text. "
            f"No text, no letters, no labels, no watermark. "
            f"Premium, clean, professional educational visual, 4K quality."
        )
    elif intro_type == "subtopic":
        # Focused, detailed for subtopics
        return (
            f"A detailed instructional illustration of '{title}'. "
            f"Focus on core concepts and visual elements. "
            f"Professional educational design. "
            f"Clear, precise details. Balanced composition. "
            f"Technical precision with artistic flair. Studio lighting. 4K quality."
        )
    else:
        return f"Educational illustration of {title}. Professional design."


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


def extract_title_and_tagline(narration_text: str, context_name: str) -> tuple:
    """
    Extract title and tagline from narration text.
    
    For lesson intro: Use the topic/main concept as title, first sentence as tagline.
    For subtopic intro: Extract key phrase as title, main idea as tagline.
    """
    if not narration_text:
        return context_name, "Explore this section"
    
    sentences = [s.strip() for s in narration_text.split('.') if s.strip()]
    
    if len(sentences) == 0:
        return context_name, "Learn more"
    
    # Preserve the full first sentence so intro slides do not look clipped.
    tagline = sentences[0]
    
    # Title defaults to context_name but can be enhanced
    title = context_name
    
    return title, tagline


def intro_narration_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """LangGraph node to generate unique, style-independent lesson and subtopic intros."""
    topic = state.get("topic", "General Topic")
    difficulty = state.get("difficulty", "Beginner")

    # 1. Generate Lesson Opening (Once) - regenerate if payload exists but narration is empty
    lesson_intro_payload = state.get("lesson_intro_narration")
    needs_lesson_intro = (
        not lesson_intro_payload
        or not str(lesson_intro_payload.get("narration_text", "")).strip()
    )

    if needs_lesson_intro:
        print("Generating lesson opening narration...")
        lesson_intro = generate_lesson_opening(topic, difficulty)
        title, tagline = extract_title_and_tagline(lesson_intro, topic)
        state["lesson_intro_narration"] = {
            "narration_text": lesson_intro,
            "title": title,
            "tagline": tagline,
            "badge": "LESSON",
            "image_url": None,  # Will be set by image generation node
            "html_doc": None,   # Will be set by rendering node
        }
    else:
        lesson_intro = state["lesson_intro_narration"].get("narration_text", "")
        # Ensure fields exist
        if "title" not in state["lesson_intro_narration"]:
            title, tagline = extract_title_and_tagline(lesson_intro, topic)
            state["lesson_intro_narration"]["title"] = title
            state["lesson_intro_narration"]["tagline"] = tagline
            state["lesson_intro_narration"]["badge"] = "LESSON"
            state["lesson_intro_narration"]["image_url"] = None
            state["lesson_intro_narration"]["html_doc"] = None

    # Return only modified fields for clean state management
    return {
        "lesson_intro_narration": state["lesson_intro_narration"],
    }


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
