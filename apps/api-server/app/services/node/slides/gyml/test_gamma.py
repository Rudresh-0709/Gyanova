"""Generate Gamma-style test output with rich content."""

import os
import sys

# Add parent to path
parent = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent not in sys.path:
    sys.path.insert(0, parent)

from gyml.composer import SlideComposer
from gyml.serializer import GyMLSerializer
from gyml.validator import GyMLValidator
from gyml.renderer import GyMLRenderer
from gyml.theme import get_theme
from gyml.types import ComposedSlide, ComposedSection, ComposedBlock, Emphasis
from gyml.constants import BlockType, SectionPurpose


def create_rich_slide():
    """Create a Gamma-style slide with rich content structure."""

    # Manually create a rich slide matching Gamma examples
    slide = ComposedSlide(
        id="slide_gamma_demo",
        intent="explain",
        sections=[
            # Title section
            ComposedSection(
                purpose=SectionPurpose.INTRODUCTION.value,
                blocks=[
                    ComposedBlock(
                        type=BlockType.HEADING.value,
                        content={"text": "Why This Problem Is Hard", "level": 1},
                        emphasis=Emphasis.PRIMARY,
                    ),
                ],
            ),
            # Card grid section
            ComposedSection(
                purpose=SectionPurpose.CONTENT.value,
                blocks=[
                    ComposedBlock(
                        type=BlockType.CARD_GRID.value,
                        content={
                            "cards": [
                                {
                                    "heading": "No Single Source",
                                    "text": "There's no authoritative, centralized database tracking new projects. Information exists in fragments across disconnected sources.",
                                },
                                {
                                    "heading": "Pre-Market Timing",
                                    "text": "Projects emerge months before inventory is marketed publicly. Traditional portals miss this critical early window entirely.",
                                },
                                {
                                    "heading": "Data Complexity",
                                    "text": "Project data is semi-structured, often delayed, sometimes hidden, and rarely standardized across sources.",
                                },
                                {
                                    "heading": "Rapid Changes",
                                    "text": "Project availability, pricing, and specifications shift too quickly for manual tracking methods to remain reliable.",
                                },
                            ]
                        },
                        emphasis=Emphasis.SECONDARY,
                    ),
                ],
            ),
            # Takeaway section with callout
            ComposedSection(
                purpose=SectionPurpose.TAKEAWAY.value,
                blocks=[
                    ComposedBlock(
                        type=BlockType.DIVIDER.value,
                        content={},
                        emphasis=Emphasis.TERTIARY,
                    ),
                    ComposedBlock(
                        type=BlockType.CALLOUT.value,
                        content={
                            "text": "This is an **intelligence problem**, not a listing problem."
                        },
                        emphasis=Emphasis.TERTIARY,
                    ),
                    ComposedBlock(
                        type=BlockType.PARAGRAPH.value,
                        content={
                            "text": "Humans can't monitor 50 fragmented sources daily. Machines can."
                        },
                        emphasis=Emphasis.TERTIARY,
                    ),
                ],
            ),
        ],
        image_layout="blank",
    )

    return slide


def main():
    print("Creating Gamma-style slide...")

    # Create rich slide
    slide = create_rich_slide()
    print(f"Created slide with {len(slide.sections)} sections")

    # Serialize
    from gyml.serializer import GyMLSerializer

    serializer = GyMLSerializer()
    gyml_section = serializer.serialize(slide)
    print(f"Serialized to GyML")

    # Validate
    from gyml.validator import GyMLValidator

    validator = GyMLValidator()
    result = validator.validate(gyml_section)
    print(
        f"Valid: {result.is_valid}, Errors: {result.errors}, Warnings: {result.warnings}"
    )

    # Render
    from gyml.renderer import GyMLRenderer
    from gyml.theme import get_theme

    renderer = GyMLRenderer(theme=get_theme("gamma_light"))
    html = renderer.render_complete([gyml_section])
    print(f"Rendered HTML: {len(html)} chars")

    # Save
    output_dir = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "output", "gyml_demos"
    )
    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, "gamma_style_test.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Saved to: {output_path}")
    print("Done!")


if __name__ == "__main__":
    main()
