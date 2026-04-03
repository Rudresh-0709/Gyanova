from __future__ import annotations

try:
    from app.services.node.slides.gyml.image_manager import ImageManager
except ImportError:
    from ..slides.gyml.image_manager import ImageManager  # type: ignore


_DENSITY_TO_FLOAT = {
    "ultra_sparse": 0.25,
    "sparse": 0.45,
    "balanced": 0.65,
    "standard": 0.90,
    "dense": 1.05,
    "super_dense": 1.25,
}


def _normalize_history_layout(token: str) -> str:
    value = str(token or "").strip().lower()
    if not value:
        return ""
    if "|" in value:
        parts = value.split("|", 1)
        return str(parts[1]).strip().lower()
    return value


def determine_image_layout_v2(
    engine_density: str,
    intent: str,
    slide_index: int,
    has_wide_block: bool,
    layout_history: list[str] | None = None,
    explicit_layout: str | None = None,
) -> str:
    density_key = str(engine_density or "balanced").strip().lower()
    mapped_float = _DENSITY_TO_FLOAT.get(density_key, _DENSITY_TO_FLOAT["balanced"])

    raw_result = ImageManager.determine_placement(
        slide_density=mapped_float,
        has_user_image=False,
        intent=intent,
        explicit_layout=explicit_layout,
        slide_index=slide_index,
        has_wide_block=has_wide_block,
    )

    raw_result = str(raw_result or "blank").strip().lower()

    if density_key in ("dense", "super_dense") and raw_result in ("left", "right"):
        raw_result = "top" if slide_index % 2 == 0 else "bottom"

    normalized_history = [_normalize_history_layout(item) for item in list(layout_history or []) if str(item or "").strip()]
    if normalized_history:
        last_layout = normalized_history[-1]
        if raw_result == last_layout:
            flip_map = {
                "left": "right",
                "right": "left",
                "top": "bottom",
                "bottom": "top",
                "blank": "left",
            }
            raw_result = flip_map.get(raw_result, raw_result)

        if len(normalized_history) >= 2:
            last_two = normalized_history[-2:]
            if all(ly in ("left", "right") for ly in last_two) and raw_result in ("left", "right"):
                raw_result = "top" if slide_index % 2 == 0 else "bottom"

    return raw_result
