import sys
import os
import json

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.langgraphflow import planning_graph


def test_incremental_planning():
    print("\n--- Testing Incremental Planning Stream ---")

    initial_state = {
        "user_input": "Parallel Computing",
        "topic": "",
        "difficulty": "Intermediate",
        "granularity": "Detailed",
        "sub_topics": [],
        "plans": {},
        "slides": {},
        "intro_text": "",
        "messages": [],
    }

    subtopics_found = False
    plans_received = 0

    print("Starting stream...")
    for chunk in planning_graph.stream(initial_state):
        for node_name, state_update in chunk.items():
            print(f"Node: {node_name}")

            if "sub_topics" in state_update and state_update["sub_topics"]:
                print(
                    f"  ✓ Subtopics generated: {[s['name'] for s in state_update['sub_topics']]}"
                )
                subtopics_found = True

            if "plans" in state_update and state_update["plans"]:
                new_plans = len(state_update["plans"])
                print(
                    f"  ⚡ Incremental update: {new_plans} subtopic(s) planned so far."
                )
                plans_received = new_plans

    print("\n--- Summary ---")
    print(f"Subtopics found: {subtopics_found}")
    print(f"Total subtopics planned: {plans_received}")

    if subtopics_found and plans_received > 0:
        print("\n✅ SUCCESS: Incremental planning is working as expected.")
    else:
        print("\n❌ FAILURE: Planning did not yield expected incremental updates.")


if __name__ == "__main__":
    test_incremental_planning()
