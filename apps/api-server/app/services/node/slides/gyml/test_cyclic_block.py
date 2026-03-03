import sys
import os
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
    GyMLCyclicBlock,
    GyMLCyclicItem,
)
from app.services.node.slides.gyml.renderer import GyMLRenderer
from app.services.node.slides.gyml.theme import THEMES

output_file = "cyclic_block_test.html"

sections = []

# 3 Items Cycle
sections.append(
    GyMLSection(
        id="test_3",
        body=GyMLBody(
            children=[
                GyMLHeading(level=1, text="The Learning Loop"),
                GyMLCyclicBlock(
                    hub_label="Grow",
                    items=[
                        GyMLCyclicItem(
                            label="Learn",
                            icon="book-open",
                            description="Acquire new knowledge and theoretical foundations.",
                            color="#3498db",
                        ),
                        GyMLCyclicItem(
                            label="Practice",
                            icon="hammer",
                            description="Apply knowledge to real-world problems and projects.",
                            color="#2ecc71",
                        ),
                        GyMLCyclicItem(
                            label="Reflect",
                            icon="brain",
                            description="Analyze outcomes and identify areas for improvement.",
                            color="#e74c3c",
                        ),
                    ],
                ),
            ]
        ),
    )
)

# 4 Items Cycle
sections.append(
    GyMLSection(
        id="test_4",
        body=GyMLBody(
            children=[
                GyMLHeading(level=1, text="Product Development Cycle"),
                GyMLCyclicBlock(
                    hub_label="Agile",
                    items=[
                        GyMLCyclicItem(
                            label="Discover",
                            icon="search",
                            description="Research user needs and identify market opportunities.",
                            color="#34495e",
                        ),
                        GyMLCyclicItem(
                            label="Design",
                            icon="pen-nib",
                            description="Create prototypes and validate solutions with users.",
                            color="#9b59b6",
                        ),
                        GyMLCyclicItem(
                            label="Develop",
                            icon="code-s-slash",
                            description="Build robust software following engineering best practices.",
                            color="#e67e22",
                        ),
                        GyMLCyclicItem(
                            label="Deploy",
                            icon="rocket",
                            description="Release to production and monitor initial performance.",
                            color="#1abc9c",
                        ),
                    ],
                ),
            ]
        ),
    )
)

# 5 Items Cycle
sections.append(
    GyMLSection(
        id="test_5",
        body=GyMLBody(
            children=[
                GyMLHeading(level=1, text="Design Thinking Process"),
                GyMLCyclicBlock(
                    # No hub_label to test the empty center
                    items=[
                        GyMLCyclicItem(
                            label="Empathize",
                            icon="user-heart",
                            description="Understand the user's emotions, needs, and motivations deeply.",
                            color="#16a085",
                        ),
                        GyMLCyclicItem(
                            label="Define",
                            icon="focus-3",
                            description="Synthesize findings to form a clear problem statement.",
                            color="#27ae60",
                        ),
                        GyMLCyclicItem(
                            label="Ideate",
                            icon="lightbulb",
                            description="Brainstorm a wide range of creative and radical solutions.",
                            color="#2980b9",
                        ),
                        GyMLCyclicItem(
                            label="Prototype",
                            icon="mickey",
                            description="Build scaled-down versions of the product to investigate ideas.",
                            color="#8e44ad",
                        ),
                        GyMLCyclicItem(
                            label="Test",
                            icon="test-tube",
                            description="Return to the users with prototypes to get feedback and refine.",
                            color="#c0392b",
                        ),
                    ],
                ),
            ]
        ),
    )
)

renderer = GyMLRenderer(theme=THEMES["gamma_light"], animated=False)
html_content = renderer.render_complete(sections)

with open(output_file, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"Generated {output_file} successfully.")
