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
except ImportError:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from icon_selector import select_icons_batch

load_dotenv()
tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))


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


def generate_slide_content(
    narration_text: str,
    slide_title: str,
    slide_purpose: str,
    subtopic_name: str,
    blueprint_hint: str = "",
    constraints: Dict = None,
) -> Dict[str, Any]:
    """
    Unified generation function using the Expanded Content Schema.

    Flow:
    1. Check if fact-checking is needed (Tavily).
    2. Load JSON Schema.
    3. Prompt LLM to generate valid JSON matching schema.
    4. Return structured content.
    """
    llm = load_openai()
    schema_json = load_llm_schema()
    constraints = constraints or {}

    # 1. Fact Checking
    search_context = ""
    if should_fact_check(slide_title, slide_purpose, subtopic_name):
        try:
            search_query = f"{subtopic_name} {slide_title} facts details"
            print(f"   🔍 Fact-checking: {search_query[:50]}...")
            search_results = tavily.search(query=search_query, max_results=3)
            search_context = f"\\n\\n📚 VERIFIED CONTEXT (Use these facts):\\n{json.dumps(search_results.get('results', []), indent=2)}\\n"
        except Exception as e:
            print(f"   ⚠ Tavily search failed: {e}")

    # 2. Construct Prompt
    PROMPT = f"""
    You are an expert educational content designer.
    Your task is to convert the Teacher's Narration into a structured visual slide.

    SLIDE CONTEXT:
    - Title: {slide_title}
    - Purpose: {slide_purpose}
    - Blueprint Hint: {blueprint_hint} (Use this to guide your layout choice)
    - Narration: {narration_text}

    {search_context}

    STRICT OUTPUT SCHEMA (JSON ONLY):
    {schema_json}

    INSTRUCTIONS:
    1. Analyze the narration to determine the best 'intent' and 'contentBlocks'.
    2. RICH CONTENT RULE: Most slides should have multiple blocks.
       - A slide with just a Timeline or just a Table is boring.
       - ALWAYS include a short introductory 'paragraph' block before complex blocks (Timeline, Code, Table) to provide context.
    3. If the Blueprint Hint suggests a structure (e.g. TIMELINE_STEPS -> timeline), use it as the PRIMARY block.
    4. If the hint is generic (BULLET_POINTS), you may choose a better visualization (e.g. card_grid, step_list).
    5. Ensure all content is FACTUALLY ACCURATE using the provided Context.
    6. Output MUST be valid JSON matching the schema exactly.
    """

    try:
        response = llm.invoke([{"role": "user", "content": PROMPT}])
        content = response.content.replace("```json", "").replace("```", "").strip()
        result = json.loads(content)

        # Post-processing: Add specific icons if needed (optional, can be done by Composer/Renderer)
        # For now, we trust the LLM or let the Composer handle defaults.

        return result

    except Exception as e:
        print(f"   ❌ Content generation failed: {e}")
        # Fallback to simple bullet list
        return {
            "title": slide_title,
            "intent": "explain",
            "contentBlocks": [
                {
                    "type": "bullet_list",
                    "items": ["Content generation failed.", "Please review narration."],
                }
            ],
        }


def content_generation_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main content generation node.
    Reads narration + blueprint metadata and generates structured visual content.
    Uses Tavily for fact-checking when dealing with historical/technical content.
    """
    slides = state.get("slides", {})

    for sub_id, slide_list in slides.items():
        for slide in slide_list:
            narration_text = slide.get("narration_text", "")
            blueprint_type = slide.get("content_type", "")  # Use as hint
            constraints = slide.get("narration_constraints", {})

            slide_title = slide.get("slide_title", "")
            slide_purpose = slide.get("slide_purpose", "")
            subtopic_name = slide.get("subtopic_name", "")

            print(f"📝 Generating content for: {slide_title} [Hint: {blueprint_type}]")

            # Unified Generation
            generated_content = generate_slide_content(
                narration_text=narration_text,
                slide_title=slide_title,
                slide_purpose=slide_purpose,
                subtopic_name=subtopic_name,
                blueprint_hint=blueprint_type,
                constraints=constraints,
            )

            # Store the structured content
            # We store it in 'gyml_content' to distinguish from legacy 'visual_content'
            slide["gyml_content"] = generated_content

            # For backward compatibility / debugging
            slide["visual_content"] = generated_content

            print(
                f"   → Generated {len(generated_content.get('contentBlocks', []))} blocks"
            )

    state["slides"] = slides
    return state
