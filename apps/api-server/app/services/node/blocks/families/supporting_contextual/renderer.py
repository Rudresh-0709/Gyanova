from typing import Any

def render_supporting_contextual(variant: str, block: Any, context: Any) -> str:
    """
    Renders Supporting & Contextual family blocks.
    Handles GyMLCyclicProcessBlock and SmartLayout variants: sequentialOutput, converging_funnel.
    """
    block_type = type(block).__name__

    if variant == "sequentialOutput" or block_type == "GyMLSequentialOutput":
        from ...blocks.families.sequential_process.renderer import render_sequential_process
        return render_sequential_process(variant, block, context)

    if block_type == "GyMLCyclicProcessBlock":
        n = len(block.items)
        items_html = []

        for i, item in enumerate(block.items):
            label = context._escape(item.label)
            desc = context._escape(item.description or "")
            img_url = item.image_url

            if not img_url or img_url == "null":
                img_html = f'<div class="cp-circle-placeholder"><i class="ri-image-line"></i></div>'
            else:
                img_html = f'<img src="{context._escape(img_url)}" alt="{label}" />'

            items_html.append(
                f'<div class="cp-item">'
                f'  <div class="cp-circle">{img_html}</div>'
                f'  <div class="cp-info">'
                f'    <div class="cp-label">{label}</div>'
                f'    <div class="cp-description">{desc}</div>'
                f"  </div>"
                f"</div>"
            )

        # Build per-circle SVG arcs: simple semicircular arrows
        circle_d = 240
        # Keep circles nearly touching so connector arcs feel continuous.
        gap_px = 2
        # Pull arrow endpoints inward so arrowheads don't overlap next start-dot.
        arrow_end_inset = 10
        cr = 118.5  # center of the 3px CSS border (radius 120, border 117-120)
        cy = circle_d / 2  # 120
        total_w = n * circle_d + (n - 1) * gap_px
        step = circle_d + gap_px  # distance between centers

        defs_html = []
        paths_html = []

        for i in range(n):
            cx_i = circle_d / 2 + i * step  # center x of circle i

            # All arrows: start at mid-LEFT, end at mid-RIGHT
            sx = cx_i - cr  # left midpoint (9 o'clock)
            sy = cy
            ex_pt = cx_i + cr - arrow_end_inset  # inset from right midpoint
            ey_pt = cy

            if i % 2 == 0:
                # TOP semicircle: left → top → right (CW, sweep=1)
                sweep = 1
            else:
                # BOTTOM semicircle: left → bottom → right (CCW, sweep=0)
                sweep = 0

            d = (
                f"M {sx:.1f},{sy:.1f} "
                f"A {cr:.1f},{cr:.1f} 0 0,{sweep} {ex_pt:.1f},{ey_pt:.1f}"
            )

            # Arrowhead marker
            arrow_color = "#2e77ff"
            defs_html.append(
                f'<marker id="cp-head-{i}" markerWidth="10" markerHeight="8" '
                f'refX="8" refY="4" orient="auto">'
                f'<polygon points="0 0, 10 4, 0 8" fill="{arrow_color}" />'
                f"</marker>"
            )
            # Filled dot at start point
            paths_html.append(
                f'<circle cx="{sx:.1f}" cy="{sy:.1f}" r="6" fill="#555" />'
            )
            # The arc path
            paths_html.append(
                f'<path d="{d}" fill="none" stroke="{arrow_color}" '
                f'style="fill:none !important; stroke:{arrow_color} !important;" '
                f'stroke-width="4" stroke-linecap="round" '
                f'marker-end="url(#cp-head-{i})" />'
            )

        svg_overlay = (
            f'<svg class="cp-arrows-overlay" viewBox="0 0 {total_w} {circle_d}" '
            f'width="{total_w}" height="{circle_d}" '
            f'preserveAspectRatio="xMidYMid meet">'
            f"<defs>{chr(10).join(defs_html)}</defs>"
            f"{chr(10).join(paths_html)}"
            f"</svg>"
        )

        return (
            f'<div class="cyclic-process-container" data-count="{n}">'
            f'  <div class="cp-items-row" style="gap:{gap_px}px; '
            f'width:{total_w}px; margin:0 auto;">'
            f'{"".join(items_html)}'
            f"</div>"
            f"  {svg_overlay}"
            f"</div>"
        )

    # SmartLayout rendering for converging_funnel
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
