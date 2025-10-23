from ..llm.model_loader import load_groq, load_groq_fast, load_openai, load_gemini
from ..state import TutorState
import json
import re

def generate_narration_for_slide(slide, subtopic_name, narration_style):
    """Generate narration text for a single slide."""
    llm = load_openai()

    SYSTEM_PROMPT = f"""
        You are an expert educational slide designer and content creator for an AI teaching platform.

        Your task is to transform each educational concept into a **visually balanced slide**, 
        combining **short, clear point-form narration** with an appropriate **image type and layout template**.

        🎯 PURPOSE:
        Create slide data that can later be converted into both narration and HTML slides.
        Each slide should explain **one key idea** clearly and visually.

        🧩 SLIDE STRUCTURE:
        Each slide must include:
        1. **title** — short and clear (derived from the main concept)
        2. **points** — 3 to 5 concise and visually readable points (15–25 words each)
        3. **template** — choose from ["image_right", "image_left", "image_full", "text_only", "split_horizontal"], try to keep the template different for each slide.
        4. **imageType** — choose from ["ai_image", "ai_enhanced_image", "chart_diagram"]
        - Use:
            - `ai_image` for creative or everyday scenes.
            - `ai_enhanced_image` for precise and majority of images.
            - `chart_diagram` for visualizable data or structured explanations (e.g. comparisons, hierarchies)
        5. **imagePrompt** — concise and descriptive prompt describing what the image should contain.

        📚 CONTENT STYLE:
        - Write in **point format**, suitable for slide display.
        - Focus on clarity, brevity, and logical sequencing.
        - Do not write long paragraphs.
        - Avoid jargon-heavy or overly scientific wording — make it visually scannable.
        - Each point should introduce **one clear sub-idea**.
        - Maintain a natural teaching flow from curiosity → concept → conclusion.

        🎨 VISUAL VARIETY RULE:
        - Randomize or intuitively vary template layouts across slides to keep visuals engaging.
        - Ensure slide structure complements the concept (e.g., image on side for processes, full image for diagrams).

        📏 OUTPUT FORMAT:
        Return valid JSON only — no markdown or extra text.
        Example:
        {{
        "title": "Structure of an Atom",
        "points": [
            "Atoms are the smallest units of all matter.",
            "Each atom has a nucleus made of protons and neutrons.",
            "Electrons orbit around the nucleus in energy levels."
        ],
        "template": "image_right",
        "imageType": "ai_enhanced_image",
        "imagePrompt": "detailed labeled diagram of an atom showing nucleus and orbiting electrons"
        }}

        💡 LENGTH:
        - 3–5 points per slide.
        - Each point: 10–20 words max.

        Avoid:
        - Long explanations or paragraphs.
        - Phrases like “In this slide” or “We will learn”.
        - Repetitive sentence structures.

        Your role: Create **educationally meaningful, visually diverse slides** that can be directly converted to both narration and HTML visuals.
        """


    user_prompt = f"""
    Subtopic: {subtopic_name or "General"}
    Slide details:
    {json.dumps(slide, ensure_ascii=False, indent=2)}
    """

    response = llm.invoke([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt}
    ])

    # Try to safely parse JSON
    try:
        slide_data = json.loads(response.content)
    except Exception:
        import re
        text = str(response)
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            slide_data = json.loads(match.group(0))
        else:
            slide_data = {
                "title": slide.get("title", "Untitled Slide"),
                "points": ["Parsing failed, please retry."],
                "template": "image_right",
                "imageType": "ai_enhanced_image",
                "imagePrompt": "no image"
            }

    return slide_data


def generate_all_narrations(state):
    slides_by_subtopic = state.get("slides", {})
    narration_style = state.get("narration_style", "default educational style")

    for sub_id, slide_list in slides_by_subtopic.items():
        for i, slide in enumerate(slide_list):
            slides_by_subtopic[sub_id][i] = generate_narration_for_slide(
                slide=slide,
                subtopic_name=sub_id,
                narration_style=narration_style   # ✅ Add this line
            )

    state["slides"] = slides_by_subtopic
    return state





if __name__ == "__main__":
    TutorState = {
        "topic": "Computer generations",
        "narration_style":"Teach like you are explaining it to a 7 year old, give analogies and examples.",
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