import sys
import os
import json
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(
    0, str(Path(__file__).resolve().parent.parent.parent.parent.parent.parent)
)

from app.services.node.slides.gyml.definitions import (
    GyMLSection,
    GyMLBody,
    GyMLHeading,
    GyMLParagraph,
    GyMLSmartLayout,
    GyMLSmartLayoutItem,
    GyMLIcon,
)
from app.services.node.slides.gyml.renderer import GyMLRenderer
from app.services.node.slides.gyml.theme import THEMES

output_file = "variants_test.html"

variants_to_test = [
    {
        "name": "Process Arrow",
        "variant": "processArrow",
        "items": [
            GyMLSmartLayoutItem(heading="Step 1", description="Start here."),
            GyMLSmartLayoutItem(heading="Step 2", description="Continue here."),
            GyMLSmartLayoutItem(heading="Step 3", description="Finish here."),
        ],
    },
    {
        "name": "Timeline Sequential",
        "variant": "timelineSequential",
        "items": [
            GyMLSmartLayoutItem(heading="Phase 1", description="Research"),
            GyMLSmartLayoutItem(heading="Phase 2", description="Design"),
            GyMLSmartLayoutItem(heading="Phase 3", description="Build"),
        ],
    },
    {
        "name": "Timeline Milestone",
        "variant": "timelineMilestone",
        "items": [
            GyMLSmartLayoutItem(heading="2020", description="Company founded."),
            GyMLSmartLayoutItem(heading="2022", description="1M users reached."),
            GyMLSmartLayoutItem(heading="2024", description="Global expansion."),
        ],
    },
    {
        "name": "Stats Comparison",
        "variant": "statsComparison",
        "items": [
            GyMLSmartLayoutItem(label="Before", value="10%"),
            GyMLSmartLayoutItem(label="After", value="85%"),
        ],
    },
    {
        "name": "Bullet Check",
        "variant": "bulletCheck",
        "items": [
            GyMLSmartLayoutItem(description="Fully responsive."),
            GyMLSmartLayoutItem(description="Accessible by default."),
        ],
    },
    {
        "name": "Comparison Pros Cons",
        "variant": "comparisonProsCons",
        "items": [
            GyMLSmartLayoutItem(heading="Pros", description="Fast, reliable, cheap."),
            GyMLSmartLayoutItem(heading="Cons", description="Steep learning curve."),
        ],
    },
    {
        "name": "Comparison Before After",
        "variant": "comparisonBeforeAfter",
        "items": [
            GyMLSmartLayoutItem(
                heading="Before AI", description="Manual, slow, error-prone."
            ),
            GyMLSmartLayoutItem(
                heading="After AI", description="Automated, fast, precise."
            ),
        ],
    },
    {
        "name": "Quote Citation",
        "variant": "quoteCitation",
        "items": [
            GyMLSmartLayoutItem(
                heading="- Jane Doe",
                description="This is a profound quote that changes everything.",
            )
        ],
    },
]

sections = []

for idx, test_case in enumerate(variants_to_test):
    section = GyMLSection(
        id=f"slide_{idx}",
        body=GyMLBody(
            children=[
                GyMLHeading(level=1, text=test_case["name"]),
                GyMLParagraph(
                    text=f"Testing the {test_case['variant']} variant.", variant="intro"
                ),
                GyMLSmartLayout(variant=test_case["variant"], items=test_case["items"]),
            ]
        ),
    )
    sections.append(section)

renderer = GyMLRenderer(theme=THEMES["gamma_light"], animated=False)
html_content = renderer.render_complete(sections)

with open(output_file, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"Generated {output_file}. Please open in a browser to check variants.")
