"""
GyML Real Slide Verification

Generates a realistic slide to test the full pipeline:
Preprocessor -> Composer (Smart Layouts) -> Serializer -> Renderer
"""

import os
import sys

# Ensure import path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from gyml.preprocessor import ContentPreprocessor
from gyml.composer import SlideComposer, Intent
from gyml.serializer import GyMLSerializer
from gyml.renderer import GyMLRenderer
from gyml.theme import get_theme


def generate_real_slide():
    # 1. Input Content (Timeline of AI)
    # This should trigger the Timeline Smart Layout because of "Narrate" intent + dates
    raw_content = {
        "title": "The Evolution of AI",
        "intent": "narrate",
        "points": [
            "1950: The Turing Test proposed by Alan Turing",
            "1956: Dartmouth Conference coin the term 'Artificial Intelligence'",
            "1997: Deep Blue defeats Garry Kasparov",
            "2012: AlexNet breakthrough in computer vision",
            "2017: Transformer architecture introduced by Google",
        ],
        "image": {
            "url": "https://example.com/ai-history.jpg",
            "alt": "Timeline graphic of AI history",
        },
    }

    print(f"[*] Input: {raw_content['title']} (Intent: {raw_content['intent']})")

    # 2. Pipeline Components
    preprocessor = ContentPreprocessor(strict_mode=True)
    theme = get_theme("gamma_blue")  # Use a specific theme
    composer = SlideComposer(theme=theme)
    serializer = GyMLSerializer()
    renderer = GyMLRenderer(theme=theme)

    # 3. Execution Flow
    try:
        # Step A: Validate
        clean_content = preprocessor.process(raw_content)
        print("[*] Preprocessor: Validated & Sanitized")

        # Step B: Compose
        # This determines layout. We expect a TIMELINE variant.
        slides = composer.compose(clean_content)
        slide = slides[0]
        print(f"[*] Composer: Generated {len(slides)} slide(s)")
        print(f"    -> Intent: {slide.intent}")
        print(
            f"    -> Hierarchy: {slide.hierarchy.name if slide.hierarchy else 'None'}"
        )

        # Verify Smart Layout Selection
        has_timeline = False
        for section in slide.sections:
            for block in section.blocks:
                if block.type == "smart_layout":
                    print(
                        f"    -> Smart Layout Variant: {block.content.get('variant')}"
                    )
                    if block.content.get("variant") == "timeline":
                        has_timeline = True

        if not has_timeline:
            print("[!] WARNING: Did not autoselect Timeline layout!")

        # Step C: Serialize
        section_ir = serializer.serialize(slide)
        print("[*] Serializer: Converted to GyML Section")

        # Step D: Render
        html_output = renderer.render_complete([section_ir])
        print("[*] Renderer: Generated HTML")

        # 4. Verification Check
        if 'role="region"' in html_output:
            print("    -> [PASS] ARIA role detected")
        if "var(--timeline-color" in html_output:
            print("    -> [PASS] Theme variables detected")

        # Save to file
        output_path = os.path.join(os.path.dirname(__file__), "output_real_slide.html")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_output)

        print(f"[*] SUCCESS. Saved to: {output_path}")

        # =========================================================
        # TEST 2: SPARSE CONTENT (Visual Balance Check)
        # =========================================================
        print("\n[*] --- TEST 2: Sparse Content (Visual Balance) ---")
        sparse_content = {
            "title": "Minimal Slide",
            "text": "This slide has very little content.",
            "intent": "explain",
        }

        sparse_slides = composer.compose(sparse_content)
        s_slide = sparse_slides[0]

        print(f"[*] Density Score: {composer._calculate_visual_density(s_slide):.2f}")

        if s_slide.accent_image_url == "placeholder":
            print("    -> [PASS] Auto-injected placeholder image")
        else:
            print(
                f"    -> [FAIL] No placeholder injected! (Image: {s_slide.accent_image_url})"
            )

        # Write sparse slide to file
        section_sparse = serializer.serialize(s_slide)
        html_sparse = renderer.render_complete([section_sparse])
        output_path_sparse = os.path.join(
            os.path.dirname(__file__), "output_sparse.html"
        )
        with open(output_path_sparse, "w", encoding="utf-8") as f:
            f.write(html_sparse)
        print(f"[*] Saved sparse slide to: {output_path_sparse}")

        # =========================================================
        # TEST 3: STATS GRID (Intent: Prove)
        # =========================================================
        print("\n[*] --- TEST 3: Stats Grid (Intent: Prove) ---")
        stats_content = {
            "title": "AI Market Growth",
            "intent": "prove",
            "points": [
                {"value": "40%", "label": "CAGR Growth"},
                {"value": "$1.3T", "label": "Market Size by 2030"},
                {"value": "85%", "label": "Enterprise Adoption"},
            ],
            "image": {
                "url": "https://example.com/chart.png",
                "alt": "Growth Chart",
            },
        }

        stats_slides = composer.compose(stats_content)
        stats_slide = stats_slides[0]

        # Verify Layout
        print(f"[*] Generated Stats Slide Intent: {stats_slide.intent}")
        for s in stats_slide.sections:
            for b in s.blocks:
                if b.type == "smart_layout":
                    print(f"    -> Variant: {b.content.get('variant')}")

        # Write to file
        section_stats = serializer.serialize(stats_slide)
        html_stats = renderer.render_complete([section_stats])
        output_path_stats = os.path.join(os.path.dirname(__file__), "output_stats.html")
        with open(output_path_stats, "w", encoding="utf-8") as f:
            f.write(html_stats)
        print(f"[*] Saved stats slide to: {output_path_stats}")

        # =========================================================
        # TEST 4: PROCESS STEPS (Intent: Demo)
        # =========================================================
        print("\n[*] --- TEST 4: Process Steps (Intent: Demo) ---")
        demo_content = {
            "title": "How LLMs Work",
            "intent": "demo",
            "points": [
                "Tokenization: Breaking text into chunks",
                "Embedding: Converting tokens to vectors",
                "Attention: Analyzing relationships",
                "Generation: Predicting next token",
            ],
        }

        demo_slides = composer.compose(demo_content)
        demo_slide = demo_slides[0]

        # Verify Layout
        print(f"[*] Generated Demo Slide Intent: {demo_slide.intent}")
        for s in demo_slide.sections:
            for b in s.blocks:
                if b.type == "smart_layout":
                    print(f"    -> Variant: {b.content.get('variant')}")

        # Write to file
        section_demo = serializer.serialize(demo_slide)
        html_demo = renderer.render_complete([section_demo])
        output_path_demo = os.path.join(os.path.dirname(__file__), "output_demo.html")
        with open(output_path_demo, "w", encoding="utf-8") as f:
            f.write(html_demo)
        print(f"[*] Saved demo slide to: {output_path_demo}")

    except Exception as e:
        print(f"[!] FAILED: {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    generate_real_slide()
