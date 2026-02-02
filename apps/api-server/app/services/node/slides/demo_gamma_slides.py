"""
Demo examples showcasing Gamma-like markup features.
Run this to generate example slides.
"""

from gamma_engine import GammaSlideEngine
import os


def create_output_dir():
    """Create output directory if it doesn't exist."""
    output_dir = os.path.join(os.path.dirname(__file__), "output", "gamma_demos")
    os.makedirs(output_dir, exist_ok=True)
    return output_dir


def example_1_smart_bullets():
    """Example using smart layout bullets."""
    markup = {
        "id": "smart_bullets_demo",
        "sections": [
            {
                "purpose": "introduction",
                "blocks": [
                    {"type": "heading", "level": 1, "text": "Why Choose Our Platform?"},
                    {
                        "type": "paragraph",
                        "text": "Built for modern teams who value speed and collaboration",
                    },
                ],
            },
            {
                "purpose": "content",
                "blocks": [
                    {
                        "type": "smart_layout_bullets",
                        "items": [
                            {
                                "text": "Lightning-fast performance with real-time sync",
                                "icon": "ri-flashlight-line",
                            },
                            {
                                "text": "Enterprise-grade security and compliance",
                                "icon": "ri-shield-check-line",
                            },
                            {
                                "text": "Beautiful, intuitive interface",
                                "icon": "ri-palette-line",
                            },
                            {
                                "text": "24/7 customer support",
                                "icon": "ri-customer-service-line",
                            },
                        ],
                    }
                ],
            },
        ],
    }

    return markup


def example_2_columns_with_stats():
    """Example using columns layout with stats."""
    markup = {
        "id": "columns_stats_demo",
        "sections": [
            {
                "purpose": "introduction",
                "blocks": [{"type": "heading", "level": 1, "text": "Product Overview"}],
            },
            {
                "purpose": "content",
                "blocks": [
                    {
                        "type": "columns",
                        "widths": [60, 40],
                        "columns": [
                            [
                                {"type": "heading", "level": 2, "text": "Key Features"},
                                {
                                    "type": "bullet_list",
                                    "items": [
                                        "Real-time collaboration",
                                        "Cloud-based storage",
                                        "Advanced analytics",
                                        "API integrations",
                                    ],
                                },
                            ],
                            [
                                {
                                    "type": "heading",
                                    "level": 2,
                                    "text": "By the Numbers",
                                },
                                {
                                    "type": "stats_grid",
                                    "stats": [
                                        {"value": "500K+", "label": "Users"},
                                        {"value": "99.9%", "label": "Uptime"},
                                        {"value": "24/7", "label": "Support"},
                                    ],
                                },
                            ],
                        ],
                    }
                ],
            },
        ],
    }

    return markup


def example_3_timeline():
    """Example using timeline."""
    markup = {
        "id": "timeline_demo",
        "sections": [
            {
                "purpose": "introduction",
                "blocks": [
                    {"type": "heading", "level": 1, "text": "Company Milestones"},
                    {
                        "type": "paragraph",
                        "text": "Our journey from startup to industry leader",
                    },
                ],
            },
            {
                "purpose": "content",
                "blocks": [
                    {
                        "type": "timeline",
                        "events": [
                            {
                                "year": "2019",
                                "description": "Company founded with a vision to revolutionize the industry",
                            },
                            {
                                "year": "2020",
                                "description": "Launched first product and secured seed funding",
                            },
                            {
                                "year": "2021",
                                "description": "Reached 100K users and Series A funding",
                            },
                            {
                                "year": "2023",
                                "description": "Expanded globally to 50+ countries",
                            },
                        ],
                    }
                ],
            },
        ],
    }

    return markup


def example_4_diagrams():
    """Example using various diagrams."""
    markup = {
        "id": "diagrams_demo",
        "sections": [
            {
                "purpose": "introduction",
                "blocks": [{"type": "heading", "level": 1, "text": "Visual Diagrams"}],
            },
            {
                "purpose": "content",
                "blocks": [
                    {"type": "heading", "level": 3, "text": "Sales Funnel"},
                    {
                        "type": "diagram_funnel",
                        "stages": [
                            "Awareness (10,000 visitors)",
                            "Interest (5,000 signups)",
                            "Decision (1,000 trials)",
                            "Action (500 customers)",
                        ],
                    },
                    {"type": "divider"},
                    {"type": "heading", "level": 3, "text": "Skill Overlap"},
                    {
                        "type": "diagram_venn",
                        "circles": [
                            {"label": "Tech", "text": "Engineering"},
                            {"label": "Creative", "text": "Design"},
                            {"label": "Both", "text": "Product"},
                        ],
                    },
                ],
            },
        ],
    }

    return markup


def example_5_complete_deck():
    """Complete example combining multiple features."""
    markup = {
        "id": "complete_demo",
        "sections": [
            {
                "purpose": "title",
                "blocks": [
                    {"type": "heading", "level": 1, "text": "Evolution of Computers"},
                    {
                        "type": "paragraph",
                        "text": "A journey through technological innovation",
                    },
                ],
            },
            {
                "purpose": "content",
                "blocks": [
                    {"type": "heading", "level": 2, "text": "Historical Timeline"},
                    {
                        "type": "timeline",
                        "events": [
                            {
                                "year": "1940s-1950s",
                                "description": "First Generation: Vacuum tubes enabled the first programmable computers",
                            },
                            {
                                "year": "1950s-1960s",
                                "description": "Second Generation: Transistors replaced tubes, improving reliability",
                            },
                            {
                                "year": "1960s-1970s",
                                "description": "Third Generation: Integrated circuits enabled compact designs",
                            },
                            {
                                "year": "1970s-Present",
                                "description": "Fourth Generation: Microprocessors revolutionized computing",
                            },
                        ],
                    },
                ],
            },
            {
                "purpose": "content",
                "blocks": [
                    {"type": "divider"},
                    {
                        "type": "columns",
                        "widths": [50, 50],
                        "columns": [
                            [
                                {
                                    "type": "heading",
                                    "level": 2,
                                    "text": "Key Innovations",
                                },
                                {
                                    "type": "smart_layout_bullets",
                                    "items": [
                                        {
                                            "text": "Miniaturization of components",
                                            "icon": "ri-arrow-down-line",
                                        },
                                        {
                                            "text": "Exponential processing power",
                                            "icon": "ri-speed-line",
                                        },
                                        {
                                            "text": "Energy efficiency gains",
                                            "icon": "ri-leaf-line",
                                        },
                                    ],
                                },
                            ],
                            [
                                {
                                    "type": "heading",
                                    "level": 2,
                                    "text": "Impact Statistics",
                                },
                                {
                                    "type": "stats_grid",
                                    "stats": [
                                        {"value": "1M×", "label": "Faster"},
                                        {"value": "100K×", "label": "Smaller"},
                                        {"value": "1000×", "label": "Cheaper"},
                                    ],
                                },
                            ],
                        ],
                    },
                ],
            },
            {
                "purpose": "takeaway",
                "blocks": [
                    {
                        "type": "takeaway",
                        "label": "Key Insight",
                        "text": "Each generation of computers brought exponential improvements in size, speed, and cost-effectiveness",
                    }
                ],
            },
        ],
    }

    return markup


def example_6_xml_markup():
    """Example using XML markup format."""
    markup = """
<slide id="xml_demo">
    <section purpose="introduction">
        <heading level="1">Getting Started</heading>
        <paragraph>Simple steps to begin your journey</paragraph>
    </section>
    
    <section purpose="content">
        <smart-layout type="processSteps">
            <item>Sign up for free account</item>
            <item>Complete your profile</item>
            <item>Invite your team</item>
            <item>Start collaborating</item>
        </smart-layout>
    </section>
</slide>
"""

    return markup


def main():
    """Generate all example slides."""
    output_dir = create_output_dir()
    engine = GammaSlideEngine()

    examples = [
        ("smart_bullets", example_1_smart_bullets()),
        ("columns_stats", example_2_columns_with_stats()),
        ("timeline", example_3_timeline()),
        ("diagrams", example_4_diagrams()),
        ("complete_deck", example_5_complete_deck()),
        ("xml_format", example_6_xml_markup()),
    ]

    print("🎨 Generating Gamma-style demo slides...\\n")

    for name, markup in examples:
        try:
            html = engine.render_from_markup(markup)
            output_path = os.path.join(output_dir, f"{name}.html")

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(html)

            print(f"✅ Generated: {name}.html")
        except Exception as e:
            print(f"❌ Error generating {name}: {e}")

    print(f"\\n🎉 All demos generated in: {output_dir}")
    print("\\n📂 Open any HTML file in your browser to see the slides!")


if __name__ == "__main__":
    main()
