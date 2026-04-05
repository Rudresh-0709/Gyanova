"""Generate a standalone GyML v2 gallery with hard-coded demo slides.

Output:
  apps/api-server/app/services/node/slides/output/v2_gallery/index.html

Usage (from apps/api-server):
  python -m app.services.node.generate_v2_gallery_demo
or (from repo root):
  python apps/api-server/app/services/node/generate_v2_gallery_demo.py
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
            "title": "AI Tutor Workflow Overview",
            "subtitle": "Large-box primary variant baseline",
            "intent": "explain",
            "layout": "right",
            "image_layout": "right",
            "slide_density": "balanced",
            "contentBlocks": [
                {
                    "type": "intro_paragraph",
                    "text": "This slide verifies that the new large-box primary layout is rendered correctly in the v2 pipeline.",
                },
                {
                    "type": "smart_layout",
                    "variant": "solidBoxesWithIconsInside",
                    "items": [
                        {
                            "heading": "Input",
                            "description": "Collect learner context, level, and objectives.",
                            "icon_name": "ri-file-list-3-line",
                        },
                        {
                            "heading": "Reason",
                            "description": "Assemble a concise explanation strategy for the concept.",
                            "icon_name": "ri-brain-line",
                        },
                        {
                            "heading": "Deliver",
                            "description": "Render visually clear teaching blocks with consistent hierarchy.",
                            "icon_name": "ri-slideshow-3-line",
                        },
                    ],
                },
                {
                    "type": "annotation_paragraph",
                    "text": "Takeaway: large boxes should remain the visual primary with supporting text secondary.",
                },
            ],
            "accentImagePrompt": "Simple abstract tutoring workflow illustration with clean geometry.",
        },
        {
            "title": "Foundational Concepts",
            "subtitle": "General intent/foundation case",
            "intent": "introduce",
            "layout": "left",
            "image_layout": "left",
            "slide_density": "sparse",
            "contentBlocks": [
                {
                    "type": "context_paragraph",
                    "text": "Use this slide to validate default foundation/overview behavior for general intents.",
                },
                {
                    "type": "smart_layout",
                    "variant": "solidBoxesWithIconsInside",
                    "items": [
                        {
                            "heading": "Scope",
                            "description": "Define what is included and what is intentionally out of scope.",
                            "icon_name": "ri-focus-2-line",
                        },
                        {
                            "heading": "Language",
                            "description": "Align wording with learner vocabulary and prior knowledge.",
                            "icon_name": "ri-chat-3-line",
                        },
                        {
                            "heading": "Outcome",
                            "description": "Set a practical objective that can be checked quickly.",
                            "icon_name": "ri-flag-2-line",
                        },
                    ],
                },
            ],
            "accentImagePrompt": "Minimal educational icon collage showing scope, language, and outcome.",
        },
        {
            "title": "Supporting Side Strip Demo",
            "subtitle": "Thin right-strip supporting text",
            "intent": "explain",
            "layout": "right",
            "image_layout": "right",
            "slide_density": "balanced",
            "contentBlocks": [
                {
                    "type": "smart_layout",
                    "variant": "solidBoxesWithIconsInside",
                    "items": [
                        {
                            "heading": "Concept",
                            "description": "Introduce one core idea per card to reduce split attention.",
                            "icon_name": "ri-lightbulb-line",
                        },
                        {
                            "heading": "Example",
                            "description": "Attach one concrete real-world case to each concept.",
                            "icon_name": "ri-shapes-line",
                        },
                        {
                            "heading": "Check",
                            "description": "Ask one quick question to verify understanding.",
                            "icon_name": "ri-questionnaire-line",
                        },
                    ],
                },
                {
                    "type": "paragraph",
                    "variant": "side-strip",
                    "text": "Supporting note: this paragraph uses the side-strip variant with a thin right accent line for quick contextual guidance.",
                },
            ],
            "accentImagePrompt": "Teaching notes sidebar style illustration with neutral tones.",
        },
        {
            "title": "No-Image Blank Layout",
            "subtitle": "image_tier none equivalent",
            "intent": "list",
            "layout": "blank",
            "image_layout": "blank",
            "slide_density": "standard",
            "contentBlocks": [
                {
                    "type": "intro_paragraph",
                    "text": "This slide intentionally has no image prompt and blank image layout.",
                },
                {
                    "type": "smart_layout",
                    "variant": "solidBoxesWithIconsInside",
                    "items": [
                        {
                            "heading": "Rule 1",
                            "description": "Do not emit accentImagePrompt when image tier is none.",
                            "icon_name": "ri-image-line",
                        },
                        {
                            "heading": "Rule 2",
                            "description": "Keep image_layout as blank to disable all image regions.",
                            "icon_name": "ri-layout-line",
                        },
                        {
                            "heading": "Rule 3",
                            "description": "Use structure and typography to maintain clarity.",
                            "icon_name": "ri-font-size-2",
                        },
                    ],
                },
            ],
        },
        {
            "title": "Summary & Reinforcement",
            "subtitle": "General summarize mapping behavior",
            "intent": "summarize",
            "layout": "bottom",
            "image_layout": "bottom",
            "slide_density": "balanced",
            "contentBlocks": [
                {
                    "type": "smart_layout",
                    "variant": "solidBoxesWithIconsInside",
                    "items": [
                        {
                            "heading": "Remember",
                            "description": "Keep one primary structured block per non-title slide.",
                            "icon_name": "ri-bookmark-3-line",
                        },
                        {
                            "heading": "Avoid",
                            "description": "Do not combine intro and takeaway/callout on the same slide.",
                            "icon_name": "ri-forbid-2-line",
                        },
                        {
                            "heading": "Rotate",
                            "description": "Vary composition styles to avoid repetitive 3-block patterns.",
                            "icon_name": "ri-refresh-line",
                        },
                    ],
                },
                {
                    "type": "outro_paragraph",
                    "text": "Final takeaway: this gallery should let you visually inspect new v2 block behavior quickly.",
                },
            ],
            "accentImagePrompt": "Subtle summary-themed illustration with checkmarks and arrows.",
        },
        {
            "title": "Process Mapping Control Slide",
            "subtitle": "Specialized variants still available",
            "intent": "teach",
            "layout": "top",
            "image_layout": "top",
            "slide_density": "balanced",
            "contentBlocks": [
                {
                    "type": "smart_layout",
                    "variant": "processSteps",
                    "items": [
                        {
                            "heading": "Plan",
                            "description": "Define objective and constraints before generation.",
                            "icon_name": "ri-map-pin-time-line",
                        },
                        {
                            "heading": "Generate",
                            "description": "Produce structured slide content blocks.",
                            "icon_name": "ri-magic-line",
                        },
                        {
                            "heading": "Validate",
                            "description": "Run compose, serialize, and render checks end-to-end.",
                            "icon_name": "ri-checkbox-circle-line",
                        },
                    ],
                },
                {
                    "type": "annotation_paragraph",
                    "text": "Control slide: processSteps is intentionally included to verify specialized mappings still render.",
                },
            ],
            "accentImagePrompt": "Clean process flow diagram with three stages.",
        },
    ]


def _render_slide(renderer: GyMLRenderer, serializer: GyMLSerializer, composer: SlideComposer, payload: Dict[str, Any]) -> str:
    composed = composer.compose(payload)
    gyml_sections = serializer.serialize_many(composed)
    return renderer.render_complete(gyml_sections)


def main() -> None:
    output_dir = os.path.join(SCRIPT_DIR, "slides", "output", "v2_gallery")
    os.makedirs(output_dir, exist_ok=True)

    composer = SlideComposer()
    serializer = GyMLSerializer()
    renderer = GyMLRenderer(theme=get_theme("midnight"), animated=True)

    demos = _demo_slides()
    slide_files: List[str] = []

    for idx, payload in enumerate(demos, start=1):
        html = _render_slide(renderer, serializer, composer, payload)
        slide_file = f"slide_{idx:02d}.html"
        with open(os.path.join(output_dir, slide_file), "w", encoding="utf-8") as f:
            f.write(html)
        slide_files.append(slide_file)

    # Persist source payload for quick debugging/reference.
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
            f"""
            <section class=\"card\">
              <header>
                <h2>{idx}. {title}</h2>
                <p><strong>intent:</strong> {intent} | <strong>variant:</strong> {variant or 'n/a'}</p>
              </header>
              <iframe src=\"{slide_file}\" loading=\"lazy\"></iframe>
            </section>
            """
        )

    index_html = f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"UTF-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
  <title>GyML v2 Content Block Gallery</title>
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
      background: radial-gradient(circle at top, #182447 0%, var(--bg) 45%);
      color: var(--text);
      padding: 24px;
    }}
    h1 {{ margin: 0 0 0.35rem; font-size: 1.75rem; }}
    .lead {{ margin: 0 0 1.25rem; color: var(--muted); }}
    .grid {{ display: grid; gap: 18px; }}
    .card {{
      background: color-mix(in srgb, var(--panel) 88%, #0a0f1f);
      border: 1px solid var(--border);
      border-radius: 14px;
      overflow: hidden;
    }}
    .card header {{ padding: 14px 16px; border-bottom: 1px solid var(--border); }}
    .card h2 {{ margin: 0 0 0.3rem; font-size: 1.05rem; }}
    .card p {{ margin: 0; color: var(--muted); font-size: 0.9rem; }}
    iframe {{ width: 100%; height: 720px; border: 0; background: #020612; }}
    @media (max-width: 900px) {{
      body {{ padding: 12px; }}
      iframe {{ height: 620px; }}
    }}
  </style>
</head>
<body>
  <h1>GyML v2 Demo Gallery</h1>
  <p class=\"lead\">Hard-coded slides rendered through composer → serializer → renderer for visual verification of new variants.</p>
  <div class=\"grid\">
    {''.join(cards)}
  </div>
</body>
</html>
"""

    index_path = os.path.join(output_dir, "index.html")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(index_html)

    print(f"Generated {len(slide_files)} demo slides -> {index_path}")


if __name__ == "__main__":
    main()
