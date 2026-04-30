from typing import Any

def render_stats_quantitative(variant: str, block: Any, context: Any) -> str:
    """
    Renders Stats & Quantitative family blocks.
    Handles SmartLayout variants: progress_bars, score_card, change_delta, stats.
    """
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
            anim_class = "anim-slide-up"
            card_parts = [
                f'<div class="card {anim_class}" '
                f'data-index="{index}" data-segment="{seg}">'
            ]
        else:
            card_parts = [f'<div class="card" data-index="{index}">']

        # Auto-Icon Selection
        icon_class = None
        if item.icon:
            icon_class = str(item.icon.alt or "").strip()
            if icon_class:
                if not icon_class.startswith("ri-"):
                    icon_class = f"ri-{icon_class}-line"
                elif not (icon_class.endswith("-line") or icon_class.endswith("-fill")):
                    concept_bases = ["brain", "pencil", "link", "shield", "star", "heart"]
                    if any(b in icon_class for b in concept_bases) or not any(c.isdigit() for c in icon_class[-2:]):
                         icon_class = f"{icon_class}-line"

        if icon_class:
            print(f"   [RENDER] Item Icon: {icon_class} (variant: {variant})")
            card_parts.append(
                f'<div class="card-icon"><i class="{context._escape(icon_class)}"></i></div>'
            )

        # Content
        card_parts.append('<div class="card-content">')

        if variant == "stats":
            if item.value:
                card_parts.append(
                    f'<div class="card-value">{context._escape(item.value)}</div>'
                )
            if item.label:
                card_parts.append(
                    f'<div class="card-label">{context._escape(item.label)}</div>'
                )

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
