from __future__ import annotations

from typing import Literal

BRIEF_DENSITY = Literal["low", "medium", "high"]
ENGINE_DENSITY = Literal["ultra_sparse", "sparse", "balanced", "standard", "dense", "super_dense"]

_ENGINE_DENSITIES = {"ultra_sparse", "sparse", "balanced", "standard", "dense", "super_dense"}


def map_brief_density_to_engine(brief: str, slide_index: int | None = None) -> str:
    density = str(brief or "medium").strip().lower()
    if density in _ENGINE_DENSITIES:
        return density

    parity = 0 if slide_index is None else abs(int(slide_index)) % 2

    if density == "low":
        return "sparse" if parity == 0 else "ultra_sparse"
    if density == "medium":
        return "balanced" if parity == 0 else "standard"
    if density == "high":
        return "dense" if parity == 0 else "super_dense"

    return "balanced" if parity == 0 else "standard"