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
                    "narration_text": "The history of Artificial Intelligence is a journey of ambition and cycles. It began in the 1950s when Alan Turing proposed the Turing Test, asking 'Can machines think?', setting the philosophical groundwork. The 1980s saw the rise of Expert Systems, which used rule-based logic to solve specific problems but were brittle and hard to scale. A major breakthrough occurred in 2012 with AlexNet, which proved the power of Deep Learning and largely solved image recognition. Today, we are in the era of Generative AI, where models like Transformers can create art, code, and text, fundamentally reshaping how we interact with information. The pace of change is accelerating faster than ever.",
                    "narration_constraints": {"point_count": [3, 5]},
                },
                {
                    "slide_id": "test_slide_2_comparison",
                    "slide_title": "Supervised vs Unsupervised Learning",
                    "slide_purpose": "compare",
                    "subtopic_name": "Machine Learning Paradigms",
                    "content_type": "TWO_COLUMN_TEXT",  # Hint for comparison
                    "narration_text": "Machine Learning is broadly divided into two main paradigms. Supervised Learning is like a classroom setting where the model learns from labeled examples—it knows the right answer and corrects itself using error minimization. It requires massive annotated datasets but is highly accurate for specific classification tasks. Unsupervised Learning, however, is like self-discovery. The model looks at raw, unlabeled data and tries to find hidden patterns or structures on its own. While less precise for specific targets, it is essential for discovering new insights and clustering data without human bias. Both are critical for a complete AI system.",
                },
                {
                    "slide_id": "test_slide_3_code",
                    "slide_title": "Python List Comprehension",
                    "slide_purpose": "teach",
                    "subtopic_name": "Python Basics",
                    "content_type": "CODE_SNIPPET",  # Custom hint
                    "narration_text": "List comprehensions are a distinctive feature of Python that allows for concise, readable list creation. Instead of writing a verbose multi-line for-loop to populate a list, you can condense the logic into a single line. For example, squaring numbers from 0 to 9 becomes `[x**2 for x in range(10)]`. This is not only more 'Pythonic' and easier to read but often computationally faster than using `append()` in a loop. It's a key tool for any data scientist working with large arrays, reducing clutter and improving maintainability.",
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
    print(f"\n[3] Saving individual slide outputs...")
    for slide in state_final["slides"]["demo_subtopic"]:
        html = slide.get("html_content", "")
        slide_id = slide["slide_id"]
        filename = f"targeted_test_output_{slide_id}.html"

        with open(filename, "w", encoding="utf-8") as f:
            f.write(html)

        print(f"   -> Saved {filename} ({len(html)} chars)")

    print(f"\n✅ Targeted Test Complete. Slides saved as individual HTML files.")


if __name__ == "__main__":
    verify_specific_slides()
