from typing import Any

def render_sequential_process(variant: str, block: Any, context: Any) -> str:
    """
    Renders Sequential & Process family blocks.
    Handles standalone blocks (GyMLSequentialOutput, GyMLProcessArrowBlock)
    and SmartLayout variants (processSteps, processAccordion, sequentialSteps, etc.).
    """
    if variant == "branching_path":
        from ..conceptual_relational.renderer import render_branching_path

        return render_branching_path(block, context)

    block_type = type(block).__name__

    if block_type == "GyMLSequentialOutput":
        items_html = []
        for i, item in enumerate(block.items):
            anim_attrs = ""
            anim_class = ""
            if context.animated:
                seg = context._segment_counter
                context._segment_counter += 1
                anim_attrs = f' data-segment="{seg}"'
                anim_class = " anim-typewriter"
            
            items_html.append(
                f'<div class="output-line{anim_class}"{anim_attrs}>'
                f'<span class="prompt-symbol">></span>'
                f'<span class="line-text">{context._escape(item)}</span>'
                f'</div>'
            )
        return f'<div class="sequential-output-container">{"".join(items_html)}</div>'

    elif block_type == "GyMLProcessArrowBlock":
        n = len(block.items)
        items_html = []

        blue_palette = ["#1e3a8a", "#2563eb", "#3b82f6", "#60a5fa", "#93c5fd"]
        for i, item in enumerate(block.items):
            color = item.color or blue_palette[i % len(blue_palette)]
            image_url = item.image_url

            # Minimalist Image Card
            if not image_url or image_url == "null":
                image_html = f'<div class="pa-img-minimal placeholder" style="--item-color: {color}"><i class="ri-image-line"></i></div>'
            else:
                image_html = f'<div class="pa-img-minimal"><img src="{context._escape(image_url)}" alt="{context._escape(item.label)}" /></div>'

            is_first = i == 0
            is_last = i == (n - 1)
            item_class = "pa-col-min"
            if is_first:
                item_class += " is-first"
            if is_last:
                item_class += " is-last"

            label = context._escape(item.label)
            desc_html = ""
            if item.description:
                desc_html = (
                    f'<div class="pa-desc-min">{context._escape(item.description)}</div>'
                )

            anim_attrs = ""
            anim_class = ""
            if context.animated:
                seg = context._segment_counter
                context._segment_counter += 1
                anim_attrs = f' data-segment="{seg}"'
                anim_class = " anim-fade"

            items_html.append(
                f'<div class="{item_class}{anim_class}"{anim_attrs} style="--item-color: {color};">'
                f"  {image_html}"
                f'  <div class="pa-arrow-min">'
                f"    <span>{label}</span>"
                f"  </div>"
                f"  {desc_html}"
                f"</div>"
            )

        return (
            f'<div class="pa-container-min" data-count="{n}">'
            f'  {"".join(items_html)}'
            f"</div>"
        )

    if variant == "processAccordion":
        item_count = len(block.items)
        html_parts = [
            '<div class="smart-layout process-accordion-layout" '
            f'data-variant="{variant}" '
            f'data-item-count="{item_count}">'
        ]

        for index, item in enumerate(block.items):
            title = getattr(item, "heading", None) or getattr(item, "label", None) or f"Step {index + 1}"
            title_escaped = context._escape(title)
            open_attr = " open" if index == 0 else ""

            anim_attrs = ""
            anim_class = ""
            if context.animated:
                seg = context._segment_counter
                context._segment_counter += 1
                anim_attrs = f' data-segment="{seg}"'
                anim_class = " anim-slide-up"

            icon_class = None
            if getattr(item, "icon", None):
                icon_class = str(item.icon.alt or "").strip()
                if icon_class:
                    if not icon_class.startswith("ri-"):
                        icon_class = f"ri-{icon_class}-line"
                    elif not (icon_class.endswith("-line") or icon_class.endswith("-fill")):
                        icon_class = f"{icon_class}-line"
            if not icon_class:
                icon_class = "ri-focus-3-line"

            panel_parts = []
            points = getattr(item, "points", None)
            if not points:
                # Fallback: convert description text into point items so accordion
                # content always renders as bullets.
                description = str(getattr(item, "description", "") or "").strip()
                if description:
                    raw_chunks = [chunk.strip(" -•\t\r\n") for chunk in description.split("\n")]
                    filtered_chunks = [chunk for chunk in raw_chunks if chunk]
                    points = filtered_chunks or [description]
                else:
                    points = []

            if points:
                list_items = "".join(f"<li>{context._escape(p)}</li>" for p in points)
                panel_parts.append(
                    f'<div class="process-accordion-body">'
                    f'  <div class="process-accordion-body-icon"><i class="{context._escape(icon_class)}"></i></div>'
                    f'  <ul class="process-accordion-list-points">{list_items}</ul>'
                    f"</div>"
                )

            html_parts.append(
                f'<details class="process-accordion-item{anim_class}" data-index="{index}"{anim_attrs}{open_attr}>'
                f'  <summary class="process-accordion-summary">'
                f'    <span class="process-accordion-step">{index + 1}</span>'
                f'    <span class="process-accordion-title">{title_escaped}</span>'
                f'  </summary>'
                f'  <div class="process-accordion-panel">{"".join(panel_parts)}</div>'
                f"</details>"
            )

        html_parts.append("</div>")
        return "\n".join(html_parts)

    # SmartLayout image_process should use the same visual structure as GyMLProcessArrowBlock.
    if variant == "image_process":
        n = len(block.items)
        items_html = []
        blue_palette = ["#1e3a8a", "#2563eb", "#3b82f6", "#60a5fa", "#93c5fd"]

        for i, item in enumerate(block.items):
            color = getattr(item, "color", None) or blue_palette[i % len(blue_palette)]
            image_url = getattr(item, "image_url", None)

            title = getattr(item, "heading", None) or getattr(item, "label", None) or f"Step {i + 1}"
            title_escaped = context._escape(title)

            if not image_url or image_url == "null":
                image_html = (
                    f'<div class="pa-img-minimal placeholder" style="--item-color: {color}">'
                    f'<i class="ri-image-line"></i></div>'
                )
            else:
                image_html = (
                    f'<div class="pa-img-minimal">'
                    f'<img src="{context._escape(image_url)}" alt="{title_escaped}" />'
                    f"</div>"
                )

            is_first = i == 0
            is_last = i == (n - 1)
            item_class = "pa-col-min"
            if is_first:
                item_class += " is-first"
            if is_last:
                item_class += " is-last"

            desc_html = ""
            description = getattr(item, "description", None)
            if description:
                desc_html = f'<div class="pa-desc-min">{context._escape(description)}</div>'

            anim_attrs = ""
            anim_class = ""
            if context.animated:
                seg = context._segment_counter
                context._segment_counter += 1
                anim_attrs = f' data-segment="{seg}"'
                anim_class = " anim-fade"

            items_html.append(
                f'<div class="{item_class}{anim_class}"{anim_attrs} style="--item-color: {color};">'
                f"  {image_html}"
                f'  <div class="pa-arrow-min">'
                f"    <span>{title_escaped}</span>"
                f"  </div>"
                f"  {desc_html}"
                f"</div>"
            )

        return (
            f'<div class="pa-container-min" data-count="{n}">'
            f'  {"".join(items_html)}'
            f"</div>"
        )

    # Otherwise, it is a SmartLayout node (or behaves like one).
    item_count = len(block.items)
    class_attr = "smart-layout"
    
    html_parts = [
        f'<div class="{class_attr}" '
        f'data-variant="{variant}" '
        f'data-item-count="{item_count}">'
    ]

    for index, item in enumerate(block.items):
        item_class = "arrow-step" if variant == "processArrow" else "card"
        if context.animated:
            seg = context._segment_counter
            context._segment_counter += 1
            anim_class = "anim-slide-up"
            card_parts = [
                f'<div class="{item_class} {anim_class}" '
                f'data-index="{index}" data-segment="{seg}">'
            ]
        else:
            card_parts = [f'<div class="{item_class}" data-index="{index}">']

        # Number badge at top
        if variant in ["processSteps", "processArrow", "sequentialOutput"]:
            card_parts.append(f'<div class="card-number"><span>{index + 1}</span></div>')

        # Icon processing
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
        
        # Fallback for sequentialOutput if the LLM didn't generate icons yet
        if not icon_class and variant == "sequentialOutput":
            fallbacks = ["file-text", "pie-chart", "settings-3", "search-eye", "trophy", "flag", "lightbulb"]
            icon_class = f"ri-{fallbacks[index % len(fallbacks)]}-line"

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
