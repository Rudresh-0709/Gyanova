from llm.model_loader import load_groq,load_groq_fast,load_openai,load_gemini
from state import TutorState
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
        "visual_type": "pptslide",
        "narration_tone": "friendly"
    },
    {
        "title": "Protons and Neutrons",
        "key_terms": ["nucleon", "proton", "neutron"],
        "visual_type": "ai_image",
        "narration_tone": "analytical"
    },
    {
        "title": "Electrons and Orbits",
        "key_terms": ["electron", "orbit", "energy level"],
        "visual_type": "pptslide",
        "narration_tone": "curious"
    },
    {
        "title": "Isotopes and Stability",
        "key_terms": ["isotope", "atomic mass", "stability"],
        "visual_type": "stock",
        "narration_tone": "neutral"
    }
    ]

    Your JSON must begin with '[' and end with ']' with no trailing text or commentary.
    """