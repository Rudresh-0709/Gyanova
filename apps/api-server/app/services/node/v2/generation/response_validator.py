from __future__ import annotations

from typing import Any, Dict, List, Tuple

try:
    from app.services.node.blocks.shared.schema_loader import load_schema
except ImportError:
    from ...blocks.shared.schema_loader import load_schema  # type: ignore

try:
    from app.services.node.slides.gyml.definitions import (
        GyMLBody,
        GyMLColumnDiv,
        GyMLColumns,
        GyMLComparisonTable,
        GyMLCyclicBlock,
        GyMLCyclicItem,
        GyMLCyclicProcessBlock,
        GyMLCyclicProcessItem,
        GyMLFeatureShowcaseBlock,
        GyMLFeatureShowcaseItem,
        GyMLFormulaBlock,
        GyMLHeading,
        GyMLHierarchyTree,
        GyMLHubAndSpoke,
        GyMLHubAndSpokeItem,
        GyMLIcon,
        GyMLImage,
        GyMLKeyValueItem,
        GyMLKeyValueList,
        GyMLLabeledDiagram,
        GyMLNumberedList,
        GyMLNumberedListItem,
        GyMLPanel,
        GyMLParagraph,
        GyMLProcessArrowBlock,
        GyMLProcessArrowItem,
        GyMLRichText,
        GyMLSection,
        GyMLSequentialOutput,
        GyMLSmartLayout,
        GyMLSmartLayoutItem,
        GyMLSplitPanel,
        GyMLTreeNode,
    )
    from app.services.node.slides.gyml.validator import GyMLValidator
except ImportError:
    from ...slides.gyml.definitions import (  # type: ignore
        GyMLBody,
        GyMLColumnDiv,
        GyMLColumns,
        GyMLComparisonTable,
        GyMLCyclicBlock,
        GyMLCyclicItem,
        GyMLCyclicProcessBlock,
        GyMLCyclicProcessItem,
        GyMLFeatureShowcaseBlock,
        GyMLFeatureShowcaseItem,
        GyMLFormulaBlock,
        GyMLHeading,
        GyMLHierarchyTree,
        GyMLHubAndSpoke,
        GyMLHubAndSpokeItem,
        GyMLIcon,
        GyMLImage,
        GyMLKeyValueItem,
        GyMLKeyValueList,
        GyMLLabeledDiagram,
        GyMLNumberedList,
        GyMLNumberedListItem,
        GyMLPanel,
        GyMLParagraph,
        GyMLProcessArrowBlock,
        GyMLProcessArrowItem,
        GyMLRichText,
        GyMLSection,
        GyMLSequentialOutput,
        GyMLSmartLayout,
        GyMLSmartLayoutItem,
        GyMLSplitPanel,
        GyMLTreeNode,
    )
    from ...slides.gyml.validator import GyMLValidator  # type: ignore

from .prompt_builder import _normalize_layout


_SMART_LAYOUT_ITEM_FIELDS = {
    "heading",
    "description",
    "points",
    "year",
    "value",
    "label",
}


def _schema_fields(item_schema: Dict[str, Any], section: str) -> Dict[str, Any]:
    fields = item_schema.get(section, {})
    return fields if isinstance(fields, dict) else {}


def _item_schema_for_variant(variant: str) -> Dict[str, Any]:
    schema = load_schema(variant)
    item_schema = schema.get("item_schema", {})
    return item_schema if isinstance(item_schema, dict) else {}


def _schema_item_field_names(variant: str) -> set[str]:
    item_schema = _item_schema_for_variant(variant)
    field_names = set(_schema_fields(item_schema, "required_fields"))
    field_names.update(_schema_fields(item_schema, "optional_fields"))
    return field_names


def _accepted_item_fields_for_variant(variant: str) -> set[str]:
    schema_fields = _schema_item_field_names(variant)
    accepted_fields = schema_fields & _SMART_LAYOUT_ITEM_FIELDS
    return accepted_fields if accepted_fields else set(_SMART_LAYOUT_ITEM_FIELDS)


def _field_word_limits_from_schema(
    variant: str,
    field_name: str,
    default_min: int | None = None,
    default_max: int | None = None,
) -> Tuple[int | None, int | None]:
    item_schema = _item_schema_for_variant(variant)
    for fields in (
        _schema_fields(item_schema, "required_fields"),
        _schema_fields(item_schema, "optional_fields"),
    ):
        field_schema = fields.get(field_name)
        if isinstance(field_schema, dict):
            return (
                field_schema.get("min_words", default_min),
                field_schema.get("max_words", default_max),
            )
    return default_min, default_max


def _validate_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    title = str(payload.get("title") or "Untitled Slide").strip()
    layout = _normalize_layout(
        payload.get("layout") or payload.get("image_layout") or "blank"
    )
    image_layout = _normalize_layout(payload.get("image_layout") or layout)
    if layout == "blank" and image_layout != "blank":
        layout = image_layout
    elif image_layout == "blank" and layout != "blank":
        image_layout = layout
    content_blocks = payload.get("contentBlocks", [])
    if not isinstance(content_blocks, list):
        content_blocks = []
    normalized_blocks: List[Dict[str, Any]] = []
    for block in content_blocks:
        if not isinstance(block, dict):
            continue
        block_type = str(block.get("type") or "").strip().lower()
        if block_type in {
            "heading",
            "paragraph",
            "intro_paragraph",
            "context_paragraph",
            "annotation_paragraph",
            "outro_paragraph",
            "caption",
            "comparison_table",
            "key_value_list",
            "rich_text",
            "numbered_list",
            "formula_block",
            "process_arrow_block",
            "cyclic_process_block",
            "smart_layout",
            "image",
        }:
            normalized_blocks.append(block)
            continue

        content = block.get("content")
        if isinstance(content, list) and content:
            items = []
            for i, item in enumerate(content[:4]):
                text = str(item).strip()
                if text:
                    items.append({"heading": f"Point {i + 1}", "description": text})
            if items:
                normalized_blocks.append(
                    {"type": "smart_layout", "variant": "bigBullets", "items": items}
                )
                continue

        text_value = str(
            block.get("text") or block.get("description") or block.get("title") or title
        ).strip()
        normalized_blocks.append({"type": "paragraph", "text": text_value})

    if not normalized_blocks:
        normalized_blocks = [{"type": "paragraph", "text": title}]
    if not isinstance(payload.get("primary_block_index"), int):
        payload["primary_block_index"] = 1 if len(normalized_blocks) > 1 else 0
    payload["title"] = title
    payload["layout"] = layout
    payload["image_layout"] = image_layout
    payload["contentBlocks"] = normalized_blocks
    return payload


def _slide_to_section(payload: Dict[str, Any]) -> GyMLSection:
    # Minimal mapping for structural validation with the existing validator.
    slide_title = str(payload.get("title") or "Untitled Slide")
    image_layout = str(payload.get("image_layout") or payload.get("layout") or "blank")
    body_children: List[Any] = [GyMLHeading(level=1, text=slide_title)]
    for block in payload.get("contentBlocks", []):
        if not isinstance(block, dict):
            continue
        block_type = str(block.get("type") or "paragraph").strip().lower()
        if block_type in {
            "paragraph",
            "intro_paragraph",
            "context_paragraph",
            "annotation_paragraph",
            "outro_paragraph",
            "caption",
        }:
            body_children.append(
                GyMLParagraph(
                    text=str(block.get("text") or block.get("description") or "")
                )
            )
        elif block_type == "comparison_table":
            body_children.append(
                GyMLComparisonTable(
                    headers=list(block.get("headers", [])),
                    rows=list(block.get("rows", [])),
                    caption=block.get("caption"),
                )
            )
        elif block_type == "key_value_list":
            items = [
                GyMLKeyValueItem(
                    key=str(item.get("key") or item.get("label") or "Key"),
                    value=str(item.get("value") or item.get("description") or "Value"),
                )
                for item in block.get("items", [])
                if isinstance(item, dict)
            ]
            body_children.append(GyMLKeyValueList(items=items))
        elif block_type == "rich_text":
            body_children.append(
                GyMLRichText(paragraphs=[str(p) for p in block.get("paragraphs", [])])
            )
        elif block_type == "numbered_list":
            items = [
                GyMLNumberedListItem(
                    title=str(item.get("title") or item.get("label") or "Item"),
                    description=str(item.get("description") or ""),
                )
                for item in block.get("items", [])
                if isinstance(item, dict)
            ]
            body_children.append(GyMLNumberedList(items=items))
        elif block_type == "formula_block":
            variables = []
            for var in block.get("variables", []):
                if isinstance(var, dict):
                    variables.append(
                        {
                            "name": str(var.get("name") or "x"),
                            "meaning": str(var.get("meaning") or ""),
                        }
                    )
            body_children.append(
                GyMLFormulaBlock(
                    expression=str(block.get("expression") or ""),
                    variables=variables,
                    example=str(block.get("example") or ""),
                )
            )
        elif block_type == "process_arrow_block":
            items = [
                GyMLProcessArrowItem(
                    label=str(item.get("label") or "Step"),
                    description=str(item.get("description") or ""),
                    imagePrompt=str(item.get("imagePrompt") or ""),
                    color=item.get("color"),
                )
                for item in block.get("items", [])
                if isinstance(item, dict)
            ]
            body_children.append(GyMLProcessArrowBlock(items=items))
        elif block_type == "cyclic_process_block":
            items = [
                GyMLCyclicProcessItem(
                    label=str(item.get("label") or "Step"),
                    description=str(item.get("description") or ""),
                    image_url=str(
                        item.get("image_url") or item.get("imagePrompt") or ""
                    ),
                )
                for item in block.get("items", [])
                if isinstance(item, dict)
            ]
            body_children.append(GyMLCyclicProcessBlock(items=items))
        elif block_type == "feature_showcase_block":
            items = []
            for it in block.get("items", []):
                if not isinstance(it, dict):
                    continue
                icon_name = it.get("icon_name") or it.get("icon")
                items.append(
                    GyMLFeatureShowcaseItem(
                        label=str(it.get("heading") or it.get("title") or "Feature"),
                        description=it.get("description"),
                        icon=str(icon_name) if icon_name else None,
                    )
                )
            body_children.append(
                GyMLFeatureShowcaseBlock(
                    title=str(block.get("title") or slide_title),
                    items=items,
                    image_url=str(
                        block.get("image_url") or block.get("imagePrompt") or ""
                    ),
                )
            )
        elif block_type == "hub_and_spoke":
            items = []
            for it in block.get("items", []):
                if not isinstance(it, dict):
                    continue
                icon_name = it.get("icon_name") or it.get("icon")
                items.append(
                    GyMLHubAndSpokeItem(
                        label=str(it.get("heading") or it.get("title") or "Point"),
                        description=it.get("description"),
                        icon=str(icon_name) if icon_name else None,
                    )
                )
            body_children.append(
                GyMLHubAndSpoke(
                    hub_label=str(block.get("hub_label") or slide_title), items=items
                )
            )
        elif block_type == "smart_layout":
            variant = block.get("variant")
            # Route specialized variants to their dedicated GyML classes
            if variant == "hubAndSpoke":
                items = []
                for it in block.get("items", []):
                    if not isinstance(it, dict):
                        continue
                    icon_name = it.get("icon_name") or it.get("icon")
                    items.append(
                        GyMLHubAndSpokeItem(
                            label=str(it.get("heading") or it.get("title") or "Point"),
                            description=it.get("description"),
                            icon=str(icon_name) if icon_name else None,
                        )
                    )
                body_children.append(
                    GyMLHubAndSpoke(
                        hub_label=str(block.get("hub_label") or slide_title),
                        items=items,
                    )
                )
            elif variant == "featureShowcase":
                items = []
                for it in block.get("items", []):
                    if not isinstance(it, dict):
                        continue
                    icon_name = it.get("icon_name") or it.get("icon")
                    items.append(
                        GyMLFeatureShowcaseItem(
                            label=str(
                                it.get("heading") or it.get("title") or "Feature"
                            ),
                            description=it.get("description"),
                            icon=str(icon_name) if icon_name else None,
                        )
                    )
                body_children.append(
                    GyMLFeatureShowcaseBlock(
                        title=str(block.get("title") or slide_title),
                        items=items,
                        image_url=str(
                            block.get("image_url") or block.get("imagePrompt") or ""
                        ),
                    )
                )
            elif variant == "cyclicBlock":
                items = []
                for it in block.get("items", []):
                    if not isinstance(it, dict):
                        continue
                    icon_name = it.get("icon_name") or it.get("icon")
                    items.append(
                        GyMLCyclicItem(
                            label=str(it.get("heading") or it.get("title") or "Stage"),
                            description=it.get("description"),
                            icon=str(icon_name) if icon_name else None,
                        )
                    )
                body_children.append(
                    GyMLCyclicBlock(
                        items=items,
                        hub_label=str(block.get("hub_label") or slide_title),
                    )
                )
            elif variant == "sequentialOutput":
                items = [
                    str(it.get("text") or it.get("description") or it)
                    for it in block.get("items", [])
                ]
                body_children.append(GyMLSequentialOutput(items=items))
            else:
                accepted_fields = _accepted_item_fields_for_variant(
                    str(block.get("variant") or "bigBullets")
                )
                items = []
                for item in block.get("items", []):
                    if not isinstance(item, dict):
                        continue
                    item_kwargs = {
                        k: v
                        for k, v in item.items()
                        if k in accepted_fields
                    }
                    # Accept both v2 (`icon_name`) and legacy (`icon`) keys.
                    icon_name = item.get("icon_name") or item.get("icon")
                    if icon_name:
                        item_kwargs["icon"] = GyMLIcon(alt=str(icon_name))
                    items.append(GyMLSmartLayoutItem(**item_kwargs))
                body_children.append(
                    GyMLSmartLayout(
                        variant=str(block.get("variant") or "bigBullets"),
                        items=items,
                        start=block.get("start"),
                        decision=block.get("decision"),
                        branches=block.get("branches", []) or [],
                        fallback=block.get("fallback"),
                    )
                )
        elif block_type == "image":
            body_children.append(
                GyMLImage(
                    src=str(block.get("src") or block.get("imagePrompt") or ""),
                    alt=str(block.get("alt") or slide_title),
                    is_accent=bool(block.get("is_accent", False)),
                )
            )
        else:
            body_children.append(
                GyMLParagraph(
                    text=str(
                        block.get("text") or block.get("description") or slide_title
                    )
                )
            )

    section = GyMLSection(
        id=str(payload.get("title") or "slide").strip().replace(" ", "_"),
        image_layout=image_layout,
        body=GyMLBody(children=body_children),
        slide_density=str(payload.get("slide_density") or "balanced").strip().lower(),
    )
    return section


def _validate_with_existing_validator(
    payload: Dict[str, Any],
) -> Tuple[bool, List[str], List[str]]:
    validator = GyMLValidator()
    result = validator.validate(_slide_to_section(payload))
    return result.is_valid, list(result.errors), list(result.warnings)


# Maximum characters for fallback smart_layout headings (schemas currently define word
# budgets, not character budgets).
_MAX_ITEM_HEADING_LENGTH = 60
_DEFAULT_DESCRIPTION_WORD_LIMITS = _field_word_limits_from_schema(
    "bigBullets", "description", 12, 15
)
_MIN_ITEM_DESCRIPTION_WORDS = _DEFAULT_DESCRIPTION_WORD_LIMITS[0] or 12
_MAX_ITEM_DESCRIPTION_WORDS = _DEFAULT_DESCRIPTION_WORD_LIMITS[1] or 15


def _count_words(text: str) -> int:
    tokens = [t for t in str(text or "").strip().split() if t.strip()]
    return len(tokens)


def _trim_to_word_budget(text: str, max_words: int) -> str:
    cleaned = str(text or "").strip()
    if not cleaned:
        return ""
    words = cleaned.split()
    if len(words) <= max_words:
        return cleaned

    trimmed = " ".join(words[:max_words]).rstrip()
    # Prefer ending at punctuation if we cut mid-thought.
    for punct in (".", ";", ":"):
        idx = trimmed.rfind(punct)
        if idx >= max(0, len(trimmed) - 22):
            trimmed = trimmed[: idx + 1].strip()
            break
    if trimmed and trimmed[-1] not in {".", "!", "?"}:
        trimmed = f"{trimmed}."
    return trimmed
