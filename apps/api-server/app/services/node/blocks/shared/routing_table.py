"""
blocks/shared/routing_table.py

Routing table for the designer node — phase 1 of block selection.

Pipeline:
    Teacher → (content_structure, item_relationship) → routing_table
           → candidate list → constraint filter → selected block

This module maps a (content_structure, item_relationship) pair produced by
the teacher node into a ranked list of candidate block variant names. The
designer then applies constraint filtering (data shape, item count, media
availability, etc.) on top of this list to pick the final block.

Ordering convention:
    Variants earlier in a list have higher priority. The most semantically
    accurate block for the (structure, relationship) pair comes first.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Master set of all valid block variant names (used for typo validation).
# Keep this in sync with the block registry. Any variant referenced in
# STRUCTURE_TO_BLOCKS or DEFAULT_CANDIDATES must appear here.
# ---------------------------------------------------------------------------
ALL_VARIANT_NAMES: frozenset[str] = frozenset(
    {
        # timeline family
        "timeline",
        "timelineHorizontal",
        "timelineIcon",
        "timelineMilestone",
        # sequential_process family
        "processAccordion",
        "processArrow",
        "processSteps",
        "sequentialOutput",
        "sequentialSteps",
        "branching_path",
        "image_process",
        "input_process_output",
        # comparison_analytical family
        "comparison_table",
        "split_panel",
        "comparisonBeforeAfter",
        "comparisonProsCons",
        "ranking_ladder",
        "spectrum_scale",
        "venn_overlap",
        # stats_quantitative family
        "formula_block",
        "interlockingArrows",
        "stats",
        "statsComparison",
        "statsPercentage",
        # conceptual_relational family
        "feature_showcase",
        "diamondHub",
        "hubAndSpoke",
        "relationshipMap",
        "cause_effect_web",
        "dependency_chain",
        "ecosystem_map",
        # hierarchical_structural family
        "hierarchy_tree",
        "layer_stack",
        # grid_container family
        "bigBullets",
        "bulletIcon",
        "cardGridDiamond",
        "cardGridImage",
        "cardGridSimple",
        "diamondGrid",
        "diamondRibbon",
        "ribbonFold",
        "bento_grid",
        "pillar_cards",
        # supporting_contextual family
        "intro_paragraph",
        "quote",
        "annotation_paragraph",
        "callout",
        "caption",
        "divider",
        "image",
        "outro_paragraph",
        "rich_text",
        "definition",
        "myth_vs_fact",
        "summary_strip",
        # cyclic_feedback family
        "cyclic_process_block",
    }
)


# ---------------------------------------------------------------------------
# Routing table.
#
# Key:   (content_structure, item_relationship)
# Value: ranked list of candidate block variant names
#
# Coverage: Every (structure, relationship) combination the teacher might
# realistically produce should have an entry. Combinations explicitly listed
# in the spec are encoded verbatim; remaining plausible combinations are
# filled in by semantic inference. If something genuinely doesn't match,
# get_candidates() falls back to DEFAULT_CANDIDATES.
# ---------------------------------------------------------------------------
STRUCTURE_TO_BLOCKS: dict[tuple[str, str], list[str]] = {

    # ---- steps -----------------------------------------------------------
    # processArrow: wide, balanced–super_dense, 2–5 items, steps/funnel
    # processSteps: normal, sparse–dense, 3–5 items, steps
    # sequentialOutput: wide, balanced–dense, 2–6 items, steps
    # processAccordion: normal, standard–super_dense, 3–5 items, steps
    # input_process_output: normal, balanced–dense, 3 items, steps
    # sequentialSteps: wide, balanced–dense, 2–6 items, steps
    # branching_path: wide, balanced–standard, 2–4 items, steps
    # image_process: wide, dense–super_dense, 3–5 items, steps
    ("steps", "sequential"): ["processSteps", "processArrow", "sequentialOutput", "processAccordion", "input_process_output"],
    ("steps", "causal"): ["processArrow", "branching_path", "sequentialOutput"],
    ("steps", "cyclical"): ["cyclic_process_block", "processArrow"],
    ("steps", "parallel"): ["processSteps", "bigBullets", "cardGridSimple"],
    ("steps", "hierarchical"): ["hierarchy_tree", "processAccordion", "branching_path"],
    ("steps", "ranked"): ["ranking_ladder", "processSteps", "processArrow"],
    ("steps", "single"): ["processSteps", "callout"],

    # ---- timeline --------------------------------------------------------
    # timeline: normal, sparse–dense, 4–6 items
    # timelineMilestone: normal, sparse–standard, 2–6 items
    # timelineHorizontal: wide, sparse–standard, 3–5 items
    # timelineIcon: normal, sparse–dense, 4–6 items (icons)
    ("timeline", "sequential"): ["timelineMilestone", "timeline", "timelineHorizontal", "timelineIcon"],
    ("timeline", "causal"): ["timeline", "timelineMilestone", "processArrow"],
    ("timeline", "cyclical"): ["cyclic_process_block", "timeline"],
    ("timeline", "ranked"): ["timelineMilestone", "timeline", "ranking_ladder"],
    ("timeline", "parallel"): ["timelineHorizontal", "timeline", "timelineIcon"],

    # ---- list ------------------------------------------------------------
    # Grid/container blocks (parallel, list structure) are the natural fit.
    # bigBullets: no icons, ultra_sparse–standard, 2–6 items
    # bulletIcon: icons, sparse–standard, 2–6 items
    # cardGridSimple: no icons, ultra_sparse–balanced, 2–6 items
    # cardGridDiamond: icons, sparse–standard, 3–6 items
    # cardGridImage: no icons, ultra_sparse–balanced, 2–4 items (wide)
    # diamondGrid: icons, ultra_sparse–standard, 1–6 items
    # diamondRibbon: icons, balanced–super_dense, 1–6 items
    # ribbonFold: icons, balanced–dense, 3–5 items
    # bento_grid: icons, balanced–standard, 3–5 items
    # pillar_cards: icons, sparse–standard, 3–5 items
    ("list", "parallel"): ["bigBullets", "cardGridSimple", "bulletIcon", "cardGridDiamond", "diamondGrid"],
    ("list", "ranked"): ["ranking_ladder", "bigBullets", "processSteps"],
    ("list", "hierarchical"): ["hierarchy_tree", "definition"],
    ("list", "cyclical"): ["cyclic_process_block", "processAccordion"],
    ("list", "causal"): ["processArrow", "hubAndSpoke", "cause_effect_web"],
    ("list", "overlapping"): ["venn_overlap", "ecosystem_map"],
    ("list", "sequential"): ["bigBullets", "processSteps", "processAccordion"],
    ("list", "opposing"): ["comparisonProsCons", "split_panel", "comparisonBeforeAfter"],
    ("list", "radial"): ["hubAndSpoke", "diamondGrid", "diamondHub"],
    ("list", "layered"): ["layer_stack", "definition"],
    ("list", "single"): ["bigBullets", "cardGridSimple", "callout"],

    # ---- two_sided -------------------------------------------------------
    # split_panel: wide, balanced–standard, 2 items, opposing
    # comparisonBeforeAfter: normal, balanced–standard, 1–6 items, opposing
    # comparisonProsCons: normal, balanced–dense, 2 items, opposing (icons)
    # myth_vs_fact: normal, ultra_sparse–standard, 1 item, opposing
    ("two_sided", "opposing"): ["split_panel", "comparisonBeforeAfter", "comparisonProsCons", "myth_vs_fact"],
    ("two_sided", "overlapping"): ["venn_overlap", "split_panel"],
    ("two_sided", "parallel"): ["split_panel", "comparisonProsCons", "statsComparison"],
    ("two_sided", "causal"): ["comparisonBeforeAfter", "split_panel"],
    ("two_sided", "sequential"): ["comparisonBeforeAfter", "split_panel"],
    ("two_sided", "ranked"): ["split_panel", "ranking_ladder"],
    ("two_sided", "single"): ["split_panel", "comparisonBeforeAfter"],

    # ---- single ----------------------------------------------------------
    # stats: sparse–standard, 2–4 items, single struct
    # statsPercentage: sparse–standard, 2–4 items, single struct (wide)
    # quote: ultra_sparse–sparse, 1 item, single struct
    # definition: sparse–balanced, 1–3 items, single struct
    # callout: ultra_sparse–standard, 1 item, single struct
    ("single", "single"): ["stats", "statsPercentage", "definition", "quote"],
    ("single", "causal"): ["stats", "callout"],
    ("single", "sequential"): ["stats", "callout"],
    ("single", "parallel"): ["stats", "statsPercentage"],
    ("single", "ranked"): ["stats", "statsPercentage"],

    # ---- matrix ----------------------------------------------------------
    # comparison_table: wide, balanced–super_dense, 2–4 items, matrix struct
    # statsComparison: normal, sparse–standard, 3–6 items, matrix struct
    ("matrix", "parallel"): ["statsComparison", "comparison_table", "cardGridSimple"],
    ("matrix", "opposing"): ["comparison_table", "statsComparison"],
    ("matrix", "hierarchical"): ["hierarchy_tree", "statsComparison"],
    ("matrix", "ranked"): ["statsComparison", "ranking_ladder"],
    ("matrix", "overlapping"): ["venn_overlap", "statsComparison"],
    ("matrix", "sequential"): ["statsComparison", "processArrow"],
    ("matrix", "causal"): ["statsComparison", "cause_effect_web"],

    # ---- spectrum --------------------------------------------------------
    # spectrum_scale: wide, balanced–standard, 3–6 items, spectrum struct
    ("spectrum", "ranked"): ["spectrum_scale", "ranking_ladder"],
    ("spectrum", "opposing"): ["spectrum_scale", "split_panel"],
    ("spectrum", "sequential"): ["spectrum_scale", "timelineHorizontal"],
    ("spectrum", "parallel"): ["spectrum_scale", "statsComparison"],
    ("spectrum", "overlapping"): ["spectrum_scale", "venn_overlap"],

    # ---- tree ------------------------------------------------------------
    # hierarchy_tree: wide, balanced–super_dense, 2–4 items, tree struct
    ("tree", "hierarchical"): ["hierarchy_tree", "layer_stack"],
    ("tree", "radial"): ["hubAndSpoke", "hierarchy_tree"],
    ("tree", "parallel"): ["hierarchy_tree", "bigBullets"],
    ("tree", "layered"): ["layer_stack", "hierarchy_tree"],

    # ---- layers ----------------------------------------------------------
    # layer_stack: normal, balanced–dense, 3–6 items, layers struct
    ("layers", "layered"): ["layer_stack", "hierarchy_tree"],
    ("layers", "hierarchical"): ["layer_stack", "hierarchy_tree"],
    ("layers", "sequential"): ["layer_stack", "processArrow"],
    ("layers", "parallel"): ["layer_stack", "bigBullets"],

    # ---- network ---------------------------------------------------------
    # hubAndSpoke: wide, dense–super_dense, 3–6 items, network struct (icons)
    # ecosystemMap: wide, standard–super_dense, 4–7 items, network struct (icons)
    # feature_showcase: wide, dense–super_dense, 4–6 items, network struct (icons)
    # diamondHub: wide, balanced–dense, 4 items, network struct (icons)
    # relationshipMap: wide, dense–super_dense, 3 items, network struct (icons)
    # cause_effect_web: wide, balanced–standard, 2–4 items, network struct (icons)
    # dependency_chain: wide, standard–super_dense, 4–7 items, network struct (icons)
    # cyclic_process_block: wide, balanced–dense, 3–4 items, network struct
    ("network", "radial"): ["hubAndSpoke", "ecosystem_map", "diamondHub", "feature_showcase"],
    ("network", "overlapping"): ["ecosystem_map", "venn_overlap"],
    ("network", "hierarchical"): ["dependency_chain", "hierarchy_tree", "hubAndSpoke"],
    ("network", "parallel"): ["ecosystem_map", "feature_showcase", "hubAndSpoke"],
    ("network", "cyclical"): ["cyclic_process_block", "ecosystem_map"],
    ("network", "causal"): ["cause_effect_web", "relationshipMap", "hubAndSpoke"],
    ("network", "layered"): ["dependency_chain", "layer_stack"],

    # ---- web -------------------------------------------------------------
    # venn_overlap: normal, balanced–standard, 3 items, web struct
    ("web", "radial"): ["ecosystem_map", "hubAndSpoke", "feature_showcase"],
    ("web", "overlapping"): ["venn_overlap", "ecosystem_map"],
    ("web", "hierarchical"): ["hierarchy_tree", "ecosystem_map"],
    ("web", "parallel"): ["ecosystem_map", "feature_showcase"],
    ("web", "causal"): ["cause_effect_web", "relationshipMap"],

    # ---- funnel ----------------------------------------------------------
    # processArrow has content_structure_fit=("steps", "funnel")
    ("funnel", "sequential"): ["processArrow", "sequentialOutput", "sequentialSteps"],
    ("funnel", "causal"): ["branching_path", "processArrow"],
    ("funnel", "ranked"): ["ranking_ladder", "processArrow"],
    ("funnel", "parallel"): ["processArrow", "sequentialOutput"],
}


# ---------------------------------------------------------------------------
# Fallback used when no entry matches the (structure, relationship) pair.
# These are safe, general-purpose blocks that work for most content:
#   bigBullets: normal width, ultra_sparse–standard, 2–6 items, no icons
#   cardGridSimple: normal width, ultra_sparse–balanced, 2–6 items, no icons
#   bulletIcon: normal width, sparse–standard, 2–6 items, with icons
#   stats: normal width, sparse–standard, 2–4 items, primary candidate
# ---------------------------------------------------------------------------
DEFAULT_CANDIDATES: list[str] = ["bigBullets", "cardGridSimple", "bulletIcon", "stats"]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def get_candidates(content_structure: str, item_relationship: str) -> list[str]:
    """
    Look up the ranked candidate list for a (content_structure, item_relationship)
    pair produced by the teacher node.

    Returns a *copy* of the list so callers can mutate it freely (e.g. during
    constraint filtering) without corrupting the routing table.

    If no entry matches, returns a copy of DEFAULT_CANDIDATES.
    """
    candidates = STRUCTURE_TO_BLOCKS.get((content_structure, item_relationship))
    if candidates is None:
        return list(DEFAULT_CANDIDATES)
    return list(candidates)


def validate_routing_table() -> None:
    """
    Sanity-check the routing table at import time.

    Raises RuntimeError if any variant name referenced in STRUCTURE_TO_BLOCKS
    or DEFAULT_CANDIDATES is not present in ALL_VARIANT_NAMES. This catches
    typos like "processArow" or stale variant names that have been removed
    from the block registry.
    """
    unknown: set[str] = set()

    for key, variants in STRUCTURE_TO_BLOCKS.items():
        if not isinstance(variants, list) or not variants:
            raise RuntimeError(
                f"Routing entry {key!r} must map to a non-empty list of variants."
            )
        for v in variants:
            if v not in ALL_VARIANT_NAMES:
                unknown.add(f"{v!r} (in entry {key!r})")

    for v in DEFAULT_CANDIDATES:
        if v not in ALL_VARIANT_NAMES:
            unknown.add(f"{v!r} (in DEFAULT_CANDIDATES)")

    if unknown:
        raise RuntimeError(
            "routing_table.py references unknown block variant(s): "
            + ", ".join(sorted(unknown))
        )


# Run validation at import time so typos surface immediately rather than
# waiting until a particular (structure, relationship) pair is hit at runtime.
validate_routing_table()


__all__ = [
    "ALL_VARIANT_NAMES",
    "STRUCTURE_TO_BLOCKS",
    "DEFAULT_CANDIDATES",
    "get_candidates",
    "validate_routing_table",
]