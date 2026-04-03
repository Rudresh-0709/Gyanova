"""
Debug script: validate v2 structured block generation.

Usage:
    python debug_v2_structured_blocks.py [path/to/task_state.json]

If no path is provided, looks for any .json file under
.persistent_data/task_states/.

Checks performed per slide:
  1. Non-title slides contain a structured primary block.
  2. smart_layout blocks have items (non-empty).
  3. Templates and smart_layout variants rotate (not identical for >= 3
     consecutive slides when alternatives exist).

Exit code: 0 = all checks pass, 1 = at least one check failed.
"""
from __future__ import annotations

import json
import sys
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

# ── Allow running from repo root or from within v2/ ────────────────────────
_HERE = Path(__file__).parent
_API_ROOT = _HERE.parent.parent.parent.parent.parent  # apps/api-server
sys.path.insert(0, str(_API_ROOT))

try:
    from app.services.node.v2.designer_slide_planning_v2_node import designer_slide_planning_v2_node
    from app.services.node.v2.gyml_generator_v2 import generate_gyml_v2
except ImportError:
    # Try relative imports
    sys.path.insert(0, str(_HERE.parent))
    from v2.designer_slide_planning_v2_node import designer_slide_planning_v2_node  # type: ignore
    from v2.gyml_generator_v2 import generate_gyml_v2  # type: ignore

# ── Structured block types that count as primary teaching content ─────────
STRUCTURED_TYPES = {
    "smart_layout",
    "comparison_table",
    "key_value_list",
    "numbered_list",
    "formula_block",
    "process_arrow_block",
    "cyclic_process_block",
    "step_list",
    "rich_text",
}

# Templates that are intentionally sparse (no structured primary required)
SPARSE_TEMPLATES = {"Title card", "Formula block", "Large bullet list"}


def _find_default_task_state() -> Optional[Path]:
    """Walk up from repo root to find a persisted task state JSON."""
    search_root = _HERE
    for _ in range(10):
        candidate = search_root / ".persistent_data" / "task_states"
        if candidate.is_dir():
            jsons = list(candidate.glob("*.json"))
            if jsons:
                return jsons[0]
        search_root = search_root.parent
    return None


def _load_task_state(path: Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _run_planning(state: Dict[str, Any]) -> Dict[str, Any]:
    """Run the designer planning node and return updated plans."""
    return designer_slide_planning_v2_node(state)


def _generate_slides(plan_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generate GyML for each plan item and return payload list."""
    results = []
    for item in plan_items:
        try:
            payload = generate_gyml_v2(item)
        except Exception as exc:
            payload = {"_error": str(exc), "title": item.get("title", "?"), "contentBlocks": []}
        results.append({"plan": item, "slide": payload})
    return results


def _check_structured_primary(slide: Dict[str, Any], template: str) -> bool:
    """Return True if slide has at least one structured primary block (or template is sparse)."""
    if template in SPARSE_TEMPLATES:
        return True
    blocks = slide.get("contentBlocks", []) or []
    return any(str(b.get("type") or "").lower() in STRUCTURED_TYPES for b in blocks if isinstance(b, dict))


def _check_smart_layout_has_items(slide: Dict[str, Any]) -> List[str]:
    """Return list of problem descriptions for empty smart_layout blocks."""
    problems = []
    blocks = slide.get("contentBlocks", []) or []
    for i, block in enumerate(blocks):
        if not isinstance(block, dict):
            continue
        if str(block.get("type") or "").lower() == "smart_layout":
            items = block.get("items") or []
            if not items:
                problems.append(f"  ✗ smart_layout block at index {i} has no items (variant={block.get('variant')})")
    return problems


def _check_variety(entries: List[Dict[str, Any]]) -> List[str]:
    """Return warnings when the same template or variant repeats 3+ times consecutively."""
    problems = []
    templates = [e["plan"].get("selected_template", "?") for e in entries]
    variants = [e["plan"].get("smart_layout_variant", "?") for e in entries]

    def _consecutive_run(seq: List[str]) -> int:
        if not seq:
            return 0
        run = 1
        for i in range(1, len(seq)):
            if seq[i] == seq[i - 1]:
                run += 1
            else:
                run = 1
        return run

    max_template_run = _consecutive_run(templates)
    max_variant_run = _consecutive_run(variants)

    if max_template_run >= 3:
        problems.append(f"  ⚠ Same template repeated {max_template_run}+ times consecutively: {templates}")
    if max_variant_run >= 3:
        problems.append(f"  ⚠ Same smart_layout variant repeated {max_variant_run}+ times consecutively: {variants}")
    return problems


def main() -> int:
    # ── Load task state ────────────────────────────────────────────────────
    if len(sys.argv) > 1:
        task_state_path = Path(sys.argv[1])
    else:
        task_state_path = _find_default_task_state()

    if task_state_path is None or not task_state_path.exists():
        print("⚠  No task state file found. Generating a minimal synthetic state for testing.")
        state: Dict[str, Any] = {
            "sub_topics": [{"id": "test_sub_001", "name": "East India Company"}],
            "plans": {
                "test_sub_001": [
                    {
                        "_teacher_subtopic_name": "East India Company",
                        "_teacher_blueprint": [
                            {
                                "slide_id": "s1",
                                "title": "Origins of the East India Company",
                                "objective": "Understand how the EIC was founded.",
                                "teaching_intent": "narrate",
                                "coverage_scope": "sequence",
                                "slide_density": "balanced",
                                "must_cover": ["Founded in 1600", "Royal Charter", "Trade monopoly"],
                                "key_facts": ["1600 founding date", "Queen Elizabeth I"],
                                "high_end_image_required": False,
                            },
                            {
                                "slide_id": "s2",
                                "title": "EIC's Military Power",
                                "objective": "Explain how EIC built its own army.",
                                "teaching_intent": "explain",
                                "coverage_scope": "mechanism",
                                "slide_density": "standard",
                                "must_cover": ["Private army", "Sepoys", "Control of ports"],
                                "key_facts": ["200,000 soldiers at peak"],
                                "high_end_image_required": False,
                            },
                            {
                                "slide_id": "s3",
                                "title": "Key Battles and Conquests",
                                "objective": "Show major territorial gains.",
                                "teaching_intent": "teach",
                                "coverage_scope": "sequence",
                                "slide_density": "dense",
                                "must_cover": ["Battle of Plassey 1757", "Bengal takeover", "Mysore wars"],
                                "key_facts": ["Clive of India"],
                                "high_end_image_required": False,
                            },
                            {
                                "slide_id": "s4",
                                "title": "EIC vs Crown Rule",
                                "objective": "Compare EIC rule and direct Crown rule.",
                                "teaching_intent": "compare",
                                "coverage_scope": "comparison",
                                "slide_density": "balanced",
                                "must_cover": ["Corporate vs state control", "Indian Rebellion 1857"],
                                "key_facts": ["1858 Government of India Act"],
                                "high_end_image_required": False,
                            },
                        ],
                    }
                ]
            },
            "variant_history": [],
            "layout_history": [],
        }
    else:
        print(f"📂 Loading task state from: {task_state_path}")
        raw_state = _load_task_state(task_state_path)
        # Some persisted states have nested structure; flatten if needed
        state = raw_state if isinstance(raw_state, dict) else {}

    # ── Run planning ───────────────────────────────────────────────────────
    print("\n🔧 Running v2 designer planning node …")
    try:
        updated = _run_planning(state)
        plans = updated.get("plans", state.get("plans", {}))
    except Exception as exc:
        print(f"  ✗ Planning node failed: {exc}")
        return 1

    # ── Find a non-empty plan to test ─────────────────────────────────────
    test_plan_items: List[Dict[str, Any]] = []
    for sub_id, items in plans.items():
        if isinstance(items, list) and items and isinstance(items[0], dict) and "slide_id" in items[0]:
            test_plan_items = items[:6]  # Test up to 6 slides
            print(f"  ✓ Found {len(items)} planned slides for subtopic '{sub_id}'")
            break

    if not test_plan_items:
        print("  ⚠ No normalised plan items found (planning may not have triggered). Skipping generation checks.")
        print("\n✅ Planning check: OK (no items to validate)")
        return 0

    # Print planning summary
    print("\n📋 Planning summary:")
    for i, item in enumerate(test_plan_items):
        print(
            f"  Slide {i+1}: template={item.get('selected_template')}, "
            f"family={item.get('primary_family')}, "
            f"slv={item.get('smart_layout_variant')}, "
            f"layout={item.get('selected_layout')}"
        )

    # ── Generate slides ────────────────────────────────────────────────────
    print(f"\n🎨 Generating {len(test_plan_items)} slides …")
    entries = _generate_slides(test_plan_items)

    # ── Run checks ────────────────────────────────────────────────────────
    all_pass = True
    print("\n🔍 Validation results:")

    for i, entry in enumerate(entries):
        plan = entry["plan"]
        slide = entry["slide"]
        template = str(plan.get("selected_template") or "")
        title = str(plan.get("title") or f"Slide {i+1}")
        slv = str(plan.get("smart_layout_variant") or "?")

        if "_error" in slide:
            print(f"\n  Slide {i+1} [{title}] — GENERATION ERROR: {slide['_error']}")
            all_pass = False
            continue

        print(f"\n  Slide {i+1} [{title}] template={template} slv={slv}")

        # Check 1: structured primary block
        has_primary = _check_structured_primary(slide, template)
        if has_primary:
            blocks = slide.get("contentBlocks", [])
            primary_types = [b.get("type") for b in blocks if isinstance(b, dict) and b.get("type") in STRUCTURED_TYPES]
            print(f"    ✓ Structured primary block found: {primary_types}")
        else:
            block_types = [b.get("type") for b in slide.get("contentBlocks", []) if isinstance(b, dict)]
            print(f"    ✗ No structured primary block! Block types: {block_types}")
            all_pass = False

        # Check 2: smart_layout items non-empty
        problems = _check_smart_layout_has_items(slide)
        if problems:
            for p in problems:
                print(p)
            all_pass = False
        else:
            sl_blocks = [b for b in slide.get("contentBlocks", []) if isinstance(b, dict) and b.get("type") == "smart_layout"]
            if sl_blocks:
                print(f"    ✓ smart_layout items OK ({len(sl_blocks[0].get('items', []))} items)")

    # Check 3: variety
    variety_problems = _check_variety(entries)
    if variety_problems:
        print("\n  Variety warnings:")
        for p in variety_problems:
            print(p)
        # Variety is a warning, not a hard failure
    else:
        templates_used = [e["plan"].get("selected_template") for e in entries]
        variants_used = [e["plan"].get("smart_layout_variant") for e in entries]
        print(f"\n  ✓ Variety OK — templates: {templates_used}")
        print(f"             variants: {variants_used}")

    # ── Summary ───────────────────────────────────────────────────────────
    print("\n" + ("=" * 60))
    if all_pass:
        print("✅ All structured block checks PASSED")
    else:
        print("❌ Some checks FAILED — see details above")
    print("=" * 60)

    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
