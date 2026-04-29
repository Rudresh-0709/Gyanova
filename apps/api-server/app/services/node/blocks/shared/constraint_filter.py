"""
blocks/shared/constraint_filter.py

Phases 2 and 3 of the designer node's block selection pipeline.

Pipeline:
    Teacher output
        → routing_table.get_candidates(structure, relationship)   ← phase 1
        → constraint_filter.filter_catalog(candidates, ...)        ← phase 2
        → constraint_filter.score_candidates(filtered, ...)        ← phase 3
        → selected block variant (string)

Design philosophy:
    - Fail LOUDLY. Never silently return a wrong block.
    - Every elimination, fallback, and tiebreak prints a [filter]-prefixed
      message so misconfigurations are visible during slide generation.
    - Never raise in production — every error path returns a sensible
      fallback (ultimately "bigBullets") accompanied by a CRITICAL log.
    - `all_blocks` is resolved lazily so test code can monkeypatch the
      registry without import-order headaches.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from blocks.shared.base_spec import (
    BlockSpec,
    ItemCountProfile,
    DENSITY_ORDER,
    satisfies_density,
)


# ---------------------------------------------------------------------------
# Public data structure
# ---------------------------------------------------------------------------
@dataclass
class SlideConstraints:
    """
    The full set of constraints the designer needs to pick a block.

    Most fields come straight from the teacher's structured output; only
    `variant_history` is sourced from pipeline state (so the designer can
    avoid repeating the same block on consecutive slides).
    """

    content_structure: str  # list / steps / timeline / two_sided / ...
    item_relationship: str  # parallel / sequential / opposing / ...
    target_density: (
        str  # ultra_sparse / sparse / balanced / standard / dense / super_dense
    )
    estimated_items: int  # 1..8
    allows_wide_layout: bool  # False when a side image is expected
    requires_icons: bool  # True when icons aid comprehension
    image_role: str  # content / accent / none
    variant_history: list[str] = field(default_factory=list)  # most recent LAST


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------
def _resolve_blocks(all_blocks: Optional[dict[str, BlockSpec]]) -> dict[str, BlockSpec]:
    """
    Lazily resolve the block registry. We import inside the function body so
    that `ALL_BLOCKS` is read at call time, not at module import time. This
    matters for tests that monkeypatch the registry, and for avoiding
    circular imports during package initialisation.
    """
    if all_blocks is None:
        from blocks.registry import ALL_BLOCKS as _ALL_BLOCKS

        return _ALL_BLOCKS
    return all_blocks


def _block_supports_item_count(block: BlockSpec, n: int) -> bool:
    """True if any profile's item_range contains n."""
    for profile in block.item_count_profiles:
        lo, hi = profile.item_range
        if lo <= n <= hi:
            return True
    return False


def _block_only_wide(block: BlockSpec) -> bool:
    """True if EVERY profile of the block is wide-only."""
    profiles = block.item_count_profiles
    if not profiles:
        return False
    return all(p.width_class == "wide" for p in profiles)


def _block_has_wide_profile(block: BlockSpec) -> bool:
    """True if at least one profile is wide."""
    return any(p.width_class == "wide" for p in block.item_count_profiles)


# ---------------------------------------------------------------------------
# Phase 2 — hard constraint filter
# ---------------------------------------------------------------------------
def filter_catalog(
    candidates: list[str],
    constraints: SlideConstraints,
    all_blocks: Optional[dict[str, BlockSpec]] = None,
) -> list[str]:
    """
    Eliminate candidates that fail any hard constraint. Order is preserved.

    If every candidate is eliminated, fall back to DEFAULT_CANDIDATES (run
    through the same filter). If THAT also empties out, last resort is
    ["bigBullets"]. Both fallback paths log loudly.
    """
    all_blocks = _resolve_blocks(all_blocks)
    survivors: list[str] = []

    for variant in candidates:
        # 1. Variant unknown
        if variant not in all_blocks:
            print(f"[filter] '{variant}' not in catalog — skipping")
            continue

        block = all_blocks[variant]

        # 2. Density mismatch
        if not satisfies_density(block, constraints.target_density):
            print(
                f"[filter] '{variant}' eliminated: density "
                f"'{constraints.target_density}' outside block range "
                f"{block.density_range}"
            )
            continue

        # 3. Item count mismatch
        if not _block_supports_item_count(block, constraints.estimated_items):
            print(
                f"[filter] '{variant}' eliminated: no profile supports "
                f"{constraints.estimated_items} items"
            )
            continue

        # 4. Width mismatch — only eliminate if ALL profiles are wide-only
        if not constraints.allows_wide_layout and _block_only_wide(block):
            print(
                f"[filter] '{variant}' eliminated: requires wide layout but "
                f"allows_wide_layout=False"
            )
            continue

        # 5. Icon mismatch
        if constraints.requires_icons and not block.requires_icons:
            print(
                f"[filter] '{variant}' eliminated: requires_icons=True but "
                f"block does not support icons"
            )
            continue

        survivors.append(variant)

    if survivors:
        return survivors

    # ----- fallback path: try DEFAULT_CANDIDATES -----
    print(
        f"[filter] WARNING: all candidates eliminated for constraints "
        f"{constraints}. Falling back to DEFAULT_CANDIDATES."
    )

    # Lazy import to avoid any circularity with routing_table.
    from blocks.shared.routing_table import DEFAULT_CANDIDATES

    # IMPORTANT: re-run through filter logic, but guard against infinite
    # recursion by inlining rather than calling filter_catalog again.
    default_survivors: list[str] = []
    for variant in DEFAULT_CANDIDATES:
        if variant not in all_blocks:
            print(f"[filter] '{variant}' not in catalog — skipping")
            continue
        block = all_blocks[variant]
        if not satisfies_density(block, constraints.target_density):
            print(
                f"[filter] '{variant}' eliminated: density "
                f"'{constraints.target_density}' outside block range "
                f"{block.density_range}"
            )
            continue
        if not _block_supports_item_count(block, constraints.estimated_items):
            print(
                f"[filter] '{variant}' eliminated: no profile supports "
                f"{constraints.estimated_items} items"
            )
            continue
        if not constraints.allows_wide_layout and _block_only_wide(block):
            print(
                f"[filter] '{variant}' eliminated: requires wide layout but "
                f"allows_wide_layout=False"
            )
            continue
        if constraints.requires_icons and not block.requires_icons:
            print(
                f"[filter] '{variant}' eliminated: requires_icons=True but "
                f"block does not support icons"
            )
            continue
        default_survivors.append(variant)

    if default_survivors:
        return default_survivors

    print(
        "[filter] CRITICAL: even DEFAULT_CANDIDATES failed. "
        "Using bigBullets as last resort."
    )
    return ["bigBullets"]


# ---------------------------------------------------------------------------
# Phase 3 — scoring
# ---------------------------------------------------------------------------
def _recency_penalty(variant: str, history: list[str]) -> int:
    """
    Penalty based on how recently `variant` appears in history (most recent
    last). Only the last 3 history entries count.

      last 1 slide  → -3
      last 2 slides → -2
      last 3 slides → -1
      otherwise     →  0

    If the variant appears in multiple recent slots, the strongest (most
    recent) penalty wins.
    """
    if not history:
        return 0
    last3 = history[-3:]  # up to 3 most-recent entries
    # Walk from most-recent backwards.
    # last3[-1] is the most recent slide, last3[-2] one before, etc.
    if len(last3) >= 1 and last3[-1] == variant:
        return -3
    if len(last3) >= 2 and last3[-2] == variant:
        return -2
    if len(last3) >= 3 and last3[-3] == variant:
        return -1
    return 0


def score_candidates(
    candidates: list[str],
    constraints: SlideConstraints,
    all_blocks: Optional[dict[str, BlockSpec]] = None,
) -> str:
    """
    Score every candidate and return the winner. Ties broken by earlier
    position in the candidates list.
    """
    all_blocks = _resolve_blocks(all_blocks)

    if not candidates:
        print(
            "[filter] CRITICAL: score_candidates received empty list. "
            "Returning 'bigBullets' as last resort."
        )
        return "bigBullets"

    best_variant: Optional[str] = None
    best_score: Optional[int] = None

    for idx, variant in enumerate(candidates):
        if variant not in all_blocks:
            # Shouldn't happen post-filter, but be defensive.
            print(
                f"[filter] '{variant}' missing from catalog during scoring — "
                f"skipping"
            )
            continue

        block = all_blocks[variant]
        score = 0

        # 1. Recency penalty
        score += _recency_penalty(variant, constraints.variant_history)

        # 2. Primary candidate bonus
        if block.is_primary_candidate:
            score += 2

        # 3. Icon match bonus
        if constraints.requires_icons and block.requires_icons:
            score += 1

        # 4. Position bonus (only the first candidate gets it)
        if idx == 0:
            score += 1

        # 5. Wide-layout fit bonus
        if constraints.allows_wide_layout and _block_has_wide_profile(block):
            score += 1

        # Strict ">" so earlier-list ties keep the earlier candidate.
        if best_score is None or score > best_score:
            best_score = score
            best_variant = variant

    if best_variant is None:
        # Every candidate was missing from the catalog — extreme edge case.
        print(
            "[filter] CRITICAL: no scorable candidates. "
            "Returning 'bigBullets' as last resort."
        )
        return "bigBullets"

    return best_variant


# ---------------------------------------------------------------------------
# Profile selection helper
# ---------------------------------------------------------------------------
def _select_profile(block: BlockSpec, estimated_items: int) -> ItemCountProfile:
    """
    Pick the best ItemCountProfile for `estimated_items`.

    Strategy:
      1. First profile whose [min, max] contains the count → use it.
      2. Otherwise the profile whose midpoint is closest to the count.
    """
    # Exact-fit pass.
    for profile in block.item_count_profiles:
        lo, hi = profile.item_range
        if lo <= estimated_items <= hi:
            return profile

    # Midpoint-distance pass.
    best_profile: Optional[ItemCountProfile] = None
    best_dist: Optional[float] = None
    for profile in block.item_count_profiles:
        lo, hi = profile.item_range
        midpoint = (lo + hi) / 2.0
        dist = abs(midpoint - estimated_items)
        if best_dist is None or dist < best_dist:
            best_dist = dist
            best_profile = profile

    if best_profile is None:
        # Block has zero profiles — should never happen, but don't crash.
        print(
            f"[filter] CRITICAL: block has no ItemCountProfiles; "
            f"synthesising a degenerate one."
        )
        return ItemCountProfile(
            item_range=(estimated_items, estimated_items),
            width_class="normal",
            combinable=False,
        )
    return best_profile


# ---------------------------------------------------------------------------
# Main entry point — orchestrates phases 1, 2, 3
# ---------------------------------------------------------------------------
def select_block(
    constraints: SlideConstraints,
    all_blocks: Optional[dict[str, BlockSpec]] = None,
) -> tuple[str, BlockSpec, ItemCountProfile]:
    """
    The designer node's main hook. Runs the full three-phase pipeline and
    returns (variant_name, block_spec, item_count_profile).

    Never raises in production — fallback paths always yield a usable
    triple, accompanied by loud logs.
    """
    all_blocks = _resolve_blocks(all_blocks)

    # Phase 1 — routing
    from blocks.shared.routing_table import get_candidates

    candidates = get_candidates(
        constraints.content_structure, constraints.item_relationship
    )

    # Phase 2 — hard constraints
    filtered = filter_catalog(candidates, constraints, all_blocks)

    # Phase 3 — scoring
    winner = score_candidates(filtered, constraints, all_blocks)

    # Resolve block + profile.
    if winner not in all_blocks:
        # Last-resort safety net: bigBullets might be missing in a malformed
        # registry. Synthesise a degenerate triple rather than raising.
        print(
            f"[filter] CRITICAL: winning variant '{winner}' is not in "
            f"catalog. Returning a degenerate triple."
        )
        # Try ANY block in the catalog as ultimate fallback.
        if all_blocks:
            fallback_name, fallback_block = next(iter(all_blocks.items()))
            print(f"[filter] Using '{fallback_name}' as emergency fallback.")
            profile = _select_profile(fallback_block, constraints.estimated_items)
            return fallback_name, fallback_block, profile
        # If even the catalog is empty there's nothing we can do.
        raise RuntimeError("constraint_filter.select_block: block catalog is empty")

    block = all_blocks[winner]
    profile = _select_profile(block, constraints.estimated_items)
    return winner, block, profile


__all__ = [
    "SlideConstraints",
    "filter_catalog",
    "score_candidates",
    "select_block",
]
