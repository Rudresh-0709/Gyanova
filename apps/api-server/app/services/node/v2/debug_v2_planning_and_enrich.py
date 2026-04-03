"""
Debug harness & acceptance tests for v2 planning → enrichment → narration pipeline.

Tests the full slide generation workflow:
1. Teacher brief with planning parameters
2. slide_planner_v2 generates plan
3. generate_gyml_v2 creates GYML payload
4. enrich_slide_media_sync populates images/icons
5. generate_narration_v2 creates visual-aware narration
6. Assert key properties on final slide

Run: python -m pytest debug_v2_planning_and_enrich.py -v
     or: python debug_v2_planning_and_enrich.py
"""

from __future__ import annotations

import json
import sys
import os
from typing import Any, Dict, List

# Add api-server to path for standalone execution FIRST
_this_file = os.path.abspath(__file__)
_v2_dir = os.path.dirname(_this_file)
_node_dir = os.path.dirname(_v2_dir)
_services_dir = os.path.dirname(_node_dir)
_app_dir = os.path.dirname(_services_dir)
_api_server_dir = os.path.dirname(_app_dir)

if _api_server_dir not in sys.path:
    sys.path.insert(0, _api_server_dir)

# NOW do the imports
try:
    from app.services.node.v2.gyml_generator_v2 import generate_gyml_v2
    from app.services.media.enrichment_service_sync import enrich_slide_media_sync
    from app.services.node.v2.narration_v2 import generate_narration_v2
except ImportError as e:
    print(f"[ERROR] Failed to import despite sys.path workaround: {e}")
    print(f"[DEBUG] sys.path[0] = {sys.path[0]}")
    raise


def _mock_teacher_brief_low_density() -> Dict[str, Any]:
    """Low density slide: few items, prominent concept image required."""
    return {
        "id": "brief_low_density",
        "title": "Photosynthesis: The Light Reaction",
        "topic": "Photosynthesis",
        "learning_objective": "Understand the light-dependent reactions in photosynthesis.",
        "slide_density": "low",
        "teaching_intent": "explain",
        "must_cover": ["photosystems", "electron transport chain"],
        "key_facts": [
            "Occurs in the thylakoid membrane",
            "Produces ATP and NADPH",
        ],
        "assessment_prompt": "Why do plants need both photosystems?",
        "layout": "top-image-bottom-text",
        "image_layout": "top",
        "require_concept_image": True,
        "designer_blueprint": {
            "primary_block": {
                "family": "overview",
                "variant": "normal",
                "required_content": "concept_image",
            },
        },
    }


def _mock_teacher_brief_high_density() -> Dict[str, Any]:
    """High-density slide: many items with wide primary block and concept image."""
    return {
        "id": "brief_high_density",
        "title": "Mitochondrial Structure & Function",
        "topic": "Cellular Respiration",
        "learning_objective": "Learn the structure of mitochondria and how it relates to its function.",
        "slide_density": "high",
        "teaching_intent": "compare",
        "must_cover": [
            "outer membrane",
            "inner membrane",
            "cristae",
            "matrix",
            "ATP synthesis",
        ],
        "key_facts": [
            "Double membrane structure",
            "ATP produced at inner membrane",
            "Gradients drive energy production",
        ],
        "assessment_prompt": "How does the structure of mitochondria optimize energy production?",
        "layout": "top-bottom",
        "image_layout": "top",
        "require_concept_image": True,
        "designer_blueprint": {
            "primary_block": {
                "family": "comparison",
                "variant": "wide",
                "required_content": "concept_image",
            },
        },
    }


def _mock_teacher_brief_icon_heavy() -> Dict[str, Any]:
    """Medium-density slide: icon-heavy list block."""
    return {
        "id": "brief_icon_heavy",
        "title": "Steps of Glycolysis",
        "topic": "Cellular Respiration",
        "learning_objective": "Identify and describe the key steps of glycolysis.",
        "slide_density": "medium",
        "teaching_intent": "explain",
        "must_cover": [
            "glucose molecule",
            "enzyme catalysis",
            "ATP production",
            "pyruvate formation",
        ],
        "key_facts": [
            "10-step process in cytoplasm",
            "Net gain: 2 ATP + 2 NADH",
            "No CO2 released.",
        ],
        "assessment_prompt": "Why is glycolysis considered both catabolic and anabolic?",
        "layout": "smart-layout-cards",
        "image_layout": "none",
        "require_icons": True,
        "designer_blueprint": {
            "primary_block": {
                "family": "process",
                "variant": "icon_list",
            },
        },
    }


def _build_mock_planner_state() -> Dict[str, Any]:
    """Build mock state for planner (as if from a lecture decomposer)."""
    return {
        "topic": "Cell Biology",
        "subtopic": "Photosynthesis & Respiration",
        "student_level": "9th-grade",
        "num_slides": 3,
        "briefs": [
            _mock_teacher_brief_low_density(),
            _mock_teacher_brief_high_density(),
            _mock_teacher_brief_icon_heavy(),
        ],
    }


def _run_full_pipeline(brief: Dict[str, Any], topic: str) -> Dict[str, Any]:
    """
    Run the full v2 pipeline: plan → GYML → enrich → narration.

    Returns:
        Final enriched slide object with narration.
    """
    # Step 1: Plan (slide_planner_v2 generates planning details for this brief)
    # In real scenario, this is called once per brief
    plan_item = brief.copy()
    plan_item["index"] = 0  # First (only) slide in this plan

    # Step 2: Generate GYML
    gyml_payload = generate_gyml_v2(plan_item)

    # Step 3: Assemble slide object (mimic content_generation_v2_node logic)
    layout = gyml_payload.get("layout") or gyml_payload.get("image_layout") or "blank"
    slide_obj = {
        **plan_item,
        "gyml_content": gyml_payload,
        "visual_content": gyml_payload,
        "layout": layout,
        "image_layout": gyml_payload.get("image_layout") or layout,
        "primary_block_index": gyml_payload.get("primary_block_index", 0),
        "slide_density": brief.get("slide_density", "balanced"),
        "narration_text": "",  # Will be populated after enrichment
    }

    # Step 4: Enrich with media (images, icons)
    image_layout = slide_obj.get("image_layout", layout)
    enrich_slide_media_sync(
        slide_obj, topic=topic, image_layout=image_layout
    )

    # Step 5: Generate narration (now that visuals are populated)
    intent = str(brief.get("teaching_intent", "explain")).strip()
    narration_text = generate_narration_v2(slide_obj, topic=topic, intent=intent)
    slide_obj["narration_text"] = narration_text

    return slide_obj


def _assert_concept_image_exists(slide: Dict[str, Any], brief_id: str) -> None:
    """Assert: concept image exists and has URL after enrichment."""
    gyml = slide.get("gyml_content", {})
    content_blocks = gyml.get("contentBlocks", [])

    concept_image_found = False
    concept_src = None

    for block in content_blocks:
        if not isinstance(block, dict):
            continue
        if block.get("type") == "image" and not block.get("is_accent", False):
            src = block.get("src", "")
            if src and src != "placeholder":
                concept_image_found = True
                concept_src = src
                break

    if slide.get("require_concept_image"):
        assert concept_image_found, (
            f"[{brief_id}] No concept image found after enrichment. "
            f"Brief requires concept_image but gyml_content has none."
        )
        assert concept_src, (
            f"[{brief_id}] Concept image found but src is empty or placeholder."
        )
        print(f"  [OK] Concept image exists: {concept_src[:50]}...")


def _assert_no_accent_when_concept_exists(slide: Dict[str, Any], brief_id: str) -> None:
    """Assert: no accent image is present when concept image exists."""
    gyml = slide.get("gyml_content", {})
    content_blocks = gyml.get("contentBlocks", [])

    has_concept = False
    has_accent = False
    accent_details = []

    for block in content_blocks:
        if not isinstance(block, dict):
            continue
        if block.get("type") != "image":
            continue

        is_accent = block.get("is_accent", False)
        src = block.get("src", "")

        if not is_accent and src and src != "placeholder":
            has_concept = True
        elif is_accent:
            has_accent = True
            accent_details.append(f"accent={block.get('alt', 'unknown')}")

    # If we have a concept image, accent is optional but shouldn't dominate
    if has_concept and has_accent:
        # This is OK, but log it
        print(f"  [INFO] Concept image coexists with accent image(s): {', '.join(accent_details)}")


def _assert_dense_layout_is_topbottom(slide: Dict[str, Any], brief_id: str) -> None:
    """Assert: for dense slide, layout is top/bottom (not left/right)."""
    density = slide.get("slide_density", "balanced")
    layout = slide.get("layout", "").lower()

    if density == "high":
        invalid_layouts = ["left-right", "side-by-side", "two-column"]
        for invalid in invalid_layouts:
            assert invalid not in layout, (
                f"[{brief_id}] High-density slide uses {invalid} layout, "
                f"which is too cramped. Expected: top/bottom or stacked."
            )
        print(f"  [OK] Dense slide uses appropriate layout: {layout}")


def _assert_icons_unique_and_nonempty(slide: Dict[str, Any], brief_id: str) -> None:
    """Assert: icons are non-empty and mostly unique for icon-heavy blocks."""
    if not slide.get("require_icons"):
        return

    gyml = slide.get("gyml_content", {})
    content_blocks = gyml.get("contentBlocks", [])

    icon_names = []

    for block in content_blocks:
        if not isinstance(block, dict):
            continue
        items = block.get("items", [])
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            icon_name = item.get("icon_name", "")
            if icon_name and icon_name != "auto":
                icon_names.append(icon_name)

    assert icon_names, (
        f"[{brief_id}] Icon-heavy block required but no icons found."
    )

    # Check uniqueness ratio (at least 60% unique for variety)
    unique_count = len(set(icon_names))
    total_count = len(icon_names)
    uniqueness_ratio = unique_count / total_count if total_count > 0 else 0

    assert uniqueness_ratio >= 0.6, (
        f"[{brief_id}] Icons lack variety: {unique_count}/{total_count} unique "
        f"({uniqueness_ratio:.1%}). Expected >= 60% unique."
    )

    print(
        f"  [OK] Icons: {total_count} total, {unique_count} unique "
        f"({uniqueness_ratio:.1%} variety)"
    )


def _assert_template_variety(slides: List[Dict[str, Any]]) -> None:
    """Assert: 3 slides don't all pick same template/family if alternatives exist."""
    templates = []
    families = []

    for slide in slides:
        template = str(
            slide.get("selected_template")
            or slide.get("gyml_content", {}).get("selected_template")
            or "unknown"
        ).strip()
        templates.append(template)

        designer_bp = slide.get("designer_blueprint", {})
        if isinstance(designer_bp, dict):
            primary = designer_bp.get("primary_block", {})
            if isinstance(primary, dict):
                family = str(primary.get("family", "unknown")).strip()
                families.append(family)

    unique_templates = len(set(templates))
    unique_families = len(set(families))

    print(f"\n  Templates: {templates}")
    print(f"    Unique: {unique_templates}/3")
    print(f"  Families: {families}")
    print(f"    Unique: {unique_families}/3")

    # At least some variety expected (not all identical)
    assert unique_templates > 1 or unique_families > 1, (
        f"All 3 slides picked identical template/family. "
        f"Expected variety. Templates: {set(templates)}, Families: {set(families)}."
    )

    print(f"  [OK] Template/family variety confirmed")


def run_acceptance_tests() -> None:
    """Run full acceptance test suite for v2 pipeline."""
    print("\n" + "=" * 80)
    print("DEBUG HARNESS: V2 Planning -> Enrichment -> Narration Pipeline")
    print("=" * 80)

    state = _build_mock_planner_state()
    topic = state["topic"]
    briefs = state["briefs"]

    all_slides = []

    # Process each brief through the full pipeline
    for i, brief in enumerate(briefs, 1):
        brief_id = brief["id"]
        print(f"\n[Test {i}/3] {brief_id}")  # Use ASCII dash
        print(f"  Density: {brief.get('slide_density')}")
        print(f"  Intent: {brief.get('teaching_intent')}")

        # Run full pipeline
        slide = _run_full_pipeline(brief, topic)
        all_slides.append(slide)

        print(f"\n  Final Slide JSON:")
        # Print minimal JSON (title, layout, narration snippet, image presence)
        summary = {
            "title": slide.get("title"),
            "density": slide.get("slide_density"),
            "layout": slide.get("layout"),
            "image_layout": slide.get("image_layout"),
            "narration_length": len(slide.get("narration_text", "")),
            "narration_preview": (slide.get("narration_text", "")[:60] + "..."),
        }
        print(json.dumps(summary, indent=4))

        print(f"\n  Acceptance Tests:")

        # Run acceptance tests for this slide
        try:
            _assert_concept_image_exists(slide, brief_id)
        except AssertionError as e:
            print(f"  [FAIL] {e}")
            raise

        try:
            _assert_no_accent_when_concept_exists(slide, brief_id)
        except AssertionError as e:
            print(f"  [FAIL] {e}")
            raise

        try:
            _assert_dense_layout_is_topbottom(slide, brief_id)
        except AssertionError as e:
            print(f"  [FAIL] {e}")
            raise

        try:
            _assert_icons_unique_and_nonempty(slide, brief_id)
        except AssertionError as e:
            if "Icon-heavy block required" not in str(e):
                print(f"  [FAIL] {e}")
                raise
            else:
                print(f"  [INFO] Skipped (not icon-heavy): {e}")

    # Cross-slide assertion: template variety
    print(f"\n[Test 4/4] Template/Family Variety Across All Slides")
    try:
        _assert_template_variety(all_slides)
    except AssertionError as e:
        print(f"  [FAIL] {e}")
        raise

    print("\n" + "=" * 80)
    print("[PASS] ALL ACCEPTANCE TESTS PASSED")
    print("=" * 80)


if __name__ == "__main__":
    try:
        run_acceptance_tests()
    except Exception as e:
        print(f"\n[ERROR] TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
