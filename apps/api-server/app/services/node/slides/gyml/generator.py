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
    ) -> Dict[str, Any]:
        """
        Generate structured GyML content from narration.

        Args:
            point_count: Number of narration segments. When > 1, the primary
                         smart_layout MUST have exactly this many items so
                         animations stay in sync with audio.
        """
        prompt = f"""
        You are an expert educational content designer who creates visually rich, cognitively balanced slides.
        Convert the Teacher's Narration into a structured visual slide using GyML (Gyanova Markup Language).

        SLIDE CONTEXT:
        - Title: {title}
        - Purpose/Intent: {purpose}
        - Subtopic: {subtopic}
        - Narration: {narration}
        {f"- Additional Context: {context}" if context else ""}

        ═══════════════════════════════════════════════
        STEP 1: DETERMINE THE INTENT
        ═══════════════════════════════════════════════
        Choose ONE intent based on the narration's goal:
          introduce — Hook + context (first impression, minimal text, striking visual)
          explain   — Clarity + progression (concept → diagram → example)
          narrate   — Chronological story (timeline, milestones, journey)
          compare   — Show differences/similarities (side-by-side, pros/cons)
          list      — Enumerate features, steps, items
          prove     — Evidence, data, statistics
          summarize — Reinforce key points (brevity + impact, 3-5 bullets/cards)
          teach     — Definitions, code, diagrams (build understanding)
          demo      — Walkthrough, live example

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

           TIMELINES (for narrate/chronological content):
             timeline, timelineHorizontal, timelineSequential, timelineMilestone
             → 3-5 milestones (sweet spot). Max 5. Beyond 5, split across slides.

           CARD GRIDS (for explain/list/features):
             cardGrid, cardGridIcon, cardGridSimple, cardGridImage
             → 3-4 cards (sweet spot). Max 6. Each card: heading + short text + optional icon.

           STATS (for prove/data):
             stats, statsComparison, statsPercentage
             → 2-4 stat items. Each: value + label.

           BULLETS (for list/teach):
             bigBullets, bulletIcon, bulletCheck, bulletCross
             → 3-4 bullets (sweet spot). Max 5-6. Beyond 6, split or convert to cards.

           PROCESS STEPS (for explain/demo workflows):
             processSteps, processArrow, processAccordion

           COMPARISONS (for compare intent):
             comparison, comparisonProsCons, comparisonBeforeAfter
             → Two columns. 3-4 points per side max.

           QUOTES (for narrate/introduce):
             quote, quoteTestimonial, quoteCitation

           DEFINITIONS (for teach):
             definition → Use alone with simple supporting text. Do NOT pair with complex visuals.

           CODE (for teach/demo):
             codeSnippet, codeComparison

           DIAGRAMS (for explain/teach):
             diagramFlowchart, diagramHierarchy, diagramCycle, diagramPyramid

           TABLES (for compare/prove/list):
             table, tableStriped, tableHighlight

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

        CONTENT ORDERING (top to bottom):
          1. intro_paragraph (optional — sets the stage)
          2. smart_layout (the MAIN content)
          3. annotation_paragraph or caption (optional — adds nuance)
          4. outro_paragraph or takeaway (optional — closes the slide)

        INTENT-SPECIFIC RECIPES:
          introduce → Headline + 1 striking visual/card layout + minimal text. Callouts: 0.
          explain   → intro_paragraph + diagram/cards + annotation. Callouts: 1-2 (label key parts).
          narrate   → intro_paragraph + timeline + outro_paragraph. Callouts: 0-1.
          compare   → intro_paragraph + comparison layout + callout highlighting key difference. Callouts: 1-2.
          list      → intro_paragraph + bullet/card grid + optional takeaway. Callouts: 0.
          prove     → intro_paragraph + stats/table + callout with key insight. Callouts: 1.
          summarize → 3-5 cards or bullets + takeaway. Minimal text. Callouts: 0-1.
          teach     → context_paragraph + definition/code/diagram + annotation_paragraph. Callouts: 1-2.
          demo      → intro_paragraph + code/processSteps + caption. Callouts: 0-1.

        PROHIBITED COMBINATIONS (never do these):
          ✗ Dense paragraph + complex diagram on same slide (cognitive overload)
          ✗ Definition + detailed timeline (conflicting purposes)
          ✗ Multiple competing smart_layouts on one slide (only ONE primary)
          ✗ More than 6 bullets alongside a large card grid (cramped)
          ✗ Quote + data table on same slide (emotional vs. analytical clash)
          ✗ 3+ callouts on any slide (visual noise)
          ✗ Timeline + bullet points showing the same information (redundant)

        ON-SCREEN TEXT vs NARRATION (critical for engagement):
          • On-screen text is the SHORT SUMMARY — card headings: 2-5 words, card descriptions: 1 short sentence (the "what")
          • The narration IS the full explanation — it gives context, examples, analogies
          • NEVER copy narration text verbatim into card descriptions or paragraphs
          • Students read the slide while listening — if text = narration, it feels like reading a teleprompter
          • On-screen = labels and key facts. Narration = the teacher explaining them.

        {f'''ANIMATION ALIGNMENT (non-negotiable):
          The narration has exactly {point_count} spoken segments/points.
          Your primary smart_layout MUST have exactly {point_count} items.
          Each item maps 1:1 to a narration segment for animation sync.
          If the narration has 1 segment, use a single-content layout (paragraph, definition, or quote).''' if point_count > 0 else ''}

        ═══════════════════════════════════════════════
        STEP 4: FORMATTING
        ═══════════════════════════════════════════════
        • Use 'ri-*' icon names (RemixIcon library). Examples: ri-lightbulb-line, ri-rocket-line, ri-code-line.
        • Keep paragraph text concise: 1-3 sentences max.
        • Smart layout item text: 1-2 sentences each.
        • Callout text: 1-2 lines maximum.

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
            print(f"Raw content: {content}")
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
