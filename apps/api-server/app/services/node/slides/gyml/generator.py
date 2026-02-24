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
    """

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
        narration: str,
        title: str,
        purpose: str,
        subtopic: str,
        hint: str = "",
        context: str = "",
        point_count: int = 0,
        layout_history: List[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate structured GyML content from narration.

        Args:
            point_count: Number of narration segments. When > 1, the primary
                         smart_layout MUST have exactly this many items so
                         animations stay in sync with audio.
            layout_history: List of recently used layout variants or intents
                            to avoid repetition and ensure variety.
        """
        history_str = ", ".join(layout_history) if layout_history else "None"

        prompt = f"""
        You are an expert educational content designer who creates visually rich, cognitively balanced slides.
        Convert the Teacher's Narration into a structured visual slide using GyML (Gyanova Markup Language).

        SLIDE CONTEXT:
        - Title: {title}
        - Purpose/Intent: {purpose}
        - Subtopic: {subtopic}
        - Narration: {narration}
        {f"- Additional Context: {context}" if context else ""}
        - RECENTLY USED LAYOUTS: {history_str}

        ═══════════════════════════════════════════════
        NODE SELECTION RULES (CRITICAL)
        ═══════════════════════════════════════════════
        1. SCIENCE & MATH: If the narration contains a mathematical formula or scientific law (like Snell's Law), YOU MUST USE 'formula_block'. Do NOT use 'card_grid' for formulas.
        2. DENSITY: For complex topics, use 'split_panel' to show a diagram on one side and an explanation on the other.
        3. VARIETY: Do NOT repeat the same 'smart_layout' or 'block_type' used in recent slides.
        • If the last slide had the image on the 'right', use 'left' or 'top' for this one.
        • Aim for a dynamic progression: hook (introduce) -> explain -> compare -> list -> summarize.
        • Every lesson must have at least 3 DIFFERENT smart_layout types across its slides.
        • Use diverse variants: timelineMilestone instead of just timeline; cardGridIcon instead of cardGrid.

        ═══════════════════════════════════════════════
        STEP 1: DETERMINE THE INTENT & LAYOUT
        ═══════════════════════════════════════════════
        1. Choose ONE intent based on the narration's goal:
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

        3. Choose a VISUAL DENSITY level:
           Sparse (High Impact) — Minimal text, 1-2 items, large typography. Use for intros, hooks, or big quotes.
           Balanced — Standard educational density. 3-4 items, moderate text. Great for most explanations.
           Dense (Deep Dive) — 5+ items, detailed text, complex components. Use for technical deep dives or summaries.

        ═══════════════════════════════════════════════
        STEP 2: COMPOSE CONTENT BLOCKS
        ═══════════════════════════════════════════════
        A. STRUCTURE USING SEMANTIC PARAGRAPHS
           Place these to frame the main content:
           • 'intro_paragraph'      — Opens the slide, sets the stage (use at TOP)
           • 'context_paragraph'    — Background, history, or "why this matters" (before or after main content)
           • 'annotation_paragraph' — Side note, tip, or fun fact (after main content)
           • 'outro_paragraph'      — Summary or closing thought (at BOTTOM)
           • 'caption'              — Describes a figure or visual element (directly after that element)
           Use 1-2 paragraphs per slide. Do NOT use more than 2 paragraphs—the 'smart_layout' should do the heavy lifting.

        B. PRIMARY CONTENT: USE 'smart_layout'
           Every slide SHOULD have exactly ONE 'smart_layout' block as the primary visualization.
           Choose the best variant:

           TIMELINES:
             timeline, timelineHorizontal, timelineSequential, timelineMilestone

           CARD GRIDS:
             cardGrid, cardGridIcon, cardGridSimple, cardGridImage

           STATS:
             stats, statsComparison, statsPercentage

           BULLETS:
             bigBullets, bulletIcon, bulletCheck, bulletCross

           PROCESS STEPS:
             processSteps, processArrow, processAccordion

           COMPARISONS:
             comparison, comparisonProsCons, comparisonBeforeAfter

           QUOTES:
             quote, quoteTestimonial, quoteCitation

           DEFINITIONS:
             definition

           CODE:
             codeSnippet, codeComparison

            DIAGRAMS & TREES:
              diagramFlowchart, diagramHierarchy, diagramCycle, diagramPyramid, labeled_diagram, hierarchy_tree

            TABLES & MATRICES:
              table, tableStriped, tableHighlight, comparison_table

            LISTS & KEY-VALUE:
              key_value_list, numbered_list, bullet_list (general)

            TEXT POWERHOUSES:
              rich_text (deep narrative), split_panel (side-by-side independence)

            MATH & SYMBOLS:
              formula_block

         C. OPTIONAL SUPPORTING BLOCKS (max 1-2):
            • 'callout'  — Highlight a key insight. Max 1-2 per slide. Keep to 1-2 lines.
            • 'takeaway' — The single most important point to remember.

        ═══════════════════════════════════════════════
        STEP 3: APPLY COMPOSITION RULES
        ═══════════════════════════════════════════════
        DENSITY LIMITS (non-negotiable):
          • Total content blocks per slide: 3-5 (1-2 paragraphs + 1 smart_layout + 0-2 supporting)
          • Max word count: ~300 words (hard limit: 400)
          • One primary focus per slide. 70% visual weight to the primary element, 30% to supporting.

        CONTENT ORDERING (Adaptive):
          Usually follow: Intro -> Smart Layout -> Annotation -> Outro.
          However, you can put a 'callout' or 'takeaway' at the top if it creates a better hook.

        INTENT-SPECIFIC GUIDELINES:
          introduce → Headline + 1 striking visual/card layout. Focus on emotion and the "why".
          explain   → intro_paragraph + layout variant + annotation for nuance.
          narrate   → Use timelines (rotate variants!) + short framing text.
          compare   → Use comparison layouts. Alternate layout to 'left' for balance.
          list      → Use grid or icon layouts. Avoid simple bullet lists if possible.
          prove     → Stats/Table + Callout with key insight.
          summarize → 3-5 cards or bullets + takeaway. Keep it punchy.
          teach     → Definition/Code/Diagram + annotation. Prioritize clarity over flash.
          demo      → Code or processSteps + caption describing the output.

        PROHIBITED COMBINATIONS (never do these):
          ✗ Dense paragraph + complex diagram on same slide (cognitive overload)
          ✗ Definition + detailed timeline (conflicting purposes)
          ✗ Multiple competing smart_layouts on one slide (only ONE primary)
          ✗ More than 6 bullets alongside a large card grid (cramped)
          ✗ Quote + data table on same slide (emotional vs. analytical clash)
          • Aim for visual pacing: Alternate between Dense and Sparse slides to keep the student engaged. Never do more than 2 Dense slides in a row.
          • Every lesson must have a mix of all 3 density levels.

        ON-SCREEN TEXT vs NARRATION (critical for engagement):
          • On-screen text is the KEY SUMMARY — card headings: 3-6 words, card descriptions: 2-3 sentences (the "what" and the "result")
          • The narration IS the full explanation — it gives context, examples, analogies
          • NEVER copy narration text verbatim into card descriptions or paragraphs
          • Students read the slide while listening — if text = narration, it feels like reading a teleprompter
          • On-screen = labels and key facts with brief elaboration. Narration = the teacher explaining them.

        {f'''ANIMATION ALIGNMENT (non-negotiable):
          The narration has exactly {point_count} spoken segments/points.
          Your primary smart_layout MUST have exactly {point_count} items.
          Each item maps 1:1 to a narration segment for animation sync.
          If the narration has 1 segment, use a single-content layout (paragraph, definition, or quote).''' if point_count > 0 else ''}

        ═══════════════════════════════════════════════
        STEP 4: FORMATTING
        ═══════════════════════════════════════════════
        • Use 'ri-*' icon names (RemixIcon library). Examples: ri-lightbulb-line, ri-rocket-line, ri-code-line.
        • Keep paragraph text informative: 2-4 sentences max.
        • Smart layout item text: 2-3 sentences each.
        • Callout text: 2-3 lines maximum.

        IMAGE PROMPT RULES (for the 'imagePrompt' field):
        • The imagePrompt must capture the CORE THEME or MOOD of the slide — NOT describe the content structure.
        • Do NOT reference content types like "timeline", "cards", "bullet points", "chart", or "diagram" in the imagePrompt.
        • Do NOT list specific data points, dates, or stats from the slide content.
        • DO describe a vivid, atmospheric scene or concept that evokes the slide's central idea.
        • Think of it as a background or hero image that sets the FEELING, not the layout.
        • Example for a company growth slide:
            ✗ BAD:  "A timeline showing milestones: garage in 2010, users in 2015, globe today"
            ✓ GOOD: "A panoramic view of a rising cityscape at golden hour, symbolizing growth and ambition"
        • Example for a comparison slide:
            ✗ BAD:  "Two columns comparing traditional vs modern approaches with pros and cons"
            ✓ GOOD: "A split composition with an old weathered path on one side and a sleek highway on the other"

        STRICT OUTPUT SCHEMA (JSON ONLY):
        CRITICAL INSTRUCTION: The `contentBlocks` property MUST be an array of objects `[{...}, {...}]`. It must NEVER be a string, null, or empty space. If you fail to output an array of valid block objects, the app will crash severely.
        {self.llm_schema_placeholder if hasattr(self, 'llm_schema_placeholder') else self.schema}

        OUTPUT FORMAT:
        Output ONLY the valid JSON object. No preamble, no explanation, no markdown fences.
        """

        response = self.llm.invoke([{"role": "user", "content": prompt}])
        content = response.content.replace("```json", "").replace("```", "").strip()

        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            print(f"Failed to parse LLM response as JSON: {e}")
            # Ensure we return valid GyML structure even on failure
            return {
                "title": title,
                "intent": "explain",
                "contentBlocks": [
                    {
                        "type": "paragraph",
                        "text": "Generation failed. Please check logs.",
                    }
                ],
            }


if __name__ == "__main__":
    # Test generation
    generator = GyMLContentGenerator()
    test_narration = (
        "In 2010, the company was founded in a small garage. By 2015, we reached 1 million users. "
        "Today, we are a global leader in AI education, helping millions of students learn better."
    )
    result = generator.generate(
        narration=test_narration,
        title="Our Growth Journey",
        purpose="narrate",
        subtopic="Company History",
    )
    print(json.dumps(result, indent=2))
