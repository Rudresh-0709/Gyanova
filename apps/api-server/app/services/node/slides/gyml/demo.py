"""
GyML Pipeline Demo

Demonstrates the full Composition → Serialization → Validation → Rendering pipeline.
Run this script from the slides directory: python gyml/demo.py
Or run: python -m gyml.demo
"""

import os
import sys

# Ensure we import from the parent directory
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from gyml.composer import SlideComposer
from gyml.serializer import GyMLSerializer
from gyml.validator import GyMLValidator
from gyml.renderer import GyMLRenderer
from gyml.theme import THEMES, get_theme


def create_output_dir():
    """Create output directory if it doesn't exist."""
    # Output in the slides directory, not gyml
    slides_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = os.path.join(slides_dir, "output", "gyml_demos")
    os.makedirs(output_dir, exist_ok=True)
    return output_dir


def example_1_simple_explanation():
    """Simple explanation slide."""
    return {
        "title": "What is Machine Learning?",
        "intent": "explain",
        "points": [
            "Machine learning is a subset of artificial intelligence",
            "It enables computers to learn from data without explicit programming",
            "Algorithms improve automatically through experience",
            "Used in recommendations, image recognition, and more",
        ],
    }


def example_2_timeline():
    """Timeline slide."""
    return {
        "title": "Evolution of Computing",
        "intent": "narrate",
        "contentBlocks": [
            {
                "type": "timeline",
                "events": [
                    {
                        "year": "1940s",
                        "description": "First electronic computers using vacuum tubes",
                    },
                    {
                        "year": "1960s",
                        "description": "Transistors replace tubes, computers become smaller",
                    },
                    {
                        "year": "1980s",
                        "description": "Personal computers enter homes and offices",
                    },
                    {
                        "year": "2000s",
                        "description": "Mobile computing and smartphones emerge",
                    },
                ],
            }
        ],
    }


def example_3_comparison():
    """Comparison slide with columns."""
    return {
        "title": "Python vs JavaScript",
        "intent": "compare",
        "contentBlocks": [
            {
                "type": "columns",
                "widths": [50, 50],
                "columns": [
                    [
                        {"type": "heading", "content": {"text": "Python", "level": 2}},
                        {
                            "type": "bullet_list",
                            "content": {
                                "items": [
                                    "Great for data science",
                                    "Clean syntax",
                                    "Strong in AI/ML",
                                ]
                            },
                        },
                    ],
                    [
                        {
                            "type": "heading",
                            "content": {"text": "JavaScript", "level": 2},
                        },
                        {
                            "type": "bullet_list",
                            "content": {
                                "items": [
                                    "Runs in browsers",
                                    "Full-stack capable",
                                    "Huge ecosystem",
                                ]
                            },
                        },
                    ],
                ],
            }
        ],
    }


def example_4_stats():
    """Stats grid slide."""
    return {
        "title": "Platform Performance",
        "intent": "persuade",
        "contentBlocks": [
            {
                "type": "stats_grid",
                "stats": [
                    {"value": "99.9%", "label": "Uptime"},
                    {"value": "500K+", "label": "Active Users"},
                    {"value": "<50ms", "label": "Response Time"},
                    {"value": "24/7", "label": "Support"},
                ],
            }
        ],
    }


def example_5_card_grid():
    """Card grid slide."""
    return {
        "title": "Our Core Features",
        "intent": "explain",
        "contentBlocks": [
            {
                "type": "card_grid",
                "cards": [
                    {
                        "icon": "ri-shield-check",
                        "heading": "Secure",
                        "text": "Enterprise-grade security with end-to-end encryption",
                    },
                    {
                        "icon": "ri-speed-line",
                        "heading": "Fast",
                        "text": "Optimized performance with global CDN",
                    },
                    {
                        "icon": "ri-team-line",
                        "heading": "Collaborative",
                        "text": "Real-time collaboration for teams of any size",
                    },
                    {
                        "icon": "ri-plug-line",
                        "heading": "Extensible",
                        "text": "Rich API and integration ecosystem",
                    },
                ],
            }
        ],
    }


def example_6_complete_slide():
    """Complete slide with multiple sections."""
    return {
        "title": "Introduction to Neural Networks",
        "intent": "explain",
        "sections": [
            {
                "purpose": "introduction",
                "blocks": [
                    {
                        "type": "heading",
                        "content": {
                            "text": "Introduction to Neural Networks",
                            "level": 1,
                        },
                    },
                    {
                        "type": "paragraph",
                        "content": {
                            "text": "Understanding the building blocks of deep learning"
                        },
                    },
                ],
            },
            {
                "purpose": "content",
                "blocks": [
                    {
                        "type": "smart_layout",
                        "content": {
                            "variant": "bigBullets",
                            "items": [
                                {
                                    "icon": "ri-brain-line",
                                    "text": "Inspired by biological neurons",
                                },
                                {
                                    "icon": "ri-stack-line",
                                    "text": "Organized in layers",
                                },
                                {
                                    "icon": "ri-links-line",
                                    "text": "Connected by weighted edges",
                                },
                                {
                                    "icon": "ri-loop-left-line",
                                    "text": "Learn through backpropagation",
                                },
                            ],
                        },
                    }
                ],
            },
            {
                "purpose": "takeaway",
                "blocks": [
                    {
                        "type": "takeaway",
                        "content": {
                            "label": "Key Insight",
                            "text": "Neural networks transform inputs through layers of mathematical operations to produce meaningful outputs.",
                        },
                    }
                ],
            },
        ],
    }


def run_pipeline(
    content: dict, name: str, output_dir: str, theme_name: str = "midnight"
):
    """Run the full GyML pipeline for a single content example."""
    print(f"\n{'='*60}")
    print(f"Processing: {name}")
    print(f"{'='*60}")

    # 1. Compose (GyML-agnostic)
    print("1. Composing slide...")
    composer = SlideComposer()
    composed_slides = composer.compose(content)
    print(f"   -> Created {len(composed_slides)} slide(s)")

    for slide in composed_slides:
        print(
            f"   -> Slide {slide.id}: {len(slide.sections)} sections, {slide.block_count()} blocks"
        )

    # 2. Serialize to GyML
    print("2. Serializing to GyML...")
    serializer = GyMLSerializer()
    gyml_sections = serializer.serialize_many(composed_slides)
    print(f"   -> Generated {len(gyml_sections)} GyML section(s)")

    # 3. Validate
    print("3. Validating GyML...")
    validator = GyMLValidator()
    result = validator.validate_many(gyml_sections)

    if result.is_valid:
        print("   -> [OK] Validation passed")
    else:
        print("   -> [FAIL] Validation failed:")
        for error in result.errors:
            print(f"      - {error}")

    if result.warnings:
        print("   -> [WARN] Warnings:")
        for warning in result.warnings:
            print(f"      - {warning}")

    # 4. Render (passive)
    print(f"4. Rendering with theme '{theme_name}'...")
    theme = get_theme(theme_name)
    renderer = GyMLRenderer(theme=theme)
    html = renderer.render_complete(gyml_sections)
    print(f"   -> Generated {len(html)} characters of HTML")

    # 5. Save output
    output_path = os.path.join(output_dir, f"{name}.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"5. Saved to: {output_path}")

    return True


def main():
    """Generate all example slides."""
    output_dir = create_output_dir()

    print("GyML Pipeline Demo")
    print("=" * 60)
    print(f"Output directory: {output_dir}")

    examples = [
        ("simple_explanation", example_1_simple_explanation(), "midnight"),
        ("timeline", example_2_timeline(), "ocean"),
        ("comparison", example_3_comparison(), "corporate"),
        ("stats", example_4_stats(), "dark_purple"),
        ("card_grid", example_5_card_grid(), "forest"),
        ("complete_slide", example_6_complete_slide(), "midnight"),
    ]

    success_count = 0
    for name, content, theme in examples:
        try:
            if run_pipeline(content, name, output_dir, theme):
                success_count += 1
        except Exception as e:
            print(f"   -> [ERROR]: {e}")
            import traceback

            traceback.print_exc()

    print(f"\n{'='*60}")
    print(f"Generated {success_count}/{len(examples)} slides successfully!")
    print(f"Open any HTML file in: {output_dir}")
    print("=" * 60)


if __name__ == "__main__":
    main()
