import json
import os
import sys
from typing import Dict, Any, List, Optional
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
        • comparison   → Side-by-side. Use comparison, comparisonProsCons, or comparison_table.
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

        2. Choose ONE layout for the accent image:
           right  — Image on the right (Standard, balanced)
           left   — Image on the left (Great for alternating variety)
           top    — Full-width image at the top (High impact, hero feel)
           blank  — No accent image (Use only if content is extremely dense or for variety)

        ═══════════════════════════════════════════════
        STEP 2: BUILD AROUND THE PRIMARY BLOCK
        ═══════════════════════════════════════════════
        Every slide MUST have ONE clear primary teaching block. Build the slide around it.

        A. CHOOSE THE PRIMARY BLOCK
           This is the ONE structured block that carries the slide's teaching payload.
           {"USE 'smart_layout'" if not is_sparse else "AVOID 'smart_layout'"}
           {"" if is_sparse else f"This is a '{template_name}' slide. DO NOT use 'smart_layout'. Focus on a high-impact title and a single intro_paragraph." if is_sparse else ""}

           TEMPLATE → PRIMARY BLOCK MAPPING:
           • bullets/Title with bullets → smart_layout (bulletIcon or bigBullets)
           • Comparison → smart_layout (comparison or comparisonProsCons) or comparison_table
           • Process/Steps → smart_layout (processArrow or processAccordion)
           • Timeline → smart_layout (timelineMilestone or timelineSequential)
           • Stats/Metrics → smart_layout (stats or statsComparison)
           • Key-Value list → key_value_list (top-level block)
           • Labeled diagram → labeled_diagram (top-level block)
           • Hierarchy tree → hierarchy_tree (top-level block)
           • Card grid → smart_layout (cardGridIcon or cardGridSimple)
           • Formula → formula_block (top-level block)
           • Code → code (top-level block)

           PRIMARY BLOCK ITEM COUNT:
           • The primary block MUST contain 3–6 items (never fewer than 3, never more than 6).
           • 3 items → for high-level overviews or comparison slides
           • 4 items → standard explanations and process slides
           • 5-6 items → detailed timelines, feature lists, or summaries

        B. ADD SUPPORTING CONTEXT (1-3 blocks around the primary block)
           These blocks frame, introduce, or annotate the primary block:
           • 'intro_paragraph'      — Opens the slide, sets the stage (use at TOP)
           • 'context_paragraph'    — Background or "why this matters"
           • 'annotation_paragraph' — Side note, tip, or fun fact (after primary block)
           • 'outro_paragraph'      — Summary or closing thought (at BOTTOM)
           • 'caption'              — Describes a visual element (directly after it)
           • 'callout'              — Highlight a key insight. Keep to 1-2 lines.
           • 'takeaway'             — The single most important point to remember.

        C. COMPOSITION RECIPES (follow these patterns):
           ┌─────────────────────────────────────────────────────────────┐
           │ BULLET SLIDE        → intro_paragraph + smart_layout(bulletIcon) │
           │ TIMELINE SLIDE      → smart_layout(timelineSequential) + callout │
           │ DIAGRAM SLIDE       → smart_layout(diagramFlowchart) + annotation_paragraph │
           │ COMPARISON SLIDE    → intro_paragraph + smart_layout(comparison) + takeaway │
           │ STATS SLIDE         → smart_layout(stats) + callout │
           │ PROCESS SLIDE       → intro_paragraph + smart_layout(processArrow) │
           │ CARD GRID SLIDE     → intro_paragraph + smart_layout(cardGridIcon) + outro_paragraph │
           │ KEY-VALUE SLIDE     → intro_paragraph + key_value_list │
           └─────────────────────────────────────────────────────────────┘

           Variant Dictionary:
           TIMELINES: timeline, timelineHorizontal, timelineSequential, timelineMilestone
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
        Do NOT make every slide the same density.

        DENSITY LEVELS:
          Compact (2-3 blocks) — High impact, breathing room. Best for intros, hooks, or single-concept slides.
            Example: intro_paragraph + smart_layout(bigBullets)
          Standard (3-4 blocks) — Balanced teaching density. Best for most explanations.
            Example: intro_paragraph + smart_layout(cardGridIcon) + callout
          Rich (4-5 blocks) — Deep dive density. Best for summaries, comparisons, or technical slides.
            Example: intro_paragraph + smart_layout(processArrow) + annotation_paragraph + takeaway

        RULES:
          • Max 5 content blocks per slide (hard limit).
          • Primary block = 70% visual weight. Supporting blocks = 30%.
          • The primary block MUST be the visual center of the slide.
          • ONE primary block only. NEVER put two smart_layouts on the same slide.
          • Max word count: ~300 words (hard limit: 400).

        CONTENT ORDERING:
          Always: [optional intro] → PRIMARY BLOCK → [optional annotation/callout/takeaway]

        PROHIBITED:
          ✗ Dense paragraph + complex diagram (cognitive overload)
          ✗ Multiple competing smart_layouts (only ONE primary)
          ✗ More than 6 items in the primary block alongside supporting paragraphs

        {"SPARSE VISUAL STYLE: For this '" + template_name + "' slide, keep it minimal. Use only a title and a single intro_paragraph. DO NOT use smart_layout." if is_sparse else ""}

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
                "contentBlocks": [
                    {
                        "type": "paragraph",
                        "text": "Generation failed. Please check logs.",
                    }
                ],
            }

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
