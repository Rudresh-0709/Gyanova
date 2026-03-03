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
    GyMLProcessArrowBlock,
    GyMLProcessArrowItem,
)
from app.services.node.slides.gyml.renderer import GyMLRenderer
from app.services.node.slides.gyml.theme import THEMES

output_file = "process_arrow_test.html"

sections = []

# 3 Items Process
sections.append(
    GyMLSection(
        id="test_3",
        body=GyMLBody(
            children=[
                GyMLHeading(level=1, text="Interact with Customers"),
                GyMLProcessArrowBlock(
                    items=[
                        GyMLProcessArrowItem(
                            label="Customer Insight",
                            description="Deep interviews to uncover user needs.",
                            image_url="https://picsum.photos/id/1/600/400",
                            color="#3b82f6",
                        ),
                        GyMLProcessArrowItem(
                            label="Data Analysis",
                            description="Synthesizing metrics and market trends.",
                            image_url="https://picsum.photos/id/2/600/400",
                            color="#10b981",
                        ),
                        GyMLProcessArrowItem(
                            label="Strategic Focus",
                            description="Validating findings with focus groups.",
                            image_url="https://picsum.photos/id/3/600/400",
                            color="#f59e0b",
                        ),
                    ]
                ),
            ]
        ),
    )
)

# 4 Items Process
sections.append(
    GyMLSection(
        id="test_4",
        body=GyMLBody(
            children=[
                GyMLHeading(level=1, text="Data Strategy"),
                GyMLProcessArrowBlock(
                    items=[
                        GyMLProcessArrowItem(
                            label="Phase 1",
                            description="Initial research and discovery.",
                            image_url="https://picsum.photos/id/4/600/400",
                            color="#6366f1",
                        ),
                        GyMLProcessArrowItem(
                            label="Phase 2",
                            description="Prototyping and user testing.",
                            image_url="https://picsum.photos/id/5/600/400",
                            color="#ec4899",
                        ),
                        GyMLProcessArrowItem(
                            label="Phase 3",
                            description="Finalizing assets and handoff.",
                            image_url="https://picsum.photos/id/6/600/400",
                            color="#0d9488",
                        ),
                        GyMLProcessArrowItem(
                            label="Phase 4",
                            description="Analysis and refinement.",
                            image_url="https://picsum.photos/id/7/600/400",
                            color="#2563eb",
                        ),
                    ]
                ),
            ]
        ),
    )
)

renderer = GyMLRenderer(theme=THEMES["gamma_light"], animated=True)
html_content = renderer.render_complete(sections)

with open(output_file, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"Generated {output_file} successfully.")
