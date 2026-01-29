"""
End-to-End Workflow Test
Tests the complete LangGraph pipeline with Computer Generations topic
Saves the final state to a JSON file
"""

import sys
import os
import json
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.langgraphflow import compiled_graph


def run_workflow_test(topic: str, output_filename: str = None):
    """
    Run the complete workflow and save results

    Args:
        topic: The topic to generate slides for
        output_filename: Optional custom filename for output
    """
    print("\n" + "=" * 80)
    print("AI TEACHING SYSTEM - COMPLETE WORKFLOW TEST")
    print("=" * 80)
    print(f"\nTopic: {topic}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n" + "=" * 80 + "\n")

    # Initialize state as dictionary (nodes use dict-style access like state.get())
    # topic_node expects: state.get("user_input","")
    initial_state = {
        "user_input": topic,
        "topic": "",
        "granularity": "",
        "sub_topics": [],
        "slides": {},
        "intro_text": "",
        "messages": [],
    }

    print("Starting workflow execution...")
    print("-" * 80)

    try:
        # Run the compiled graph
        final_state = compiled_graph.invoke(initial_state)

        print("\n" + "=" * 80)
        print("WORKFLOW COMPLETED SUCCESSFULLY!")
        print("=" * 80 + "\n")

        # Print summary
        print("RESULTS SUMMARY:")
        print(f"- Topic: {final_state.get('topic', 'N/A')}")
        print(f"- Subtopics: {len(final_state.get('sub_topics', []))}")

        total_slides = sum(
            len(slides) for slides in final_state.get("slides", {}).values()
        )
        print(f"- Total Slides: {total_slides}")
        print(
            f"- Intro Text: {'Generated' if final_state.get('intro_text') else 'Not generated'}"
        )

        # Count content types
        content_stats = {}
        for sub_id, slide_list in final_state.get("slides", {}).items():
            for slide in slide_list:
                content_type = slide.get("content_type", "UNKNOWN")
                content_stats[content_type] = content_stats.get(content_type, 0) + 1

        print("\nContent Type Distribution:")
        for content_type, count in content_stats.items():
            print(f"  - {content_type}: {count}")

        # Save to file
        if output_filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"workflow_output_{timestamp}.json"

        output_path = os.path.join(os.path.dirname(__file__), output_filename)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(final_state, f, indent=2, ensure_ascii=False)

        print(f"\n✓ Results saved to: {output_path}")
        print(f"  File size: {os.path.getsize(output_path) / 1024:.2f} KB")

        return final_state

    except Exception as e:
        print("\n" + "=" * 80)
        print("WORKFLOW FAILED!")
        print("=" * 80)
        print(f"\nError: {str(e)}")
        print(f"Error Type: {type(e).__name__}")

        import traceback

        print("\nFull Traceback:")
        print("-" * 80)
        traceback.print_exc()

        return None


if __name__ == "__main__":
    # Run test with Computer Generations
    topic = "Computer Generations"
    output_file = "computer_generations_workflow_output.json"

    final_state = run_workflow_test(topic, output_file)

    if final_state:
        print("\n" + "=" * 80)
        print("TEST COMPLETE!")
        print("=" * 80)
        print("\n✓ Workflow executed successfully")
        print(f"✓ Results saved to: {output_file}")
        print("\nYou can now review the generated content in the output JSON file.")
    else:
        print("\nTest failed. Check error messages above.")
