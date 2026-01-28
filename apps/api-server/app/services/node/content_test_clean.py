import sys
import os
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from node.content_generation_node import content_generation_node

if __name__ == "__main__":
    # Test with Computer Generations slides
    print("\n" + "=" * 80)
    print("CONTENT GENERATION TEST - Computer Generations (NO EMOJI)")
    print("=" * 80 + "\n")

    test_state = {
        "slides": {
            "sub_1_2b67b6": [
                {
                    "slide_title": "Introduction to Computer Generations",
                    "slide_purpose": "definition",
                    "selected_template": "Title card",
                    "narration_role": "Introduce",
                    "subtopic_name": "Introduction to Computer Generations",
                    "content_type": "NO_NARRATION_POINTS",
                    "narration_format": "paragraph",
                    "narration_text": "Computer generations represent distinct phases in computing evolution, each marked by revolutionary technological advances. Understanding these generations helps us appreciate how computers transformed from room-sized machines to the powerful devices we use today.",
                    "narration_constraints": {"sentence_count": [3, 5]},
                },
                {
                    "slide_title": "Overview of Computer Generations",
                    "slide_purpose": "intuition",
                    "selected_template": "Timeline",
                    "narration_role": "Guide",
                    "subtopic_name": "Introduction to Computer Generations",
                    "content_type": "TIMELINE_STEPS",
                    "narration_format": "sequential_points",
                    "narration_text": "The first generation from 1940-1956 used vacuum tubes as primary components. Second generation computers from 1956-1963 introduced transistors, making machines smaller and faster. The third generation from 1964-1971 brought integrated circuits, revolutionizing computing power. Fourth generation from 1971 onwards features microprocessors, enabling personal computers.",
                    "narration_constraints": {"point_count": [2, 4]},
                },
                {
                    "slide_title": "Key Features of Each Generation",
                    "slide_purpose": "reinforcement",
                    "selected_template": "Four columns",
                    "narration_role": "Reinforce",
                    "subtopic_name": "Introduction to Computer Generations",
                    "content_type": "FOUR_COLUMN_CARDS",
                    "narration_format": "points",
                    "narration_text": "First generation computers were massive, consuming enormous power with vacuum tubes. Second generation machines became more reliable with transistor technology. Third generation systems offered greater processing speed through integrated circuits. Fourth generation computers brought affordability and accessibility with microprocessor technology.",
                    "narration_constraints": {"point_count": 4},
                },
            ]
        }
    }

    result = content_generation_node(test_state)

    print("\n" + "=" * 80)
    print("DETAILED RESULTS")
    print("=" * 80 + "\n")

    for slide in result["slides"]["sub_1_2b67b6"]:
        print(f"SLIDE: {slide['slide_title']}")
        print(f"Content Type: {slide['content_type']}")
        print("-" * 80)

        visual = slide.get("visual_content", {})

        if "bullets" in visual:
            print(f"\nBULLETS GENERATED: {len(visual['bullets'])}")
            for i, bullet in enumerate(visual["bullets"], 1):
                print(f"\n  Bullet {i}:")
                print(f"    Icon: {bullet['icon']}")
                print(f"    Heading: {bullet['heading']}")
                print(f"    Description: {bullet['description']}")

        elif "timeline_items" in visual:
            print(f"\nTIMELINE ITEMS: {len(visual['timeline_items'])}")
            for i, item in enumerate(visual["timeline_items"], 1):
                print(f"\n  Timeline Item {i}:")
                print(f"    Phase: {item['phase_title']}")
                print(f"    Description: {item['description']}")

        elif "columns" in visual:
            print(f"\nCOLUMNS GENERATED: {len(visual['columns'])}")
            for i, col in enumerate(visual["columns"], 1):
                print(f"\n  Column {i}:")
                print(f"    Title: {col['title']}")
                print(f"    Text: {col['text']}")

        elif "subtitle" in visual:
            print(f"\nSUBTITLE: {visual['subtitle']}")

        print("\n" + "=" * 80 + "\n")
