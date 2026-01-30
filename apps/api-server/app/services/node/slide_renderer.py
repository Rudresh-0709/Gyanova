"""
Slide Renderer Node - Template Injection System

This node takes the generated slide data (narration + visual content) and injects it
into the appropriate HTML blueprint templates, creating final HTML slides ready for rendering.

Flow:
- Input: State with complete slide data (narration_text, visual_content, blueprint_file)
- Output: HTML files for each slide (injected with real data)
"""

import os
import json
from typing import Dict, Any, List
from pathlib import Path
import re

# Path to blueprints
BLUEPRINTS_DIR = Path(__file__).parent / "slides" / "blueprints"


def render_title_card(slide: Dict[str, Any], template_html: str) -> str:
    """
    Inject data into title card template.

    Data needed:
    - slide_title (for main title)
    - visual_content.subtitle (for subtitle text)
    - subtopic_name (for badge)
    """
    # Extract data
    title = slide.get("slide_title", "Title")
    subtitle = slide.get("visual_content", {}).get("subtitle", "")
    badge = slide.get("subtopic_name", "Chapter")

    # Inject into template
    html = template_html

    # Replace badge
    html = html.replace("Heading Placeholder", badge)

    # Replace title (handle line breaks if needed)
    # Split long titles across two lines
    words = title.split()
    if len(words) > 3:
        mid = len(words) // 2
        title_html = " ".join(words[:mid]) + "<br>" + " ".join(words[mid:])
    else:
        title_html = title

    html = re.sub(
        r"(<h1[^>]*>)(.*?)(</h1>)", f"\\1{title_html}\\3", html, flags=re.DOTALL
    )

    # Replace subtitle
    html = re.sub(
        r'(<p class="slide-subtitle"[^>]*>)(.*?)(</p>)',
        f"\\1{subtitle}\\3",
        html,
        flags=re.DOTALL,
    )

    return html


def render_bullet_points(slide: Dict[str, Any], template_html: str) -> str:
    """
    Inject bullet point data into title_with_bullets template.

    Data needed:
    - slide_title
    - visual_content.bullets (list of {icon, heading, description})
    """
    title = slide.get("slide_title", "Title")
    bullets = slide.get("visual_content", {}).get("bullets", [])

    html = template_html

    # Replace title
    html = re.sub(
        r'(<h1 class="slide-title"[^>]*>)(.*?)(</h1>)',
        f"\\1{title}\\3",
        html,
        flags=re.DOTALL,
    )

    # Remove subtitle if empty (optional subtitle)
    if not slide.get("visual_content", {}).get("subtitle"):
        html = re.sub(
            r'<div class="slide-accent"></div>\s*<p class="slide-subtitle">.*?</p>',
            '<div class="slide-accent"></div>',
            html,
            flags=re.DOTALL,
        )

    # Generate bullet cards HTML
    bullets_html = ""
    for bullet in bullets:
        icon = bullet.get("icon", "ri-circle-line")
        heading = bullet.get("heading", "Heading")
        text = bullet.get("description", "")

        bullets_html += f"""
                <li class="slide-card">
                    <div class="slide-icon"><i class="{icon}"></i></div>
                    <h3 class="slide-list-heading">{heading}</h3>
                    <p class="slide-list-text">{text}</p>
                </li>"""

    # Replace the slide-list content
    html = re.sub(
        r'(<ul class="slide-list"[^>]*>)(.*?)(</ul>)',
        f"\\1{bullets_html}\n            \\3",
        html,
        flags=re.DOTALL,
    )

    return html


def render_timeline(slide: Dict[str, Any], template_html: str) -> str:
    """
    Inject timeline data into timeline template.

    Data needed:
    - slide_title
    - visual_content.timeline_items (list of {phase_title, description})
    """
    title = slide.get("slide_title", "Timeline")
    timeline_items = slide.get("visual_content", {}).get("timeline_items", [])

    html = template_html

    # Replace title (correct class is slide-title, not timeline-title)
    html = re.sub(
        r'(<h1 class="slide-title"[^>]*>)(.*?)(</h1>)',
        f"\\1{title}\\3",
        html,
        flags=re.DOTALL,
    )

    # Generate timeline items HTML matching actual template structure
    timeline_html = ""
    for i, item in enumerate(timeline_items):
        phase = item.get("phase_title", "Phase")
        description = item.get("description", "")

        # Mark first item as active
        active_class = " active" if i == 0 else ""

        timeline_html += f"""
                <div class="slide-timeline-item{active_class}" data-index="{i}">
                    <div class="slide-timeline-dot"></div>
                    <div class="slide-timeline-line"></div>
                    <div class="slide-timeline-content">
                        <h2 class="slide-timeline-title">{phase}</h2>
                        <p class="slide-timeline-text">{description}</p>
                    </div>
                </div>"""

    # Replace the slide-timeline content
    html = re.sub(
        r'(<div class="slide-timeline"[^>]*>)(.*?)(</div>\s*</div>\s*</div>)',
        f"\\1{timeline_html}\n            \\3",
        html,
        flags=re.DOTALL,
    )

    return html


def render_columns(slide: Dict[str, Any], template_html: str) -> str:
    """
    Inject column data into two/three/four column templates.

    Data needed:
    - slide_title
    - visual_content.columns (list of {title, text})
    """
    title = slide.get("slide_title", "Columns")
    columns = slide.get("visual_content", {}).get("columns", [])

    html = template_html

    # Replace title
    html = re.sub(
        r'(<h1[^>]*class="[^"]*title[^"]*"[^>]*>)(.*?)(</h1>)',
        f"\\1{title}\\3",
        html,
        flags=re.DOTALL,
    )

    # Generate columns HTML
    columns_html = ""
    for col in columns:
        col_title = col.get("title", "Column")
        col_text = col.get("text", "")

        columns_html += f"""
            <div class="column">
                <h3 class="column-title">{col_title}</h3>
                <p class="column-text">{col_text}</p>
            </div>"""

    # Replace columns content
    html = re.sub(
        r'(<div class="columns-container"[^>]*>)(.*?)(</div>)',
        f"\\1{columns_html}\n        \\3",
        html,
        flags=re.DOTALL,
    )

    return html


def render_slide(slide: Dict[str, Any]) -> str:
    """
    Main function to render a slide based on its content type and blueprint.

    Args:
        slide: Complete slide dictionary with all metadata and content

    Returns:
        Final HTML string ready for rendering
    """
    blueprint_file = slide.get("blueprint_file", "title_card/default.html")
    content_type = slide.get("content_type", "")

    # Load template
    template_path = BLUEPRINTS_DIR / blueprint_file

    if not template_path.exists():
        print(f"⚠️  Template not found: {template_path}")
        return f"<html><body><h1>Error: Template not found</h1></body></html>"

    with open(template_path, "r", encoding="utf-8") as f:
        template_html = f.read()

    # Render based on content type
    if content_type == "NO_NARRATION_POINTS":
        # Title card
        return render_title_card(slide, template_html)

    elif content_type == "BULLET_POINTS":
        # Title with bullets
        return render_bullet_points(slide, template_html)

    elif content_type == "TIMELINE_STEPS":
        # Timeline
        return render_timeline(slide, template_html)

    elif content_type in ["TWO_COLUMN_TEXT", "THREE_COLUMN_CARDS", "FOUR_COLUMN_CARDS"]:
        # Columns
        return render_columns(slide, template_html)

    elif content_type == "ICON_GRID":
        # Very similar to bullet points
        return render_bullet_points(slide, template_html)

    else:
        print(f"⚠️  Unknown content type: {content_type}")
        return template_html


def render_all_slides(
    state: Dict[str, Any], output_dir: str = "rendered_slides"
) -> Dict[str, Any]:
    """
    Render all slides in the state to HTML files.

    Args:
        state: Complete workflow state with slides
        output_dir: Directory to save rendered HTML files

    Returns:
        Updated state with rendered_slides paths
    """
    slides = state.get("slides", {})

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    rendered_slides = {}

    for subtopic_id, slide_list in slides.items():
        print(f"\n📂 Rendering subtopic: {subtopic_id}")
        rendered_slides[subtopic_id] = []

        for i, slide in enumerate(slide_list, 1):
            slide_id = slide.get("slide_id", f"{subtopic_id}_s{i}")
            slide_title = slide.get("slide_title", "Untitled")

            print(f"   🎨 Rendering: {slide_title}")

            # Render slide to HTML
            html_content = render_slide(slide)

            # Save to file
            filename = f"{slide_id}.html"
            file_path = output_path / filename

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(html_content)

            # Store path in state
            rendered_slides[subtopic_id].append(
                {
                    "slide_id": slide_id,
                    "title": slide_title,
                    "file_path": str(file_path.absolute()),
                    "filename": filename,
                }
            )

            print(f"      → Saved: {filename}")

    # Update state
    state["rendered_slides"] = rendered_slides

    print(f"\n✅ Rendered {sum(len(v) for v in rendered_slides.values())} slides")
    return state


if __name__ == "__main__":
    # Test with workflow output
    print("=" * 80)
    print("SLIDE RENDERER TEST")
    print("=" * 80)

    # Load workflow output
    workflow_file = "computer_generations_workflow_output.json"

    if os.path.exists(workflow_file):
        with open(workflow_file, "r", encoding="utf-8") as f:
            state = json.load(f)

        print(f"\n📄 Loaded workflow output: {workflow_file}")
        print(f"   Found {len(state.get('slides', {}))} subtopics")

        # Render one subtopic for testing
        test_subtopic = "sub_1_582521"  # Introduction to Computer Generations

        if test_subtopic in state.get("slides", {}):
            test_slides = state["slides"][test_subtopic]
            print(f"\n🧪 Testing with subtopic: {test_subtopic}")
            print(f"   Slides to render: {len(test_slides)}")

            # Create test state with just this subtopic
            test_state = {"slides": {test_subtopic: test_slides}}

            # Render
            result = render_all_slides(test_state, output_dir="test_rendered_slides")

            print("\n" + "=" * 80)
            print("RENDERING COMPLETE!")
            print("=" * 80)
            print(f"\n📁 Output directory: test_rendered_slides/")
            print(f"✅ Check the HTML files to verify rendering")
        else:
            print(f"\n❌ Subtopic {test_subtopic} not found in workflow output")
    else:
        print(f"\n❌ Workflow file not found: {workflow_file}")
        print("   Please make sure the file is in the same directory as this script")
