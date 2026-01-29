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


def generate_bullet_content(
    narration_text: str,
    point_count_range: List[int],
    slide_title: str,
    slide_purpose: str,
    subtopic_name: str = "",
) -> List[Dict[str, str]]:
    """
    Generates structured bullet point content from narration.
    Each bullet has: icon, heading, description text.
    Uses Tavily for factual verification when dealing with historical/technical content.
    """
    llm = load_openai()

    min_points, max_points = point_count_range

    # ⭐ Tavily Search for Factual Accuracy
    search_context = ""
    if should_fact_check(slide_title, slide_purpose, subtopic_name):
        try:
            search_query = f"{subtopic_name} {slide_title} accurate facts details"
            print(f"   🔍 Fact-checking with Tavily: {search_query[:50]}...")
            search_results = tavily.search(query=search_query, max_results=3)
            search_context = f"\n\n📚 VERIFIED FACTS (Use these for accuracy):\n{json.dumps(search_results.get('results', []), indent=2)}\n"
        except Exception as e:
            print(f"   ⚠ Tavily search failed: {e}")
            search_context = ""

    PROMPT = f"""
    You are generating visual bullet point content for an educational slide.
    
    SLIDE CONTEXT:
    - Title: {slide_title}
    - Purpose: {slide_purpose}
    - Subtopic: {subtopic_name}
    - Required: {min_points}-{max_points} bullet points
    
    NARRATION TEXT (Teacher's spoken script):
    {narration_text}
    {search_context}
    
    YOUR TASK:
    Extract {min_points}-{max_points} distinct teaching points from the narration and structure them as bullet cards.
    
    ⚠️ CRITICAL - FACTUAL ACCURACY:
    - If VERIFIED FACTS are provided above, YOU MUST use them for dates, numbers, names, and technical details
    - DO NOT make up facts, dates, or statistics
    - If unsure about a specific detail, use general accurate descriptions
    - Accuracy is ABSOLUTELY CRITICAL for this educational content
    
    Each bullet card must have:
    1. **Heading** - Bold, concise title (3-6 words)
    2. **Description** - 1-2 sentence explanation (12-20 words)
    
    NOTE: Icons will be automatically selected based on semantic meaning, so focus on clear headings.
    
    OUTPUT RULES:
    - Output EXACTLY {min_points} to {max_points} bullets
    - Each bullet must be a standalone, complete idea
    - Descriptions should be concise but informative
    - Icons should be semantically meaningful
    - USE VERIFIED FACTS when available - accuracy is paramount
    
    OUTPUT FORMAT (JSON only):
    {{
      "bullets": [
        {{
          "heading": "Concise Title",
          "description": "Brief explanation of this point in 1-2 sentences."
        }}
      ]
    }}
    """

    try:
        response = llm.invoke([{"role": "user", "content": PROMPT}])
        content = response.content.replace("```json", "").replace("```", "").strip()
        result = json.loads(content)

        bullets = result.get("bullets", [])

        # ⭐ USE ICON SELECTOR - Intelligently select icons based on content
        print(f"   🎨 Selecting icons for {len(bullets)} bullets...")
        selected_icons = select_icons_batch(
            items=bullets,
            context={
                "slide_title": slide_title,
                "slide_purpose": slide_purpose,
                "subtopic_name": subtopic_name,
            },
        )

        # Add icons to bullets
        for i, bullet in enumerate(bullets):
            bullet["icon"] = (
                selected_icons[i] if i < len(selected_icons) else "ri-circle-line"
            )

        # Validate count
        if min_points <= len(bullets) <= max_points:
            return bullets
        else:
            print(
                f"   ⚠ Generated {len(bullets)} bullets, expected {min_points}-{max_points}"
            )
            # Trim or pad to fit range
            if len(bullets) < min_points:
                return bullets + [
                    {
                        "icon": "ri-circle-line",
                        "heading": "Additional Point",
                        "description": "Placeholder",
                    }
                ] * (min_points - len(bullets))
            else:
                return bullets[:max_points]

    except Exception as e:
        print(f"   ❌ Bullet generation failed: {e}")
        # Fallback: create generic bullets
        return [
            {
                "icon": "ri-circle-line",
                "heading": f"Point {i+1}",
                "description": "Content extraction failed. Manual review needed.",
            }
            for i in range(min_points)
        ]


def generate_column_content(
    narration_text: str, column_count: int, slide_title: str
) -> List[Dict[str, str]]:
    """
    Generates content for column-based layouts (two/three/four columns).
    Each column has: title, text content.
    """
    llm = load_openai()

    PROMPT = f"""
    Generate content for a {column_count}-column slide layout.
    
    SLIDE TITLE: {slide_title}
    NARRATION: {narration_text}
    
    Extract {column_count} distinct concepts/categories from the narration.
    
    Each column should have:
    - **Column Title**: 2-4 words
    - **Text**: 40-60 words of explanation
    
    OUTPUT FORMAT (JSON):
    {{
      "columns": [
        {{
          "title": "Column Title",
          "text": "Explanation text for this column..."
        }}
      ]
    }}
    """

    try:
        response = llm.invoke([{"role": "user", "content": PROMPT}])
        content = response.content.replace("```json", "").replace("```", "").strip()
        result = json.loads(content)
        return result.get("columns", [])[:column_count]
    except:
        return [
            {"title": f"Column {i+1}", "text": "Content generation failed"}
            for i in range(column_count)
        ]


def generate_timeline_content(
    narration_text: str,
    item_count_range: List[int],
    slide_title: str,
    subtopic_name: str = "",
) -> List[Dict[str, str]]:
    """
    Generates timeline items from sequential narration.
    Each item has: phase_title, description.
    Uses Tavily for historical accuracy.
    """
    llm = load_openai()

    min_items, max_items = item_count_range

    # Timelines often need accurate dates
    search_context = ""
    if should_fact_check(slide_title, "", subtopic_name):
        try:
            search_query = f"{subtopic_name} {slide_title} timeline chronology dates"
            print(f"   🔍 Verifying timeline with Tavily...")
            search_results = tavily.search(query=search_query, max_results=3)
            search_context = f"\n\n📚 VERIFIED TIMELINE FACTS:\n{json.dumps(search_results.get('results', []), indent=2)}\n"
        except:
            pass

    PROMPT = f"""
    Generate timeline content for a chronological slide.
    
    SLIDE TITLE: {slide_title}
    NARRATION: {narration_text}
    {search_context}
    REQUIRED: {min_items}-{max_items} timeline items
    
    ⚠️ ACCURACY CRITICAL: Use verified facts for dates and events. Do not fabricate dates.
    
    Each timeline item should have:
    - **Phase Title**: Short label (e.g., "Phase 1: Planning", "1940s-1950s")
    - **Description**: 3-5 sentences explaining this stage
    
    OUTPUT FORMAT (JSON):
    {{
      "timeline_items": [
        {{
          "phase_title": "Phase Title",
          "description": "Detailed explanation..."
        }}
      ]
    }}
    """

    try:
        response = llm.invoke([{"role": "user", "content": PROMPT}])
        content = response.content.replace("```json", "").replace("```", "").strip()
        result = json.loads(content)
        items = result.get("timeline_items", [])
        return items[:max_items]
    except:
        return [
            {"phase_title": f"Step {i+1}", "description": "Content unavailable"}
            for i in range(min_items)
        ]


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
            content_type = slide.get("content_type", "")
            narration_format = slide.get("narration_format", "points")
            constraints = slide.get("narration_constraints", {})

            slide_title = slide.get("slide_title", "")
            slide_purpose = slide.get("slide_purpose", "")
            subtopic_name = slide.get("subtopic_name", "")

            print(f"📝 Generating content for: {slide_title} [{content_type}]")

            # Generate content based on content type
            if content_type == "BULLET_POINTS":
                point_count = constraints.get("point_count", [4, 6])
                bullets = generate_bullet_content(
                    narration_text=narration_text,
                    point_count_range=point_count,
                    slide_title=slide_title,
                    slide_purpose=slide_purpose,
                    subtopic_name=subtopic_name,
                )
                slide["visual_content"] = {"bullets": bullets}
                print(f"   → Generated {len(bullets)} bullets")

            elif content_type in [
                "TWO_COLUMN_TEXT",
                "THREE_COLUMN_CARDS",
                "FOUR_COLUMN_CARDS",
            ]:
                column_count = {
                    "TWO_COLUMN_TEXT": 2,
                    "THREE_COLUMN_CARDS": 3,
                    "FOUR_COLUMN_CARDS": 4,
                }[content_type]
                columns = generate_column_content(
                    narration_text=narration_text,
                    column_count=column_count,
                    slide_title=slide_title,
                )
                slide["visual_content"] = {"columns": columns}
                print(f"   → Generated {len(columns)} columns")

            elif content_type == "TIMELINE_STEPS":
                item_count = constraints.get("point_count", [2, 4])
                timeline_items = generate_timeline_content(
                    narration_text=narration_text,
                    item_count_range=item_count,
                    slide_title=slide_title,
                    subtopic_name=subtopic_name,
                )
                slide["visual_content"] = {"timeline_items": timeline_items}
                print(f"   → Generated {len(timeline_items)} timeline items")

            elif content_type == "NO_NARRATION_POINTS":
                # Title card - just subtitle
                slide["visual_content"] = {
                    "subtitle": (
                        narration_text[:100] + "..."
                        if len(narration_text) > 100
                        else narration_text
                    )
                }
                print(f"   → Generated title card subtitle")

            else:
                print(f"   ⚠ Unknown content type: {content_type}, skipping")
                slide["visual_content"] = {}

    state["slides"] = slides
    return state
