"""Generate a standalone demo for diamond content blocks.
"""

from __future__ import annotations

import io
import json
import os
import sys
from typing import Any, Dict, List

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
API_SERVER_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", ".."))
if API_SERVER_ROOT not in sys.path:
    sys.path.insert(0, API_SERVER_ROOT)

from app.services.node.slides.gyml.composer import SlideComposer
from app.services.node.slides.gyml.serializer import GyMLSerializer
from app.services.node.slides.gyml.renderer import GyMLRenderer
from app.services.node.slides.gyml.theme import get_theme


def _demo_slides() -> List[Dict[str, Any]]:
    return [
        {
            "title": "Diamond Ribbon Layout",
            "subtitle": "Testing diamondRibbon smart layout variant",
            "intent": "explain",
            "layout": "blank",
            "image_layout": "blank",
            "slide_density": "standard",
            "contentBlocks": [
                {
                    "type": "smart_layout",
                    "variant": "diamondRibbon",
                    "items": [
                        {
                            "heading": "Analysis",
                            "description": "Gather all requirements and define the scope by collaborating with stakeholders and identifying the most critical features required for the MVP launch.",
                            "icon_name": "ri-search-line",
                        },
                        {
                            "heading": "Design",
                            "description": "Create high-fidelity wireframes and mockups for the feature layout, ensuring that accessibility standards are met and the design system is strictly followed.",
                            "icon_name": "ri-pencil-ruler-2-line",
                        },
                        {
                            "heading": "Development",
                            "description": "Write clean, modular code to implement the necessary logic, using Test-Driven Development (TDD) to prevent regressions over time.",
                            "icon_name": "ri-code-s-slash-line",
                        },
                        {
                            "heading": "Testing",
                            "description": "Verify the functionality through automated UI tests and user acceptance testing (UAT) to guarantee stable behavior in production edge cases.",
                            "icon_name": "ri-test-tube-line",
                        },
                    ],
                }
            ],
        },
        {
            "title": "Diamond Grid: Vertical Stack (3 items)",
            "subtitle": "Testing diamondGrid smart layout variant",
            "intent": "explain",
            "layout": "blank",
            "image_layout": "blank",
            "slide_density": "standard",
            "contentBlocks": [
                {
                    "type": "smart_layout",
                    "variant": "diamondGrid",
                    "items": [
                        {
                            "heading": "Phase 1: Foundation",
                            "description": "Set up the repository, configure linters and formatters, and establish the CI/CD pipelines to ensure swift future deployments.",
                            "icon_name": "ri-settings-4-line",
                        },
                        {
                            "heading": "Phase 2: Database",
                            "description": "Draft the initial database schemas, generate Prisma migrations, and seed the development environments with realistic, high volume mock data.",
                            "icon_name": "ri-database-2-line",
                        },
                        {
                            "heading": "Phase 3: Logic",
                            "description": "Construct RESTful API routes, validation schemas using Zod, and robust error handlers that provide actionable feedback to front-end clients.",
                            "icon_name": "ri-route-line",
                        },
                    ],
                }
            ],
        },
        {
            "title": "Diamond Grid: 2x2 Grid (4 items)",
            "subtitle": "Testing diamondGrid smart layout variant",
            "intent": "explain",
            "layout": "blank",
            "image_layout": "blank",
            "slide_density": "standard",
            "contentBlocks": [
                {
                    "type": "smart_layout",
                    "variant": "diamondGrid",
                    "items": [
                        {
                            "heading": "Frontend",
                            "description": "React and TailwindCSS implementation.",
                            "icon_name": "ri-reactjs-line",
                        },
                        {
                            "heading": "Backend",
                            "description": "NodeJS and Express server.",
                            "icon_name": "ri-server-line",
                        },
                        {
                            "heading": "Database",
                            "description": "PostgreSQL with Prisma ORM.",
                            "icon_name": "ri-database-2-line",
                        },
                        {
                            "heading": "DevOps",
                            "description": "Docker and GitHub Actions deployment.",
                            "icon_name": "ri-git-merge-line",
                        },
                    ],
                }
            ],
        },
        {
            "title": "Diamond Grid: Horizontal Row (4 items)",
            "subtitle": "Testing diamondGrid smart layout variant",
            "intent": "explain",
            "layout": "blank",
            "image_layout": "blank",
            "slide_density": "standard",
            "contentBlocks": [
                {
                    "type": "smart_layout",
                    "variant": "diamondGrid",
                    "items": [
                        {
                            "heading": "Step 1",
                            "description": "Identify the core problem.",
                            "icon_name": "ri-search-eye-line",
                        },
                        {
                            "heading": "Step 2",
                            "description": "Brainstorm potential solutions.",
                            "icon_name": "ri-lightbulb-line",
                        },
                        {
                            "heading": "Step 3",
                            "description": "Select the best approach.",
                            "icon_name": "ri-check-double-line",
                        },
                        {
                            "heading": "Step 4",
                            "description": "Execute the chosen plan.",
                            "icon_name": "ri-rocket-line",
                        },
                    ],
                }
            ],
        },
        {
            "title": "Diamond Grid: Diagonal Flow (3 items)",
            "subtitle": "Testing diamondGrid smart layout variant",
            "intent": "explain",
            "layout": "blank",
            "image_layout": "blank",
            "slide_density": "standard",
            "contentBlocks": [
                {
                    "type": "smart_layout",
                    "variant": "diamondGrid",
                    "items": [
                        {
                            "heading": "Start",
                            "description": "Begin the journey by establishing a strong foundation and aligning all team members on the core objectives. A solid start prevents future bottlenecks.",
                            "icon_name": "ri-arrow-right-circle-line",
                        },
                        {
                            "heading": "Middle",
                            "description": "Overcome the challenges through iterative development and constant feedback loops. This is where the bulk of the engineering and design work occurs, requiring high collaboration.",
                            "icon_name": "ri-water-flash-line",
                        },
                        {
                            "heading": "End",
                            "description": "Achieve the final goal with a rigorous QA cycle and staged rollout. Celebrate the milestones while preparing precise documentation for future handoffs.",
                            "icon_name": "ri-trophy-line",
                        },
                    ],
                }
            ],
        },
        {
            "title": "Diamond Hub",
            "subtitle": "Testing diamondHub smart layout variant",
            "intent": "explain",
            "layout": "blank",
            "image_layout": "blank",
            "slide_density": "standard",
            "contentBlocks": [
                {
                    "type": "smart_layout",
                    "variant": "diamondHub",
                    "items": [
                        {
                            "heading": "Title",
                        },
                        {
                            "description": "Please add your text description in the top-left area.",
                            "icon_name": "ri-settings-4-line",
                        },
                        {
                            "description": "Please add your text description in the top-right area.",
                            "icon_name": "ri-send-plane-fill",
                        },
                        {
                            "description": "Please add your text description in the bottom-left area.",
                            "icon_name": "ri-computer-line",
                        },
                        {
                            "description": "Please add your text description in the bottom-right area.",
                            "icon_name": "ri-global-line",
                        },
                    ],
                }
            ],
        },
        {
            "title": "Diamond Row Bottom",
            "subtitle": "Testing cardGridDiamond smart layout variant",
            "intent": "list",
            "layout": "blank",
            "image_layout": "blank",
            "slide_density": "standard",
            "contentBlocks": [
                {
                    "type": "smart_layout",
                    "variant": "cardGridDiamond",
                    "items": [
                        {
                            "heading": "Click to Replace",
                            "description": "Please add your text description to the flying impression plane. Please add your text description.",
                            "icon_name": "ri-send-plane-fill",
                        },
                        {
                            "heading": "Click to Replace",
                            "description": "Please add your text description to the flying impression plane. Please add your text description.",
                            "icon_name": "ri-store-2-line",
                        },
                        {
                            "heading": "Click to Replace",
                            "description": "Please add your text description to the flying impression plane. Please add your text description.",
                            "icon_name": "ri-truck-line",
                        },
                        {
                            "heading": "Click to Replace",
                            "description": "Please add your text description to the flying impression plane. Please add your text description.",
                            "icon_name": "ri-global-line",
                        },
                    ],
                }
            ],
        },
    ]


def _render_slide(renderer: GyMLRenderer, serializer: GyMLSerializer, composer: SlideComposer, payload: Dict[str, Any]) -> str:
    composed = composer.compose(payload)
    gyml_sections = serializer.serialize_many(composed)
    return renderer.render_complete(gyml_sections)


def main() -> None:
    output_dir = os.path.join(SCRIPT_DIR, "slides", "output", "diamond_demo")
    os.makedirs(output_dir, exist_ok=True)

    composer = SlideComposer()
    serializer = GyMLSerializer()
    renderer = GyMLRenderer(theme=get_theme("midnight"), animated=True)

    demos = _demo_slides()
    slide_files: List[str] = []

    for idx, payload in enumerate(demos, start=1):
        html = _render_slide(renderer, serializer, composer, payload)
        slide_file = f"slide_diamond_{idx:02d}.html"
        with open(os.path.join(output_dir, slide_file), "w", encoding="utf-8") as f:
            f.write(html)
        slide_files.append(slide_file)

    with open(os.path.join(output_dir, "demo_slides.json"), "w", encoding="utf-8") as f:
        json.dump(demos, f, indent=2, ensure_ascii=False)

    cards = []
    for idx, (slide_file, payload) in enumerate(zip(slide_files, demos), start=1):
        title = payload.get("title", f"Slide {idx}")
        intent = payload.get("intent", "explain")
        variant = ""
        for block in payload.get("contentBlocks", []):
            if isinstance(block, dict) and block.get("type") == "smart_layout":
                variant = str(block.get("variant") or "")
                break
        cards.append(
            f'''
            <section class="slide-container">
              <header>
                <h2>{idx}. {title}</h2>
                <p><strong>variant:</strong> {variant or 'n/a'}</p>
              </header>
              <iframe src="{slide_file}" loading="lazy"></iframe>
            </section>
            '''
        )

    index_html = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Diamond Content Blocks Demo</title>
  <style>
    :root {{
      color-scheme: dark;
      --bg: #0b1020;
      --panel: #121a2f;
      --text: #e6edf7;
      --muted: #9eb0d0;
      --border: #243257;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Segoe UI, system-ui, -apple-system, sans-serif;
      background: var(--bg);
      color: var(--text);
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 0;
    }}
    .header-container {{
      width: 100%;
      padding: 24px;
      text-align: center;
      background: radial-gradient(circle at top, #182447 0%, var(--bg) 100%);
      border-bottom: 1px solid var(--border);
    }}
    h1 {{ margin: 0 0 0.5rem; font-size: 2rem; }}
    .lead {{ margin: 0; color: var(--muted); }}
    
    .stack {{ 
      display: flex; 
      flex-direction: column; 
      width: 100%;
      max-width: 1920px; /* Max sensible width */
    }}
    
    .slide-container {{
      width: 100%;
      display: flex;
      flex-direction: column;
      border-bottom: 2px solid var(--border);
      background: #000; /* Distinct background to see slide bounds */
    }}
    
    .slide-container header {{ 
      padding: 16px 24px; 
      background: color-mix(in srgb, var(--panel) 88%, #0a0f1f);
      border-bottom: 1px solid var(--border); 
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    
    .slide-container h2 {{ margin: 0; font-size: 1.25rem; font-weight: 500; }}
    .slide-container p {{ margin: 0; color: var(--muted); font-size: 0.9rem; }}
    
    iframe {{ 
      width: 100%; 
      aspect-ratio: 16 / 9; 
      border: 0; 
      display: block;
    }}
  </style>
</head>
<body>
  <div class="header-container">
    <h1>Diamond Blocks Demo Gallery</h1>
    <p class="lead">Full width slides stacked vertically to check "diamondRibbon" and "diamondGrid".</p>
  </div>
  <div class="stack">
    {''.join(cards)}
  </div>
</body>
</html>
'''

    index_path = os.path.join(output_dir, "index.html")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(index_html)

    print(f"Generated {len(slide_files)} demo slides -> {index_path}")


if __name__ == "__main__":
    main()
