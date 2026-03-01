import os
from .renderer import GyMLRenderer
from .definitions import (
    GyMLSection,
    GyMLBody,
    GyMLSmartLayout,
    GyMLSmartLayoutItem,
    GyMLHeading,
    GyMLParagraph,
)
from .hierarchy import VisualHierarchy


def test_sequential_steps():
    layout = GyMLSmartLayout(
        variant="sequentialSteps",
        cellsize=15,
        items=[
            GyMLSmartLayoutItem(
                heading="Single strength/weakness",
                description="Initial focused analysis on a single internal factor to understand immediate constraints or advantages.",
            ),
            GyMLSmartLayoutItem(
                heading="Multiple opportunities/threats",
                description="Broaden scope to external factors, scanning the environment for multiple vectors of impact.",
            ),
            GyMLSmartLayoutItem(
                heading="Multiple strengths/weaknesses",
                description="Comprehensive internal audit comparing competing resource strengths and structural weaknesses.",
            ),
        ],
    )

    section = GyMLSection(
        id="test-sequential",
        image_layout="blank",
        hierarchy=VisualHierarchy.get_profile("dense"),
        body=GyMLBody(
            children=[
                GyMLHeading(level=1, text="Strategic Conclusion Process"),
                GyMLParagraph(
                    text="This workflow illustrates the standard method for aggregating SWOT findings into actionable intelligence.",
                    variant="intro",
                ),
                layout,
                GyMLParagraph(
                    text="The above sequence demonstrates that increasing complexity in analysis leads directly to more robust strategic options.",
                    variant="outro",
                ),
            ]
        ),
    )

    renderer = GyMLRenderer()
    html_output = renderer.render_complete([section])

    output_path = os.path.join(os.path.dirname(__file__), "test_sequential_output.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_output)
    print(f"Generated {output_path}")


if __name__ == "__main__":
    test_sequential_steps()
