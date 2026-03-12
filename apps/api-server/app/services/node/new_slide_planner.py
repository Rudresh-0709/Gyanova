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
            "left_column": "Title + 1 descriptive paragraph (no bullet points)",
            "right_column": "Title + 1 descriptive paragraph (no bullet points)",
            "balance": "Both sides must have equal word count (~40-60 words per side)",
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
    "Hub and spoke": {
        "template_name": "Hub and spoke",
        "when_to_use": [
            "Central concept with surrounding related ideas",
            "Core-peripheral relationships",
        ],
        "how_to_make": {
            "hub": "Central concept or entity",
            "spokes": "4-6 related sub-concepts radiating outward",
            "spoke_content": "Icon + Title + 1 sentence per spoke",
        },
    },
    "Sequential output": {
        "template_name": "Sequential output",
        "when_to_use": [
            "Step-by-step transformations",
            "Pipeline or chain of operations",
        ],
        "how_to_make": {
            "steps": "3-5 sequential stages",
            "step_content": "Title + brief description of input/output at each stage",
            "direction": "Left to right or top to bottom",
        },
    },
    "Process arrow block": {
        "template_name": "Process arrow block",
        "when_to_use": ["Linear workflows", "Manufacturing or data pipelines"],
        "how_to_make": {
            "nodes": "3-5 process stages connected by arrows",
            "node_content": "Icon + Title + 1-2 sentence description",
        },
    },
    "Cyclic process block": {
        "template_name": "Cyclic process block",
        "when_to_use": ["Recurring processes", "Feedback loops", "Life cycles"],
        "how_to_make": {
            "nodes": "3-6 stages forming a loop",
            "node_content": "Title + 1 sentence per stage",
            "visual": "Circular arrangement with directional arrows",
        },
    },
    "Feature showcase block": {
        "template_name": "Feature showcase block",
        "when_to_use": [
            "Product features",
            "Capabilities overview",
            "Technology highlights",
        ],
        "how_to_make": {
            "central_element": "Hero image or icon representing the main subject",
            "features": "4-6 features orbiting the central element",
            "feature_content": "Icon + Title + 1 sentence description",
        },
    },
}

# Lightweight list for the LLM prompt (avoids sending the full registry)
AVAILABLE_TEMPLATE_NAMES = list(SLIDE_TEMPLATES.keys())

SLIDE_PURPOSES = [
    "definition",
    "intuition",
    "process",
    "comparison",
    "visualization",
    "reinforcement",
    "assessment",
]
SLIDE_INTENTS = [
    "concept",
    "definition",
    "process",
    "comparison",
    "data",
    "example",
    "summary",
    "intuition",
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
VISUAL_TYPES = [
    "image",
    "diagram",
    "chart",
    "illustration",
    "none",
]
CONTENT_ANGLES = [
    "overview",
    "mechanism",
    "example",
    "comparison",
    "application",
    "visualization",
    "summary",
]


def plan_slides_for_subtopic(
    subtopic: Dict[str, Any], teacher_profile: str = "Expert Teacher"
) -> Dict[str, Any]:
    """Calls LLM to plan slides for a single subtopic."""
    SYSTEM_PROMPT = f"""
    ROLE: AI Curriculum Architect & Visual Pedagogy Expert.

    CONTEXT:
    Subtopic: {subtopic.get('name')}
    Difficulty: {subtopic.get('difficulty', 'Beginner')}
    Teacher Profile: {teacher_profile}

    AVAILABLE TEMPLATES:
    {chr(10).join(f'    * {name}' for name in AVAILABLE_TEMPLATE_NAMES)}

    SLIDE INTENTS: {json.dumps(SLIDE_INTENTS)}
    SLIDE PURPOSES: {json.dumps(SLIDE_PURPOSES)}
    NARRATION ROLES: {json.dumps(NARRATION_ROLES)}
    VISUAL TYPES: {json.dumps(VISUAL_TYPES)}

    PLANNING RULES:
    1. Plan 4-7 slides. Each slide should represent a key learning moment.
    2. ARCHITECT BY ANGLE: Ensure a diverse progression of learning perspectives:
       overview → mechanism → example → application → summary.
    3. Determine slide intent and content angle first, then select the best template.
    4. Maintain template diversity — no template more than twice.
    5. Avoid repeating the same content angle twice in a row.
    6. Prefer visuals when explaining processes, systems, or data.
    7. Set "visual_required" to true and choose the appropriate "visual_type" when a visual enhances understanding.
    8. VARIETY RULE (CRITICAL): No two slides within a subtopic may use the same CATEGORY of visual structure:
       - Timeline category: Timeline
       - Bullet category: Title with bullets, Title with bullets and image, Large bullet list
       - Card category: Icons with text, Three columns, Four columns
       - Process category: Arrows, Diagram, Process arrow block, Cyclic process block
       - Comparison category: Two columns, Comparison table, Split panel
       - Data category: Column chart, Line chart, Pie chart
       Each category may appear AT MOST ONCE per subtopic.
    9. Timeline slides must have MAX 5 items/steps.
    10. IMAGE ROLE ASSIGNMENT (CRITICAL):
        Every slide must have an "image_role" field set to one of:
        - "content": Image is essential to understanding (diagrams, photos, anatomical illustrations, labeled visuals).
          Templates that default to content: Labeled diagram, Image and text, Text and image, Diagram.
        - "accent": Image is decorative atmosphere — enhances visual appeal but doesn't teach.
          Templates that default to accent: Timeline, Icons with text, Title with bullets and image, Title card.
        - "none": No image needed — the content is self-sufficient.
          Templates that default to none: Comparison table, Formula block, Key-Value list, Split panel, Code.
        Choose based on: Does a student NEED to see a picture to understand this slide's concept?
        If yes → "content". If no but it would look nice → "accent". If it would distract → "none".
    11. Output ONLY valid JSON.

    OUTPUT FORMAT:
    {{
        "slides": [
            {{
                "title": "Technical Concept Name",
                "content_angle": "overview | mechanism | example | comparison | application | visualization | summary",
                "intent": "concept | definition | process | comparison | data | example | summary | intuition",
                "purpose": "definition | intuition | process | comparison | visualization | reinforcement | assessment",
                "selected_template": "...",
                "role": "Introduce | Interpret | Guide | Contrast | Emphasize | Connect | Reinforce | Question",
                "goal": "Detailed learning objective",
                "reasoning": "Quick pedagogical justification",
                "visual_required": true,
                "visual_type": "image | diagram | chart | illustration | none",
                "image_role": "content | accent | none"
            }}
        ]
    }}
    """

    llm = load_openai()
    response = llm.invoke([{"role": "system", "content": SYSTEM_PROMPT}])

    # DEBUG: Show raw planning output
    print("\n--- [DEBUG] SLIDE PLANNING LLM OUTPUT ---")
    print(response.content)
    print("------------------------------------------\n")

    try:
        content = response.content.replace("```json", "").replace("```", "").strip()
        data = json.loads(content)

        # ---- VALIDATION STARTS HERE ----
        VALID_TEMPLATES = set(AVAILABLE_TEMPLATE_NAMES)
        VALID_INTENTS = set(SLIDE_INTENTS)
        VALID_PURPOSES = set(SLIDE_PURPOSES)
        VALID_NARRATION = set(NARRATION_ROLES)
        VALID_VISUAL_TYPES = set(VISUAL_TYPES)
        VALID_ANGLES = set(CONTENT_ANGLES)

        validated_slides = []

        for slide in data.get("slides", []):
            # 1. Content Angle Inference/Validation
            angle = slide.get("content_angle", "").lower()
            tmpl_raw = slide.get("selected_template", "")
            # Normalize template for lookup (Title Case)
            tmpl = tmpl_raw.strip().title()
            if " And " in tmpl:
                tmpl = tmpl.replace(" And ", " and ")  # Fix common title() artifact

            purp = slide.get("purpose", "").lower()

            if angle not in VALID_ANGLES:
                # Inference Logic
                if "Timeline" in tmpl or "process" in purp:
                    angle = "mechanism"
                elif "Comparison" in tmpl or "Comparison" in purp:
                    angle = "comparison"
                elif "Diagram" in tmpl or "visualization" in purp:
                    angle = "visualization"
                elif "bullets" in tmpl.lower() or "intro" in purp:
                    angle = "overview"
                elif "example" in purp or "demo" in purp:
                    angle = "example"
                elif "summary" in purp or "reinforcement" in purp:
                    angle = "summary"
                else:
                    angle = "overview"
                slide["content_angle"] = angle
            else:
                slide["content_angle"] = angle

            intent = slide.get("intent", "").lower()
            if intent not in VALID_INTENTS:
                continue

            if tmpl not in VALID_TEMPLATES:
                # Fallback check for missing " card" etc if LLM clipped it
                matched = False
                for v_tmpl in VALID_TEMPLATES:
                    if tmpl.lower() in v_tmpl.lower():
                        tmpl = v_tmpl
                        matched = True
                        break
                if not matched:
                    continue

            slide["selected_template"] = tmpl
            slide["intent"] = intent
            if slide.get("purpose") not in VALID_PURPOSES:
                # Lenient matching or default
                matched = False
                for v_purp in VALID_PURPOSES:
                    if v_purp in slide.get("purpose", "").lower():
                        slide["purpose"] = v_purp
                        matched = True
                        break
                if not matched:
                    slide["purpose"] = "definition"  # Fallback

            if slide.get("role") not in VALID_NARRATION:
                # Lenient matching or default
                matched = False
                for v_role in VALID_NARRATION:
                    if v_role.lower() in slide.get("role", "").lower():
                        slide["role"] = v_role
                        matched = True
                        break
                if not matched:
                    slide["role"] = "Guide"  # Fallback
            if not slide.get("title"):
                if "slide_title" in slide:
                    slide["title"] = slide.pop("slide_title")
                else:
                    continue  # title is mandatory

            # Ensure goal is also handled
            if "narration_goal" in slide:
                slide["goal"] = slide.pop("narration_goal")

            # Validate visual_type
            vtype = slide.get("visual_type")
            if vtype and vtype not in VALID_VISUAL_TYPES:
                slide["visual_type"] = "none"
                slide["visual_required"] = False
            # Default visual fields if missing
            if "visual_required" not in slide:
                slide["visual_required"] = False
            if "visual_type" not in slide:
                slide["visual_type"] = "none"

            # Validate and default image_role
            VALID_IMAGE_ROLES = {"content", "accent", "none"}
            image_role = slide.get("image_role", "").lower()
            if image_role not in VALID_IMAGE_ROLES:
                # Infer from template
                CONTENT_IMAGE_TEMPLATES = {
                    "Labeled diagram", "Image and text", "Text and image", "Diagram",
                }
                ACCENT_IMAGE_TEMPLATES = {
                    "Timeline", "Icons with text", "Title with bullets and image",
                    "Title card", "Large bullet list", "Three columns", "Four columns",
                }
                NONE_IMAGE_TEMPLATES = {
                    "Comparison table", "Formula block", "Key-Value list",
                    "Split panel", "Code", "Hub and spoke",
                }
                if tmpl in CONTENT_IMAGE_TEMPLATES:
                    image_role = "content"
                elif tmpl in NONE_IMAGE_TEMPLATES:
                    image_role = "none"
                else:
                    image_role = "accent"  # Default fallback
            slide["image_role"] = image_role

            validated_slides.append(slide)

        data["slides"] = validated_slides
        # ---- VALIDATION ENDS HERE ----

        # ---- DIVERSITY ENFORCEMENT ----
        # Category mapping for variety enforcement
        TEMPLATE_CATEGORIES = {
            "Timeline": "timeline",
            "Title with bullets": "bullet",
            "Title with bullets and image": "bullet",
            "Large bullet list": "bullet",
            "Icons with text": "card",
            "Three columns": "card",
            "Four columns": "card",
            "Arrows": "process",
            "Diagram": "process",
            "Process arrow block": "process",
            "Cyclic process block": "process",
            "Feature showcase block": "process",
            "Two columns": "comparison",
            "Comparison table": "comparison",
            "Split panel": "comparison",
            "Column chart": "data",
            "Line chart": "data",
            "Pie chart": "data",
        }

        template_count = {}
        used_categories = set()
        diverse_slides = []
        last_angle = None

        for slide in data["slides"]:
            tmpl = slide.get("selected_template")
            angle = slide.get("content_angle")

            # Template cap: max 2
            template_count[tmpl] = template_count.get(tmpl, 0) + 1
            if template_count[tmpl] > 2:
                continue

            # Category cap: max 1 per category
            category = TEMPLATE_CATEGORIES.get(tmpl)
            if category and category in used_categories:
                print(f"    ⚠ Skipping '{tmpl}' — category '{category}' already used")
                continue

            # Sequential Angle check: Avoid back-to-back same angle
            if angle == last_angle:
                continue

            diverse_slides.append(slide)
            last_angle = angle
            if category:
                used_categories.add(category)

        # Clamp to 4-7 slides
        if len(diverse_slides) < 4:
            # If we filtered too aggressively, keep the original validated ones
            # but still try to respect the hard template cap
            data["slides"] = validated_slides[:7]
        else:
            data["slides"] = diverse_slides[:7]
        # ---- DIVERSITY ENFORCEMENT ENDS ----

        return data

    except Exception as e:
        print(f"Error parsing slide plan for {subtopic.get('name')}: {e}")
        return {
            "slides": [
                {
                    "title": subtopic.get("name", "Untitled"),
                    "intent": "concept",
                    "purpose": "definition",
                    "selected_template": "Title with bullets",
                    "role": "Introduce",
                    "goal": "Fallback slide",
                    "reasoning": "Auto-generated fallback due to planning error",
                    "visual_required": False,
                    "visual_type": "none",
                }
            ]
        }


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
