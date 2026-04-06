import sys
import os
import json

# Add api-server to path
base_dir = os.path.dirname(os.path.abspath(__file__))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

try:
    from app.services.node.v2.designer_slide_planning_v2_node import designer_slide_planning_v2_node
except ImportError as e:
    print(f"Import error: {e}")
    # Try alternative path if run from different location
    sys.path.insert(0, os.path.join(base_dir, "apps", "api-server"))
    from app.services.node.v2.designer_slide_planning_v2_node import designer_slide_planning_v2_node

def test_goal_generation():
    print("Testing goal generation in designer_slide_planning_v2_node...")
    
    # Mock state mimicking the output of teacher_planning_node
    state = {
        "sub_topics": [{"id": "sub1", "name": "Introduction to AI"}],
        "plans": {
            "sub1": [{
                "_teacher_blueprint": [
                    {
                        "title": "What is AI?",
                        "objective": "Define artificial intelligence and its scope.",
                        "slide_id": "sub1_t1",
                        "teaching_intent": "explain",
                        "coverage_scope": "foundation"
                    },
                    {
                        "title": "AI History",
                        # Missing objective to test fallback
                        "slide_id": "sub1_t2",
                        "teaching_intent": "explain",
                        "coverage_scope": "foundation"
                    }
                ],
                "_teacher_subtopic_name": "Introduction to AI"
            }]
        }
    }

    try:
        result = designer_slide_planning_v2_node(state)
        plans = result["plans"]["sub1"]
        
        all_passed = True
        for i, plan in enumerate(plans):
            title = plan.get("title")
            summary = plan.get("summary")
            
            print(f"\n--- Slide {i+1} ---")
            print(f"Title:   {title}")
            print(f"Summary: {summary}")
            
            if not summary:
                print(f"[FAIL] Missing summary for slide {i+1}")
                all_passed = False
            elif i == 0 and summary != "Define artificial intelligence and its scope.":
                print(f"[FAIL] Expected summary to match objective for slide 1. Got: {summary}")
                all_passed = False
            elif i == 1 and summary != "Explain the concept clearly.":
                print(f"[FAIL] Expected fallback summary for slide 2. Got: {summary}")
                all_passed = False
        
        if all_passed:
            print("\n[RESULT] PASS: All slides have correct summaries!")
        else:
            print("\n[RESULT] FAIL: Summary verification failed.")
            sys.exit(1)

    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    test_goal_generation()
