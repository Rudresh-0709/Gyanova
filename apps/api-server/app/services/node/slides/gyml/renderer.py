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

    def render(self, section: GyMLSection) -> str:
        """Passively render GyML section to HTML."""
        # Reset segment counter for each section
        self._segment_counter = 0
        lines = []

        # Generate hierarchy CSS variables if present
        style_attr = ""
        if section.hierarchy:
            vars_list = []
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
        if section.hierarchy and section.hierarchy.name in ("super_dense", "compact"):
            density_attr = f' data-density="{section.hierarchy.name}"'

        lines.append(
            f'<section id="{self._escape(section.id)}" '
            f'class="slide-section" '
            f'role="region" aria-label="Slide {section.id}" '
            f'data-image-layout="{section.image_layout}"'
            f"{style_attr}{anim_attr}{density_attr}>"
        )

        # Render Image (unless it's bottom layout, then we render it after body)
        render_image_early = section.image_layout != "bottom"

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

        lines.append(self._render_body(section.body))

        # Render Image late if it's bottom layout
        if section.accent_image and not render_image_early:
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
            f'alt="{self._escape(image.alt or "")}" loading="lazy" />'
            f"</div>"
        )

    def _render_body(self, body: GyMLBody) -> str:
        """Render body container."""
        children_html = []
        separator_count = 0  # Max 1 separator per slide
        for i, child in enumerate(body.children):
            rendered = self._render_node(child)
            if rendered:
                children_html.append(rendered)

                # Add separator logic (between distinct major blocks) — max 1 per slide
                if i < len(body.children) - 1 and separator_count < 1:
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
                        separator_count += 1

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
        return f"<!-- Unknown node type: {type(node).__name__} -->"

    def _render_heading(self, heading: GyMLHeading) -> str:
        """Render heading."""
        level = heading.level
        text = self._escape(heading.text)
        return f"<h{level}>{text}</h{level}>"

    def _render_paragraph(self, paragraph: GyMLParagraph) -> str:
        """Render paragraph."""
        text = self._escape(paragraph.text)
        variant_class = f"p-{paragraph.variant}" if paragraph.variant else ""

        # Paragraphs are always visible (not animated)
        # Only primary content (smart_layout cards) gets data-segment

        class_attr = f' class="{variant_class}"' if variant_class else ""
        return f"<p{class_attr}>{text}</p>"

    def _render_divider(self) -> str:
        """Render divider."""
        return '<hr class="divider" />'

    def _render_inline_image(self, image: GyMLImage) -> str:
        """Render inline image."""
        if not image.src or image.src.lower() == "null":
            return ""

        return (
            f'<figure class="inline-image">'
            f'<img src="{self._escape(image.src)}" '
            f'alt="{self._escape(image.alt or "")}" loading="lazy" />'
            f"</figure>"
        )

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

        html_parts = [
            f'<div class="smart-layout" '
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
            html_parts.append(f'<div class="card-number">{index + 1}</div>')

        # Auto-Icon Selection for specific variants (if icon absent or needs override)
        icon_class = None
        if item.icon:
            icon_class = item.icon.alt
            if not icon_class.startswith("ri-"):
                icon_class = f"ri-{icon_class}-line"
        elif variant == "bulletCheck":
            icon_class = "ri-check-line"
        elif variant == "bulletCross":
            icon_class = "ri-close-line"
        elif variant == "comparisonProsCons":
            icon_class = "ri-check-line" if index == 0 else "ri-close-line"

        if icon_class:
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
            if item.heading:
                html_parts.append(
                    f'<h4 class="card-title">{self._escape(item.heading)}</h4>'
                )
            if item.description:
                # Handle multiline descriptions (e.g. from comparison lists)
                desc_html = self._escape(item.description).replace("\n", "<br>")
                html_parts.append(f'<p class="card-text">{desc_html}</p>')

        html_parts.append("</div>")
        html_parts.append("</div>")

        return "\n".join(html_parts)

    def _render_comparison_table(self, table: GyMLComparisonTable) -> str:
        """Render comparison table."""
        headers_html = "".join(f"<th>{self._escape(h)}</th>" for h in table.headers)
        rows_html = []
        for row in table.rows:
            cells_html = "".join(f"<td>{self._escape(c)}</td>" for c in row)
            rows_html.append(f"<tr>{cells_html}</tr>")

        caption_html = (
            f'<div class="table-caption">{self._escape(table.caption)}</div>'
            if table.caption
            else ""
        )

        return (
            f'<div class="comparison-table-container">'
            f"<table>"
            f"<thead><tr>{headers_html}</tr></thead>"
            f'<tbody>{"".join(rows_html)}</tbody>'
            f"</table>"
            f"{caption_html}"
            f"</div>"
        )

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
        return self._render_node(node) if node else ""

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
   SECTION - Full Viewport Slide
   ================================================ */

section {
    position: relative;
    width: 100%;
    height: 100vh;
    padding: var(--section-padding, 2rem 3rem);
    background: var(--bg-secondary, #ffffff);
    overflow: hidden;
    display: flex;
    flex-direction: column;
    scroll-snap-align: start; /* Snap target */
    flex-shrink: 0; /* Prevent shrinking */
}

/* ... image layouts ... */
section[data-image-layout="right"] {
    display: grid;
    grid-template-columns: 1.5fr 1fr; /* col 1 (Text) = 60%, col 2 (Img) = 40% */
    gap: var(--block-gap, 2rem);
    align-items: center;
}
section[data-image-layout="right"] .body { order: 1; grid-column: 1; }
section[data-image-layout="right"] .accent-image-wrapper,
section[data-image-layout="right"] .accent-image-placeholder,
section[data-image-layout="right"] .accent-image-group { order: 2; grid-column: 2; }

section[data-image-layout="left"] {
    display: grid;
    grid-template-columns: 1fr 1.5fr; /* 40% Image / 60% Text */
    gap: var(--block-gap, 2rem);
    align-items: center;
}
section[data-image-layout="left"] .body { order: 2; grid-column: 2; }
section[data-image-layout="left"] .accent-image-wrapper,
section[data-image-layout="left"] .accent-image-placeholder,
section[data-image-layout="left"] .accent-image-group { order: 1; grid-column: 1; }

section[data-image-layout="right-wide"] {
    display: grid;
    grid-template-columns: 1fr 1.5fr; /* 40% Text / 60% Image */
    gap: var(--block-gap, 2rem);
    align-items: center;
}
section[data-image-layout="right-wide"] .body { order: 1; grid-column: 1; }
section[data-image-layout="right-wide"] .accent-image-wrapper,
section[data-image-layout="right-wide"] .accent-image-placeholder,
section[data-image-layout="right-wide"] .accent-image-group { order: 2; grid-column: 2; }

/* Top / Bottom Layouts (Vertical Stacking) */
section[data-image-layout="top"],
section[data-image-layout="bottom"] {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
}

section[data-image-layout="top"] .accent-image-group,
section[data-image-layout="top"] .accent-image-wrapper,
section[data-image-layout="top"] .accent-image-placeholder {
    width: 100%;
    margin-bottom: 0.5rem;
}

section[data-image-layout="bottom"] .accent-image-group,
section[data-image-layout="bottom"] .accent-image-wrapper,
section[data-image-layout="bottom"] .accent-image-placeholder {
    width: 100%;
    margin-top: auto;
}

/* Adjust aspect ratios and heights for vertical layouts */
section[data-image-layout="top"] .accent-image-placeholder,
section[data-image-layout="bottom"] .accent-image-placeholder {
    aspect-ratio: 16 / 5;
    min-height: 150px;
    max-height: 20vh;
}

section[data-image-layout="top"] .accent-image-wrapper img,
section[data-image-layout="bottom"] .accent-image-wrapper img {
    width: 100%;
    max-height: 20vh;
    object-fit: cover;
    object-position: center;
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
    font-size: 0.8125rem;
    line-height: 1.45;
    padding: 0.625rem 0.75rem;
    margin: 0;
}

/* ... */

.body {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: var(--block-gap, 1rem);
    overflow: hidden;
    justify-content: center;
}

/* ================================================
   TYPOGRAPHY - Clean & Professional
   ================================================ */

h1 {
    font-size: var(--h1-size, 2.25rem);
    font-weight: 800;
    line-height: 1.25;
    letter-spacing: -0.03em;
    color: var(--text-primary, #1a1a1a);
    margin-bottom: var(--heading-gap, 0.25rem);
}

h2 {
    font-size: var(--h2-size, 2rem);
    font-weight: 700;
    line-height: 1.2;
    letter-spacing: -0.02em;
    color: var(--text-primary, #1a1a1a);
    margin-bottom: var(--heading-gap, 0.25rem);
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
    font-size: var(--p-size, 1rem);
    line-height: var(--line-height, 1.7);
    color: var(--text-secondary, #4a4a4a);
}

.p-intro {
    font-size: 1.125rem;
    font-weight: 500;
    color: var(--text-primary, #1a1a1a);
    margin-bottom: 0.5rem;
}

.p-context {
    font-style: italic;
    color: var(--text-tertiary, #666);
    opacity: 0.9;
}

.p-annotation {
    font-size: 0.875rem;
    background: var(--callout-bg, #fbfbfb);
    color: var(--text-primary, inherit);
    padding: 0.75rem;
    border-left: 3px solid var(--accent, #e5e7eb);
    margin: 0.5rem 0;
}

.p-outro {
    font-weight: 500;
    border-top: 1px dashed #ddd;
    padding-top: 0.75rem;
    margin-top: 1rem;
}

.p-caption {
    font-size: 0.8125rem;
    color: var(--text-tertiary, #888);
    text-align: center;
    margin-top: 0.5rem;
    line-height: 1.4;
}

/* ================================================
   COLUMNS
   ================================================ */

.columns {
    display: flex;
    gap: 2rem;
    width: 100%;
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
    margin: 1.25rem 0;
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
    font-size: 1.0625rem;
    font-weight: 600;
    color: var(--text-primary, #1a1a1a);
    margin: 0;
    line-height: 1.4;
}

.card-text {
    font-size: var(--card-text-size, var(--p-size, 0.9375rem));
    line-height: var(--line-height, 1.65);
    color: var(--text-secondary, #555);
    margin: 0;
}

/* ================================================
   NEW CONTENT TYPES STYLES
   ================================================ */

/* Comparison Table */
.comparison-table-container {
    width: 100%;
    overflow-x: auto;
    margin: 1rem 0;
    border: 1px solid var(--border-color, #e5e5e5);
    border-radius: 8px;
    background: #fff;
}
.comparison-table-container table {
    width: 100%;
    border-collapse: collapse;
}
.comparison-table-container th, .comparison-table-container td {
    padding: 1rem;
    border: 1px solid var(--border-color, #e5e5e5);
    text-align: left;
}
.comparison-table-container th {
    background: #f8f9fa;
    font-weight: 700;
}
.table-caption {
    padding: 0.75rem;
    font-size: 0.875rem;
    color: #666;
    font-style: italic;
    text-align: center;
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

section[data-density="super_dense"] {
    padding-top: 1.5rem !important;
    padding-bottom: 2rem !important;
}

section[data-density="super_dense"] .body {
    justify-content: flex-start !important;
}

section[data-density="super_dense"] .card-icon {
    width: 2rem;
    height: 2rem;
    margin-bottom: 0.5rem;
}

section[data-density="super_dense"] .card-icon i {
    font-size: 0.9rem;
}

section[data-density="super_dense"] .card-number {
    padding: 0.375rem;
    margin: -1rem -1rem 0.625rem -1rem;
    width: calc(100% + 2rem);
    font-size: 0.875rem;
}

section[data-density="super_dense"] .card-content {
    gap: 0.25rem;
}

section[data-density="super_dense"] .card-title {
    font-size: 0.9375rem;
}

section[data-density="super_dense"] .block-separator {
    margin: 0.5rem 0;
}

section[data-density="super_dense"] .p-annotation {
    font-size: 0.75rem;
    padding: 0.5rem 0.625rem;
    margin: 0;
}

section[data-density="super_dense"] .numbered-list {
    gap: 0.75rem;
}

section[data-density="super_dense"] .numbered-list li {
    padding: 0.75rem;
}

section[data-density="super_dense"] .hierarchy-tree-container {
    padding: 1rem;
}

section[data-density="super_dense"] .hierarchy-tree-container ul {
    margin-top: 0.25rem;
}

/* ================================================
   TIMELINE VARIANT (Vertical)
   ================================================ */

.smart-layout[data-variant="timeline"] {
    display: flex;
    flex-direction: column;
    gap: 0;
    position: relative;
    padding-left: 2rem;
}

.smart-layout[data-variant="timeline"]::before {
    content: '';
    position: absolute;
    left: 0.5rem;
    top: 0.5rem;
    bottom: 0.5rem;
    width: 2px;
    background: var(--timeline-color, #2d8a6e);
}

.smart-layout[data-variant="timeline"] .card {
    position: relative;
    border: none;
    background: transparent;
    padding: var(--card-padding, 1.25rem) 0;
    border-radius: 0;
}

.smart-layout[data-variant="timeline"] .card::before {
    content: '';
    position: absolute;
    left: -1.75rem;
    top: 1.5rem;
    width: 12px;
    height: 12px;
    background: var(--timeline-color, #2d8a6e);
    border-radius: 50%;
}

/* Primary Item (First) */
.smart-layout[data-variant="timeline"] .card:first-child .card-text {
    color: var(--text-primary, #1a1a1a);
    font-size: 1.1rem;
}

.smart-layout[data-variant="timeline"] .card:first-child::before {
    background: var(--accent, #6366f1);
    width: 16px;
    height: 16px;
    left: -1.875rem;
    box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.2);
}

/* Secondary Items (Rest) */
.smart-layout[data-variant="timeline"] .card:not(:first-child) {
    opacity: 0.85;
}

.smart-layout[data-variant="timeline"] .card:not(:first-child) .card-text {
    font-size: 1rem;
}

.smart-layout[data-variant="timeline"] .card:not(:first-child)::before {
    top: 1.625rem; /* Adjust for smaller size alignment */
    width: 10px;
    height: 10px;
    left: -1.6875rem; /* Re-center */
    background: var(--text-tertiary, #a0a0a0);
}

.smart-layout[data-variant="timeline"] .card-number {
    display: none;
}

.card-year {
    font-size: 1.125rem;
    font-weight: 700;
    color: var(--timeline-color, #2d8a6e);
    margin-bottom: 0.375rem;
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
    gap: 1.5rem;
    position: relative;
    padding-left: 2.5rem;
}

.smart-layout[data-variant="timelineSequential"]::before {
    content: '';
    position: absolute;
    left: 1rem;
    top: 1rem;
    bottom: 1rem;
    width: 2px;
    background: var(--border-color, #e2e8f0);
    opacity: 0.6;
}

.smart-layout[data-variant="timelineSequential"] .card {
    position: relative;
    border: none;
    background: transparent;
    padding: 1rem 0;
    border-radius: 0;
}

.smart-layout[data-variant="timelineSequential"] .card-number {
    position: absolute;
    left: -2.5rem;
    top: 1.25rem;
    width: 2rem;
    height: 2rem;
    margin: 0;
    padding: 0;
    background: var(--bg-primary, #ffffff);
    color: var(--accent, #333333);
    border: 2px solid var(--accent, #333333);
    border-radius: 50%;
    font-size: 0.85rem;
    font-weight: 600;
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 2;
    box-shadow: 0 0 0 4px var(--bg-primary, #ffffff);
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

/* ================================================
   PROCESS STEPS & ARROWS
   ================================================ */

.smart-layout[data-variant="processSteps"],
.smart-layout[data-variant="processAccordion"] {
    display: flex;
    flex-direction: column;
    gap: 0;
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
    font-size: 1rem;
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
   COMPARISON VARIANT
   ================================================ */

.smart-layout[data-variant="comparison"],
.smart-layout[data-variant="comparisonProsCons"],
.smart-layout[data-variant="comparisonBeforeAfter"] {
    grid-template-columns: 1fr 1fr;
    gap: 1.5rem;
}

.smart-layout[data-variant="comparison"] .card,
.smart-layout[data-variant="comparisonProsCons"] .card,
.smart-layout[data-variant="comparisonBeforeAfter"] .card {
    border: 1px solid var(--border-color, #f1f5f9);
    border-radius: 12px;
    padding: 1.5rem;
    background: var(--bg-secondary, #ffffff);
    box-shadow: 0 2px 8px rgba(0,0,0,0.02);
}

.smart-layout[data-variant="comparison"] .card:first-child {
    border-top: 4px solid var(--accent-1, #94a3b8);
}

.smart-layout[data-variant="comparison"] .card:last-child {
    border-top: 4px solid var(--accent-2, #cbd5e1);
}

/* --- Pros / Cons --- */
.smart-layout[data-variant="comparisonProsCons"] .card:first-child {
    border-top: 4px solid #10b981; /* Success Green */
    background: linear-gradient(to bottom, rgba(16, 185, 129, 0.03), transparent);
}
.smart-layout[data-variant="comparisonProsCons"] .card:last-child {
    border-top: 4px solid #ef4444; /* Danger Red */
    background: linear-gradient(to bottom, rgba(239, 68, 68, 0.03), transparent);
}
.smart-layout[data-variant="comparisonProsCons"] .card-icon {
    font-size: 1.25rem;
    margin-bottom: 0.5rem;
}
.smart-layout[data-variant="comparisonProsCons"] .card:first-child .card-icon {
    color: #10b981;
}
.smart-layout[data-variant="comparisonProsCons"] .card:last-child .card-icon {
    color: #ef4444;
}

/* --- Before / After --- */
.smart-layout[data-variant="comparisonBeforeAfter"] {
    position: relative;
    gap: 2.5rem;
}
.smart-layout[data-variant="comparisonBeforeAfter"]::after {
    content: '\\ea6e';
    font-family: 'remixicon';
    position: absolute;
    left: 50%;
    top: 50%;
    transform: translate(-50%, -50%);
    font-size: 1.25rem;
    color: var(--text-secondary, #64748b);
    background: var(--bg-primary, #ffffff);
    border: 1px solid var(--border-color, #f1f5f9);
    border-radius: 50%;
    width: 2.5rem;
    height: 2.5rem;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    z-index: 10;
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

.body {
    flex: 1;
    display: flex;
    flex-direction: column;
    min-width: 0; /* Prevent overflow */
}

/* ================================================
   PLACEHOLDER IMAGE
   ================================================ */

.accent-image-placeholder {
    width: 100%;
    aspect-ratio: 1 / 1;
    min-height: 400px; /* Baseline visibility */
    max-height: 80vh;
    background: var(--bg-tertiary, #f1f5f9);
    border-radius: 1.25rem;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 2px dashed var(--border-color, #cbd5e1);
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
    .gyml-deck {
        padding: 1rem;
    }
    
    section {
        padding: 2rem;
    }
    
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
        max-width: 400px;
        margin: 0 auto 1.5rem auto;
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
    
    // Auto-reveal for static previews. Parent presentation controller 
    // can reset() this if it wants to control the animation.
    setTimeout(() => {
        animator.revealAll();
    }, 100);
});
</script>
"""
