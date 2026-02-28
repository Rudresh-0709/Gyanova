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
    Test cases targeting specific density profiles (Impact, Balanced, Dense).
    """
    return [
        {
            "name": "PROFILE: IMPACT (Sparse)",
            "content": {
                "title": "Topic Introduction",
                "intent": "introduce",
                "contentBlocks": [
                    {
                        "type": "intro_paragraph",
                        "text": "The first generation of computers (1946-1959) relied on vacuum tubes and electromechanical components. These early machines laid the foundation for the digital age despite their size and limitations.",
                    }
                ],
            },
        },
        {
            "name": "PROFILE: BALANCED (Standard)",
            "content": {
                "title": "Quantum Mechanics Foundations",
                "intent": "explain",
                "contentBlocks": [
                    {
                        "type": "intro_paragraph",
                        "text": "Quantum mechanics is a fundamental theory in physics that provides a description of the physical properties of nature at the scale of atoms and subatomic particles. It is the foundation of all quantum physics including quantum chemistry, quantum field theory, quantum technology, and quantum information science.",
                    },
                    {
                        "type": "paragraph",
                        "text": "At its core, it describes a world where probability takes precedence over certainty, and energy is quantized into discrete packets.",
                    },
                    {
                        "type": "smart_layout",
                        "variant": "cardGridIcon",
                        "items": [
                            {
                                "icon": "ri-lightbulb-line",
                                "heading": "Wave-Particle Duality",
                                "text": "Every particle or quantum entity may be described as either a particle or a wave. This is a central concept of quantum mechanics.",
                            },
                            {
                                "icon": "ri-focus-line",
                                "heading": "Uncertainty Principle",
                                "text": "It is impossible to know both the position and momentum of a particle with absolute precision.",
                            },
                            {
                                "icon": "ri-links-line",
                                "heading": "Entanglement",
                                "text": "Particles can become correlated such that the state of one instantly influences the other.",
                            },
                        ],
                    },
                ],
            },
        },
        {
            "name": "PROFILE: DENSE (Heavy)",
            "content": {
                "title": "Detailed Biological Classification",
                "intent": "explain",
                "contentBlocks": [
                    {
                        "type": "paragraph",
                        "text": "Biological classification is the scientific method in which biologists group and categorize organisms by biological type, such as genus or species. Modern biological classification has its root in the work of Carl Linnaeus, who grouped species according to shared physical characteristics. These groupings have since been revised to improve consistency with the Darwinian principle of common descent and genetic similarity.",
                    },
                    {
                        "type": "intro_paragraph",
                        "text": "The hierarchy of biological classification involves eight major taxonomic ranks, each narrower than the one before it. This system allows for global collaboration and precise identification of every living thing discovered on Earth.",
                    },
                    {
                        "type": "smart_layout",
                        "variant": "cardGrid",
                        "items": [
                            {
                                "heading": "Domain",
                                "text": "The highest taxonomic rank. There are three domains: Archaea, Bacteria, and Eukarya.",
                            },
                            {
                                "heading": "Kingdom",
                                "text": "Animalia, Plantae, Fungi, Protista, Archaea, and Bacteria are the primary kingdoms.",
                            },
                            {
                                "heading": "Phylum",
                                "text": "Groups organisms with a similar body plan, like Chordata or Arthropoda.",
                            },
                            {
                                "heading": "Class",
                                "text": "A taxonomic rank below phylum. For example, Mammalia or Insecta.",
                            },
                            {
                                "heading": "Order",
                                "text": "For example, Primates or Lepidoptera. It narrows down the organism type further.",
                            },
                            {
                                "heading": "Family",
                                "text": "For example, Hominidae or Felidae. Represents closely related genuses.",
                            },
                        ],
                    },
                    {
                        "type": "takeaway",
                        "text": "Taxonomy is a dynamic field that evolves as new genetic data becomes available, reflecting more accurately the evolutionary relationships between living things.",
                    },
                    {
                        "type": "annotation_paragraph",
                        "text": "Note: Modern phylogenetics often places more weight on DNA sequences than on morpholgical characteristics.",
                    },
                ],
            },
        },
        {
            "name": "PROFILE: WIDE (Table)",
            "content": {
                "title": "SQL vs NoSQL Comparison",
                "intent": "compare",
                "contentBlocks": [
                    {
                        "type": "comparison_table",
                        "headers": [
                            "Feature",
                            "SQL (Relational)",
                            "NoSQL (Non-Relational)",
                        ],
                        "rows": [
                            ["Schema", "Predefined, rigid", "Dynamic, flexible"],
                            [
                                "Scaling",
                                "Vertically scaled (HW)",
                                "Horizontally scaled (CW)",
                            ],
                            [
                                "Data Model",
                                "Tables, Rows, Columns",
                                "Key-Value, Document, Graph",
                            ],
                            ["Queries", "SQL (Complex JOINs)", "NoSQL (Object-based)"],
                        ],
                    },
                    {
                        "type": "takeaway",
                        "text": "The choice depends on the specific use case and data requirements.",
                    },
                ],
            },
        },
        {
            "name": "TOP: Banner",
            "content": {
                "title": "Top Banner Layout",
                "layout": "top",
                "intent": "intro",
                "contentBlocks": [
                    {
                        "type": "intro_paragraph",
                        "text": "This slide demonstrates the 'top' accent image layout, which places a rectangular banner above the content. Great for intro slides or visual headers.",
                    },
                    {
                        "type": "bullet_list",
                        "items": [
                            "Vertical Stacking: Content flows naturally below the header image.",
                            "Rectangular Ratio: The placeholder adapts to a horizontal format (16:5 ratio).",
                        ],
                    },
                ],
            },
        },
        {
            "name": "BOTTOM: Accent",
            "content": {
                "title": "Bottom Accent Layout",
                "layout": "bottom",
                "intent": "summary",
                "contentBlocks": [
                    {
                        "type": "intro_paragraph",
                        "text": "This slide demonstrates the 'bottom' accent image layout, which places an accent zone at the bottom of the slide. Ideal for footer-like accents.",
                    },
                    {
                        "type": "smart_layout",
                        "variant": "cardGrid",
                        "items": [
                            {
                                "heading": "Footer Style",
                                "text": "Subtle branding or concluding visuals work well here.",
                            },
                            {
                                "heading": "Flex Flow",
                                "text": "The content pushes the image to the bottom automatically.",
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
                import traceback

                print(f"FAILED {case['name']}: {str(e)}")
                traceback.print_exc()

    html_output = renderer.render_complete(gyml_sections)
    output_path = os.path.join(os.path.dirname(__file__), "density_preview.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_output)

    print("=" * 80)
    print(f"Preview generated: {output_path}")
    print("=" * 80)


if __name__ == "__main__":
    run_test()
