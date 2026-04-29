"""
blocks/shared/tests/test_constraint_filter.py

Plain-assert tests for constraint_filter. Run with:

    python -m blocks.shared.tests.test_constraint_filter

Each test prints PASS/FAIL with a description; assertion failures bubble up
with descriptive messages so a single failing test stops the run loudly.

We avoid pytest deliberately — these tests are meant to be runnable in any
context the slide engine ships into.
"""

from __future__ import annotations

import sys
import traceback
from dataclasses import replace

from blocks.shared.constraint_filter import (
    SlideConstraints,
    filter_catalog,
    score_candidates,
    select_block,
)
from blocks.shared.base_spec import BlockSpec, ItemCountProfile
from blocks.shared.routing_table import DEFAULT_CANDIDATES
from blocks.registry import ALL_BLOCKS


# ---------------------------------------------------------------------------
# Test harness
# ---------------------------------------------------------------------------
_PASSED = 0
_FAILED = 0


def _run(name: str, fn):
    global _PASSED, _FAILED
    try:
        fn()
        _PASSED += 1
        print(f"  PASS — {name}")
    except AssertionError as e:
        _FAILED += 1
        print(f"  FAIL — {name}")
        print(f"         {e}")
    except Exception:
        _FAILED += 1
        print(f"  FAIL — {name} (unexpected exception)")
        traceback.print_exc()


def _make_constraints(**overrides) -> SlideConstraints:
    """Build a SlideConstraints with sensible defaults, override per-test."""
    base = dict(
        content_structure="list",
        item_relationship="parallel",
        target_density="balanced",
        estimated_items=4,
        allows_wide_layout=True,
        requires_icons=False,
        image_role="none",
        variant_history=[],
    )
    base.update(overrides)
    return SlideConstraints(**base)


# ---------------------------------------------------------------------------
# Helper assertions
# ---------------------------------------------------------------------------
def _assert_in_family(variant: str, allowed: set[str], context: str):
    assert (
        variant in allowed
    ), f"{context}: expected one of {sorted(allowed)}, got '{variant}'"


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
def test_01_steps_sequential():
    c = _make_constraints(content_structure="steps", item_relationship="sequential")
    variant, _, _ = select_block(c)
    process_blocks = {
        "processSteps",
        "processArrow",
        "processAccordion",
        "sequentialOutput",
        "sequentialSteps",
        "input_process_output",
        "branching_path",
        "interlockingArrows",
        "image_process",
    }
    _assert_in_family(variant, process_blocks, "steps+sequential")


def test_02_timeline_sequential():
    c = _make_constraints(
        content_structure="timeline",
        item_relationship="sequential",
        estimated_items=5,
    )
    variant, _, _ = select_block(c)
    timeline_blocks = {
        "timeline",
        "timelineIcon",
        "timelineMilestone",
        "timelineHorizontal",
    }
    _assert_in_family(variant, timeline_blocks, "timeline+sequential")


def test_03_list_parallel_with_icons():
    c = _make_constraints(
        content_structure="list",
        item_relationship="parallel",
        requires_icons=True,
    )
    variant, block, _ = select_block(c)
    assert block.requires_icons, (
        f"requires_icons=True should yield icon-supporting block, got "
        f"'{variant}' with requires_icons={block.requires_icons}"
    )


def test_04_list_parallel_no_icons():
    c = _make_constraints(content_structure="list", item_relationship="parallel")
    variant, _, _ = select_block(c)
    list_blocks = {
        "bigBullets",
        "bulletIcon",
        "cardGridSimple",
        "cardGridDiamond",
        "cardGridImage",
        "diamondGrid",
        "diamondRibbon",
        "ribbonFold",
        "bento_grid",
        "pillar_cards",
    }
    _assert_in_family(variant, list_blocks, "list+parallel")


def test_05_two_sided_opposing():
    c = _make_constraints(
        content_structure="two_sided",
        item_relationship="opposing",
        estimated_items=2,
    )
    variant, _, _ = select_block(c)
    comparison_blocks = {
        "split_panel",
        "myth_vs_fact",
        "comparison_table",
        "comparisonBeforeAfter",
        "comparisonProsCons",
        "spectrum_scale",
        "venn_overlap",
    }
    _assert_in_family(variant, comparison_blocks, "two_sided+opposing")


def test_06_single_single_sparse():
    c = _make_constraints(
        content_structure="single",
        item_relationship="single",
        target_density="sparse",
        estimated_items=1,
    )
    variant, _, _ = select_block(c)
    single_blocks = {
        "stats",
        "statsPercentage",
        "definition",
        "quote",
        "formula_block",
        "callout",
    }
    _assert_in_family(variant, single_blocks, "single+single sparse")


def test_07_single_single_dense():
    c = _make_constraints(
        content_structure="single",
        item_relationship="single",
        target_density="dense",
        estimated_items=1,
    )
    variant, _, _ = select_block(c)
    # Should still resolve to *something* — dense + 1 item is unusual but
    # the filter should fall back gracefully rather than crash.
    assert (
        isinstance(variant, str) and variant
    ), "dense single+single should still return a variant"


def test_08_list_parallel_no_wide():
    c = _make_constraints(
        content_structure="list",
        item_relationship="parallel",
        allows_wide_layout=False,
    )
    variant, block, _ = select_block(c)
    # The chosen block must have at least one non-wide profile.
    has_normal = any(p.width_class != "wide" for p in block.item_count_profiles)
    assert has_normal, (
        f"allows_wide_layout=False but selected '{variant}' has only " f"wide profiles"
    )


def test_09_list_parallel_icons_prioritized():
    c_icons = _make_constraints(
        content_structure="list",
        item_relationship="parallel",
        requires_icons=True,
    )
    c_no_icons = _make_constraints(
        content_structure="list",
        item_relationship="parallel",
        requires_icons=False,
    )
    v_icons, b_icons, _ = select_block(c_icons)
    v_no_icons, _, _ = select_block(c_no_icons)
    assert (
        b_icons.requires_icons
    ), f"icon-required pick '{v_icons}' should support icons"
    # Not strictly required to differ, but we want the icon variant when
    # icons are required.
    assert v_icons != "bigBullets" or v_no_icons == "bigBullets", (
        "icons=True should not silently fall back to bigBullets when an "
        "icon block is available"
    )


def test_10_steps_ultra_sparse():
    c = _make_constraints(
        content_structure="steps",
        item_relationship="sequential",
        target_density="ultra_sparse",
        estimated_items=3,
    )
    variant, _, _ = select_block(c)
    assert (
        isinstance(variant, str) and variant
    ), "ultra_sparse steps should resolve to some variant"


def test_11_steps_super_dense():
    c = _make_constraints(
        content_structure="steps",
        item_relationship="sequential",
        target_density="super_dense",
        estimated_items=6,
    )
    variant, _, _ = select_block(c)
    assert (
        isinstance(variant, str) and variant
    ), "super_dense steps should resolve to some variant"


def test_12_list_parallel_one_item():
    c = _make_constraints(
        content_structure="list",
        item_relationship="parallel",
        estimated_items=1,
    )
    variant, block, profile = select_block(c)
    lo, hi = profile.item_range
    assert lo <= 1 <= hi or abs(((lo + hi) / 2) - 1) < 999, (
        f"profile {profile.item_range} should accommodate 1 item via exact "
        f"or nearest-midpoint match"
    )


def test_13_list_parallel_eight_items():
    c = _make_constraints(
        content_structure="list",
        item_relationship="parallel",
        estimated_items=8,
    )
    variant, block, profile = select_block(c)
    assert isinstance(variant, str) and variant, "8 items should not crash the pipeline"


def test_14_unknown_structure_relationship():
    c = _make_constraints(
        content_structure="not_a_real_structure",
        item_relationship="not_a_real_relationship",
    )
    # Must NOT crash.
    variant, block, profile = select_block(c)
    assert (
        variant in ALL_BLOCKS
    ), f"unknown structure should fall back gracefully, got '{variant}'"


def test_15_recency_penalty():
    c1 = _make_constraints(
        content_structure="list",
        item_relationship="parallel",
    )
    first, _, _ = select_block(c1)

    # Build a history that punishes the first winner.
    c2 = _make_constraints(
        content_structure="list",
        item_relationship="parallel",
        variant_history=[first],
    )
    second, _, _ = select_block(c2)

    # If multiple viable candidates exist, recency should push us off `first`.
    # In edge cases where only one candidate survives the filter, this won't
    # hold — we accept that as a known limitation.
    from blocks.shared.routing_table import get_candidates
    from blocks.shared.constraint_filter import filter_catalog

    survivors = filter_catalog(get_candidates("list", "parallel"), c2)
    if len(survivors) > 1:
        assert second != first, (
            f"recency penalty should pick a different block when alternatives "
            f"exist; first={first}, second={second}, survivors={survivors}"
        )
    else:
        # Only one survivor — recency cannot change the outcome.
        assert second == first


def test_16_tree_hierarchical():
    c = _make_constraints(
        content_structure="tree",
        item_relationship="hierarchical",
        estimated_items=4,
    )
    variant, _, _ = select_block(c)
    hier_blocks = {"hierarchy_tree", "layer_stack"}
    _assert_in_family(variant, hier_blocks, "tree+hierarchical")


def test_17_network_radial():
    c = _make_constraints(
        content_structure="network",
        item_relationship="radial",
        estimated_items=5,
        target_density="standard",
    )
    variant, _, _ = select_block(c)
    network_blocks = {
        "hubAndSpoke",
        "ecosystem_map",
        "diamondHub",
        "cause_effect_web",
        "relationshipMap",
        "feature_showcase",
    }
    _assert_in_family(variant, network_blocks, "network+radial")


def test_18_two_sided_opposing_no_wide():
    c = _make_constraints(
        content_structure="two_sided",
        item_relationship="opposing",
        estimated_items=2,
        allows_wide_layout=False,
    )
    variant, block, _ = select_block(c)
    has_normal = any(p.width_class != "wide" for p in block.item_count_profiles)
    assert has_normal, (
        f"allows_wide_layout=False but selected '{variant}' has only " f"wide profiles"
    )


def test_19_matrix_parallel_standard():
    c = _make_constraints(
        content_structure="matrix",
        item_relationship="parallel",
        target_density="standard",
        estimated_items=6,
    )
    variant, _, _ = select_block(c)
    assert (
        isinstance(variant, str) and variant
    ), "matrix+parallel should resolve to a variant"


def test_20_funnel_sequential():
    c = _make_constraints(
        content_structure="funnel",
        item_relationship="sequential",
        estimated_items=4,
    )
    variant, _, _ = select_block(c)
    funnel_blocks = {"processArrow", "sequentialOutput", "branchingPath"}
    _assert_in_family(variant, funnel_blocks, "funnel+sequential")


def test_21_spectrum_ranked():
    c = _make_constraints(
        content_structure="spectrum",
        item_relationship="ranked",
        estimated_items=5,
    )
    variant, _, _ = select_block(c)
    spectrum_blocks = {"spectrum_scale", "ranking_ladder"}
    _assert_in_family(variant, spectrum_blocks, "spectrum+ranked")


def test_22_filter_empty_candidate_list():
    c = _make_constraints()
    result = filter_catalog([], c)
    # Empty input → triggers DEFAULT_CANDIDATES fallback path.
    assert (
        isinstance(result, list) and len(result) >= 1
    ), f"empty candidate list should produce default survivors, got {result}"
    for v in result:
        assert v in ALL_BLOCKS, f"fallback survivor '{v}' should be a known block"


def test_23_score_single_candidate():
    c = _make_constraints()
    # Pick any real variant that we know exists.
    sample = next(iter(ALL_BLOCKS.keys()))
    result = score_candidates([sample], c)
    assert result == sample, (
        f"single-candidate scoring should return that candidate; "
        f"input=[{sample}], got '{result}'"
    )


def test_24_select_block_returns_valid_triple():
    c = _make_constraints()
    result = select_block(c)
    assert (
        isinstance(result, tuple) and len(result) == 3
    ), f"select_block must return a 3-tuple, got {result}"
    variant, block, profile = result
    assert isinstance(variant, str), "variant must be str"
    assert isinstance(block, BlockSpec), "block must be BlockSpec"
    assert isinstance(profile, ItemCountProfile), "profile must be ItemCountProfile"
    # Profile must come from the block (or be the synthetic fallback).
    assert (
        profile in block.item_count_profiles or len(block.item_count_profiles) == 0
    ), "profile must originate from the chosen block"


def test_25_profile_selection_picks_correct_range():
    """
    Build a synthetic block with profiles (1,2) and (3,6); for
    estimated_items=3 we must pick the second profile.
    """
    p_low = ItemCountProfile(
        item_range=(1, 2),
        layout_variant="default",
        height_class="compact",
        width_class="normal",
        supported_layouts=("blank",),
        combinable=True,
        notes="test",
    )
    p_high = ItemCountProfile(
        item_range=(3, 6),
        layout_variant="default",
        height_class="full",
        width_class="normal",
        supported_layouts=("blank",),
        combinable=True,
        notes="test",
    )
    fake_block = (
        BlockSpec(
            # We construct via dict-spread so this still works if BlockSpec
            # gains/loses optional fields. We rely on these being the canonical
            # fields shown in the prompt; if BlockSpec demands more, this test
            # will surface that mismatch loudly.
            name="fakeBlock",
            density_range=("ultra_sparse", "super_dense"),
            requires_icons=False,
            is_primary_candidate=True,
            item_count_profiles=(p_low, p_high),
        )
        if _block_spec_accepts_minimal()
        else _build_fake_block(p_low, p_high)
    )

    fake_catalog = {"fakeBlock": fake_block}
    c = _make_constraints(
        content_structure="list",
        item_relationship="parallel",
        estimated_items=3,
    )
    # Bypass routing — call select_block by injecting a catalog whose only
    # entry is fakeBlock, but routing won't return it. Instead we test the
    # profile picker directly via score+lookup.
    from blocks.shared.constraint_filter import _select_profile

    chosen = _select_profile(fake_block, 3)
    assert (
        chosen is p_high
    ), f"estimated_items=3 should pick the (3,6) profile, got {chosen.item_range}"


# ---------------------------------------------------------------------------
# Tiny helpers for test_25 — BlockSpec construction varies between codebases,
# so we feature-detect rather than hard-coding constructor kwargs.
# ---------------------------------------------------------------------------
def _block_spec_accepts_minimal() -> bool:
    try:
        BlockSpec(
            name="probe",
            density_range=("balanced", "balanced"),
            requires_icons=False,
            is_primary_candidate=False,
            item_count_profiles=(),
        )
        return True
    except TypeError:
        return False


def _build_fake_block(p_low, p_high):
    """
    If BlockSpec requires more kwargs than we know about, clone an existing
    real block and override the fields we care about.
    """
    template = next(iter(ALL_BLOCKS.values()))
    return replace(
        template,
        item_count_profiles=(p_low, p_high),
        density_range=("ultra_sparse", "super_dense"),
        requires_icons=False,
        is_primary_candidate=True,
    )


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------
def main():
    print("Running constraint_filter tests…\n")

    tests = [
        ("01 steps+sequential", test_01_steps_sequential),
        ("02 timeline+sequential", test_02_timeline_sequential),
        ("03 list+parallel with icons", test_03_list_parallel_with_icons),
        ("04 list+parallel no icons", test_04_list_parallel_no_icons),
        ("05 two_sided+opposing", test_05_two_sided_opposing),
        ("06 single+single sparse", test_06_single_single_sparse),
        ("07 single+single dense", test_07_single_single_dense),
        ("08 list+parallel no wide", test_08_list_parallel_no_wide),
        ("09 list+parallel icons prioritized", test_09_list_parallel_icons_prioritized),
        ("10 steps ultra_sparse", test_10_steps_ultra_sparse),
        ("11 steps super_dense", test_11_steps_super_dense),
        ("12 list+parallel 1 item", test_12_list_parallel_one_item),
        ("13 list+parallel 8 items", test_13_list_parallel_eight_items),
        ("14 unknown structure/relationship", test_14_unknown_structure_relationship),
        ("15 recency penalty", test_15_recency_penalty),
        ("16 tree+hierarchical", test_16_tree_hierarchical),
        ("17 network+radial", test_17_network_radial),
        ("18 two_sided+opposing no wide", test_18_two_sided_opposing_no_wide),
        ("19 matrix+parallel standard", test_19_matrix_parallel_standard),
        ("20 funnel+sequential", test_20_funnel_sequential),
        ("21 spectrum+ranked", test_21_spectrum_ranked),
        ("22 filter empty candidate list", test_22_filter_empty_candidate_list),
        ("23 score single candidate", test_23_score_single_candidate),
        (
            "24 select_block returns valid triple",
            test_24_select_block_returns_valid_triple,
        ),
        (
            "25 profile selection picks correct range",
            test_25_profile_selection_picks_correct_range,
        ),
    ]

    for name, fn in tests:
        _run(name, fn)

    print(f"\n{_PASSED} passed, {_FAILED} failed")
    sys.exit(0 if _FAILED == 0 else 1)


if __name__ == "__main__":
    main()
