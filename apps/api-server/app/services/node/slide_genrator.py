from ..llm.model_loader import load_groq, load_groq_fast, load_openai, load_gemini
from ..state import TutorState
import uuid
import json
import ast


def generate_slides_for_subtopic(subtopic):
    """Generate 1 or more slides for a given subtopic using LLM"""
    llm = load_groq()
    SYSTEM_PROMPT = """
    You are an AI tutor that generates teachable slides in strict JSON only. 
    ROLE: produce a sequence of slides that teach a single subtopic to a learner.

    REQUIREMENTS (must follow exactly):
    1. Output must be **only** a JSON array (starting with '[' and ending with ']') and nothing else.
    2. Each array element is an object with at least these fields:
    - "title": string (short, <= 60 chars)
    - "narration": string (3–6 sentences; conversational, teacher-like, expands & explains the bullets; avoid repeating bullets verbatim)
    - "content": array of 3–5 concise bullet strings (each <= 12 words)
    3. Optional but recommended fields (model may include):
    - "key_terms": array of short keywords (2–6 items)
    - "visual": single-line suggestion for an image/diagram/visual aid
    - "duration_seconds": integer (suggested spoken duration for the narration)
    4. Do NOT include any extra text, commentary, or markdown outside the JSON array. If you cannot produce the requested structure, return an empty array [].
    5. Tone: friendly, explanatory, examples & analogies when helpful, connect to prior knowledge and next steps.
    6. Bullet rules: each bullet single concise idea; bullets should support the narration (narration should expand them).
    7. Slide count guidance (choose the closest):
    - Beginner: 3–4 slides
    - Intermediate: 4–6 slides
    - Advanced: 5–8 slides
    8. If the user provides a 'focus' or 'audience' in the user prompt, tailor examples to that focus/audience.
    9. Give appropriate visual style preferable to the slide info ex. "stock" if stock image is preferred, "pptslide" if a ppt style slide image is preferred or "ai_image" if an ai generated image is preferred.

    EXAMPLE SLIDE OBJECT:
    [
    {
        "title": "Brief slide title",
        "narration": "3–6 sentence teacher-style explanation that expands the bullets.",
        "content": ["bullet 1", "bullet 2", "bullet 3"],
        "key_terms": ["term1","term2"],
        "visual": "one-line visual suggestion",
        "visual_type": "stock" or "pptslide" or "ai_image",
        "duration_seconds": 45
    }
    ]
    """

    user_prompt = f"Subtopic: {subtopic['name']}"
    response = llm.invoke(SYSTEM_PROMPT + user_prompt)

    try:
        slides = json.loads(response.content)
        for i, slide in enumerate(slides, start=1):
            slide["id"] = f"slide_{i}_{uuid.uuid4().hex[:6]}"
            slide["order"] = i
        return slides
    except Exception as e:
        print("JSON parsing failed:", e)
        return []


def generate_all_slides(state):
    """Loop over subtopics and generate slides for each"""
    state["slides"] = {}

    for subtopic in state["sub_topics"]:
        sub_id = subtopic["id"]
        state["slides"][sub_id] = generate_slides_for_subtopic(subtopic)

    return state


# Example run
if __name__ == "__main__":
    TutorState = {
        "topic": "Computer generations",
        "sub_topics": [
            {
                "name": "Introduction to Computer Generations",
                "difficulty": "Beginner",
                "id": "sub_1_89ba45",
            },
            {
                "name": "First Generation Computers (1940s-1950s): Vacuum Tubes",
                "difficulty": "Intermediate",
                "id": "sub_2_a2f29f",
            },
            {
                "name": "Second to Fifth Generation Computers (1950s-1980s): Transistors, Integrated Circuits, and Microprocessors",
                "difficulty": "Intermediate",
                "id": "sub_3_7cc90e",
            },
            {
                "name": "Modern Computer Generations (1990s-present): Advances in Microarchitecture and Artificial Intelligence",
                "difficulty": "Advanced",
                "id": "sub_4_261744",
            },
            {
                "name": "Comparison and Evolution of Computer Generations",
                "difficulty": "Intermediate",
                "id": "sub_5_632e6d",
            },
        ],
    }

    updated_state = generate_all_slides(TutorState)
    print(json.dumps(updated_state, indent=2))
