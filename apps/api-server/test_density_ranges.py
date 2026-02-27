import os
import sys

# Setup pathing
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from app.services.node.slides.gyml.composer import SlideComposer
from app.services.node.slides.gyml.fitness import SlideFitnessGate
from app.services.node.slides.gyml.serializer import GyMLSerializer
from app.services.node.slides.gyml.renderer import GyMLRenderer


def get_test_slides():
    """
    Test cases designed to hit each density range with diverse content types.
    """
    return [
        {
            "name": "IMPACT - Formula & Code",
            "content": {
                "title": "Quantum Mechanics Base",
                "intent": "teach",
                "contentBlocks": [
                    {
                        "type": "formula_block",
                        "expression": "E = mc^2",
                        "variables": [
                            {"name": "E", "definition": "Energy"},
                            {"name": "m", "definition": "Mass"},
                            {"name": "c", "definition": "Speed of Light"},
                        ],
                    },
                    {
                        "type": "code",
                        "language": "python",
                        "code": "import numpy as np\ndef wave_packet(x, t):\n    return np.exp(-x**2) * np.exp(1j * t)",
                        "variant": "snippet",
                    },
                ],
            },
        },
        {
            "name": "BALANCED - Table & Diagram",
            "content": {
                "title": "Cloud Infrastructure",
                "intent": "compare",
                "contentBlocks": [
                    {
                        "type": "comparison_table",
                        "headers": ["Service", "Type", "Cost"],
                        "rows": [
                            ["S3", "Storage", "Low"],
                            ["EC2", "Compute", "Dynamic"],
                        ],
                    },
                    {
                        "type": "labeled_diagram",
                        "imageUrl": "placeholder",
                        "labels": [
                            {"text": "Load Balancer", "x": 50, "y": 20},
                            {"text": "Web Cluster", "x": 50, "y": 60},
                        ],
                    },
                ],
            },
        },
        {
            "name": "DENSE - Hierarchy Tree & List",
            "content": {
                "title": "Biological Classification",
                "intent": "explain",
                "contentBlocks": [
                    {
                        "type": "hierarchy_tree",
                        "root": {
                            "label": "Animalia",
                            "children": [
                                {
                                    "label": "Chordata",
                                    "children": [{"label": "Mammalia"}],
                                },
                                {
                                    "label": "Arthropoda",
                                    "children": [{"label": "Insecta"}],
                                },
                            ],
                        },
                    },
                    {
                        "type": "numbered_list",
                        "items": [
                            {
                                "title": "Kingdom",
                                "description": "The highest level of biological classification.",
                            },
                            {
                                "title": "Phylum",
                                "description": "A group of related classes.",
                            },
                            {
                                "title": "Class",
                                "description": "A group of related orders.",
                            },
                        ],
                    },
                ],
            },
        },
    ]


def run_test():
    composer = SlideComposer()
    serializer = GyMLSerializer()
    renderer = GyMLRenderer()

    test_cases = get_test_slides()
    gyml_sections = []

    print("=" * 80)
    print(f"{'Test Case':<35} {'Density':>8}  {'Profile':<15} {'Layout'}")
    print("=" * 80)

    # Run 1 iteration for simplicity now that we're verifying aesthetics
    for iteration in range(1):
        for case in test_cases:
            try:
                slides = composer.compose(case["content"])
                slide = slides[0]

                density = SlideFitnessGate._calculate_estimated_height(slide)
                profile_name = slide.hierarchy.name if slide.hierarchy else "N/A"
                layout = slide.image_layout
                print(
                    f"{case['name']:<35} {density:>8.2f}  {profile_name:<15} {layout}"
                )

                section = serializer.serialize(slide)
                gyml_sections.append(section)

            except Exception as e:
                print(f"FAILED {case['name']}: {str(e)}")

    html_output = renderer.render_complete(gyml_sections)
    with open("density_preview.html", "w", encoding="utf-8") as f:
        f.write(html_output)

    print("=" * 80)
    print(f"Preview generated: density_preview.html")
    print("=" * 80)


if __name__ == "__main__":
    run_test()
