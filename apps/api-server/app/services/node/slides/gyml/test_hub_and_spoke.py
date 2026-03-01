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
    GyMLHubAndSpoke,
    GyMLHubAndSpokeItem,
)
from app.services.node.slides.gyml.renderer import GyMLRenderer
from app.services.node.slides.gyml.theme import THEMES

output_file = "hub_and_spoke_test.html"

sections = []

# 4 Spokes (Realistic Marketing Strategy)
sections.append(
    GyMLSection(
        id="test_4",
        body=GyMLBody(
            children=[
                GyMLHeading(level=1, text="Foundational Pillars of Market Leadership"),
                GyMLHubAndSpoke(
                    hub_label="Strategy",
                    items=[
                        GyMLHubAndSpokeItem(
                            label="Customer Insight",
                            icon="user-heart",
                            description="Leveraging deep behavioral analytics and qualitative feedback to anticipate unarticulated customer needs before competitors do.",
                        ),
                        GyMLHubAndSpokeItem(
                            label="Agile Delivery",
                            icon="wind",
                            description="Implementing rapid iteration cycles and cross-functional teams to bring high-quality features to market with unprecedented speed.",
                        ),
                        GyMLHubAndSpokeItem(
                            label="Brand Resonance",
                            icon="shippo",
                            description="Crafting a compelling narrative that aligns with cultural shifts and builds lasting emotional connections with the target audience.",
                        ),
                        GyMLHubAndSpokeItem(
                            label="Scale Efficiency",
                            icon="trending-up",
                            description="Optimizing unit economics and automation to maintain profitability while aggressively expanding market share globally.",
                        ),
                    ],
                ),
                GyMLParagraph(
                    text="Takeaway: Holistic integration of these pillars ensures sustainable competitive advantage.",
                    variant="outro",
                ),
            ]
        ),
    )
)

# 6 Spokes (Detailed Product Success Factors)
sections.append(
    GyMLSection(
        id="test_6",
        body=GyMLBody(
            children=[
                GyMLHeading(level=1, text="Key Product Success Dimensions"),
                GyMLHubAndSpoke(
                    hub_label="Success",
                    items=[
                        GyMLHubAndSpokeItem(
                            label="User Empathy",
                            icon="users",
                            description="The ability to step into the user's shoes, understanding their daily friction points and emotional triggers at every touchpoint.",
                        ),
                        GyMLHubAndSpokeItem(
                            label="Technical Debt",
                            icon="tool",
                            description="Balancing speed of feature delivery with the long-term maintainability and performance of the underlying architecture.",
                        ),
                        GyMLHubAndSpokeItem(
                            label="Market Fit",
                            icon="target",
                            description="Continuous validation of the value proposition against shifting market dynamics and emerging competitive threats.",
                        ),
                        GyMLHubAndSpokeItem(
                            label="Data Literacy",
                            icon="bar-chart",
                            description="Empowering every stakeholder to make decisions based on rigorous data analysis rather than intuition or highest-paid opinion.",
                        ),
                        GyMLHubAndSpokeItem(
                            label="Vision Alignment",
                            icon="eye",
                            description="Ensuring that every minor feature and major pivot stays true to the core mission and long-term goal of the organization.",
                        ),
                        GyMLHubAndSpokeItem(
                            label="Feedback Loops",
                            icon="refresh-cw",
                            description="Establishing seamless channels for customer feedback to flow directly into the product roadmap for constant refinement.",
                        ),
                    ],
                ),
                GyMLParagraph(
                    text="Takeaway: Balanced focus across these dimensions builds high-performing product organizations.",
                    variant="outro",
                ),
            ]
        ),
    )
)

renderer = GyMLRenderer(theme=THEMES["gamma_light"], animated=True)
html_content = renderer.render_complete(sections)

with open(output_file, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"Generated {output_file} with realistic content and balanced 4/6 variants.")
