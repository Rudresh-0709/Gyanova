import sys
import os
import json
import asyncio

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.node.content_generation_node import content_generation_node
from services.node.rendering_node import rendering_node


def verify_specific_slides():
    print("🧪 Starting Targeted Slide Verification...")

    # partial state with 3 specific blueprints
    test_state = {
        "slides": {
            "demo_subtopic": [
                {
                    "slide_id": "test_slide_1_timeline",
                    "slide_title": "The Evolution of AI",
                    "slide_purpose": "narrate",
                    "subtopic_name": "History of AI",
                    "content_type": "TIMELINE_STEPS",
                    "narration_text": "In the 1950s, Turing proposed his famous test. By the 1980s, expert systems emerged but failed to scale. In 2012, deep learning revolutionized the field with AlexNet. Today, generative models like Transformers are reshaping creativity.",
                    "narration_constraints": {"point_count": [3, 5]},
                },
                {
                    "slide_id": "test_slide_2_comparison",
                    "slide_title": "Supervised vs Unsupervised Learning",
                    "slide_purpose": "compare",
                    "subtopic_name": "Machine Learning Paradigms",
                    "content_type": "TWO_COLUMN_TEXT",  # Hint for comparison
                    "narration_text": "Supervised learning relies on labeled data, like a teacher correcting a student. It's great for classification. Unsupervised learning, however, explores unlabeled data to find patterns on its own, similar to self-discovery.",
                },
                {
                    "slide_id": "test_slide_3_code",
                    "slide_title": "Python List Comprehension",
                    "slide_purpose": "teach",
                    "subtopic_name": "Python Basics",
                    "content_type": "CODE_SNIPPET",  # Custom hint
                    "narration_text": "List comprehensions provide a concise way to create lists. Instead of a multi-line for loop, you can achieve the same result in a single readable line. It's faster and more pythonic.",
                },
            ]
        }
    }

    # 1. Run Content Generation
    print("\n[1] Running Content Generation Node...")
    state_after_content = content_generation_node(test_state)

    # Verify content was generated
    for slide in state_after_content["slides"]["demo_subtopic"]:
        print(f"   -> Generated Content for {slide['slide_id']}")
        print(json.dumps(slide.get("gyml_content", {}), indent=2))

    # 2. Run Rendering
    print("\n[2] Running Rendering Node...")
    state_final = rendering_node(state_after_content)

    # Save output
    output_html = ""
    for slide in state_final["slides"]["demo_subtopic"]:
        html = slide.get("html_content", "")
        print(f"   -> Rendered HTML for {slide['slide_id']}: {len(html)} chars")
        output_html += html + "\n<hr>\n"

    with open("targeted_test_output.html", "w", encoding="utf-8") as f:
        f.write(output_html)

    print(f"\n✅ Targeted Test Complete. Output saved to targeted_test_output.html")


if __name__ == "__main__":
    verify_specific_slides()
