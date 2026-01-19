try:
    from ..llm.model_loader import load_groq, load_groq_fast, load_openai, load_gemini
    from ..state import TutorState
except ImportError:
    # Fallback for direct script execution
    import sys
    import os

    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from llm.model_loader import load_groq, load_groq_fast, load_openai, load_gemini
    from state import TutorState
from tavily import TavilyClient
import os
from dotenv import load_dotenv
import json
import re

load_dotenv()
tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))


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


def generate_narration_for_slide(
    slide, subtopic_name, narration_style, difficulty_level
):
    """Generate spoken narration text for a single slide based on planning metadata."""
    llm = load_openai()

    # Tavily Search Logic
    decision = should_use_search(slide, subtopic_name)
    needs_search = decision.get("needs_search", False)
    search_results = ""

    if needs_search:
        query = decision.get("query", "")
        if query.strip():
            try:
                search = tavily.search(query=query, max_results=5)
                search_results = json.dumps(search, ensure_ascii=False)
            except:
                search_results = "Search failed."

    # Extract Metadata
    narration_role = slide.get("narration_role", "Introduce")
    narration_goal = slide.get("narration_goal", "Explain the concept clearly.")
    selected_template = slide.get("selected_template", "Generic")
    slide_purpose = slide.get("slide_purpose", "Definition")
    slide_title = slide.get("slide_title", "Untitled Slide")

    SYSTEM_PROMPT = f"""
    You are an expert teacher. Your task is to provide a **spoken narration** for an educational slide.
    
    🎯 CONTEXT:
    - Subtopic: {subtopic_name}
    - Slide Title: {slide_title}
    - Slide Purpose: {slide_purpose}
    - Narration Role: {narration_role}
    - Narration Goal: {narration_goal}
    - Selected Template: {selected_template}
    - Difficulty Level: {difficulty_level}
    - Narration Style (User Preference): {narration_style}
    
    {"🔍 VERIFIED FACTS (Use these for accuracy):\n" + search_results if needs_search else ""}

    🧩 NARRATION RULES:
    1. **Spoken Only**: Write exactly what the teacher would say. Do NOT write bullet points or slide text.
    2. **Length**: 2–4 natural sentences (approx 40–80 words).
    3. **Role-Driven**:
       - 'Introduce': Set the hook, explain why this matters, and define the scope.
       - 'Interpret': Explain the relationships or the 'why' behind what is shown.
       - 'Guide': Lead the learner through a sequence or logical flow.
       - 'Contrast': Highlight differences, pros/cons, or trade-offs.
       - 'Reinforce': Tie it all together and cement the key takeaway.
    4. **Template Aware**: Assume the visual structure (e.g., a {selected_template}) is already on screen. Do NOT describe the layout (e.g., don't say 'On the left we see...'). Instead, explain the logic of the content.
    5. **Style & Difficulty**: Strictly follow the style '{narration_style}' and ensure the complexity matches '{difficulty_level}'.
    
    � DON'Ts:
    - Do NOT say "In this slide" or "Moving on to...".
    - Do NOT use markdown formatting.
    - Do NOT repeat the slide title.

    OUTPUT FORMAT:
    Output ONLY valid JSON:
    {{
      "slide_title": "{slide_title}",
      "narration_text": "The spoken script..."
    }}
    """

    user_prompt = f"Generate narration for the slide: '{slide_title}'."

    response = llm.invoke(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]
    )

    try:
        cleaned = clean_json_output(response.content)
        return json.loads(cleaned)
    except Exception:
        return {
            "slide_title": slide_title,
            "narration_text": "I'll explain this concept simply: " + narration_goal,
        }


def generate_all_narrations(state: TutorState):
    """Processes the slide_plan to generate spoken narrations for every slide."""
    slide_plan = state.get("slide_plan", {})
    narration_style = state.get(
        "narration_style", "Clear and engaging educational style"
    )

    # We will store final slide objects in state["slides"]
    if "slides" not in state or not isinstance(state["slides"], dict):
        state["slides"] = {}

    for sub_id, plan_entry in slide_plan.items():
        subtopic_name = plan_entry.get("subtopic_name")
        planned_slides = plan_entry.get("slides", [])
        difficulty = state.get("difficulty", "Beginner")  # Overall course difficulty

        generated_slides = []
        for slide_meta in planned_slides:
            print(f"Generating narration for: {slide_meta.get('slide_title')}...")
            narration_data = generate_narration_for_slide(
                slide=slide_meta,
                subtopic_name=subtopic_name,
                narration_style=narration_style,
                difficulty_level=difficulty,
            )

            # Combine planning metadata with generated narration
            final_slide = {**slide_meta, **narration_data}
            generated_slides.append(final_slide)

        state["slides"][sub_id] = generated_slides

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
    }

    updated_state = generate_all_narrations(SampleState)
    print(json.dumps(updated_state, indent=2))
