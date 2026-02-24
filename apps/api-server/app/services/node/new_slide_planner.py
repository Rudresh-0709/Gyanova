import json
import uuid
from typing import Dict, Any, List

try:
    from ..llm.model_loader import load_openai, load_groq
    from ..state import TutorState
except ImportError:
    # Fallback for direct script execution or different import paths
    import sys
    import os

    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from llm.model_loader import load_openai, load_groq
    from state import TutorState

# TEMPLATE REGISTRY
SLIDE_TEMPLATES = {
    # ─────────────────────────────────────────────────────────────
    # HERO & TITLE SECTION
    # ─────────────────────────────────────────────────────────────
    "Title card": {
        "template_name": "Title card",
        "when_to_use": ["Start of a lesson", "Start of a new chapter or subtopic"],
        "how_to_make": {
            "title": "Clear, high-impact concept name (5-8 words)",
            "subtitle": "2-sentence hook explaining why this matters (20-30 words)",
            "image": "High-quality, thematic background or side hero",
            "layout_note": "Text should take up 40% of screen area visually",
        },
    },
    # ─────────────────────────────────────────────────────────────
    # TEXT & EXPLANATION LAYOUTS
    # ─────────────────────────────────────────────────────────────
    "Title with bullets": {
        "template_name": "Title with bullets",
        "when_to_use": [
            "Explaining a concept in points",
            "Breaking down ideas logically",
        ],
        "how_to_make": {
            "title": "Concept or idea",
            "bullets": "4-5 points total",
            "bullet_format": "Bold Header + 1 sentence explanation per point",
            "density": "Total text should be ~80-100 words to avoid whitespace",
        },
    },
    "Title with bullets and image": {
        "template_name": "Title with bullets and image",
        "when_to_use": [
            "Concept explanation that benefits from visualization",
            "Abstract topics needing visual support",
        ],
        "how_to_make": {
            "title": "Concept name",
            "bullets": "3-4 key ideas",
            "bullet_format": "Each bullet must have a 15-word description",
            "image": "Vertical aspect ratio to match text height",
            "text_balance": "Text column and image column should appear equal height",
        },
    },
    "Image and text": {
        "template_name": "Image and text",
        "when_to_use": ["Building intuition", "Narrative-style teaching"],
        "how_to_make": {
            "image": "Primary visual element (takes 50% width)",
            "text": "1 Headline + 2 substantial paragraphs (approx 60 words each)",
            "tone": "Conversational but detailed",
            "avoid": "Single sentence descriptions",
        },
    },
    "Text and image": {
        "template_name": "Text and image",
        "when_to_use": [
            "Formal explanation first, visual second",
            "Definitions with supporting imagery",
        ],
        "how_to_make": {
            "text": "Structured explanation (Headline + 3-4 detailed points)",
            "image": "Supportive, secondary",
            "content_fill": "Text must physically occupy the same vertical height as the image",
        },
    },
    # ─────────────────────────────────────────────────────────────
    # COLUMNS & COMPARISONS
    # ─────────────────────────────────────────────────────────────
    "Two columns": {
        "template_name": "Two columns",
        "when_to_use": ["Comparisons", "Pros vs cons", "Theory vs example"],
        "how_to_make": {
            "left_column": "Title + 3-4 descriptive points (Bold + Text)",
            "right_column": "Title + 3-4 descriptive points (Bold + Text)",
            "balance": "Both sides must have equal word count (~60 words per side)",
        },
    },
    "Three columns": {
        "template_name": "Three columns",
        "when_to_use": ["Categorization", "Types or classes"],
        "how_to_make": {
            "columns": "Exactly 3",
            "item_format": "Icon + Title + 25-word description per column",
            "avoid": "Orphan titles without descriptions",
        },
    },
    "Four columns": {
        "template_name": "Four columns",
        "when_to_use": ["Lists of components", "Feature breakdowns"],
        "how_to_make": {
            "columns": "Exactly 4",
            "item_format": "Title + 15-word concise explanation per column",
            "icons": "Mandatory to fill vertical space",
        },
    },
    # ─────────────────────────────────────────────────────────────
    # PROCESS & FLOW
    # ─────────────────────────────────────────────────────────────
    "Timeline": {
        "template_name": "Timeline",
        "when_to_use": ["Processes", "Historical progression"],
        "how_to_make": {
            "steps": "4-6 sequential steps",
            "step_content": "Year/Phase + Title + 1 sentence context",
            "visual_fill": "Ensure text alternates or fills the space below/above the line",
        },
    },
    "Arrows": {
        "template_name": "Arrows",
        "when_to_use": ["Cause-effect relationships", "Input → output explanation"],
        "how_to_make": {
            "nodes": "3-4 distinct stages",
            "node_content": "Box containing: Title + 2 bullet points of detail",
            "direction": "Left to right",
            "fill_strategy": "Cards should be wide to fill the slide width",
        },
    },
    "Diagram": {
        "template_name": "Diagram",
        "when_to_use": ["System architecture", "Complex abstractions"],
        "how_to_make": {
            "elements": "Visual diagram in center",
            "sidebar_text": "Mandatory: A 'Key Takeaway' sidebar with ~50 words explaining the diagram",
            "labels": "Detailed labels, not just keywords",
        },
    },
    # ─────────────────────────────────────────────────────────────
    # LISTS & SUMMARIES
    # ─────────────────────────────────────────────────────────────
    "Icons with text": {
        "template_name": "Icons with text",
        "when_to_use": ["Key takeaways", "Concept reinforcement"],
        "how_to_make": {
            "items": "4-6 items",
            "format": "Icon (Left) + Bold Title + 1 sentence description (Right)",
            "layout": "Grid 2x2 or 2x3 to fill screen",
        },
    },
    "Large bullet list": {
        "template_name": "Large bullet list",
        "when_to_use": ["Summaries", "Revision slides"],
        "how_to_make": {
            "bullets": "5-6 points",
            "text": "Full sentences (15-20 words each)",
            "styling": "Large font size, generous line height to fill vertical space",
        },
    },
    # ─────────────────────────────────────────────────────────────
    # INTERACTIVE & PROGRESSIVE
    # ─────────────────────────────────────────────────────────────
    "3 toggles": {
        "template_name": "3 toggles",
        "when_to_use": ["Progressive disclosure", "Deep dive into 3 questions"],
        "how_to_make": {
            "toggle_title": "Compelling question or topic",
            "content": "Hidden explanation must be substantial (40-50 words per toggle)",
            "tone": "Exploratory",
        },
    },
    "3 nested cards": {
        "template_name": "3 nested cards",
        "when_to_use": ["Layered learning", "Beginner → intermediate → advanced"],
        "how_to_make": {
            "cards": "3 distinct layers",
            "content": "Each card must have Title + 3 bullet points of detail",
            "visual": "Cards should overlap but have enough text to look full",
        },
    },
    # ─────────────────────────────────────────────────────────────
    # DATA & CHARTS (Preventing emptiness)
    # ─────────────────────────────────────────────────────────────
    "Column chart": {
        "template_name": "Column chart",
        "when_to_use": ["Comparing quantities"],
        "how_to_make": {
            "data": "Clear values",
            "analysis_text": "Mandatory: A 50-word 'Analysis' paragraph beside the chart explaining the trend",
            "labels": "Descriptive",
        },
    },
    "Line chart": {
        "template_name": "Line chart",
        "when_to_use": ["Trends over time"],
        "how_to_make": {
            "data": "Sequential",
            "analysis_text": "Mandatory: 'Key Observations' list (3 points) beside the chart",
        },
    },
    "Pie chart": {
        "template_name": "Pie chart",
        "when_to_use": ["Proportions"],
        "how_to_make": {
            "segments": "3-6 max",
            "legend": "Detailed legend with descriptions, not just labels",
            "analysis_text": "Summary paragraph (40 words) explaining the largest segment",
        },
    },
    # ─────────────────────────────────────────────────────────────
    # NEW PRIMARY CONTENT TYPES
    # ─────────────────────────────────────────────────────────────
    "Comparison table": {
        "template_name": "Comparison table",
        "when_to_use": ["Detailed cross-feature comparisons", "Side-by-side specs"],
        "how_to_make": {
            "headers": ["Feature", "Option A", "Option B"],
            "rows": "4-5 rows of detailed criteria",
            "capacity": "High density data",
        },
    },
    "Key-Value list": {
        "template_name": "Key-Value list",
        "when_to_use": ["Technical specs", "Properties", "Metadata"],
        "how_to_make": {
            "items": "6-8 pairs of Label: Content",
            "format": "Bold Label followed by descriptive value",
        },
    },
    "Rich text": {
        "template_name": "Rich text",
        "when_to_use": [
            "Deep dive explanations",
            "Philosophical context",
            "Complex narratives",
        ],
        "how_to_make": {
            "paragraphs": "3 substantial paragraphs (60-80 words each)",
            "tone": "Academic and thorough",
        },
    },
    "Numbered list": {
        "template_name": "Numbered list",
        "when_to_use": ["Ranked items", "Strict sequences", "Prioritized steps"],
        "how_to_make": {
            "items": "5-7 numbered items",
            "item_format": "Number + Bold Title + 1-2 sentence description",
        },
    },
    "Labeled diagram": {
        "template_name": "Labeled diagram",
        "when_to_use": ["Anatomy", "Hardware components", "Geographic maps"],
        "how_to_make": {
            "image": "Central technical visual",
            "labels": "4-6 annotations pointing to specific parts of the image",
        },
    },
    "Hierarchy tree": {
        "template_name": "Hierarchy tree",
        "when_to_use": ["Organizational charts", "Family trees", "Decision logic"],
        "how_to_make": {
            "structure": "Root node branching into at least 3 sub-levels",
            "node_content": "Brief, clear labels for each node",
        },
    },
    "Split panel": {
        "template_name": "Split panel",
        "when_to_use": ["Case studies", "Theory vs Practice", "Before vs After"],
        "how_to_make": {
            "left_panel": "Independent content (Title + 2 Paragraphs)",
            "right_panel": "Independent content (Title + 2 Paragraphs)",
            "visual_balance": "Both panels must feel equal in weight",
        },
    },
    "Formula block": {
        "template_name": "Formula block",
        "when_to_use": [
            "Mathematical proofs",
            "Scientific equations",
            "Algorithm definitions",
        ],
        "how_to_make": {
            "expression": "Core equation (LaTeX style or clear plain text)",
            "variables": "Definitions for every symbol used",
            "example": "One practical application showing numerical values",
        },
    },
}

SLIDE_PURPOSES = [
    "definition",
    "intuition",
    "process",
    "comparison",
    "visualization",
    "reinforcement",
    "assessment",
]
NARRATION_ROLES = [
    "Introduce",
    "Interpret",
    "Guide",
    "Contrast",
    "Emphasize",
    "Connect",
    "Reinforce",
    "Question",
]


def plan_slides_for_subtopic(
    subtopic: Dict[str, Any], teacher_profile: str = "Expert Teacher"
) -> Dict[str, Any]:
    """Calls LLM to plan slides for a single subtopic."""
    # SINGLE-PASS ARCHITECTURE-AWARE PLANNING
    # This prompt forces the model to first architect the technical content, then map to visuals.
    SYSTEM_PROMPT = f"""
    You are an AI Curriculum Architect & Visual Pedagogy Expert.
    Your goal is to design a high-depth, technically accurate slide plan for a lesson.
    
    SUBTOPIC: {subtopic.get('name')}
    DIFFICULTY: {subtopic.get('difficulty', 'Beginner')}
    TEACHER PROFILE: {teacher_profile}
    
    AVAILABLE TEMPLATES (Visual Delivery Mechanisms):
    {json.dumps(SLIDE_TEMPLATES, indent=2)}
    
    SLIDE PURPOSES: {json.dumps(SLIDE_PURPOSES)}
    NARRATION ROLES: {json.dumps(NARRATION_ROLES)}
    
    ⭐ PLANNING STRATEGY (CRITICAL):
    1. ARCHITECT FIRST: Identify the 4-7 specific technical "building blocks" (laws, formulas, mechanisms, examples) needed to cover this subtopic with high depth.
    2. MAP TO VISUALS: Assign the BEST visual template for each block. Use diversity (don't repeat templates unless essential).
    
    ⭐ PRIMARY CONTENT TYPES (Best Uses):
    - Comparison table: Side-by-side features.
    - Formula block: Equations + Variable keys.
    - Labeled diagram: Hardware/Anatomy/Spatial systems.
    - Timeline/Arrows: Processes and flows.
    - Key-Value list: Technical specs.
    
    RULES:
    - Plan 4-7 slides.
    - Output ONLY valid JSON.
    
    OUTPUT FORMAT:
    {{
        "slides": [
            {{
                "title": "Technical Concept Name",
                "purpose": "...",
                "selected_template": "...",
                "role": "...",
                "goal": "Detailed learning objective",
                "reasoning": "Quick pedagogical justification"
            }}
        ]
    }}
    """

    llm = load_openai()
    response = llm.invoke([{"role": "system", "content": SYSTEM_PROMPT}])

    try:
        content = response.content.replace("```json", "").replace("```", "").strip()
        data = json.loads(content)

        # ---- VALIDATION STARTS HERE ----
        VALID_TEMPLATES = set(SLIDE_TEMPLATES.keys())
        VALID_PURPOSES = set(SLIDE_PURPOSES)
        VALID_NARRATION = set(NARRATION_ROLES)

        validated_slides = []

        for slide in data.get("slides", []):
            if slide.get("selected_template") not in VALID_TEMPLATES:
                continue
            if slide.get("purpose") not in VALID_PURPOSES:
                # Support old legacy key for transition if needed, but here we enforce
                if (
                    "slide_purpose" in slide
                    and slide["slide_purpose"] in VALID_PURPOSES
                ):
                    slide["purpose"] = slide.pop("slide_purpose")
                else:
                    continue
            if slide.get("role") not in VALID_NARRATION:
                if (
                    "narration_role" in slide
                    and slide["narration_role"] in VALID_NARRATION
                ):
                    slide["role"] = slide.pop("narration_role")
                else:
                    continue
            if not slide.get("title"):
                if "slide_title" in slide:
                    slide["title"] = slide.pop("slide_title")
                else:
                    continue  # title is mandatory

            # Ensure goal is also handled
            if "narration_goal" in slide:
                slide["goal"] = slide.pop("narration_goal")

            validated_slides.append(slide)

        data["slides"] = validated_slides
        # ---- VALIDATION ENDS HERE ----

        return data

    except Exception as e:
        print(f"Error parsing slide plan for {subtopic_name}: {e}")
        return {"slides": []}


if __name__ == "__main__":
    # Test planning a single subtopic
    test_subtopic = {
        "name": "Introduction to Computer Generations",
        "difficulty": "Beginner",
        "id": "sub_1_2b67b6",
    }
    result = plan_slides_for_subtopic(test_subtopic)
    import json

    print(json.dumps(result, indent=2))
