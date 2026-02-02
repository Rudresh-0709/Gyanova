"""
Block-based slide renderer.

Renders slides using the composition engine and block system.
"""

import os
import sys
from pathlib import Path

# Add blocks directory to path
blocks_dir = Path(__file__).parent / "slides" / "blocks"
sys.path.insert(0, str(blocks_dir))

from composition_engine import compose_slide


def render_block_slide(slide_data: dict) -> str:
    """
    Render a complete HTML slide from block-based data.

    Args:
        slide_data: Dictionary containing intent, sections, and blocks

    Returns:
        Complete HTML string
    """
    # Compose the slide content
    slide_html, total_steps = compose_slide(slide_data)

    # Get CSS paths
    base_dir = Path(__file__).parent / "slides" / "blocks"
    css_dir = base_dir / "styles"

    # Read CSS files
    with open(css_dir / "base.css", "r", encoding="utf-8") as f:
        base_css = f.read()
    with open(css_dir / "layout.css", "r", encoding="utf-8") as f:
        layout_css = f.read()
    with open(css_dir / "animations.css", "r", encoding="utf-8") as f:
        animations_css = f.read()

    # Build complete HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Block-Based Slide</title>
    <link href="https://cdn.jsdelivr.net/npm/remixicon@4.5.0/fonts/remixicon.css" rel="stylesheet" />
    
    <style>
{base_css}

{layout_css}

{animations_css}
    </style>
</head>

<body>
{slide_html}

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
                // Find all animatable elements
                this.elements = Array.from(
                    document.querySelectorAll('[data-reveal-step]')
                ).sort((a, b) => {{
                    return parseInt(a.dataset.revealStep) - parseInt(b.dataset.revealStep);
                }});

                // Hide all elements initially
                this.elements.forEach(el => {{
                    el.classList.remove('reveal-visible');
                }});

                // Set up navigation buttons
                this.setupButtons();

                // Start at step 0
                this.currentStep = 0;
                this.updateButtonStates();

                console.log(`Block-based slide initialized: ${{this.totalSteps}} steps`);
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

                // Keyboard navigation
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

                // Update visibility for all elements
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

                // Update step indicator
                const indicator = document.getElementById('slideStepIndicator');
                if (indicator) {{
                    indicator.textContent = `${{this.currentStep}} / ${{this.totalSteps}}`;
                }}
            }}
        }}

        // Initialize controller
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
</html>
"""

    return html


if __name__ == "__main__":
    # Test with sample data
    test_slide = {
        "intent": "Explain computer generations evolution",
        "sections": [
            {
                "purpose": "introduction",
                "blocks": [
                    {"type": "heading", "text": "Computer Generations", "level": 1},
                    {
                        "type": "paragraph",
                        "text": "Technology evolved through five distinct generations, each marked by revolutionary advances in hardware and capabilities.",
                    },
                ],
            },
            {
                "purpose": "content",
                "blocks": [
                    {
                        "type": "card_grid",
                        "cards": [
                            {
                                "icon": "ri-computer-line",
                                "heading": "First Generation",
                                "text": "Vacuum tubes and magnetic drums for memory. Large, expensive, and power-hungry.",
                            },
                            {
                                "icon": "ri-cpu-line",
                                "heading": "Second Generation",
                                "text": "Transistors replaced vacuum tubes. Smaller, faster, and more reliable.",
                            },
                            {
                                "icon": "ri-chip-line",
                                "heading": "Third Generation",
                                "text": "Integrated circuits (ICs) enabled miniaturization and mass production.",
                            },
                        ],
                    },
                    {
                        "type": "takeaway",
                        "text": "Each generation brought exponential improvements in speed, size, and cost efficiency.",
                    },
                ],
            },
        ],
    }

    html = render_block_slide(test_slide)

    # Save to test file
    output_path = (
        Path(__file__).parent / "test_rendered_slides" / "block_system_test.html"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✅ Test slide generated: {output_path}")
