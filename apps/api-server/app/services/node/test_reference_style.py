"""
Create test slides that match the reference style:
- 2x2 grids (like "Why This Problem Is Hard")
- Two-column text (like "The Early Discovery Challenge")
- Hero images + content (like "Introducing Redevo")
- Dark card variants (like "Introducing Redevo")
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "slides" / "blocks"))

from block_slide_renderer import render_block_slide


# Example 1: 2x2 Grid with Takeaway (matches "Why This Problem Is Hard")
example_grid_2x2 = {
    "intent": "Explain challenges with proper 2x2 layout",
    "sections": [
        {
            "purpose": "content",
            "blocks": [
                {"type": "heading", "text": "Why This Problem Is Hard", "level": 1},
                {
                    "type": "card_grid",
                    "cards": [
                        {
                            "number": "1",
                            "icon": "ri-database-line",
                            "heading": "No Single Source",
                            "text": "There's no authoritative, centralized database tracking new projects. Information exists in fragments across disconnected sources.",
                        },
                        {
                            "number": "2",
                            "icon": "ri-time-line",
                            "heading": "Pre-Market Timing",
                            "text": "Projects emerge months before inventory is marketed publicly. Traditional portals miss this critical early window entirely.",
                        },
                        {
                            "number": "3",
                            "icon": "ri-stack-line",
                            "heading": "Data Complexity",
                            "text": "Project data is semi-structured, often delayed, sometimes hidden, and rarely standardized across sources.",
                        },
                        {
                            "number": "4",
                            "icon": "ri-speed-line",
                            "heading": "Rapid Changes",
                            "text": "Project availability, pricing, and specifications shift too quickly for manual tracking methods to remain reliable.",
                        },
                    ],
                },
                {
                    "type": "takeaway",
                    "label": "Key Insight",
                    "text": "This is an intelligence problem, not a listing problem. Humans can't monitor 50 fragmented sources daily. Machines can.",
                },
            ],
        }
    ],
}

# Example 2: Two-Column Text Layout (matches "The Early Discovery Challenge")
example_two_column_text = {
    "intent": "Show problem vs cost comparison",
    "sections": [
        {
            "purpose": "introduction",
            "blocks": [
                {"type": "heading", "text": "The Early Discovery Challenge", "level": 1}
            ],
        },
        {
            "purpose": "content",
            "layout": "two-column",
            "blocks": [
                # Left column
                {"type": "heading", "text": "The Reality Today", "level": 2},
                {
                    "type": "paragraph",
                    "text": "A broker hears about a redevelopment project 3 months late—not because it didn't exist, but because it never showed up on portals.",
                },
                # Right column
                {"type": "heading", "text": "The Cost", "level": 2},
                {
                    "type": "paragraph",
                    "text": "Property portals focus exclusively on available inventory—listings ready to sell—not emerging project discovery.\n\nThe result? Missed opportunities, wasted hours, and persistent information asymmetry between those in the know and everyone else.",
                },
            ],
        },
    ],
}

# Example 3: Step List + Sidebar (matches "What Redevo Does Today")
example_steps_with_sidebar = {
    "intent": "Show features with visual hierarchy",
    "sections": [
        {
            "purpose": "introduction",
            "blocks": [
                {"type": "heading", "text": "What Redevo Does Today", "level": 1}
            ],
        },
        {
            "purpose": "content",
            "blocks": [
                # Steps
                {
                    "type": "step_list",
                    "steps": [
                        {
                            "number": "01",
                            "text": "Detects Projects Early - Identifies newly built and redevelopment projects as they emerge",
                        },
                        {
                            "number": "02",
                            "text": "Extracts Structured Data - Converts fragmented information into organized, searchable profiles",
                        },
                        {
                            "number": "03",
                            "text": "Validates Using Multiple Signals - Cross-references sources to ensure accuracy and reliability",
                        },
                        {
                            "number": "04",
                            "text": "Surfaces Intelligence - Delivers timely alerts on projects matching your criteria",
                        },
                    ],
                },
                {"type": "divider"},
                # Sidebar content BELOW, not side-by-side
                {"type": "heading", "text": "What We Don't Do", "level": 3},
                {
                    "type": "bullet_list",
                    "style": "unnumbered",
                    "items": [
                        "Promise real-time flat availability",
                        "Act as a broker or transactional marketplace",
                        "Compete with property listing portals",
                    ],
                },
                {
                    "type": "paragraph",
                    "text": "We avoid these deliberately to stay accurate, neutral, and trusted.",
                },
            ],
        },
    ],
}

# Example 4: Dark Cards (matches "Introducing Redevo")
example_dark_cards = {
    "intent": "Introduce solution with visual impact",
    "sections": [
        {
            "purpose": "introduction",
            "blocks": [
                {"type": "heading", "text": "Introducing Redevo", "level": 1},
                {
                    "type": "paragraph",
                    "text": "Redevo automatically discovers and tracks newly built and redevelopment projects before they become mainstream.",
                },
            ],
        },
        {
            "purpose": "content",
            "blocks": [
                {
                    "type": "card_grid",
                    "cards": [
                        {
                            "icon": "ri-robot-line",
                            "heading": "AI-Driven Discovery",
                            "text": "Machine learning algorithms continuously scan and validate emerging projects",
                            "variant": "dark",
                        },
                        {
                            "icon": "ri-file-list-line",
                            "heading": "Structured Intelligence",
                            "text": "Raw data transformed into queryable, actionable project profiles",
                            "variant": "dark",
                        },
                        {
                            "icon": "ri-map-pin-line",
                            "heading": "Deep City Coverage",
                            "text": "Comprehensive mapping of development activity, neighborhood by neighborhood",
                            "variant": "dark",
                        },
                        {
                            "icon": "ri-shield-check-line",
                            "heading": "Neutral Platform",
                            "text": "Non-advertisement driven, delivering unbiased project intelligence",
                            "variant": "dark",
                        },
                    ],
                },
                {
                    "type": "takeaway",
                    "text": "Redevo tracks projects, not daily sales inventory.",
                },
            ],
        },
    ],
}

# Render all examples
examples = [
    ("grid_2x2", example_grid_2x2),
    ("two_column_text", example_two_column_text),
    ("steps_sidebar", example_steps_with_sidebar),
    ("dark_cards", example_dark_cards),
]

output_dir = Path(__file__).parent / "test_rendered_slides"

for name, data in examples:
    html = render_block_slide(data)
    output_path = output_dir / f"reference_style_{name}.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ Generated: {name} → {output_path.name}")

print(f"\n🎨 All {len(examples)} reference-style slides generated!")
