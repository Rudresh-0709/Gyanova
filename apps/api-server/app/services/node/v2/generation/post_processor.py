from __future__ import annotations

from typing import Any, Callable, Dict, List

from .prompt_builder import (
    PromptBuildResult,
    _build_image_prompt,
    _ensure_sentence,
    _normalize_layout,
)
from .response_validator import (
    _MAX_ITEM_DESCRIPTION_WORDS,
    _MAX_ITEM_HEADING_LENGTH,
    _count_words,
    _trim_to_word_budget,
    _validate_payload,
    _validate_with_existing_validator,
)


def _default_icon_name(index: int) -> str:
    icons = [
        "ri-lightbulb-line",
        "ri-compass-3-line",
        "ri-flag-2-line",
        "ri-book-open-line",
        "ri-shield-check-line",
        "ri-line-chart-line",
    ]
    return icons[index % len(icons)]


# Block types that count as structured primary blocks (non-trivial teaching content)
_STRUCTURED_PRIMARY_TYPES = {
    "smart_layout",
    "comparison_table",
    "key_value_list",
    "numbered_list",
    "formula_block",
    "process_arrow_block",
    "cyclic_process_block",
    "feature_showcase_block",
    "hub_and_spoke",
    "cyclic_block",
    "sequential_output",
    "step_list",
    "rich_text",
}

# Block types that are only acceptable as *supporting* blocks (never primary)
_SUPPORTING_ONLY_TYPES = {
    "heading",
    "paragraph",
    "intro_paragraph",
    "context_paragraph",
    "annotation_paragraph",
    "outro_paragraph",
    "caption",
    "image",
}


def _find_primary_block_index(blocks: List[Dict[str, Any]]) -> int:
    for i, block in enumerate(blocks):
        if not isinstance(block, dict):
            continue
        block_type = str(block.get("type") or "").strip().lower()
        if block_type in _STRUCTURED_PRIMARY_TYPES:
            return i
    return -1


def _pick_best_supporting_fact(plan_item: Dict[str, Any]) -> str:
    key_facts = [
        str(v).strip() for v in plan_item.get("key_facts", []) if str(v).strip()
    ]
    must_cover = [
        str(v).strip() for v in plan_item.get("must_cover", []) if str(v).strip()
    ]

    # Prefer richer full-sentence facts over terse keywords.
    if key_facts:
        key_facts_sorted = sorted(key_facts, key=lambda text: len(text), reverse=True)
        return _ensure_sentence(key_facts_sorted[0])
    if must_cover:
        return _ensure_sentence(must_cover[0])
    return ""


def _build_intro_text(plan_item: Dict[str, Any]) -> str:
    objective = str(plan_item.get("objective") or "").strip()
    if objective:
        return _ensure_sentence(objective)
    title = str(plan_item.get("title") or "this topic").strip()
    return _ensure_sentence(
        f"Let's frame {title} before diving into the core structure"
    )


def _build_context_text(plan_item: Dict[str, Any]) -> str:
    title = str(plan_item.get("title") or "this topic").strip()
    objective = str(plan_item.get("objective") or "").strip()
    best_fact = _pick_best_supporting_fact(plan_item)

    if best_fact and objective:
        return _ensure_sentence(f"{objective} {best_fact}")
    if best_fact:
        return best_fact
    if objective:
        return _ensure_sentence(objective)
    return _ensure_sentence(
        f"This context sets up the core idea in {title} with a concrete teaching anchor"
    )


def _build_callout_text(plan_item: Dict[str, Any]) -> str:
    assessment = str(plan_item.get("assessment_prompt") or "").strip()
    best_fact = _pick_best_supporting_fact(plan_item)
    if best_fact and assessment:
        return _ensure_sentence(f"{best_fact} Check your understanding: {assessment}")
    if assessment:
        return _ensure_sentence(f"Check your understanding: {assessment}")
    if best_fact:
        return _ensure_sentence(f"Key takeaway: {best_fact}")
    return "Key takeaway: summarize the most actionable insight from this slide."


def _enforce_supporting_for_big_boxes(
    payload: Dict[str, Any], plan_item: Dict[str, Any]
) -> None:
    """Ensure solidBoxesWithIconsInside always has a supporting paragraph block."""
    blocks = payload.get("contentBlocks", [])
    if not isinstance(blocks, list) or not blocks:
        return

    primary_idx = _find_primary_block_index(blocks)
    if primary_idx < 0 or primary_idx >= len(blocks):
        return

    primary_block = blocks[primary_idx] if isinstance(blocks[primary_idx], dict) else {}
    primary_type = str(primary_block.get("type") or "").strip().lower()
    primary_variant = str(primary_block.get("variant") or "").strip()

    if primary_type != "smart_layout" or primary_variant != "solidBoxesWithIconsInside":
        return

    paragraph_like = {
        "paragraph",
        "intro_paragraph",
        "context_paragraph",
        "annotation_paragraph",
        "outro_paragraph",
    }
    has_supporting = any(
        isinstance(block, dict)
        and str(block.get("type") or "").strip().lower() in paragraph_like
        for block in blocks
    )
    if has_supporting:
        return

    insert_at = min(primary_idx + 1, len(blocks))
    blocks.insert(
        insert_at,
        {"type": "annotation_paragraph", "text": _build_callout_text(plan_item)},
    )
    payload["contentBlocks"] = blocks
    payload["primary_block_index"] = _find_primary_block_index(blocks)


def _apply_composition_style(
    payload: Dict[str, Any], plan_item: Dict[str, Any], composition_style: str
) -> None:
    blocks = payload.get("contentBlocks", [])
    if not isinstance(blocks, list):
        return

    paragraph_like = {
        "paragraph",
        "intro_paragraph",
        "context_paragraph",
        "annotation_paragraph",
        "outro_paragraph",
    }

    # Keep non-paragraph-like blocks intact, then layer style-specific supporting text.
    filtered_blocks = []
    for block in blocks:
        if not isinstance(block, dict):
            continue
        block_type = str(block.get("type") or "").strip().lower()
        if block_type in paragraph_like:
            continue
        filtered_blocks.append(block)

    primary_idx = _find_primary_block_index(filtered_blocks)
    if primary_idx < 0:
        payload["contentBlocks"] = filtered_blocks
        return

    before_primary: List[Dict[str, Any]] = []
    after_primary: List[Dict[str, Any]] = []

    if composition_style == "context_then_primary":
        before_primary.append(
            {"type": "context_paragraph", "text": _build_context_text(plan_item)}
        )
    elif composition_style == "primary_then_callout":
        after_primary.append(
            {"type": "annotation_paragraph", "text": _build_callout_text(plan_item)}
        )
    elif composition_style == "intro_then_primary":
        before_primary.append(
            {"type": "intro_paragraph", "text": _build_intro_text(plan_item)}
        )

    rebuilt: List[Dict[str, Any]] = []
    rebuilt.extend(filtered_blocks[:primary_idx])
    rebuilt.extend(before_primary)
    rebuilt.append(filtered_blocks[primary_idx])
    rebuilt.extend(after_primary)
    rebuilt.extend(filtered_blocks[primary_idx + 1 :])

    # Hard rule: never allow intro + annotation/outro on the same slide.
    has_intro = any(
        str(block.get("type") or "").strip().lower() == "intro_paragraph"
        for block in rebuilt
        if isinstance(block, dict)
    )
    if has_intro:
        rebuilt = [
            block
            for block in rebuilt
            if not (
                isinstance(block, dict)
                and str(block.get("type") or "").strip().lower()
                in {"annotation_paragraph", "outro_paragraph"}
            )
        ]

    payload["contentBlocks"] = rebuilt
    payload["primary_block_index"] = _find_primary_block_index(rebuilt)


def _enforce_side_strip_only_on_blank_layout(payload: Dict[str, Any]) -> None:
    blocks = payload.get("contentBlocks", [])
    if not isinstance(blocks, list):
        return

    image_layout = (
        str(payload.get("image_layout") or payload.get("layout") or "blank")
        .strip()
        .lower()
    )
    is_blank_layout = image_layout == "blank"

    rebuilt: List[Dict[str, Any]] = []
    for block in blocks:
        if not isinstance(block, dict):
            rebuilt.append(block)
            continue

        block_type = str(block.get("type") or "").strip().lower()
        variant = str(block.get("variant") or "").strip().lower()
        is_side_strip = block_type == "side_strip_paragraph" or variant in {
            "side-strip",
            "side-strip-left",
        }

        if is_side_strip and not is_blank_layout:
            text = str(block.get("text") or "").strip()
            if text:
                rebuilt.append({"type": "annotation_paragraph", "text": text})
            continue

        rebuilt.append(block)

    payload["contentBlocks"] = rebuilt


def _enforce_primary_description_word_budget(payload: Dict[str, Any]) -> None:
    """
    Mutates ``payload`` in-place: ensure the primary smart_layout item descriptions
    are scannable by keeping them within the configured word budget.
    """
    try:
        primary_index = int(payload.get("primary_block_index", 0) or 0)
    except Exception:
        primary_index = 0

    blocks = payload.get("contentBlocks", [])
    if not isinstance(blocks, list) or not blocks:
        return
    if primary_index < 0 or primary_index >= len(blocks):
        return

    block = blocks[primary_index]
    if not isinstance(block, dict):
        return
    if str(block.get("type") or "").strip().lower() != "smart_layout":
        return

    items = block.get("items", [])
    if not isinstance(items, list):
        return

    for item in items:
        if not isinstance(item, dict):
            continue
        description = str(item.get("description") or "").strip()
        if not description:
            continue
        if _count_words(description) > _MAX_ITEM_DESCRIPTION_WORDS:
            item["description"] = _trim_to_word_budget(
                description, _MAX_ITEM_DESCRIPTION_WORDS
            )


def _branch_from_item(item: Dict[str, Any], index: int) -> Dict[str, Any]:
    suffix = chr(65 + index)
    label = str(
        item.get("path_label")
        or item.get("heading")
        or item.get("label")
        or item.get("title")
        or f"Path {suffix}"
    ).strip()
    description = str(
        item.get("path_description")
        or item.get("description")
        or item.get("text")
        or item.get("content")
        or ""
    ).strip()
    outcome = str(
        item.get("outcome_label")
        or item.get("outcome")
        or item.get("result")
        or f"Outcome {suffix}"
    ).strip()

    branch = {
        "edge_label": str(item.get("edge_label") or f"Option {suffix}").strip(),
        "path_label": label,
        "path_description": description,
        "outcome_label": outcome,
        "outcome_description": str(
            item.get("outcome_description") or item.get("result_description") or description
        ).strip(),
    }
    color = item.get("color")
    if color:
        branch["color"] = color
    return branch


def _fallback_branch_items(plan_item: Dict[str, Any], target_count: int) -> List[Dict[str, Any]]:
    source_values = [
        str(value).strip()
        for value in (
            list(plan_item.get("must_cover", []) or [])
            + list(plan_item.get("key_facts", []) or [])
        )
        if str(value).strip()
    ]
    if not source_values:
        objective = str(plan_item.get("objective") or "").strip()
        title = str(plan_item.get("title") or "the topic").strip()
        source_values = [
            objective or f"Apply the first condition in {title}.",
            str(plan_item.get("assessment_prompt") or "").strip()
            or f"Choose the alternate route in {title}.",
        ]

    items: List[Dict[str, Any]] = []
    for index, value in enumerate(source_values[:target_count]):
        heading = value[:_MAX_ITEM_HEADING_LENGTH].strip()
        items.append({"heading": heading or f"Path {index + 1}", "description": value})
    while len(items) < target_count:
        index = len(items)
        items.append(
            {
                "heading": f"Path {chr(65 + index)}",
                "description": "Use this route when the matching condition applies.",
            }
        )
    return items


def _normalize_branching_path_blocks(
    payload: Dict[str, Any], plan_item: Dict[str, Any]
) -> None:
    blocks = payload.get("contentBlocks", [])
    if not isinstance(blocks, list):
        return

    constraints = plan_item.get("block_constraints") or {}
    try:
        min_branches = int(constraints.get("item_min", 2))
    except Exception:
        min_branches = 2
    try:
        max_branches = int(constraints.get("item_max", 4))
    except Exception:
        max_branches = 4
    min_branches = max(2, min(min_branches, max_branches))
    max_branches = max(min_branches, max_branches)

    for block in blocks:
        if not isinstance(block, dict):
            continue
        if str(block.get("type") or "").strip().lower() != "smart_layout":
            continue
        if str(block.get("variant") or "").strip() != "branching_path":
            continue

        if not isinstance(block.get("start"), dict) or not block.get("start"):
            block["start"] = {
                "label": "Start",
                "description": _ensure_sentence(plan_item.get("objective") or ""),
            }
        if not isinstance(block.get("decision"), dict) or not block.get("decision"):
            block["decision"] = {
                "label": "Choose Path",
                "description": "Decide which condition applies.",
            }

        raw_branches = block.get("branches", [])
        branches = [
            _branch_from_item(branch, index)
            for index, branch in enumerate(raw_branches)
            if isinstance(branch, dict)
        ] if isinstance(raw_branches, list) else []

        if len(branches) < min_branches:
            raw_items = block.get("items", [])
            item_branches = [
                _branch_from_item(item, index)
                for index, item in enumerate(raw_items)
                if isinstance(item, dict)
            ] if isinstance(raw_items, list) else []
            branches = item_branches or branches

        if len(branches) < min_branches:
            branches = [
                _branch_from_item(item, index)
                for index, item in enumerate(
                    _fallback_branch_items(plan_item, min_branches)
                )
            ]

        block["branches"] = branches[:max_branches]
        block.pop("items", None)


def _has_structured_primary(blocks: List[Dict[str, Any]]) -> bool:
    """Return True if any block in the list qualifies as a structured primary block."""
    return any(
        str(b.get("type") or "").strip().lower() in _STRUCTURED_PRIMARY_TYPES
        for b in blocks
        if isinstance(b, dict)
    )


def _enforce_structured_primary(
    payload: Dict[str, Any], plan_item: Dict[str, Any], smart_layout_variant: str
) -> None:
    """
    Mutates ``payload`` in-place: if the slide has no structured primary block,
    inject a smart_layout block built from plan_item data as a fallback.

    This satisfies the hard requirement that non-title slides always include
    a structured primary block.
    """
    blocks = payload.get("contentBlocks", [])
    if not isinstance(blocks, list):
        return

    # Check if this is a sparse/title-only block variant - those may skip primary block.
    # Sparse blocks that intentionally have no structured primary
    sparse_variants = {"definition", "quote", "callout", "keyTakeaway", "annotation_paragraph"}
    selected_block_variant = str(payload.get("selected_block_variant") or plan_item.get("selected_block_variant") or "").strip()
    if selected_block_variant in sparse_variants:
        return

    if _has_structured_primary(blocks):
        return

    # Build a minimal smart_layout block from plan_item content
    title = str(plan_item.get("title") or "The Topic").strip()
    objective = str(plan_item.get("objective") or "").strip()
    must_cover = [
        str(v).strip() for v in plan_item.get("must_cover", []) if str(v).strip()
    ]
    key_facts = [
        str(v).strip() for v in plan_item.get("key_facts", []) if str(v).strip()
    ]

    items = []
    # Use must_cover points as items
    for point in (must_cover + key_facts)[:6]:
        items.append(
            {"heading": point[:_MAX_ITEM_HEADING_LENGTH], "description": point}
        )
    # Ensure at least 2 items
    if len(items) < 2:
        items = [
            {"heading": "Key Concept", "description": objective or title},
            {
                "heading": "Why It Matters",
                "description": str(
                    plan_item.get("assessment_prompt") or "Reflect on what you learned."
                ),
            },
        ]

    fallback_block: Dict[str, Any] = {
        "type": "smart_layout",
        "variant": smart_layout_variant or "bigBullets",
        "items": items[:6],
    }

    if (smart_layout_variant or "").strip() == "solidBoxesWithIconsInside":
        for idx, item in enumerate(fallback_block.get("items", [])):
            if isinstance(item, dict) and not str(item.get("icon_name") or "").strip():
                item["icon_name"] = _default_icon_name(idx)

    # Insert after the first heading/paragraph block (or at position 1)
    insert_at = 1
    for i, block in enumerate(blocks):
        if (
            isinstance(block, dict)
            and str(block.get("type") or "").strip().lower()
            not in _SUPPORTING_ONLY_TYPES
        ):
            break
        insert_at = i + 1

    blocks.insert(insert_at, fallback_block)
    payload["contentBlocks"] = blocks
    # Update primary_block_index to point to the injected block
    payload["primary_block_index"] = insert_at


def post_process_payload(
    payload: Dict[str, Any],
    plan_item: Dict[str, Any],
    prompt_context: PromptBuildResult,
    fallback_builder: Callable[[Dict[str, Any]], Dict[str, Any]],
) -> Dict[str, Any]:
    payload = _validate_payload(payload)

    image_tier = prompt_context.image_tier
    if image_tier == "hero":
        payload.pop("accentImagePrompt", None)
        hero_prompt = _build_image_prompt(plan_item)
        payload["heroImagePrompt"] = hero_prompt
        payload["imagePrompt"] = hero_prompt
    elif image_tier == "accent":
        payload.pop("heroImagePrompt", None)
        accent_prompt = _build_image_prompt(plan_item)
        payload["accentImagePrompt"] = accent_prompt
        payload["imagePrompt"] = accent_prompt
    else:
        payload.pop("accentImagePrompt", None)
        payload.pop("heroImagePrompt", None)
        payload.pop("imagePrompt", None)

    # Enforce: use the layout decided by the planner (ground truth for variety/constraints)
    # Use allows_wide_layout + supported_layouts to pick the best image layout
    allows_wide_layout = bool(plan_item.get("allows_wide_layout", True))
    image_role = str(plan_item.get("image_role", "none")).strip().lower()
    supported_layouts = prompt_context.supported_layouts

    if image_role == "content" and supported_layouts:
        # Pick a side layout if supported, else blank
        side_layouts = [l for l in supported_layouts if l in {"left", "right"}]
        planned_layout = side_layouts[0] if side_layouts else "blank"
    elif image_role == "accent":
        top_bottom = [l for l in supported_layouts if l in {"top", "bottom"}]
        planned_layout = top_bottom[0] if top_bottom else "blank"
    else:
        planned_layout = "blank"

    planned_layout = _normalize_layout(planned_layout)
    payload["layout"] = planned_layout
    payload["image_layout"] = planned_layout

    # Enforce: non-title slides must have a structured primary block.
    # If the LLM only produced paragraphs/headings, inject a fallback smart_layout.
    _enforce_structured_primary(
        payload,
        plan_item,
        prompt_context.smart_layout_variant,
    )

    # branching_path is not an item grid. Repair older/partial LLM outputs so
    # the renderer always has real branches below the start and decision nodes.
    _normalize_branching_path_blocks(payload, plan_item)

    # Enforce composition style and hard exclusion rule for intro+callout coexistence.
    _apply_composition_style(payload, plan_item, prompt_context.composition_style)

    # Keep primary smart_layout descriptions within the scannable word budget.
    _enforce_primary_description_word_budget(payload)

    # Hard rule: solid boxes primary must include at least one supporting paragraph block.
    _enforce_supporting_for_big_boxes(payload, plan_item)

    # Enforce: side-strip supporting text may only appear on blank image layout slides.
    _enforce_side_strip_only_on_blank_layout(payload)

    is_valid, errors, warnings = _validate_with_existing_validator(payload)
    if not is_valid:
        fallback = fallback_builder(plan_item)
        fallback = _validate_payload(fallback)
        payload = fallback
        payload["validation_errors"] = errors
    if warnings:
        payload["validation_warnings"] = warnings

    payload["title"] = prompt_context.title
    payload["selected_template"] = prompt_context.selected_template
    payload["selected_block_variant"] = prompt_context.selected_block_variant
    payload["image_need"] = prompt_context.image_need
    payload["image_tier"] = prompt_context.image_tier
    payload["designer_blueprint"] = prompt_context.designer_blueprint
    payload["slide_density"] = prompt_context.slide_density
    payload["composition_style"] = prompt_context.composition_style
    return payload
