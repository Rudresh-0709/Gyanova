from typing import Any


GRID_CONTAINER_VARIANTS = {
    "bigBullets",
    "bulletIcon",
    "cardGrid",
    "cardGridIcon",
    "cardGridDiamond",
    "cardGridImage",
    "cardGridSimple",
    "diamondGrid",
    "diamondRibbon",
    "ribbonFold",
    "bento_grid",
    "icon_label_grid",
    "pillar_cards",
}


def render_grid_container(variant: str, block: Any, context: Any) -> str:
    """
    Renders Grid & Container family blocks.
    Handles standalone container blocks (comparison table, split panel) and
    SmartLayout grid/card variants.
    """
    block_type = type(block).__name__

    if block_type == "GyMLComparisonTable":
        return _render_comparison_table(block, context)

    if block_type == "GyMLSplitPanel":
        return _render_split_panel(block, context)

    item_count = len(block.items)
    extra_classes = []

    if variant == "diamondGrid":
        if not hasattr(context, "_diamond_idx"):
            context._diamond_idx = 0

        if item_count == 4:
            if context._diamond_idx % 2 == 1:
                extra_classes.append("grid-2d")
        elif item_count in {3, 5}:
            if context._diamond_idx % 2 == 1:
                extra_classes.append("diagonal")

        context._diamond_idx += 1

    class_attr = " ".join(["smart-layout"] + extra_classes)
    html_parts = [
        f'<div class="{class_attr}" '
        f'data-variant="{variant}" '
        f'data-item-count="{item_count}">'
    ]

    for index, item in enumerate(block.items):
        html_parts.append(_render_grid_item(item, variant, index, context))

    html_parts.append("</div>")
    return "\n".join(html_parts)


def _render_comparison_table(block: Any, context: Any) -> str:
    html_parts = ['<div class="comparison-table-wrapper">']

    if block.caption:
        html_parts.append(
            f'<h3 class="comparison-table-title">{context._escape(block.caption)}</h3>'
        )

    html_parts.append('<div class="comparison-table-scroll-container">')
    html_parts.append('<table class="refined-comparison-table">')

    if block.headers:
        html_parts.append("<thead><tr>")
        for header in block.headers:
            html_parts.append(f"<th>{context._escape(header)}</th>")
        html_parts.append("</tr></thead>")

    if block.rows:
        html_parts.append("<tbody>")
        for row in block.rows:
            html_parts.append("<tr>")
            col_count = len(block.headers) if block.headers else len(row)
            row_list = [str(x) for x in row]
            for col_idx in range(col_count):
                cell_val = ""
                if col_idx < len(row_list):
                    cell_val = context._escape(row_list[col_idx])
                html_parts.append(f"<td>{cell_val}</td>")
            html_parts.append("</tr>")
        html_parts.append("</tbody>")

    html_parts.append("</table>")
    html_parts.append("</div>")
    html_parts.append("</div>")

    return "\n".join(html_parts)


def _render_split_panel(panel: Any, context: Any) -> str:
    left_html = _render_embedded_panel(panel.left_panel, context)
    right_html = _render_embedded_panel(panel.right_panel, context)

    return (
        f'<div class="split-panel">'
        f'<div class="panel-half left">{left_html}</div>'
        f'<div class="panel-half right">{right_html}</div>'
        f"</div>"
    )


def _render_embedded_panel(panel_data: Any, context: Any) -> str:
    title = context._escape(panel_data.title)
    content = context._escape(panel_data.content).replace("\n", "<br>")
    return f"<div class=\"embedded-panel\"><h3>{title}</h3><p>{content}</p></div>"


def _render_grid_item(item: Any, variant: str, index: int, context: Any) -> str:
    if context.animated:
        seg = context._segment_counter
        context._segment_counter += 1
        anim_class = "anim-slide-up"
        html_parts = [
            f'<div class="card {anim_class}" '
            f'data-index="{index}" data-segment="{seg}">'
        ]
    else:
        html_parts = [f'<div class="card" data-index="{index}">']

    if variant in {"bigBullets", "cardGrid"}:
        html_parts.append(f'<div class="card-number"><span>{index + 1}</span></div>')

    icon_class = _icon_class_for_item(item, variant, index)
    if icon_class:
        print(f"   [RENDER] Item Icon: {icon_class} (variant: {variant})")
        html_parts.append(
            f'<div class="card-icon"><i class="{context._escape(icon_class)}"></i></div>'
        )

    html_parts.append('<div class="card-content">')

    title = item.heading or item.label
    if title:
        html_parts.append(f'<h4 class="card-title">{context._escape(title)}</h4>')

    if item.points:
        is_dim_centric = all(":" in str(p) for p in item.points) and len(item.points) > 0
        if is_dim_centric:
            dim_html = []
            for point in item.points:
                subject, value = str(point).split(":", 1)
                dim_html.append(
                    f'<div class="card-comparison-row">'
                    f'<span class="card-comparison-subject">{context._escape(subject.strip())}</span>'
                    f'<span class="card-comparison-value">{context._escape(value.strip())}</span>'
                    f"</div>"
                )
            html_parts.append(f'<div class="card-comparison-grid">{"".join(dim_html)}</div>')
        else:
            points_html = "".join(f"<li>{context._escape(p)}</li>" for p in item.points)
            html_parts.append(f'<ul class="card-list">{points_html}</ul>')
    elif item.description:
        desc_html = context._escape(item.description).replace("\n", "<br>")
        html_parts.append(f'<p class="card-text">{desc_html}</p>')

    html_parts.append("</div>")
    html_parts.append("</div>")

    return "\n".join(html_parts)


def _icon_class_for_item(item: Any, variant: str, index: int) -> str | None:
    if item.icon:
        icon_class = str(item.icon.alt or "").strip()
        if icon_class:
            if not icon_class.startswith("ri-"):
                return f"ri-{icon_class}-line"
            if not (icon_class.endswith("-line") or icon_class.endswith("-fill")):
                concept_bases = ["brain", "pencil", "link", "shield", "star", "heart"]
                if any(base in icon_class for base in concept_bases) or not any(
                    char.isdigit() for char in icon_class[-2:]
                ):
                    return f"{icon_class}-line"
            return icon_class

    if variant == "solidBoxesWithIconsInside":
        default_icons = [
            "ri-lightbulb-line",
            "ri-compass-3-line",
            "ri-flag-2-line",
            "ri-book-open-line",
            "ri-shield-check-line",
            "ri-line-chart-line",
        ]
        return default_icons[index % len(default_icons)]

    return None
