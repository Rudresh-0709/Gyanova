from typing import Any


def render_branching_path(block: Any, context: Any) -> str:
    """
    Render the branching_path variant.

    Expected shape:
        start: {label, description}
        decision: {label, description}
        branches: [
            {
                edge_label, path_label, path_description,
                outcome_label, outcome_description, color
            }
        ]
        fallback: {label, description, style} (optional)
    """

    def _get(source: Any, key: str, default: Any = None) -> Any:
        if source is None:
            return default
        if isinstance(source, dict):
            return source.get(key, default)
        return getattr(source, key, default)

    def _seg(anim_class: str = "anim-fade") -> tuple[str, str]:
        if context.animated:
            seg = context._segment_counter
            context._segment_counter += 1
            return f" {anim_class}", f' data-segment="{seg}"'
        return "", ""

    def _esc(value: Any) -> str:
        return context._escape(str(value)) if value else ""

    start = _get(block, "start", {}) or {}
    decision = _get(block, "decision", {}) or {}
    branches = _get(block, "branches", []) or []
    if not branches:
        items = _get(block, "items", []) or []
        if items:
            print(
                "[RENDER WARNING] branching_path received items[]; expected "
                "start/decision/branches. Converting legacy items as a fallback."
            )
            branches = [
                {
                    "edge_label": f"Option {chr(65 + index)}",
                    "path_label": _get(item, "heading") or _get(item, "label") or f"Path {chr(65 + index)}",
                    "path_description": _get(item, "description", ""),
                    "outcome_label": _get(item, "label") or _get(item, "heading") or f"Outcome {chr(65 + index)}",
                    "outcome_description": _get(item, "description", ""),
                }
                for index, item in enumerate(items)
            ]
        else:
            print(
                "[RENDER WARNING] branching_path received no branches and no "
                "legacy items; rendering schema error state."
            )
            return (
                '<div class="smart-layout" data-variant="branching_path" data-item-count="0">'
                '  <div class="bp-schema-error">'
                '    branching_path requires start, decision, and 2-4 branches.'
                '  </div>'
                '</div>'
            )
    fallback = _get(block, "fallback")
    branch_count = len(branches)
    spine_count = max(branch_count, 1)

    start_anim, start_seg = _seg("anim-fade")
    start_desc = _get(start, "description")
    start_desc_html = (
        f'<span class="bp-node-desc">{_esc(start_desc)}</span>'
        if start_desc else ""
    )
    start_html = (
        f'<div class="bp-start{start_anim}"{start_seg}>'
        f'  <span class="bp-node-label">{_esc(_get(start, "label", "Start"))}</span>'
        f'  {start_desc_html}'
        f'</div>'
    )

    conn1_html = '<div class="bp-connector"></div>'

    dec_anim, dec_seg = _seg("anim-fade")
    decision_html = (
        f'<div class="bp-decision-wrap{dec_anim}"{dec_seg}>'
        f'  <div class="bp-diamond">'
        f'    <span class="bp-diamond-text">{_esc(_get(decision, "label", "Choose"))}</span>'
        f'  </div>'
        f'</div>'
    )

    conn2_html = '<div class="bp-connector"></div>'

    spine_left = round(0.5 / spine_count * 100, 2)
    spine_right = round(0.5 / spine_count * 100, 2)

    branch_cols = []
    for index, branch in enumerate(branches):
        color = _esc(_get(branch, "color", "#2563eb")) or "#2563eb"
        b_anim, b_seg = _seg("anim-slide-up")

        default_suffix = chr(65 + index)
        edge_label = _esc(_get(branch, "edge_label", f"Option {default_suffix}"))
        path_label = _esc(_get(branch, "path_label", f"Path {default_suffix}"))
        path_desc = _esc(_get(branch, "path_description", ""))
        outcome_label = _esc(_get(branch, "outcome_label", f"Outcome {default_suffix}"))
        outcome_desc = _esc(_get(branch, "outcome_description", ""))

        path_desc_html = (
            f'<span class="bp-node-desc">{path_desc}</span>'
            if path_desc else ""
        )
        outcome_desc_html = (
            f'<span class="bp-node-desc">{outcome_desc}</span>'
            if outcome_desc else ""
        )

        branch_cols.append(
            f'<div class="bp-branch{b_anim}"{b_seg} style="--bp-color:{color};">'
            f'  <div class="bp-branch-drop"></div>'
            f'  <span class="bp-edge-label">{edge_label}</span>'
            f'  <div class="bp-path-node">'
            f'    <span class="bp-node-label">{path_label}</span>'
            f'    {path_desc_html}'
            f'  </div>'
            f'  <div class="bp-connector"></div>'
            f'  <div class="bp-outcome-node">'
            f'    <span class="bp-node-label">{outcome_label}</span>'
            f'    {outcome_desc_html}'
            f'  </div>'
            f'</div>'
        )

    branch_row_html = (
        f'<div class="bp-branch-row" '
        f'style="--bp-spine-left:{spine_left}%; --bp-spine-right:{spine_right}%;">'
        f'{"".join(branch_cols)}'
        f'</div>'
    )

    fallback_html = ""
    if fallback:
        fb_anim, fb_seg = _seg("anim-fade")
        fb_desc = _esc(_get(fallback, "description", ""))
        fb_desc_html = f'<span class="bp-node-desc">{fb_desc}</span>' if fb_desc else ""
        style = _get(fallback, "style", "solid")
        dashed_class = " bp-dashed" if style == "dashed" else ""

        fallback_html = (
            f'<div class="bp-fallback-row{fb_anim}"{fb_seg}>'
            f'  <div class="bp-connector{dashed_class}"></div>'
            f'  <div class="bp-fallback">'
            f'    <span class="bp-node-label">{_esc(_get(fallback, "label", "Re-evaluate"))}</span>'
            f'    {fb_desc_html}'
            f'  </div>'
            f'</div>'
        )

    return (
        f'<div class="smart-layout" data-variant="branching_path" data-item-count="{branch_count}">'
        f'  {start_html}'
        f'  {conn1_html}'
        f'  {decision_html}'
        f'  {conn2_html}'
        f'  {branch_row_html}'
        f'  {fallback_html}'
        f'</div>'
    )


def render_conceptual_relational(variant: str, block: Any, context: Any) -> str:
    """
    Renders Conceptual & Relational family blocks.
    Handles SmartLayout variants: hubAndSpoke, venn_overlap, cause_effect_web, 
    ecosystem_map, dependency_chain, relationshipMap, knowledgeWeb.
    """
    if variant == "branching_path":
        return render_branching_path(block, context)

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
        ICON_SKIP_VARIANTS = {
            "relationshipMap"
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

        if variant == "relationshipMap" and index < 2:
            connector_icon = "ri-arrow-right-line"
            if item.icon:
                connector_icon = item.icon.alt
                if not connector_icon.startswith("ri-"):
                    connector_icon = f"ri-{connector_icon}-line"
            card_parts.append(
                f'<div class="relationship-connector"><i class="{context._escape(connector_icon)}"></i></div>'
            )

        card_parts.append("</div>")

        html_parts.append("\n".join(card_parts))

    html_parts.append("</div>")
    return "\n".join(html_parts)
