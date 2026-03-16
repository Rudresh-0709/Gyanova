import json
import os
import sys
import random
from typing import Dict, Any, List, Optional, Tuple
from dotenv import load_dotenv

try:
    from ...llm.model_loader import load_openai
except ImportError:
    # Fallback for different import paths
    # Need 5 levels up to reach api-server root from gyml/
    root = os.path.dirname(os.path.abspath(__file__))
    for _ in range(5):
        root = os.path.dirname(root)
    if root not in sys.path:
        sys.path.append(root)
    from app.services.llm.model_loader import load_openai


# ═══════════════════════════════════════════════════════════════════════════
# VISUAL VARIANT ROTATION (Fix Visual Monotony)
# ═══════════════════════════════════════════════════════════════════════════

# Maps content_angle (and fallback intent) to a pool of renderable variants.
# Each angle has 2-3 variants that rotate based on slide index, item count,
# and layout history to prevent visual monotony.
INTENT_VARIANTS = {
    # Content Angles — 5-6 options per pool for maximum variety
    "overview":      ["cardGridIcon", "bigBullets", "cardGridSimple", "bulletIcon", "cardGridImage", "bulletCheck"],
    "mechanism":     ["timelineSequential", "timelineIcon", "processArrow", "processSteps", "processAccordion", "timeline"],
    "example":       ["cardGridImage", "cardGridIcon", "bulletIcon", "bigBullets", "cardGridSimple", "timeline"],
    "comparison":    ["comparisonCards", "comparisonProsCons", "comparisonBeforeAfter", "statsComparison", "cardGridSimple"],
    "application":   ["cardGridIcon", "bulletIcon", "processSteps", "processArrow", "bigBullets", "cardGridImage"],
    "visualization": ["stats", "statsComparison", "cardGridSimple", "cardGridIcon", "bigBullets"],
    "summary":       ["bigBullets", "bulletCheck", "bulletIcon", "cardGridSimple", "cardGridIcon"],
    # Intent fallbacks (used if content_angle is missing or generic)
    "explain":       ["cardGridIcon", "cardGridSimple", "bigBullets", "bulletIcon", "cardGridImage", "processSteps"],
    "narrate":       ["timelineSequential", "timelineIcon", "processArrow", "processSteps", "processAccordion", "timeline"],
    "compare":       ["comparisonCards", "comparisonProsCons", "comparisonBeforeAfter", "statsComparison", "cardGridSimple"],
    "list":          ["bigBullets", "bulletCheck", "processSteps", "bulletIcon", "cardGridSimple", "bulletCross"],
    "prove":         ["stats", "statsComparison", "cardGridSimple", "bigBullets", "cardGridIcon"],
    "teach":         ["cardGridIcon", "processSteps", "bulletIcon", "bigBullets", "cardGridSimple", "processArrow"],
    "summarize":     ["bigBullets", "bulletCheck", "bulletIcon", "cardGridSimple", "cardGridIcon"],
    "introduce":     ["cardGridSimple", "bigBullets", "cardGridIcon", "bulletIcon", "cardGridImage"],
    "demo":          ["processArrow", "processSteps", "processAccordion", "timelineSequential", "bulletIcon", "timeline"],
}


# ═══════════════════════════════════════════════════════════════════════════
# COMPOSITION STYLES (Fix Layout Monotony)
# ═══════════════════════════════════════════════════════════════════════════

# Each style defines a distinct block structure recipe.
# The style is injected into the LLM prompt so every slide doesn't follow
# the same intro → primary → annotation pattern.

COMPOSITION_STYLES = {
    "standard": {
        "label": "Standard",
        "recipe": "intro_paragraph → PRIMARY BLOCK → annotation_paragraph",
        "description": "Classic teaching pattern. Opens with a brief intro that frames the topic, "
                       "presents the primary visual, then closes with a contextual annotation.",
        "block_count": "3 blocks",
    },
    "visual_lead": {
        "label": "Visual Lead",
        "recipe": "PRIMARY BLOCK → callout",
        "description": "Opens directly with the primary visual block, no intro paragraph. "
                       "Closes with a single punchy callout. Feels immediate and visual-first.",
        "block_count": "2 blocks",
    },
    "context_heavy": {
        "label": "Context Heavy",
        "recipe": "context_paragraph → PRIMARY BLOCK",
        "description": "Opens with a rich context/framing paragraph that explains WHY this matters, "
                       "then delivers the primary visual. No closing block — let the content breathe.",
        "block_count": "2 blocks",
    },
    "minimal": {
        "label": "Minimal",
        "recipe": "PRIMARY BLOCK only",
        "description": "Just the primary teaching block, nothing else. Maximum breathing room "
                       "and visual impact. Best for bold, simple concepts.",
        "block_count": "1 block",
    },
    "bookend": {
        "label": "Bookend",
        "recipe": "callout → PRIMARY BLOCK → takeaway",
        "description": "Opens with a hook callout ('Did you know...'), presents the primary visual, "
                       "then closes with a memorable takeaway. Feels like a complete story.",
        "block_count": "3 blocks",
    },
    "narrative": {
        "label": "Narrative",
        "recipe": "intro_paragraph → PRIMARY BLOCK → annotation_paragraph → outro_paragraph",
        "description": "Full storytelling arc. Opens with scene-setting, presents visuals, "
                       "adds a detail/insight annotation, and closes with a forward-looking outro.",
        "block_count": "4 blocks",
    },
    "insight": {
        "label": "Insight",
        "recipe": "PRIMARY BLOCK → callout → takeaway",
        "description": "Opens with the visual, then adds a surprising insight callout, "
                       "and closes with the key takeaway. Conclusion-driven layout.",
        "block_count": "3 blocks",
    },
    "discovery": {
        "label": "Discovery",
        "recipe": "context_paragraph → PRIMARY BLOCK → annotation_paragraph",
        "description": "Opens with an exploratory question or 'what if' paragraph, "
                       "presents the answer through the primary visual, then annotates with details.",
        "block_count": "3 blocks",
    },
    "impact": {
        "label": "Impact",
        "recipe": "PRIMARY BLOCK → takeaway",
        "description": "Data-forward. Opens directly with the primary visual (stats, comparison, chart), "
                       "then hammers home the conclusion with a takeaway. No fluff.",
        "block_count": "2 blocks",
    },
    "guided": {
        "label": "Guided",
        "recipe": "intro_paragraph → PRIMARY BLOCK → callout",
        "description": "Teacher-led. Opens with a gentle intro that previews what's coming, "
                       "presents the primary visual, then highlights a key detail with a callout.",
        "block_count": "3 blocks",
    },
}

# Maps content_angle → ordered list of preferred composition styles.
# The picker cycles through these and avoids repeating the last 2 used.
ANGLE_TO_STYLES = {
    "overview":      ["standard", "guided", "visual_lead", "discovery", "bookend", "narrative"],
    "mechanism":     ["context_heavy", "guided", "narrative", "discovery", "standard", "visual_lead"],
    "example":       ["visual_lead", "minimal", "insight", "bookend", "guided", "standard"],
    "comparison":    ["impact", "context_heavy", "bookend", "discovery", "visual_lead", "insight"],
    "application":   ["guided", "narrative", "standard", "insight", "bookend", "discovery"],
    "visualization": ["visual_lead", "impact", "minimal", "insight", "standard", "context_heavy"],
    "summary":       ["insight", "impact", "minimal", "bookend", "visual_lead", "guided"],
    # Intent-level fallbacks
    "explain":       ["standard", "guided", "discovery", "context_heavy", "visual_lead", "narrative", "bookend"],
    "narrate":       ["narrative", "context_heavy", "guided", "discovery", "standard", "bookend"],
    "compare":       ["impact", "context_heavy", "bookend", "discovery", "insight", "visual_lead"],
    "list":          ["visual_lead", "standard", "minimal", "guided", "insight", "bookend"],
    "prove":         ["impact", "insight", "bookend", "visual_lead", "standard", "context_heavy"],
    "teach":         ["guided", "standard", "narrative", "discovery", "context_heavy", "visual_lead"],
    "summarize":     ["insight", "impact", "minimal", "bookend", "visual_lead", "guided"],
    "introduce":     ["minimal", "visual_lead", "bookend", "standard", "guided", "impact"],
    "demo":          ["guided", "narrative", "context_heavy", "standard", "visual_lead", "insight"],
}


# ═══════════════════════════════════════════════════════════════════════════
# LAYOUT COMPATIBILITY MATRIX (Fix Spatial Monotony)
# ═══════════════════════════════════════════════════════════════════════════

# Category A: Wide/Fixed-Width Content -> NO Left/Right
WIDE_VARIANTS = {
    "timeline", "timelineHorizontal", "timelineSequential", "timelineMilestone", "timelineIcon",
    "hub_and_spoke", "hierarchy_tree"
}

# Category B: Dynamic Grid Content (Flexible height/width)
WIDE_VARIANTS_MAYBE = {
    "comparison", "comparisonCards", "comparisonProsCons", "comparisonBeforeAfter", "statsComparison"
}

# Category C: Self-Contained Visuals & Data-Heavy -> Forced Blank
FORCED_BLANK_VARIANTS = {
    "table", "comparison_table",
    "cyclic_process", "processArrow", "processSteps", "feature_showcase", "diagram", "labeled_diagram"
}


def pick_composition_style(
    content_angle: str,
    intent: str,
    slide_index: int,
    composition_history: Optional[List[str]] = None,
) -> str:
    """
    Select a composition style that is contextually appropriate and non-repetitive.
    
    Strategy:
    1. Look up the preferred style pool for the content_angle (or intent fallback).
    2. Filter out the last 2 styles used (from composition_history).
    3. Cycle through remaining options based on slide_index.
    """
    key = content_angle if content_angle in ANGLE_TO_STYLES else intent
    pool = ANGLE_TO_STYLES.get(key, ["standard", "guided", "visual_lead", "discovery", "bookend", "narrative"])
    
    # Filter out recently used styles
    recent = set(composition_history[-2:]) if composition_history else set()
    fresh = [s for s in pool if s not in recent]
    if not fresh:
        fresh = pool  # All exhausted, reset
    
    return fresh[slide_index % len(fresh)]


def pick_variant(
    content_angle: str,
    intent: str,
    slide_index: int,
    item_count: int,
    layout_history: List[str],
    variant_history: Optional[List[str]] = None,
) -> Tuple[str, str]:
    """
    Pick a (variant, image_layout) pair using weighted selection, enforcing Strict Variety 
    and the Layout Compatibility Matrix.

    Goal: achieve visual variety while optimizing layout for spatial constraints.
    - Max 2 uses per variant strictly enforced.
    - Wide components get full-width vertical layouts (top/bottom) or blank.
    - Tall grids get vertical constraints (left/right) or blank.
    - Self-contained components (diagrams, processes) force 'blank' to avoid clutter.
    - Dense slides get 'blank' to maximize space.
    """
    # 1. Resolve variant pool
    key = content_angle if content_angle in INTENT_VARIANTS else intent
    pool = INTENT_VARIANTS.get(key, ["cardGridIcon", "bigBullets", "cardGridSimple"])

    # 2. History Filter (Strict Max 2 Uses)
    full_history = variant_history or []
    usage_counts = {}
    for v in full_history:
        usage_counts[v] = usage_counts.get(v, 0) + 1

    eligible_variants = [v for v in pool if usage_counts.get(v, 0) < 2]
    # If all variants in pool have been used twice or more, fallback to those with lowest usage
    if not eligible_variants:
        min_usage = min([usage_counts.get(v, 0) for v in pool]) if pool else 0
        eligible_variants = [v for v in pool if usage_counts.get(v, 0) == min_usage]

    # Exclude last slide's variant strictly to avoid sequential monotony
    last_v = full_history[-1] if full_history else None
    fresh = [v for v in eligible_variants if v != last_v] or eligible_variants

    # 3. Weighted Selection
    weights = []
    for v in fresh:
        count = usage_counts.get(v, 0)
        if count == 0:
            weights.append(3.0)   # Never used — strongly preferred
        else:
            weights.append(1.0)   # Used once

    # Selection
    total = sum(weights)
    if total > 0:
        normalized = [w / total for w in weights]
        rng = random.Random(slide_index * 7 + len(full_history) * 13)
        variant = rng.choices(fresh, weights=normalized, k=1)[0]
    else:
        variant = fresh[slide_index % len(fresh)]

    # Use the shared layout picker
    image_layout = pick_layout(
        variant=variant,
        item_count=item_count,
        slide_index=slide_index,
        layout_history=layout_history,
    )

    return variant, image_layout


def pick_layout(
    variant: Optional[str],
    item_count: int,
    slide_index: int,
    layout_history: List[str],
) -> str:
    """Shared logic for picking an image_layout based on rotation and compatibility."""
    if slide_index == 0:
        return "behind"

    if variant in FORCED_BLANK_VARIANTS:
        return "blank"

    if item_count > 6:
        return "blank"

    if variant in WIDE_VARIANTS:
        # Category A (Wide) -> Top/Bottom
        if slide_index % 4 in [1, 2]:
            return "bottom"
        else:
            return "top"

    # Category D or B (Flexible/Tall) -> Alternating sidebars
    recent_lr = [ly for ly in reversed(layout_history) if ly in ["left", "right"]]
    last_lr = recent_lr[0] if recent_lr else ""

    # Primary rotation: left -> right
    if last_lr == "left":
        image_layout = "right"
    else:
        image_layout = "left"

    # Variety: Occasionally use top/bottom even if not wide
    flexible_count = len([ly for ly in layout_history if ly in ["left", "right"]])
    if (flexible_count + 1) % 3 == 0:
        # Avoid top if it was used very recently
        if layout_history and layout_history[-1] == "top":
            return "bottom"
        else:
            return "top" if (slide_index % 2 == 0) else "bottom"

    return image_layout


class GyMLContentGenerator:
    """
    Standalone utility to generate GyML-compliant slide content using LLMs.
    Content-First: Generates visual content from learning objectives, WITHOUT narration.
    """

    # Block types that qualify as the "primary teaching structure"
    PRIMARY_BLOCK_TYPES = {
        "bullet_list",
        "timeline",
        "comparison_table",
        "card_grid",
        "smart_layout",
        "numbered_list",
        "diagram",
        "key_value_list",
        "stats",
        "step_list",
        "comparison",
        "hierarchy_tree",
        "labeled_diagram",
        "split_panel",
        "formula_block",
        "hub_and_spoke",
        "process_arrow_block",
        "cyclic_process_block",
        "feature_showcase_block",
        "code",
        "table",
        "rich_text",
    }

    def __init__(self):
        self.llm = load_openai()
        self.schema = self._load_schema()

    def _load_schema(self) -> str:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        schema_path = os.path.join(current_dir, "llm_schema.json")
        try:
            with open(schema_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            print(f"Error loading schema: {e}")
            return "{}"

    def generate(
        self,
        title: str,
        goal: str,
        purpose: str,
        subtopic: str,
        content_angle: str = "overview",
        context: str = "",
        layout_history: List[str] = None,
        template_name: str = None,
        slide_index: int = 0,
        intent: str = "explain",
        composition_style: Optional[str] = None,
        composition_history: Optional[List[str]] = None,
        variant_history: Optional[List[str]] = None,
        image_role: str = "accent",
    ) -> Dict[str, Any]:
        """
        Generate structured GyML content from slide metadata (Content-First).
        No narration is needed — visuals are designed from the learning objective.
        """
        history_str = ", ".join(layout_history) if layout_history else "None"

        # Sanitize template name
        normalized_template = template_name.strip() if template_name else ""

        # These templates prioritize premium visual style over dense content
        SPARSE_TEMPLATES = [
            "Title card",
            "Image and text",
            "Text and image",
            "Rich text",
            "Formula block",
            "Definition",
            "Quote",
        ]
        is_sparse = normalized_template in SPARSE_TEMPLATES

        # ── VISUAL VARIANT & LAYOUT ROTATION ─────────────────────────
        # Templates that use top-level block types (not smart_layout) skip variant rotation
        # but SHOULD still participate in image_layout rotation.
        TOP_LEVEL_BLOCK_TEMPLATES = [
            "Comparison table", "Key-Value list", "Labeled diagram",
            "Hierarchy tree", "Split panel", "Formula block",
            "Hub and spoke", "Process arrow block", "Cyclic process block",
            "Feature showcase block",
        ]
        
        # Determine if we should at least rotate the image_layout
        # Sparse templates (Title, Image and text) and standard teaching slides should rotate.
        # Only hard-structured templates like Comparison Table might want to force a specific layout (blank).
        can_rotate_layout = normalized_template not in ["Comparison table", "Formula block", "Code"]
        
        uses_smart_layout = (
            not is_sparse and normalized_template not in TOP_LEVEL_BLOCK_TEMPLATES
        )

        chosen_variant, chosen_layout = None, None
        rotation_directives = ""
        
        # ── COMPREHENSIVE LAYOUT ROTATION ────────────────────────────
        # Even if not using smart variant, we should rotate the image layout
        if can_rotate_layout:
            estimated_items = 4
            # If it uses a smart layout variant pool, pick both. Otherwise just pick layout.
            if uses_smart_layout:
                chosen_variant, chosen_layout = pick_variant(
                    content_angle=content_angle,
                    intent=intent,
                    slide_index=slide_index,
                    item_count=estimated_items,
                    layout_history=layout_history or [],
                    variant_history=variant_history,
                )
            else:
                # Use the shared layout picker even if no variant rotation is needed
                chosen_layout = pick_layout(
                    variant=None, # Not using smart variant
                    item_count=estimated_items,
                    slide_index=slide_index,
                    layout_history=layout_history or [],
                )

            rotation_directives = f"⚡ MANDATORY LAYOUT: Use '{chosen_layout}' as the slide-level image_layout."
            if chosen_variant:
                rotation_directives += f"\n        ⚡ MANDATORY VARIANT: Use '{chosen_variant}' for the primary smart_layout block."
            
            print(f"    🎨 Rotation: variant='{chosen_variant}', layout='{chosen_layout}' for index={slide_index}")

        # ── IMAGE ROLE ROUTING ──────────────────────────
        image_role_directives = ""
        if image_role == "content":
            # Override layout to sidebars for inline content images
            if chosen_layout not in ["left", "right"]:
                chosen_layout = "right" if (slide_index % 2 == 1) else "left"
            
            image_role_directives = f"""
        ⚡ IMAGE ROLE: CONTENT (MANDATORY)
           You MUST include an 'image' block in `contentBlocks`.
           This image is pedagogically necessary. Set a descriptive `imagePrompt`.
           Set `image_layout` to "{chosen_layout}". Do not use an accent image.
            """
        elif image_role == "none":
            chosen_layout = "blank"
            image_role_directives = """
        ⚡ IMAGE ROLE: NONE (MANDATORY)
           No images should be generated for this slide.
           Set `image_layout` to "blank". DO NOT include an 'image' block.
            """
        else:
            # Default accent behavior
            image_role_directives = f"""
        ⚡ IMAGE ROLE: ACCENT
           The image on this slide is decorative (in the sidebar or background).
           Do NOT include an 'image' block within `contentBlocks`.
           Instead, set `imagePrompt` at the ROOT level of the JSON.
           Suggested layout: "{chosen_layout}".
            """

        # ── COMPOSITION STYLE SELECTION ──────────────────────────
        # Pick a composition style if not explicitly provided
        if composition_style is None:
            composition_style = pick_composition_style(
                content_angle=content_angle,
                intent=intent,
                slide_index=slide_index,
                composition_history=composition_history,
            )
        style_info = COMPOSITION_STYLES.get(composition_style, COMPOSITION_STYLES["standard"])
        composition_recipe_directive = f"""
        ⚡ MANDATORY COMPOSITION STYLE: '{style_info['label']}'
           Recipe: {style_info['recipe']}
           Description: {style_info['description']}
           Target block count: {style_info['block_count']}
           YOU MUST follow this exact block pattern. Do NOT add extra blocks beyond this recipe.
        """
        print(f"    🎨 Composition style: {composition_style} ({style_info['recipe']})")

        prompt = f"""
        You are an expert educational content designer who creates visually rich, cognitively balanced slides.
        Design a structured visual slide using GyML (Gyanova Markup Language) based on the learning objective and content angle.

        ═══════════════════════════════════════════════
        CONTEXT & PEDAGOGY
        ═══════════════════════════════════════════════
        Topic: {subtopic}
        Slide Title: {title}
        Learning Goal: {goal}
        Purpose: {purpose}
        Content Angle: {content_angle}
        Recommended Template: {template_name}
        {f"Research Context: {context}" if context else ""}
        Recently Used Layouts: {history_str}

        ═══════════════════════════════════════════════
        CONTENT-FIRST DESIGN PRINCIPLES
        ═══════════════════════════════════════════════
        You are designing the VISUAL CONTENT of the slide. A teacher's narration will be generated AFTER
        to explain this content. Therefore:
        1. Focus on creating clear, self-explanatory visual structures.
        2. On-screen text should be KEY SUMMARIES — card headings: 3-6 words, descriptions: 1-2 sentences.
        3. The content should stand on its own visually — a student should understand the structure at a glance.
        4. DO NOT write narration text. Only write concise on-screen labels, headings, and descriptions.

        ═══════════════════════════════════════════════
        CONTENT ANGLE GUIDELINES
        ═══════════════════════════════════════════════
        Use the Content Angle to decide HOW to present the information:
        • overview     → Broad introduction. Use cardGridIcon, bigBullets, or intro_paragraph.
        • mechanism    → How it works. Use timeline, processArrow, processSteps, or diagram.
        • example      → Concrete case. Use split_panel, two-column, or cardGridImage.
        • comparison   → Side-by-side. Use comparisonCards, comparisonProsCons, or comparison_table.
                         CRITICAL: For comparisons, you MUST use the structured `criteria` and `subjects` schema.
                         • `criteria`: Array of dimension objects {{id, label}} (e.g., Purpose, Strength).
                         • `subjects`: Array of subject objects {{id, label, values}}.
                         • `values`: Array of {{criterion_id, value}} matching the defined criteria.
                         • `conclusion`: A short summary sentence explaining the key difference.
                         Example: Criteria: [Purpose, Efficiency]. Subjects: [SQL, NoSQL].
        • application  → Real-world use. Use cardGridIcon with practical icons, or key_value_list.
        • visualization → Visual representation. Use labeled_diagram, hierarchy_tree, or diagramFlowchart.
        • summary      → Key takeaways. Use bigBullets, bulletCheck, or stats.

        ═══════════════════════════════════════════════
        NODE SELECTION RULES (CRITICAL)
        ═══════════════════════════════════════════════
        1. SCIENCE & MATH: If the topic involves a formula or scientific law, USE 'formula_block'.
        2. DENSITY: For complex topics, use 'split_panel' for diagram + explanation.
        3. VARIETY: Do NOT repeat the same layout used in recent slides.
        • If the last slide had the image on the 'right', use 'left' or 'top' for this one.
        • Every lesson must have at least 3 DIFFERENT smart_layout types across its slides.

        ═══════════════════════════════════════════════
        STEP 1: DETERMINE THE INTENT & LAYOUT
        ═══════════════════════════════════════════════
        1. Choose ONE intent based on the learning goal:
           introduce — Hook + context (first impression, minimal text, striking visual)
           explain   — Clarity + progression (concept → diagram → example)
           narrate   — Chronological story (timeline, milestones, journey)
           compare   — Show differences/similarities (side-by-side, pros/cons)
           list      — Enumerate features, steps, items
           prove     — Evidence, data, statistics
           summarize — Reinforce key points (brevity + impact, 3-5 bullets/cards)
           teach     — Definitions, code, diagrams (build understanding)
           demo      — Walkthrough, live example

        2. Choose ONE layout for the accent image. 
           VARIETY IS CRITICAL: Do NOT default to 'left'. You MUST rotate between layouts across the lesson.
           right  — Image on the right (Standard, balanced)
           left   — Image on the left (Great for alternating variety)
           top    — Full-width banner image at the top (High impact hero)
           bottom — Full-width banner image at the bottom (Modern visual anchor)
           blank  — No accent image (Use only if content is extremely dense)

        ═══════════════════════════════════════════════
        STEP 2: BUILD AROUND THE PRIMARY BLOCK
        ═══════════════════════════════════════════════
        Every slide MUST have ONE clear primary teaching block. Build the slide around it.

        A. CHOOSE THE PRIMARY BLOCK
           This is the ONE structured block that carries the slide's teaching payload.
           {"USE 'smart_layout'" if not is_sparse else "AVOID 'smart_layout'"}
           {"" if is_sparse else f"This is a '{template_name}' slide. DO NOT use 'smart_layout'. Focus on a high-impact title and a single intro_paragraph." if is_sparse else ""}

        {rotation_directives}

           TEMPLATE → PRIMARY BLOCK MAPPING:
           • bullets/Title with bullets → smart_layout (bulletIcon or bigBullets)
           • Comparison / Two columns → smart_layout (comparison, comparisonProsCons, comparisonBeforeAfter, or split_panel)
           • Comparison table → comparison_table (MUST USE `comparison_table` block type)
           • Process/Steps → smart_layout (processArrow or processAccordion)
           • Timeline → smart_layout (timelineSequential or timelineIcon)
           • Stats/Metrics → smart_layout (stats or statsComparison)
           • Key-Value list → key_value_list (top-level block)
           • Labeled diagram → labeled_diagram (top-level block)
           • Hierarchy tree → hierarchy_tree (top-level block)
           • Card grid → smart_layout (cardGridIcon or cardGridSimple)
           • Formula → formula_block (top-level block)
            • Cyclic process block → cyclic_process_block (MUST USE `cyclic_process_block` block type)
               ⚡ PREMIUM LAYOUT: These cards 'float' near the central wheel.
               You MUST provide rich, multi-sentence descriptions (15-25 words) per item to fill these teaching containers.
               Do not just use single words.

           PRIMARY BLOCK ITEM COUNT:
           • The primary block MUST contain 2–6 items (never more than 6).
           • 2-3 items → for high-level overviews or compact slides
           • 4 items → medium explanations and process slides
           • 5-6 items → dense summaries, detailed comparisons, or timelines

        B. ADD SUPPORTING CONTEXT (1-3 blocks around the primary block)
           These blocks frame, introduce, or annotate the primary block:
           • 'intro_paragraph'      — Opens the slide, sets the stage (use at TOP)
           • 'context_paragraph'    — Background or "why this matters"
           • 'annotation_paragraph' — Side note, tip, or fun fact (after primary block)
           • 'outro_paragraph'      — Summary or closing thought (at BOTTOM)
           • 'caption'              — Describes a visual element (directly after it)
           • 'callout'              — Highlight a key insight. Keep to 1-2 lines.
           • 'takeaway'             — The single most important point to remember.

        C. COMPOSITION STYLE (FOLLOW THIS EXACT RECIPE FOR THIS SLIDE):
           {composition_recipe_directive}

           IMPORTANT: The recipe above specifies which supporting blocks to use and their order.
           Do NOT deviate. If the recipe says "PRIMARY BLOCK only", output only the primary block.
           If the recipe says "callout → PRIMARY BLOCK → takeaway", output exactly those 3 blocks in that order.

           Variant Dictionary:
           TIMELINES: timeline, timelineHorizontal, timelineSequential, timelineMilestone, timelineIcon
           CARD GRIDS: cardGrid, cardGridIcon, cardGridSimple, cardGridImage
           STATS: stats, statsComparison, statsPercentage
           BULLETS: bigBullets, bulletIcon, bulletCheck, bulletCross
           PROCESS STEPS: processSteps, processArrow, processAccordion
           COMPARISONS: comparison, comparisonProsCons, comparisonBeforeAfter
           QUOTES: quote, quoteTestimonial, quoteCitation
           DEFINITIONS: definition
           CODE: codeSnippet, codeComparison
           DIAGRAMS & TREES: diagramFlowchart, diagramHierarchy, diagramCycle, diagramPyramid, labeled_diagram, hierarchy_tree
           TABLES & MATRICES: table, tableStriped, tableHighlight, comparison_table
           LISTS & KEY-VALUE: key_value_list, numbered_list, bigBullets, bulletIcon
           TEXT: rich_text, split_panel
           MATH: formula_block

        ═══════════════════════════════════════════════
        STEP 3: DENSITY VARIATION
        ═══════════════════════════════════════════════
        Vary the number of blocks per slide to create visual rhythm across the lesson.
        Do NOT make every slide the same density. You MUST intentionally vary between Compact, Medium, and Dense slides.

        DENSITY LEVELS:
          Compact (2 blocks, 2-3 items) — High impact, breathing room. Best for intros, hooks, or single-concept slides.
            Example: intro_paragraph + smart_layout(bigBullets, 3 items max)
          Medium (3-4 blocks, 3-4 items) — Balanced teaching density. Best for most explanations.
            Example: intro_paragraph + smart_layout(cardGridIcon) + callout
          Dense (5-7 blocks or 5-6 items) — Deep dive density. Best for summaries, comparisons, or technical slides.
            Example: intro_paragraph + context_paragraph + smart_layout(processArrow, 5+ items) + annotation_paragraph + takeaway

        RULES:
          • Max 7 content blocks per slide (hard limit).
          • Primary block = 70% visual weight. Supporting blocks = 30%.
          • The primary block MUST be the visual center of the slide.
          • ONE primary block only. NEVER put two smart_layouts on the same slide.
          • Max word count: ~300 words (hard limit: 400).

        CONTENT ORDERING:
          Always: [optional intro] → [optional context] → PRIMARY BLOCK → [optional annotation/callout/takeaway]

        PROHIBITED:
          ✗ Dense paragraph + complex diagram (cognitive overload)
          ✗ Multiple competing smart_layouts (only ONE primary)
          ✗ More than 6 items in the primary block alongside supporting paragraphs

        {"SPARSE VISUAL STYLE: For this '" + template_name + "' slide, keep it minimal. Use only a title and a single intro_paragraph. DO NOT use smart_layout." if is_sparse else ""}

        {image_role_directives}

        ═══════════════════════════════════════════════
        STEP 4: FORMATTING & OUTPUT
        ═══════════════════════════════════════════════
        • Use 'ri-*' icon names (RemixIcon library). Examples: ri-lightbulb-line, ri-rocket-line.
        • Keep paragraph text informative: 2-4 sentences max.
        • Smart layout item text: 1-2 sentences each.

        IMAGE PROMPT RULES (for the 'imagePrompt' field):
        • Capture the CORE THEME or MOOD — NOT the content structure.
        • Do NOT reference "timeline", "cards", "chart", "diagram" in the imagePrompt.
        • DO describe a vivid, atmospheric scene that evokes the slide's central idea.

        PRIMARY BLOCK INDEX:
        You MUST include a "primary_block_index" field in the root of your JSON output.
        This is the 0-based index of the main teaching block within "contentBlocks".
        The primary block should be the structured content block (smart_layout, key_value_list, etc.)
        that represents the core visual teaching structure.

        STRICT OUTPUT SCHEMA (JSON ONLY):
        CRITICAL: The `contentBlocks` MUST be an array of objects `[{{...}}, {{...}}]`. Never null or empty.
        {self.llm_schema_placeholder if hasattr(self, 'llm_schema_placeholder') else self.schema}

        OUTPUT FORMAT:
        Output ONLY the valid JSON object. No preamble, no explanation, no markdown fences.
        """

        response = self.llm.invoke([{"role": "user", "content": prompt}])

        # DEBUG: Show raw GyML output
        print("\n--- [DEBUG] GyML GENERATION LLM OUTPUT ---")
        print(response.content)
        print("------------------------------------------\n")

        content = response.content.replace("```json", "").replace("```", "").strip()

        try:
            result = json.loads(content)
        except json.JSONDecodeError as e:
            print(f"Failed to parse LLM response as JSON: {e}")
            result = {
                "title": title,
                "intent": "explain",
                "image_role": image_role,
                "contentBlocks": [
                    {
                        "type": "paragraph",
                        "text": "Generation failed. Please check logs.",
                    }
                ],
            }

        # Ensure image_role is tracked
        result["image_role"] = image_role

        # ── POST-GENERATION ENFORCEMENT ──────────────────
        # Force the rotation choices if they were mandatory
        if chosen_layout:
            result["layout"] = chosen_layout
        
        if chosen_variant:
            # Find the primary block and force its variant
            blocks = result.get("contentBlocks", [])
            primary_idx = result.get("primary_block_index", 0)
            if 0 <= primary_idx < len(blocks):
                block = blocks[primary_idx]
                if block.get("type") == "smart_layout":
                    block["variant"] = chosen_variant

        # Validate and ensure primary_block_index
        return self._validate_primary_block(result)

    def _validate_primary_block(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ensure primary_block_index is valid and points to a structured teaching block.
        If the LLM didn't provide one or it's invalid, infer it from the content blocks.
        """
        blocks = content.get("contentBlocks", [])
        idx = content.get("primary_block_index")

        if (
            idx is not None
            and isinstance(idx, int)
            and 0 <= idx < len(blocks)
            and blocks[idx].get("type") in self.PRIMARY_BLOCK_TYPES
        ):
            return content  # Valid

        # Infer: find the first structured block
        for i, block in enumerate(blocks):
            if block.get("type") in self.PRIMARY_BLOCK_TYPES:
                content["primary_block_index"] = i
                return content

        # Fallback: use 0
        content["primary_block_index"] = 0
        return content


if __name__ == "__main__":
    # Test content-first generation
    generator = GyMLContentGenerator()
    result = generator.generate(
        title="Timeline of Computer Generations",
        goal="Explain the chronological development of computer generations from 1st to 5th.",
        purpose="process",
        subtopic="Computer Generations",
        content_angle="mechanism",
        template_name="Timeline",
    )
    print(json.dumps(result, indent=2))
