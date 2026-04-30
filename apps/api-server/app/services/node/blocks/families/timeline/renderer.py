"""
Timeline & Chronological block family renderer.
"""

from typing import Any

def render_timeline(variant: str, block: Any, context: Any) -> str:
    """Render Timeline & Chronological family blocks."""
    item_count = len(block.items)
    
    html_parts = [
        f'<div class="smart-layout" '
        f'data-variant="{variant}" '
        f'data-item-count="{item_count}">'
    ]
    
    for index, item in enumerate(block.items):
        # Animation: cards get data-segment for sequential reveal
        if context.animated:
            seg = context._segment_counter
            context._segment_counter += 1
            anim_class = "anim-slide-up"
            html_parts.append(
                f'<div class="card {anim_class}" '
                f'data-index="{index}" data-segment="{seg}">'
            )
        else:
            html_parts.append(f'<div class="card" data-index="{index}">')

        # timelineIcon: show icon in the badge position instead of a number
        if variant == "timelineIcon":
            icon_cls = "ri-checkbox-blank-circle-fill"  # default fallback
            if item.icon:
                icon_cls = item.icon.alt
                if not icon_cls.startswith("ri-"):
                    icon_cls = f"ri-{icon_cls}-line"
            html_parts.append(
                f'<div class="card-number timeline-icon-badge"><i class="{context._escape(icon_cls)}"></i></div>'
            )

        # Content
        html_parts.append('<div class="card-content">')

        if variant == "timeline":
            if item.year:
                html_parts.append(
                    f'<div class="card-year">{context._escape(item.year)}</div>'
                )
            if item.description:
                html_parts.append(
                    f'<p class="card-text">{context._escape(item.description)}</p>'
                )
        else:
            title = item.heading or item.label
            if title:
                html_parts.append(f'<h4 class="card-title">{context._escape(title)}</h4>')

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
                    html_parts.append(f'<div class="card-comparison-grid">{"".join(dim_html)}</div>')
                else:
                    points_html = "".join(
                        f"<li>{context._escape(p)}</li>" for p in item.points
                    )
                    html_parts.append(f'<ul class="card-list">{points_html}</ul>')
            elif item.description:
                desc_html = context._escape(item.description).replace("\n", "<br>")
                html_parts.append(f'<p class="card-text">{desc_html}</p>')

        html_parts.append("</div>")
        html_parts.append("</div>")

    html_parts.append("</div>")
    return "\n".join(html_parts)
