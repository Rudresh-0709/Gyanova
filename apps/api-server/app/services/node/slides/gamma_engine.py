"""
Slide Engine with Gamma-like Markup Support.

This engine renders slides from markup language (XML or JSON).
"""

from typing import Dict, List, Any, Union
from markup.parser import SlideMarkupParser
from blocks.block_renderers import BLOCK_RENDERERS


class GammaSlideEngine:
    """Render slides from Gamma-like markup language."""

    def __init__(self):
        self.parser = SlideMarkupParser()

    def render_from_markup(self, markup: Union[str, dict]) -> str:
        """
        Render a complete HTML slide from markup.

        Args:
            markup: XML string, JSON string, or dict

        Returns:
            Complete HTML document as string
        """
        slide_data = self.parser.parse(markup)
        return self.render_slide(slide_data)

    def render_slide(self, slide_data: Dict[str, Any]) -> str:
        """Render slide data to HTML."""
        slide_id = slide_data.get("id", "slide_1")
        sections = slide_data.get("sections", [])

        # Render all sections
        sections_html = []
        total_reveal_steps = 0

        for section in sections:
            section_html, steps = self._render_section(section, total_reveal_steps)
            sections_html.append(section_html)
            total_reveal_steps += steps

        # Wrap in full HTML template
        return self._wrap_in_template(
            slide_id=slide_id, sections=sections_html, total_steps=total_reveal_steps
        )

    def _render_section(
        self, section: Dict[str, Any], start_step: int
    ) -> tuple[str, int]:
        """Render a section and return (html, num_steps)."""
        purpose = section.get("purpose", "content")
        blocks = section.get("blocks", [])

        html = f'<section class="slide-section" data-purpose="{purpose}">\n'

        current_step = start_step
        for block in blocks:
            block_html = self._render_block(block, current_step)
            html += block_html
            current_step += self._count_reveal_steps(block)

        html += "</section>\n"

        total_steps = current_step - start_step
        return html, total_steps

    def _render_block(self, block: Dict[str, Any], reveal_step: int) -> str:
        """Render a single block."""
        block_type = block.get("type")
        renderer = BLOCK_RENDERERS.get(block_type)

        if renderer:
            return renderer(block, reveal_step)
        else:
            print(f"Warning: No renderer for block type '{block_type}'")
            return ""

    def _count_reveal_steps(self, block: Dict[str, Any]) -> int:
        """Count how many reveal steps a block needs."""
        block_type = block.get("type")

        if block_type == "timeline":
            return len(block.get("events", []))
        elif block_type == "card_grid":
            return len(block.get("cards", []))
        elif block_type == "bullet_list":
            return len(block.get("items", []))
        elif block_type == "step_list":
            return len(block.get("steps", []))
        elif block_type == "smart_layout_bullets":
            return len(block.get("items", []))
        elif block_type == "stats_grid":
            return len(block.get("stats", []))
        elif block_type == "diagram_funnel":
            return len(block.get("stages", []))
        else:
            return 1

    def _wrap_in_template(
        self, slide_id: str, sections: List[str], total_steps: int
    ) -> str:
        """Wrap sections in complete HTML template."""
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gamma-Style Slide</title>
    <link href="https://cdn.jsdelivr.net/npm/remixicon@4.5.0/fonts/remixicon.css" rel="stylesheet" />
    <link rel="stylesheet" href="../../blocks/styles/base.css">
    <link rel="stylesheet" href="../../blocks/styles/gamma_blocks.css">
</head>
<body>
    <div class="slide-root block-based" id="{slide_id}">
        {''.join(sections)}
    </div>
    
    <!-- Navigation Controls -->
    <div class="slide-nav">
        <button id="slidePrevBtn" class="slide-nav-btn">← Previous</button>
        <span id="slideStepIndicator" class="slide-step-indicator">0 / {total_steps}</span>
        <button id="slideNextBtn" class="slide-nav-btn">Next →</button>
    </div>
    
    <!-- Animation Controller -->
    <script>
        class SlideAnimationController {{
            constructor() {{
                this.currentStep = 0;
                this.totalSteps = {total_steps};
                this.elements = [];
                this.prevBtn = null;
                this.nextBtn = null;
            }}

            init() {{
                this.elements = Array.from(
                    document.querySelectorAll('[data-reveal-step]')
                ).sort((a, b) => {{
                    return parseInt(a.dataset.revealStep) - parseInt(b.dataset.revealStep);
                }});

                this.elements.forEach(el => {{
                    el.classList.remove('reveal-visible');
                }});

                this.setupButtons();
                this.currentStep = 0;
                this.updateButtonStates();

                console.log(`Slide initialized: ${{this.totalSteps}} steps`);
            }}

            setupButtons() {{
                this.prevBtn = document.getElementById('slidePrevBtn');
                this.nextBtn = document.getElementById('slideNextBtn');

                if (this.prevBtn) {{
                    this.prevBtn.addEventListener('click', () => this.previous());
                }}

                if (this.nextBtn) {{
                    this.nextBtn.addEventListener('click', () => this.next());
                }}

                document.addEventListener('keydown', (e) => {{
                    if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {{
                        e.preventDefault();
                        this.next();
                    }} else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {{
                        e.preventDefault();
                        this.previous();
                    }}
                }});
            }}

            next() {{
                if (this.currentStep < this.totalSteps) {{
                    this.currentStep++;
                    this.goToStep(this.currentStep);
                }}
            }}

            previous() {{
                if (this.currentStep > 0) {{
                    this.currentStep--;
                    this.goToStep(this.currentStep);
                }}
            }}

            goToStep(step) {{
                this.currentStep = Math.max(0, Math.min(step, this.totalSteps));

                this.elements.forEach((el, index) => {{
                    const elementStep = index + 1;

                    if (elementStep <= this.currentStep) {{
                        el.classList.add('reveal-visible');
                    }} else {{
                        el.classList.remove('reveal-visible');
                    }}
                }});

                this.updateButtonStates();
            }}

            updateButtonStates() {{
                if (this.prevBtn) {{
                    this.prevBtn.disabled = this.currentStep === 0;
                }}

                if (this.nextBtn) {{
                    this.nextBtn.disabled = this.currentStep === this.totalSteps;
                }}

                const indicator = document.getElementById('slideStepIndicator');
                if (indicator) {{
                    indicator.textContent = `${{this.currentStep}} / ${{this.totalSteps}}`;
                }}
            }}
        }}

        if (document.readyState === 'loading') {{
            document.addEventListener('DOMContentLoaded', () => {{
                window.slideController = new SlideAnimationController();
                window.slideController.init();
            }});
        }} else {{
            window.slideController = new SlideAnimationController();
            window.slideController.init();
        }}
    </script>
</body>
</html>"""


if __name__ == "__main__":
    # Example usage
    engine = GammaSlideEngine()

    # Example 1: JSON format
    json_markup = {
        "id": "demo_slide",
        "sections": [
            {
                "purpose": "introduction",
                "blocks": [
                    {
                        "type": "heading",
                        "level": 1,
                        "text": "Welcome to Gamma-Style Slides",
                    },
                    {
                        "type": "paragraph",
                        "text": "Built with responsive blocks and smart layouts",
                    },
                ],
            },
            {
                "purpose": "content",
                "blocks": [
                    {
                        "type": "smart_layout_bullets",
                        "items": [
                            {"text": "Easy to create", "icon": "ri-check-line"},
                            {"text": "Fully responsive", "icon": "ri-smartphone-line"},
                            {"text": "LLM-friendly", "icon": "ri-robot-line"},
                        ],
                    }
                ],
            },
        ],
    }

    html = engine.render_from_markup(json_markup)
    print("Demo slide generated successfully!")
    print(f"Total HTML length: {len(html)} characters")
