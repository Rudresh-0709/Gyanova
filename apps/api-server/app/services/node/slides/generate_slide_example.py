"""
Example: Generate a slide using the Gamma-like markup workflow.
This demonstrates the complete workflow from markup to HTML.
"""

from gamma_engine import GammaSlideEngine

# Initialize the engine
engine = GammaSlideEngine()

# Define slide content using JSON markup
slide_markup = {
    "id": "ai_teacher_demo",
    "sections": [
        {
            "purpose": "introduction",
            "blocks": [
                {"type": "heading", "level": 1, "text": "AI Teacher Platform Features"},
                {
                    "type": "paragraph",
                    "text": "Revolutionizing education through intelligent content generation",
                },
            ],
        },
        {
            "purpose": "content",
            "blocks": [
                {
                    "type": "columns",
                    "widths": [50, 50],
                    "columns": [
                        [
                            {
                                "type": "heading",
                                "level": 2,
                                "text": "Core Capabilities",
                            },
                            {
                                "type": "smart_layout_bullets",
                                "items": [
                                    {
                                        "text": "AI-powered content generation",
                                        "icon": "ri-robot-line",
                                    },
                                    {
                                        "text": "Dynamic slide creation",
                                        "icon": "ri-presentation-line",
                                    },
                                    {
                                        "text": "Smart icon selection",
                                        "icon": "ri-lightbulb-line",
                                    },
                                    {
                                        "text": "Fact verification system",
                                        "icon": "ri-shield-check-line",
                                    },
                                ],
                            },
                        ],
                        [
                            {"type": "heading", "level": 2, "text": "Platform Stats"},
                            {
                                "type": "stats_grid",
                                "stats": [
                                    {"value": "8", "label": "Node Pipeline"},
                                    {"value": "100%", "label": "Automated"},
                                    {"value": "∞", "label": "Possibilities"},
                                ],
                            },
                        ],
                    ],
                }
            ],
        },
        {
            "purpose": "content",
            "blocks": [
                {"type": "divider"},
                {"type": "heading", "level": 2, "text": "Development Timeline"},
                {
                    "type": "timeline",
                    "events": [
                        {
                            "year": "Phase 1",
                            "description": "Content generation with LangGraph workflow",
                        },
                        {
                            "year": "Phase 2",
                            "description": "Smart layouts and responsive blocks",
                        },
                        {
                            "year": "Phase 3",
                            "description": "Gamma-style markup integration",
                        },
                        {
                            "year": "Current",
                            "description": "Full-featured slide generation system",
                        },
                    ],
                },
            ],
        },
        {
            "purpose": "takeaway",
            "blocks": [
                {
                    "type": "takeaway",
                    "label": "Key Achievement",
                    "text": "Successfully integrated Gamma's responsive, markup-driven approach with existing block-based rendering system",
                }
            ],
        },
    ],
}

# Generate the HTML slide
print("🎨 Generating slide using Gamma-like markup workflow...\n")
html_output = engine.render_from_markup(slide_markup)

# Save to file
import os

output_dir = os.path.join(os.path.dirname(__file__), "output", "gamma_demos")
os.makedirs(output_dir, exist_ok=True)
output_file = os.path.join(output_dir, "ai_teacher_demo.html")

with open(output_file, "w", encoding="utf-8") as f:
    f.write(html_output)

print(f"✅ Slide generated successfully!")
print(f"📁 Location: {output_file}")
print(f"📊 Total size: {len(html_output):,} characters")
print(f"\n🌐 Open the file in your browser to see the result!")

# Also show the markup structure
print("\n" + "=" * 60)
print("📝 Markup Structure Used:")
print("=" * 60)
print(f"Sections: {len(slide_markup['sections'])}")
for i, section in enumerate(slide_markup["sections"], 1):
    print(
        f"  {i}. {section['purpose'].title()} section - {len(section['blocks'])} blocks"
    )
    for block in section["blocks"]:
        block_type = block.get("type", "unknown")
        print(f"     • {block_type}")
