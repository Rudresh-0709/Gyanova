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


# ═══════════════════════════════════════════════════════════════════════════
# CORE GENERATION LOGIC
# ═══════════════════════════════════════════════════════════════════════════


def plan_slides_for_subtopic(
    subtopic_name: str, difficulty: str
) -> List[Dict[str, str]]:
    """Plans 3-5 slide concepts (titles/goals) for a subtopic without templates."""
    llm = load_openai()

    prompt = f"""
    You are an AI Curriculum Planner. Plan a series of 3-5 slides for the subtopic: '{subtopic_name}'.
    Difficulty: {difficulty}
    
    For each slide, provide a 'title' and a 'goal' (what the student should learn).
    Ensure logical progression and high educational value.
    DO NOT mention layouts or templates.

    Output ONLY valid JSON:
    {{
        "slides": [
            {{"title": "...", "goal": "..."}},
            ...
        ]
    }}
    """

    resp = llm.invoke([{"role": "user", "content": prompt}])
    try:
        content = resp.content.replace("```json", "").replace("```", "").strip()
        return json.loads(content).get("slides", [])
    except:
        return [
            {"title": subtopic_name, "goal": f"Master the basics of {subtopic_name}."}
        ]


def generate_narration(
    slide_title: str, slide_goal: str, subtopic_name: str, context: str = ""
) -> str:
    """Generates the spoken narration for a slide."""
    llm = load_openai()

    prompt = f"""
    You are an expert teacher. Write the spoken narration for a slide.
    
    CONTEXT:
    - Subtopic: {subtopic_name}
    - Slide Title: {slide_title}
    - Slide Goal: {slide_goal}
    {f"📚 RESEARCH CONTEXT:\n{context}" if context else ""}
    
    RULES:
    1. Write exactly what the teacher would say.
    2. Be engaging, clear, and pedagogically sound.
    3. 120-180 words.
    4. NO markdown, NO "In this slide", NO "Moving on".
    """

    resp = llm.invoke([{"role": "user", "content": prompt}])
    return resp.content.strip()


def content_generation_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    New Structured Content Node.
    Iterates over subtopics and their slide concepts to generate:
    1. Narration
    2. GyML JSON
    """
    sub_topics = state.get("sub_topics", [])
    difficulty = state.get("difficulty", "Beginner")

    if "slides" not in state:
        state["slides"] = {}

    for subtopic in sub_topics:
        sub_id = subtopic.get("id")
        subtopic_name = subtopic.get("name")
        sub_difficulty = subtopic.get("difficulty", difficulty)

        print(f"\n🎬 Planning and Generating for Subtopic: {subtopic_name}")

        # Step 1: Internal Planning (Subtopics from sub_topic_node don't have slides)
        slide_concepts = plan_slides_for_subtopic(subtopic_name, sub_difficulty)

        state["slides"][sub_id] = []

        for i, concept in enumerate(slide_concepts, start=1):
            title = concept.get("title")
            goal = concept.get("goal")

            print(f"  📝 Generating Slide {i}: {title}")

            # 1. Fact Check if needed
            search_context = ""
            if should_fact_check(title, "explanation", subtopic_name):
                try:
                    search_query = f"{subtopic_name} {title} verified facts and details"
                    search_results = tavily.search(query=search_query, max_results=3)
                    search_context = json.dumps(
                        search_results.get("results", []), indent=2
                    )
                except Exception as e:
                    print(f"    ⚠ Search failed: {e}")

            # 2. Generate Narration
            narration = generate_narration(title, goal, subtopic_name, search_context)

            # 3. Generate GyML JSON
            generated_content = gyml_generator.generate(
                narration=narration,
                title=title,
                purpose="explain",  # Default purpose
                subtopic=subtopic_name,
                context=search_context,
            )

            # 4. Store
            slide_obj = {
                **concept,
                "subtopic_name": subtopic_name,
                "narration_text": narration,
                "gyml_content": generated_content,
                "visual_content": generated_content,  # Compatibility
            }
            state["slides"][sub_id].append(slide_obj)

            print(
                f"    → Generated {len(generated_content.get('contentBlocks', []))} blocks"
            )

    return state
