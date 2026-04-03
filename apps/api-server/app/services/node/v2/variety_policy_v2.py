"""
Variety Policy for v2 slide generation.

Provides scoring/penalty helpers that inspect TutorState history fields
(layout_history, variant_history, composition_history) to discourage
repeating the same template, smart_layout variant, or image layout on
consecutive slides.

All functions are pure/stateless – they receive history lists and return
penalty/bonus scores or filtered candidate lists.  No state is mutated here.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# How many recent entries to inspect when computing variety penalties.
RECENT_WINDOW = 4

# Penalty applied when the candidate was used in the most-recent slide.
PENALTY_IMMEDIATE_REPEAT = 30

# Penalty when candidate appeared within the last RECENT_WINDOW slides.
PENALTY_RECENT_REPEAT = 15

# Bonus for candidates that have not appeared in recent history at all.
BONUS_FRESH = 10


# ---------------------------------------------------------------------------
# Core helpers
# ---------------------------------------------------------------------------


def score_against_history(candidate: str, history: List[str]) -> int:
    """
    Return a *penalty* score (positive = worse) for using ``candidate``
    given the recent ``history``.

    Callers should *subtract* this value from a candidate's total score.
    """
    if not candidate or not history:
        return 0
    recent = history[-RECENT_WINDOW:]
    if not recent:
        return 0
    if recent[-1] == candidate:
        return PENALTY_IMMEDIATE_REPEAT
    if candidate in recent:
        return PENALTY_RECENT_REPEAT
    return 0


def fresh_bonus(candidate: str, history: List[str]) -> int:
    """
    Return a *bonus* score for using ``candidate`` if it has not appeared
    in the recent history at all.
    """
    recent = history[-RECENT_WINDOW:]
    if not recent:
        return BONUS_FRESH
    return BONUS_FRESH if candidate not in recent else 0


def score_template(template_name: str, variant_history: List[str]) -> int:
    """
    Net score adjustment for a template given composition/variant history.
    Positive = prefer this template.  Negative = avoid.
    """
    return fresh_bonus(template_name, variant_history) - score_against_history(template_name, variant_history)


def score_smart_layout_variant(slv: str, variant_history: List[str]) -> int:
    """
    Net score adjustment for a smart_layout variant given history.
    Positive = prefer.  Negative = avoid.
    """
    return fresh_bonus(slv, variant_history) - score_against_history(slv, variant_history)


def score_layout(layout: str, layout_history: List[str]) -> int:
    """
    Net score adjustment for an image layout (right/left/top/bottom/blank).
    Positive = prefer.  Negative = avoid.
    """
    return fresh_bonus(layout, layout_history) - score_against_history(layout, layout_history)


# ---------------------------------------------------------------------------
# Template selection helper
# ---------------------------------------------------------------------------


def rank_templates(
    candidates: List[Any],  # List[TemplateSpec]
    *,
    variant_history: List[str],
) -> List[Any]:
    """
    Re-rank a list of TemplateSpec candidates by applying variety penalties.

    Returns the same candidates sorted best-first, with recently-used
    templates penalised.  The caller's original score ordering is used as
    a tiebreaker via stable sort.
    """
    if not candidates:
        return candidates

    def _variety_score(template: Any) -> int:
        return score_template(template.name, variant_history)

    # Sort descending by variety adjustment (higher = better)
    return sorted(candidates, key=lambda t: _variety_score(t), reverse=True)


# ---------------------------------------------------------------------------
# Smart-layout variant selection helper
# ---------------------------------------------------------------------------


def pick_smart_layout_variant(
    preferred_variant: str,
    allowed_variants: List[str],
    variant_history: List[str],
) -> str:
    """
    Choose the best smart_layout variant from ``allowed_variants``, applying
    variety scoring.

    ``preferred_variant`` is the planner's first-choice (from intent/scope
    mapping).  If it has been used recently, a fresh alternative is returned.
    Returns ``preferred_variant`` as a last resort if no alternatives exist.
    """
    if not allowed_variants:
        return preferred_variant or "bigBullets"

    scored: List[Tuple[int, str]] = []
    for variant in allowed_variants:
        base = 10 if variant == preferred_variant else 0
        adjustment = score_smart_layout_variant(variant, variant_history)
        scored.append((base + adjustment, variant))

    scored.sort(key=lambda x: -x[0])
    return scored[0][1] if scored else (preferred_variant or "bigBullets")


# ---------------------------------------------------------------------------
# Layout selection helper
# ---------------------------------------------------------------------------


def pick_layout(
    allowed_layouts: List[str],
    *,
    layout_history: List[str],
    image_need: str = "optional",
    density: str = "balanced",
) -> str:
    """
    Choose the best image layout from ``allowed_layouts``, preferring variety
    and respecting image_need / density constraints.
    """
    if not allowed_layouts:
        return "blank"

    # Hard filter: if no image, prefer blank
    if image_need == "forbidden":
        return "blank" if "blank" in allowed_layouts else allowed_layouts[0]

    # Soft filter: dense slides prefer blank / top / bottom
    dense_preferred = {"blank", "top", "bottom"}

    scored: List[Tuple[int, str]] = []
    for layout in allowed_layouts:
        base = 0
        if density in {"dense", "super_dense"} and layout in dense_preferred:
            base += 5
        adjustment = score_layout(layout, layout_history)
        scored.append((base + adjustment, layout))

    scored.sort(key=lambda x: -x[0])
    return scored[0][1] if scored else allowed_layouts[0]
