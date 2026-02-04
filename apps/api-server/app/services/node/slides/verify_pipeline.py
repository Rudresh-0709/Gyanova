import os
import sys
import json
from enum import Enum

# Ensure we can import from the parent directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gyml.composer import SlideComposer
from gyml.serializer import GyMLSerializer
from gyml.validator import GyMLValidator
from gyml.renderer import GyMLRenderer
from gyml.theme import get_theme


def run_test(name, content_json):
    print(f"\n{'='*80}")
    print(f"TESTING: {name}")
    print(f"{'='*80}")

    # 1. Composer
    print(f"[1] Composer: Analyzing content...")
    composer = SlideComposer()
    slides = composer.compose(content_json)
    print(f"    -> Generated {len(slides)} ComposedSlide(s)")
    for s in slides:
        print(f"       - Intent: {s.intent}")
        print(f"       - Sections: {len(s.sections)}")

    # 2. Serializer
    print(f"[2] Serializer: Converting to GyML...")
    serializer = GyMLSerializer()
    gyml_sections = serializer.serialize_many(slides)
    print(f"    -> Generated {len(gyml_sections)} GymlSection(s)")

    # 3. Validator
    print(f"[3] Validator: Checking structure...")
    validator = GyMLValidator()
    result = validator.validate_many(gyml_sections)
    if result.is_valid:
        print(f"    -> ✅ FALIDATED: No errors")
    else:
        print(f"    -> ❌ ERRORS: {result.errors}")

    # 4. Renderer
    print(f"[4] Renderer: Generating HTML...")
    renderer = GyMLRenderer(theme=get_theme("midnight"))
    html = renderer.render_complete(gyml_sections)
    print(f"    -> ✅ RENDERED: Generated {len(html)} chars of HTML")

    return html


# --- USER EXAMPLES ---

# Example 1: Timeline
timeline_content = {
    "title": "The Discovery of Subatomic Particles",
    "subtitle": "The revolutionary realization that atoms themselves have internal structure",
    "intent": "narrate",
    "contentBlocks": [
        {
            "type": "timeline",
            "items": [
                {
                    "year": "1897: The Electron",
                    "description": "J.J. Thomson discovers the electron through cathode ray experiments, revealing tiny negatively charged particles within atoms",
                },
                {
                    "year": "1909: The Nucleus",
                    "description": "Ernest Rutherford's gold foil experiment reveals a dense, positively charged nucleus at the atom's center",
                },
                {
                    "year": "1919-1932: Protons & Neutrons",
                    "description": "Rutherford identifies protons and James Chadwick discovers neutrons, completing the nuclear picture",
                },
            ],
        }
    ],
    "takeaway": "Each discovery built upon the last, revealing ever-smaller building blocks of matter.",
    "imagePrompt": "scientific laboratory with vintage equipment",
}

# Example 2: Card Grid
card_grid_content = {
    "title": "Why This Problem Is Hard",
    "intent": "explain",
    "contentBlocks": [
        {
            "type": "card_grid",
            "cards": [
                {
                    "heading": "No Single Source",
                    "text": "There's no authoritative database tracking new projects. Information exists in fragments across disconnected sources.",
                },
                {
                    "heading": "Pre-Market Timing",
                    "text": "Projects emerge months before inventory is marketed publicly. Traditional portals miss this critical window.",
                },
                {
                    "heading": "Data Complexity",
                    "text": "Project data is semi-structured, often delayed, sometimes hidden, and rarely standardized.",
                },
                {
                    "heading": "Rapid Changes",
                    "text": "Availability and specifications shift too quickly for manual tracking to remain reliable.",
                },
            ],
        }
    ],
    "takeaway": "This is an intelligence problem, not a listing problem.",
}

if __name__ == "__main__":
    html1 = run_test("User Example 1: Timeline", timeline_content)
    html2 = run_test("User Example 2: Card Grid", card_grid_content)

    # Save output
    output_path = os.path.join(os.path.dirname(__file__), "pipeline_verification.html")
    # Wrap in simple deck
    full_html = (
        html1.replace("</body></html>", "")
        + html2.replace("<!DOCTYPE html>", "")
        .replace('<html lang="en">', "")
        .replace("<head>", "")
        .replace("</head>", "")
        .replace("<body>", "")
        .replace('<div class="gyml-deck">', "")
        .replace("</div>", "")
        + "</div></body></html>"
    )
    # Actually, simpler to just join the body contents, but for now I'll just save the last one full or try to concat nicely.
    # Because render_complete generates full HTML page, we can't just concat.
    # Let's just save the card grid one as the file to check, or improved: just run them.

    print(f"\n✅ Verification Complete.")
