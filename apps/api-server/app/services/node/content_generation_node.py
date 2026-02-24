"""
Content Generation Node (Enhanced with Tavily)

Generates structured visual content that matches both:
1. Blueprint requirements (template structure)
2. Narration structure (number of points/paragraphs)
3. Verified facts from Tavily when needed

Flow:
- Input: Slide with blueprint metadata + narration text
- Output: Structured content ready for rendering (fact-checked)
"""

import json
import re
from typing import Dict, Any, List
import os
import sys  # Need this for all path manipulations
from dotenv import load_dotenv
from tavily import TavilyClient

try:
    from ..llm.model_loader import load_groq, load_groq_fast, load_openai, load_gemini
    from ..state import TutorState
except ImportError:
    # Fallback for direct script execution
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from llm.model_loader import load_groq, load_groq_fast, load_openai, load_gemini
    from state import TutorState

# Import segment counting for narration↔content alignment
try:
    from .audio_generation_node import segment_narration
except ImportError:
    from audio_generation_node import segment_narration

# Import icon selector
try:
    from ..icon_selector import select_icons_batch
    from .slides.gyml.generator import GyMLContentGenerator
except ImportError:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from icon_selector import select_icons_batch
    from services.node.slides.gyml.generator import GyMLContentGenerator

load_dotenv()
tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

# Initialize generator
gyml_generator = GyMLContentGenerator()


# ═══════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════


def should_fact_check(slide_title: str, slide_purpose: str, subtopic_name: str) -> bool:
    """Determines if this slide needs Tavily fact-checking."""
    fact_check_keywords = [
        "generation",
        "history",
        "timeline",
        "evolution",
        "year",
        "date",
        "version",
        "release",
        "statistics",
        "data",
        "percentage",
        "number",
        "event",
        "discovery",
        "invention",
        "founder",
        "origin",
    ]

    combined = f"{slide_title} {slide_purpose} {subtopic_name}".lower()
    return any(keyword in combined for keyword in fact_check_keywords)


def load_llm_schema() -> str:
    """Load the LLM content schema."""
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        schema_path = os.path.join(current_dir, "slides", "gyml", "llm_schema.json")
        with open(schema_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"   ⚠ Failed to load LLM schema: {e}")
        return "{}"


def generate_narration(
    title: str, goal: str, role: str, subtopic_name: str, context: str = ""
) -> str:
    """Generates the spoken narration for a slide."""
    llm = load_openai()

    prompt = f"""
    You are an expert teacher. Write the spoken narration for a slide.
    
    CONTEXT:
    - Subtopic: {subtopic_name}
    - Slide Title: {title}
    - Slide Goal: {goal}
    - Teacher Role: {role}
    {f"📚 RESEARCH CONTEXT:\n{context}" if context else ""}
    
    STRUCTURE RULES:
    1. Provide 3-5 distinct teaching points.
    2. Use clear transition markers to separate these points so they can be animated:
       - Start the first point with "First,"
       - Start the second point with "Second,"
       - Start the third point with "Third,"
       - And so on...
    3. Each point should be 25-40 words long.
    4. Total length MUST be 120-180 words.

    CONTENT RULES:
    1. Write exactly what the teacher would say.
    2. Be engaging, clear, and pedagogically sound.
    3. NO markdown, NO "In this slide", NO "Moving on".
    4. Your narration EXPLAINS what the student sees on screen.
       The slide will show short labels, card headings, and brief summaries.
       Your job is to ELABORATE with deeper context, examples, real-world
       connections, and analogies that are NOT written on screen.
       Do NOT just read out what the slide says — add value beyond the visuals.
    """

    resp = llm.invoke([{"role": "user", "content": prompt}])
    return resp.content.strip()


# ═══════════════════════════════════════════════════════════════════════════
# CORE GENERATION LOGIC
# ═══════════════════════════════════════════════════════════════════════════


def content_generation_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Incremental Content Generation Node (Batch of 2).
    Generates at most BATCH_SIZE slides per invocation, across subtopics.
    """
    BATCH_SIZE = 2

    sub_topics = state.get("sub_topics", [])
    difficulty = state.get("difficulty", "Beginner")
    plans = state.get("plans", {})

    if "slides" not in state:
        state["slides"] = {}
    if "layout_history" not in state:
        state["layout_history"] = []

    # ── Find the next subtopic + slide offset to generate ────────────
    # We look for the first subtopic where len(generated slides) < len(planned slides).
    next_subtopic = None
    start_offset = 0

    for sub in sub_topics:
        sub_id = sub["id"]
        planned_count = len(plans.get(sub_id, []))
        generated_count = len(state["slides"].get(sub_id, []))
        if generated_count < planned_count:
            next_subtopic = sub
            start_offset = generated_count
            break

    if not next_subtopic:
        print("✅ [Content Gen] All slides already have content.")
        return state

    sub_id = next_subtopic.get("id")
    subtopic_name = next_subtopic.get("name")
    sub_difficulty = next_subtopic.get("difficulty", difficulty)

    slide_concepts = plans.get(sub_id, [])

    # Initialize slides list for this subtopic if needed
    if sub_id not in state["slides"]:
        state["slides"][sub_id] = []

    # Determine batch range
    end_offset = min(start_offset + BATCH_SIZE, len(slide_concepts))

    print(
        f"\n🎬 [Batch Gen] Subtopic: {subtopic_name} | Slides {start_offset + 1}-{end_offset} of {len(slide_concepts)}"
    )
    layout_history = state["layout_history"]

    for i in range(start_offset, end_offset):
        concept = slide_concepts[i]
        title = concept.get("title")
        goal = concept.get("goal")

        print(f"  📝 Generating Slide {i + 1}: {title}")

        # 1. Fact Check if needed
        search_context = ""
        if should_fact_check(title, "explanation", subtopic_name):
            try:
                search_query = f"{subtopic_name} {title} verified facts and details"
                search_results = tavily.search(query=search_query, max_results=3)
                search_context = json.dumps(search_results.get("results", []), indent=2)
            except Exception as e:
                print(f"    ⚠ Search failed: {e}")

        # 2. Generate Narration
        role = concept.get("role", "Teacher")
        narration = generate_narration(title, goal, role, subtopic_name, search_context)

        # 3. Count narration segments for content alignment
        segments = segment_narration(narration, "points")
        point_count = len(segments)
        print(f"    → Narration: {point_count} segment(s)")

        # 4. Generate GyML JSON
        generated_content = gyml_generator.generate(
            narration=narration,
            title=title,
            purpose=concept.get("purpose", "explain"),
            subtopic=subtopic_name,
            context=search_context,
            point_count=point_count,
            layout_history=layout_history,
        )

        # Update layout history
        blocks = generated_content.get("contentBlocks", [])
        smart_layout = next(
            (b for b in blocks if b.get("type") == "smart_layout"), None
        )
        if smart_layout:
            layout_history.append(smart_layout.get("variant", "unknown"))
        else:
            layout_history.append(generated_content.get("intent", "explain"))

        if len(layout_history) > 10:  # Keep a longer history for better variety
            layout_history.pop(0)

        state["layout_history"] = layout_history

        # 5. Store
        slide_obj = {
            **concept,
            "subtopic_name": subtopic_name,
            "narration_text": narration,
            "gyml_content": generated_content,
            "visual_content": generated_content,
        }
        state["slides"][sub_id].append(slide_obj)

    return state
