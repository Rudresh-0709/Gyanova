import sys
import os
import json

# Standardize sys.path for the entire pipeline
current_dir = os.path.dirname(os.path.abspath(__file__))  # gyml/
slides_dir = os.path.abspath(os.path.join(current_dir, ".."))  # slides/
services_dir = os.path.abspath(os.path.join(slides_dir, "..", ".."))  # services/
project_root = os.path.abspath(os.path.join(services_dir, "..", ".."))  # api-server/

# Ensure both project root (for 'app') and slides dir (for 'gyml') are in path
for p in [project_root, slides_dir]:
    if p not in sys.path:
        sys.path.append(p)

from app.services.langgraphflow import graph
from app.services.state import TutorState


def test_workflow():
    print("🚀 Starting End-to-End Workflow Verification...")

    # Initialize state
    state = {
        "user_input": "Teach me about the evolution of Microprocessors in 3 subtopics.",
        "topic": "Microprocessors",
        "difficulty": "Intermediate",
        "teacher_id": "Expert Tech Teacher",
        "slides": {},
    }

    # Run the graph
    app = graph.compile()

    print("📈 Running LangGraph flow...")
    final_state = app.invoke(state)

    # Validation
    print("\n✅ Flow Completed!")

    sub_topics = final_state.get("sub_topics", [])
    print(f"Subtopics generated: {len(sub_topics)}")
    for sub in sub_topics:
        print(f"  - {sub.get('name')}")

    slides = final_state.get("slides", {})
    total_slides = sum(len(s_list) for s_list in slides.values())
    print(f"Total slides generated: {total_slides}")

    # Check GyML quality
    if slides:
        example_sub = list(slides.keys())[0]
        if slides[example_sub]:
            example_slide = slides[example_sub][0]
            gyml = example_slide.get("gyml_content", {})
            blocks = gyml.get("contentBlocks", [])
            print(f"Example Slide Blocks: {len(blocks)}")
            print(
                f"Narration Length: {len(example_slide.get('narration_text', '').split())} words"
            )

    # Save results for inspection
    with open("workflow_results.json", "w", encoding="utf-8") as f:
        json.dump(final_state, f, indent=2)
    print("\n📄 Results saved to workflow_results.json")


if __name__ == "__main__":
    test_workflow()
