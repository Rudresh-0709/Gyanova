from ..llm.model_loader import load_groq,load_groq_fast,load_openai,load_gemini
from ..state import TutorState
import uuid
import json
import ast

def generate_slides_for_subtopic(subtopic):
    """Generate 1 or more slides for a given subtopic using LLM"""
    llm = load_groq()
    
    SYSTEM_PROMPT="""
    You are an AI slide planner that designs structured, teachable slides for an interactive AI tutor.

    ROLE:
    Your job is to create the *skeleton* or *structure* for slides that will later be filled with narration and visuals by other modules.
    You DO NOT generate any narration or bullet content yourself.

    OUTPUT RULES:
    1. Output must be a **JSON array** only — no text, markdown, or explanations outside JSON.
    2. Each object in the array must contain:
    - "title": string (<= 60 chars, clear and specific)
    - "key_terms": array of 2–6 short keywords
    - "visual_type": choose one of the following based on content:
        - "pptslide" → when visual explanation can be done using simple text, diagrams, or cliparts (e.g., conceptual, sequential, summary slides).
        - "stock" → when topic has real-world, photographic examples (e.g., environment, biology, geography, daily-life examples).
        - "ai_image" → when visuals are abstract, scientific, historical, or not easily available in stock libraries (e.g., “ancient atom model”, “black hole cross-section”, “AI neural network visualization”).
    3. Each slide should teach one clear concept or idea.
    4. Number of slides:
    - Beginner topics → 3–4 slides
    - Intermediate → 4–6 slides
    - Advanced → 5–8 slides
    5. Titles must follow a logical teaching flow: introduction → concept → example/application → summary.

    TONE:
    Structured, logical, and modular. Think like a lesson designer/teacher who plans what will be taught per slide — not how it’s taught.

    EXAMPLE OUTPUT:
    [
    {
        "title": "Introduction to Atoms",
        "key_terms": ["atom", "matter", "structure"],
        "visual_type": "pptslide"
    },
    {
        "title": "Protons and Neutrons",
        "key_terms": ["nucleon", "proton", "neutron"],
        "visual_type": "ai_image"
    },
    {
        "title": "Electrons and Orbits",
        "key_terms": ["electron", "orbit", "energy level"],
        "visual_type": "pptslide"
    },
    {
        "title": "Isotopes and Stability",
        "key_terms": ["isotope", "atomic mass", "stability"],
        "visual_type": "stock"
    }
    ]

    Your JSON must begin with '[' and end with ']' with no trailing text or commentary.
    """
    
    user_prompt = f"Subtopic: {subtopic['name']}"
    response = llm.invoke(SYSTEM_PROMPT + user_prompt)

    print("Model raw output:", response.content)

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
                "name": "What is an atom?",
                "difficulty": "Beginner",
                "id": "sub_1_af16be"
            },
            {
                "name": "Parts of an atom",
                "difficulty": "Intermediate",
                "id": "sub_2_f30be9"
            },
            {
                "name": "Atomic number and mass number",
                "difficulty": "Intermediate",
                "id": "sub_3_7b69d0"
            },
            {
                "name": "Electron shells for first 20 elements",
                "difficulty": "Advanced",
                "id": "sub_4_78635b"
            },
            {
                "name": "Ions and neutral atoms",
                "difficulty": "Intermediate",
                "id": "sub_5_283526"
            }
        ]
    }

    updated_state = generate_all_slides(TutorState)
    print(json.dumps(updated_state, indent=2))