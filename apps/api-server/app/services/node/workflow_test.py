import os
import sys
import json
from typing import Dict, Any

# Ensure we can import from the app directory
# The script is in apps/api-server/app/services/node/
# We want to be able to import 'app.services.node' etc.
# So we add 'apps/api-server' to sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

# Also add the directory above 'app/' to handle 'from app.services...'
# If we are in 'apps/api-server/', then 'app/' is a subdirectory.
# So BASE_DIR should be 'apps/api-server/'

from app.services.node.topic_node import extract_topic
from app.services.node.sub_topic_node import extract_sub_topic
from app.services.node.new_slide_planner import plan_slides_for_subtopic
from app.services.node.content_generation_node import content_generation_node
from app.services.state import TutorState


def run_test():
    # Logging to file to avoid terminal garbling
    log_file = open("workflow_test_output.log", "w", encoding="utf-8")
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    sys.stdout = log_file
    sys.stderr = log_file

    def log(msg):
        print(msg, flush=True)

    log("==================================================")
    log("   AI TEACHER WORKFLOW TEST & DEBUG SCRIPT")
    log("==================================================")

    # 1. Use hardcoded topic for debugging consistency
    user_input = "Computer generations"
    log(f"\nTopic: {user_input}")

    # Initialize state
    state: TutorState = {
        "user_input": user_input,
        "slides": {},
        "plans": {},
        "layout_history": [],
    }

    log(f"\n[STEP 1] Extracting Topic...")
    state = extract_topic(state)
    log(f"  Extracted Topic: {state.get('topic')}")
    log(f"  Granularity: {state.get('granularity')}")

    log(f"\n[STEP 2] Extracting Sub-topics...")
    state = extract_sub_topic(state)
    sub_topics = state.get("sub_topics", [])
    log(f"  Found {len(sub_topics)} sub-topics:")
    for i, sub in enumerate(sub_topics):
        log(f"    {i+1}. {sub['name']} ({sub['difficulty']})")

    if not sub_topics:
        log("  No sub-topics found. Exiting.")
        return

    # 3. Plan slides for the first subtopic
    first_sub = sub_topics[0]
    log(f"\n[STEP 3] Planning Slides for Subtopic: '{first_sub['name']}'")
    # This will trigger the debug print in new_slide_planner.py
    plan = plan_slides_for_subtopic(first_sub)

    state["plans"][first_sub["id"]] = plan.get("slides", [])
    log(f"  Planned {len(state['plans'][first_sub['id']])} slides.")

    # 4. Generate content for the first 2 slides
    log("\n[STEP 4] Generating Content for First 5 Slides...")
    log("  (This will trigger debug prints for Narration and GyML generation)")

    # Run content generation (will do 5 slides if we loop or if node logic allows)
    # The node generates 2 slides by default if not specified otherwise in state?
    # Actually, content_generation_node processes the first 2 UNCOMPLETED slides.
    # We need to run it multiple times to do more.

    for i in range(3):  # Run 3 times to get 6 slides (2 each)
        state = content_generation_node(state)
        total_gen = sum(len(slides) for slides in state.get("slides", {}).values())
        log(f"  [Batch {i+1}] Processed {total_gen} total slides.")

    # 5. Output final state for inspection
    log(f"\n==================================================")
    log("           FINAL WORKFLOW SUMMARY")
    log("==================================================")
    generated_slides = state["slides"].get(first_sub["id"], [])
    log(f"Total Slides Generated: {len(generated_slides)}")

    for i, slide in enumerate(generated_slides):
        log(f"\n--- SLIDE {i+1} ---")
        log(f"TITLE: {slide.get('title')}")
        log(f"TEMPLATE: {slide.get('selected_template')}")
        log(f"NARRATION (First 150 chars): {slide.get('narration_text', '')[:150]}...")

        gyml = slide.get("gyml_content", {})
        log(f"INTENT: {gyml.get('intent')}")
        log(f"BLOCKS: {len(gyml.get('contentBlocks', []))} blocks generated.")

    log("\n[TEST COMPLETED SUCCESSFULLY]")
    log_file.close()


if __name__ == "__main__":
    try:
        run_test()
    except Exception as e:
        # We need a fallback log if run_test hasn't initialized log_file or failed early
        print(f"\n[CRITICAL ERROR] Workflow failed: {e}")
        import traceback

        traceback.print_exc()
