"""
GyML Renderer

PASSIVE renderer: GyML → HTML.
Maps GyML structure to HTML without any inference or semantic decisions.
Designed to match Gamma-style professional slides.
"""

from typing import List, Optional
import html

from .types import (
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
    GyMLNode,
)
from .theme import Theme, THEMES


class GyMLRenderer:
    """
    PASSIVE renderer: GyML → HTML.
    Gamma-style professional output.
    """

    def __init__(self, theme: Optional[Theme] = None):
        self.theme = theme or THEMES.get("gamma_light")

    def render(self, section: GyMLSection) -> str:
        """Passively render GyML section to HTML."""
        lines = []

        lines.append(
            f'<section id="{self._escape(section.id)}" '
            f'data-image-layout="{section.image_layout}">'
        )

        if section.accent_image:
            lines.append(self._render_accent_image(section.accent_image))

        lines.append(self._render_body(section.body))
        lines.append("</section>")

        return "\n".join(lines)

    def render_many(self, sections: List[GyMLSection]) -> str:
        """Render multiple sections."""
        rendered_sections = [self.render(s) for s in sections]
        return "\n\n".join(rendered_sections)

    def render_complete(self, sections: List[GyMLSection]) -> str:
        """Render complete HTML document with Gamma-style styles."""
        sections_html = self.render_many(sections)

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GyML Slides</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/remixicon@4.2.0/fonts/remixicon.css" rel="stylesheet">
    <style>
{self._get_gamma_styles()}
{self.theme.to_css_vars() if self.theme else ""}
    </style>
</head>
<body>
    <div class="gyml-deck">
{sections_html}
    </div>
</body>
</html>"""

    # =========================================================================
    # ELEMENT RENDERERS
    # =========================================================================

    def _render_accent_image(self, image: GyMLImage) -> str:
        """Render accent image."""
        return (
            f'<div class="accent-image-wrapper">'
            f'<img class="accent-image" '
            f'src="{self._escape(image.src)}" '
            f'alt="{self._escape(image.alt)}" />'
            f"</div>"
        )

    def _render_body(self, body: GyMLBody) -> str:
        """Render body container."""
        children_html = []
        for i, child in enumerate(body.children):
            rendered = self._render_node(child)
            if rendered:
                children_html.append(rendered)

                # Add separator logic (between distinct major blocks)
                if i < len(body.children) - 1:
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
        return f"<!-- Unknown node type: {type(node).__name__} -->"

    def _render_heading(self, heading: GyMLHeading) -> str:
        """Render heading."""
        level = heading.level
        text = self._escape(heading.text)
        return f"<h{level}>{text}</h{level}>"

    def _render_paragraph(self, paragraph: GyMLParagraph) -> str:
        """Render paragraph."""
        text = self._escape(paragraph.text)
        return f"<p>{text}</p>"

    def _render_divider(self) -> str:
        """Render divider."""
        return '<hr class="divider" />'

    def _render_inline_image(self, image: GyMLImage) -> str:
        """Render inline image."""
        return (
            f'<figure class="inline-image">'
            f'<img src="{self._escape(image.src)}" '
            f'alt="{self._escape(image.alt)}" />'
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
        html_parts = [f'<div class="card" data-index="{index}">']

        # Number badge at top (Gamma style)
        if variant in ["bigBullets", "processSteps", "cardGrid"]:
            html_parts.append(f'<div class="card-number">{index + 1}</div>')

        # Icon
        if item.icon:
            icon_class = item.icon.alt
            if not icon_class.startswith("ri-"):
                icon_class = f"ri-{icon_class}-line"
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
                html_parts.append(
                    f'<p class="card-text">{self._escape(item.description)}</p>'
                )

        html_parts.append("</div>")
        html_parts.append("</div>")

        return "\n".join(html_parts)

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
    overflow: hidden; /* Hide main scrollbar */
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
    overflow: hidden; /* Prevent scrolling */
    scroll-snap-type: none;
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
    padding: 2rem 3rem; /* Reduced from 3rem 5rem */
    background: var(--bg-secondary, #ffffff);
    overflow: hidden;
    display: flex;
    flex-direction: column;
    scroll-snap-align: start; /* Snap target */
    flex-shrink: 0; /* Prevent shrinking */
}

/* Image Layouts */
section[data-image-layout="right"] {
    display: grid;
    grid-template-columns: 1fr 45%;
    gap: 2rem; /* Reduced from 3rem */
    align-items: center;
}

section[data-image-layout="left"] {
    display: grid;
    grid-template-columns: 45% 1fr;
    gap: 2rem;
    align-items: center;
}

section[data-image-layout="left"] .accent-image-wrapper {
    order: -1;
}

section[data-image-layout="top"] {
    display: flex;
    flex-direction: column;
}

section[data-image-layout="top"] .accent-image-wrapper {
    order: -1;
    margin-bottom: 1.5rem;
}

section[data-image-layout="behind"] {
    position: relative;
}

section[data-image-layout="behind"] .accent-image-wrapper {
    position: absolute;
    inset: 0;
    z-index: 0;
}

section[data-image-layout="behind"] .accent-image {
    width: 100%;
    height: 100%;
    object-fit: cover;
    opacity: 0.15;
}

section[data-image-layout="behind"] .body {
    position: relative;
    z-index: 1;
}

/* Accent Image */
.accent-image-wrapper {
    border-radius: 0.5rem;
    overflow: hidden;
}

.accent-image {
    width: 100%;
    height: auto;
    display: block;
}

/* ================================================
   BODY - Content Container (Fills viewport)
   ================================================ */

.body {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 1rem; /* Reduced from 1.5rem */
    overflow: hidden;
    justify-content: center;
}

/* ================================================
   TYPOGRAPHY - Clean & Professional
   ================================================ */

h1 {
    font-size: 2.25rem; /* Reduced from 2.75rem */
    font-weight: 800;
    line-height: 1.15;
    letter-spacing: -0.03em;
    color: var(--text-primary, #1a1a1a);
    margin-bottom: 0.25rem; /* Reduced */
}

h2 {
    font-size: 2rem;
    font-weight: 700;
    line-height: 1.2;
    letter-spacing: -0.02em;
    color: var(--text-primary, #1a1a1a);
}

h3 {
    font-size: 1.5rem;
    font-weight: 600;
    color: var(--text-primary, #1a1a1a);
}

h4 {
    font-size: 1.125rem;
    font-weight: 600;
    color: var(--text-primary, #1a1a1a);
    line-height: 1.3;
}

p {
    font-size: 1rem;
    line-height: 1.7;
    color: var(--text-secondary, #4a4a4a);
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
    gap: 1.25rem;
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
    padding: 1.5rem;
    background: var(--bg-secondary, #ffffff);
    border: 1px solid var(--border-color, #e5e5e5);
    border-radius: 4px;
    transition: box-shadow 0.2s ease;
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
    font-size: 1.125rem;
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
    font-size: 0.9375rem;
    line-height: 1.65;
    color: var(--text-secondary, #555);
    margin: 0;
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
    padding: 1.25rem 0;
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

.smart-layout[data-variant="timelineHorizontal"] .card:nth-child(even) .card-year {
    order: -1;
}

.smart-layout[data-variant="timelineHorizontal"] .card-text {
    font-size: 0.875rem;
    line-height: 1.5;
    color: var(--text-secondary, #555);
}

/* ================================================
   STATS VARIANT
   ================================================ */

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
   PROCESS STEPS VARIANT
   ================================================ */

.smart-layout[data-variant="processSteps"] {
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

.smart-layout[data-variant="processSteps"] .card:last-child::after {
    display: none;
}

/* ================================================
   BIG BULLETS VARIANT
   ================================================ */

.smart-layout[data-variant="bigBullets"] .card {
    flex-direction: row;
    align-items: flex-start;
    gap: 1rem;
    padding: 1.25rem;
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
    padding: 1.5rem;
    border-radius: 6px;
    width: 100%;
    margin: 1rem 0;
    overflow-x: auto;
    font-family: 'Fira Code', 'Roboto Mono', monospace;
}

.code-block pre {
    margin: 0;
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
.smart-layout[data-variant="quoteTestimonial"] .card {
    border: none;
    background: transparent;
    padding: 0;
    flex-direction: column;
    align-items: center;
    text-align: center;
}

.smart-layout[data-variant="quote"] .card-number { display: none; }

.smart-layout[data-variant="quote"] .card-text {
    font-size: 1.5rem;
    font-style: italic;
    font-weight: 300;
    color: var(--text-primary, #333);
    line-height: 1.4;
    position: relative;
    padding: 0 2rem;
}

.smart-layout[data-variant="quote"] .card-title {
    margin-top: 1.5rem;
    font-size: 1rem;
    font-weight: 600;
    color: var(--text-secondary, #666);
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

.smart-layout[data-variant="comparison"] {
    grid-template-columns: 1fr 1fr;
    gap: 2rem;
}

.smart-layout[data-variant="comparison"] .card {
    border-top: 4px solid var(--border-color, #e5e5e5);
    border-radius: 4px;
}

.smart-layout[data-variant="comparison"] .card:first-child {
    border-top-color: var(--accent-1, #d4d4d4);
}

.smart-layout[data-variant="comparison"] .card:last-child {
    border-top-color: var(--accent-2, #888);
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

.inline-image img {
    width: 100%;
    height: auto;
    border-radius: 0.5rem;
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
    
    section[data-image-layout="left"] .accent-image-wrapper {
        order: -1;
    }
    
    .columns {
        flex-direction: column;
    }
    
    .column {
        flex: 1 1 100% !important;
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
}
"""
