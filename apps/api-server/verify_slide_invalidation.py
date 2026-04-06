import asyncio
import logging
import sys
import os
from typing import Dict, Any, List
from unittest.mock import MagicMock, AsyncMock

# Add api-server to path
base_dir = os.path.dirname(os.path.abspath(__file__))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

# Mocking LangGraph which might attempt to import libraries not in current env
sys.modules['langgraph'] = MagicMock()
sys.modules['langgraph.graph'] = MagicMock()

# Setup logging to see the invalidation messages
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("app.api.generate")

# Import dependencies after mocking
try:
    from app.api.generate import run_generation_task, ConfirmPlanRequest, tasks_db
    import app.api.generate as generate_mod
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

# Mock full_graph to prevent actual generation
generate_mod.full_graph = MagicMock()
generate_mod.full_graph.astream = MagicMock(return_value=AsyncMock())
generate_mod.full_graph.astream.return_value.__aiter__.return_value = []

# Mock persistence to avoid file IO errors
generate_mod.persist_task_state = MagicMock()
generate_mod.save_tasks = MagicMock()

async def test_invalidation():
    task_id = "test-invalidation-task"
    print("\n" + "="*60)
    print("VERIFYING SLIDE INVALIDATION LOGIC")
    print("="*60)

    # setup initial state
    def reset_task_state():
        tasks_db[task_id] = {
            "status": "planning_completed",
            "result": {
                "plans": {
                    "sub1": [
                        {"slide_id": "s1", "title": "Intro", "summary": "Goal 1"},
                        {"slide_id": "s2", "title": "Middle", "summary": "Goal 2"},
                        {"slide_id": "s3", "title": "End", "summary": "Goal 3"}
                    ]
                },
                "slides": {
                    "sub1": [
                        {"slide_id": "s1", "html": "<html>1</html>"},
                        {"slide_id": "s2", "html": "<html>2</html>"},
                        {"slide_id": "s3", "html": "<html>3</html>"}
                    ]
                },
                "layout_history": ["template1", "template2"],
                "variant_history": ["v1", "v2"],
                "composition_history": ["c1", "c2"]
            }
        }

    # CASE 1: No changes
    reset_task_state()
    print("\n[CASE 1] No changes in plan")
    request1 = ConfirmPlanRequest(plans=tasks_db[task_id]["result"]["plans"])
    await run_generation_task(task_id, request1)
    
    slides = tasks_db[task_id]["result"]["slides"]["sub1"]
    print(f"  Slide count: {len(slides)} (Expected: 3)")
    assert len(slides) == 3, "Slides should not be invalidated when plan is identical"

    # CASE 2: Change middle slide (index 1)
    reset_task_state()
    print("\n[CASE 2] Modify second slide (index 1)")
    new_plans2 = {
        "sub1": [
            {"slide_id": "s1", "title": "Intro", "summary": "Goal 1"},
            {"slide_id": "s2", "title": "NEW MIDDLE", "summary": "Goal 2"}, # Change here
            {"slide_id": "s3", "title": "End", "summary": "Goal 3"}
        ]
    }
    request2 = ConfirmPlanRequest(plans=new_plans2)
    await run_generation_task(task_id, request2)
    
    slides = tasks_db[task_id]["result"]["slides"]["sub1"]
    print(f"  Slide count: {len(slides)} (Expected: 1)")
    assert len(slides) == 1, "Slides should be truncated to the earliest change index (1)"
    assert slides[0]["slide_id"] == "s1", "Only the first slide should remain"

    # CASE 3: Change first slide (index 0) - check history clearing
    reset_task_state()
    print("\n[CASE 3] Modify first slide (index 0)")
    new_plans3 = {
        "sub1": [
            {"slide_id": "s1", "title": "BRAND NEW INTRO", "summary": "Goal 1"}, # Change here
            {"slide_id": "s2", "title": "Middle", "summary": "Goal 2"},
            {"slide_id": "s3", "title": "End", "summary": "Goal 3"}
        ]
    }
    request3 = ConfirmPlanRequest(plans=new_plans3)
    await run_generation_task(task_id, request3)
    
    res = tasks_db[task_id]["result"]
    slides = res["slides"]["sub1"]
    print(f"  Slide count: {len(slides)} (Expected: 0)")
    assert len(slides) == 0, "All slides should be removed if index 0 changed"
    
    # Check histories
    histories = ["layout_history", "variant_history", "composition_history", "angle_history"]
    for h in histories:
        exists = h in res
        if not exists:
            print(f"  [OK] {h} cleared")
        else:
            print(f"  [FAIL] {h} still exists")
            assert h not in res

    print("\n" + "="*60)
    print("VERIFICATION COMPLETED: ALL CASES PASSED")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(test_invalidation())
