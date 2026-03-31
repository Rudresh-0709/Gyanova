import json
import uuid
from typing import Dict, Any, List

try:
    from app.services.llm.model_loader import load_openai, load_groq
    from app.services.state import TutorState
except ImportError:
    # Try relative if running from within app/services/node
    try:
        from ..llm.model_loader import load_openai, load_groq
        from ..state import TutorState
    except ImportError:
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


SAFE_FALLBACK_SEQUENCE = [
    {
        "intent": "concept",
        "purpose": "intuition",
        "selected_template": "Title card",
        "role": "Introduce",
        "goal": "Open the subtopic with relevance and curiosity.",
        "visual_required": True,
        "visual_type": "image",
        "image_role": "accent",
        "target_density": "sparse",
        "content_angle": "overview",
    },
    {
        "intent": "definition",
        "purpose": "definition",
        "selected_template": "Title with bullets",
        "role": "Guide",
        "goal": "Explain the core idea with a few clear points.",
        "visual_required": False,
        "visual_type": "none",
        "image_role": "none",
        "target_density": "standard",
        "content_angle": "overview",
    },
    {
        "intent": "process",
        "purpose": "process",
        "selected_template": "Process arrow block",
        "role": "Interpret",
        "goal": "Show how the idea works step by step.",
        "visual_required": True,
        "visual_type": "diagram",
        "image_role": "content",
        "target_density": "balanced",
        "content_angle": "mechanism",
    },
    {
        "intent": "example",
        "purpose": "reinforcement",
        "selected_template": "Icons with text",
        "role": "Connect",
        "goal": "Ground the concept in examples or applications.",
        "visual_required": False,
        "visual_type": "none",
        "image_role": "none",
        "target_density": "dense",
        "content_angle": "application",
    },
]


def _rebalance_density_targets(slides: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Repair density concentration instead of rejecting the full plan."""
    if not slides:
        return slides

    preferred_cycle = ["sparse", "balanced", "standard", "dense"]

    while True:
        density_counts: Dict[str, int] = {}
        for slide in slides:
            density = slide.get("target_density", "standard")
            density_counts[density] = density_counts.get(density, 0) + 1

        dominant_density = max(density_counts, key=density_counts.get)
        dominant_count = density_counts[dominant_density]
        if dominant_count <= len(slides) / 2:
            break

        for idx, slide in enumerate(slides):
            if slide.get("target_density") == dominant_density:
                slide["target_density"] = preferred_cycle[idx % len(preferred_cycle)]
                dominant_count -= 1
                if dominant_count <= len(slides) / 2:
                    break

    return slides


def _ensure_sparse_and_dense_mix(slides: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Guarantee at least one sparse slide and one dense slide."""
    if not slides:
        return slides

    densities = {slide.get("target_density") for slide in slides}

    if "sparse" not in densities and "ultra_sparse" not in densities:
        slides[0]["target_density"] = "sparse"
        slides[0]["selected_template"] = "Title card"
        slides[0]["image_role"] = "accent"
        slides[0]["visual_required"] = True
        slides[0]["visual_type"] = "image"
        slides[0]["content_angle"] = slides[0].get("content_angle") or "overview"

    densities = {slide.get("target_density") for slide in slides}
    if "dense" not in densities and "super_dense" not in densities and len(slides) > 1:
        slides[-1]["target_density"] = "dense"

    return slides


def _get_domain_specific_guidance(domain: str) -> str:
    """Return domain-specific template guidance."""
    guidance_map = {
        "math": """
    DOMAIN-SPECIFIC GUIDANCE (MATHEMATICS):
    - REQUIREMENT: Include at least ONE slide using 'Formula block' template to display key equations.
    - Math slides should emphasize: equations/formulas, variable definitions, step-by-step derivations.
    - Use 'Formula block' for core equations. Use 'Process arrow block' or 'Arrows' for multi-step proofs/derivations.
    - Include 'Key-Value list' for variable definitions (e.g., "e = 2.718...", "π = 3.14159...").
    - Example angles: "mechanism" (how to solve), "comparison" (different formula forms), "example" (application).
    - When selecting templates, prioritize Formula block, Process arrow, Key-Value list over generic bullet templates.
""",
        "science": """
    DOMAIN-SPECIFIC GUIDANCE (SCIENCE):
    - Feature diagrams heavily (use 'Diagram', 'Labeled diagram', 'Process arrow block' for processes).
    - Include at least ONE slide with a visual that shows structure (cell, molecule, system, apparatus).
    - Use 'Comparison table' or 'Two columns' to contrast concepts (reactants vs products, structure vs function).
    - Example angles: "mechanism" (how biological/chemical process works), "comparison" (similar/different systems).
""",
        "history": """
    DOMAIN-SPECIFIC GUIDANCE (HISTORY/SOCIAL STUDIES):
    - Use 'Timeline' to show chronological sequence (events, eras, movements).
    - Use 'Comparison table' or 'Split panel' to contrast historical periods, figures, or ideologies.
    - Include map/diagram visuals when discussing geography or territorial changes.
    - Example angles: "mechanism" (cause and effect), "comparison" (different periods or perspectives), "application" (modern relevance).
""",
        "language": """
    DOMAIN-SPECIFIC GUIDANCE (LANGUAGE/LITERATURE):
    - Use 'Arrows' or 'Process arrow block' to show narrative flow or argument structure.
    - Use 'Icons with text' for contrasting literary devices (metaphor, simile, personification).
    - Use 'Key-Value list' for vocabulary, grammar rules, or character traits.
    - Example angles: "overview" (genre intro), "comparison" (stylistic choices), "example" (textual analysis).
""",
    }
    return guidance_map.get(domain, "")


def _ensure_domain_specific_templates(slides: List[Dict[str, Any]], domain: str) -> List[Dict[str, Any]]:
    """Enforce domain-specific template requirements."""
    if not slides or domain == "general":
        return slides
    
    # Math: must include at least one Formula block
    if domain == "math":
        has_formula = any(s.get("selected_template") == "Formula block" for s in slides)
        if not has_formula and len(slides) > 1:
            # Insert Formula block as a middle slide
            insert_idx = len(slides) // 2
            formula_slide = {
                "title": f"{slides[0].get('title', 'Math Concept')} - Key Equation",
                "content_angle": "mechanism",
                "intent": "definition",
                "purpose": "definition",
                "selected_template": "Formula block",
                "role": "Emphasize",
                "goal": "Display and explain core equation(s).",
                "reasoning": "Domain-enforced: math topics require Formula block slide.",
                "visual_required": False,
                "visual_type": "none",
                "image_role": "none",
                "target_density": "standard",
            }
            slides.insert(insert_idx, formula_slide)
    
    # Science: must include at least one Diagram or process
    if domain == "science":
        has_diagram = any(
            s.get("selected_template") in {"Diagram", "Labeled diagram", "Process arrow block"}
            for s in slides
        )
        if not has_diagram and len(slides) > 1:
            insert_idx = len(slides) // 2
            diagram_slide = {
                "title": f"{slides[0].get('title', 'Science Concept')} - System/Structure",
                "content_angle": "visualization",
                "intent": "process",
                "purpose": "visualization",
                "selected_template": "Labeled diagram",
                "role": "Interpret",
                "goal": "Show key system structure or anatomical relationships.",
                "reasoning": "Domain-enforced: science topics require visual diagram.",
                "visual_required": True,
                "visual_type": "diagram",
                "image_role": "content",
                "target_density": "balanced",
            }
            slides.insert(insert_idx, diagram_slide)
    
    # History: use Timeline if chronological content
    if domain == "history":
        has_timeline = any(s.get("selected_template") == "Timeline" for s in slides)
        if not has_timeline and len(slides) > 1:
            # Try to add a timeline slide if not already present
            insert_idx = min(1, len(slides) - 1)  # Often after intro
            timeline_slide = {
                "title": f"{slides[0].get('title', 'Historical Period')} - Timeline",
                "content_angle": "mechanism",
                "intent": "process",
                "purpose": "process",
                "selected_template": "Timeline",
                "role": "Guide",
                "goal": "Show chronological progression of events.",
                "reasoning": "Domain-enforced: history topics should include Timeline.",
                "visual_required": False,
                "visual_type": "none",
                "image_role": "accent",
                "target_density": "standard",
            }
            slides.insert(insert_idx, timeline_slide)
    
    return slides
    """Keep sparse/title-card slides visually alive unless template is explicitly no-image."""
    if not slides:
        return slides

    no_image_templates = {
        "Comparison table",
        "Formula block",
        "Key-Value list",
        "Split panel",
        "Code",
        "Hub and spoke",
    }

    for slide in slides:
        template = (slide.get("selected_template") or "").strip()
        density = (slide.get("target_density") or "standard").lower()
        image_role = (slide.get("image_role") or "").lower()

        # Title cards should always carry an accent visual to avoid blank hero slides.
        if template == "Title card" and image_role != "accent":
            slide["image_role"] = "accent"
            if slide.get("visual_type") in (None, "", "none"):
                slide["visual_type"] = "image"
            slide["visual_required"] = True
            continue

        # Sparse/ultra-sparse slides should not suppress visuals unless template is no-image by design.
        if density in {"sparse", "ultra_sparse"} and image_role == "none" and template not in no_image_templates:
            slide["image_role"] = "accent"
            if slide.get("visual_type") in (None, "", "none"):
                slide["visual_type"] = "image"
            slide["visual_required"] = True

    return slides


def _build_safe_fallback_plan(subtopic: Dict[str, Any]) -> Dict[str, Any]:
    """Return a small deterministic lesson skeleton instead of a single fallback slide."""
    subtopic_name = subtopic.get("name", "Untitled")
    slides: List[Dict[str, Any]] = []

    fallback_title_templates = [
        f"{subtopic_name}: Big Picture",
        f"{subtopic_name}: Core Concepts",
        f"{subtopic_name}: How It Works",
        f"{subtopic_name}: Examples and Uses",
    ]

    for idx, base in enumerate(SAFE_FALLBACK_SEQUENCE):
        slide = dict(base)
        if idx < len(fallback_title_templates):
            slide["title"] = fallback_title_templates[idx]
        else:
            slide["title"] = f"{subtopic_name}: Deep Dive {idx + 1}"
        slide["reasoning"] = "Auto-generated safe fallback after planning retries failed"
        slides.append(slide)

    return {"slides": slides}


def filter_out_intro_only_slides(slides: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Remove slides that are purely introductory from the plan.
    
    When a subtopic intro narration is present, we don't need intro-only slides
    that would create redundancy by re-introducing the same topic.
    
    Removes slides where role="Introduce" since the subtopic intro already covers that.
    
    If removal would drop slides below minimum (4), keeps at least first slide.
    """
    if not slides or len(slides) <= 4:
        # If we only have 4 or fewer slides, we can't afford to filter any
        return slides
    
    # Filter: Keep all slides EXCEPT those with role="Introduce" on the first slide
    # The first slide is typically the "Title card" with role="Introduce" if it exists
    filtered = []
    skip_first_intro = False
    
    for i, slide in enumerate(slides):
        # Only skip the FIRST slide if it has role="Introduce"
        if i == 0 and slide.get("role") == "Introduce" and len(slides) > 4:
            skip_first_intro = True
            print(f"🔥 INTRO FILTER: Removing first slide with role='Introduce' (redundant with subtopic intro)")
            continue
        filtered.append(slide)
    
    return filtered if len(filtered) >= 4 else slides


def enforce_no_introduce_first_slide(slides: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Safety check: Ensure the first slide never has role="Introduce".
    If it does, change it to "Guide".
    
    This rule applies because:
    - Lesson intro narration already welcomes the student at lesson start
    - Subtopic intro narration already bridges to this subtopic section
    - First slide should guide/explain content, not introduce it again
    
    This is a critical no-redundancy rule for the intro hierarchy.
    """
    if not slides or len(slides) == 0:
        return slides
    
    # If filter_out_intro_only_slides already removed the first intro slide,
    # this becomes a no-op (first slide is no longer "Introduce").
    # This function acts as a fallback safety check.
    first_slide = slides[0]
    if first_slide.get("role") == "Introduce":
        print(f"⚠️  INTRO RULE ENFORCEMENT: First slide had role='Introduce', changing to 'Guide'")
        first_slide["role"] = "Guide"
        first_slide["rule_note"] = "Updated: First slide cannot be 'Introduce' (handled by lesson/subtopic intros)"
    
    return slides


def _detect_domain(subtopic: Dict[str, Any]) -> str:
    """Detect the domain/subject from subtopic name and metadata."""
    topic_name = (subtopic.get("name") or "").lower()
    topic_subject = (subtopic.get("subject") or "").lower()
    
    # Combine name and subject for detection
    combined = f"{topic_name} {topic_subject}"
    
    # Math detection
    math_keywords = {"math", "maths", "algebra", "geometry", "calculus", "trigonometry", "equation", 
                     "formula", "derivative", "integral", "polynomial", "function", "theorem", 
                     "proof", "number theory", "linear", "quadratic", "matrix", "vector",
                     "probability", "statistics", "exponential", "logarithm"}
    if any(keyword in combined for keyword in math_keywords):
        return "math"
    
    # Science detection
    science_keywords = {"science", "physics", "chemistry", "biology", "anatomy", "physiology", 
                        "reaction", "element", "atom", "molecule", "cell", "organism", "system"}
    if any(keyword in combined for keyword in science_keywords):
        return "science"
    
    # History/Social Studies detection
    history_keywords = {"history", "social", "government", "civics", "culture", "society", 
                        "war", "revolution", "political", "economic"}
    if any(keyword in combined for keyword in history_keywords):
        return "history"
    
    # Literature/Language detection
    language_keywords = {"english", "literature", "grammar", "composition", "syntax", "vocabulary",
                         "writing", "analysis", "author", "character", "plot", "theme"}
    if any(keyword in combined for keyword in language_keywords):
        return "language"
    
    return "general"


def _get_domain_specific_guidance(domain: str) -> str:
    """Return domain-specific template guidance."""
    guidance_map = {
        "math": """
    DOMAIN-SPECIFIC GUIDANCE (MATHEMATICS):
    - REQUIREMENT: Include at least ONE slide using 'Formula block' template to display key equations.
    - Math slides should emphasize: equations/formulas, variable definitions, step-by-step derivations.
    - Use 'Formula block' for core equations. Use 'Process arrow block' or 'Arrows' for multi-step proofs/derivations.
    - Include 'Key-Value list' for variable definitions (e.g., "e = 2.718...", "π = 3.14159...").
    - Example angles: "mechanism" (how to solve), "comparison" (different formula forms), "example" (application).
    - When selecting templates, prioritize Formula block, Process arrow, Key-Value list over generic bullet templates.
""",
        "science": """
    DOMAIN-SPECIFIC GUIDANCE (SCIENCE):
    - Feature diagrams heavily (use 'Diagram', 'Labeled diagram', 'Process arrow block' for processes).
    - Include at least ONE slide with a visual that shows structure (cell, molecule, system, apparatus).
    - Use 'Comparison table' or 'Two columns' to contrast concepts (reactants vs products, structure vs function).
    - Example angles: "mechanism" (how biological/chemical process works), "comparison" (similar/different systems).
""",
        "history": """
    DOMAIN-SPECIFIC GUIDANCE (HISTORY/SOCIAL STUDIES):
    - Use 'Timeline' to show chronological sequence (events, eras, movements).
    - Use 'Comparison table' or 'Split panel' to contrast historical periods, figures, or ideologies.
    - Include map/diagram visuals when discussing geography or territorial changes.
    - Example angles: "mechanism" (cause and effect), "comparison" (different periods or perspectives), "application" (modern relevance).
""",
        "language": """
    DOMAIN-SPECIFIC GUIDANCE (LANGUAGE/LITERATURE):
    - Use 'Arrows' or 'Process arrow block' to show narrative flow or argument structure.
    - Use 'Icons with text' for contrasting literary devices (metaphor, simile, personification).
    - Use 'Key-Value list' for vocabulary, grammar rules, or character traits.
    - Example angles: "overview" (genre intro), "comparison" (stylistic choices), "example" (textual analysis).
""",
    }
    return guidance_map.get(domain, "")


def plan_slides_for_subtopic(
    subtopic: Dict[str, Any], teacher_profile: str = "Expert Teacher"
) -> Dict[str, Any]:
    """Calls LLM to plan slides for a single subtopic."""
    # Detect domain for domain-specific guidance
    domain = _detect_domain(subtopic)
    domain_guidance = _get_domain_specific_guidance(domain)
    
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
    4. STRICT VARIETY CONSTRAINT: Maintain template diversity — absolutely NEVER use any single template or primary content type more than TWICE in the entire presentation.
    5. Avoid repeating the same content angle twice in a row.
    6. Prefer visuals when explaining processes, systems, or data.
    7. Set "visual_required" to true and choose the appropriate "visual_type" when a visual enhances understanding.
    8. VARIETY RULE (CRITICAL): Ensure a wide mix of visual categories. NEVER use any of the following visual structure categories more than TWICE per subtopic:
       - Timeline category: Timeline
       - Bullet category: Title with bullets, Title with bullets and image, Large bullet list
       - Card category: Icons with text, Three columns, Four columns
       - Process category: Arrows, Diagram, Process arrow block, Cyclic process block
       - Comparison category: Two columns, Comparison table, Split panel
       - Data category: Column chart, Line chart, Pie chart
       Force yourself to pick from different categories for each slide.
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
    11. DENSITY TARGET (CRITICAL):
        Plan a mix of density levels. A lesson MUST include at least one sparse slide (hero/intro) and at least one dense slide (data/comparison). Most slides should be balanced or standard.
    
    12. CRITICAL INTRO RULE - NO INTRODUCE ON FIRST SLIDE:
        The FIRST SLIDE in your plan must NEVER have role="Introduce".
        The first slide represents the opening of this subtopic section. It will be preceded by:
        - A lesson intro narration (at the very start of the lesson)
        - A subtopic intro narration (before this subtopic's slides)
        Therefore, assign the FIRST SLIDE a different role such as:
        - "Guide" (recommended for first slides: "Here's how we explore this...")
        - "Interpret" or "Explain" (if showing a key visual first)
        NEVER use "Introduce" for slide position 0. Use "Introduce" only if truly pedagogically justified for middle slides.
    
{domain_guidance}

    13. Output ONLY valid JSON.

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
                "image_role": "content | accent | none",
                "target_density": "ultra_sparse | sparse | balanced | standard | dense | super_dense"
            }}
        ]
    }}
    """

    llm = load_openai()

    MAX_RETRIES = 3
    for attempt in range(MAX_RETRIES):
        response = llm.invoke([{"role": "system", "content": SYSTEM_PROMPT}])

        # DEBUG: Show raw planning output
        print(f"\n--- [DEBUG] SLIDE PLANNING LLM OUTPUT (Attempt {attempt+1}) ---")
        print(response.content)
        print("------------------------------------------\n")

        try:
            content_str = response.content.replace("```json", "").replace("```", "").strip()
            data = json.loads(content_str)

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
                if slide is not None:
                    slide["image_role"] = image_role
    
                    # Validate target_density
                    VALID_DENSITIES = {"ultra_sparse", "sparse", "balanced", "standard", "dense", "super_dense"}
                    target_density = slide.get("target_density", "").lower()
                    if target_density not in VALID_DENSITIES:
                        target_density = "standard"
                    slide["target_density"] = target_density
        
                    validated_slides.append(slide)
    
            validated_slides = _rebalance_density_targets(validated_slides)
            validated_slides = _ensure_sparse_and_dense_mix(validated_slides)
    
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
            total_filtered = len(diverse_slides)
            if total_filtered < 4:
                data["slides"] = validated_slides[:7]
            else:
                data["slides"] = diverse_slides[:7]
            # ---- DIVERSITY ENFORCEMENT ENDS ----

            # Temporarily disabled: helper is currently undefined and causes planner fallback.
            # data["slides"] = _normalize_sparse_image_policy(data["slides"])
            
            # ⭐ DOMAIN-SPECIFIC TEMPLATE ENFORCEMENT
            data["slides"] = _ensure_domain_specific_templates(data["slides"], domain)
            
            # ⭐ INTRO REDUNDANCY FILTER: Remove intro-only slides since subtopic intro already covers
            data["slides"] = filter_out_intro_only_slides(data["slides"])
            # ⭐ INTRO RULE ENFORCEMENT: First slide must not be "Introduce"
            data["slides"] = enforce_no_introduce_first_slide(data["slides"])
    
            return data
    
        except Exception as e:
            print(f"Error parsing slide plan for {subtopic.get('name')}: {e}")
            # Let the loop retry
            continue

    # If we exhaust retries, return fallback
    print(f"Failed to generate valid slide plan after {MAX_RETRIES} attempts. Using fallback.")
    return _build_safe_fallback_plan(subtopic)


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
