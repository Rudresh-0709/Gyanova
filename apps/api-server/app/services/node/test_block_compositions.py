"""
Test the block-based slide system with various compositions.

Demonstrates the flexibility of composing different block types.
"""

import sys
from pathlib import Path

# Add blocks to path
sys.path.insert(0, str(Path(__file__).parent / "slides" / "blocks"))

from block_slide_renderer import render_block_slide


# Test 1: Simple slide (like template system)
test_simple = {
    "intent": "Explain computer generations",
    "sections": [
        {
            "purpose": "content",
            "blocks": [
                {"type": "heading", "text": "Computer Generations", "level": 1},
                {
                    "type": "card_grid",
                    "cards": [
                        {
                            "icon": "ri-computer-line",
                            "heading": "First Generation",
                            "number": 1,
                            "text": "Vacuum tubes and magnetic drums for memory.",
                        },
                        {
                            "icon": "ri-cpu-line",
                            "heading": "Second Generation",
                            "number": 2,
                            "text": "Transistors replaced vacuum tubes for processing.",
                        },
                        {
                            "icon": "ri-chip-line",
                            "heading": "Third Generation",
                            "number": 3,
                            "text": "Integrated circuits led to smaller size and reduced cost.",
                        },
                    ],
                },
            ],
        }
    ],
}

# Test 2: Rich composition (demonstrates flexibility)
test_rich = {
    "intent": "Explain computer generations with context and takeaway",
    "sections": [
        {
            "purpose": "introduction",
            "blocks": [
                {"type": "heading", "text": "Computer Generations", "level": 1},
                {"type": "divider"},
                {
                    "type": "paragraph",
                    "text": "Understanding computer generations helps us appreciate how modern computing evolved from room-sized machines to pocket devices.",
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
                            "icon": "ri-computer-line",
                            "heading": "First (1940s-1950s)",
                            "text": "Vacuum tubes, magnetic drums. Room-sized, expensive, unreliable.",
                        },
                        {
                            "icon": "ri-cpu-line",
                            "heading": "Second (1950s-1960s)",
                            "text": "Transistors enabled smaller, faster, cooler machines.",
                        },
                        {
                            "icon": "ri-chip-line",
                            "heading": "Third (1960s-1970s)",
                            "text": "Integrated circuits brought mass production and affordability.",
                        },
                        {
                            "icon": "ri-computer-line",
                            "heading": "Fourth (1970s-Present)",
                            "text": "Microprocessors enabled personal computers.",
                        },
                        {
                            "icon": "ri-robot-line",
                            "heading": "Fifth (Present-Future)",
                            "text": "AI and ML define the current generation.",
                        },
                    ],
                },
                {
                    "type": "takeaway",
                    "text": "Each generation brought 10-100x improvements in speed, size, and cost efficiency.",
                },
            ],
        },
    ],
}

# Test 3: Mixed blocks (shows composition power)
test_mixed = {
    "intent": "Teach computer generation progression with steps",
    "sections": [
        {
            "purpose": "introduction",
            "blocks": [
                {"type": "heading", "text": "Evolution of Computing", "level": 1},
                {
                    "type": "paragraph",
                    "text": "Five generations of revolutionary technological change:",
                },
            ],
        },
        {
            "purpose": "content",
            "blocks": [
                {
                    "type": "step_list",
                    "steps": [
                        {
                            "number": "01",
                            "text": "Vacuum tubes created the first programmable computers (1940s)",
                        },
                        {
                            "number": "02",
                            "text": "Transistors reduced size and improved reliability (1950s)",
                        },
                        {
                            "number": "03",
                            "text": "Integrated circuits enabled mass production (1960s)",
                        },
                        {
                            "number": "04",
                            "text": "Microprocessors brought computing to individuals (1970s)",
                        },
                        {
                            "number": "05",
                            "text": "AI systems now surpass human capabilities in specific tasks (2020s)",
                        },
                    ],
                },
                {"type": "divider"},
                {
                    "type": "bullet_list",
                    "style": "unnumbered",
                    "items": [
                        "Each generation built on previous innovations",
                        "Performance improved exponentially (Moore's Law)",
                        "Cost decreased while capabilities increased",
                    ],
                },
            ],
        },
    ],
}

# Test 4: Minimal (just cards, like current template)
test_minimal = {
    "intent": "Show computer generations simply",
    "sections": [
        {
            "purpose": "content",
            "blocks": [
                {
                    "type": "heading",
                    "text": "Summary of Computer Generations",
                    "level": 1,
                },
                {
                    "type": "card_grid",
                    "cards": [
                        {
                            "icon": "ri-computer-line",
                            "heading": "Defining Computer Generations",
                            "text": "Each generation is marked by major technological advances, from vacuum tubes to artificial intelligence.",
                        },
                        {
                            "icon": "ri-cpu-line",
                            "heading": "Key Technological Advances",
                            "text": "Generations progressed from vacuum tubes to transistors, integrated circuits, microprocessors, and AI.",
                        },
                        {
                            "icon": "ri-arrow-up-line",
                            "heading": "Improvements Over Time",
                            "text": "Computers became faster, smaller, more reliable, and more efficient with each generation.",
                        },
                        {
                            "icon": "ri-arrow-right-line",
                            "heading": "Understanding Evolution",
                            "text": "Knowing generation differences shows how computing technology has evolved and impacts our world today.",
                        },
                        {
                            "icon": "ri-book-line",
                            "heading": "Foundation for Learning",
                            "text": "Remembering main features of each generation builds a strong base for exploring advanced computer concepts.",
                        },
                    ],
                },
                {
                    "type": "takeaway",
                    "text": "Understanding computer generations provides essential context for how modern technology evolved.",
                },
            ],
        }
    ],
}

# Render all tests
tests = [
    ("simple", test_simple),
    ("rich", test_rich),
    ("mixed", test_mixed),
    ("minimal", test_minimal),
]

output_dir = Path(__file__).parent / "test_rendered_slides"
output_dir.mkdir(parents=True, exist_ok=True)

for name, data in tests:
    html = render_block_slide(data)
    output_path = output_dir / f"block_test_{name}.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ Generated: {name} → {output_path.name}")

print(f"\n🎉 All {len(tests)} test slides generated successfully!")
print(f"📂 Output directory: {output_dir}")
