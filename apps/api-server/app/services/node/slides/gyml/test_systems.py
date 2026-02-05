"""
GyML Systems Verification

Tests the Responsive Layer and Visual Hierarchy System.
"""

import os
import sys

# Ensure import path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from gyml.composer import SlideComposer
from gyml.serializer import GyMLSerializer
from gyml.renderer import GyMLRenderer
from gyml.responsive import ResponsiveConstraints
from gyml.constants import Intent


def test_responsive_generation():
    print("Test 1: Responsive CSS Generation")

    constraints = ResponsiveConstraints(
        breakpoints={"mobile": 500},
        layout_fallbacks={"columns": "stack"},
        viewport_padding={"mobile": "0.5rem"},
    )

    renderer = GyMLRenderer(responsive_constraints=constraints)
    css = renderer._get_responsive_styles()

    if "@media (max-width: 500px)" in css:
        print("   -> [PASS] Breakpoint generated")
    else:
        print(f"   -> [FAIL] Missing breakpoint in CSS: {css[:100]}...")

    if "--section-padding: 0.5rem" in css:
        print("   -> [PASS] Padding variable generated")
    else:
        print("   -> [FAIL] Missing padding variable")

    print("")


def test_hierarchy_assignment():
    print("Test 2: Hierarchy Assignment")

    composer = SlideComposer()

    # 1. Low Density
    low_content = {"title": "Simple Slide", "points": ["Point 1", "Point 2"]}
    slide = composer.compose_single(low_content)
    print(f"   -> Words: {slide.total_word_count()}, Intent: {slide.intent}")

    if slide.hierarchy and slide.hierarchy.name == "default":
        print("   -> [PASS] Low density -> 'default' profile")
    else:
        print(
            f"   -> [FAIL] Expected 'default', got {slide.hierarchy.name if slide.hierarchy else 'None'}"
        )

    # 2. High Density
    high_content = {
        "title": "Dense Slide",
        "points": ["Word " * 10] * 20,  # 200 words > 150 threshold
        "intent": "explain",
    }
    slide_high = composer.compose_single(high_content)
    print(f"   -> Words: {slide_high.total_word_count()}, Intent: {slide_high.intent}")

    if slide_high.hierarchy and slide_high.hierarchy.name == "dense":
        print("   -> [PASS] High density -> 'dense' profile")
    else:
        print(
            f"   -> [FAIL] Expected 'dense', got {slide_high.hierarchy.name if slide_high.hierarchy else 'None'}"
        )

    print("")


def test_integration():
    print("Test 3: End-to-End Integration")

    content = {"title": "Integrated Slide", "points": ["Checking CSS injection"]}

    composer = SlideComposer()
    serializer = GyMLSerializer()
    renderer = GyMLRenderer()

    slide = composer.compose_single(content)
    section = serializer.serialize(slide)
    html = renderer.render(section)

    if 'style="--h1-size:' in html:
        print("   -> [PASS] Inline styles injected")
    else:
        print(f"   -> [FAIL] Inline styles missing: {html[:200]}...")

    doc = renderer.render_complete([section])
    if "/* Dynamic Responsive Styles */" in doc:
        print("   -> [PASS] Responsive CSS injected in doc")
    else:
        print("   -> [FAIL] Responsive CSS missing")


if __name__ == "__main__":
    test_responsive_generation()
    test_hierarchy_assignment()
    test_integration()
