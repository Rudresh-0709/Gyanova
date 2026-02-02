"""
Test multi-column and space-aware layouts.

Demonstrates how blocks can utilize horizontal space better.
"""

import sys
from pathlib import Path

# Add blocks to path
sys.path.insert(0, str(Path(__file__).parent / "slides" / "blocks"))

from block_slide_renderer import render_block_slide


# Test 1: Multi-column bullet list (4 items → 2 columns)
test_columns_bullets = {
    "intent": "Demonstrate multi-column bullet list",
    "sections": [
        {
            "purpose": "content",
            "blocks": [
                {"type": "heading", "text": "Key Features", "level": 1},
                {
                    "type": "bullet_list",
                    "columns": 2,  # Split into 2 columns
                    "items": [
                        "Fast processing with modern CPUs",
                        "Large memory capacity for multitasking",
                        "Energy-efficient design for portability",
                        "Advanced graphics for gaming and design",
                    ],
                },
            ],
        }
    ],
}

# Test 2: Two-column section layout (left: bullets, right: cards)
test_two_column_section = {
    "intent": "Show content side-by-side",
    "sections": [
        {
            "purpose": "introduction",
            "blocks": [
                {"type": "heading", "text": "Computer Generations", "level": 1},
                {
                    "type": "paragraph",
                    "text": "Evolution across five distinct technological eras.",
                },
            ],
        },
        {
            "purpose": "content",
            "layout": "two-column",  # Side-by-side layout
            "blocks": [
                # Left column
                {
                    "type": "bullet_list",
                    "style": "numbered",
                    "items": [
                        "First: Vacuum tubes (1940s)",
                        "Second: Transistors (1950s)",
                        "Third: Integrated circuits (1960s)",
                        "Fourth: Microprocessors (1970s)",
                        "Fifth: AI systems (2020s)",
                    ],
                },
                # Right column
                {
                    "type": "card_grid",
                    "cards": [
                        {
                            "icon": "ri-speed-line",
                            "heading": "Speed",
                            "text": "10,000x faster than first generation",
                        },
                        {
                            "icon": "ri-money-dollar-circle-line",
                            "heading": "Cost",
                            "text": "1/1000th the price per calculation",
                        },
                    ],
                },
            ],
        },
    ],
}

# Test 3: Dense content that fits in viewport
test_dense_content = {
    "intent": "Maximum content without overflow",
    "sections": [
        {
            "purpose": "content",
            "blocks": [
                {"type": "heading", "text": "Computer Evolution Summary", "level": 1},
                {
                    "type": "bullet_list",
                    "columns": 3,  # 3 columns for dense content
                    "items": [
                        "Vacuum tubes",
                        "Transistors",
                        "ICs",
                        "Microprocessors",
                        "AI chips",
                        "Quantum computing",
                    ],
                },
                {"type": "divider"},
                {
                    "type": "card_grid",
                    "cards": [
                        {
                            "icon": "ri-arrow-up-line",
                            "heading": "Performance",
                            "text": "Exponential growth",
                        },
                        {
                            "icon": "ri-arrow-down-line",
                            "heading": "Size",
                            "text": "Miniaturization",
                        },
                        {
                            "icon": "ri-wallet-line",
                            "heading": "Cost",
                            "text": "Dramatic reduction",
                        },
                    ],
                },
                {
                    "type": "takeaway",
                    "text": "Each generation brought revolutionary improvements in all metrics.",
                },
            ],
        }
    ],
}

# Test 4: Comparison - same content, different layouts
test_comparison = {
    "intent": "Show layout flexibility",
    "sections": [
        {
            "purpose": "introduction",
            "blocks": [
                {"type": "heading", "text": "Generation Comparison", "level": 1}
            ],
        },
        {
            "purpose": "content",
            "layout": "two-column",
            "blocks": [
                # Left: Step list
                {
                    "type": "step_list",
                    "steps": [
                        {"number": "01", "text": "Vacuum tubes - Room-sized machines"},
                        {"number": "02", "text": "Transistors - Desk-sized computers"},
                        {"number": "03", "text": "ICs - Personal computers"},
                    ],
                },
                # Right: Bullet list
                {
                    "type": "bullet_list",
                    "style": "unnumbered",
                    "items": [
                        "Size decreased exponentially",
                        "Speed increased dramatically",
                        "Cost became affordable",
                        "Accessibility improved widely",
                    ],
                },
            ],
        },
    ],
}

# Render all tests
tests = [
    ("columns_bullets", test_columns_bullets),
    ("two_column_section", test_two_column_section),
    ("dense_content", test_dense_content),
    ("comparison_layout", test_comparison),
]

output_dir = Path(__file__).parent / "test_rendered_slides"
output_dir.mkdir(parents=True, exist_ok=True)

for name, data in tests:
    html = render_block_slide(data)
    output_path = output_dir / f"space_test_{name}.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ Generated: {name} → {output_path.name}")

print(f"\n🎉 All {len(tests)} space-aware test slides generated!")
print(f"📂 Output directory: {output_dir}")
