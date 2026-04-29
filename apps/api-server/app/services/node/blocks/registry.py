"""
blocks/registry.py

Single source of truth for the GyML block catalog.

This module imports every family-level BLOCKS dictionary, merges them into
a single ALL_BLOCKS mapping keyed by variant name, and validates the
combined catalog at import time. Any structural violation raises a
RuntimeError immediately so problems surface on startup rather than
deep inside the rendering pipeline.
"""

from __future__ import annotations

from .shared.base_spec import BlockSpec, DENSITY_ORDER

from .families.timeline.spec import TIMELINE_BLOCKS
from .families.sequential_process.spec import SEQUENTIAL_PROCESS_BLOCKS
from .families.comparison.spec import COMPARISON_ANALYTICAL_BLOCKS
from .families.stats_quantitative.spec import STATS_QUANTITATIVE_BLOCKS
from .families.conceptual_relational.spec import CONCEPTUAL_RELATIONAL_BLOCKS
from .families.hierarchical_structural.spec import HIERARCHICAL_STRUCTURAL_BLOCKS
from .families.grid_container.spec import GRID_CONTAINER_BLOCKS
from .families.supporting_contextual.spec import SUPPORTING_CONTEXTUAL_BLOCKS
from .families.cyclic_feedback.spec import CYCLIC_FEEDBACK_BLOCKS


# ---------------------------------------------------------------------------
# Family registry
# ---------------------------------------------------------------------------
# Ordered list so duplicate detection can name the family that introduced
# the conflict. The order itself has no semantic meaning.
_FAMILY_DICTS: tuple[tuple[str, dict[str, BlockSpec]], ...] = (
    ("timeline", TIMELINE_BLOCKS),
    ("sequential_process", SEQUENTIAL_PROCESS_BLOCKS),
    ("comparison", COMPARISON_ANALYTICAL_BLOCKS),
    ("stats_quantitative", STATS_QUANTITATIVE_BLOCKS),
    ("conceptual_relational", CONCEPTUAL_RELATIONAL_BLOCKS),
    ("hierarchical_structural", HIERARCHICAL_STRUCTURAL_BLOCKS),
    ("grid_container", GRID_CONTAINER_BLOCKS),
    ("supporting_contextual", SUPPORTING_CONTEXTUAL_BLOCKS),
    ("cyclic_feedback", CYCLIC_FEEDBACK_BLOCKS),
)


def _merge_families() -> dict[str, BlockSpec]:
    """Merge all per-family dicts, raising on duplicate variant names."""
    merged: dict[str, BlockSpec] = {}
    origin: dict[str, str] = {}  # variant -> family that contributed it

    for family_name, family_dict in _FAMILY_DICTS:
        for variant, spec in family_dict.items():
            if variant in merged:
                raise RuntimeError(
                    f"[registry] Duplicate variant name '{variant}': "
                    f"already registered by family '{origin[variant]}', "
                    f"redefined by family '{family_name}'."
                )
            merged[variant] = spec
            origin[variant] = family_name

    return merged


ALL_BLOCKS: dict[str, BlockSpec] = _merge_families()


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
def validate_catalog() -> None:
    """
    Validate the merged ALL_BLOCKS catalog. Raises RuntimeError on the
    first violation encountered, with a message that identifies the
    offending variant and the failed constraint.

    Constraints enforced:
      1. No duplicate variant names across families
         (already enforced during merge; re-checked defensively here).
      2. Every block has at least one ItemCountProfile.
      3. density_range values must be members of DENSITY_ORDER.
      4. density_range[0] index must be <= density_range[1] index.
      5. Every profile's item_range must satisfy min <= max.
      6. A wide block (width_class == "wide") must not declare
         "left" or "right" in supported_layouts.
    """
    # Defensive duplicate re-check (in case ALL_BLOCKS was mutated post-merge).
    seen: set[str] = set()
    for variant in ALL_BLOCKS:
        if variant in seen:
            raise RuntimeError(
                f"[registry] Duplicate variant name '{variant}' detected "
                f"in ALL_BLOCKS."
            )
        seen.add(variant)

    density_index = {name: i for i, name in enumerate(DENSITY_ORDER)}

    for variant, spec in ALL_BLOCKS.items():
        # 2. At least one profile.
        if len(spec.item_count_profiles) == 0:
            raise RuntimeError(
                f"[registry] Block '{variant}' (family '{spec.family}') "
                f"has zero item_count_profiles; every block must define "
                f"at least one ItemCountProfile."
            )

        # 3 & 4. density_range validity.
        d_min, d_max = spec.density_range
        if d_min not in density_index:
            raise RuntimeError(
                f"[registry] Block '{variant}' has invalid density_range "
                f"lower bound '{d_min}'; must be one of {DENSITY_ORDER}."
            )
        if d_max not in density_index:
            raise RuntimeError(
                f"[registry] Block '{variant}' has invalid density_range "
                f"upper bound '{d_max}'; must be one of {DENSITY_ORDER}."
            )
        if density_index[d_min] > density_index[d_max]:
            raise RuntimeError(
                f"[registry] Block '{variant}' has inverted density_range: "
                f"min '{d_min}' is ranked higher than max '{d_max}' "
                f"in DENSITY_ORDER."
            )

        # 5 & 6. Per-profile validations.
        for idx, profile in enumerate(spec.item_count_profiles):
            lo, hi = profile.item_range
            if lo > hi:
                raise RuntimeError(
                    f"[registry] Block '{variant}' profile #{idx} "
                    f"(layout_variant='{profile.layout_variant}') has "
                    f"invalid item_range ({lo}, {hi}): min > max."
                )

            if profile.width_class == "wide":
                bad = [
                    side
                    for side in ("left", "right")
                    if side in profile.supported_layouts
                ]
                if bad:
                    raise RuntimeError(
                        f"[registry] Block '{variant}' profile #{idx} "
                        f"(layout_variant='{profile.layout_variant}') is "
                        f"width_class='wide' but declares disallowed "
                        f"supported_layouts {bad}; wide blocks cannot use "
                        f"'left' or 'right' layouts."
                    )


# Run validation at import time so structural errors surface immediately
# on engine startup rather than at slide-generation time.
validate_catalog()


__all__ = ["ALL_BLOCKS", "validate_catalog"]