"""
Verification script for Expanded Content Schema.
Tests rendering of:
1. Comparison
2. Code Block
3. Table
4. Quote
5. Definition
"""

import os
from gyml.types import ComposedSlide, ComposedSection, ComposedBlock
from gyml.constants import BlockType, Intent, SmartLayoutVariant
from gyml.serializer import GyMLSerializer
from gyml.renderer import GyMLRenderer


def create_comparison_slide():
    return ComposedSlide(
        id="slide-comparison",
        intent=Intent.COMPARE.value,
        sections=[
            ComposedSection(
                purpose="content",
                blocks=[
                    ComposedBlock(
                        type=BlockType.HEADING.value,
                        content={"text": "Architecture Comparison", "level": 1},
                    ),
                    ComposedBlock(
                        type=BlockType.COMPARISON.value,
                        content={
                            "variant": "comparison",
                            "left": {
                                "label": "Monolithic",
                                "points": [
                                    "Single codebase",
                                    "Hard to scale",
                                    "Single failure point",
                                ],
                            },
                            "right": {
                                "label": "Microservices",
                                "points": [
                                    "Decoupled services",
                                    "Independent scaling",
                                    "Complex deployment",
                                ],
                            },
                        },
                    ),
                ],
            )
        ],
    )


def create_code_slide():
    return ComposedSlide(
        id="slide-code",
        intent=Intent.TEACH.value,
        sections=[
            ComposedSection(
                purpose="content",
                blocks=[
                    ComposedBlock(
                        type=BlockType.HEADING.value,
                        content={"text": "Python Implementation", "level": 1},
                    ),
                    ComposedBlock(
                        type=BlockType.CODE.value,
                        content={
                            "code": "def hello_world():\n    print('Hello GyML!')\n    return True",
                            "language": "python",
                            "variant": "snippet",
                        },
                    ),
                    ComposedBlock(
                        type=BlockType.CALLOUT.value,
                        content={"text": "Clean and readable code.", "label": "Note"},
                    ),
                ],
            )
        ],
    )


def create_table_slide():
    return ComposedSlide(
        id="slide-table",
        intent=Intent.COMPARE.value,
        sections=[
            ComposedSection(
                purpose="content",
                blocks=[
                    ComposedBlock(
                        type=BlockType.HEADING.value,
                        content={"text": "Feature Matrix", "level": 1},
                    ),
                    ComposedBlock(
                        type=BlockType.TABLE.value,
                        content={
                            "variant": "striped",
                            "headers": ["Feature", "Basic", "Pro", "Enterprise"],
                            "rows": [
                                ["Users", "1", "5", "Unlimited"],
                                ["Storage", "5GB", "50GB", "1TB"],
                                ["Support", "Email", "Priority", "24/7 Dedicated"],
                            ],
                        },
                    ),
                ],
            )
        ],
    )


def create_quote_slide():
    return ComposedSlide(
        id="slide-quote",
        intent=Intent.PROVE.value,
        sections=[
            ComposedSection(
                purpose="content",
                blocks=[
                    ComposedBlock(
                        type=BlockType.HEADING.value,
                        content={"text": "User Feedback", "level": 1},
                    ),
                    ComposedBlock(
                        type=BlockType.QUOTE.value,
                        content={
                            "text": "The new architecture cut our build times by 50%. It's a game changer.",
                            "author": "Jane Doe",
                            "source": "CTO, TechCorp",
                            "variant": "quote",
                        },
                    ),
                ],
            )
        ],
    )


def main():
    slides = [
        create_comparison_slide(),
        create_code_slide(),
        create_table_slide(),
        create_quote_slide(),
    ]

    serializer = GyMLSerializer()
    renderer = GyMLRenderer()

    gyml_sections = serializer.serialize_many(slides)
    html_output = renderer.render_complete(gyml_sections)

    output_path = "expanded_schema_test.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_output)

    print(f"Generated {output_path}")


if __name__ == "__main__":
    main()
