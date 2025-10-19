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
        ],
        "slides": {
            "sub_1_af16be": [
            {
                "title": "Introduction to Atoms",
                "key_terms": [
                "atom",
                "matter",
                "structure"
                ],
                "id": "slide_1_075595",
                "order": 1
            },
            {
                "title": "Atom Composition",
                "key_terms": [
                "proton",
                "neutron",
                "electron"
                ],
                "id": "slide_2_7cd67b",
                "order": 2
            },
            {
                "title": "Atomic Structure",
                "key_terms": [
                "nucleus",
                "orbit",
                "energy level"
                ],
                "id": "slide_3_09a1ad",
                "order": 3
            },
            {
                "title": "Atom Summary",
                "key_terms": [
                "atom",
                "element",
                "compound"
                ],
                "id": "slide_4_e5cdd6",
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
                "id": "slide_1_61a532",
                "order": 1
            },
            {
                "title": "Protons and Neutrons",
                "key_terms": [
                "nucleon",
                "proton",
                "neutron"
                ],
                "id": "slide_2_dbebc2",
                "order": 2
            },
            {
                "title": "Electrons and Orbits",
                "key_terms": [
                "electron",
                "orbit",
                "energy level"
                ],
                "id": "slide_3_ad9a57",
                "order": 3
            },
            {
                "title": "Atom Structure Summary",
                "key_terms": [
                "nucleus",
                "electron cloud",
                "atomic mass"
                ],
                "id": "slide_4_82e3a8",
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
                "id": "slide_1_dfbeae",
                "order": 1
            },
            {
                "title": "Understanding Mass Number",
                "key_terms": [
                "mass number",
                "nucleons",
                "isotopes"
                ],
                "id": "slide_2_65abc0",
                "order": 2
            },
            {
                "title": "Relationship Between Atomic and Mass Number",
                "key_terms": [
                "atomic mass",
                "protons",
                "neutrons"
                ],
                "id": "slide_3_09dff5",
                "order": 3
            },
            {
                "title": "Applications of Atomic and Mass Number",
                "key_terms": [
                "isotopes",
                "atomic structure",
                "chemistry"
                ],
                "id": "slide_4_703696",
                "order": 4
            }
            ],
            "sub_4_78635b": [
            {
                "title": "Introduction to Electron Shells",
                "key_terms": [
                "electron",
                "shell",
                "atom"
                ],
                "id": "slide_1_127355",
                "order": 1
            },
            {
                "title": "Electron Shell Configuration",
                "key_terms": [
                "electron configuration",
                "shell model",
                "energy level"
                ],
                "id": "slide_2_301bcd",
                "order": 2
            },
            {
                "title": "First 20 Elements: Electron Shells",
                "key_terms": [
                "periodic table",
                "electron shell",
                "elements"
                ],
                "id": "slide_3_44aae9",
                "order": 3
            },
            {
                "title": "Applying Electron Shells to Elements",
                "key_terms": [
                "electron configuration",
                "chemical properties",
                "periodicity"
                ],
                "id": "slide_4_7f9ef8",
                "order": 4
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
                "id": "slide_1_609c03",
                "order": 1
            },
            {
                "title": "Formation of Ions",
                "key_terms": [
                "ionization",
                "electron",
                "proton"
                ],
                "id": "slide_2_ba47a4",
                "order": 2
            },
            {
                "title": "Neutral Atoms vs Ions",
                "key_terms": [
                "neutral",
                "ion",
                "stability"
                ],
                "id": "slide_3_d5c448",
                "order": 3
            },
            {
                "title": "Properties of Ions",
                "key_terms": [
                "ionic",
                "compound",
                "reactivity"
                ],
                "id": "slide_4_9768fa",
                "order": 4
            }
            ]
        }
    }

    updated_state = generate_all_narrations(TutorState)
    print(json.dumps(updated_state, indent=2))