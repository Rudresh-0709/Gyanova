"""
GyML Renderer

PASSIVE renderer: GyML → HTML.
Maps GyML structure to HTML without any inference or semantic decisions.
Designed to match Gamma-style professional slides.
"""

from typing import List, Optional, Dict, Any
import html

from .definitions import (
    GyMLSection,
    GyMLBody,
    GyMLHeading,
    GyMLParagraph,
    GyMLColumns,
    GyMLColumnDiv,
    GyMLSmartLayout,
    GyMLSmartLayoutItem,
    GyMLImage,
    GyMLDivider,
    GyMLTable,
    GyMLCode,
    GyMLComparisonTable,
    GyMLKeyValueList,
    GyMLRichText,
    GyMLNumberedList,
    GyMLLabeledDiagram,
    GyMLHierarchyTree,
    GyMLSplitPanel,
    GyMLFormulaBlock,
    GyMLHubAndSpoke,
    GyMLCyclicBlock,
    GyMLProcessArrowBlock,
    GyMLProcessArrowItem,
    GyMLCyclicProcessBlock,
    GyMLCyclicProcessItem,
    GyMLFeatureShowcaseBlock,
    GyMLSequentialOutput,
    GyMLNode,
)
from .theme import Theme, THEMES
from .responsive import ResponsiveConstraints
from .hierarchy import VisualHierarchy


class GyMLRenderer:
    """
    PASSIVE renderer: GyML → HTML.
    Gamma-style professional output.

    When animated=True, injects data-segment attributes on primary content
    (smart_layout cards only) for reveal animations synced to narration audio.
    All other elements (paragraphs, columns, headings, accent images, tables,
    code blocks) remain always visible.
    """

    def __init__(
        self,
        theme: Optional[Theme] = None,
        responsive_constraints: Optional[ResponsiveConstraints] = None,
        animated: bool = False,
    ):
        self.theme = theme or THEMES.get("gamma_light")
        self.responsive_constraints = (
            responsive_constraints or ResponsiveConstraints.default()
        )
        self.animated = animated
        self._segment_counter = 0  # tracks current segment index per section
        self._current_accent_image_src: Optional[str] = None

    def render(self, section: GyMLSection) -> str:
        """Passively render GyML section to HTML."""
        # Reset segment counter for each section
        self._segment_counter = 0
        lines: List[str] = []

        # Generate hierarchy CSS variables if present
        style_attr: str = ""
        vars_list: List[str] = []
        if section.hierarchy:
            # Typography
            vars_list.append(f"--h1-size: {section.hierarchy.typography.h1}")
            vars_list.append(f"--h2-size: {section.hierarchy.typography.h2}")
            vars_list.append(f"--p-size: {section.hierarchy.typography.body}")
            vars_list.append(
                f"--line-height: {section.hierarchy.typography.line_height_base}"
            )
            vars_list.append(
                f"--card-number-size: {section.hierarchy.typography.card_number}"
            )
            vars_list.append(f"--card-text-size: {section.hierarchy.typography.small}")

            # Spacing
            vars_list.append(
                f"--section-padding: {section.hierarchy.spacing.section_padding}"
            )
            vars_list.append(f"--block-gap: {section.hierarchy.spacing.block_gap}")
            vars_list.append(
                f"--card-padding: {section.hierarchy.spacing.card_padding}"
            )
            h_gap = (
                section.hierarchy.spacing.heading_gap
                or section.hierarchy.spacing.block_gap
            )
            vars_list.append(f"--heading-gap: {h_gap}")

            style_attr = f' style="{"; ".join(vars_list)}"'

        # Add animated data attribute so CSS knows to apply animation styles
        anim_attr = ' data-animated="true"' if self.animated else ""

        # Add density hint so CSS can compact card internals for dense slides
        density_attr = ""
        density_val = section.slide_density or (
            section.hierarchy.name if section.hierarchy else None
        )
        if density_val:
            density_attr = f' data-density="{density_val}"'

        # Add special class for hub-and-spoke slides to handle layout safely
        has_hub = any(
            isinstance(node, GyMLHubAndSpoke) for node in section.body.children
        )
        hub_class = " holds-hub" if has_hub else ""

        # Identify if this slide has a comparison block (to adjust layout width)
        has_comparison = False
        for node in section.body.children:
            node_variant = getattr(node, "variant", "")
            if isinstance(node, GyMLSmartLayout):
                v = str(node_variant).lower()
                if v.startswith("comparison") or "comparison" in v:
                    has_comparison = True
                    break
            elif isinstance(node, GyMLComparisonTable):
                has_comparison = True
                break
            elif str(getattr(node, "type", "")).endswith("comparison"):
                has_comparison = True
                break
        
        accent_width = "180px" if has_comparison else "500px"
        block_gap = "1rem" if has_comparison else "3rem"
        comparison_class = " comparison-layout" if has_comparison else ""
        
        vars_list_str = "; ".join(vars_list) if section.hierarchy else ""

        # Used by CSS to gracefully fall back to "blank" layout when a planner chose
        # left/right/top/bottom but no accent image is actually present.
        render_image = section.image_layout != "blank"
        has_image_attr = (
            ' data-has-image="true"'
            if (render_image and section.accent_image is not None)
            else ' data-has-image="false"'
        )
        lines.append(
            f'<section id="{self._escape(section.id)}" '
            f'class="slide-section{hub_class}{comparison_class}" '
            f'role="region" aria-label="Slide {section.id}" '
            f'data-image-layout="{section.image_layout}" '
            f'style="--accent-width: {accent_width}; --block-gap: {block_gap}; {vars_list_str}"'
            f"{anim_attr}{density_attr}{has_image_attr}>"
        )

        # 'behind' layout needs the image to be technically before the body 
        # but styled as absolute background.
        render_image_early = render_image and section.image_layout != "bottom"

        if section.accent_image and render_image_early:
            # Wrap accent image + optional caption in a container
            has_caption = section.image_caption is not None
            if has_caption:
                lines.append('<div class="accent-image-group">')

            lines.append(self._render_accent_image(section.accent_image))

            if has_caption:
                caption_text = self._escape(section.image_caption.text)
                lines.append(
                    f'<p class="p-annotation image-annotation">{caption_text}</p>'
                )
                lines.append("</div>")

        previous_accent_src = self._current_accent_image_src
        self._current_accent_image_src = (
            section.accent_image.src
            if section.accent_image and section.accent_image.src != "placeholder"
            else None
        )
        lines.append(self._render_body(section.body))
        self._current_accent_image_src = previous_accent_src

        # Render Image late if it's bottom layout
        if section.accent_image and render_image and not render_image_early:
            has_caption = section.image_caption is not None
            if has_caption:
                lines.append('<div class="accent-image-group">')

            lines.append(self._render_accent_image(section.accent_image))

            if has_caption:
                caption_text = self._escape(section.image_caption.text)
                lines.append(
                    f'<p class="p-annotation image-annotation">{caption_text}</p>'
                )
                lines.append("</div>")
        lines.append("</section>")

        return "\n".join(lines)

    def render_many(self, sections: List[GyMLSection]) -> str:
        """Render multiple sections."""
        rendered_sections = [self.render(s) for s in sections]
        return "\n\n".join(rendered_sections)

    def render_complete(self, sections: List[GyMLSection]) -> str:
        """Render complete HTML document with Gamma-style styles."""
        sections_html = self.render_many(sections)
        animator_js = self._get_animator_js() if self.animated else ""

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GyML Slides</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/remixicon@4.2.0/fonts/remixicon.css" rel="stylesheet">
    
    <!-- KaTeX for professional math rendering -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
    <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
    <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js" onload="renderMathInElement(document.body, {{ 
        delimiters: [
            {{left: '$$', right: '$$', display: true}},
            {{left: '$', right: '$', display: false}},
            {{left: '\\\\(', right: '\\\\)', display: false}},
            {{left: '\\\\[', right: '\\\\]', display: true}}
        ],
        throwOnError : false 
    }});"></script>

    <style>
{self._get_gamma_styles()}
{self.theme.to_css_vars() if self.theme else ""}
{self._get_responsive_styles()}
    </style>
</head>
<body>
    <div class="gyml-deck">
{sections_html}
    </div>
{animator_js}
</body>
</html>"""

    def _get_responsive_styles(self) -> str:
        """Generate responsive CSS from constraints."""
        c = self.responsive_constraints
        css = ["/* Dynamic Responsive Styles */"]

        # 1. Breakpoints
        for bp_name, width in c.breakpoints.items():
            fallback_padding = c.viewport_padding.get(bp_name, "1rem")
            scale = c.typography_scale.get(bp_name, 1.0)

            css.append(f"@media (max-width: {width}px) {{")

            # Global adjustments
            css.append("  :root {")
            css.append(f"    --section-padding: {fallback_padding};")
            # We can scale the base font size if we used rems correctly
            css.append(f"    font-size: {scale * 100}%;")
            css.append("  }")

            # Apply layout fallbacks
            if c.layout_fallbacks.get("columns") == "stack":
                css.append("  .columns { flex-direction: column; }")
                css.append("  .column { flex: 1 1 100% !important; }")

            if c.layout_fallbacks.get("image_layout") == "stack":
                css.append(
                    "  section[data-image-layout='right'], section[data-image-layout='left'] {"
                )
                css.append(
                    "    grid-template-columns: 1fr; display: flex; flex-direction: column;"
                )
                css.append("  }")
                css.append("  .accent-image { max-width: 100%; margin-bottom: 1rem; }")

            css.append("}")

        return "\n".join(css)

    # =========================================================================
    # ELEMENT RENDERERS
    # =========================================================================

    def _render_accent_image(self, image: GyMLImage) -> str:
        """Render accent image."""
        if image.src == "placeholder":
            return (
                f'<div class="accent-image-placeholder">'
                f'<div class="placeholder-content">'
                f'<span class="placeholder-icon">🖼️</span>'
                f'<span class="placeholder-text">{self._escape(image.alt)}</span>'
                f"</div>"
                f"</div>"
            )

        return (
            f'<div class="accent-image-wrapper">'
            f'<img class="accent-image" '
            f'src="{self._escape(image.src)}" '
            f'alt="{self._escape(image.alt or "")}" '
            f'loading="lazy" referrerpolicy="no-referrer" />'
            f"</div>"
        )

    def _render_body(self, body: GyMLBody) -> str:
        """Render body container."""
        children_html: List[str] = []
        separator_count: int = 0  # Max 1 separator per slide
        for i, child in enumerate(body.children):
            rendered = self._render_node(child)
            if rendered:
                children_html.append(rendered)

                # Add separator logic (between distinct major blocks) — max 1 per slide
                if i < len(body.children) - 1 and int(separator_count) < 1:
                    next_child = body.children[i + 1]

                    # Geometry Rule: Separator between Dense (Visual) and Flow (Text)
                    is_dense_current = isinstance(
                        child, (GyMLColumns, GyMLSmartLayout, GyMLTable, GyMLCode)
                    )
                    is_dense_next = isinstance(
                        next_child, (GyMLColumns, GyMLSmartLayout, GyMLTable, GyMLCode)
                    )

                    # Flow elements: Paragraph, Heading
                    is_flow_current = isinstance(child, (GyMLParagraph, GyMLHeading))
                    is_flow_next = isinstance(next_child, (GyMLParagraph, GyMLHeading))

                    should_separate = (
                        (is_dense_current and is_dense_next)  # Between two visuals
                        or (is_dense_current and is_flow_next)  # Visual -> Text
                        or (is_flow_current and is_dense_next)  # Text -> Visual
                    )

                    if should_separate:
                        children_html.append('<div class="block-separator"></div>')
                        separator_count = int(separator_count) + 1

        return f'<div class="body">\n{chr(10).join(children_html)}\n</div>'

    def _render_node(self, node: GyMLNode) -> Optional[str]:
        """Render any GyML node by type."""
        if isinstance(node, GyMLHeading):
            return self._render_heading(node)
        elif isinstance(node, GyMLParagraph):
            return self._render_paragraph(node)
        elif isinstance(node, GyMLColumns):
            return self._render_columns(node)
        elif isinstance(node, GyMLSmartLayout):
            return self._render_smart_layout(node)
        elif isinstance(node, GyMLImage):
            return self._render_inline_image(node)
        elif isinstance(node, GyMLDivider):
            return self._render_divider()
        elif isinstance(node, GyMLCode):
            return self._render_code(node)
        elif isinstance(node, GyMLTable):
            return self._render_table(node)
        elif isinstance(node, GyMLComparisonTable):
            return self._render_comparison_table(node)
        elif isinstance(node, GyMLKeyValueList):
            return self._render_key_value_list(node)
        elif isinstance(node, GyMLRichText):
            return self._render_rich_text(node)
        elif isinstance(node, GyMLNumberedList):
            return self._render_numbered_list(node)
        elif isinstance(node, GyMLLabeledDiagram):
            return self._render_labeled_diagram(node)
        elif isinstance(node, GyMLHierarchyTree):
            return self._render_hierarchy_tree(node)
        elif isinstance(node, GyMLSplitPanel):
            return self._render_split_panel(node)
        elif isinstance(node, GyMLFormulaBlock):
            return self._render_formula_block(node)
        elif isinstance(node, GyMLHubAndSpoke):
            return self._render_hub_and_spoke(node)
        elif isinstance(node, GyMLCyclicBlock):
            return self._render_cyclic_block(node)
        elif isinstance(node, GyMLProcessArrowBlock):
            return self._render_process_arrow_block(node)
        elif isinstance(node, GyMLCyclicProcessBlock):
            return self._render_cyclic_process_block(node)
        elif isinstance(node, GyMLFeatureShowcaseBlock):
            return self._render_feature_showcase(node)
        elif isinstance(node, GyMLSequentialOutput):
            return self._render_sequential_output(node)
        return f"<!-- Unknown node type: {type(node).__name__} -->"

    def _render_heading(self, heading: GyMLHeading) -> str:
        """Render heading."""
        level = heading.level
        text = self._escape(heading.text)
        return f"<h{level}>{text}</h{level}>"

    def _render_paragraph(self, paragraph: GyMLParagraph) -> str:
        """Render paragraph with optional icon support."""
        text = self._escape(paragraph.text)
        variant_class = f"p-{paragraph.variant}" if paragraph.variant else ""

        # Icon map for specific paragraph variants
        icon_map = {
            "annotation": "ri-information-line",
            "callout": "ri-lightbulb-line",
            "takeaway": "ri-check-line"
        }

        # Build paragraph with optional icon wrapper
        if paragraph.variant in icon_map:
            icon_class = icon_map[paragraph.variant]
            class_attr = f' class="{variant_class} p-with-icon"' if variant_class else ' class="p-with-icon"'
            return f'<p{class_attr}><span class="p-icon" aria-hidden="true"><i class="{icon_class}"></i></span><span class="p-text">{text}</span></p>'
        else:
            class_attr = f' class="{variant_class}"' if variant_class else ""
            return f"<p{class_attr}>{text}</p>"

    def _render_divider(self) -> str:
        """Render divider."""
        return '<hr class="divider" />'

    def _render_inline_image(self, image: GyMLImage) -> str:
        """Render inline image."""
        if not image.src or image.src.lower() == "null":
            return ""

        src = image.src.strip()
        src_lower = src.lower()

        # Replace known placeholder URLs with the generated accent image when available.
        if src_lower == "placeholder" or "example.com/" in src_lower:
            if self._current_accent_image_src:
                src = self._current_accent_image_src
            else:
                return ""

        components = [
            f'<figure class="inline-image">',
            f'<img src="{self._escape(src)}" '
            f'alt="{self._escape(image.alt or "")}" '
            f'loading="lazy" referrerpolicy="no-referrer" />',
        ]

        if image.alt:
            components.append(
                f'<figcaption class="p-annotation image-caption">{self._escape(image.alt)}</figcaption>'
            )

        components.append("</figure>")
        return "".join(components)

    def _render_code(self, code: GyMLCode) -> str:
        """Render code block."""
        return (
            f'<div class="code-block" data-variant="{self._escape(code.variant)}">'
            f'<pre><code class="language-{self._escape(code.language)}">'
            f"{self._escape(code.code)}"
            f"</code></pre>"
            f"</div>"
        )

    def _render_table(self, table: GyMLTable) -> str:
        """Render table."""
        headers_html = "".join(f"<th>{self._escape(h)}</th>" for h in table.headers)

        rows_html = []
        for row in table.rows:
            cells_html = "".join(f"<td>{self._escape(c)}</td>" for c in row)
            rows_html.append(f"<tr>{cells_html}</tr>")

        return (
            f'<div class="table-container" data-variant="{self._escape(table.variant)}">'
            f"<table>"
            f"<thead><tr>{headers_html}</tr></thead>"
            f'<tbody>{"".join(rows_html)}</tbody>'
            f"</table>"
            f"</div>"
        )

    def _render_columns(self, columns: GyMLColumns) -> str:
        """Render columns as flex container."""
        widths_str = ",".join(str(w) for w in columns.colwidths)

        html_parts = [f'<div class="columns" data-colwidths="{widths_str}">']

        for i, col in enumerate(columns.columns):
            width = columns.colwidths[i] if i < len(columns.colwidths) else 50

            # Columns are always visible (not animated)
            html_parts.append(
                f'<div class="column" style="flex: 0 0 calc({width}% - 1rem);">'
            )

            for child in col.children:
                rendered = self._render_node(child)
                if rendered:
                    html_parts.append(rendered)

            html_parts.append("</div>")

        html_parts.append("</div>")
        return "\n".join(html_parts)

    def _render_smart_layout(self, layout: GyMLSmartLayout) -> str:
        """Render smart-layout as grid container."""
        variant = self._escape(layout.variant)
        item_count = len(layout.items)
        extra_classes = []

        # Variety rotation for diamondGrid sub-layouts
        if variant == "diamondGrid":
            # Initialize a simple counter on the instance if not present
            if not hasattr(self, "_diamond_idx"):
                self._diamond_idx = 0
            
            if item_count == 4:
                # Rotate between Row and 2x2 Grid
                if self._diamond_idx % 2 == 1:
                    extra_classes.append("grid-2d")
            elif item_count in {3, 5}:
                # Rotate between Vertical and Diagonal
                if self._diamond_idx % 2 == 1:
                    extra_classes.append("diagonal")
            
            self._diamond_idx += 1

        class_attr = ' '.join(["smart-layout"] + extra_classes)
        html_parts = [
            f'<div class="{class_attr}" '
            f'data-variant="{variant}" '
            f'data-item-count="{item_count}">'
        ]

        for i, item in enumerate(layout.items):
            html_parts.append(self._render_smart_layout_item(item, layout.variant, i))

        html_parts.append("</div>")
        return "\n".join(html_parts)

    def _render_smart_layout_item(
        self, item: GyMLSmartLayoutItem, variant: str, index: int = 0
    ) -> str:
        """Render smart-layout-item Gamma-style."""
        # Animation: cards get data-segment for sequential reveal
        # Each card maps to one narration segment
        if self.animated:
            seg = self._segment_counter
            self._segment_counter += 1
            # Comparison cards slide from sides, others slide up
            if variant == "comparison":
                direction = "left" if index == 0 else "right"
                anim_class = f"anim-slide-{direction}"
            else:
                anim_class = "anim-slide-up"
            html_parts = [
                f'<div class="card {anim_class}" '
                f'data-index="{index}" data-segment="{seg}">'
            ]
        else:
            html_parts = [f'<div class="card" data-index="{index}">']

        # Number badge at top (Gamma style)
        if variant in [
            "bigBullets",
            "processSteps",
            "processArrow",
            "cardGrid",
            "timelineSequential",
        ]:
            html_parts.append(f'<div class="card-number"><span>{index + 1}</span></div>')

        # timelineIcon: show icon in the badge position instead of a number
        if variant == "timelineIcon":
            icon_cls = "ri-checkbox-blank-circle-fill"  # default fallback
            if item.icon:
                icon_cls = item.icon.alt
                if not icon_cls.startswith("ri-"):
                    icon_cls = f"ri-{icon_cls}-line"
            html_parts.append(
                f'<div class="card-number timeline-icon-badge"><i class="{self._escape(icon_cls)}"></i></div>'
            )

        # Auto-Icon Selection for specific variants (if icon absent or needs override)
        # Skip timeline families (except timelineIcon) and comparison base variant.
        # These use dedicated dot/axis/number treatments.
        ICON_SKIP_VARIANTS = {
            "timeline",
            "timelineHorizontal",
            "timelineSequential",
            "timelineMilestone",
            "comparison",
            "relationshipMap",
        }
        icon_class = None
        if variant not in ICON_SKIP_VARIANTS:
            if item.icon:
                icon_class = str(item.icon.alt or "").strip()
                if icon_class:
                    if not icon_class.startswith("ri-"):
                        icon_class = f"ri-{icon_class}-line"
                    elif not (icon_class.endswith("-line") or icon_class.endswith("-fill")):
                        # Special cases like ri-github-fill or ri-number-1
                        # Most concepts need -line or -fill. 
                        # If it's a concept (not a number/brand that usually exists as-is), add -line
                        concept_bases = ["brain", "pencil", "link", "shield", "star", "heart"]
                        if any(b in icon_class for b in concept_bases) or not any(c.isdigit() for c in icon_class[-2:]):
                             icon_class = f"{icon_class}-line"
            elif variant == "solidBoxesWithIconsInside":
                default_icons = [
                    "ri-lightbulb-line",
                    "ri-compass-3-line",
                    "ri-flag-2-line",
                    "ri-book-open-line",
                    "ri-shield-check-line",
                    "ri-line-chart-line",
                ]
                icon_class = default_icons[index % len(default_icons)]
            elif variant == "bulletCheck":
                icon_class = "ri-check-line"
            elif variant == "bulletCross":
                icon_class = "ri-close-line"
            elif variant == "comparisonProsCons":
                icon_class = "ri-check-line" if index == 0 else "ri-close-line"

        if icon_class:
            # Diagnostic Log
            print(f"   [RENDER] Item Icon: {icon_class} (variant: {variant})")
            html_parts.append(
                f'<div class="card-icon"><i class="{self._escape(icon_class)}"></i></div>'
            )

        # Content
        html_parts.append('<div class="card-content">')

        if variant == "timeline":
            if item.year:
                html_parts.append(
                    f'<div class="card-year">{self._escape(item.year)}</div>'
                )
            if item.description:
                html_parts.append(
                    f'<p class="card-text">{self._escape(item.description)}</p>'
                )

        elif variant == "stats":
            if item.value:
                html_parts.append(
                    f'<div class="card-value">{self._escape(item.value)}</div>'
                )
            if item.label:
                html_parts.append(
                    f'<div class="card-label">{self._escape(item.label)}</div>'
                )

        else:
            title = item.heading or item.label
            if title:
                html_parts.append(f'<h4 class="card-title">{self._escape(title)}</h4>')

            # Render points as a proper list or structured grid
            if item.points:
                # HEURISTIC: Check for Dimension-centric format: ["Subject: Value", ...]
                is_dim_centric = all(":" in str(p) for p in item.points) and len(item.points) > 0
                
                if is_dim_centric:
                    dim_html = []
                    for p in item.points:
                        parts = str(p).split(":", 1)
                        sub = parts[0].strip()
                        val = parts[1].strip()
                        dim_html.append(
                            f'<div class="card-comparison-row">'
                            f'<span class="card-comparison-subject">{self._escape(sub)}</span>'
                            f'<span class="card-comparison-value">{self._escape(val)}</span>'
                            f'</div>'
                        )
                    html_parts.append(f'<div class="card-comparison-grid">{"".join(dim_html)}</div>')
                else:
                    points_html = "".join(
                        f"<li>{self._escape(p)}</li>" for p in item.points
                    )
                    html_parts.append(f'<ul class="card-list">{points_html}</ul>')
            elif item.description:
                # Handle multiline descriptions (fallback)
                desc_html = self._escape(item.description).replace("\n", "<br>")
                html_parts.append(f'<p class="card-text">{desc_html}</p>')

        html_parts.append("</div>")

        if variant == "relationshipMap" and index < 2:
            connector_icon = "ri-arrow-right-line"
            if item.icon:
                connector_icon = item.icon.alt
                if not connector_icon.startswith("ri-"):
                    connector_icon = f"ri-{connector_icon}-line"
            html_parts.append(
                f'<div class="relationship-connector"><i class="{self._escape(connector_icon)}"></i></div>'
            )

        html_parts.append("</div>")

        return "\n".join(html_parts)

    def _render_comparison_table(self, table: GyMLComparisonTable) -> str:
        """Render comparison table as a clean, refined HTML table."""
        html_parts = ['<div class="comparison-table-wrapper">']
        
        if table.caption:
            html_parts.append(
                f'<h3 class="comparison-table-title">{self._escape(table.caption)}</h3>'
            )

        html_parts.append('<div class="comparison-table-scroll-container">')
        html_parts.append('<table class="refined-comparison-table">')
        
        # Headers
        if table.headers:
            html_parts.append('<thead><tr>')
            for header in table.headers:
                html_parts.append(f'<th>{self._escape(header)}</th>')
            html_parts.append('</tr></thead>')
            
        # Body rows
        if table.rows:
            html_parts.append('<tbody>')
            for row in table.rows:
                html_parts.append('<tr>')
                # Guarantee matching column count
                headers_list = table.headers
                col_count = len(headers_list) if headers_list else len(row)
                for col_idx in range(col_count):
                    # Manual indexing to avoid list(row) confusion
                    cell_val = ""
                    row_list = [str(x) for x in row]
                    if col_idx < len(row_list):
                        cell_val = self._escape(row_list[col_idx])
                    html_parts.append(f'<td>{cell_val}</td>')
                html_parts.append('</tr>')
            html_parts.append('</tbody>')
            
        html_parts.append('</table>')
        html_parts.append('</div>')
        html_parts.append('</div>')
        
        return "\n".join(html_parts)

    def _render_sequential_output(self, node: GyMLSequentialOutput) -> str:
        """Render sequential output block (terminal style)."""
        items_html = []
        for i, item in enumerate(node.items):
            anim_attrs = ""
            anim_class = ""
            if self.animated:
                seg = self._segment_counter
                self._segment_counter += 1
                anim_attrs = f' data-segment="{seg}"'
                anim_class = " anim-typewriter"
            
            items_html.append(
                f'<div class="output-line{anim_class}"{anim_attrs}>'
                f'<span class="prompt-symbol">></span>'
                f'<span class="line-text">{self._escape(item)}</span>'
                f'</div>'
            )
        return f'<div class="sequential-output-container">{"".join(items_html)}</div>'

    def _render_key_value_list(self, kv_list: GyMLKeyValueList) -> str:
        """Render key-value list."""
        items_html = []
        for item in kv_list.items:
            key = self._escape(item.key)
            val = self._escape(item.value)
            items_html.append(
                f'<div class="kv-item">'
                f'<span class="kv-key">{key}</span>'
                f'<span class="kv-value">{val}</span>'
                f"</div>"
            )
        return f'<div class="key-value-list">{"".join(items_html)}</div>'

    def _render_rich_text(self, rich_text: GyMLRichText) -> str:
        """Render rich text block."""
        paragraphs_html = "".join(
            f"<p>{self._escape(p)}</p>" for p in rich_text.paragraphs
        )
        return f'<div class="rich-text-block">{paragraphs_html}</div>'

    def _render_numbered_list(self, num_list: GyMLNumberedList) -> str:
        """Render numbered list."""
        items_html = []
        for item in num_list.items:
            title = self._escape(item.title)
            desc = self._escape(item.description)
            items_html.append(
                f"<li>"
                f'<div class="item-content">'
                f'<div class="item-title">{title}</div>'
                f'<div class="item-desc">{desc}</div>'
                f"</div>"
                f"</li>"
            )
        return f'<ol class="numbered-list">{"".join(items_html)}</ol>'

    def _render_labeled_diagram(self, diagram: GyMLLabeledDiagram) -> str:
        """Render labeled diagram."""
        labels_html = []
        for label in diagram.labels:
            x = label.x
            y = label.y
            text = self._escape(label.text)
            labels_html.append(
                f'<div class="diagram-label" style="left: {x}%; top: {y}%;">'
                f'<span class="label-dot"></span>'
                f'<span class="label-text">{text}</span>'
                f"</div>"
            )
        img_url = self._escape(diagram.image_url) if diagram.image_url else ""
        return (
            f'<div class="labeled-diagram-container">'
            f'<img src="{img_url}" class="diagram-base" />'
            f'<div class="diagram-labels">{"".join(labels_html)}</div>'
            f"</div>"
        )

    def _render_hierarchy_tree(self, tree: GyMLHierarchyTree) -> str:
        """Render hierarchy tree."""

        def render_nested(node):
            label = self._escape(node.label)
            children = node.children
            child_html = ""
            if children:
                child_items = "".join(f"<li>{render_nested(c)}</li>" for c in children)
                child_html = f"<ul>{child_items}</ul>"
            return f'<div class="tree-node">{label}</div>{child_html}'

        return f'<div class="hierarchy-tree-container">{render_nested(tree.root)}</div>'

    def _render_split_panel(self, panel: GyMLSplitPanel) -> str:
        """Render split panel."""
        left_html = self._render_embedded_panel(panel.left_panel)
        right_html = self._render_embedded_panel(panel.right_panel)

        return (
            f'<div class="split-panel">'
            f'<div class="panel-half left">{left_html}</div>'
            f'<div class="panel-half right">{right_html}</div>'
            f"</div>"
        )

    def _render_embedded_panel(self, panel_data: Any) -> str:
        """Helper to render a panel in a split panel."""
        title = self._escape(panel_data.title)
        content = self._escape(panel_data.content).replace("\n", "<br>")
        return f'<div class="embedded-panel"><h3>{title}</h3><p>{content}</p></div>'

    def _render_embedded_block(self, block_data: Dict[str, Any]) -> str:
        """Helper to render a block inside another block (like split panel)."""
        from .serializer import GyMLSerializer
        from .definitions import ComposedBlock

        s = GyMLSerializer()
        composed = ComposedBlock(
            type=block_data.get("type", "paragraph"),
            content=block_data.get("content", block_data),
        )
        node = s._serialize_block(composed)
        rendered = self._render_node(node) if node else ""
        return str(rendered) if rendered else ""

    def _render_formula_block(self, block: GyMLFormulaBlock) -> str:
        """Render formula block."""
        expression = self._escape(block.expression)
        example = self._escape(block.example) if block.example else ""

        vars_html = []
        for var in block.variables:
            vars_html.append(
                f'<div class="formula-var">'
                f'<span class="var-name">{self._escape(var.name)}</span>'
                f'<span class="var-def">{self._escape(var.definition)}</span>'
                f"</div>"
            )

        return (
            f'<div class="formula-block-container">'
            f'<div class="formula-display">$${expression}$$</div>'
            f'<div class="formula-example">{example}</div>'
            f'<div class="formula-variables">{"".join(vars_html)}</div>'
            f"</div>"
        )

    def _render_hub_and_spoke(self, node: "GyMLHubAndSpoke") -> str:
        """Render hub and spoke visualization."""
        hub_label = self._escape(node.hub_label)
        items_html = []
        blue_palette = ["#1e3a8a", "#2563eb", "#3b82f6", "#60a5fa", "#93c5fd"]
        for i, item in enumerate(node.items):
            label = self._escape(item.label)
            icon_html = ""
            if item.icon:
                icon_class = item.icon
                if not icon_class.startswith("ri-"):
                    icon_class = f"ri-{icon_class}-line"
                icon_html = f'<i class="{self._escape(icon_class)}"></i>'

            color = item.color or blue_palette[i % len(blue_palette)]
            style = f' style="--item-color: {color};"'
            desc_html = ""
            if item.description:
                anim_attrs = ""
                anim_class = ""
                if self.animated:
                    seg = self._segment_counter
                    self._segment_counter += 1
                    anim_attrs = f' data-segment="{seg}"'
                    anim_class = " anim-fade"
                desc_html = f'<div class="spoke-info-box{anim_class}"{anim_attrs}><p>{self._escape(item.description)}</p></div>'

            items_html.append(
                f'<div class="spoke-item" data-index="{i}"{style}>'
                f'<div class="hexagon">'
                f'<div class="hexagon-inner">'
                f"{icon_html}"
                f'<span class="spoke-label">{label}</span>'
                f"</div>"
                f"</div>"
                f"{desc_html}"
                f"</div>"
            )

        return (
            f'<div class="hub-and-spoke-container" data-variant="{node.variant}" data-item-count="{len(node.items)}">'
            f'<div class="hub-center">'
            f'<div class="hub-circle">'
            f'<span class="hub-label">{hub_label}</span>'
            f"</div>"
            f"</div>"
            f'<div class="hub-connection-line"></div>'
            f'<div class="spokes-wrapper">'
            f'{"".join(items_html)}'
            f"</div>"
            f"</div>"
        )

    def _render_cyclic_block(self, node: "GyMLCyclicBlock") -> str:
        """Render cyclic block as a blue-hue interlocking wheel with support cards."""
        import math

        n = len(node.items)
        if n < 2:
            n = 2

        cx, cy = 250, 250
        R_outer = 180
        R_inner = 75
        R_icon = (R_outer + R_inner) / 2
        viewbox_size = 500

        DEFAULT_SECTOR_COLOR = "#10233f"
        DEFAULT_STROKE = "#1d3f6e"
        blue_palette = [
            "#2563eb",
            "#3b82f6",
            "#1d4ed8",
            "#0ea5e9",
            "#1e40af",
            "#38bdf8",
        ]

        def polar(cx, cy, r, angle_deg):
            a = math.radians(angle_deg)
            return cx + r * math.cos(a), cy + r * math.sin(a)

        def chevron_arc_path(cx, cy, R_out, R_in, start_deg, sweep, chevron_deg=8.0):
            R_mid = (R_out + R_in) / 2
            end_deg = start_deg + sweep
            ox1, oy1 = polar(cx, cy, R_out, start_deg)
            ox2, oy2 = polar(cx, cy, R_out, end_deg)
            tx, ty = polar(cx, cy, R_mid, end_deg + chevron_deg)
            ix1, iy1 = polar(cx, cy, R_in, end_deg)
            ix2, iy2 = polar(cx, cy, R_in, start_deg)
            nx, ny = polar(cx, cy, R_mid, start_deg + chevron_deg)
            large = 1 if sweep > 180 else 0

            d = f"M {ox1:.3f},{oy1:.3f}"
            d += f" A {R_out},{R_out} 0 {large},1 {ox2:.3f},{oy2:.3f}"
            d += f" L {tx:.3f},{ty:.3f}"
            d += f" L {ix1:.3f},{iy1:.3f}"
            d += f" A {R_in},{R_in} 0 {large},0 {ix2:.3f},{iy2:.3f}"
            d += f" L {nx:.3f},{ny:.3f}"
            d += " Z"
            return d

        gap_deg = 4.0
        n_val = float(max(1, n))
        sweep_deg = (360.0 / n_val) - gap_deg
        chevron_deg = 10.0

        svg_parts = [
            f'<svg class="cyclic-svg" viewBox="0 0 {viewbox_size} {viewbox_size}" '
            f'xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">'
        ]
        svg_parts.append("<defs></defs>")

        for i, item in enumerate(node.items):
            start_angle = -90.0 + float(i) * (360.0 / n_val)
            mid_angle = start_angle + sweep_deg / 2.0
            color = blue_palette[i % len(blue_palette)]
            path_d = chevron_arc_path(cx, cy, R_outer, R_inner, start_angle, sweep_deg, chevron_deg=chevron_deg)
            svg_parts.append(
                f'<path d="{path_d}" fill="{color}" stroke="{DEFAULT_STROKE}" '
                f'stroke-width="1.5" stroke-linejoin="round"/>'
            )
            if item.icon:
                icon_class = item.icon
                if not icon_class.startswith("ri-"):
                    icon_class = f"ri-{icon_class}-line"
                ix, iy = polar(cx, cy, R_icon, mid_angle)
                svg_parts.append(
                    f'<foreignObject x="{ix-16:.1f}" y="{iy-16:.1f}" width="32" height="32">'
                    f'<div xmlns="http://www.w3.org/1999/xhtml" style="width:100%;height:100%;display:flex;align-items:center;justify-content:center;">'
                    f'<i class="{self._escape(icon_class)}" style="font-size:1.2rem;color:rgba(255,255,255,0.85);"></i>'
                    f"</div>"
                    f"</foreignObject>"
                )

        hub_text = self._escape(node.hub_label) if node.hub_label else ""
        if hub_text:
            svg_parts.append(
                f'<circle cx="{cx}" cy="{cy}" r="{R_inner - 6}" '
                f'fill="{DEFAULT_SECTOR_COLOR}" stroke="{DEFAULT_STROKE}" stroke-width="3"/>'
                f'<text x="{cx}" y="{cy}" text-anchor="middle" dominant-baseline="middle" '
                f'font-size="16" font-weight="800" fill="white" font-family="Inter,sans-serif" letter-spacing="-0.5">'
                f"{hub_text}</text>"
            )
        else:
            svg_parts.append(
                f'<circle cx="{cx}" cy="{cy}" r="{R_inner - 6}" '
                f'fill="{DEFAULT_SECTOR_COLOR}" stroke="{DEFAULT_STROKE}" stroke-width="3"/>'
            )

        svg_parts.append("</svg>")
        svg_html = "\n".join(svg_parts)

        def build_card_html(item, i: int, extra_classes=None, style: str = "") -> str:
            anim_attrs = ""
            anim_class = ""
            if self.animated and item.description:
                seg = self._segment_counter
                self._segment_counter += 1
                anim_attrs = f' data-segment="{seg}"'
                anim_class = " anim-fade"

            label_html = f'<strong class="cyclic-ib-title">{self._escape(item.label)}</strong>'
            desc_html = ""
            if item.description:
                desc_html = f'<p class="cyclic-ib-text">{self._escape(item.description)}</p>'

            icon_html = ""
            effective_icon = item.icon or "ri-checkbox-circle-line"
            if effective_icon:
                icon_class_card = effective_icon
                if not icon_class_card.startswith("ri-"):
                    icon_class_card = f"ri-{icon_class_card}-line"
                icon_html = (
                    f'<div class="cyclic-ib-icon" aria-hidden="true">'
                    f'<i class="{self._escape(icon_class_card)}"></i>'
                    f"</div>"
                )

            color = blue_palette[i % len(blue_palette)]
            class_names = ["cyclic-info-box"]
            if extra_classes:
                class_names.extend(extra_classes)
            final_style = f"{style}--item-color:{color};"
            return (
                f'<div class="{" ".join(class_names)}{anim_class}"{anim_attrs} style="{final_style}">'
                f"  {icon_html}"
                f"  {label_html}{desc_html}"
                f"</div>"
            )

        if n == 6:
            orbital_positions = [
                "left: 50%; top: 8%; transform: translate(-50%, 0%); ",
                "right: 8%; top: 23%; ",
                "right: 8%; bottom: 23%; ",
                "left: 50%; bottom: 8%; transform: translate(-50%, 0%); ",
                "left: 8%; bottom: 23%; ",
                "left: 8%; top: 23%; ",
            ]
            orbital_cards = "".join(
                build_card_html(
                    node.items[i],
                    i,
                    ["cyclic-info-box--orbital", f"cyclic-info-box--orbital-{i + 1}"],
                    orbital_positions[i],
                )
                for i in range(6)
            )
            return (
                f'<div class="cyclic-container cyclic-container--orbital" data-variant="{node.variant}" data-item-count="{n}">'
                f'  <div class="cyclic-orbital-stage">'
                f'    <div class="cyclic-wheel-area"><div class="cyclic-svg-wrapper">{svg_html}</div></div>'
                f'    <div class="cyclic-floating-cards">{orbital_cards}</div>'
                f'  </div>'
                f"</div>"
            )

        if n >= 5:
            right_indices = list(range((n + 1) // 2))
            left_indices = list(range(n - 1, (n + 1) // 2 - 1, -1))
            left_cards = "".join(build_card_html(node.items[idx], idx, ["cyclic-info-box--landscape"]) for idx in left_indices)
            right_cards = "".join(build_card_html(node.items[idx], idx, ["cyclic-info-box--landscape"]) for idx in right_indices)
            return (
                f'<div class="cyclic-container cyclic-container--balanced" data-variant="{node.variant}" data-item-count="{n}">'
                f'  <div class="cyclic-main-row">'
                f'    <div class="cyclic-col cyclic-col--left">{left_cards}</div>'
                f'    <div class="cyclic-wheel-area"><div class="cyclic-svg-wrapper">{svg_html}</div></div>'
                f'    <div class="cyclic-col cyclic-col--right">{right_cards}</div>'
                f'  </div>'
                f"</div>"
            )

        floating_cards = []
        R_cards = 235
        if n == 4:
            R_cards = 245

        for i, item in enumerate(node.items):
            start_angle = -90.0 + float(i) * (360.0 / n_val)
            mid_angle_deg = (start_angle + sweep_deg / 2.0) % 360.0
            mid_angle_rad = math.radians(mid_angle_deg)
            pos_x = 50 + (R_cards / 500 * 100) * math.cos(mid_angle_rad)
            pos_y = 50 + (R_cards / 500 * 100) * math.sin(mid_angle_rad)
            tx = -50 - 50 * math.cos(mid_angle_rad)
            ty = -50 - 50 * math.sin(mid_angle_rad)
            card_style = (
                f'left:{pos_x:.1f}%; top:{pos_y:.1f}%; '
                f'transform: translate({tx}%, {ty}%); '
            )
            floating_cards.append(build_card_html(item, i, None, card_style))

        return (
            f'<div class="cyclic-container" data-variant="{node.variant}" data-item-count="{n}">'
            f'  <div class="cyclic-wheel-area">'
            f'    <div class="cyclic-svg-wrapper">{svg_html}</div>'
            f'    <div class="cyclic-floating-cards">{"".join(floating_cards)}</div>'
            f'  </div>'
            f"</div>"
        )

    def _render_process_arrow_block(self, node: GyMLProcessArrowBlock) -> str:
        """Render minimalist interlocking process arrow block using CSS clip-paths."""
        n = len(node.items)
        items_html = []

        blue_palette = ["#1e3a8a", "#2563eb", "#3b82f6", "#60a5fa", "#93c5fd"]
        for i, item in enumerate(node.items):
            color = item.color or blue_palette[i % len(blue_palette)]
            image_url = item.image_url

            # Minimalist Image Card
            if not image_url or image_url == "null":
                image_html = f'<div class="pa-img-minimal placeholder" style="--item-color: {color}"><i class="ri-image-line"></i></div>'
            else:
                image_html = f'<div class="pa-img-minimal"><img src="{self._escape(image_url)}" alt="{self._escape(item.label)}" /></div>'

            is_first = i == 0
            is_last = i == (n - 1)
            item_class = "pa-col-min"
            if is_first:
                item_class += " is-first"
            if is_last:
                item_class += " is-last"

            label = self._escape(item.label)
            desc_html = ""
            if item.description:
                desc_html = (
                    f'<div class="pa-desc-min">{self._escape(item.description)}</div>'
                )

            anim_attrs = ""
            anim_class = ""
            if self.animated:
                seg = self._segment_counter
                self._segment_counter += 1
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

    def _render_cyclic_process_block(self, node: GyMLCyclicProcessBlock) -> str:
        """Render cyclic process with circles and a single SVG overlay for sweeping arc arrows."""
        n = len(node.items)
        items_html = []

        for i, item in enumerate(node.items):
            label = self._escape(item.label)
            desc = self._escape(item.description or "")
            img_url = item.image_url

            if not img_url or img_url == "null":
                img_html = f'<div class="cp-circle-placeholder"><i class="ri-image-line"></i></div>'
            else:
                img_html = f'<img src="{self._escape(img_url)}" alt="{label}" />'

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
        import math

        circle_d = 240
        gap_px = 15
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
            ex_pt = cx_i + cr  # right midpoint (3 o'clock)
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
            defs_html.append(
                f'<marker id="cp-head-{i}" markerWidth="10" markerHeight="8" '
                f'refX="8" refY="4" orient="auto">'
                f'<polygon points="0 0, 10 4, 0 8" fill="#555" />'
                f"</marker>"
            )
            # Filled dot at start point
            paths_html.append(
                f'<circle cx="{sx:.1f}" cy="{sy:.1f}" r="6" fill="#555" />'
            )
            # The arc path
            paths_html.append(
                f'<path d="{d}" fill="none" stroke="#555" '
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

    def _render_feature_showcase(self, node: GyMLFeatureShowcaseBlock) -> str:
        """Render feature showcase with radial connectors and supporting cards."""
        import math

        n = len(node.items)
        title = self._escape(node.title)
        default_colors = [
            "#3b82f6",
            "#8b5cf6",
            "#10b981",
            "#f59e0b",
            "#06b6d4",
            "#ec4899",
            "#14b8a6",
            "#ef4444",
        ]

        W, H = 1100, 700
        cx, cy = W / 2, H / 2
        R_center = 148
        R_orbit = 268
        r_icon = 40
        connector_gap = 68
        icon_fill = "#3b82f6"

        if n == 1:
            angles = [180]
        elif n == 2:
            angles = [140, 400]
        elif n == 3:
            angles = [130, 250, 410]
        else:
            start_deg = 140
            end_deg = 400
            step = (end_deg - start_deg) / (n - 1)
            angles = [start_deg + i * step for i in range(n)]

        def polar(angle_deg, radius):
            a = math.radians(angle_deg)
            return cx + radius * math.cos(a), cy + radius * math.sin(a)

        svg_parts = [
            f'<svg class="fs-radial-svg" viewBox="0 0 {W} {H}" '
            f'xmlns="http://www.w3.org/2000/svg" '
            f'xmlns:xlink="http://www.w3.org/1999/xlink">'
        ]
        svg_parts.append(
            f'<circle cx="{cx}" cy="{cy}" r="{R_center}" '
            f'fill="none" stroke="rgba(99,102,241,0.08)" stroke-width="16" />'
        )

        items_html = []
        for i, item in enumerate(node.items):
            angle = angles[i]
            color = item.color or default_colors[i % len(default_colors)]
            label = self._escape(item.label)
            description = self._escape(item.description) if item.description else ""
            ix, iy = polar(angle, R_orbit)
            lx1, ly1 = polar(angle, R_center + 2)

            svg_parts.append(
                f'<line x1="{lx1:.1f}" y1="{ly1:.1f}" x2="{ix:.1f}" y2="{iy:.1f}" '
                f'stroke="{icon_fill}" stroke-width="2" stroke-opacity="0.35" />'
            )
            svg_parts.append(
                f'<circle cx="{ix:.1f}" cy="{iy:.1f}" r="{r_icon}" fill="{icon_fill}" />'
            )

            icon_class = "ri-checkbox-blank-circle-fill"
            if item.icon:
                icon_class = item.icon
                if not icon_class.startswith("ri-"):
                    icon_class = f"ri-{icon_class}-line"

            svg_parts.append(
                f'<foreignObject x="{ix - r_icon:.1f}" y="{iy - r_icon:.1f}" width="{r_icon * 2}" height="{r_icon * 2}">'
                f'<div xmlns="http://www.w3.org/1999/xhtml" style="width:100%;height:100%;display:flex;align-items:center;justify-content:center;">'
                f'<i class="{self._escape(icon_class)}" style="font-size:1.6rem;color:white;"></i>'
                f"</div></foreignObject>"
            )

            norm_angle = angle % 360
            is_left = 90 < norm_angle < 270
            lbl_end_x = ix - connector_gap if is_left else ix + connector_gap
            lbl_y = iy

            svg_parts.append(
                f'<line x1="{ix:.1f}" y1="{iy:.1f}" x2="{lbl_end_x:.1f}" y2="{lbl_y:.1f}" '
                f'stroke="{icon_fill}" stroke-width="1.5" stroke-opacity="0.4" />'
            )
            svg_parts.append(
                f'<circle cx="{lbl_end_x:.1f}" cy="{lbl_y:.1f}" r="3" fill="{icon_fill}" fill-opacity="0.5" />'
            )

            x_pct = (lbl_end_x / W) * 100
            y_pct = (iy / H) * 100
            side = "left" if is_left else "right"

            anim_attrs = ""
            anim_class = ""
            if self.animated:
                seg = self._segment_counter
                self._segment_counter += 1
                anim_attrs = f' data-segment="{seg}"'
                anim_class = " anim-fade"

            desc_html = f'<div class="fs-card-desc">{description}</div>' if description else ""
            items_html.append(
                f'<div class="fs-info-card fs-info-card--{side}{anim_class}"{anim_attrs} '
                f'style="left:{x_pct:.2f}%;top:{y_pct:.2f}%;--item-color:{color};">'
                f'<div class="fs-card-content">'
                f'<div class="fs-card-title">{label}</div>'
                f"{desc_html}"
                f"</div>"
                f"</div>"
            )

        svg_parts.append("</svg>")

        if node.image_url and node.image_url != "null":
            center_html = (
                f'<div class="fs-hub-img">'
                f'<img src="{self._escape(node.image_url)}" alt="{title}" />'
                f"</div>"
            )
        else:
            center_html = (
                f'<div class="fs-hub-img fs-hub-placeholder">'
                f'<i class="ri-user-line"></i>'
                f"</div>"
            )

        bottom_label = f'<div class="fs-bottom-label"><span>{title}</span></div>'

        return (
            f'<div class="fs-radial-container fs-radial-container--spacious" data-item-count="{n}">'
            f'{"".join(svg_parts)}'
            f"{center_html}"
            f'{"".join(items_html)}'
            f"{bottom_label}"
            f"</div>"
        )

    def _escape(self, text: str) -> str:
        """Escape HTML special characters."""
        if not text:
            return ""
        return html.escape(str(text))

    def _get_gamma_styles(self) -> str:
        """Get Gamma-style CSS."""
        return """
/* ================================================
   GAMMA-STYLE SLIDE DESIGN
   Clean, professional, light theme
   Viewport-fitted (no scrolling)
   ================================================ */

*, *::before, *::after {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

html, body {
    height: 100%;
    margin: 0;
    padding: 0;
}

body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: var(--bg-primary, #f8f7f4);
    color: var(--text-primary, #1a1a1a);
    line-height: 1.5;
    -webkit-font-smoothing: antialiased;
}

:root {
    --bg-primary: #0b1121;
    --bg-secondary: #0f172a;
    --text-primary: #f8fafc;
    --text-secondary: rgba(255, 255, 255, 0.7);
    --accent: #4f46e5;
    
    /* Single source of truth for content padding (applied ONLY on .body). */
    /* Use responsive padding by default; allow per-slide overrides via --section-padding. */
    --slide-content-padding: var(
        --section-padding,
        clamp(1.5rem, 3.2vh, 2.75rem) clamp(1.75rem, 3vw, 3.25rem)
    );
}

/* Deck Container - Full viewport with snap scrolling */
.gyml-deck {
    width: 100%;
    height: 100vh;
    max-width: 100%;
    margin: 0;
    padding: 0;
    overflow-y: auto; /* Enable vertical scrolling */
    overflow-x: hidden;
    scroll-snap-type: y mandatory; /* Enable snap scrolling */
    scrollbar-width: none;
    -ms-overflow-style: none;
}

/* Chrome/Safari: Hide scrollbar */
.gyml-deck::-webkit-scrollbar {
    display: none;
}

/* ================================================
   PROCESS ARROW BLOCK (Minimalist Interlocking)
   ================================================ */
.pa-container-min {
    display: flex;
    flex-direction: row;
    width: 100%;
    max-width: 1200px;
    margin: 0.5rem auto;
    gap: 0;
    padding: 1rem;
    align-items: flex-start;
}

.pa-col-min {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    position: relative;
    padding: 0 5px; /* Spacing between columns for images/text */
}

/* Image styling - non overlapping */
.pa-img-minimal {
    width: 100%;
    aspect-ratio: 1 / 1;
    border-radius: 12px;
    overflow: hidden;
    margin-bottom: 20px;
    background: #f8f9fa;
    border: 1px solid rgba(0,0,0,0.05);
    display: flex;
    align-items: center;
    justify-content: center;
    transition: transform 0.3s ease;
}

.pa-img-minimal img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

.pa-img-minimal.placeholder {
    color: var(--item-color);
    font-size: 2.5rem;
    opacity: 0.4;
}

.pa-col-min:hover .pa-img-minimal {
    transform: translateY(-5px);
}

/* Arrow styling - interlocking via negative margin on the arrow wrapper only */
.pa-arrow-min {
    width: calc(100% + 20px); /* Extend to reach next column */
    height: 54px;
    background: var(--item-color);
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 1rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    position: relative;
    z-index: 1;
    margin-left: -10px; /* Pull left to interlock */
    margin-right: -10px; /* Pull right to interlock */
    
    /* Default Interlocking Shape (Notch left, Point right) */
    clip-path: polygon(0 0, calc(100% - 15px) 0, 100% 50%, calc(100% - 15px) 100%, 0 100%, 15px 50%);
}

.pa-col-min.is-first .pa-arrow-min {
    margin-left: 0;
    width: calc(100% + 10px);
    /* No notch on left */
    clip-path: polygon(0 0, calc(100% - 15px) 0, 100% 50%, calc(100% - 15px) 100%, 0 100%);
}

.pa-col-min.is-last .pa-arrow-min {
    margin-right: 0;
    width: calc(100% + 10px);
    /* No point on right */
    clip-path: polygon(0 0, 100% 0, 100% 100%, 0 100%, 15px 50%);
}

.pa-arrow-min span {
    padding: 0 20px;
    text-align: center;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

/* Description styling */
.pa-desc-min {
    margin-top: 15px;
    font-size: 0.95rem;
    color: #4b5563;
    text-align: center;
    line-height: 1.5;
    padding: 0 10px;
}

/* Responsive adjustment */
@media (max-width: 800px) {
    .pa-container-min {
        flex-direction: column;
        gap: 3rem;
    }
    .pa-col-min {
        width: 100%;
        padding: 0;
    }
    .pa-arrow-min {
        width: 100% !important;
        margin: 0 !important;
        clip-path: polygon(0 0, 100% 0, 100% 100%, 0 100%) !important;
        border-radius: 8px;
    }
}

/* ================================================
   FEATURE SHOWCASE BLOCK (Radial Arc Layout)
   ================================================ */
.fs-radial-container {
    position: relative;
    width: 100%;
    margin: 0 auto;
    aspect-ratio: 1100 / 700;
}

.fs-radial-container--spacious {
    max-width: 1320px;
    max-height: 590px;
}

/* SVG layer (connectors, icon circles) */
.fs-radial-svg {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    z-index: 1;
}

/* Central hub image */
.fs-hub-img {
    position: absolute;
    left: 50%;
    top: 50%;
    transform: translate(-50%, -50%);
    width: 240px;
    height: 240px;
    border-radius: 50%;
    overflow: hidden;
    background: linear-gradient(135deg, #e0e7ff 0%, #c7d2fe 100%);
    border: 4px solid rgba(99, 102, 241, 0.12);
    box-shadow: 0 8px 32px rgba(99, 102, 241, 0.15),
                0 0 0 10px rgba(99, 102, 241, 0.04);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 3;
    transition: transform 0.3s ease;
}

.fs-radial-container--spacious .fs-hub-img {
    width: 24.5%;
    height: auto;
    aspect-ratio: 1 / 1;
}

.fs-hub-img:hover {
    transform: translate(-50%, -50%) scale(1.04);
}

.fs-hub-img img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

.fs-hub-placeholder {
    background: linear-gradient(135deg, #e0e7ff 0%, #ddd6fe 100%);
}

.fs-hub-placeholder i {
    font-size: 4.5rem;
    color: rgba(99, 102, 241, 0.35);
}

.fs-bottom-label {
    position: absolute;
    bottom: 2%;
    left: 50%;
    transform: translateX(-50%);
    z-index: 4;
}

.fs-bottom-label span {
    display: inline-block;
    font-size: 0.9rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: var(--text-primary, #1e293b);
    padding: 0.4rem 1.5rem;
    background: var(--bg-secondary, #fff);
    border: 2px solid rgba(0,0,0,0.1);
    border-radius: 999px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}

.fs-radial-container--spacious .fs-bottom-label span {
    font-size: 0.95rem;
    padding: 0.55rem 1.9rem;
}

.fs-info-card {
    position: absolute;
    z-index: 4;
    cursor: default;
    width: 200px;
    --fs-connector-gap: 0px;
}

.fs-radial-container--spacious .fs-info-card {
    width: 238px;
}

.fs-info-card--left {
    transform: translateX(calc(-66% + var(--fs-connector-gap))) translateY(-50%);
    transition: transform 0.2s ease;
}

.fs-info-card--left:hover {
    transform: translateX(calc(-66% + var(--fs-connector-gap))) translateY(-50%) scale(1.03);
}

.fs-info-card--right {
    transform: translateX(calc(-34% - var(--fs-connector-gap))) translateY(-50%);
    transition: transform 0.2s ease;
}

.fs-info-card--right:hover {
    transform: translateX(calc(-34% - var(--fs-connector-gap))) translateY(-50%) scale(1.03);
}

section[data-animated="true"] .fs-info-card--left.anim-fade.active {
    transform: translateX(calc(-66% + var(--fs-connector-gap))) translateY(-50%) !important;
}

section[data-animated="true"] .fs-info-card--right.anim-fade.active {
    transform: translateX(calc(-34% - var(--fs-connector-gap))) translateY(-50%) !important;
}

.fs-card-content {
    display: flex;
    flex-direction: column;
    gap: 0.3rem;
    padding: 0.7rem 0.9rem;
    border: 2px solid color-mix(in srgb, var(--item-color, #6366f1) 30%, transparent);
    border-radius: 10px;
    background: rgba(255, 255, 255, 0.97);
    backdrop-filter: blur(8px);
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
    transition: all 0.2s ease;
    position: relative;
}

.fs-radial-container--spacious .fs-card-content {
    gap: 0.4rem;
    padding: 0.9rem 1.1rem;
    border-radius: 12px;
}

.fs-info-card:hover .fs-card-content {
    border-color: var(--item-color, #6366f1);
    background: white;
    box-shadow: 0 6px 24px rgba(0, 0, 0, 0.12);
}

.fs-info-card--left .fs-card-content::before {
    content: '';
    position: absolute;
    right: -10px;
    top: 50%;
    transform: translateY(-50%);
    width: 0;
    height: 0;
    border-top: 8px solid transparent;
    border-bottom: 8px solid transparent;
    border-left: 9px solid color-mix(in srgb, var(--item-color, #6366f1) 30%, transparent);
}

.fs-info-card--left .fs-card-content::after {
    content: '';
    position: absolute;
    right: -8px;
    top: 50%;
    transform: translateY(-50%);
    width: 0;
    height: 0;
    border-top: 7px solid transparent;
    border-bottom: 7px solid transparent;
    border-left: 8px solid rgba(255, 255, 255, 0.97);
    filter: drop-shadow(2px 0 2px rgba(0, 0, 0, 0.04));
}

.fs-info-card--right .fs-card-content::before {
    content: '';
    position: absolute;
    left: -10px;
    top: 50%;
    transform: translateY(-50%);
    width: 0;
    height: 0;
    border-top: 8px solid transparent;
    border-bottom: 8px solid transparent;
    border-right: 9px solid color-mix(in srgb, var(--item-color, #6366f1) 30%, transparent);
}

.fs-info-card--right .fs-card-content::after {
    content: '';
    position: absolute;
    left: -8px;
    top: 50%;
    transform: translateY(-50%);
    width: 0;
    height: 0;
    border-top: 7px solid transparent;
    border-bottom: 7px solid transparent;
    border-right: 8px solid rgba(255, 255, 255, 0.97);
    filter: drop-shadow(-2px 0 2px rgba(0, 0, 0, 0.04));
}

.fs-card-title {
    font-size: 0.85rem;
    font-weight: 800;
    color: #0f172a;
    line-height: 1.2;
}

.fs-radial-container--spacious .fs-card-title {
    font-size: 1rem;
}

.fs-card-desc {
    font-size: 0.7rem;
    color: #475569;
    line-height: 1.4;
    white-space: normal;
}

.fs-radial-container--spacious .fs-card-desc {
    font-size: 0.82rem;
}

@media (max-width: 700px) {
    .fs-radial-container {
        aspect-ratio: unset;
        padding: 2rem 1rem;
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 1rem;
    }
    .fs-radial-svg {
        display: none;
    }
    .fs-hub-img {
        position: static;
        transform: none;
        width: 130px;
        height: 130px;
    }
    .fs-hub-img:hover {
        transform: scale(1.04);
    }
    .fs-info-card,
    .fs-info-card--left,
    .fs-info-card--right {
        position: static !important;
        transform: none !important;
        width: min(100%, 320px);
    }
    .fs-bottom-label {
        position: static;
        transform: none;
        margin-top: 0.5rem;
    }
}


/* ================================================
   CYCLIC PROCESS BLOCK
   ================================================ */
.cyclic-process-container {
    position: relative;
    width: 100%;
    margin: 0 auto;
    padding: 1.5rem;
    display: flex;
    flex-direction: column;
    align-items: center;
}

.cp-items-row {
    display: flex;
    flex-direction: row;
    justify-content: center;
    align-items: flex-start;
    position: relative;
    z-index: 2;
}

.cp-item {
    flex: 0 0 240px;
    display: flex;
    flex-direction: column;
    align-items: center;
    min-width: 0;
}

.cp-circle {
    box-sizing: border-box;
    width: 100%;
    max-width: 240px;
    height: auto;
    aspect-ratio: 1 / 1;
    border-radius: 50%;
    border: 3px solid #ddd;
    background: #fff;
    padding: 12px;
    overflow: hidden;
    box-shadow: 0 4px 16px rgba(0,0,0,0.06);
    flex-shrink: 1;
}

.cp-circle img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    border-radius: 50%;
}

.cp-circle-placeholder {
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 3rem;
    color: #888;
    opacity: 0.25;
}

/* SVG arrow overlay — positioned over the circle row */
.cp-arrows-overlay {
    position: absolute;
    top: 1.5rem;
    left: 50%;
    transform: translateX(-50%);
    height: 240px;
    overflow: visible;
    pointer-events: none;
    z-index: 3;
}

.cp-info {
    text-align: center;
    padding: 1.25rem 0.5rem 0;
}

.cp-label {
    font-weight: 700;
    font-size: 1.1rem;
    margin-bottom: 0.5rem;
    color: var(--text-primary, #111827);
    text-transform: uppercase;
    letter-spacing: 0.3px;
}

.cp-description {
    font-size: 0.95rem;
    line-height: 1.55;
    color: var(--text-secondary, #4b5563);
}

@media (max-width: 900px) {
    .cp-items-row {
        flex-direction: column;
        align-items: center;
        gap: 3rem;
    }
    .cp-arrows-overlay {
        display: none;
    }
}


/* ================================================
   SECTION - Full Viewport Slide
   ================================================ */

section {
    position: relative;
    width: 100%;
    height: 100vh;
    /* Section never has padding — all padding lives on .body. */
    padding: 0;
    background: radial-gradient(circle at 2% 2%, rgba(56, 189, 248, 0.1) 0%, transparent 45%),
                radial-gradient(circle at 98% 98%, rgba(79, 70, 229, 0.1) 0%, transparent 45%),
                #0b1121;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    scroll-snap-align: start; /* Snap target */
    flex-shrink: 0;           /* Prevent shrinking */
}

/* Precise Digital Grid Overlay - Hoisted to top layer for visibility */
section::after {
    content: "";
    position: absolute;
    inset: 0;
    background-image: linear-gradient(rgba(255, 255, 255, 0.015) 1px, transparent 1px),
                      linear-gradient(90deg, rgba(255, 255, 255, 0.015) 1px, transparent 1px);
    background-size: 60px 60px;
    pointer-events: none;
    z-index: 100;
}

/* Explicitly disable grid for full-image background slides to keep them clean */
section[data-image-layout="behind"]::after {
    display: none;
}

/* ... image layouts ... */
section[data-image-layout="right"] {
    display: grid;
    grid-template-columns: 1fr var(--accent-width, 500px);
    gap: 0;
    align-items: stretch;
}
section[data-image-layout="right"] .body { 
    order: 1; 
    grid-column: 1; 
    padding: var(--slide-content-padding);
    padding-right: 0;
    margin-right: var(--block-gap, 3rem);
}
section[data-image-layout="right"] .accent-image-wrapper,
section[data-image-layout="right"] .accent-image-placeholder,
section[data-image-layout="right"] .accent-image-group { 
    order: 2; 
    grid-column: 2; 
    width: 100%;
    height: 100%;
}

section[data-image-layout="left"] {
    display: grid;
    grid-template-columns: var(--accent-width, 500px) 1fr;
    gap: 0;
    align-items: stretch;
}
section[data-image-layout="left"] .body { 
    order: 2; 
    grid-column: 2; 
    padding: var(--slide-content-padding);
    padding-left: 0;
    margin-left: var(--block-gap, 3rem);
}
section[data-image-layout="left"] .accent-image-wrapper,
section[data-image-layout="left"] .accent-image-placeholder,
section[data-image-layout="left"] .accent-image-group { 
    order: 1; 
    grid-column: 1; 
    width: 100%;
    height: 100%;
}

section[data-image-layout="right-wide"] {
    display: grid;
    grid-template-columns: 1fr 500px;
    gap: 0;
    align-items: stretch;
}
section[data-image-layout="right-wide"] .body { 
    order: 1; 
    grid-column: 1; 
    padding: var(--slide-content-padding);
    padding-right: 0;
    margin-right: var(--block-gap, 3rem);
}
section[data-image-layout="right-wide"] .accent-image-wrapper,
section[data-image-layout="right-wide"] .accent-image-placeholder,
section[data-image-layout="right-wide"] .accent-image-group { 
    order: 2; 
    grid-column: 2; 
    width: 100%;
    height: 100%;
}

/* If the planner chose a side layout but no image exists, fall back to normal padded layout. */
section[data-image-layout="right"][data-has-image="false"],
section[data-image-layout="left"][data-has-image="false"],
section[data-image-layout="right-wide"][data-has-image="false"] {
    display: flex !important;
    flex-direction: column !important;
    gap: 0 !important;
}
section[data-image-layout="right"][data-has-image="false"] .body,
section[data-image-layout="left"][data-has-image="false"] .body,
section[data-image-layout="right-wide"][data-has-image="false"] .body {
    order: 0 !important;
    grid-column: auto !important;
    padding: var(--slide-content-padding) !important;
    margin: 0 !important;
}

/* Top / Bottom Layouts (Vertical Stacking) */
section[data-image-layout="top"] {
    display: flex;
    flex-direction: column;
    gap: 0;
}
section[data-image-layout="top"] .accent-image-wrapper,
section[data-image-layout="bottom"] .accent-image-wrapper {
    position: relative;
}
section[data-image-layout="top"] .accent-image-wrapper::after,
section[data-image-layout="bottom"] .accent-image-wrapper::after {
    content: "";
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.4);
    pointer-events: none;
    z-index: 1;
}

section[data-image-layout="bottom"] {
    display: flex;
    flex-direction: column;
    gap: 0;
}

section[data-image-layout="top"] .accent-image-group,
section[data-image-layout="top"] .accent-image-wrapper,
section[data-image-layout="top"] .accent-image-placeholder,
section[data-image-layout="bottom"] .accent-image-group,
section[data-image-layout="bottom"] .accent-image-wrapper,
section[data-image-layout="bottom"] .accent-image-placeholder {
    width: 100% !important;
    height: 220px !important; /* Reduced to save vertical space */
    min-height: 0 !important;   /* Kill the global min-height */
    aspect-ratio: auto !important; /* Allow the height to take precedence */
    margin: 0;
    flex-shrink: 0;
}

section[data-image-layout="top"] .body {
    flex: 1;
    position: relative; /* Required for z-index */
    padding: var(--slide-content-padding);
    margin-top: -100px; /* Overlap adjusted for shorter image */
    z-index: 10;
    /* Smooth gradient from transparent to solid dark background */
    background: linear-gradient(to bottom, transparent 0%, rgba(13, 27, 42, 0.9) 60px, var(--bg-color, #0d1b2a) 100px);
}
section[data-image-layout="bottom"] .body {
    flex: 1;
    position: relative; /* Required for z-index */
    padding: var(--slide-content-padding);
    margin-bottom: -100px; /* Overlap adjusted for shorter image */
    z-index: 10;
    background: linear-gradient(to top, transparent 0%, rgba(13, 27, 42, 0.9) 60px, var(--bg-color, #0d1b2a) 100px);
}

/* If top/bottom was chosen but no image exists, behave like a normal padded slide. */
section[data-image-layout="top"][data-has-image="false"],
section[data-image-layout="bottom"][data-has-image="false"] {
    gap: 0 !important;
}
section[data-image-layout="top"][data-has-image="false"] .body,
section[data-image-layout="bottom"][data-has-image="false"] .body {
    position: static !important;
    padding: var(--slide-content-padding) !important;
    margin: 0 !important;
    background: transparent !important;
}

/* --- Aggressive Compacting for Super Dense Slides --- */
section[data-density="super_dense"] {
    --section-padding: 1rem 1.5rem !important;
    --block-gap: 0.25rem !important;
}

section[data-density="super_dense"] h1 { font-size: 1.8rem !important; margin-bottom: 0.15rem; }

/* Preserve large title for relationshipMap even in dense mode */
section:has(.smart-layout[data-variant="relationshipMap"]) h1 {
    font-size: calc(var(--h1-size, 2.25rem) + 0.2rem) !important;
}
section[data-density="super_dense"] h2 { font-size: 1.5rem !important; margin-bottom: 0.15rem; }
section[data-density="super_dense"] p { font-size: 0.95rem !important; line-height: 1.4; }

section[data-density="super_dense"] .body {
    justify-content: center;
}

section[data-density="super_dense"] .hub-and-spoke-container {
    margin-top: 5px;
    margin-bottom: 5px;
}

section[data-density="super_dense"] .spokes-wrapper {
    width: 380px;
    height: 380px;
}

section[data-density="super_dense"] .hexagon {
    transform: scale(0.8);
}

section[data-density="super_dense"] .spoke-item {
    width: 100px;
    height: 120px;
}

section[data-density="super_dense"] .cyclic-container {
    min-height: 500px;
}

section[data-density="super_dense"] .cyclic-svg-wrapper {
    width: 400px;
    height: 400px;
}

section[data-density="super_dense"] .cyclic-container[data-item-count="6"] .cyclic-wheel-area {
    width: min(760px, 96vw);
    height: min(760px, 96vw);
}

section[data-density="super_dense"] .cyclic-container[data-item-count="6"] .cyclic-info-box {
    width: min(300px, 31vw);
    min-height: 104px;
    padding: 0.8rem 1rem 0.9rem;
    border-radius: 18px;
}

section[data-density="super_dense"] .cyclic-container[data-item-count="6"] .cyclic-ib-title {
    font-size: 0.9rem;
}

section[data-density="super_dense"] .cyclic-container[data-item-count="6"] .cyclic-ib-text {
    font-size: 0.82rem;
    line-height: 1.38;
}

section[data-density="super_dense"] .cyclic-container[data-item-count="6"] .cyclic-info-box--six {
    display: block;
    text-align: left;
}

section[data-density="super_dense"] .cyclic-container[data-item-count="6"] .cyclic-info-box--six-1,
section[data-density="super_dense"] .cyclic-container[data-item-count="6"] .cyclic-info-box--six-2,
section[data-density="super_dense"] .cyclic-container[data-item-count="6"] .cyclic-info-box--six-4,
section[data-density="super_dense"] .cyclic-container[data-item-count="6"] .cyclic-info-box--six-5 {
    width: min(280px, 29vw);
}

section[data-density="super_dense"] .cyclic-container[data-item-count="6"] .cyclic-info-box--six-3,
section[data-density="super_dense"] .cyclic-container[data-item-count="6"] .cyclic-info-box--six-6 {
    width: min(250px, 27vw);
}

section[data-density="super_dense"] .cyclic-container[data-item-count="6"] .cyclic-info-box--six .cyclic-ib-icon {
    float: left;
    margin: 0.1rem 0.8rem 0.35rem 0;
}

section[data-density="super_dense"] .cyclic-container[data-item-count="6"] .cyclic-info-box--six .cyclic-ib-title {
    margin-bottom: 0.2rem;
    line-height: 1.25;
}

section[data-density="super_dense"] .cyclic-container[data-item-count="6"] .cyclic-info-box--six .cyclic-ib-text {
    display: -webkit-box;
    -webkit-box-orient: vertical;
    -webkit-line-clamp: 4;
    overflow: hidden;
}

section[data-density="super_dense"] .fs-radial-container {
    transform: scale(0.85);
    margin: -20px 0;
}

section[data-density="super_dense"][data-image-layout="top"] .accent-image-wrapper,
section[data-density="super_dense"][data-image-layout="bottom"] .accent-image-wrapper {
    height: 160px !important;
}

/* Behind Layout (Hero/Background) */
section[data-image-layout="behind"] {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    text-align: center;
    --slide-content-padding: 4rem;
}

section[data-image-layout="behind"] .accent-image-group,
section[data-image-layout="behind"] .accent-image-wrapper,
section[data-image-layout="behind"] .accent-image-placeholder {
    position: absolute;
    inset: 0;
    width: 100% !important;
    height: 100% !important;
    z-index: 1;
}

section[data-image-layout="behind"] .accent-image-group::after {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(to bottom, rgba(0,0,0,0.2), rgba(0,0,0,0.7));
    z-index: 2;
}

section[data-image-layout="behind"] .body {
    position: relative;
    z-index: 10;
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    padding: var(--slide-content-padding);
    color: white !important;
}

section[data-image-layout="behind"] .body h1,
section[data-image-layout="behind"] .body h2,
section[data-image-layout="behind"] .body p {
    color: white !important;
    text-shadow: 0 2px 10px rgba(0,0,0,0.5);
}

/* Adjust aspect ratios and heights for vertical layouts */
section[data-image-layout="top"] .accent-image-placeholder,
section[data-image-layout="bottom"] .accent-image-placeholder {
    aspect-ratio: 16 / 9;
    width: 100%;
    height: 100%;
    max-height: 100%;
    border-radius: 0;
}

section[data-image-layout="left"] .accent-image-placeholder,
section[data-image-layout="right"] .accent-image-placeholder,
section[data-image-layout="right-wide"] .accent-image-placeholder {
    aspect-ratio: 9 / 16;
    width: 100%;
    max-height: 80vh;
}

section[data-image-layout="top"] .accent-image-wrapper img,
section[data-image-layout="bottom"] .accent-image-wrapper img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    object-position: center;
    border-radius: 0;
}

section[data-image-layout="left"] .accent-image-wrapper img,
section[data-image-layout="right"] .accent-image-wrapper img,
section[data-image-layout="right-wide"] .accent-image-wrapper img {
    width: 100%;
    height: 100%;
    max-height: 100vh;
    object-fit: cover;
    border-radius: 0;
}

/* Accent Image + Annotation Group */
.accent-image-group {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    align-self: center;
}

.accent-image-group .accent-image-wrapper {
    flex: 1;
}

.image-annotation {
    font-size: var(--p-size, 1.15rem);
    line-height: 1.5;
    padding: 0.75rem 1rem;
    margin: 0.5rem 0;
}

/* ... */

.body {
    flex: 1 1 0;
    height: 100%;
    align-self: stretch;
    display: flex;
    flex-direction: column;
    min-width: 0; /* Prevent overflow in grid/flex layouts */
    gap: var(--block-gap, 0.75rem);
    padding: var(--slide-content-padding);
    overflow-y: auto;
    overflow-x: hidden;
    scrollbar-width: none; /* Firefox */
    -ms-overflow-style: none; /* IE/Edge */
    /* Vertical centering: equal whitespace above/below when content is short.
       "safe center" prevents top clipping if content overflows. */
    justify-content: center;
    min-height: 0;
}

/* Chrome/Safari: Hide scrollbar for body content */
.body::-webkit-scrollbar {
    display: none;
}

/* ================================================
   TYPOGRAPHY - Clean & Professional
   ================================================ */

h1 {
    font-size: calc(var(--h1-size, 2.25rem) + 0.2rem);
    font-weight: 800;
    line-height: 1.25;
    letter-spacing: -0.03em;
    color: #D0E4FF;
    margin-bottom: var(--heading-gap, 0.5rem);
    position: relative;
    padding-bottom: 0.75rem;
    display: inline-block;
}

h1::after {
    content: "";
    position: absolute;
    bottom: 0;
    left: 0;
    width: 120px;
    height: 4px;
    background: linear-gradient(90deg, #D0E4FF, #2E6BC4, transparent);
    border-radius: 2px;
}

h2 {
    font-size: calc(var(--h2-size, 2rem) + 0.15rem);
    font-weight: 700;
    line-height: 1.2;
    letter-spacing: -0.02em;
    color: var(--text-primary, #1a1a1a);
    margin-bottom: var(--heading-gap, 0.1rem);
}

h3 {
    font-size: var(--h3-size, 1.5rem);
    font-weight: 600;
    color: var(--text-primary, #1a1a1a);
}

h4 {
    font-size: var(--h4-size, 1.125rem);
    font-weight: 600;
    color: var(--text-primary, #1a1a1a);
    line-height: 1.3;
}

p {
    font-size: var(--p-size, 1.125rem);
    line-height: var(--line-height, 1.7);
    color: var(--text-secondary, #4a4a4a);
}

.p-intro, .p-context {
    font-size: calc(var(--h1-size, 2.25rem) * 0.5);
    font-weight: 500;
    line-height: normal;
}

.p-intro {
    color: var(--text-primary, #1a1a1a);
    margin-bottom: 0.4rem;
    line-height: 1.55;
    border-left: 3px solid color-mix(in srgb, var(--accent, #4f46e5) 55%, transparent);
    padding-left: 0.85rem;
}

.p-context {
    font-style: italic;
    color: var(--text-tertiary, #666);
    opacity: 0.95;
    /* Keep context/subtitle clearly subordinate to the main title */
    font-size: calc(var(--h1-size, 2.25rem) * 0.5);
    line-height: 1.55;
    background: color-mix(in srgb, var(--bg-secondary, #f8fafc) 78%, transparent);
    border: 1px dashed color-mix(in srgb, var(--border-color, #d1d5db) 85%, transparent);
    border-radius: 0.75rem;
    padding: 0.6rem 0.85rem;
}

.p-annotation {
    position: relative;
    font-size: calc(var(--p-size) * 0.95);
    font-style: italic;
    color: #8AAFDB;
    background: rgba(20, 60, 110, 0.25);
    padding: 0.85rem 1.25rem;
    border-radius: 8px;
    margin: 1.2rem 0;
    border: 1px solid rgba(100, 170, 230, 0.2);
    border-left: 3px solid #2E6BC4;
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
}

/* Accent bar is now handled by border-left on the container */
.p-annotation::before {
    display: none;
}

.p-annotation::after {
    content: "•";
    position: absolute;
    left: 0.45rem;
    top: 0.2rem;
    color: color-mix(in srgb, var(--accent, #64748b) 65%, transparent);
    font-size: 0.6rem;
    font-weight: bold;
}

.p-annotation.p-with-icon::before,
.p-annotation.p-with-icon::after {
    content: none;
}

.p-callout {
    font-size: calc(var(--p-size) * 1.05);
    font-weight: 500;
    color: var(--text-primary, #1f2937);
    background: linear-gradient(135deg, color-mix(in srgb, var(--accent, #f97316) 12%, #fff7ed) 0%, color-mix(in srgb, var(--accent, #f97316) 5%, white) 100%);
    border: 1px solid color-mix(in srgb, var(--accent, #f97316) 35%, #fed7aa);
    border-left: 4px solid color-mix(in srgb, var(--accent, #f97316) 75%, #f97316);
    border-radius: 0.6rem;
    padding: 0.9rem 1rem;
    margin: 0.6rem 0;
}

.p-takeaway {
    font-size: calc(var(--p-size) * 1.08);
    font-weight: 600;
    color: var(--text-primary, #0f172a);
    background: linear-gradient(180deg, color-mix(in srgb, var(--accent, #2563eb) 8%, white) 0%, color-mix(in srgb, var(--accent, #2563eb) 5%, #f0f9ff) 100%);
    border: 1px solid color-mix(in srgb, var(--accent, #2563eb) 32%, #bfdbfe);
    border-radius: 0.6rem;
    padding: 0.95rem 1rem;
    position: relative;
    margin: 0.7rem 0;
}

.p-takeaway::after {
    content: "";
    position: absolute;
    bottom: -1px;
    left: 0;
    right: 0;
    height: 3px;
    background: color-mix(in srgb, var(--accent, #2563eb) 65%, transparent);
    border-radius: 0 0 0.6rem 0.6rem;
}

.p-outro {
    font-weight: 500;
    font-size: calc(var(--p-size) * 1.04);
    color: var(--text-secondary, #4b5563);
    background: linear-gradient(180deg, color-mix(in srgb, var(--text-secondary, #4b5563) 8%, transparent) 0%, transparent 100%);
    padding-top: 0.75rem;
    padding-bottom: 0rem;
    margin-top: 1rem;
    border-top: 1px solid color-mix(in srgb, var(--text-secondary, #4b5563) 15%, transparent);
}

.p-caption {
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: color-mix(in srgb, var(--text-tertiary, #888) 85%, #888);
    text-align: center;
    margin-top: 0.8rem;
    margin-bottom: 0.4rem;
    line-height: 1.2;
}

/* Icon layout utilities */
.p-with-icon {
    display: flex;
    align-items: flex-start;
    gap: 0.6rem;
}

.p-icon {
    flex: 0 0 auto;
    font-size: 1rem;
    opacity: 0.82;
}

.p-text {
    flex: 1 1 auto;
    min-width: 0;
}

/* ================================================
   COLUMNS
   ================================================ */

.columns {
    display: flex;
    gap: 2rem;
    width: 100%;
}

/* Comparison Layout Overrides — Maximize horizontal room */
.comparison-layout .body {
    padding: var(--slide-content-padding);
    padding-right: 0;
    padding-left: 1.5rem;
    max-width: none !important;
}

.comparison-layout[data-image-layout="right"] .body {
    padding-right: 0;
}

.column {
    display: flex;
    flex-direction: column;
    gap: 1rem;
}

/* ================================================
   SMART LAYOUT - Gamma Card Grid
   ================================================ */


.smart-layout {
    display: grid;
    gap: var(--card-gap, 1.25rem);
    width: 100%;
}

.smart-layout[data-item-count="2"] {
    grid-template-columns: repeat(2, 1fr);
}

.smart-layout[data-item-count="3"] {
    grid-template-columns: repeat(3, 1fr);
}

.smart-layout[data-item-count="4"] {
    grid-template-columns: repeat(2, 1fr);
}

.smart-layout[data-item-count="5"],
.smart-layout[data-item-count="6"] {
    grid-template-columns: repeat(3, 1fr);
}

/* ================================================
   CARD - Gamma Style
   ================================================ */

.card {
    display: flex;
    flex-direction: column;
    padding: var(--card-padding, 1.5rem);
    background: var(--bg-secondary, #ffffff);
    border: 1px solid var(--border-color, #e5e5e5);
    border-radius: var(--card-radius, 0.5rem);
    box-shadow: var(--card-shadow, none);
    transition: box-shadow 0.2s ease;
}

.block-separator {
    width: 100%;
    height: 1px;
    background: #b0b0b0;
    margin: 0.25rem 0;
}

.card:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

/* Card Number - Gamma style top badge */
.card-number {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 100%;
    padding: 0.75rem;
    margin: -1.5rem -1.5rem 1.25rem -1.5rem;
    width: calc(100% + 3rem);
    background: var(--number-bg, #f0f0f0);
    font-size: var(--card-number-size, 1.125rem);
    font-weight: 600;
    color: var(--text-secondary, #666);
    border-bottom: 1px solid var(--border-color, #e5e5e5);
    border-radius: 4px 4px 0 0;
}

/* Card Icon */
.card-icon {
    width: 3rem;
    height: 3rem;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--icon-bg, #1a1a1a);
    border-radius: 50%;
    margin-bottom: 1rem;
}

.card-icon i {
    font-size: 1.25rem;
    color: #ffffff;
}

/* Card Content */
.card-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
}

.card-title {
    font-size: 1.25rem;
    font-weight: 600;
    color: var(--text-primary, #1a1a1a);
    margin: 0;
    line-height: 1.4;
}

.card-text {
    font-size: var(--card-text-size, var(--p-size, 1.125rem));
    line-height: var(--line-height, 1.65);
    color: var(--text-secondary, #555);
    margin: 0;
}

/* ================================================
   NEW CONTENT TYPES STYLES
   ================================================ */

/* Comparison Table (Refined Table Layout - Dark Mode Compatible) */
.comparison-table-wrapper {
    width: 100%;
    margin: 1.5rem 0;
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
}

.comparison-table-title {
    margin: 0;
    font-size: 1.75rem;
    font-weight: 800;
    color: var(--text-primary, #ffffff);
    text-align: left;
    letter-spacing: -0.02em;
}

.comparison-table-scroll-container {
    width: 100%;
    overflow-x: auto;
    border-radius: 12px;
    background: var(--bg-secondary, #0f172a); /* Dark slate background */
    border: 1px solid rgba(255, 255, 255, 0.1);
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
}

.comparison-table-scroll-container::-webkit-scrollbar {
    height: 6px;
}
.comparison-table-scroll-container::-webkit-scrollbar-track {
    background: transparent;
}
.comparison-table-scroll-container::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 10px;
}

/* Base table styles */
.refined-comparison-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 1rem;
    background: transparent;
    table-layout: fixed;
    min-width: 600px;
}

.refined-comparison-table th, 
.refined-comparison-table td {
    border: 1px solid rgba(255, 255, 255, 0.08); /* Subtle dark borders */
    padding: 1.5rem 1.25rem;
    text-align: left;
    vertical-align: top;
    line-height: 1.6;
}

.refined-comparison-table th {
    font-weight: 700;
    color: #94a3b8; /* Muted headers */
    background: rgba(255, 255, 255, 0.03);
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.refined-comparison-table td {
    color: #e2e8f0; /* Bright but soft white text */
    font-weight: 400;
}

.refined-comparison-table tr:hover td {
    background: rgba(255, 255, 255, 0.02);
}

/* Dimension-centric Card Styles */
.card-comparison-grid {
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
    margin-top: 0.5rem;
}

.card-comparison-row {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    gap: 0.5rem;
    padding-bottom: 0.25rem;
    border-bottom: 1px solid var(--border-color, rgba(255, 255, 255, 0.05));
}

.card-comparison-row:last-child {
    border-bottom: none;
}

.card-comparison-subject {
    font-size: 0.65rem;
    font-weight: 700;
    text-transform: uppercase;
    color: var(--text-secondary, #94a3b8);
    letter-spacing: 0.05em;
    flex-shrink: 0;
}

.card-comparison-value {
    font-size: 0.9rem;
    color: var(--text-primary, #f8fafc);
    text-align: right;
    line-height: 1.25;
}

/* Light mode overrides if the user ever switches */
:root:not([class~="dark"]) .comparison-table-scroll-container {
    background: #ffffff;
    border: 1px solid #e2e8f0;
}
:root:not([class~="dark"]) .refined-comparison-table td {
    color: #1e293b;
    border-color: #e2e8f0;
}
:root:not([class~="dark"]) .refined-comparison-table th {
    background: #f8fafc;
    color: #64748b;
}

/* Key-Value List */
.key-value-list {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
}
.kv-item {
    display: flex;
    justify-content: space-between;
    padding: 0.75rem;
    background: #f8f9fa;
    border-radius: 6px;
    border-left: 4px solid var(--accent, #1a1a1a);
}
.kv-key {
    font-weight: 700;
}

/* Formula Block */
.formula-block-container {
    padding: 2rem;
    background: #1a1a1a;
    color: #fff;
    border-radius: 12px;
    text-align: center;
    margin: 1.5rem 0;
}
.formula-display {
    font-family: 'Cambria Math', 'Times New Roman', serif;
    font-size: 2.5rem;
    margin-bottom: 1rem;
}
.formula-example {
    font-size: 1.125rem;
    font-style: italic;
    opacity: 0.8;
    margin-bottom: 1.5rem;
}
.formula-variables {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 1rem;
    border-top: 1px solid #444;
    padding-top: 1rem;
}
.formula-var {
    text-align: left;
}
.var-name {
    font-weight: 700;
    margin-right: 0.5rem;
    color: #ffd700;
}
.var-def {
    opacity: 0.9;
}

/* Split Panel */
.split-panel {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 2rem;
    height: 100%;
}
.panel-half {
    display: flex;
    flex-direction: column;
    justify-content: center;
}

/* Labeled Diagram */
.labeled-diagram-container {
    position: relative;
    width: 100%;
    max-height: 60vh;
    overflow: hidden;
    border-radius: 12px;
}
.diagram-base {
    width: 100%;
    height: auto;
    display: block;
}
.diagram-label {
    position: absolute;
    transform: translate(-50%, -50%);
    display: flex;
    flex-direction: column;
    align-items: center;
}
.label-dot {
    width: 12px;
    height: 12px;
    background: #ff4757;
    border-radius: 50%;
    border: 2px solid #fff;
    box-shadow: 0 0 10px rgba(0,0,0,0.3);
}
.label-text {
    background: rgba(255,255,255,0.9);
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 700;
    margin-top: 4px;
    white-space: nowrap;
}

/* Rich Text */
.rich-text-block {
    line-height: 1.8;
}

/* Hierarchy Tree */
.hierarchy-tree-container {
    padding: 1.5rem;
    background: var(--bg-secondary, #ffffff);
}

.hierarchy-tree-container ul {
    list-style: none;
    padding-left: 2rem;
    position: relative;
    margin-top: 0.5rem;
}

.hierarchy-tree-container ul::before {
    content: '';
    position: absolute;
    left: 0.75rem;
    top: 0;
    bottom: 1.5rem;
    width: 2px;
    background: #e5e7eb;
}

.hierarchy-tree-container li {
    position: relative;
    padding-bottom: 0.75rem;
}

.hierarchy-tree-container li::before {
    content: '';
    position: absolute;
    left: -1.25rem;
    top: 1.25rem;
    width: 1rem;
    height: 2px;
    background: #e5e7eb;
}

.tree-node {
    padding: 0.75rem 1.25rem;
    background: #fff;
    border: 1.5px solid #eef2f6;
    border-radius: 8px;
    display: inline-block;
    font-weight: 600;
    color: var(--text-primary, #1a1a1a);
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
    transition: transform 0.2s ease;
}

.tree-node:hover {
    transform: translateY(-2px);
    border-color: var(--accent, #6366f1);
}

/* Numbered List - Premium Style */
.numbered-list {
    list-style: none;
    counter-reset: slide-counter;
    display: flex;
    flex-direction: column;
    gap: 1.25rem;
    margin: 1rem 0;
}

.numbered-list li {
    counter-increment: slide-counter;
    display: flex;
    gap: 1.25rem;
    align-items: flex-start;
    padding: 1rem;
    background: var(--bg-tertiary, #fafafa);
    border-radius: 12px;
    border: 1px solid #f0f0f0;
}

.numbered-list li::before {
    content: counter(slide-counter);
    width: 2.5rem;
    height: 2.5rem;
    flex-shrink: 0;
    background: var(--accent, #1a1a1a);
    color: #ffffff;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 800;
    font-size: 1.125rem;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

.numbered-list .item-content {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
}

.numbered-list .item-title {
    font-weight: 700;
    color: var(--text-primary, #1a1a1a);
    font-size: 1.1rem;
}

.numbered-list .item-desc {
    color: var(--text-secondary, #4a4a4a);
    font-size: 0.9375rem;
    line-height: 1.6;
}

/* ================================================
   COMPACT OVERRIDES - Dense Slides
   Shrinks card internals that are otherwise hardcoded.
   ================================================ */

section[data-density="super_dense"] .body,
section[data-density="dense"] .body {
    justify-content: center;
}

@supports (justify-content: safe center) {
    section[data-density="super_dense"] .body,
    section[data-density="dense"] .body {
        justify-content: safe center;
    }
}

section[data-density="super_dense"] .card-icon,
section[data-density="dense"] .card-icon {
    width: 2rem;
    height: 2rem;
    margin-bottom: 0.5rem;
}

section[data-density="super_dense"] .card-icon i,
section[data-density="dense"] .card-icon i {
    font-size: 0.9rem;
}

section[data-density="super_dense"] .card-number,
section[data-density="dense"] .card-number {
    padding: 0.375rem;
    margin: -1rem -1rem 0.625rem -1rem;
    width: calc(100% + 2rem);
    font-size: 0.875rem;
}

section[data-density="super_dense"] .card-content,
section[data-density="dense"] .card-content {
    gap: 0.25rem;
}

section[data-density="super_dense"] .card-title,
section[data-density="dense"] .card-title {
    font-size: 0.9375rem;
}

section[data-density="super_dense"] .block-separator,
section[data-density="dense"] .block-separator {
    margin: 0.5rem 0;
}

section[data-density="super_dense"] .p-annotation,
section[data-density="dense"] .p-annotation {
    font-size: calc(var(--p-size) * 1.02);
    padding: 0.5rem 0.625rem;
    margin: 0;
}

section[data-density="super_dense"] .numbered-list,
section[data-density="dense"] .numbered-list {
    gap: 0.75rem;
}

section[data-density="super_dense"] .numbered-list li,
section[data-density="dense"] .numbered-list li {
    padding: 0.75rem;
}

section[data-density="super_dense"] .hierarchy-tree-container,
section[data-density="dense"] .hierarchy-tree-container {
    padding: 1rem;
}

section[data-density="super_dense"] .hierarchy-tree-container ul,
section[data-density="dense"] .hierarchy-tree-container ul {
    margin-top: 0.25rem;
}

section[data-density="dense"] .smart-layout[data-variant="relationshipMap"],
section[data-density="super_dense"] .smart-layout[data-variant="relationshipMap"] {
    gap: 1.5rem;
}

section[data-density="dense"] .smart-layout[data-variant="relationshipMap"] .card,
section[data-density="super_dense"] .smart-layout[data-variant="relationshipMap"] .card {
    min-height: 11.5rem;
    padding: 1.4rem;
}

section[data-density="dense"] .smart-layout[data-variant="relationshipMap"] .card-title,
section[data-density="super_dense"] .smart-layout[data-variant="relationshipMap"] .card-title {
    font-size: 1rem;
}

section[data-density="dense"] .smart-layout[data-variant="relationshipMap"] .card-text,
section[data-density="super_dense"] .smart-layout[data-variant="relationshipMap"] .card-text {
    font-size: 0.84rem;
    line-height: 1.45;
}

/* Dense timeline slides need extra legibility compared to generic dense cards. */
section[data-density="dense"] .smart-layout[data-variant="timeline"],
section[data-density="dense"] .smart-layout[data-variant="timelineSequential"],
section[data-density="dense"] .smart-layout[data-variant="timelineIcon"] {
    gap: 0.5rem;
}

section[data-density="dense"] .smart-layout[data-variant="timeline"] {
    padding-left: 2rem;
}

section[data-density="dense"] .smart-layout[data-variant="timelineSequential"],
section[data-density="dense"] .smart-layout[data-variant="timelineIcon"] {
    padding-left: 2.2rem;
}

section[data-density="dense"] .smart-layout[data-variant="timeline"] .card,
section[data-density="dense"] .smart-layout[data-variant="timelineSequential"] .card,
section[data-density="dense"] .smart-layout[data-variant="timelineIcon"] .card {
    padding: 0.55rem 0;
}

section[data-density="dense"] .smart-layout[data-variant="timeline"] .card-text,
section[data-density="dense"] .smart-layout[data-variant="timelineSequential"] .card-text,
section[data-density="dense"] .smart-layout[data-variant="timelineIcon"] .card-text,
section[data-density="dense"] .smart-layout[data-variant="timelineHorizontal"] .card-text,
section[data-density="dense"] .smart-layout[data-variant="timelineMilestone"] .card-text {
    font-size: 0.98rem;
    line-height: 1.55;
}

section[data-density="dense"] .smart-layout[data-variant="timeline"] .card-title,
section[data-density="dense"] .smart-layout[data-variant="timelineSequential"] .card-title,
section[data-density="dense"] .smart-layout[data-variant="timelineIcon"] .card-title,
section[data-density="dense"] .smart-layout[data-variant="timelineHorizontal"] .card-title,
section[data-density="dense"] .smart-layout[data-variant="timelineMilestone"] .card-title {
    font-size: 1.02rem;
}

section[data-density="dense"] .smart-layout[data-variant="timeline"]::before,
section[data-density="dense"] .smart-layout[data-variant="timelineSequential"]::before,
section[data-density="dense"] .smart-layout[data-variant="timelineIcon"]::before {
    width: 3px;
}

section[data-density="dense"] .smart-layout[data-variant="timeline"] .card::before {
    width: 10px;
    height: 10px;
    left: -1.75rem;
}

section[data-density="dense"] .smart-layout[data-variant="timelineSequential"] .card-number {
    width: 1.65rem;
    height: 1.65rem;
    font-size: 0.78rem;
}

section[data-density="dense"] .smart-layout[data-variant="timelineIcon"] .timeline-icon-badge,
section[data-density="dense"] .smart-layout[data-variant="timelineIcon"] .card-number {
    width: 1.7rem;
    height: 1.7rem;
    font-size: 0.82rem;
}

section[data-density="dense"] .smart-layout[data-variant="timelineHorizontal"] {
    min-height: 340px;
    gap: 0 1.25rem;
}

section[data-density="dense"] .smart-layout[data-variant="timelineHorizontal"] .card {
    padding: 1.2rem;
}

section[data-density="dense"] .smart-layout[data-variant="timelineMilestone"] {
    grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
    gap: 1.75rem;
}

section[data-density="dense"] .smart-layout[data-variant="timelineMilestone"] .card {
    padding: 1.7rem;
}

/* ================================================
   TIMELINE VARIANT (Vertical)
   ================================================ */

.smart-layout[data-variant="timeline"] {
    display: flex;
    flex-direction: column;
    gap: 0;
    position: relative;
    padding-left: 1.75rem;
}

.smart-layout[data-variant="timeline"]::before {
    content: '';
    position: absolute;
    left: 0.45rem;
    top: 0.25rem;
    bottom: 0.25rem;
    width: 2px;
    background: var(--timeline-color, #2d8a6e);
}

.smart-layout[data-variant="timeline"] .card {
    position: relative;
    border: none;
    background: transparent;
    padding: 0.4rem 0;
    border-radius: 0;
}

.smart-layout[data-variant="timeline"] .card::before {
    content: '';
    position: absolute;
    left: -1.55rem;
    top: 0.65rem;
    width: 8px;
    height: 8px;
    background: var(--timeline-color, #2d8a6e);
    border-radius: 50%;
}

/* Primary Item (First) */
.smart-layout[data-variant="timeline"] .card:first-child .card-text {
    color: var(--text-primary, #1a1a1a);
    font-size: 0.95rem;
}

.smart-layout[data-variant="timeline"] .card:first-child::before {
    background: var(--accent, #6366f1);
    width: 10px;
    height: 10px;
    left: -1.6rem;
    box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2);
}

/* Secondary Items (Rest) */
.smart-layout[data-variant="timeline"] .card:not(:first-child) {
    opacity: 0.9;
}

.smart-layout[data-variant="timeline"] .card:not(:first-child) .card-text {
    font-size: 0.875rem;
}

.smart-layout[data-variant="timeline"] .card:not(:first-child)::before {
    top: 0.7rem;
    width: 6px;
    height: 6px;
    left: -1.5rem;
    background: var(--text-tertiary, #a0a0a0);
}

.smart-layout[data-variant="timeline"] .card-number {
    display: none;
}

.card-year {
    font-size: 0.95rem;
    font-weight: 700;
    color: var(--timeline-color, #2d8a6e);
    margin-bottom: 0.2rem;
}

/* ================================================
   TIMELINE HORIZONTAL VARIANT (Alternating)
   ================================================ */

.smart-layout[data-variant="timelineHorizontal"] {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    grid-template-rows: 1fr auto 1fr;
    gap: 0 1rem;
    position: relative;
    min-height: 300px;
}

/* The horizontal line */
.smart-layout[data-variant="timelineHorizontal"]::before {
    content: '';
    position: absolute;
    top: 50%;
    left: 2rem;
    right: 2rem;
    height: 3px;
    background: var(--timeline-color, #2d8a6e);
    transform: translateY(-50%);
    z-index: 1;
}

.smart-layout[data-variant="timelineHorizontal"] .card {
    position: relative;
    border: none;
    background: transparent;
    padding: 1rem;
    border-radius: 0;
    text-align: center;
    display: flex;
    flex-direction: column;
    justify-content: flex-end;
}

/* Odd cards (1, 3) go in top row */
.smart-layout[data-variant="timelineHorizontal"] .card:nth-child(odd) {
    grid-row: 1;
}

/* Even cards (2, 4) go in bottom row */
.smart-layout[data-variant="timelineHorizontal"] .card:nth-child(even) {
    grid-row: 3;
    justify-content: flex-start;
}

/* Position each card in its column */
.smart-layout[data-variant="timelineHorizontal"] .card:nth-child(1) { grid-column: 1; }
.smart-layout[data-variant="timelineHorizontal"] .card:nth-child(2) { grid-column: 2; }
.smart-layout[data-variant="timelineHorizontal"] .card:nth-child(3) { grid-column: 3; }
.smart-layout[data-variant="timelineHorizontal"] .card:nth-child(4) { grid-column: 4; }

/* Dots on the timeline - middle row */
.smart-layout[data-variant="timelineHorizontal"] .card::before {
    content: '';
    position: absolute;
    left: 50%;
    transform: translateX(-50%);
    width: 16px;
    height: 16px;
    background: var(--timeline-color, #2d8a6e);
    border-radius: 50%;
    border: 3px solid var(--bg-secondary, #ffffff);
    z-index: 2;
}

/* Dot position for odd cards (bottom of card) */
.smart-layout[data-variant="timelineHorizontal"] .card:nth-child(odd)::before {
    bottom: -8px;
}

/* Dot position for even cards (top of card) */
.smart-layout[data-variant="timelineHorizontal"] .card:nth-child(even)::before {
    top: -8px;
}

.smart-layout[data-variant="timelineHorizontal"] .card-number {
    display: none;
}

.smart-layout[data-variant="timelineHorizontal"] .card-year {
    text-align: center;
    font-size: 1rem;
    font-weight: 700;
    color: var(--timeline-color, #2d8a6e);
    margin-bottom: 0.5rem;
}

/* ================================================
   TIMELINE SEQUENTIAL VARIANT
   ================================================ */

.smart-layout[data-variant="timelineSequential"] {
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
    position: relative;
    padding-left: 2rem;
}

.smart-layout[data-variant="timelineSequential"]::before {
    content: '';
    position: absolute;
    left: 0.7rem;
    top: 0.5rem;
    bottom: 0.5rem;
    width: 2px;
    background: var(--border-color, #e2e8f0);
    opacity: 0.6;
}

.smart-layout[data-variant="timelineSequential"] .card {
    position: relative;
    border: none;
    background: transparent;
    padding: 0.35rem 0;
    border-radius: 0;
}

.smart-layout[data-variant="timelineSequential"] .card-number {
    position: absolute;
    left: -2rem;
    top: 0.5rem;
    width: 1.4rem;
    height: 1.4rem;
    margin: 0;
    padding: 0;
    background: var(--bg-primary, #ffffff);
    color: var(--accent, #333333);
    border: 2px solid var(--accent, #333333);
    border-radius: 50%;
    font-size: 0.7rem;
    font-weight: 600;
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 2;
    box-shadow: 0 0 0 3px var(--bg-primary, #ffffff);
}

.smart-layout[data-variant="timelineSequential"] .card-title {
    font-size: 0.95rem;
    margin-bottom: 0.1rem;
}

.smart-layout[data-variant="timelineSequential"] .card-text {
    font-size: 0.85rem;
    line-height: 1.45;
}

/* ================================================
   TIMELINE ICON VARIANT (Icons instead of numbers)
   ================================================ */

.smart-layout[data-variant="timelineIcon"] {
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
    position: relative;
    padding-left: 2rem;
}

.smart-layout[data-variant="timelineIcon"]::before {
    content: '';
    position: absolute;
    left: 0.7rem;
    top: 0.5rem;
    bottom: 0.5rem;
    width: 2px;
    background: var(--border-color, #e2e8f0);
    opacity: 0.6;
}

.smart-layout[data-variant="timelineIcon"] .card {
    position: relative;
    border: none;
    background: transparent;
    padding: 0.35rem 0;
    border-radius: 0;
}

.smart-layout[data-variant="timelineIcon"] .card-number,
.smart-layout[data-variant="timelineIcon"] .timeline-icon-badge {
    position: absolute;
    left: -2rem;
    top: 0.4rem;
    width: 1.5rem;
    height: 1.5rem;
    margin: 0;
    padding: 0;
    background: var(--accent, #6366f1);
    color: #ffffff;
    border: none;
    border-radius: 50%;
    font-size: 0.75rem;
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 2;
    box-shadow: 0 0 0 3px var(--bg-primary, #ffffff);
}

.smart-layout[data-variant="timelineIcon"] .card-icon {
    display: none; /* Hide the regular card-icon since we use the badge */
}

.smart-layout[data-variant="timelineIcon"] .card-title {
    font-size: 0.95rem;
    margin-bottom: 0.1rem;
}

.smart-layout[data-variant="timelineIcon"] .card-text {
    font-size: 0.85rem;
    line-height: 1.45;
}

/* ================================================
   TIMELINE MILESTONE VARIANT
   ================================================ */

.smart-layout[data-variant="timelineMilestone"] {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 1.5rem;
    position: relative;
    padding-top: 2.5rem;
}

.smart-layout[data-variant="timelineMilestone"]::before {
    content: '';
    position: absolute;
    top: 0.75rem;
    left: 0;
    right: 0;
    height: 2px;
    background: var(--border-color, #e2e8f0);
}

.smart-layout[data-variant="timelineMilestone"] .card {
    position: relative;
    border: none;
    background: transparent;
    padding: 1.5rem;
    text-align: left;
    background: var(--bg-tertiary, #f8fafc);
    border-radius: 12px;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.smart-layout[data-variant="timelineMilestone"] .card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.03);
}

.smart-layout[data-variant="timelineMilestone"] .card::before {
    content: '';
    position: absolute;
    top: -2.35rem; /* center on the line */
    left: 1.5rem;
    width: 14px;
    height: 14px;
    background: var(--accent, #333333);
    border: 3px solid var(--bg-primary, #ffffff);
    border-radius: 50%;
    z-index: 2;
    box-shadow: 0 0 0 2px var(--border-color, #e2e8f0);
}

.smart-layout[data-variant="timelineMilestone"] .card-number { display: none; }


.smart-layout[data-variant="timelineHorizontal"] .card:nth-child(even) .card-year {
    order: -1;
}

.smart-layout[data-variant="timelineHorizontal"] .card-text {
    font-size: 0.875rem;
    line-height: 1.5;
    color: var(--text-secondary, #555);
}

/* ================================================
   STATS VARIANT (and Stats Comparison/Percentage)
   ================================================ */

.smart-layout[data-variant="stats"] .card,
.smart-layout[data-variant="statsComparison"] .card,
.smart-layout[data-variant="statsPercentage"] .card {
    text-align: center;
    padding: 2.5rem 1.5rem;
    background: var(--bg-secondary, #ffffff);
    border-radius: 16px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.02);
    border: 1px solid var(--border-color, #f1f5f9);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.smart-layout[data-variant="statsComparison"] .card:hover,
.smart-layout[data-variant="statsPercentage"] .card:hover,
.smart-layout[data-variant="stats"] .card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(0,0,0,0.04);
}

.smart-layout[data-variant="stats"] .card-number,
.smart-layout[data-variant="statsComparison"] .card-number,
.smart-layout[data-variant="statsPercentage"] .card-number {
    display: none;
}

.smart-layout[data-variant="statsComparison"] {
    grid-template-columns: 1fr 1fr;
    gap: 2rem;
}
.smart-layout[data-variant="statsComparison"] .card-value {
    font-size: 3.5rem;
    font-weight: 300;
    color: var(--accent, #1e293b);
    line-height: 1;
    margin-bottom: 0.5rem;
}
.smart-layout[data-variant="statsComparison"] .card-label {
    font-size: 0.875rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--text-secondary, #64748b);
    font-weight: 500;
}

.smart-layout[data-variant="statsPercentage"] .card {
    background: radial-gradient(circle at center, var(--bg-secondary, #ffffff) 65%, var(--bg-tertiary, #f8fafc) 100%);
    border-radius: 50%;
    aspect-ratio: 1/1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    border: 1px solid var(--border-color, #e2e8f0);
}


.smart-layout[data-variant="stats"] .card {
    text-align: center;
    padding: 2rem;
}

.smart-layout[data-variant="stats"] .card-number {
    display: none;
}

.card-value {
    font-size: 2.5rem;
    font-weight: 800;
    color: var(--accent, #1a1a1a);
    line-height: 1;
    margin-bottom: 0.5rem;
}

.card-label {
    font-size: 0.8125rem;
    font-weight: 500;
    color: var(--text-secondary, #666);
    text-transform: uppercase;
    letter-spacing: 0.08em;
}

.smart-layout[data-variant="solidBoxesWithIconsInside"] {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: var(--block-gap, 1.25rem);
    width: 100%;
    margin-inline: 0;
    margin-top: 0;
    padding: 0;
    overflow: visible;
    flex: 0 1 auto;
    align-content: flex-start;
}

.smart-layout[data-variant="solidBoxesWithIconsInside"] .card {
    position: relative;
    min-height: 8.8rem;
    padding: 1.25rem 1.15rem 0.9rem;
    border-radius: 1rem;
    border: 1px solid color-mix(in srgb, var(--accent, #38bdf8) 38%, #7a8ea8);
    background: transparent;
    box-shadow: none;
    text-align: left;
    justify-content: flex-start;
    height: 100%;
}

.smart-layout[data-variant="solidBoxesWithIconsInside"] .card::before {
    display: none;
}

.smart-layout[data-variant="solidBoxesWithIconsInside"] .card:hover {
    transform: none;
    box-shadow: none;
}

.smart-layout[data-variant="solidBoxesWithIconsInside"] .card-content {
    gap: 0.55rem;
    align-items: flex-start;
}

.smart-layout[data-variant="solidBoxesWithIconsInside"] .card-icon {
    width: 2.7rem;
    height: 2.7rem;
    margin-bottom: 0.35rem;
    border-radius: 0.78rem;
    background: linear-gradient(to bottom, #1A4B8C, #3B7DD8);
    color: #D0E4FF;
    box-shadow: 0 0 20px rgba(46, 107, 196, 0.25);
}

.smart-layout[data-variant="solidBoxesWithIconsInside"] .card-icon i {
    font-size: 1.15rem;
    color: #D0E4FF;
}

.smart-layout[data-variant="solidBoxesWithIconsInside"] .card-number {
    width: 2.7rem;
    min-height: 2.7rem;
    margin-bottom: 0.45rem;
    border-radius: 0.78rem;
    background: color-mix(in srgb, var(--accent, #38bdf8) 12%, transparent);
    color: color-mix(in srgb, var(--accent, #38bdf8) 82%, #ffffff);
    font-weight: 800;
}

.smart-layout[data-variant="solidBoxesWithIconsInside"] .card-title {
    font-size: 1.35rem;
    line-height: 1.3;
    font-weight: 800;
    color: #f8fbff;
    letter-spacing: -0.02em;
}

.smart-layout[data-variant="solidBoxesWithIconsInside"] .card-text {
    font-size: 0.92rem;
    line-height: 1.55;
    color: color-mix(in srgb, var(--text-secondary, #475569) 82%, #ffffff);
}

.smart-layout[data-variant="solidBoxesWithIconsInside"] .card-icon {
    width: 3rem;
    height: 3rem;
}

.smart-layout[data-variant="solidBoxesWithIconsInside"] .card-icon i {
    font-size: 1.3rem;
}

section[data-density="balanced"] .smart-layout[data-variant="solidBoxesWithIconsInside"],
section[data-density="standard"] .smart-layout[data-variant="solidBoxesWithIconsInside"],
section[data-density="dense"] .smart-layout[data-variant="solidBoxesWithIconsInside"] {
    max-width: none;
}

section[data-image-layout="right"] .smart-layout[data-variant="solidBoxesWithIconsInside"],
section[data-image-layout="left"] .smart-layout[data-variant="solidBoxesWithIconsInside"],
section[data-image-layout="right-wide"] .smart-layout[data-variant="solidBoxesWithIconsInside"] {
    /* With a side image: bento grid inside the text column */
    grid-template-columns: repeat(2, minmax(0, 1fr));
    grid-auto-rows: minmax(6.5rem, auto);
    width: 100%;
    max-width: none;
}

/* No-image (blank layout): keep a stable 3-column grid */
section[data-image-layout="blank"] .smart-layout[data-variant="solidBoxesWithIconsInside"][data-item-count="2"] {
    grid-template-columns: repeat(2, minmax(0, 1fr));
}

section[data-image-layout="blank"] .smart-layout[data-variant="solidBoxesWithIconsInside"][data-item-count="3"],
section[data-image-layout="blank"] .smart-layout[data-variant="solidBoxesWithIconsInside"][data-item-count="4"],
section[data-image-layout="blank"] .smart-layout[data-variant="solidBoxesWithIconsInside"][data-item-count="5"],
section[data-image-layout="blank"] .smart-layout[data-variant="solidBoxesWithIconsInside"][data-item-count="6"] {
    grid-template-columns: repeat(3, minmax(0, 1fr));
}

/* Side-image (left/right): bento rules */
section[data-image-layout="right"] .smart-layout[data-variant="solidBoxesWithIconsInside"] .card,
section[data-image-layout="left"] .smart-layout[data-variant="solidBoxesWithIconsInside"] .card,
section[data-image-layout="right-wide"] .smart-layout[data-variant="solidBoxesWithIconsInside"] .card {
    min-height: 8.8rem;
}

section[data-image-layout="right"] .smart-layout[data-variant="solidBoxesWithIconsInside"][data-item-count="2"],
section[data-image-layout="left"] .smart-layout[data-variant="solidBoxesWithIconsInside"][data-item-count="2"],
section[data-image-layout="right-wide"] .smart-layout[data-variant="solidBoxesWithIconsInside"][data-item-count="2"] {
    grid-template-columns: 1fr;
}

section[data-image-layout="right"] .smart-layout[data-variant="solidBoxesWithIconsInside"][data-item-count="3"] .card:nth-child(1),
section[data-image-layout="left"] .smart-layout[data-variant="solidBoxesWithIconsInside"][data-item-count="3"] .card:nth-child(1),
section[data-image-layout="right-wide"] .smart-layout[data-variant="solidBoxesWithIconsInside"][data-item-count="3"] .card:nth-child(1),
section[data-image-layout="right"] .smart-layout[data-variant="solidBoxesWithIconsInside"][data-item-count="5"] .card:nth-child(1),
section[data-image-layout="left"] .smart-layout[data-variant="solidBoxesWithIconsInside"][data-item-count="5"] .card:nth-child(1),
section[data-image-layout="right-wide"] .smart-layout[data-variant="solidBoxesWithIconsInside"][data-item-count="5"] .card:nth-child(1) {
    grid-row: span 2;
    min-height: 15rem;
}

/* Explicitly force symmetrical grid for even counts (4, 6) */
section[data-image-layout] .smart-layout[data-variant="solidBoxesWithIconsInside"][data-item-count="4"] .card,
section[data-image-layout] .smart-layout[data-variant="solidBoxesWithIconsInside"][data-item-count="6"] .card {
    grid-row: auto;
    grid-column: auto;
}
section[data-image-layout] .smart-layout[data-variant="solidBoxesWithIconsInside"][data-item-count="4"],
section[data-image-layout] .smart-layout[data-variant="solidBoxesWithIconsInside"][data-item-count="6"] {
    grid-template-columns: repeat(2, minmax(0, 1fr));
}

/* Guard: never force the 3rd card full-width for top/bottom/blank layouts */
.smart-layout[data-variant="solidBoxesWithIconsInside"][data-item-count="3"] .card:nth-child(3) {
    grid-column: auto;
}

@media (max-width: 1080px) {
    .smart-layout[data-variant="solidBoxesWithIconsInside"] {
        /* Keep 3-up on typical slide widths; collapse at 720px */
        grid-template-columns: repeat(3, minmax(0, 1fr));
        width: 100%;
    }
}

@media (max-width: 720px) {
    .smart-layout[data-variant="solidBoxesWithIconsInside"] {
        grid-template-columns: 1fr;
        width: 100%;
    }

    .smart-layout[data-variant="solidBoxesWithIconsInside"] .card {
        min-height: auto;
        padding: 1.45rem 1.25rem 1.2rem;
    }
}

.p-side-strip,
.p-side-strip-left {
    position: relative;
    width: min(20rem, 32%);
    max-width: 100%;
    margin-top: 0.9rem;
    margin-bottom: 0.3rem;
    padding: 0.95rem 1rem 0.95rem 1rem;
    border-radius: 0.8rem;
    background: color-mix(in srgb, var(--bg-secondary, #f8fafc) 84%, transparent);
    border: 1px solid color-mix(in srgb, var(--border-color, #d1d5db) 72%, transparent);
    font-size: calc(var(--p-size) * 0.94);
    line-height: 1.55;
    color: var(--text-secondary, #475569);
    box-shadow: 0 10px 24px rgba(15, 23, 42, 0.05);
}

.p-side-strip {
    margin-left: auto;
    margin-right: 0;
    border-right: 4px solid color-mix(in srgb, var(--accent, #64748b) 72%, #94a3b8);
    padding-right: 1.1rem;
}

.p-side-strip-left {
    margin-left: 0;
    margin-right: auto;
    border-right: none;
    border-left: 4px solid color-mix(in srgb, var(--accent, #64748b) 72%, #94a3b8);
    padding-left: 1.1rem;
}

.p-side-strip::after,
.p-side-strip-left::after {
    content: "";
    position: absolute;
    top: 0.45rem;
    bottom: 0.45rem;
    width: 2px;
    border-radius: 999px;
    background: color-mix(in srgb, var(--accent, #64748b) 70%, #94a3b8);
    opacity: 0.9;
}

.p-side-strip::after {
    right: 0.35rem;
}

.p-side-strip-left::after {
    left: 0.35rem;
}

@media (max-width: 840px) {
    .p-side-strip,
    .p-side-strip-left {
        width: 100%;
    }
}

.smart-layout[data-variant="relationshipMap"] {
    grid-template-columns: repeat(3, minmax(0, 1fr));
    align-items: center;
    gap: 0.9rem;
    padding: 0.35rem 1rem;
    overflow: visible;
}

.smart-layout[data-variant="relationshipMap"] .card:nth-child(1) {
    z-index: 3;
}

.smart-layout[data-variant="relationshipMap"] .card {
    position: relative;
    min-height: 13rem;
    aspect-ratio: 1 / 1;
    border-radius: 50%;
    border: 1px solid rgba(100, 160, 220, 0.15);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    z-index: 1;
    align-items: center;
    justify-content: center;
    text-align: center;
    padding: 1.15rem;
    background: #142A4A;
    color: #ffffff;
}

.smart-layout[data-variant="relationshipMap"] .card:hover {
    box-shadow: 0 10px 28px rgba(15, 23, 42, 0.12);
}

.smart-layout[data-variant="relationshipMap"] .card:nth-child(2) {
    z-index: 2;
    background: #1A3A5C;
    border: 1.5px solid rgba(100, 170, 230, 0.25);
    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.4);
    color: #ffffff;
}

.smart-layout[data-variant="relationshipMap"] .card-content {
    align-items: center;
    justify-content: center;
    gap: 0.55rem;
}

.smart-layout[data-variant="relationshipMap"] .card-title {
    font-size: 1.45rem;
    font-weight: 600;
    text-transform: none;
    letter-spacing: normal;
    color: #8AAFDB;
}

.smart-layout[data-variant="relationshipMap"] .card:nth-child(2) .card-title {
    color: #D0E4FF;
}

.smart-layout[data-variant="relationshipMap"] .card-text {
    font-size: 1.05rem;
    line-height: 1.5;
    color: #5A7EA3;
    max-width: none;
    text-transform: none;
}

.smart-layout[data-variant="relationshipMap"] .card:nth-child(2) .card-text {
    color: #8AAFDB;
}

.smart-layout[data-variant="relationshipMap"] .relationship-connector {
    position: absolute;
    right: -0.55rem;
    width: 5.5rem;
    height: 5.5rem;
    border-radius: 999px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(to bottom, #1A4B8C, #3B7DD8);
    color: #D0E4FF;
    border: 3px solid rgba(255, 255, 255, 0.1);
    box-shadow: 0 10px 32px rgba(46, 107, 196, 0.45);
    z-index: 20;
}

.smart-layout[data-variant="relationshipMap"] .relationship-connector i {
    font-size: 2.25rem;
}

.smart-layout[data-variant="relationshipMap"] .card:nth-child(1) .relationship-connector {
    top: 64%;
    transform: translate(50%, -50%);
}

.smart-layout[data-variant="relationshipMap"] .card:nth-child(2) .relationship-connector {
    top: 34%;
    transform: translate(50%, -50%);
}

.smart-layout[data-variant="ribbonFold"] {
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 0.85rem;
    align-items: start;
    padding: 0.5rem 0.25rem 1.2rem;
}

.smart-layout[data-variant="ribbonFold"] .card {
    position: relative;
    min-height: 17rem;
    padding: 1.3rem 1rem 3.2rem;
    border: none;
    border-radius: 0;
    box-shadow: none;
    clip-path: polygon(0 0, 100% 0, 100% 84%, 50% 100%, 0 84%);
    align-items: center;
    text-align: center;
}

.smart-layout[data-variant="ribbonFold"] .card:hover {
    box-shadow: none;
}

.smart-layout[data-variant="ribbonFold"] .card:nth-child(odd) {
    background: #d92929;
    color: #ffffff;
}

.smart-layout[data-variant="ribbonFold"] .card:nth-child(even) {
    background: #35383f;
    color: #ffffff;
}

.smart-layout[data-variant="ribbonFold"] .card:nth-child(2),
.smart-layout[data-variant="ribbonFold"] .card:nth-child(4) {
    margin-top: 0.9rem;
}

.smart-layout[data-variant="ribbonFold"] .card::before {
    content: "";
    position: absolute;
    top: 0;
    left: -0.75rem;
    width: 0.75rem;
    height: 100%;
    background: rgba(0, 0, 0, 0.2);
    clip-path: polygon(100% 0, 0 8%, 0 92%, 100% 100%);
}

.smart-layout[data-variant="ribbonFold"] .card:first-child::before {
    display: none;
}

.smart-layout[data-variant="ribbonFold"] .card-icon {
    width: 3.2rem;
    height: 3.2rem;
    margin: 0 auto 1rem;
    background: rgba(255, 255, 255, 0.96);
    color: #1f2937;
}

.smart-layout[data-variant="ribbonFold"] .card-icon i {
    font-size: 1.5rem;
    color: #1f2937;
}

.smart-layout[data-variant="ribbonFold"] .card-content {
    align-items: center;
    gap: 0.75rem;
}

.smart-layout[data-variant="ribbonFold"] .card-title {
    font-size: 1rem;
    font-weight: 800;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    color: inherit;
}

.smart-layout[data-variant="ribbonFold"] .card-text {
    font-size: 0.88rem;
    line-height: 1.45;
    color: inherit;
}

.smart-layout[data-variant="statsBadgeGrid"] {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 0.9rem 1rem;
    padding: 0.25rem 0;
    overflow: visible;
}

.smart-layout[data-variant="statsBadgeGrid"] .card {
    position: relative;
    min-height: 9rem;
    padding: 1rem 1rem 0.95rem;
    border: none;
    border-radius: 0.6rem;
    box-shadow: none;
    text-align: center;
    justify-content: center;
}

.smart-layout[data-variant="statsBadgeGrid"] .card:nth-child(1) {
    clip-path: polygon(0 0, calc(100% - 1rem) 0, 100% 50%, calc(100% - 1rem) 100%, 0 100%, 0 60%, 0.7rem 50%, 0 40%);
}

.smart-layout[data-variant="statsBadgeGrid"] .card:nth-child(2) {
    clip-path: polygon(0 0, calc(100% - 0.7rem) 0, 100% 0.7rem, 100% calc(100% - 1rem), 50% 100%, 0 calc(100% - 1rem), 0 0);
}

.smart-layout[data-variant="statsBadgeGrid"] .card:nth-child(3) {
    clip-path: polygon(0 0, calc(100% - 0.7rem) 0, 100% 0.7rem, 100% calc(100% - 0.7rem), calc(100% - 0.7rem) 100%, 0 100%, 0 60%, 0.7rem 50%, 0 40%);
}

.smart-layout[data-variant="statsBadgeGrid"] .card:nth-child(4) {
    clip-path: polygon(1rem 0, 100% 0, 100% 60%, calc(100% - 0.7rem) 50%, 100% 40%, 100% 100%, 0 100%, 0 0);
}

.smart-layout[data-variant="statsBadgeGrid"] .card:hover {
    transform: none;
    box-shadow: none;
}

.smart-layout[data-variant="statsBadgeGrid"] .card:nth-child(1),
.smart-layout[data-variant="statsBadgeGrid"] .card:nth-child(4) {
    background: #dd2b2b;
    color: #ffffff;
}

.smart-layout[data-variant="statsBadgeGrid"] .card:nth-child(2),
.smart-layout[data-variant="statsBadgeGrid"] .card:nth-child(3) {
    background: #45484f;
    color: #ffffff;
}

.smart-layout[data-variant="statsBadgeGrid"] .card-content {
    align-items: center;
    gap: 0.55rem;
}

.smart-layout[data-variant="statsBadgeGrid"] .card-title {
    font-size: 2.3rem;
    font-weight: 900;
    line-height: 0.95;
    letter-spacing: -0.03em;
    text-transform: uppercase;
    color: inherit;
}

.smart-layout[data-variant="statsBadgeGrid"] .card-text {
    max-width: 18ch;
    margin: 0 auto;
    font-size: 0.72rem;
    font-weight: 700;
    line-height: 1.35;
    text-transform: uppercase;
    color: inherit;
}

.smart-layout[data-variant="statsBadgeGrid"] .card-icon,
.smart-layout[data-variant="statsBadgeGrid"] .card-number {
    display: none;
}

.smart-layout[data-variant="statsBadgeGrid"] .card:nth-child(1)::after,
.smart-layout[data-variant="statsBadgeGrid"] .card:nth-child(4)::after {
    content: "";
    position: absolute;
    top: 50%;
    width: 1rem;
    height: 0.34rem;
    background: #7c828b;
    transform: translateY(-50%);
    z-index: 3;
}

.smart-layout[data-variant="statsBadgeGrid"] .card:nth-child(1)::after {
    right: -1rem;
}

.smart-layout[data-variant="statsBadgeGrid"] .card:nth-child(4)::after {
    left: -1rem;
}

.smart-layout[data-variant="statsBadgeGrid"] .card:nth-child(1)::before,
.smart-layout[data-variant="statsBadgeGrid"] .card:nth-child(2)::before,
.smart-layout[data-variant="statsBadgeGrid"] .card:nth-child(4)::before {
    content: "";
    position: absolute;
    width: 0.72rem;
    height: 0.72rem;
    border-top: 0.34rem solid transparent;
    border-bottom: 0.34rem solid transparent;
    z-index: 4;
}

.smart-layout[data-variant="statsBadgeGrid"] .card:nth-child(1)::before {
    top: 50%;
    right: -1.58rem;
    border-left: 0.72rem solid #7c828b;
    transform: translateY(-50%);
}

.smart-layout[data-variant="statsBadgeGrid"] .card:nth-child(2)::after {
    content: "";
    position: absolute;
    left: 50%;
    bottom: -1rem;
    width: 0.34rem;
    height: 1rem;
    background: #7c828b;
    transform: translateX(-50%);
    z-index: 3;
}

.smart-layout[data-variant="statsBadgeGrid"] .card:nth-child(2)::before {
    left: 50%;
    bottom: -1.58rem;
    width: 0;
    height: 0;
    border-left: 0.34rem solid transparent;
    border-right: 0.34rem solid transparent;
    border-top: 0.72rem solid #7c828b;
    transform: translateX(-50%);
}

.smart-layout[data-variant="statsBadgeGrid"] .card:nth-child(4)::before {
    top: 50%;
    left: -1.58rem;
    border-right: 0.72rem solid #7c828b;
    transform: translateY(-50%);
}

.smart-layout[data-variant="diamondRibbon"] {
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 0.8rem;
    align-items: start;
    padding: 0.4rem 0.25rem 1.35rem;
    overflow: visible;
}

.smart-layout[data-variant="diamondRibbon"] .card {
    position: relative;
    min-height: 15rem;
    padding: 1.15rem 0.85rem 2.35rem;
    border: none;
    border-radius: 0;
    box-shadow: none;
    align-items: center;
    text-align: center;
    background: transparent;
}

.smart-layout[data-variant="diamondRibbon"] .card:hover {
    transform: none;
    box-shadow: none;
}

.smart-layout[data-variant="diamondRibbon"] .card:nth-child(odd) {
    color: #ffffff;
}

.smart-layout[data-variant="diamondRibbon"] .card:nth-child(even) {
    color: #ffffff;
}

.smart-layout[data-variant="diamondRibbon"] .card:nth-child(2),
.smart-layout[data-variant="diamondRibbon"] .card:nth-child(4) {
    margin-top: 0.55rem;
}

.smart-layout[data-variant="diamondRibbon"] .card::before {
    content: "";
    position: absolute;
    top: 0;
    left: 50%;
    width: 6.5rem;
    height: 6.5rem;
    border-radius: 0.3rem;
    transform: translateX(-50%) rotate(45deg);
    box-shadow: 0 10px 24px rgba(15, 23, 42, 0.12);
    z-index: 0;
}

.smart-layout[data-variant="diamondRibbon"] .card:nth-child(odd)::before,
.smart-layout[data-variant="diamondRibbon"] .card:nth-child(even)::before {
    background: linear-gradient(to bottom, #1A4B8C, #3B7DD8);
    box-shadow: 0 0 20px rgba(46, 107, 196, 0.3);
}

.smart-layout[data-variant="diamondRibbon"] .card::after {
    content: "";
    position: absolute;
    top: 7.95rem;
    left: 50%;
    width: 1px;
    height: 1.5rem;
    background: #2E6BC4;
    transform: translateX(-50%);
}

.smart-layout[data-variant="diamondRibbon"] .card-content {
    position: relative;
    z-index: 1;
    align-items: center;
    gap: 0.5rem;
    margin-top: 10rem;
}

.smart-layout[data-variant="diamondRibbon"] .card-icon,
.smart-layout[data-variant="diamondRibbon"] .card-number {
    position: absolute;
    top: 1.75rem;
    left: 50%;
    width: 3rem;
    height: 3rem;
    margin: 0;
    border-radius: 999px;
    transform: translateX(-50%);
    background: transparent;
    color: #ffffff;
    z-index: 1;
}

.smart-layout[data-variant="diamondRibbon"] .card-icon i,
.smart-layout[data-variant="diamondRibbon"] .card-number {
    font-size: 1.8rem;
    color: #D0E4FF;
}

.smart-layout[data-variant="diamondRibbon"] .card-title {
    font-size: 1.15rem;
    font-weight: 800;
    line-height: 1.35;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    color: #8AAFDB;
}

.smart-layout[data-variant="diamondRibbon"] .card-text {
    max-width: 16ch;
    margin: 0 auto;
    font-size: 0.95rem;
    line-height: 1.55;
    color: #5A7EA3;
}

section[data-density="super_dense"] .smart-layout[data-variant="diamondRibbon"] {
    gap: 0.65rem;
    padding-bottom: 1rem;
}

section[data-density="super_dense"] .smart-layout[data-variant="diamondRibbon"] .card {
    min-height: 13.6rem;
    padding-inline: 0.65rem;
    padding-bottom: 1.8rem;
}

section[data-density="super_dense"] .smart-layout[data-variant="diamondRibbon"] .card::before {
    width: 4.15rem;
    height: 4.15rem;
}

section[data-density="super_dense"] .smart-layout[data-variant="diamondRibbon"] .card::after {
    top: 4.65rem;
    height: 1.2rem;
}

section[data-density="super_dense"] .smart-layout[data-variant="diamondRibbon"] .card-content {
    margin-top: 5.55rem;
}

section[data-density="super_dense"] .smart-layout[data-variant="diamondRibbon"] .card-icon,
section[data-density="super_dense"] .smart-layout[data-variant="diamondRibbon"] .card-number {
    top: 1.14rem;
    width: 2.1rem;
    height: 2.1rem;
}

section[data-density="super_dense"] .smart-layout[data-variant="diamondRibbon"] .card-title {
    font-size: 0.76rem;
}

section[data-density="super_dense"] .smart-layout[data-variant="diamondRibbon"] .card-text {
    font-size: 0.62rem;
    line-height: 1.35;
}

/* ================================================
   DIAMOND GRID VARIANTS
   Adapts layout based on item count (3 or 4)
   ================================================ */

.smart-layout[data-variant="diamondGrid"] {
    display: grid;
    width: 100%;
    margin: 1.5rem auto;
    overflow: visible;
    padding-left: 2rem;
    padding-right: 2rem;
}

.smart-layout[data-variant="diamondGrid"] .card {
    background: transparent;
    border: none;
    box-shadow: none;
    padding: 0;
    position: relative;
    display: flex;
    overflow: visible;
    gap: 2.5rem;
    grid-template-columns: auto 1fr;
}

.smart-layout[data-variant="diamondGrid"] .card-content {
    display: flex;
    flex-direction: column;
}

.smart-layout[data-variant="diamondGrid"] .card-number,
.smart-layout[data-variant="diamondGrid"] .card-icon {
    flex-shrink: 0;
    width: 6.5rem;
    height: 6.5rem;
    margin: 0;
    background: var(--item-color, #2563eb);
    color: white;
    transform: rotate(45deg);
    border: none;
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 8px 20px rgba(15, 23, 42, 0.12);
}

.smart-layout[data-variant="diamondGrid"] .card:nth-child(even) .card-number,
.smart-layout[data-variant="diamondGrid"] .card:nth-child(even) .card-icon {
    /* Alternate with a lighter tint of the same base color */
    background: color-mix(in srgb, var(--item-color, #2563eb) 55%, white);
    color: #0f172a;
}

.smart-layout[data-variant="diamondGrid"] .card:nth-child(even) .card-icon i {
    color: #0f172a;
}

.smart-layout[data-variant="diamondGrid"] .card-number span,
.smart-layout[data-variant="diamondGrid"] .card-icon i {
    transform: rotate(-45deg);
    font-size: 2.2rem;
    font-weight: 800;
}

/* Sub-Layout 1: Vertical Stack (Slide 1 Style - n=3) */
.smart-layout[data-variant="diamondGrid"][data-item-count="3"]:not(.diagonal) {
    grid-template-columns: 140px 1fr;
    gap: 5rem 4rem;
}

.smart-layout[data-variant="diamondGrid"][data-item-count="3"]:not(.diagonal) .card {
    grid-column: 1 / 3;
    display: grid;
    grid-template-columns: auto 1fr;
    gap: 2.5rem;
    align-items: center;
}

.smart-layout[data-variant="diamondGrid"][data-item-count="3"]:not(.diagonal) .card-number,
.smart-layout[data-variant="diamondGrid"][data-item-count="3"]:not(.diagonal) .card-icon {
    width: 5.5rem;
    height: 5.5rem;
}

/* Sub-Layout 2: Horizontal Row (Slide 2 Style - n=4) */
.smart-layout[data-variant="diamondGrid"][data-item-count="4"]:not(.grid-2d) {
    grid-template-columns: repeat(4, 1fr);
    gap: 3rem;
    text-align: center;
}

.smart-layout[data-variant="diamondGrid"][data-item-count="4"]:not(.grid-2d) .card {
    flex-direction: column;
    align-items: center;
    gap: 2.5rem;
}

/* Sub-Layout 3: 2x2 Grid (Slide 3 Style - n=4) */
.smart-layout[data-variant="diamondGrid"].grid-2d[data-item-count="4"] {
    grid-template-columns: repeat(2, 1fr);
    gap: 4rem 5rem;
}

.smart-layout[data-variant="diamondGrid"].grid-2d[data-item-count="4"] .card {
    display: grid;
    grid-template-columns: auto 1fr;
    gap: 2.5rem;
    align-items: flex-start;
}

/* Sub-Layout 4: Diagonal Flow (Slide 4 Style) */
.smart-layout[data-variant="diamondGrid"].diagonal {
    display: flex;
    flex-direction: column;
    min-height: 700px;
    position: relative;
    padding-left: 6rem; /* extra padding for diagonal */
}

.smart-layout[data-variant="diamondGrid"].diagonal .card {
    position: absolute;
    width: 440px;
    display: grid;
    grid-template-columns: 100px 1fr;
    gap: 2.5rem;
    align-items: center;
}

.smart-layout[data-variant="diamondGrid"].diagonal .card:nth-child(1) { top: 0%; left: 0%; }
.smart-layout[data-variant="diamondGrid"].diagonal .card:nth-child(2) { top: 35%; left: 30%; }
.smart-layout[data-variant="diamondGrid"].diagonal .card:nth-child(3) { top: 70%; left: 60%; }

/* Typography */
.smart-layout[data-variant="diamondGrid"] .card-title {
    /* ~55–60% of title size, but keep within a readable clamp */
    font-size: clamp(1.2rem, calc(var(--h1-size, 2.25rem) * 0.58), 1.45rem);
    font-weight: 800;
    color: var(--text-primary);
    margin-bottom: 0.5rem;
    line-height: 1.25;
}

.smart-layout[data-variant="diamondGrid"] .card-text {
    /* Keep body text readable and clearly distinct from subtitle/context */
    font-size: clamp(0.95rem, calc(var(--h1-size, 2.25rem) * 0.40), 1.1rem);
    line-height: 1.62;
    color: var(--text-secondary);
}

/* ================================================
   DIAMOND HUB VARIANT
   ================================================ */

.smart-layout[data-variant="diamondHub"] {
    display: grid;
    grid-template-columns: 1fr 200px 1fr;
    grid-template-rows: 1fr 200px 1fr;
    gap: 1rem;
    width: 100%;
    margin: 0.5rem auto;
    align-items: center;
}

.smart-layout[data-variant="diamondHub"] .card {
    background: transparent;
    border: none;
    box-shadow: none;
    padding: 0;
    position: relative;
    display: flex;
}

/* Center Node (Item 1) */
.smart-layout[data-variant="diamondHub"] .card:nth-child(1) {
    grid-column: 2;
    grid-row: 2;
    width: 200px;
    height: 200px;
    justify-self: center;
    align-self: center;
    align-items: center;
    justify-content: center;
    z-index: 2;
}

.smart-layout[data-variant="diamondHub"] .card:nth-child(1)::before {
    content: "";
    position: absolute;
    width: 140px;
    height: 140px;
    background: #2b3a4a;
    transform: rotate(45deg);
    border-radius: 0.5rem;
    z-index: -1;
    box-shadow: 0 10px 30px rgba(0,0,0,0.15);
}

.smart-layout[data-variant="diamondHub"] .card:nth-child(1) .card-content {
    text-align: center;
    padding: 1rem;
    margin: 0;
}

.smart-layout[data-variant="diamondHub"] .card:nth-child(1) .card-title {
    font-size: 1.8rem;
    font-weight: 800;
    color: #ffffff;
    margin: 0;
}

.smart-layout[data-variant="diamondHub"] .card:nth-child(1) .card-text,
.smart-layout[data-variant="diamondHub"] .card:nth-child(1) .card-icon,
.smart-layout[data-variant="diamondHub"] .card:nth-child(1) .card-number {
    display: none;
}

/* Satellite Nodes (Items 2-5) */
.smart-layout[data-variant="diamondHub"] .card:not(:nth-child(1)) {
    align-items: center;
    gap: 1.5rem;
    z-index: 1;
}

.smart-layout[data-variant="diamondHub"] .card-icon {
    position: relative;
    width: 5.5rem;
    height: 5.5rem;
    background: transparent;
    color: #ffffff;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}

.smart-layout[data-variant="diamondHub"] .card-icon::before {
    content: "";
    position: absolute;
    inset: 0;
    border-radius: 0.4rem;
    transform: rotate(45deg);
    z-index: -1;
    box-shadow: 0 8px 20px rgba(0,0,0,0.12);
}

/* Satellite Colors */
.smart-layout[data-variant="diamondHub"] .card:nth-child(2) .card-icon::before,
.smart-layout[data-variant="diamondHub"] .card:nth-child(5) .card-icon::before {
    background: #d1d5db;
}
.smart-layout[data-variant="diamondHub"] .card:nth-child(2) .card-icon i,
.smart-layout[data-variant="diamondHub"] .card:nth-child(5) .card-icon i {
    color: #374151;
}

.smart-layout[data-variant="diamondHub"] .card:nth-child(3) .card-icon::before,
.smart-layout[data-variant="diamondHub"] .card:nth-child(4) .card-icon::before {
    background: #4b5563;
}

.smart-layout[data-variant="diamondHub"] .card-icon i {
    z-index: 1;
    font-size: 2rem;
}

.smart-layout[data-variant="diamondHub"] .card:not(:nth-child(1)) .card-content {
    display: flex;
    flex-direction: column;
    justify-content: center;
    max-width: 200px;
}

.smart-layout[data-variant="diamondHub"] .card-text {
    font-size: 1rem;
    color: var(--text-secondary);
    line-height: 1.4;
    margin: 0;
}

/* Specific Positions */
.smart-layout[data-variant="diamondHub"] .card:nth-child(2) {
    grid-column: 1;
    grid-row: 1;
    flex-direction: row-reverse;
    justify-self: end;
    text-align: right;
    transform: translate(25px, 25px);
}
.smart-layout[data-variant="diamondHub"] .card:nth-child(3) {
    grid-column: 3;
    grid-row: 1;
    flex-direction: row;
    justify-self: start;
    text-align: left;
    transform: translate(-25px, 25px);
}
.smart-layout[data-variant="diamondHub"] .card:nth-child(4) {
    grid-column: 1;
    grid-row: 3;
    flex-direction: row-reverse;
    justify-self: end;
    text-align: right;
    transform: translate(25px, -25px);
}
.smart-layout[data-variant="diamondHub"] .card:nth-child(5) {
    grid-column: 3;
    grid-row: 3;
    flex-direction: row;
    justify-self: start;
    text-align: left;
    transform: translate(-25px, -25px);
}

/* ================================================
   CARD GRID DIAMOND BOTTOM VARIANT
   ================================================ */

.smart-layout[data-variant="cardGridDiamond"] {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 2rem;
    width: 100%;
    margin: 0.5rem auto;
    align-items: stretch;
}

.smart-layout[data-variant="cardGridDiamond"] .card {
    position: relative;
    background: transparent;
    border: 2px solid #cbd5e1;
    border-radius: 4px;
    padding: 2.5rem 1.5rem 4rem 1.5rem;
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    box-shadow: none;
    margin-bottom: 2.5rem;
}

.smart-layout[data-variant="cardGridDiamond"] .card-content {
    display: flex;
    flex-direction: column;
    align-items: center;
    width: 100%;
}

.smart-layout[data-variant="cardGridDiamond"] .card-title {
    font-size: 1.4rem;
    font-weight: 800;
    color: var(--text-primary);
    margin-bottom: 1rem;
}

.smart-layout[data-variant="cardGridDiamond"] .card-text {
    font-size: 1.05rem;
    color: var(--text-secondary);
    line-height: 1.5;
}

.smart-layout[data-variant="cardGridDiamond"] .card-icon {
    position: absolute;
    bottom: 0;
    left: 50%;
    transform: translate(-50%, 50%);
    width: 4.5rem;
    height: 4.5rem;
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1;
}

.smart-layout[data-variant="cardGridDiamond"] .card-icon::before {
    content: "";
    position: absolute;
    inset: 0;
    transform: rotate(45deg);
    border-radius: 0.3rem;
    z-index: -1;
    box-shadow: 0 4px 10px rgba(0,0,0,0.1);
}

/* Colors mirroring reference image sequence */
.smart-layout[data-variant="cardGridDiamond"] .card:nth-child(4n+1) .card-icon::before { background: #475569; }
.smart-layout[data-variant="cardGridDiamond"] .card:nth-child(4n+2) .card-icon::before { background: #1e293b; }
.smart-layout[data-variant="cardGridDiamond"] .card:nth-child(4n+3) .card-icon::before { background: #3f3f46; }
.smart-layout[data-variant="cardGridDiamond"] .card:nth-child(4n+4) .card-icon::before { background: #e2e8f0; }

.smart-layout[data-variant="cardGridDiamond"] .card:nth-child(4n+4) .card-icon i { color: #1e293b; }
.smart-layout[data-variant="cardGridDiamond"] .card-icon i {
    color: #ffffff;
    font-size: 1.8rem;
    z-index: 1;
}

/* ================================================
   PROCESS STEPS & ARROWS
   ================================================ */

.smart-layout[data-variant="processSteps"],
.smart-layout[data-variant="processSteps"] {
    display: flex;
    flex-direction: column;
    gap: 0;
}

.smart-layout[data-variant="processAccordion"] {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 1.5rem;
    width: 100%;
}

.smart-layout[data-variant="processSteps"] .card {
    position: relative;
    border: none;
    background: transparent;
    padding: 1.5rem 0;
    padding-left: 4rem;
}

.smart-layout[data-variant="processSteps"] .card-number {
    position: absolute;
    left: 0;
    top: 1.5rem;
    width: 2.5rem;
    height: 2.5rem;
    margin: 0;
    padding: 0;
    background: var(--number-bg, #e8e8e8);
    border-radius: 50%;
    font-size: 1.25rem;
    display: flex;
    align-items: center;
    justify-content: center;
    border: none;
}

.smart-layout[data-variant="processSteps"] .card::after {
    content: '';
    position: absolute;
    left: 1.125rem;
    top: 4.5rem;
    width: 0;
    height: 0;
    border-left: 6px solid transparent;
    border-right: 6px solid transparent;
    border-top: 8px solid var(--number-bg, #e8e8e8);
}

.smart-layout[data-variant="processSteps"] .card:last-child::after,
.smart-layout[data-variant="processAccordion"] .card:last-child::after {
    display: none;
}

.smart-layout[data-variant="processAccordion"] .card {
    position: relative;
    border: 1px solid rgba(255, 255, 255, 0.15);
    background: rgba(255, 255, 255, 0.1);
    padding: 1.25rem 1.5rem;
    margin: 0;
    border-left: 4px solid var(--accent, #6366f1);
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
}

.smart-layout[data-variant="processAccordion"] .card-title {
    font-size: clamp(1.125rem, 2vw, 1.25rem);
    font-weight: 600;
    color: #ffffff;
    margin-bottom: 0.5rem;
}

.smart-layout[data-variant="processAccordion"] .card-text {
    font-size: clamp(0.875rem, 1.5vw, 1rem);
    line-height: 1.55;
    color: rgba(255, 255, 255, 0.65);
}

.smart-layout[data-variant="processAccordion"] .card-number {
    display: none;
}

section[data-density="super_dense"] .smart-layout[data-variant="processAccordion"] .card {
    padding: 0.75rem 1rem;
}

/* --- Process Arrow --- */
.smart-layout[data-variant="processArrow"] {
    display: flex;
    flex-direction: row;
    gap: 2rem;
    align-items: stretch;
}

.smart-layout[data-variant="processArrow"] .card {
    flex: 1;
    position: relative;
    padding: 1.5rem;
    background: var(--bg-secondary, #ffffff);
    border: none;
    border-radius: 12px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.03);
    z-index: 1;
    transition: transform 0.2s ease;
}
.smart-layout[data-variant="processArrow"] .card:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(0,0,0,0.05);
}

.smart-layout[data-variant="processArrow"] .card:not(:last-child)::after {
    content: '\\ea6e';  /* remixicon arrow-right-line */
    font-family: 'remixicon';
    position: absolute;
    right: -1.5rem;
    top: 50%;
    transform: translateY(-50%);
    font-size: 1.25rem;
    color: var(--text-tertiary, #cbd5e1);
    z-index: 0;
}

/* --- Sequential Steps --- */
.smart-layout[data-variant="sequentialSteps"] {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0;               /* No gap — the triangle bridges the space */
    position: relative;
    padding: 0.5rem 0;
    width: 100%;
}

.smart-layout[data-variant="sequentialSteps"] .card {
    position: relative;
    width: 70%;
    max-width: 550px;
    padding: 1.1rem 2rem;
    border: none;
    border-radius: 0;
    text-align: center;
    box-shadow: none;
    z-index: 1;
    background: var(--seq-step-bg, #c8941a);
    color: #ffffff;
    margin-bottom: 1.75rem;  /* space for the arrow triangle + gap */
}

/* Last card needs no bottom margin for the arrow */
.smart-layout[data-variant="sequentialSteps"] .card:last-child {
    margin-bottom: 0;
}

/* Arrow: same-color triangle flush at the box bottom */
.smart-layout[data-variant="sequentialSteps"] .card:not(:last-child)::after {
    content: '';
    position: absolute;
    top: 100%;          /* flush with bottom edge */
    left: 50%;
    transform: translateX(-50%);
    width: 0;
    height: 0;
    border-left: 1.75rem solid transparent;
    border-right: 1.75rem solid transparent;
    border-top: 1.25rem solid var(--seq-step-bg, #c8941a);
    z-index: 2;
}

.smart-layout[data-variant="sequentialSteps"] .card-number,
.smart-layout[data-variant="sequentialSteps"] .card-icon {
    display: none;
}

.smart-layout[data-variant="sequentialSteps"] .card-title {
    font-size: 1.25rem;
    font-weight: 700;
    margin: 0;
    color: #ffffff;
}

.smart-layout[data-variant="sequentialSteps"] .card-text {
    margin-top: 0.25rem;
    font-size: 0.9rem;
    line-height: 1.4;
    color: rgba(255, 255, 255, 0.9);
}

/* ================================================
   BULLET LIST VARIANTS
   ================================================ */

.smart-layout[data-variant="bigBullets"] .card,
.smart-layout[data-variant="bulletIcon"] .card,
.smart-layout[data-variant="bulletCheck"] .card,
.smart-layout[data-variant="bulletCross"] .card {
    flex-direction: row;
    align-items: flex-start;
    gap: 1.25rem;
    padding: 1rem 1.25rem;
    background: transparent;
    border: none;
    border-radius: 8px;
    transition: background-color 0.2s ease;
}

.smart-layout[data-variant="bulletCheck"] .card-icon {
    color: #10b981; /* Success Green */
    background: rgba(16, 185, 129, 0.1);
    padding: 0.5rem;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
}

.smart-layout[data-variant="bulletCross"] .card-icon {
    color: #ef4444; /* Danger Red */
    background: rgba(239, 68, 68, 0.1);
    padding: 0.5rem;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
}


.smart-layout[data-variant="bigBullets"] .card-number {
    position: relative;
    width: auto;
    min-width: 2rem;
    padding: 0.25rem 0.5rem;
    margin: 0;
    background: transparent;
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--accent, #ccc);
    border: none;
    border-radius: 0;
}

/* ================================================
   CALLOUT / TAKEAWAY
   ================================================ */

.callout {
    padding: 1.25rem 1.5rem;
    background: var(--callout-bg, #f5f5f5);
    border-left: 4px solid var(--accent, #666);
    border-radius: 4px;
    margin-top: 1rem;
    font-size: 1.0625rem;
    color: var(--text-primary, #333);
}

/* ================================================
   CODE BLOCK
   ================================================ */

.code-block {
    background: #1e1e1e;
    color: #d4d4d4;
    padding: 1rem;
    border-radius: 0.5rem;
    font-family: 'Fira Code', 'Roboto Mono', monospace;
    font-size: 0.875rem;
    overflow-x: auto; /* Allow scroll if a single word is too long */
    white-space: pre-wrap; /* Wrap text to avoid horizontal scroll/clip */
    word-break: break-word; /* Ensure long words break */
    border: 1px solid var(--border-color, #333);
}

.code-block pre {
    margin: 0;
    overflow-x: auto; /* Ensure inner pre also scrolls */
}

.code-block code {
    font-size: 0.9rem;
    line-height: 1.5;
}

/* ================================================
   TABLE
   ================================================ */

.table-container {
    width: 100%;
    overflow-x: auto;
    margin: 1rem 0;
}

table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.95rem;
}

th, td {
    padding: 0.75rem 1rem;
    text-align: left;
    border-bottom: 1px solid var(--border-color, #e5e5e5);
}

th {
    font-weight: 600;
    color: var(--text-secondary, #555);
    background: var(--bg-secondary, #fafafa);
}

/* Striped variant */
.table-container[data-variant="striped"] tr:nth-child(even) {
    background: var(--bg-tertiary, #f8f9fa);
}

/* Highlight variant */
.table-container[data-variant="highlight"] th {
    background: var(--accent-light, #e6f0ff);
    color: var(--accent, #0066cc);
}

/* ================================================
   QUOTE VARIANT
   ================================================ */

.smart-layout[data-variant="quote"] .card,
.smart-layout[data-variant="quoteTestimonial"] .card,
.smart-layout[data-variant="quoteCitation"] .card {
    border: none;
    background: transparent;
    padding: 0;
    flex-direction: column;
    align-items: center;
    text-align: center;
}

.smart-layout[data-variant="quote"] .card-number,
.smart-layout[data-variant="quoteTestimonial"] .card-number,
.smart-layout[data-variant="quoteCitation"] .card-number { display: none; }

.smart-layout[data-variant="quote"] .card-text,
.smart-layout[data-variant="quoteTestimonial"] .card-text,
.smart-layout[data-variant="quoteCitation"] .card-text {
    font-size: 1.5rem;
    font-style: italic;
    font-weight: 300;
    color: var(--text-primary, #333);
    line-height: 1.4;
    position: relative;
    padding: 0 2rem;
}

.smart-layout[data-variant="quote"] .card-title,
.smart-layout[data-variant="quoteTestimonial"] .card-title {
    margin-top: 1.5rem;
    font-size: 1rem;
    font-weight: 600;
    color: var(--text-secondary, #666);
}

.smart-layout[data-variant="quoteCitation"] .card-title {
    margin-top: 1.5rem;
    font-size: 1rem;
    font-weight: 600;
    color: var(--text-primary, #1a1a1a);
    text-align: right;
    width: 100%;
}
.smart-layout[data-variant="quoteCitation"] .card-text::after {
    content: "”";
    position: absolute;
    right: 0;
    bottom: -1rem;
    font-size: 4rem;
    color: var(--accent, #e5e5e5);
    opacity: 0.5;
    line-height: 1;
}
.smart-layout[data-variant="quoteCitation"] .card-text::before {
    content: "“";
    position: absolute;
    left: 0;
    top: -1rem;
    font-size: 4rem;
    color: var(--accent, #e5e5e5);
    opacity: 0.5;
    line-height: 1;
}


/* ================================================
   DEFINITION VARIANT
   ================================================ */

.smart-layout[data-variant="definition"] .card {
    background: var(--bg-secondary, #fff);
    border-left: 4px solid var(--accent, #666);
}

.smart-layout[data-variant="definition"] .card-title {
    font-size: 1.25rem;
    color: var(--accent, #333);
    margin-bottom: 0.5rem;
}

/* ================================================
   COMPARISON VARIANT (Gamma-style Premium)
   ================================================ */

.smart-layout[data-variant="comparison"],
.smart-layout[data-variant="comparisonProsCons"],
.smart-layout[data-variant="comparisonBeforeAfter"] {
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 2.5rem;
    align-items: stretch;
    padding: 0.5rem 0;
}

.smart-layout[data-variant="comparison"] .card,
.smart-layout[data-variant="comparisonProsCons"] .card,
.smart-layout[data-variant="comparisonBeforeAfter"] .card {
    border: 1px solid color-mix(in srgb, var(--card-accent) 25%, transparent);
    border-radius: 16px;
    padding: 2.5rem 2rem;
    background: var(--bg-secondary, #0f172a);
    box-shadow: none;
    display: flex;
    flex-direction: column;
    transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    position: relative;
    overflow: hidden;
    z-index: 1;
}

.smart-layout[data-variant="comparison"] .card:hover,
.smart-layout[data-variant="comparisonProsCons"] .card:hover,
.smart-layout[data-variant="comparisonBeforeAfter"] .card:hover {
    transform: translateY(-4px);
    box-shadow: none;
    border-color: var(--card-accent);
}

/* Accent strip at the top (Removed based on user request) */
.smart-layout[data-variant="comparison"] .card::before,
.smart-layout[data-variant="comparisonProsCons"] .card::before,
.smart-layout[data-variant="comparisonBeforeAfter"] .card::before {
    display: none;
}

.smart-layout[data-variant="comparison"] .card:nth-child(1) { --card-accent: #3b82f6; } /* Blue */
.smart-layout[data-variant="comparison"] .card:nth-child(2) { --card-accent: #8b5cf6; } /* Purple */
.smart-layout[data-variant="comparison"] .card:nth-child(3) { --card-accent: #f59e0b; } /* Orange */
.smart-layout[data-variant="comparison"] .card:nth-child(4) { --card-accent: #10b981; } /* Green */
.smart-layout[data-variant="comparison"] .card:nth-child(5) { --card-accent: #ef4444; } /* Red */
.smart-layout[data-variant="comparison"] .card:nth-child(6) { --card-accent: #06b6d4; } /* Cyan */
.smart-layout[data-variant="comparison"] .card:nth-child(7) { --card-accent: #ec4899; } /* Pink */
.smart-layout[data-variant="comparison"] .card:nth-child(8) { --card-accent: #eab308; } /* Yellow */

.smart-layout[data-variant="comparison"] .card-icon {
    width: 4rem;
    height: 4rem;
    margin-bottom: 2rem;
    background: color-mix(in srgb, var(--card-accent) 15%, transparent);
    border-radius: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
    transform: rotate(-3deg);
    transition: transform 0.3s ease;
}

.smart-layout[data-variant="comparison"] .card:hover .card-icon {
    transform: rotate(0deg) scale(1.1);
}

.smart-layout[data-variant="comparison"] .card-icon i {
    color: var(--card-accent);
    font-size: 1.75rem;
}

.smart-layout[data-variant="comparison"] .card-title,
.smart-layout[data-variant="comparisonProsCons"] .card-title,
.smart-layout[data-variant="comparisonBeforeAfter"] .card-title {
    font-size: 1.25rem;
    font-weight: 800;
    margin-bottom: 1.5rem;
    color: var(--card-accent);
    letter-spacing: 0.05em;
    text-transform: uppercase;
    line-height: 1.4;
}

/* Premium Card List */
.card-list {
    list-style: none;
    padding: 0;
    margin: 0;
}

.card-list li {
    position: relative;
    padding-left: 1.5rem;
    margin-bottom: 1rem;
    font-size: 0.95rem;
    line-height: 1.5;
    color: var(--text-secondary, #cbd5e1);
}

.card-list li::before {
    content: '•';
    position: absolute;
    left: 0;
    top: 0;
    color: var(--card-accent);
    font-size: 1.25rem;
    line-height: 1.1;
    opacity: 0.8;
}

.smart-layout[data-variant="comparisonProsCons"] .card:last-child .card-list li::before {
    content: '\\eb98'; /* remixicon close */
}

/* --- Pros / Cons --- */
.smart-layout[data-variant="comparisonProsCons"] .card:first-child {
    --card-accent: #10b981;
    background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, var(--bg-secondary) 100%);
}
.smart-layout[data-variant="comparisonProsCons"] .card:last-child {
    --card-accent: #ef4444;
    background: linear-gradient(135deg, rgba(239, 68, 68, 0.1) 0%, var(--bg-secondary) 100%);
}

/* --- Before / After --- */
.smart-layout[data-variant="comparisonBeforeAfter"] .card:nth-child(1) { --card-accent: #64748b; background: linear-gradient(135deg, rgba(100, 116, 139, 0.1) 0%, var(--bg-secondary) 100%); }
.smart-layout[data-variant="comparisonBeforeAfter"] .card:nth-child(2) { --card-accent: #3b82f6; }
.smart-layout[data-variant="comparisonBeforeAfter"]::after {
    content: '\\ea6e';
    font-family: 'remixicon';
    position: absolute;
    left: 50%;
    top: 50%;
    transform: translate(-50%, -50%);
    font-size: 1.75rem;
    color: #fff;
    background: var(--card-accent, #3b82f6);
    border: 4px solid var(--bg-primary, #0f172a);
    border-radius: 50%;
    width: 4rem;
    height: 4rem;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 10px 20px rgba(0,0,0,0.4);
    z-index: 10;
}

/* --- Density Overrides --- */
.slide-section[data-density="super_dense"] .smart-layout[data-variant="comparison"] .card,
.slide-section[data-density="super_dense"] .smart-layout[data-variant="comparisonProsCons"] .card,
.slide-section[data-density="super_dense"] .smart-layout[data-variant="comparisonBeforeAfter"] .card {
    padding: 1.25rem 1rem;
    gap: 0.5rem;
}

.slide-section[data-density="super_dense"] .smart-layout[data-variant="comparison"] .card-icon {
    width: 2.5rem;
    height: 2.5rem;
    margin-bottom: 0.5rem;
}

.slide-section[data-density="super_dense"] .smart-layout[data-variant="comparison"] .card-icon i {
    font-size: 1.25rem;
}

.slide-section[data-density="super_dense"] .smart-layout[data-variant="comparison"] .card-title,
.slide-section[data-density="super_dense"] .smart-layout[data-variant="comparisonProsCons"] .card-title,
.slide-section[data-density="super_dense"] .smart-layout[data-variant="comparisonBeforeAfter"] .card-title {
    font-size: 1.15rem;
    margin-bottom: 0.75rem;
}

.slide-section[data-density="super_dense"] .card-list li {
    font-size: 0.9rem;
    margin-bottom: 0.4rem;
    padding-left: 1.5rem;
}

.slide-section[data-density="super_dense"] .card-list li::before {
    font-size: 0.85rem;
}

/* --- Bento Grid (3 items: 2 on top, 1 wide on bottom) --- */
.smart-layout[data-variant^="comparison"][data-item-count="3"] {
    grid-template-columns: repeat(2, 1fr);
    gap: 1rem;
}

/* Make the 3rd card span full width */
.smart-layout[data-variant^="comparison"][data-item-count="3"] .card:nth-child(3) {
    grid-column: span 2;
    display: flex;
    flex-direction: row;
    align-items: center;
    gap: 2rem;
    padding: 1.5rem 2rem;
}

/* Adjust card 3 icon/content for horizontal flow */
.smart-layout[data-variant^="comparison"][data-item-count="3"] .card:nth-child(3) .card-icon {
    margin-bottom: 0;
    flex-shrink: 0;
}

.smart-layout[data-variant^="comparison"][data-item-count="3"] .card:nth-child(3) .card-title {
    margin-bottom: 0.5rem;
}

.slide-section[data-density="super_dense"] .smart-layout[data-variant^="comparison"][data-item-count="3"] .card:nth-child(3) {
    padding: 1rem 1.25rem;
    gap: 1.25rem;
}

/* --- Dense Grid for 4-8 Items --- */
.smart-layout[data-variant^="comparison"][data-item-count="4"],
.smart-layout[data-variant^="comparison"][data-item-count="5"],
.smart-layout[data-variant^="comparison"][data-item-count="6"],
.smart-layout[data-variant^="comparison"][data-item-count="7"],
.smart-layout[data-variant^="comparison"][data-item-count="8"] {
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
    padding: 1rem 0;
}

.smart-layout[data-variant^="comparison"][data-item-count="4"] .card,
.smart-layout[data-variant^="comparison"][data-item-count="5"] .card,
.smart-layout[data-variant^="comparison"][data-item-count="6"] .card,
.smart-layout[data-variant^="comparison"][data-item-count="7"] .card,
.smart-layout[data-variant^="comparison"][data-item-count="8"] .card {
    padding: 1rem 1.25rem;
}

.smart-layout[data-variant^="comparison"][data-item-count="5"] .card-title,
.smart-layout[data-variant^="comparison"][data-item-count="6"] .card-title,
.smart-layout[data-variant^="comparison"][data-item-count="7"] .card-title,
.smart-layout[data-variant^="comparison"][data-item-count="8"] .card-title {
    font-size: 1.05rem;
    margin-bottom: 0.5rem;
}

.smart-layout[data-variant^="comparison"][data-item-count="5"] .card-icon,
.smart-layout[data-variant^="comparison"][data-item-count="6"] .card-icon,
.smart-layout[data-variant^="comparison"][data-item-count="7"] .card-icon,
.smart-layout[data-variant^="comparison"][data-item-count="8"] .card-icon {
    width: 2.25rem;
    height: 2.25rem;
    margin-bottom: 0.5rem;
}

.smart-layout[data-variant^="comparison"][data-item-count="5"] .card-icon i,
.smart-layout[data-variant^="comparison"][data-item-count="6"] .card-icon i,
.smart-layout[data-variant^="comparison"][data-item-count="7"] .card-icon i,
.smart-layout[data-variant^="comparison"][data-item-count="8"] .card-icon i {
    font-size: 1.2rem;
}

.smart-layout[data-variant^="comparison"][data-item-count="5"] .card-text,
.smart-layout[data-variant^="comparison"][data-item-count="6"] .card-text,
.smart-layout[data-variant^="comparison"][data-item-count="7"] .card-text,
.smart-layout[data-variant^="comparison"][data-item-count="8"] .card-text {
    font-size: 0.85rem;
    line-height: 1.4;
}


.callout p {
    font-size: 0.9375rem;
    margin: 0;
}

.callout strong {
    font-weight: 600;
    color: var(--text-primary, #1a1a1a);
}

/* ================================================
   DIVIDER
   ================================================ */

.divider {
    border: none;
    height: 1px;
    background: var(--border-color, #e5e5e5);
    margin: 1.5rem 0;
}

/* ================================================
   INLINE IMAGE
   ================================================ */

.inline-image {
    margin: 0;
}


.accent-image-group {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    align-self: center;
    width: 100%; /* Ensure it takes full grid column width */
}

.accent-image-group .accent-image-wrapper,
.accent-image-group .accent-image-placeholder {
    flex: 1;
    width: 100%;
}

.image-annotation {
    font-size: 0.8125rem;
    line-height: 1.45;
    padding: 0.625rem 0.75rem;
    margin: 0;
}

.inline-image img {
    width: 100%;
    height: auto;
    border-radius: 0.5rem;
}

/* Dense column image constraint */
.columns .inline-image img {
    max-height: 40vh;
    width: auto;
    max-width: 100%;
    object-fit: contain;
    align-self: center;
}

/* ================================================
   PLACEHOLDER IMAGE
   ================================================ */

.accent-image-placeholder {
    width: 100%;
    aspect-ratio: 1 / 1;
    min-height: 400px; /* Baseline visibility */
    background: var(--bg-tertiary, #f1f5f9);
    border-radius: 1.25rem;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 2px dashed var(--border-color, #cbd5e1);
}

section[data-image-layout="left"] .accent-image-placeholder,
section[data-image-layout="right"] .accent-image-placeholder {
    height: 100vh;
    max-height: 100vh;
    border-radius: 0;
    border: none;
}

.placeholder-content {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1.25rem;
    color: var(--text-secondary, #64748b);
}

.placeholder-icon {
    font-size: 4rem;
    opacity: 0.8;
}

.placeholder-text {
    font-size: 0.875rem;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

/* ================================================
   RESPONSIVE
   ================================================ */

@media (max-width: 768px) {
    :root {
        --section-padding: clamp(1rem, 2.4vh, 1.25rem) clamp(1.25rem, 3vw, 1.5rem);
    }

    .gyml-deck { padding: 0; }
    section { padding: 0; }
    
    section[data-image-layout="right"],
    section[data-image-layout="left"] {
        grid-template-columns: 1fr;
    }
    
    section[data-image-layout="left"] .accent-image-wrapper,
    section[data-image-layout="left"] .accent-image-placeholder,
    section[data-image-layout="left"] .accent-image-group {
        order: -1;
    }
    
    .columns {
        flex-direction: column;
    }
    
    .column {
        flex: 1 1 100% !important;
    }
    
    .accent-image-group {
        width: 100%;
        max-width: none;
        margin: 0;
    }
    
    .smart-layout {
        grid-template-columns: 1fr !important;
    }
    
    h1 {
        font-size: 2rem;
    }
    
    h2 {
        font-size: 1.5rem;
    }
    /* Component Overrides */
    hr, .divider {
        background: none !important;
        height: 0 !important;
        border: 0;
        border-top: 1px var(--divider-style, solid) var(--border-color, #e5e5e5);
        margin: 2rem 0;
    }
}

/* ================================================
   ANIMATION SYSTEM
   Elements with data-segment start hidden when
   inside an animated section. The .active class
   reveals them with per-type transitions.
   ================================================ */

/* --- Hidden state (only in animated sections) --- */
section[data-animated="true"] [data-segment] {
    opacity: 0;
    visibility: hidden;
    transition: opacity 0.5s ease, transform 0.5s ease, visibility 0s 0.5s;
}

/* --- Revealed state --- */
section[data-animated="true"] [data-segment].active {
    opacity: 1;
    visibility: visible;
    transform: translate(0, 0) !important;
    transition: opacity 0.5s ease, transform 0.5s ease, visibility 0s 0s;
}

/* --- Slide Up (cards, timeline items) --- */
section[data-animated="true"] .anim-slide-up {
    transform: translateY(24px);
}

/* --- Slide from Left (first column, first comparison card) --- */
section[data-animated="true"] .anim-slide-left {
    transform: translateX(-30px);
}

/* --- Slide from Right (second column, second comparison card) --- */
section[data-animated="true"] .anim-slide-right {
    transform: translateX(30px);
}

/* --- Fade only (paragraphs) --- */
section[data-animated="true"] .anim-fade {
    transform: none;
}

/* Timeline line and dots are ALWAYS visible (never hidden) */
section[data-animated="true"] .smart-layout[data-variant="timeline"]::before,
section[data-animated="true"] .smart-layout[data-variant="timelineHorizontal"]::before {
    opacity: 1;
    visibility: visible;
}

/* ================================================
   HUB AND SPOKE (Circular Hexagon Layout)
   ================================================ */

/* HUB AND SPOKE SLIDE OVERRIDES */
section.holds-hub {
    --slide-content-padding: 1.5rem 3rem 2.5rem 3rem;
}

section.holds-hub .body {
    justify-content: center;
}

.hub-and-spoke-container {
    position: relative;
    width: 100%;
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-top: 20px;
    margin-bottom: 20px;
    overflow: visible;
}

.hub-center {
    position: absolute;
    z-index: 10;
    width: 160px;
    height: 160px;
    display: flex;
    align-items: center;
    justify-content: center;
}

.hub-circle {
    width: 100%;
    height: 100%;
    background: #fff;
    border: 4px solid var(--accent-primary, #2d3436);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    text-align: center;
    padding: 15px;
}

.hub-label {
    font-size: 1.2rem;
    font-weight: 800;
    color: var(--text-primary, #1a1a1a);
    text-transform: uppercase;
    line-height: 1.2;
}

.spokes-wrapper {
    position: relative;
    width: 500px;
    height: 500px;
    z-index: 5;
}

.hub-connection-line {
    position: absolute;
    width: 320px; /* Diameter of the orbit (160px * 2) */
    height: 320px;
    border: 3px dashed rgba(45, 52, 70, 0.15);
    border-radius: 50%;
    z-index: 1; /* Behind spokes */
    pointer-events: none;
}

.spoke-item {
    position: absolute;
    width: 120px;
    height: 140px;
    top: 50%;
    left: 50%;
    transform-origin: center;
    margin-top: -70px;
    margin-left: -60px;
}

/* Dynamic Positioning Logic (4, 5, 6 items) */
/* Radius reduced slightly to 230px to ensure nothing is cut off */

/* Case: 4 items (90 deg intervals) */
.hub-and-spoke-container[data-item-count="4"] .spoke-item[data-index="0"] { transform: rotate(-90deg) translate(160px) rotate(90deg); }
.hub-and-spoke-container[data-item-count="4"] .spoke-item[data-index="1"] { transform: rotate(0deg) translate(160px) rotate(0deg); }
.hub-and-spoke-container[data-item-count="4"] .spoke-item[data-index="2"] { transform: rotate(90deg) translate(160px) rotate(-90deg); }
.hub-and-spoke-container[data-item-count="4"] .spoke-item[data-index="3"] { transform: rotate(180deg) translate(160px) rotate(-180deg); }

/* Case: 5 items (72 deg intervals) */
.hub-and-spoke-container[data-item-count="5"] .spoke-item[data-index="0"] { transform: rotate(-90deg) translate(160px) rotate(90deg); }
.hub-and-spoke-container[data-item-count="5"] .spoke-item[data-index="1"] { transform: rotate(-18deg) translate(160px) rotate(18deg); }
.hub-and-spoke-container[data-item-count="5"] .spoke-item[data-index="2"] { transform: rotate(54deg) translate(160px) rotate(-54deg); }
.hub-and-spoke-container[data-item-count="5"] .spoke-item[data-index="3"] { transform: rotate(126deg) translate(160px) rotate(-126deg); }
.hub-and-spoke-container[data-item-count="5"] .spoke-item[data-index="4"] { transform: rotate(198deg) translate(160px) rotate(-198deg); }

/* Case: 6 items (60 deg intervals) */
.hub-and-spoke-container[data-item-count="6"] .spoke-item[data-index="0"] { transform: rotate(-90deg) translate(160px) rotate(90deg); }
.hub-and-spoke-container[data-item-count="6"] .spoke-item[data-index="1"] { transform: rotate(-30deg) translate(160px) rotate(30deg); }
.hub-and-spoke-container[data-item-count="6"] .spoke-item[data-index="2"] { transform: rotate(30deg) translate(160px) rotate(-30deg); }
.hub-and-spoke-container[data-item-count="6"] .spoke-item[data-index="3"] { transform: rotate(90deg) translate(160px) rotate(-90deg); }
.hub-and-spoke-container[data-item-count="6"] .spoke-item[data-index="4"] { transform: rotate(150deg) translate(160px) rotate(-150deg); }
.hub-and-spoke-container[data-item-count="6"] .spoke-item[data-index="5"] { transform: rotate(210deg) translate(160px) rotate(-210deg); }

/* Hexagon Shape */
.hexagon {
    width: 100%;
    height: 100%;
    background: var(--item-color, #3498db);
    clip-path: polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%);
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    cursor: pointer;
    transition: all 0.3s ease;
    z-index: 5;
}

/* Ensure Top and Bottom spokes are on top of their neighbors to prevent box occlusion */
.hub-and-spoke-container .spoke-item[data-index="0"],
.hub-and-spoke-container .spoke-item[data-index="3"] {
    z-index: 20;
}

.hexagon-inner {
    width: 90%;
    height: 90%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    color: white;
    padding: 10px;
}

.hexagon-inner i {
    font-size: 1.8rem;
    margin-bottom: 5px;
}

.spoke-label {
    font-size: 0.85rem;
    font-weight: 700;
    line-height: 1.2;
}

/* Always Visible Side Info Box */
.spoke-info-box {
    position: absolute;
    width: 150px;
    background: rgba(255, 255, 255, 1);
    padding: 0.5rem;
    border-radius: 6px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    opacity: 1; /* Always visible */
    visibility: visible;
    z-index: 10;
    --y-offset: -50%;
    transform: translateY(var(--y-offset));
    text-align: left;
    border-left: 3px solid var(--item-color, #3498db);
    pointer-events: auto;
}

/* Ensure animation doesn't kill the transform positioning */
section[data-animated="true"] .hub-and-spoke-container .spoke-info-box[data-segment].active {
    transform: translateY(var(--y-offset)) !important;
}

.spoke-info-box p {
    margin: 0;
    font-size: 0.7rem;
    color: #333;
    line-height: 1.3;
}

/* Positioning boxes STRICTLY on the SIDES (Left or Right) */

/* Positioning boxes STRICTLY on the SIDES (Left or Right) */
/* Using staggered vertical and horizontal offsets to prevent overlap */

/* Primary Side Assignment */
.hub-and-spoke-container .spoke-item[data-index="0"] .spoke-info-box,
.hub-and-spoke-container .spoke-item[data-index="1"] .spoke-info-box,
.hub-and-spoke-container .spoke-item[data-index="2"] .spoke-info-box {
    left: 140%; /* Pushed out substantially to prevent hexagon overlap */
    top: 50%;
}

.hub-and-spoke-container .spoke-item[data-index="3"] .spoke-info-box,
.hub-and-spoke-container .spoke-item[data-index="4"] .spoke-info-box,
.hub-and-spoke-container .spoke-item[data-index="5"] .spoke-info-box {
    right: 140%; /* Pushed out substantially */
    top: 50%;
}

/* Vertical and Horizontal Staggering for 6 items - PERFECT DUAL COLUMN */
.hub-and-spoke-container[data-item-count="6"] .spoke-item[data-index="0"] .spoke-info-box { --y-offset: -100%; left: 140%; } /* Top -> Higher */
.hub-and-spoke-container[data-item-count="6"] .spoke-item[data-index="1"] .spoke-info-box { --y-offset: -40%; left: 140%; } /* Mid -> Centered, Closer Right */
.hub-and-spoke-container[data-item-count="6"] .spoke-item[data-index="2"] .spoke-info-box { --y-offset: 10%; left: 140%; } /* Bottom -> Lower, Closer Right */

.hub-and-spoke-container[data-item-count="6"] .spoke-item[data-index="5"] .spoke-info-box { --y-offset: -100%; right: 140%; } /* Top-Left -> Higher, Closer Left */
.hub-and-spoke-container[data-item-count="6"] .spoke-item[data-index="4"] .spoke-info-box { --y-offset: -40%; right: 140%; } /* Mid-Left -> Centered, Closer Left */
.hub-and-spoke-container[data-item-count="6"] .spoke-item[data-index="3"] .spoke-info-box { --y-offset: 10%; right: 140%; } /* Bottom-Left -> Lower */

/* 4 Items Logic */
.hub-and-spoke-container[data-item-count="4"] .spoke-item .spoke-info-box { --y-offset: -50%; }
.hub-and-spoke-container[data-item-count="4"] .spoke-item[data-index="2"] .spoke-info-box,
.hub-and-spoke-container[data-item-count="4"] .spoke-item[data-index="3"] .spoke-info-box { right: 140%; left: auto; }

/* Dynamically use the --item-color for the hexagon background */
.hexagon { background: var(--item-color, #3498db); }

/* ================================================
   CYCLIC BLOCK (SVG Arc-Sector Wheel)
   3-column flex layout: left-col | svg-wheel | right-col
   ================================================ */

.cyclic-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: flex-start;
    width: 100%;
    min-height: 520px;
    flex: 1;
    padding: 1rem 0;
    overflow: visible;
}

.cyclic-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    width: 100%;
    min-height: 620px;
    flex: 1;
    padding: 0.5rem 0;
    overflow: visible;
}

.cyclic-wheel-area {
    position: relative;
    width: min(520px, 92vw);
    height: min(520px, 92vw);
    display: flex;
    align-items: center;
    justify-content: center;
    margin: auto;
}

.cyclic-container--balanced .cyclic-main-row {
    position: relative;
    width: 1100px;
    max-width: 1100px;
    min-height: 560px;
    margin: 0 auto;
}

.cyclic-container--balanced {
    align-self: center;
    width: fit-content;
    max-width: 1100px;
    margin: 0 auto;
}

.cyclic-container--balanced .cyclic-col {
    position: absolute;
    top: 50%;
    display: flex;
    flex-direction: column;
    justify-content: center;
    gap: 0.85rem;
    width: 220px;
    transform: translateY(-50%);
}

.cyclic-container--balanced .cyclic-col--left {
    left: 0;
    align-items: stretch;
}

.cyclic-container--balanced .cyclic-col--right {
    right: 0;
    align-items: stretch;
}

.cyclic-container--balanced .cyclic-wheel-area {
    position: absolute;
    top: 50%;
    left: 50%;
    margin: 0;
    transform: translate(-50%, -50%);
}

.cyclic-svg-wrapper {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 2;
}

.cyclic-svg {
    width: 100%;
    height: 100%;
    overflow: visible;
}

.cyclic-floating-cards {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
    z-index: 5;
}

.cyclic-container--orbital {
    align-self: center;
    width: min(980px, 100%);
    margin: 0 auto;
}

.cyclic-orbital-stage {
    position: relative;
    width: 940px;
    max-width: 940px;
    min-height: 640px;
    margin: 0 auto;
}

.cyclic-container--orbital .cyclic-wheel-area {
    position: absolute;
    top: 50%;
    left: 50%;
    margin: 0;
    transform: translate(-50%, -50%);
}

.cyclic-info-box {
    position: absolute;
    pointer-events: auto;
    width: min(250px, 35vw);
    padding: 1rem 1.2rem;
    background: rgba(255, 255, 255, 0.88);
    backdrop-filter: blur(14px);
    border: 1px solid color-mix(in srgb, var(--item-color, #2563eb) 20%, rgba(255,255,255,0.4));
    border-radius: 20px;
    box-shadow: 0 14px 40px rgba(2, 8, 23, 0.12);
    text-align: left;
    transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 0.3s ease;
}

.cyclic-container--orbital .cyclic-info-box--orbital {
    width: 220px;
    min-height: 108px;
    padding: 0.85rem 1rem 0.95rem;
}

.cyclic-container--orbital .cyclic-info-box--orbital .cyclic-ib-icon {
    float: left;
    margin: 0.15rem 0.8rem 0.35rem 0;
}

.cyclic-container--orbital .cyclic-info-box--orbital .cyclic-ib-title {
    line-height: 1.2;
    margin-bottom: 0.2rem;
}

.cyclic-container--orbital .cyclic-info-box--orbital .cyclic-ib-text {
    display: -webkit-box;
    -webkit-box-orient: vertical;
    -webkit-line-clamp: 4;
    overflow: hidden;
}

.cyclic-container--balanced .cyclic-info-box {
    position: relative;
    width: 100%;
    max-width: 220px;
    min-height: 104px;
}

.cyclic-container--balanced .cyclic-info-box--landscape {
    display: block;
}

.cyclic-container--balanced .cyclic-info-box--landscape .cyclic-ib-icon {
    float: left;
    margin: 0.1rem 0.8rem 0.35rem 0;
}

.cyclic-container--balanced .cyclic-info-box--landscape .cyclic-ib-title {
    margin-bottom: 0.2rem;
    line-height: 1.25;
}

.cyclic-container--balanced .cyclic-info-box--landscape .cyclic-ib-text {
    display: -webkit-box;
    -webkit-box-orient: vertical;
    -webkit-line-clamp: 4;
    overflow: hidden;
}

.cyclic-info-box:hover {
    box-shadow: 0 20px 50px rgba(2, 8, 23, 0.22);
    z-index: 10;
}

.cyclic-info-box::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 5px;
    background: linear-gradient(to right, var(--item-color, #2563eb), color-mix(in srgb, var(--item-color, #2563eb) 40%, white));
    border-radius: 20px 20px 0 0;
}

.cyclic-ib-icon {
    width: 2.25rem;
    height: 2.25rem;
    border-radius: 50%;
    background: linear-gradient(135deg, var(--item-color, #2563eb), color-mix(in srgb, var(--item-color, #2563eb) 60%, white));
    color: white;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 0.8rem;
    box-shadow: 0 6px 14px color-mix(in srgb, var(--item-color, #2563eb) 35%, transparent);
}

.cyclic-ib-icon i {
    font-size: 1.1rem;
}

.cyclic-ib-title {
    display: block;
    font-size: 1rem;
    font-weight: 700;
    color: var(--text-primary, #1a1a1a);
    margin-bottom: 0.35rem;
    line-height: 1.3;
}

.cyclic-ib-text {
    margin: 0;
    font-size: 0.9rem;
    color: var(--text-secondary, #555);
    line-height: 1.5;
}

/* Animation */
section[data-animated="true"] .cyclic-info-box[data-segment] {
    opacity: 0;
    visibility: hidden;
    transition: opacity 0.5s ease, visibility 0s 0.5s;
}




/* Responsive Scaling */

@media (max-width: 1000px) {
    .spokes-wrapper, .cyclic-items-wrapper {
        transform: scale(0.8);
    }
    .cyclic-track {
        transform: scale(0.8);
    }
}
@media (max-width: 768px) {
    .hub-and-spoke-container, .cyclic-container {
        transform: scale(0.6);
        padding: 1rem;
    }
    .spoke-info-box, .cyclic-info-box {
        display: none; /* Hide boxes on mobile to prevent clutter */
    }
}
"""

    def _get_animator_js(self) -> str:
        """Get the SlideAnimator JavaScript controller."""
        return """
<script>
/**
 * SlideAnimator — Controls segment-by-segment reveal of slide elements.
 *
 * Usage:
 *   const section = document.querySelector('section[data-animated]');
 *   const animator = new SlideAnimator(section);
 *   animator.revealSegment(0);  // reveal first segment
 *   animator.revealSegment(1);  // reveal second segment
 *   animator.revealAll();       // show everything
 *   animator.reset();           // hide all animated elements
 */
class SlideAnimator {
    constructor(sectionEl) {
        this.section = sectionEl;
        this.segments = Array.from(
            sectionEl.querySelectorAll('[data-segment]')
        ).sort((a, b) => {
            return parseInt(a.dataset.segment) - parseInt(b.dataset.segment);
        });
        this.revealedCount = 0;
        this.totalSegments = this.segments.length;
    }

    /** Reveal a specific segment by index. */
    revealSegment(index) {
        const els = this.segments.filter(
            el => parseInt(el.dataset.segment) === index
        );
        els.forEach(el => el.classList.add('active'));
        this.revealedCount = Math.max(this.revealedCount, index + 1);
    }

    /** Reveal the next unrevealed segment. Returns the index or -1 if done. */
    revealNext() {
        if (this.revealedCount >= this.totalSegments) return -1;
        // Find the next segment index
        const nextIdx = parseInt(this.segments[this.revealedCount].dataset.segment);
        this.revealSegment(nextIdx);
        return nextIdx;
    }

    /** Reveal all segments at once (skip animation). */
    revealAll() {
        this.segments.forEach(el => {
            el.style.transition = 'none';
            el.classList.add('active');
        });
        this.revealedCount = this.totalSegments;
    }

    /** Hide all animated elements (reset to initial state). */
    reset() {
        this.segments.forEach(el => {
            el.classList.remove('active');
            el.style.transition = '';
        });
        this.revealedCount = 0;
    }

    /** Check if all segments have been revealed. */
    get isComplete() {
        return this.revealedCount >= this.totalSegments;
    }
}

// Auto-init: create animators for all animated sections
window.slideAnimators = {};
document.querySelectorAll('section[data-animated="true"]').forEach(section => {
    const animator = new SlideAnimator(section);
    window.slideAnimators[section.id] = animator;
    
    // Only auto-reveal in standalone mode (direct file open / static preview).
    // When embedded inside the player iframe, the parent bridge script controls
    // the animation via postMessage — auto-revealing here would race with it.
    if (window.parent === window) {
        setTimeout(() => {
            animator.revealAll();
        }, 100);
    }
});
</script>
"""
