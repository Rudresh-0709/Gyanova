from __future__ import annotations

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
    block_spec=None,
    layout_history: list[str] | None = None,
    explicit_layout: str | None = None,
    allowed_layouts: list[str] | tuple[str, ...] | None = None,
) -> str:
    """
    Determines image layout by prioritizing Block Catalog constraints.
    Bypasses legacy heuristics in favor of variety-aware catalog rotation.
    """
    # 1. Determine the pool of valid layouts for this specific block
    # Use explicit check to allow empty tuples if they were provided (though catalog defaults to ())
    block_supported = getattr(block_spec, "supported_layouts", None)
    
    if block_supported is not None and len(block_supported) > 0:
        valid_pool = list(block_supported)
    elif block_supported is not None:
        # If it was empty but not None, it means all are allowed (per catalog documentation)
        valid_pool = ["top", "bottom", "blank"] if has_wide_block else ["left", "right", "top", "bottom", "blank"]
    else:
        # Fallback for un-audited or legacy blocks (block_spec is None or doesn't have the attr)
        valid_pool = ["top", "bottom", "blank"] if has_wide_block else ["left", "right", "top", "bottom", "blank"]

    # 2. Intersect with template constraints
    if allowed_layouts:
        template_set = {str(l).strip().lower() for l in allowed_layouts}
        # Filter the pool to only what the template allows
        intersection = [ly for ly in valid_pool if ly in template_set]
        if intersection:
            valid_pool = intersection
        # else: if no overlap, we keep valid_pool as is (safest fallback for rendering)

    # 3. Handle explicit requests (from user/LLM)
    if explicit_layout and explicit_layout in valid_pool:
        return explicit_layout

    # 4. Variety: Simple rotation through the active (non-blank) pool
    active_pool = [l for l in valid_pool if l != "blank"]
    if not active_pool:
        active_pool = ["blank"]

    # Use slide_index to ensures alternating placement (left/right or top/bottom)
    choice = active_pool[slide_index % len(active_pool)]
    
    # 5. Flip if it repeats the previous slide (Deep variety)
    normalized_history = [
        _normalize_history_layout(item)
        for item in list(layout_history or [])
        if str(item or "").strip()
    ]
    if normalized_history and normalized_history[-1] == choice and len(active_pool) > 1:
        # Simple cyclic rotation
        idx = (active_pool.index(choice) + 1) % len(active_pool)
        choice = active_pool[idx]

    return choice
