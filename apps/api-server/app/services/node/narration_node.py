from ..llm.model_loader import load_groq, load_groq_fast, load_openai, load_gemini
from ..state import TutorState
import json

def generate_narration_for_slide(slide, subtopic_name, narration_style):
    """Generate narration text for a single slide."""
    llm = load_openai()

    SYSTEM_PROMPT = f"""
    You are an expert educational narrator and explainer for an AI teaching platform.
    Your role is to transform each slide into a clear, emotionally engaging, and pedagogically sound spoken narration — 
    as if a passionate teacher is speaking to a student.

    🎭 TEACHING STYLE (USER PREFERENCE):
    {narration_style if narration_style else "Default: Use a clear, structured, and balanced tone suitable for general learners."}

    🎯 PURPOSE:
    Turn slide content (title + key terms + subtopic) into a teaching experience — not just an explanation.
    Make it easy to follow, interesting to listen to, and emotionally engaging.
    Focus on **one core idea** per slide's narration to prevent cognitive overload.

    - Explain concepts step-by-step, introducing each term in a way that builds understanding.
    - Maintain curiosity flow: start with a small question, build explanation, end with insight.

    📚 CONTENT STRUCTURE:
    Each narration should:
    1. Begin with a *hook* or *curiosity trigger* related to the slide title.
    2. Gradually explain the concept and introduce `key_terms` naturally, **defining them implicitly or with brief clarity**.
    3. Use analogies, mini examples, or scenarios where helpful, strictly adhering to the TEACHING STYLE.
    4. End with a small reflective or transition sentence (“Now that we understand…, let’s explore…”).
    5. Conclude the narration on a high, encouraging note.

    🧩 OUTPUT FORMAT:
    Return only valid JSON, no markdown or text outside JSON.
    Example:
    {{
      "narration": "Have you ever wondered what holds the center of an atom together? At the core lies the nucleus — made of protons and neutrons, tightly packed together...",
      "style": "{narration_style if narration_style else 'default'}"
    }}

    📏 LENGTH:
    - 80–140 words.
    - Must sound like a teacher speaking naturally for 25–35 seconds.

    Avoid:
    - Lists or bullet formats.
    - Robotic or formal textbook tone.
    - Phrases like “In this slide we will learn” or “This slide explains”.
    - **Avoid filler phrases** like 'Alright,' 'So,' or 'Moving on,' unless they serve a clear conversational purpose.

    You are the voice of the teacher. Teach with flow, presence, and clarity.
    """

    user_prompt = f"""
    Subtopic: {subtopic_name}
    Slide: {json.dumps(slide, ensure_ascii=False)}
    """

    response = llm.invoke([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt}
    ])

    try:
        narration_data = json.loads(response.content)
    except Exception:
        import re
        text = str(response)
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            narration_data = json.loads(match.group(0))
        else:
            narration_data = {"narration": "Parsing failed.", "style": "neutral"}


    try:
        narration_data = json.loads(response.content)
        slide["narration"] = narration_data.get("narration", "").strip()
        slide["narration_style"] = narration_data.get("style", slide.get("narration_tone", "neutral"))
    except Exception as e:
        print("Narration JSON parsing failed:", e)
        slide["narration"] = "Narration unavailable due to parsing error."
        slide["narration_style"] = "neutral"

    return slide


def generate_all_narrations(state):
    """Generate narrations for all slides directly (not grouped by subtopics)."""
    slides_by_subtopic = state.get("slides", {})
    narration_style = state.get("narration_style", "default educational style")

    # ✅ Loop through all subtopic slide groups
    for sub_id, slide_list in slides_by_subtopic.items():
        for i, slide in enumerate(slide_list):
            # Pass each slide individually
            slides_by_subtopic[sub_id][i] = generate_narration_for_slide(
                slide=slide,
                subtopic_name=None,  # Not needed anymore
                narration_style=narration_style
            )

    # ✅ Update state with new narrations
    state["slides"] = slides_by_subtopic
    return state


if __name__ == "__main__":
    TutorState = {
        "topic": "Computer generations",
        "narration_style": "Narrate the topics like you are teaching a 5 year old, simplify the topics. Give analogies and examples to teach hard topics.",
        "slides": {
            "sub_1_af16be": [
            {
                "title": "Introduction to Atoms",
                "key_terms": [
                "atom",
                "matter",
                "structure"
                ],
                "visual_type": "pptslide",
                "id": "slide_1_774d9b",
                "order": 1
            },
            {
                "title": "Atom Components",
                "key_terms": [
                "proton",
                "neutron",
                "electron"
                ],
                "visual_type": "ai_image",
                "id": "slide_2_65e33c",
                "order": 2
            },
            {
                "title": "Atomic Structure",
                "key_terms": [
                "nucleus",
                "orbit",
                "shell"
                ],
                "visual_type": "pptslide",
                "id": "slide_3_204c70",
                "order": 3
            },
            {
                "title": "Real World Atoms",
                "key_terms": [
                "element",
                "compound",
                "molecule"
                ],
                "visual_type": "stock",
                "id": "slide_4_ad5234",
                "order": 4
            }
            ],
            "sub_2_f30be9": [
            {
                "title": "Introduction to Atoms",
                "key_terms": [
                "atom",
                "matter",
                "structure"
                ],
                "visual_type": "pptslide",
                "id": "slide_1_a69640",
                "order": 1
            },
            {
                "title": "Protons and Neutrons",
                "key_terms": [
                "nucleon",
                "proton",
                "neutron"
                ],
                "visual_type": "ai_image",
                "id": "slide_2_1a2afc",
                "order": 2
            },
            {
                "title": "Electrons and Orbits",
                "key_terms": [
                "electron",
                "orbit",
                "energy level"
                ],
                "visual_type": "pptslide",
                "id": "slide_3_b17a7f",
                "order": 3
            },
            {
                "title": "Atomic Nucleus",
                "key_terms": [
                "nucleus",
                "proton",
                "neutron"
                ],
                "visual_type": "ai_image",
                "id": "slide_4_8e2d37",
                "order": 4
            }
            ],
            "sub_3_7b69d0": [
            {
                "title": "Introduction to Atomic Number",
                "key_terms": [
                "atomic number",
                "protons",
                "elements"
                ],
                "visual_type": "pptslide",
                "id": "slide_1_4b22b8",
                "order": 1
            },
            {
                "title": "Understanding Mass Number",
                "key_terms": [
                "mass number",
                "nucleons",
                "isotopes"
                ],
                "visual_type": "ai_image",
                "id": "slide_2_f22849",
                "order": 2
            },
            {
                "title": "Relationship Between Atomic and Mass Numbers",
                "key_terms": [
                "atomic mass",
                "protons",
                "neutrons"
                ],
                "visual_type": "pptslide",
                "id": "slide_3_2c9e3e",
                "order": 3
            },
            {
                "title": "Real-World Applications of Atomic and Mass Numbers",
                "key_terms": [
                "isotopes",
                "radioactivity",
                "nuclear reactions"
                ],
                "visual_type": "stock",
                "id": "slide_4_00f946",
                "order": 4
            }
            ],
            "sub_4_78635b": [
            {
                "title": "Introduction to Electron Shells",
                "key_terms": [
                "electron",
                "shell",
                "orbital"
                ],
                "visual_type": "pptslide",
                "id": "slide_1_f8a634",
                "order": 1
            },
            {
                "title": "Electron Shell Configuration",
                "key_terms": [
                "electron configuration",
                "shell filling",
                "aufbau principle"
                ],
                "visual_type": "ai_image",
                "id": "slide_2_5cd233",
                "order": 2
            },
            {
                "title": "First 10 Elements' Electron Shells",
                "key_terms": [
                "hydrogen",
                "helium",
                "alkali metals"
                ],
                "visual_type": "pptslide",
                "id": "slide_3_8a547d",
                "order": 3
            },
            {
                "title": "Transition to d-Block Elements",
                "key_terms": [
                "d-block",
                "transition metals",
                "electron shell"
                ],
                "visual_type": "ai_image",
                "id": "slide_4_482c6d",
                "order": 4
            },
            {
                "title": "Electron Shells of First 20 Elements",
                "key_terms": [
                "s-block",
                "p-block",
                "d-block"
                ],
                "visual_type": "stock",
                "id": "slide_5_812d69",
                "order": 5
            },
            {
                "title": "Stability and Reactivity Trends",
                "key_terms": [
                "reactivity",
                "stability",
                "electron configuration"
                ],
                "visual_type": "pptslide",
                "id": "slide_6_ce490b",
                "order": 6
            }
            ],
            "sub_5_283526": [
            {
                "title": "Introduction to Ions",
                "key_terms": [
                "ion",
                "atom",
                "charge"
                ],
                "visual_type": "pptslide",
                "id": "slide_1_017de5",
                "order": 1
            },
            {
                "title": "Formation of Cations",
                "key_terms": [
                "cation",
                "electron loss",
                "positive charge"
                ],
                "visual_type": "ai_image",
                "id": "slide_2_1b5fd2",
                "order": 2
            },
            {
                "title": "Formation of Anions",
                "key_terms": [
                "anion",
                "electron gain",
                "negative charge"
                ],
                "visual_type": "ai_image",
                "id": "slide_3_adddfa",
                "order": 3
            },
            {
                "title": "Neutral Atoms vs Ions",
                "key_terms": [
                "neutral atom",
                "ion",
                "electroneutrality"
                ],
                "visual_type": "pptslide",
                "id": "slide_4_5e6832",
                "order": 4
            }
            ]
        }
    }

    updated_state = generate_all_narrations(TutorState)
    print(json.dumps(updated_state, indent=2))