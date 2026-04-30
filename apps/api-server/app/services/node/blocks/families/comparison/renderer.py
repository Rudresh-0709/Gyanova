from typing import Any

def render_comparison(variant: str, block: Any, context: Any) -> str:
    """
    Renders Comparison family blocks.
    Handles GyMLComparisonTable and SmartLayout variants 
    (comparison, comparisonProsCons, comparisonBeforeAfter, ranking_ladder, spectrum_scale, weighted_comparison).
    """
    block_type = type(block).__name__

    if block_type == "GyMLComparisonTable":
        html_parts = ['<div class="comparison-table-wrapper">']
        
        if block.caption:
            html_parts.append(
                f'<h3 class="comparison-table-title">{context._escape(block.caption)}</h3>'
            )

        html_parts.append('<div class="comparison-table-scroll-container">')
        html_parts.append('<table class="refined-comparison-table">')
        
        # Headers
        if block.headers:
            html_parts.append('<thead><tr>')
            for header in block.headers:
                html_parts.append(f'<th>{context._escape(header)}</th>')
            html_parts.append('</tr></thead>')
            
        # Body rows
        if block.rows:
            html_parts.append('<tbody>')
            for row in block.rows:
                html_parts.append('<tr>')
                # Guarantee matching column count
                headers_list = block.headers
                col_count = len(headers_list) if headers_list else len(row)
                for col_idx in range(col_count):
                    # Manual indexing to avoid list(row) confusion
                    cell_val = ""
                    row_list = [str(x) for x in row]
                    if col_idx < len(row_list):
                        cell_val = context._escape(row_list[col_idx])
                    html_parts.append(f'<td>{cell_val}</td>')
                html_parts.append('</tr>')
            html_parts.append('</tbody>')
            
        html_parts.append('</table>')
        html_parts.append('</div>')
        html_parts.append('</div>')
        
        return "\n".join(html_parts)

    # SmartLayout rendering
    item_count = len(block.items)
    class_attr = "smart-layout"
    
    html_parts = [
        f'<div class="{class_attr}" '
        f'data-variant="{variant}" '
        f'data-item-count="{item_count}">'
    ]

    for index, item in enumerate(block.items):
        if context.animated:
            seg = context._segment_counter
            context._segment_counter += 1
            # Comparison cards slide from sides, others slide up
            if variant == "comparison":
                direction = "left" if index == 0 else "right"
                anim_class = f"anim-slide-{direction}"
            else:
                anim_class = "anim-slide-up"
            card_parts = [
                f'<div class="card {anim_class}" '
                f'data-index="{index}" data-segment="{seg}">'
            ]
        else:
            card_parts = [f'<div class="card" data-index="{index}">']

        # Auto-Icon Selection
        ICON_SKIP_VARIANTS = {
            "comparison"
        }
        icon_class = None
        if variant not in ICON_SKIP_VARIANTS:
            if item.icon:
                icon_class = str(item.icon.alt or "").strip()
                if icon_class:
                    if not icon_class.startswith("ri-"):
                        icon_class = f"ri-{icon_class}-line"
                    elif not (icon_class.endswith("-line") or icon_class.endswith("-fill")):
                        concept_bases = ["brain", "pencil", "link", "shield", "star", "heart"]
                        if any(b in icon_class for b in concept_bases) or not any(c.isdigit() for c in icon_class[-2:]):
                             icon_class = f"{icon_class}-line"
            elif variant == "comparisonProsCons":
                icon_class = "ri-check-line" if index == 0 else "ri-close-line"

        if icon_class:
            print(f"   [RENDER] Item Icon: {icon_class} (variant: {variant})")
            card_parts.append(
                f'<div class="card-icon"><i class="{context._escape(icon_class)}"></i></div>'
            )

        # Content
        card_parts.append('<div class="card-content">')

        title = item.heading or item.label
        if title:
            card_parts.append(f'<h4 class="card-title">{context._escape(title)}</h4>')

        if item.points:
            is_dim_centric = all(":" in str(p) for p in item.points) and len(item.points) > 0
            if is_dim_centric:
                dim_html = []
                for p in item.points:
                    parts = str(p).split(":", 1)
                    sub = parts[0].strip()
                    val = parts[1].strip()
                    dim_html.append(
                        f'<div class="card-comparison-row">'
                        f'<span class="card-comparison-subject">{context._escape(sub)}</span>'
                        f'<span class="card-comparison-value">{context._escape(val)}</span>'
                        f'</div>'
                    )
                card_parts.append(f'<div class="card-comparison-grid">{"".join(dim_html)}</div>')
            else:
                points_html = "".join(
                    f"<li>{context._escape(p)}</li>" for p in item.points
                )
                card_parts.append(f'<ul class="card-list">{points_html}</ul>')
        elif item.description:
            desc_html = context._escape(item.description).replace("\n", "<br>")
            card_parts.append(f'<p class="card-text">{desc_html}</p>')

        card_parts.append("</div>")
        card_parts.append("</div>")

        html_parts.append("\n".join(card_parts))

    html_parts.append("</div>")
    return "\n".join(html_parts)
