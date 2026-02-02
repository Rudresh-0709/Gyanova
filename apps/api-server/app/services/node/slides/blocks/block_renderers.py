"""Block renderers for the block-based slide system.

Each function renders a specific block type to HTML.
"""


def render_heading(block: dict, reveal_step: int) -> str:
    """Render a heading block."""
    level = block.get("level", 1)
    text = block.get("text", "")

    return f"""
        <h{level} class="block-heading block-heading-{level}" data-reveal-step="{reveal_step}">
            {text}
        </h{level}>
    """


def render_paragraph(block: dict, reveal_step: int) -> str:
    """Render a paragraph block."""
    text = block.get("text", "")

    return f"""
        <p class="block-paragraph" data-reveal-step="{reveal_step}">
            {text}
        </p>
    """


def render_card_grid(block: dict, reveal_step: int) -> str:
    """Render a card grid block."""
    cards = block.get("cards", [])

    html = f'<div class="block-card-grid" data-card-count="{len(cards)}">\n'

    for i, card in enumerate(cards):
        icon = card.get("icon", "ri-circle-line")
        heading = card.get("heading", "")
        text = card.get("text", "")
        number = card.get("number")  # Optional card number
        variant = card.get("variant", "light")  # "light" or "dark"

        variant_class = f" card-{variant}" if variant == "dark" else ""

        html += f"""
            <div class="card{variant_class}" data-reveal-step="{reveal_step + i}">
                {f'<div class="card-number">{number}</div>' if number else ''}
                <div class="card-icon"><i class="{icon}"></i></div>
                <h3 class="card-heading">{heading}</h3>
                <p class="card-text">{text}</p>
            </div>
        """

    html += "    </div>\n"
    return html


def render_bullet_list(block: dict, reveal_step: int) -> str:
    """Render a bullet list block."""
    items = block.get("items", [])
    style = block.get("style", "unnumbered")  # "numbered" or "unnumbered"
    columns = block.get("columns", 1)  # Number of columns (1, 2, or 3)

    tag = "ol" if style == "numbered" else "ul"
    column_class = f" columns-{columns}" if columns > 1 else ""
    html = (
        f'<{tag} class="block-bullet-list block-bullet-list-{style}{column_class}">\n'
    )

    for i, item in enumerate(items):
        html += f"""
            <li data-reveal-step="{reveal_step + i}">{item}</li>
        """

    html += f"    </{tag}>\n"
    return html


def render_step_list(block: dict, reveal_step: int) -> str:
    """Render a step list block (01 / 02 / 03 style)."""
    steps = block.get("steps", [])

    html = '<div class="block-step-list">\n'

    for i, step in enumerate(steps):
        number = step.get("number", f"{i+1:02d}")
        text = step.get("text", "")

        # Bold text before " - " if present
        if " - " in text:
            parts = text.split(" - ", 1)
            text_html = f"<strong>{parts[0]}</strong> - {parts[1]}"
        else:
            text_html = text

        html += f"""
            <div class="step" data-reveal-step="{reveal_step + i}">
                <div class="step-number">{number}</div>
                <div class="step-text">{text_html}</div>
            </div>
        """

    html += "    </div>\n"
    return html


def render_takeaway(block: dict, reveal_step: int) -> str:
    """Render a takeaway/callout block."""
    text = block.get("text", "")
    label = block.get("label", "Key Takeaway")

    return f"""
        <div class="block-takeaway" data-reveal-step="{reveal_step}">
            <strong>{label}:</strong> {text}
        </div>
    """


def render_image(block: dict, reveal_step: int) -> str:
    """Render an image block."""
    url = block.get("url", "")
    caption = block.get("caption", "")

    html = f"""
        <div class="block-image" data-reveal-step="{reveal_step}">
            <img src="{url}" alt="{caption}">
    """

    if caption:
        html += f"""
            <p class="image-caption">{caption}</p>
        """

    html += """
        </div>
    """

    return html


def render_stat(block: dict, reveal_step: int) -> str:
    """Render a stat block."""
    value = block.get("value", "")
    label = block.get("label", "")

    return f"""
        <div class="block-stat" data-reveal-step="{reveal_step}">
            <div class="stat-value">{value}</div>
            <div class="stat-label">{label}</div>
        </div>
    """


def render_divider(block: dict, reveal_step: int) -> str:
    """Render a divider block."""
    return f"""
        <div class="block-divider" data-reveal-step="{reveal_step}"></div>
    """


def render_columns(block: dict, reveal_step: int) -> str:
    """Render a columns layout block."""
    widths = block.get("widths", [50, 50])
    columns = block.get("columns", [])

    # Convert widths to CSS percentages
    total = sum(widths)
    width_styles = [f"{(w/total)*100}%" for w in widths]

    html = '<div class="block-columns">\n'

    for i, column_blocks in enumerate(columns):
        width_style = width_styles[i] if i < len(width_styles) else "auto"
        html += f'    <div class="column" style="flex: 0 0 {width_style};">\n'

        # Recursively render blocks in this column
        for block_data in column_blocks:
            block_type = block_data.get("type")
            renderer = BLOCK_RENDERERS.get(block_type)
            if renderer:
                html += renderer(block_data, reveal_step)

        html += "    </div>\n"

    html += "</div>\n"
    return html


def render_timeline(block: dict, reveal_step: int) -> str:
    """Render a timeline block (enhanced version)."""
    events = block.get("events", [])
    num_events = len(events)

    html = f'<div class="block-timeline" data-event-count="{num_events}">\n'

    for i, event in enumerate(events):
        year = event.get("year", "")
        description = event.get("description", "")

        html += f"""
        <div class="timeline-event" data-reveal-step="{reveal_step + i}">
            <div class="timeline-year">{year}</div>
            <div class="timeline-description">{description}</div>
        </div>
        """

    html += "</div>\n"
    return html


def render_smart_layout_bullets(block: dict, reveal_step: int) -> str:
    """Render smart layout: big bullets with icons."""
    items = block.get("items", [])

    html = '<div class="block-smart-bullets">\n'

    for i, item in enumerate(items):
        text = item.get("text", "") if isinstance(item, dict) else item
        icon = (
            item.get("icon", "ri-check-line")
            if isinstance(item, dict)
            else "ri-check-line"
        )

        html += f"""
        <div class="smart-bullet" data-reveal-step="{reveal_step + i}">
            <div class="smart-bullet-icon"><i class="{icon}"></i></div>
            <div class="smart-bullet-text">{text}</div>
        </div>
        """

    html += "</div>\n"
    return html


def render_stats_grid(block: dict, reveal_step: int) -> str:
    """Render a stats grid (smart layout)."""
    stats = block.get("stats", [])

    html = f'<div class="block-stats-grid" data-stat-count="{len(stats)}">\n'

    for i, stat in enumerate(stats):
        value = stat.get("value", "")
        label = stat.get("label", "")

        html += f"""
        <div class="stat-item" data-reveal-step="{reveal_step + i}">
            <div class="stat-value">{value}</div>
            <div class="stat-label">{label}</div>
        </div>
        """

    html += "</div>\n"
    return html


def render_diagram_venn(block: dict, reveal_step: int) -> str:
    """Render a Venn diagram."""
    circles = block.get("circles", [])

    html = f'<div class="block-diagram-venn" data-reveal-step="{reveal_step}">\n'

    for i, circle in enumerate(circles):
        label = circle.get("label", "")
        text = circle.get("text", "")

        html += f"""
        <div class="venn-circle venn-circle-{i}">
            <div class="venn-label">{label}</div>
            <div class="venn-text">{text}</div>
        </div>
        """

    html += "</div>\n"
    return html


def render_diagram_funnel(block: dict, reveal_step: int) -> str:
    """Render a funnel diagram."""
    stages = block.get("stages", [])

    html = '<div class="block-diagram-funnel">\n'

    for i, stage in enumerate(stages):
        width_percent = 100 - (i * 15)  # Progressive narrowing

        html += f"""
        <div class="funnel-stage" data-reveal-step="{reveal_step + i}" 
             style="width: {width_percent}%;">
            {stage}
        </div>
        """

    html += "</div>\n"
    return html


def render_diagram_flowchart(block: dict, reveal_step: int) -> str:
    """Render a simple flowchart diagram."""
    nodes = block.get("nodes", [])
    edges = block.get("edges", [])

    html = f'<div class="block-diagram-flowchart" data-reveal-step="{reveal_step}">\n'

    # Render nodes
    for node in nodes:
        node_id = node.get("id", "")
        node_type = node.get("type", "process")
        text = node.get("text", "")

        html += f"""
        <div class="flowchart-node flowchart-node-{node_type}" data-node-id="{node_id}">
            {text}
        </div>
        """

    # Note: Edges rendered as simple arrows in CSS
    # For complex flowcharts, consider using Mermaid.js or similar

    html += "</div>\n"
    return html


def render_table(block: dict, reveal_step: int) -> str:
    """Render a table block."""
    rows = block.get("rows", [])

    if not rows:
        return ""

    html = f'<table class="block-table" data-reveal-step="{reveal_step}">\n'

    # First row as header
    if rows:
        html += "<thead><tr>\n"
        for cell in rows[0]:
            html += f"<th>{cell}</th>\n"
        html += "</tr></thead>\n"

    # Remaining rows as body
    if len(rows) > 1:
        html += "<tbody>\n"
        for row in rows[1:]:
            html += "<tr>\n"
            for cell in row:
                html += f"<td>{cell}</td>\n"
            html += "</tr>\n"
        html += "</tbody>\n"

    html += "</table>\n"
    return html


# Registry of all block renderers
BLOCK_RENDERERS = {
    "heading": render_heading,
    "paragraph": render_paragraph,
    "card_grid": render_card_grid,
    "bullet_list": render_bullet_list,
    "step_list": render_step_list,
    "takeaway": render_takeaway,
    "image": render_image,
    "stat": render_stat,
    "divider": render_divider,
    # Gamma-like features
    "columns": render_columns,
    "timeline": render_timeline,
    "smart_layout_bullets": render_smart_layout_bullets,
    "stats_grid": render_stats_grid,
    "diagram_venn": render_diagram_venn,
    "diagram_funnel": render_diagram_funnel,
    "diagram_flowchart": render_diagram_flowchart,
    "table": render_table,
}
