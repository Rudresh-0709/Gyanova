"""Composition engine for block-based slides.

Composes slides from intent, sections, and blocks.
"""

from block_renderers import BLOCK_RENDERERS


def compose_slide(slide_data: dict) -> tuple[str, int]:
    """
    Compose a slide from sections and blocks.

    Args:
        slide_data: Dictionary with 'intent' and 'sections'

    Returns:
        Tuple of (html_string, total_reveal_steps)
    """
    intent = slide_data.get("intent", "")
    sections = slide_data.get("sections", [])

    html = f'<div class="slide-root block-based" data-intent="{intent}">\n'

    reveal_step = 0

    for section in sections:
        purpose = section.get("purpose", "")
        blocks = section.get("blocks", [])
        layout = section.get("layout", "")  # Optional: "two-column", etc.

        layout_class = f" {layout}" if layout else ""
        html += f'    <section class="slide-section{layout_class}" data-purpose="{purpose}">\n'

        for block in blocks:
            block_type = block.get("type")
            renderer = BLOCK_RENDERERS.get(block_type)

            if renderer:
                # Render the block
                block_html = renderer(block, reveal_step)
                html += f"        {block_html}\n"

                # Increment reveal step based on block complexity
                reveal_step += get_block_step_count(block)
            else:
                print(f"Warning: No renderer for block type '{block_type}'")

        html += "    </section>\n"

    html += "</div>\n"

    return html, reveal_step


def get_block_step_count(block: dict) -> int:
    """
    Calculate how many reveal steps a block needs.

    Most blocks = 1 step
    Card grids = number of cards
    Bullet/step lists = number of items
    """
    block_type = block.get("type")

    if block_type == "card_grid":
        return len(block.get("cards", []))
    elif block_type == "bullet_list":
        return len(block.get("items", []))
    elif block_type == "step_list":
        return len(block.get("steps", []))
    else:
        return 1
