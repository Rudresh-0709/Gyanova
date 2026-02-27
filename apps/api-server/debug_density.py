import os
import sys

# Setup pathing
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from app.services.node.slides.gyml.composer import SlideComposer
from app.services.node.slides.gyml.fitness import SlideFitnessGate


def get_test_slides():
    return [
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
        }
    ]


def check_density():
    composer = SlideComposer()
    test_cases = get_test_slides()

    for case in test_cases:
        slides = composer.compose(case["content"])
        slide = slides[0]

        # We want to see the density BEFORE and AFTER image injection
        # compose() calls ensure_visual_balance which injects images.

        density = SlideFitnessGate._calculate_estimated_height(slide)
        print(f"Slide: {case['name']}")
        print(f"Final Density: {density:.2f}")
        print(f"Final Hierarchy: {slide.hierarchy.name if slide.hierarchy else 'N/A'}")
        print(f"Final Layout: {slide.image_layout}")
        print(f"Has Image: {bool(slide.accent_image_url)}")


if __name__ == "__main__":
    check_density()
