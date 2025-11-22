from ..llm.model_loader import load_groq, load_groq_fast, load_openai, load_gemini
from ..state import TutorState
from tavily import TavilyClient
import os
from dotenv import load_dotenv
import json
import re

load_dotenv()
tavily=TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

def clean_json_output(text: str) -> str:
    """
    Remove code fences and extract JSON cleanly from Gemini.
    """
    text = text.strip()

    # Remove ```json or ``` wrappers
    if text.startswith("```"):
        text = text.strip("`")
        # sometimes gemini sends: ```json\n{ ... }\n```
        text = text.replace("json\n", "", 1).replace("json", "", 1).strip()

    # Find the first { and last }
    import re
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return match.group(0)

    # fallback: return text as-is
    return text


def should_use_search(slide, subtopic_name):
    llm = load_groq_fast()  # very cheap model

    prompt = f"""
        Decide if external web search (Tavily) is ABSOLUTELY REQUIRED for generating accurate slide narration.

        Use search ONLY when the slide needs:
        - exact facts (dates, numbers, timelines, stats)
        - historical accuracy (events, inventions, discoveries)
        - version/release information
        - real-world data that must be correct and up-to-date

        Do NOT use search for:
        - concepts, explanations, definitions, principles
        - theories, abstractions, analogies
        - content that can be answered from general knowledge

        If accurate narration is possible WITHOUT verified facts, set needs_search to false.

        Respond with ONLY this JSON (no markdown, no code fences):
        {{
        "needs_search": true/false,
        "query": "short search query or empty string"
        }}
        """


    resp = llm.invoke([{"role": "user", "content": prompt}])
    raw = resp.content

    cleaned = clean_json_output(raw)
    try:
        print(cleaned)
        return json.loads(cleaned)
    except:
        return {"needs_search": False, "query": ""}


def generate_narration_for_slide(slide, subtopic_name, narration_style):
    """Generate narration text for a single slide."""
    llm = load_openai()

    decision = should_use_search(slide, subtopic_name)
    needs_search = decision.get("needs_search", False)
    search_results = ""

    if needs_search:
        query = decision.get("query", "")
        if query.strip():
            try:
                search = tavily.search(query=query, max_results=5)
                search_results = json.dumps(search, ensure_ascii=False)
                print(search_results)
            except:
                search_results = "Search failed."
                
    SYSTEM_PROMPT = f"""
    You are an expert educational content creator and slide narrator for an AI teaching platform.
    {"USE THE FOLLOWING VERIFIED FACTUAL INFORMATION FOR HIGH ACCURACY:\n" + search_results if needs_search else ""}

    🎯 PURPOSE:
    Your task is to transform each educational concept into a **clear, concise, and engaging narration** suitable for use in slides or spoken teaching.
    Each narration should effectively explain **one key idea** using 3–5 logically ordered points that are short, easy to follow, and pedagogically sound.

    🧩 SLIDE NARRATION STRUCTURE:
    Each slide must include:
    1. **title** — A short, clear title derived from the main concept.
    2. **points** — 3 to 5 concise and visually readable points (15–25 words each).

    📚 NARRATION STYLE:
    - The narration must feel like a teacher explaining the concept with natural flow and curiosity.
    - Maintain an educational tone that encourages understanding, not just definition.
    - Avoid robotic, repetitive, or mechanical phrasing.
    - Each point should focus on **one distinct sub-idea** and follow a logical teaching flow:
    curiosity → explanation → insight → takeaway.
    - Use transitions and progression between points where needed.
    - Adapt the narration style based on the user’s preference if provided: {narration_style}

    🎓 TEACHING PRINCIPLES TO FOLLOW:
    - Begin with **what** and **why** before **how** — establish curiosity.
    - Use simple, accessible language that a broad audience can understand.
    - Present information in a **build-up manner** — each point should add depth to the previous one.
    - Ensure points are **self-contained** (each makes sense independently) yet **connected** (they form a coherent mini-lesson).

    ✅ DOs:
    - Do use clear and engaging phrasing (e.g., “Let’s explore how...” / “This helps us understand...”).
    - Do simplify complex ideas into relatable explanations.
    - Do use active voice and educational tone.
    - Do ensure logical sequencing — each point should naturally lead to the next.
    - Do maintain a balanced mix of conceptual and factual points.
    - Do emphasize takeaways or conclusions in the last point.
    - Do use analogy or comparison **only** if it enhances clarity.

    🚫 DON’Ts:
    - Don’t include any visual references (no mention of images, charts, diagrams, etc.).
    - Don’t repeat the same idea across multiple points.
    - Don’t use filler phrases like “In this slide” or “We will learn about”.
    - Don’t use overly technical jargon or definitions straight from textbooks.
    - Don’t write long paragraphs — each point should be a compact educational statement.
    - Don’t include any meta text, formatting, or markdown.

    💡 LENGTH & FORMAT:
    - Total: 3–5 points per slide.
    - Each point: 10–25 words max.
    - Title: concise and clear (4–8 words ideally).
    - Output valid JSON only — no markdown or extra text.

    📏 OUTPUT FORMAT EXAMPLE:
    {{
    "title": "Structure of an Atom",
    "points": [
        "Atoms are the fundamental units that make up all forms of matter.",
        "Each atom contains a central nucleus made of protons and neutrons.",
        "Electrons orbit the nucleus in different energy levels that define the atom’s behavior."
    ]
    }}

    Your role: Create **educationally meaningful, logically structured, and engaging narration** that can later be paired with visuals and voiceovers for AI-powered teaching slides.
    """

    user_prompt = f"""
    Subtopic: {subtopic_name or "General"}
    Slide details:
    {json.dumps(slide, ensure_ascii=False, indent=2)}
    """

    response = llm.invoke(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]
    )

    # Try to safely parse JSON
    try:
        slide_data = json.loads(response.content)
    except Exception:
        import re

        text = str(response)
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            slide_data = json.loads(match.group(0))
        else:
            slide_data = {
                "title": slide.get("title", "Untitled Slide"),
                "points": ["Parsing failed, please retry."]
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
                narration_style=narration_style,  # ✅ Add this line
            )

    state["slides"] = slides_by_subtopic
    return state


if __name__ == "__main__":
    TutorState = {
        "topic": "Computer generations",
        "sub_topics": [
            {
                "name": "Introduction to Computer Generations",
                "difficulty": "Beginner",
                "id": "sub_1_2b67b6",
            },
            {
                "name": "First Generation Computers (1940s-1950s): Vacuum Tubes",
                "difficulty": "Intermediate",
                "id": "sub_2_30755b",
            },
            {
                "name": "Second to Fifth Generation Computers (1950s-1980s): Transistors, Integrated Circuits, and Microprocessors",
                "difficulty": "Intermediate",
                "id": "sub_3_d87eaf",
            },
            {
                "name": "Modern Computer Generations (1980s-present): Artificial Intelligence, Internet, and Beyond",
                "difficulty": "Advanced",
                "id": "sub_4_c8e0dd",
            },
            {
                "name": "Comparison and Evolution of Computer Generations",
                "difficulty": "Intermediate",
                "id": "sub_5_dca7e2",
            },
        ],
        "slides": {
            "sub_1_2b67b6": [
                {
                    "title": "Intro to Comp Generations",
                    "key_terms": ["computer", "generation", "history"],
                    "id": "slide_1_cf42b9",
                    "order": 1,
                },
                {
                    "title": "First Generation Computers",
                    "key_terms": ["vacuum tube", "eniac", "1940s"],
                    "id": "slide_2_17fab4",
                    "order": 2,
                },
                {
                    "title": "Second to Third Gen Computers",
                    "key_terms": ["transistor", "ic", "mainframe"],
                    "id": "slide_3_3d214e",
                    "order": 3,
                },
                {
                    "title": "Modern Computer Generations",
                    "key_terms": ["microprocessor", "pc", "ai"],
                    "id": "slide_4_2c77d4",
                    "order": 4,
                },
            ],
            "sub_2_30755b": [
                {
                    "title": "Intro to First Gen Computers",
                    "key_terms": [
                        "vacuum tube",
                        "first generation",
                        "computer history",
                    ],
                    "id": "slide_1_79aa21",
                    "order": 1,
                },
                {
                    "title": "Vacuum Tube Basics",
                    "key_terms": ["vacuum tube", "electronic switch", "amplifier"],
                    "id": "slide_2_d01730",
                    "order": 2,
                },
                {
                    "title": "ENIAC and Vacuum Tubes",
                    "key_terms": [
                        "ENIAC",
                        "vacuum tube computer",
                        "electronic numerical integrator",
                    ],
                    "id": "slide_3_69c986",
                    "order": 3,
                },
                {
                    "title": "Limitations of Vacuum Tubes",
                    "key_terms": [
                        "heat generation",
                        "reliability issues",
                        "maintenance challenges",
                    ],
                    "id": "slide_4_fb67e4",
                    "order": 4,
                },
            ],
            "sub_3_d87eaf": [
                {
                    "title": "Intro to 2nd Gen Computers",
                    "key_terms": ["transistor", "computer", "generation"],
                    "id": "slide_1_1aa180",
                    "order": 1,
                },
                {
                    "title": "Integrated Circuits",
                    "key_terms": ["IC", "circuit", "silicon"],
                    "id": "slide_2_80a056",
                    "order": 2,
                },
                {
                    "title": "Microprocessors Emergence",
                    "key_terms": ["microprocessor", "CPU", "chip"],
                    "id": "slide_3_cef665",
                    "order": 3,
                },
                {
                    "title": "4th Gen Computers Overview",
                    "key_terms": ["personal", "computer", "microcomputer"],
                    "id": "slide_4_46b1c0",
                    "order": 4,
                },
                {
                    "title": "5th Gen Computers Advances",
                    "key_terms": ["AI", "parallel", "processing"],
                    "id": "slide_5_6056ac",
                    "order": 5,
                },
                {
                    "title": "Comparison of Generations",
                    "key_terms": ["generation", "comparison", "evolution"],
                    "id": "slide_6_f19c18",
                    "order": 6,
                },
            ],
            "sub_4_c8e0dd": [
                {
                    "title": "Intro to Modern Computers",
                    "key_terms": ["microprocessor", "personal computer", "revolution"],
                    "id": "slide_1_4b161e",
                    "order": 1,
                },
                {
                    "title": "Artificial Intelligence Basics",
                    "key_terms": ["AI", "machine learning", "neural networks"],
                    "id": "slide_2_972354",
                    "order": 2,
                },
                {
                    "title": "Internet and Networking",
                    "key_terms": ["internet", "world wide web", "connectivity"],
                    "id": "slide_3_c110de",
                    "order": 3,
                },
                {
                    "title": "Cloud Computing and Beyond",
                    "key_terms": ["cloud", "big data", "IoT"],
                    "id": "slide_4_2302fc",
                    "order": 4,
                },
            ],
            "sub_5_dca7e2": [
                {
                    "title": "Introduction to Computer Generations",
                    "key_terms": ["computer", "generation", "evolution"],
                    "id": "slide_1_e682ab",
                    "order": 1,
                },
                {
                    "title": "First Generation Computers",
                    "key_terms": ["vacuum tube", "ENIAC", "1940s"],
                    "id": "slide_2_ebadde",
                    "order": 2,
                },
                {
                    "title": "Second to Fourth Generations",
                    "key_terms": ["transistor", "microprocessor", "mainframe"],
                    "id": "slide_3_9feef4",
                    "order": 3,
                },
                {
                    "title": "Fifth Generation and Beyond",
                    "key_terms": ["AI", "parallel processing", "nanotechnology"],
                    "id": "slide_4_690af8",
                    "order": 4,
                },
                {
                    "title": "Comparison of Computer Generations",
                    "key_terms": ["performance", "size", "cost"],
                    "id": "slide_5_a4610d",
                    "order": 5,
                },
                {
                    "title": "Impact of Evolution on Society",
                    "key_terms": ["technology", "innovation", "globalization"],
                    "id": "slide_6_55d941",
                    "order": 6,
                },
            ],
        },
    }

    updated_state = generate_all_narrations(TutorState)
    print(json.dumps(updated_state, indent=2))
