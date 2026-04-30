"""
Enhanced Interactive Sandbox for GyML Content Block Audit.

Generates an HTML page showing EVERY content block variant from:
  1. BLOCK_CATALOG (smart_layout family entries)
  2. _VARIANT_CANONICAL (renderer canonical list)
  3. Standalone block types (hub_and_spoke, cyclic, etc.)

Each block is tagged with its source status so the auditor can
decide: keep, fix, or remove.
"""
import os
import sys
import random

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
API_SERVER_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "apps", "api-server"))
if API_SERVER_ROOT not in sys.path:
    sys.path.insert(0, API_SERVER_ROOT)

from app.services.node.slides.gyml.composer import SlideComposer
from app.services.node.slides.gyml.serializer import GyMLSerializer
from app.services.node.slides.gyml.renderer import GyMLRenderer, _VARIANT_CANONICAL
from app.services.node.slides.gyml.theme import THEMES
from app.services.node.blocks.shared.styles import get_slide_css
from app.services.node.v2.block_catalog_v2 import BLOCK_CATALOG

# ── Master variant lists ────────────────────────────────────────────────────
# 1. smart_layout variants from BLOCK_CATALOG
CATALOG_SL_VARIANTS = {}
for (family, variant), spec in BLOCK_CATALOG.items():
    if family == "smart_layout" and spec.smart_layout_variant:
        CATALOG_SL_VARIANTS[spec.smart_layout_variant] = spec

# 2. Renderer canonical variants
RENDERER_VARIANTS = set(_VARIANT_CANONICAL.values())

# 3. Standalone block types (rendered via their own GyML* classes)
STANDALONE_BLOCKS = [
    "hub_and_spoke",
    "cyclic_block",
    "feature_showcase_block",
    "process_arrow_block",
    "cyclic_process_block",
]

# 4. Text-like families from catalog that aren't smart_layout
NON_SL_FAMILIES = {}
for (family, variant), spec in BLOCK_CATALOG.items():
    if family not in ("smart_layout", "supporting_text", "supporting_callout",
                      "supporting_image", "concept_image"):
        key = f"{family}:{variant}"
        if key not in NON_SL_FAMILIES:
            NON_SL_FAMILIES[key] = spec

# ── Build the COMPLETE variant set ──────────────────────────────────────────
ALL_SL_VARIANTS = sorted(set(list(CATALOG_SL_VARIANTS.keys()) + list(RENDERER_VARIANTS)))


def get_status_tag(variant):
    """Return audit status for a smart_layout variant."""
    in_catalog = variant in CATALOG_SL_VARIANTS
    in_renderer = variant in RENDERER_VARIANTS
    if in_catalog and in_renderer:
        return "BOTH", "#22c55e"   # green
    elif in_catalog:
        return "CATALOG ONLY", "#f59e0b"  # amber
    else:
        return "RENDERER ONLY", "#ef4444"  # red


def generate_smart_items(variant, num=4):
    """Generate appropriate dummy items based on variant type."""
    stats_variants = {"stats", "InterlockingArrows", "statsComparison", "statsPercentage"}
    timeline_variants = {"timeline", "timelineIcon", "timelineHorizontal",
                         "timelineSequential", "timelineMilestone"}
    comparison_variants = {"comparison", "comparisonProsCons",
                           "comparisonBeforeAfter", "comparisonCards"}

    items = []
    for i in range(num):
        item = {
            "heading": f"Concept {i+1}",
            "label": f"Label {i+1}",
            "description": f"This is a detailed description for item {i+1} demonstrating content flow and text wrapping behavior.",
            "icon_name": ["ri-lightbulb-line", "ri-rocket-line", "ri-check-line",
                          "ri-star-line", "ri-shield-check-line", "ri-brain-line"][i % 6],
            "value": f"{random.randint(10, 99)}%",
            "year": f"{2020 + i}",
            "points": [f"Sub-point {j+1} for item {i+1}" for j in range(3)],
        }
        if variant in comparison_variants and i < 2:
            item["heading"] = ["Option A", "Option B"][i]
            item["description"] = f"Detailed analysis of {'the first' if i==0 else 'the second'} option with supporting evidence."
            item["points"] = [f"Point {j+1}" for j in range(3)]
        items.append(item)

    if variant in stats_variants:
        return items[:4]
    elif variant in timeline_variants:
        return items[:5]
    elif variant in comparison_variants:
        return items[:2]
    elif variant == "relationshipMap":
        return items[:3]
    elif variant == "sequentialOutput":
        return [f"$ step {i+1}: processing..." for i in range(4)]
    return items


def generate_standalone_items(family, num=4):
    """Generate items for standalone block types."""
    items = []
    for i in range(num):
        items.append({
            "label": f"Phase {i+1}",
            "heading": f"Phase {i+1}",
            "description": f"Details about phase {i+1} demonstrating the block layout.",
            "icon": ["ri-lightbulb-line", "ri-rocket-line",
                     "ri-check-line", "ri-star-line"][i % 4],
            "color": ["#6366f1", "#22c55e", "#f59e0b", "#ef4444"][i % 4],
        })
    return items


def main():
    composer = SlideComposer()
    serializer = GyMLSerializer()
    selected_theme = THEMES["midnight"]
    renderer = GyMLRenderer(theme=selected_theme, animated=False)

    entries = []  # List of (key, status_tag, status_color, html)
    errors = []

    # ── A. Render ALL smart_layout variants ──────────────────────────────────
    for variant in ALL_SL_VARIANTS:
        tag, color = get_status_tag(variant)
        num_items = 4
        if variant in ("comparison", "comparisonProsCons", "comparisonBeforeAfter", "comparisonCards"):
            num_items = 2
        elif variant == "relationshipMap":
            num_items = 3
        elif variant in ("timeline", "timelineIcon", "timelineHorizontal", "timelineSequential", "timelineMilestone"):
            num_items = 5

        if variant == "sequentialOutput":
            payload_block = {
                "type": "smart_layout",
                "variant": "sequentialOutput",
                "items": ["$ npm install gyanova", "$ node setup.js", "> Initializing engine...", "> Ready!"]
            }
        else:
            payload_block = {
                "type": "smart_layout",
                "variant": variant,
                "items": generate_smart_items(variant, num_items),
            }

        payload = {
            "title": f"{variant}",
            "subtitle": f"smart_layout | {tag}",
            "intent": "explain",
            "layout": "blank",
            "image_layout": "blank",
            "slide_density": "balanced",
            "contentBlocks": [payload_block],
        }

        try:
            composed = composer.compose(payload)
            gyml_sections = serializer.serialize_many(composed)
            html_output = renderer.render_many(gyml_sections)
            entries.append((f"smart_layout:{variant}", tag, color, html_output))
        except Exception as e:
            errors.append(f"smart_layout:{variant} -> {e}")
            print(f"  [SKIP] smart_layout:{variant} -> {e}")

    # ── B. Render standalone block types ─────────────────────────────────────
    for family in STANDALONE_BLOCKS:
        items = generate_standalone_items(family)
        payload_block = {
            "type": family,
            "variant": "normal",
            "items": items,
            "hub_label": "Central Concept",
            "title": "Feature Showcase Title",
        }
        if family == "feature_showcase_block":
            payload_block["image_url"] = "placeholder"

        payload = {
            "title": family.replace("_", " ").title(),
            "subtitle": f"standalone | IN CATALOG",
            "intent": "explain",
            "layout": "blank",
            "image_layout": "blank",
            "slide_density": "balanced",
            "contentBlocks": [payload_block],
        }

        try:
            composed = composer.compose(payload)
            gyml_sections = serializer.serialize_many(composed)
            html_output = renderer.render_many(gyml_sections)
            entries.append((f"standalone:{family}", "STANDALONE", "#8b5cf6", html_output))
        except Exception as e:
            errors.append(f"standalone:{family} -> {e}")
            print(f"  [SKIP] standalone:{family} -> {e}")

    # ── C. Render non-smart_layout catalog families ─────────────────────────
    for key, spec in sorted(NON_SL_FAMILIES.items()):
        family, variant = key.split(":")
        if family in ("definition",):
            payload_block = {
                "type": "definition",
                "term": "Artificial Intelligence",
                "definition": "The simulation of human intelligence processes by machines."
            }
        elif family in ("formula",):
            payload_block = {
                "type": "formula_block",
                "expression": "E = mc^2",
                "variables": [
                    {"name": "E", "definition": "Energy"},
                    {"name": "m", "definition": "Mass"},
                    {"name": "c", "definition": "Speed of light"},
                ]
            }
        elif family in ("process", "comparison", "recap"):
            slv = spec.smart_layout_variant or "solidBoxesWithIconsInside"
            payload_block = {
                "type": "smart_layout",
                "variant": slv,
                "items": generate_smart_items(slv, 4),
            }
        elif family in ("title", "overview"):
            payload_block = {
                "type": "smart_layout",
                "variant": spec.smart_layout_variant or "diamondHub",
                "items": generate_smart_items("diamondHub", 4),
            }
        else:
            payload_block = {
                "type": "smart_layout",
                "variant": "solidBoxesWithIconsInside",
                "items": generate_smart_items("solidBoxesWithIconsInside", 3),
            }

        payload = {
            "title": f"{family} ({variant})",
            "subtitle": f"family alias | maps to: {spec.smart_layout_variant or 'N/A'}",
            "intent": "explain",
            "layout": "blank",
            "image_layout": "blank",
            "slide_density": "balanced",
            "contentBlocks": [payload_block],
        }

        try:
            composed = composer.compose(payload)
            gyml_sections = serializer.serialize_many(composed)
            html_output = renderer.render_many(gyml_sections)
            entries.append((f"family:{key}", "FAMILY ALIAS", "#06b6d4", html_output))
        except Exception as e:
            errors.append(f"family:{key} -> {e}")
            print(f"  [SKIP] family:{key} -> {e}")

    # ── Build the interactive HTML ──────────────────────────────────────────
    options_html = ""
    divs_html = ""
    for idx, (key, tag, color, html) in enumerate(entries):
        display = "block" if idx == 0 else "none"
        badge = f'<span style="background:{color};color:#fff;padding:2px 8px;border-radius:4px;font-size:11px;margin-left:8px;">{tag}</span>'
        options_html += f'<option value="slide-{idx}" data-tag="{tag}" data-color="{color}">{key}</option>\n'
        divs_html += f'<div id="slide-{idx}" class="slide-container" style="display:{display};">{html}</div>\n'

    gamma_styles = get_slide_css("__all__", selected_theme)
    responsive = renderer._get_responsive_styles()

    # Count stats for the header
    both_count = sum(1 for _,t,_,_ in entries if t == "BOTH")
    catalog_only = sum(1 for _,t,_,_ in entries if t == "CATALOG ONLY")
    renderer_only = sum(1 for _,t,_,_ in entries if t == "RENDERER ONLY")
    standalone_count = sum(1 for _,t,_,_ in entries if t == "STANDALONE")
    alias_count = sum(1 for _,t,_,_ in entries if t == "FAMILY ALIAS")
    error_count = len(errors)

    final_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GyML Audit Sandbox</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/remixicon@4.2.0/fonts/remixicon.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
    <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
    <style>
        * {{ box-sizing: border-box; }}
        body {{
            margin: 0;
            padding: 0;
            font-family: 'Inter', sans-serif;
            background: #020617;
            color: #f8fafc;
            display: flex;
            flex-direction: column;
            height: 100vh;
            overflow: hidden;
        }}

        /* ── Top Control Bar ─────────────────────────────────────── */
        .controls {{
            background: #0f172a;
            padding: 12px 24px;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.5);
            display: flex;
            align-items: center;
            gap: 16px;
            z-index: 1000;
            border-bottom: 1px solid #1e293b;
            flex-wrap: wrap;
        }}
        .controls label {{
            font-size: 14px;
            font-weight: 600;
            white-space: nowrap;
        }}
        .controls select {{
            padding: 8px 12px;
            font-size: 14px;
            border-radius: 8px;
            border: 1px solid #334155;
            background: #1e293b;
            color: #f8fafc;
            outline: none;
            cursor: pointer;
            min-width: 340px;
            flex: 1;
        }}
        .status-badge {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 0.5px;
            text-transform: uppercase;
        }}
        .filter-btn {{
            padding: 6px 14px;
            border-radius: 6px;
            border: 1px solid #334155;
            background: transparent;
            color: #94a3b8;
            cursor: pointer;
            font-size: 12px;
            font-weight: 600;
            transition: all 0.2s;
        }}
        .filter-btn:hover, .filter-btn.active {{
            background: #1e40af;
            color: #fff;
            border-color: #1e40af;
        }}

        /* ── Stats Bar ───────────────────────────────────────────── */
        .stats-bar {{
            background: #0f172a;
            padding: 8px 24px;
            display: flex;
            gap: 16px;
            font-size: 12px;
            border-bottom: 1px solid #1e293b;
            flex-wrap: wrap;
        }}
        .stat-chip {{
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        .stat-dot {{
            width: 8px;
            height: 8px;
            border-radius: 50%;
            display: inline-block;
        }}

        /* ── Navigation ──────────────────────────────────────────── */
        .nav-controls {{
            display: flex;
            gap: 8px;
            align-items: center;
        }}
        .nav-btn {{
            padding: 6px 12px;
            border-radius: 6px;
            border: 1px solid #334155;
            background: #1e293b;
            color: #f8fafc;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.15s;
        }}
        .nav-btn:hover {{
            background: #334155;
        }}
        .counter {{
            font-size: 13px;
            color: #94a3b8;
            min-width: 60px;
            text-align: center;
        }}

        /* ── Viewer ──────────────────────────────────────────────── */
        .viewer {{
            flex: 1;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 16px;
            overflow: hidden;
        }}
        .mock-browser {{
            width: 100%;
            max-width: 1200px;
            height: 100%;
            max-height: 800px;
            background: #0a0f1a;
            border-radius: 12px;
            box-shadow: 0 20px 25px -5px rgba(0,0,0,0.5);
            overflow: hidden;
            border: 1px solid #1e293b;
        }}
        .slide-container {{
            width: 100%;
            height: 100%;
            overflow-y: auto;
        }}

        /* ── GyML Engine Styles ──────────────────────────────────── */
        {gamma_styles}
        {responsive}

        .gyml-deck {{ height: 100%; }}
        .slide-section {{ height: 100% !important; }}
    </style>
</head>
<body>
    <div class="controls">
        <label for="block-select"><i class="ri-layout-grid-line"></i> Block:</label>
        <select id="block-select" onchange="switchBlock(this.value)">
            {options_html}
        </select>
        <div id="status-badge" class="status-badge" style="background:#22c55e;">BOTH</div>
        <div class="nav-controls">
            <button class="nav-btn" onclick="navPrev()" title="Previous"><i class="ri-arrow-left-s-line"></i></button>
            <span class="counter" id="counter">1 / {len(entries)}</span>
            <button class="nav-btn" onclick="navNext()" title="Next"><i class="ri-arrow-right-s-line"></i></button>
        </div>
    </div>
    <div class="stats-bar">
        <span class="stat-chip"><span class="stat-dot" style="background:#22c55e;"></span> Both: {both_count}</span>
        <span class="stat-chip"><span class="stat-dot" style="background:#f59e0b;"></span> Catalog Only: {catalog_only}</span>
        <span class="stat-chip"><span class="stat-dot" style="background:#ef4444;"></span> Renderer Only: {renderer_only}</span>
        <span class="stat-chip"><span class="stat-dot" style="background:#8b5cf6;"></span> Standalone: {standalone_count}</span>
        <span class="stat-chip"><span class="stat-dot" style="background:#06b6d4;"></span> Family Alias: {alias_count}</span>
        <span class="stat-chip"><span class="stat-dot" style="background:#64748b;"></span> Errors: {error_count}</span>
        <span style="margin-left:auto;">
            <button class="filter-btn active" onclick="filterBy('ALL')">All</button>
            <button class="filter-btn" onclick="filterBy('BOTH')">Both</button>
            <button class="filter-btn" onclick="filterBy('CATALOG ONLY')">Catalog Only</button>
            <button class="filter-btn" onclick="filterBy('RENDERER ONLY')">Renderer Only</button>
            <button class="filter-btn" onclick="filterBy('STANDALONE')">Standalone</button>
            <button class="filter-btn" onclick="filterBy('FAMILY ALIAS')">Family Alias</button>
        </span>
    </div>

    <div class="viewer">
        <div class="mock-browser">
            <div class="gyml-deck">
                {divs_html}
            </div>
        </div>
    </div>

    <script>
        const select = document.getElementById('block-select');
        const badge = document.getElementById('status-badge');
        const counterEl = document.getElementById('counter');
        const allOptions = Array.from(select.options);
        let currentFilter = 'ALL';

        function switchBlock(targetId) {{
            document.querySelectorAll('.slide-container').forEach(el => {{
                el.style.display = 'none';
            }});
            const target = document.getElementById(targetId);
            if (target) target.style.display = 'block';

            // Update badge
            const opt = select.options[select.selectedIndex];
            if (opt) {{
                badge.textContent = opt.dataset.tag;
                badge.style.background = opt.dataset.color;
            }}
            updateCounter();
        }}

        function updateCounter() {{
            const visibleOpts = Array.from(select.options);
            const idx = select.selectedIndex + 1;
            counterEl.textContent = idx + ' / ' + visibleOpts.length;
        }}

        function navPrev() {{
            if (select.selectedIndex > 0) {{
                select.selectedIndex--;
                switchBlock(select.value);
            }}
        }}

        function navNext() {{
            if (select.selectedIndex < select.options.length - 1) {{
                select.selectedIndex++;
                switchBlock(select.value);
            }}
        }}

        function filterBy(tag) {{
            // Update filter buttons
            document.querySelectorAll('.filter-btn').forEach(btn => {{
                btn.classList.toggle('active', btn.textContent.trim() === tag || (tag === 'ALL' && btn.textContent.trim() === 'All'));
            }});
            currentFilter = tag;

            // Rebuild select options
            select.innerHTML = '';
            allOptions.forEach(opt => {{
                if (tag === 'ALL' || opt.dataset.tag === tag) {{
                    select.appendChild(opt.cloneNode(true));
                }}
            }});

            if (select.options.length > 0) {{
                select.selectedIndex = 0;
                switchBlock(select.value);
            }}
        }}

        // Keyboard navigation
        document.addEventListener('keydown', (e) => {{
            if (e.key === 'ArrowLeft') navPrev();
            if (e.key === 'ArrowRight') navNext();
        }});

        // Initial counter
        updateCounter();
    </script>
</body>
</html>"""

    output_path = os.path.join(SCRIPT_DIR, "interactive_sandbox.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(final_html)

    print(f"[OK] Created interactive_sandbox.html")
    print(f"     Total entries: {len(entries)}")
    print(f"       BOTH (catalog+renderer): {both_count}")
    print(f"       CATALOG ONLY: {catalog_only}")
    print(f"       RENDERER ONLY: {renderer_only}")
    print(f"       STANDALONE: {standalone_count}")
    print(f"       FAMILY ALIAS: {alias_count}")
    print(f"     Errors/Skipped: {error_count}")
    if errors:
        print(f"     Error details:")
        for e in errors:
            print(f"       - {e}")


if __name__ == "__main__":
    main()
