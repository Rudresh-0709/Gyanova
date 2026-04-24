from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any, Dict, List, Optional, Tuple

try:
    from app.services.llm.model_loader import load_openai
except ImportError:
    from ...llm.model_loader import load_openai  # type: ignore

try:
    from app.services.node.slides.gyml.definitions import (
        GyMLBody,
        GyMLComparisonTable,
        GyMLCyclicProcessBlock,
        GyMLCyclicProcessItem,
        GyMLFormulaBlock,
        GyMLHeading,
        GyMLImage,
        GyMLIcon,
        GyMLKeyValueItem,
        GyMLKeyValueList,
        GyMLNumberedList,
        GyMLNumberedListItem,
        GyMLParagraph,
        GyMLProcessArrowBlock,
        GyMLProcessArrowItem,
        GyMLRichText,
        GyMLSection,
        GyMLSmartLayout,
        GyMLSmartLayoutItem,
        GyMLNode,
        GyMLColumns,
        GyMLColumnDiv,
        GyMLSplitPanel,
        GyMLPanel,
        GyMLDiagramLabel,
        GyMLLabeledDiagram,
        GyMLHierarchyTree,
        GyMLTreeNode,
        GyMLFeatureShowcaseBlock,
        GyMLFeatureShowcaseItem,
        GyMLHubAndSpoke,
        GyMLHubAndSpokeItem,
        GyMLCyclicBlock,
        GyMLCyclicItem,
        GyMLSequentialOutput,
    )
    from app.services.node.slides.gyml.validator import GyMLValidator
except ImportError:
    from ..slides.gyml.definitions import (  # type: ignore
        GyMLBody,
        GyMLComparisonTable,
        GyMLCyclicProcessBlock,
        GyMLCyclicProcessItem,
        GyMLFormulaBlock,
        GyMLHeading,
        GyMLImage,
        GyMLIcon,
        GyMLKeyValueItem,
        GyMLKeyValueList,
        GyMLNumberedList,
        GyMLNumberedListItem,
        GyMLParagraph,
        GyMLProcessArrowBlock,
        GyMLProcessArrowItem,
        GyMLRichText,
        GyMLSection,
        GyMLSmartLayout,
        GyMLSmartLayoutItem,
        GyMLNode,
        GyMLColumns,
        GyMLColumnDiv,
        GyMLSplitPanel,
        GyMLPanel,
        GyMLDiagramLabel,
        GyMLLabeledDiagram,
        GyMLHierarchyTree,
        GyMLTreeNode,
        GyMLFeatureShowcaseBlock,
        GyMLFeatureShowcaseItem,
        GyMLHubAndSpoke,
        GyMLHubAndSpokeItem,
        GyMLCyclicBlock,
        GyMLCyclicItem,
        GyMLSequentialOutput,
    )
    from ..slides.gyml.validator import GyMLValidator  # type: ignore


def _clean_json(raw: str) -> str:
    return raw.replace("```json", "").replace("```", "").strip()


def _safe_json_loads(raw: str) -> Optional[Dict[str, Any]]:
    if not raw:
        return None
    try:
        return json.loads(_clean_json(raw))
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Canonical camelCase variant names.  The LLM sometimes emits these in
# lowercase ("solidboxeswithiconsinside") which breaks downstream CSS
# attribute selectors and the _slide_to_section router that both rely on
# exact case matching.
# Build a lookup: lowered_name -> officialCamelCase
# ---------------------------------------------------------------------------
_CANONICAL_VARIANTS: List[str] = [
    "solidBoxesWithIconsInside",
    "timeline",
    "processSteps",
    "comparison",
    "stats",
    "bigBullets",
    "cardGrid",
    "comparisonCards",
    "processAccordion",
    "hubAndSpoke",
    "relationshipMap",
    "ribbonFold",
    "statsBadgeGrid",
    "diamondRibbon",
    "diamondGrid",
    "diamondHub",
    "featureShowcase",
    "cyclicBlock",
    "sequentialOutput",
    "sequentialSteps",
    "bulletIcon",
    "bulletCheck",
    "bulletCross",
    "timelineIcon",
    "timelineHorizontal",
    "timelineSequential",
    "timelineMilestone",
    "cardGridIcon",
    "cardGridSimple",
    "cardGridImage",
    "cardGridDiamond",
    "processArrow",
    "comparisonProsCons",
    "comparisonBeforeAfter",
    "statsComparison",
    "statsPercentage",
    "quote",
    "quoteTestimonial",
    "quoteCitation",
    "definition",
    "knowledgeWeb",
]

_VARIANT_LOOKUP: Dict[str, str] = {v.lower(): v for v in _CANONICAL_VARIANTS}


def _normalize_variant(raw: Optional[str]) -> str:
    """Return the canonical camelCase variant name for any casing the LLM
    might produce.  Falls back to the raw string unchanged if no match is
    found (the validator will still warn about truly unknown variants)."""
    if not raw:
        return "bigBullets"
    cleaned = str(raw).strip()
    return _VARIANT_LOOKUP.get(cleaned.lower(), cleaned)


def _get_block_item_schema(variant: str) -> str:
    """Get the representative JSON schema for a smart_layout item based on its variant."""
    v = str(variant).lower()
    if "stats" in v:
        # Stats variants use value/label
        return '{"value": "50%", "label": "Accuracy Rating"}'
    if "timeline" in v:
        # Timeline variants use year/description
        return '{"year": "1994", "description": "Detailed event description"}'
    if "numberedlist" in v or "step" in v:
        # Numbered lists use title/description
        return '{"title": "Step Name", "description": "What to do in this step."}'

    # Check if variant typically supports icons (standard across gyanova)
    icon_variants = {
        "bigbullets",
        "cardgridicon",
        "cardgriddiamond",
        "relationshipmap",
        "ribbonfold",
        "diamondribbon",
        "diamondgrid",
        "diamondhub",
        "hubandspoke",
        "cyclicblock",
        "bulleticon",
        "timelineicon",
        "solidboxeswithiconsinside",
        "processaccordion",
    }

    if any(iv in v for iv in icon_variants):
        return '{"heading": "Item Title", "description": "Self-contained teaching point.", "icon_name": "ri-lightbulb-line"}'

    return '{"heading": "Item Title", "description": "Self-contained teaching point."}'


def _get_primary_block_schema(family: str, variant: str, expected_items: int) -> str:
    """Construct a sample JSON schema snippet for the primary block based on its family/variant."""
    family = str(family).strip().lower()
    variant = str(variant).strip().lower()

    if family == "formula":
        return (
            "{\n"
            '      "type": "formula_block",\n'
            '      "expression": "E = mc^2",\n'
            '      "variables": [{"name": "E", "definition": "Energy"}, {"name": "m", "definition": "Mass"}],\n'
            '      "example": "Calculating energy from 1kg of mass."\n'
            "    }"
        )

    if family == "comparison_table" or (
        family == "comparison" and "smart_layout" not in variant
    ):
        return (
            "{\n"
            '      "type": "comparison_table",\n'
            '      "headers": ["Feature", "Option A", "Option B"],\n'
            f'      "rows": [["Performance", "High", "Low"]],  // Exactly {expected_items} rows\n'
            '      "caption": "Comparison of A and B"\n'
            "    }"
        )

    if family == "hub_and_spoke" or variant == "hubAndSpoke":
        return (
            "{\n"
            '      "type": "hub_and_spoke",\n'
            '      "hub_label": "The Core Concept",\n'
            f'      "items": [{{"label": "Satellite Point", "description": "...", "icon_name": "ri-..."}}]  // {expected_items} items\n'
            "    }"
        )

    if family == "feature_showcase_block" or variant == "featureShowcase":
        return (
            "{\n"
            '      "type": "feature_showcase_block",\n'
            '      "title": "Central Feature Name",\n'
            f'      "items": [{{"label": "Feature Item", "description": "...", "icon_name": "ri-..."}}]  // {expected_items} items\n'
            "    }"
        )

    if family == "key_value_list":
        return (
            "{\n"
            '      "type": "key_value_list",\n'
            f'      "items": [{{"key": "Term", "value": "Definition"}}]  // {expected_items} items\n'
            "    }"
        )

    if family == "sequential_output" or variant == "sequentialOutput":
        return (
            "{\n"
            '      "type": "sequential_output",\n'
            f'      "items": ["First output string", "Second output string"]  // {expected_items} items\n'
            "    }"
        )

    # Default to smart_layout
    item_schema = _get_block_item_schema(variant)
    return (
        "{\n"
        '      "type": "smart_layout",\n'
        f'      "variant": "{variant}",\n'
        f'      "items": [{item_schema}]  // Repeat this item structure exactly {expected_items} times\n'
        "    }"
    )


def _join_limited(values: List[str], max_items: int = 4) -> str:
    cleaned = [str(v).strip() for v in values if str(v).strip()]
    return "; ".join(cleaned[:max_items])


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


def _intent_for_teacher(teacher_intent: str) -> str:
    intent = str(teacher_intent or "explain").strip().lower()
    return (
        intent
        if intent
        in {
            "introduce",
            "explain",
            "teach",
            "compare",
            "demo",
            "prove",
            "summarize",
            "narrate",
            "list",
        }
        else "explain"
    )


def _build_narration_text(
    plan_item: Dict[str, Any], slide_payload: Dict[str, Any]
) -> str:
    title = str(
        plan_item.get("title") or slide_payload.get("title") or "This slide"
    ).strip()
    must_cover = _join_limited(plan_item.get("must_cover", []), max_items=4)
    key_facts = _join_limited(plan_item.get("key_facts", []), max_items=3)
    formulas = _join_limited(plan_item.get("formulas", []), max_items=2)
    assessment = str(plan_item.get("assessment_prompt") or "").strip()

    parts = [
        f"This slide focuses on {title}.",
    ]
    if must_cover:
        parts.append(f"We will cover {must_cover}.")
    if key_facts:
        parts.append(f"Key facts to remember are {key_facts}.")
    if formulas:
        parts.append(f"Use these formulas where relevant: {formulas}.")
    if assessment:
        parts.append(f"Check understanding by asking: {assessment}.")
    parts.append(
        "Keep the explanation concise, accurate, and connected to the learner's objective."
    )

    sentences = [segment.strip() for segment in parts if segment.strip()]
    return "\n\n".join(sentences)


def _build_image_prompt(plan_item: Dict[str, Any]) -> str:
    title = str(plan_item.get("title") or "the topic").strip()
    objective = str(plan_item.get("objective") or "teach the concept clearly").strip()
    tier = str(plan_item.get("image_tier") or "none").strip().lower()

    # Negative indexing: focus on symbolic representation to avoid letters/labels
    style_suffix = " No text, no words, no letters, no labels, purely visual symbolic illustration, premium artistic composition."

    if tier == "hero":
        return f"High-end editorial hero image for {title}, visually explaining {objective}.{style_suffix}"
    if tier == "accent":
        return f"Accent illustration for {title}, supporting {objective}.{style_suffix}"
    return ""


def _normalize_layout(layout: str) -> str:
    value = str(layout or "blank").strip().lower()
    if value not in {"right", "left", "top", "bottom", "blank"}:
        return "blank"
    return value


_COMPOSITION_STYLES = (
    "primary_only",
    "context_then_primary",
    "primary_then_callout",
    "intro_then_primary",
)


def _resolve_composition_style(
    plan_item: Dict[str, Any], designer_blueprint: Dict[str, Any]
) -> str:
    raw_style = (
        str(
            plan_item.get("composition_style")
            or designer_blueprint.get("composition_style")
            or ""
        )
        .strip()
        .lower()
    )
    if raw_style in _COMPOSITION_STYLES:
        return raw_style

    # Deterministic fallback for legacy plan items that do not set composition_style.
    seq_idx = plan_item.get("sequence_index")
    try:
        seq_num = int(seq_idx)
    except Exception:
        seq_num = 0
    return _COMPOSITION_STYLES[seq_num % len(_COMPOSITION_STYLES)]


def _find_primary_block_index(blocks: List[Dict[str, Any]]) -> int:
    for i, block in enumerate(blocks):
        if not isinstance(block, dict):
            continue
        block_type = str(block.get("type") or "").strip().lower()
        if block_type in _STRUCTURED_PRIMARY_TYPES:
            return i
    return -1


def _ensure_sentence(text: str) -> str:
    cleaned = str(text or "").strip()
    if not cleaned:
        return ""
    if cleaned[-1] in {".", "!", "?"}:
        return cleaned
    return f"{cleaned}."


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
    """Build a mentor-like intro sentence that bridges the slide title to the content."""
    title = str(plan_item.get("title") or "this topic").strip()
    objective = str(plan_item.get("objective") or "").strip()
    teaching_intent = str(plan_item.get("teaching_intent") or "").strip().lower()

    if teaching_intent in ("introduce", "narrate") and objective:
        return _ensure_sentence(f"To understand {title}, it helps to first ask: {objective}")
    if teaching_intent in ("teach", "demo") and objective:
        return _ensure_sentence(f"Here is how {title} actually works in practice: {objective}")
    if teaching_intent == "compare" and objective:
        return _ensure_sentence(f"Let's look at both sides of {title} — {objective}")
    if objective:
        return _ensure_sentence(f"This slide unpacks {title}. {objective}")
    return _ensure_sentence(f"Let's break down {title} step by step.")


def _build_context_text(plan_item: Dict[str, Any]) -> str:
    """Build a natural context bridge using a key fact as an analogy anchor."""
    title = str(plan_item.get("title") or "this topic").strip()
    best_fact = _pick_best_supporting_fact(plan_item)
    objective = str(plan_item.get("objective") or "").strip()

    if best_fact:
        return _ensure_sentence(
            f"To make sense of {title}, remember that {best_fact.rstrip('.')}."
        )
    if objective:
        return _ensure_sentence(f"Before the details, here is the big picture: {objective}")
    return _ensure_sentence(f"Here is the foundational idea behind {title}.")


def _build_callout_text(plan_item: Dict[str, Any]) -> str:
    """Build a concise, conversational key-takeaway sentence."""
    best_fact = _pick_best_supporting_fact(plan_item)
    assessment = str(plan_item.get("assessment_prompt") or "").strip()
    title = str(plan_item.get("title") or "this topic").strip()

    if best_fact:
        return _ensure_sentence(f"The key insight here is that {best_fact.rstrip('.')}. Keep this in mind as you move forward.")
    if assessment:
        return _ensure_sentence(f"Pause and reflect — {assessment}")
    return _ensure_sentence(f"The most important takeaway from {title} is the pattern it reveals.")


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
    """Enforce composition style while preserving high-quality LLM-generated paragraphs.

    Strategy:
    1. Every slide gets an intro_paragraph before the primary block (always).
    2. For styles that add a post-primary block (callout/context after), we:
       - Prefer the LLM's block if it exists and is non-empty.
       - Fall back to our mentor-tone builder only if the LLM omitted it.
    3. For primary_only, we strip all paragraph blocks.
    """
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

    # ── Separate paragraph blocks from structured blocks ────────────────────
    llm_paragraphs: Dict[str, Dict[str, Any]] = {}
    structured_blocks: List[Dict[str, Any]] = []

    for block in blocks:
        if not isinstance(block, dict):
            continue
        block_type = str(block.get("type") or "").strip().lower()
        text_content = str(block.get("text") or "").strip()
        if block_type in paragraph_like:
            # Keep the LLM's paragraph if it has meaningful content (>8 words)
            if text_content and len(text_content.split()) > 8:
                llm_paragraphs[block_type] = block
        else:
            structured_blocks.append(block)

    primary_idx = _find_primary_block_index(structured_blocks)
    if primary_idx < 0:
        payload["contentBlocks"] = structured_blocks
        return

    # ── Primary-only: strip all paragraph blocks and return early ───────────
    if composition_style == "primary_only":
        payload["contentBlocks"] = structured_blocks
        payload["primary_block_index"] = primary_idx
        return

    # ── Always inject an intro_paragraph before the primary block ───────────
    # Prefer what the LLM wrote; fall back to our mentor-tone builder.
    intro_block = (
        llm_paragraphs.get("intro_paragraph")
        or llm_paragraphs.get("paragraph")
        or {"type": "intro_paragraph", "text": _build_intro_text(plan_item)}
    )
    if intro_block.get("type") != "intro_paragraph":
        intro_block = {"type": "intro_paragraph", "text": intro_block.get("text", _build_intro_text(plan_item))}

    # ── Build optional post-primary block based on composition style ────────
    after_primary: List[Dict[str, Any]] = []

    if composition_style == "context_then_primary":
        # context_then_primary uses context_paragraph as the "before" block;
        # we already handle the "before" with intro, so add context as "after" callout.
        context_block = llm_paragraphs.get("context_paragraph")
        if not context_block:
            context_block = {"type": "context_paragraph", "text": _build_context_text(plan_item)}
        after_primary.append(context_block)

    elif composition_style == "primary_then_callout":
        callout_block = llm_paragraphs.get("annotation_paragraph")
        if not callout_block:
            callout_block = {"type": "annotation_paragraph", "text": _build_callout_text(plan_item)}
        after_primary.append(callout_block)

    # ── Reassemble: [other before] + [intro] + [primary] + [after] + [rest] ─
    rebuilt: List[Dict[str, Any]] = []
    rebuilt.extend(structured_blocks[:primary_idx])
    rebuilt.append(intro_block)
    rebuilt.append(structured_blocks[primary_idx])
    rebuilt.extend(after_primary)
    rebuilt.extend(structured_blocks[primary_idx + 1:])

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


def _build_fallback_slide(plan_item: Dict[str, Any]) -> Dict[str, Any]:
    title = str(plan_item.get("title") or "Untitled Slide").strip()
    intent = _intent_for_teacher(plan_item.get("teaching_intent", "explain"))
    template = str(plan_item.get("selected_template") or "Title with bullets").strip()
    designer_blueprint = (
        plan_item.get("designer_blueprint", {})
        if isinstance(plan_item.get("designer_blueprint"), dict)
        else {}
    )
    primary = (
        designer_blueprint.get("primary_block", {})
        if isinstance(designer_blueprint.get("primary_block"), dict)
        else {}
    )
    supporting_blocks = (
        designer_blueprint.get("supporting_blocks", [])
        if isinstance(designer_blueprint.get("supporting_blocks"), list)
        else []
    )
    image_need = str(plan_item.get("image_need") or "optional").strip().lower()
    image_tier = str(plan_item.get("image_tier") or "accent").strip().lower()
    layout = _normalize_layout(
        plan_item.get("selected_layout") or designer_blueprint.get("layout") or "blank"
    )

    # Resolve the intended smart_layout variant from plan
    smart_layout_variant = (
        str(plan_item.get("smart_layout_variant") or "")
        or str(designer_blueprint.get("smart_layout_variant") or "")
        or "bigBullets"
    ).strip()

    content_blocks: List[Dict[str, Any]] = [
        {
            "type": "heading",
            "level": 1,
            "text": title,
        }
    ]

    family = (
        str(primary.get("family") or plan_item.get("primary_family") or "smart_layout")
        .strip()
        .lower()
    )

    # Build content-rich primary block based on planned family
    must_cover = [
        str(v).strip() for v in plan_item.get("must_cover", []) if str(v).strip()
    ]
    key_facts = [
        str(v).strip() for v in plan_item.get("key_facts", []) if str(v).strip()
    ]
    objective = str(plan_item.get("objective") or "").strip()

    if family == "comparison":
        content_blocks.append(
            {
                "type": "comparison_table",
                "headers": ["Idea", "Meaning", "Use"],
                "rows": [
                    ["Core concept", "What it is", "Definition"],
                    ["Mechanism", "How it works", "Explanation"],
                    ["Application", "Where it appears", "Example"],
                ],
                "caption": str(
                    plan_item.get("objective") or "Comparison of key dimensions"
                ).strip(),
            }
        )
    elif family == "formula":
        formula_text = (
            _join_limited(plan_item.get("formulas", []), max_items=2) or "y = f(x)"
        )
        content_blocks.append(
            {
                "type": "formula_block",
                "expression": formula_text,
                "variables": [
                    {"name": "x", "meaning": "Input"},
                    {"name": "y", "meaning": "Output"},
                ],
                "example": str(
                    plan_item.get("objective") or "Show how the formula applies."
                ).strip(),
            }
        )
    elif family == "process":
        items = [
            {
                "label": "Step 1",
                "description": (
                    must_cover[0] if must_cover else "Start with the core idea."
                ),
                "description": (
                    f"{must_cover[0]}. Build context first, then connect this step to the objective: {objective}."
                    if must_cover
                    else f"Start with the core idea and explicitly connect it to the objective: {objective or title}."
                ),
                "color": "#4B5563",
            },
            {
                "label": "Step 2",
                "description": (
                    must_cover[1]
                    if len(must_cover) > 1
                    else "Show how the idea develops."
                ),
                "description": (
                    f"{must_cover[1]}. Explain how this follows from Step 1 and what changes in understanding it produces."
                    if len(must_cover) > 1
                    else "Show how the idea develops, including cause-and-effect and at least one concrete implication."
                ),
                "color": "#2563EB",
            },
            {
                "label": "Step 3",
                "description": (
                    must_cover[2] if len(must_cover) > 2 else "Close with the outcome."
                ),
                "description": (
                    f"{must_cover[2]}. Close with the outcome and a practical takeaway learners can apply immediately."
                    if len(must_cover) > 2
                    else "Close with the outcome, then state the practical takeaway and how to check understanding."
                ),
                "color": "#10B981",
            },
        ]
        content_blocks.append({"type": "process_arrow_block", "items": items})
    elif family == "recap":
        items_recap = []
        if must_cover:
            items_recap.append({"title": "Key idea", "description": must_cover[0]})
        if key_facts:
            items_recap.append({"title": "Key fact", "description": key_facts[0]})
        items_recap.append(
            {
                "title": "Check",
                "description": str(
                    plan_item.get("assessment_prompt")
                    or "Explain it back in your own words."
                ),
            }
        )
        content_blocks.append({"type": "numbered_list", "items": items_recap})
    else:
        # Default: rich smart_layout with the planned variant
        sl_items = []
        all_points = must_cover[:4] + key_facts[:2]
        if all_points:
            for i, point in enumerate(all_points[:4]):
                item = {"heading": f"Point {i + 1}", "description": point}
                if smart_layout_variant == "solidBoxesWithIconsInside":
                    item["icon_name"] = _default_icon_name(i)
                sl_items.append(item)
        else:
            sl_items = [
                {
                    "heading": "Core idea",
                    "description": objective or "Teach the concept clearly.",
                },
                {
                    "heading": "Must cover",
                    "description": _join_limited(must_cover, max_items=3)
                    or "Key supporting points.",
                },
                {
                    "heading": "Why it matters",
                    "description": str(
                        plan_item.get("assessment_prompt")
                        or "Ask the learner to apply the idea."
                    ),
                },
            ]
            if smart_layout_variant == "solidBoxesWithIconsInside":
                for idx, item in enumerate(sl_items):
                    item["icon_name"] = _default_icon_name(idx)
        content_blocks.append(
            {
                "type": "smart_layout",
                "variant": smart_layout_variant,
                "items": sl_items,
            }
        )

    for block in supporting_blocks[:2]:
        if not isinstance(block, dict):
            continue
        if block.get("family") == "supporting_image" and image_need != "forbidden":
            continue
        content_blocks.append(
            {
                "type": "paragraph",
                "text": f"{block.get('family', 'supporting')} {block.get('variant', 'normal')} reinforces {title}.",
            }
        )

    payload: Dict[str, Any] = {
        "title": title,
        "subtitle": str(plan_item.get("objective") or "").strip() or None,
        "intent": intent,
        "layout": layout,
        "image_layout": layout,
        "contentBlocks": content_blocks,
        "primary_block_index": 1 if len(content_blocks) > 1 else 0,
        "slide_density": str(plan_item.get("slide_density") or "balanced")
        .strip()
        .lower(),
        "selected_template": template,
        "image_need": image_need,
        "image_tier": image_tier,
    }

    if image_tier == "hero":
        payload["heroImagePrompt"] = _build_image_prompt(plan_item)
    elif image_tier == "accent":
        payload["accentImagePrompt"] = _build_image_prompt(plan_item)

    return payload


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
            variant = _normalize_variant(block.get("variant"))
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
                items = []
                for item in block.get("items", []):
                    if not isinstance(item, dict):
                        continue
                    heading_value = item.get("heading") or item.get("title")
                    item_kwargs = {
                        k: v
                        for k, v in item.items()
                        if k
                        in {
                            "heading",
                            "description",
                            "points",
                            "year",
                            "value",
                            "label",
                        }
                    }
                    if heading_value:
                        item_kwargs["heading"] = str(heading_value)
                    # Accept both v2 (`icon_name`) and legacy (`icon`) keys.
                    icon_name = item.get("icon_name") or item.get("icon")
                    if icon_name:
                        item_kwargs["icon"] = GyMLIcon(alt=str(icon_name))
                    items.append(GyMLSmartLayoutItem(**item_kwargs))
                body_children.append(
                    GyMLSmartLayout(
                        variant=_normalize_variant(block.get("variant")), items=items
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

# Maximum characters for a smart_layout item heading (keeps cards readable at typical font sizes)
_MAX_ITEM_HEADING_LENGTH = 60
# Word budget for smart_layout item descriptions (keeps cards scannable on desktop/mobile)
_MIN_ITEM_DESCRIPTION_WORDS = 12
_MAX_ITEM_DESCRIPTION_WORDS = 15


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
    variant = str(block.get("variant") or "").lower()
    # Stats use 'label' for their text content, most others use 'description'
    content_key = "label" if "stats" in variant else "description"

    items = block.get("items", [])
    if not isinstance(items, list):
        return

    for item in items:
        if not isinstance(item, dict):
            continue
        text_content = str(item.get(content_key) or "").strip()
        if not text_content:
            continue
        if _count_words(text_content) > _MAX_ITEM_DESCRIPTION_WORDS:
            item[content_key] = _trim_to_word_budget(
                text_content, _MAX_ITEM_DESCRIPTION_WORDS
            )


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

    # Check if a template is explicitly title/sparse – those may skip primary block.
    selected_template = str(
        payload.get("selected_template") or plan_item.get("selected_template") or ""
    ).strip()
    sparse_templates = {"Title card", "Formula block", "Large bullet list"}
    if selected_template in sparse_templates:
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


def generate_gyml_v2(plan_item: Dict[str, Any]) -> Dict[str, Any]:
    title = str(plan_item.get("title") or "Untitled Slide").strip()
    selected_template = str(
        plan_item.get("selected_template") or "Title with bullets"
    ).strip()
    designer_blueprint = (
        plan_item.get("designer_blueprint", {})
        if isinstance(plan_item.get("designer_blueprint"), dict)
        else {}
    )
    composition_style = _resolve_composition_style(plan_item, designer_blueprint)
    image_need = str(plan_item.get("image_need") or "optional").strip().lower()
    image_tier = str(plan_item.get("image_tier") or "accent").strip().lower()

    # ── Planned primary block info ───────────────────────────────────────────
    primary_family = (
        str(
            plan_item.get("primary_family")
            or designer_blueprint.get("primary_family")
            or "smart_layout"
        )
        .strip()
        .lower()
    )
    primary_variant = str(
        plan_item.get("primary_variant")
        or designer_blueprint.get("primary_variant")
        or "bigBullets"
    ).strip()
    smart_layout_variant = str(
        plan_item.get("smart_layout_variant")
        or designer_blueprint.get("smart_layout_variant")
        or "bigBullets"
    ).strip()
    slide_density = str(plan_item.get("slide_density") or "balanced").strip().lower()

    # Derive expected item count from density
    density_item_counts = {
        "ultra_sparse": "2–3",
        "sparse": "2–3",
        "balanced": "3–4",
        "standard": "4–5",
        "dense": "5–6",
        "super_dense": "5–6",
    }
    expected_items = density_item_counts.get(slide_density, "3–4")

    # ── Research / grounding context ────────────────────────────────────────
    if smart_layout_variant == "relationshipMap":
        expected_items = "3"
    if smart_layout_variant == "ribbonFold":
        expected_items = "4"
    if smart_layout_variant == "statsBadgeGrid":
        expected_items = "4"

    research_context = str(
        plan_item.get("research_context") or plan_item.get("research_raw_text") or ""
    ).strip()
    factual_confidence = (
        str(plan_item.get("factual_confidence") or "low").strip().lower()
    )

    if research_context:
        grounding_instruction = (
            f"RESEARCH CONTEXT (use this as primary source for facts, dates, and names):\n{research_context[:5000]}\n"
            "When research context is provided: use only the facts, dates, entities, and relationships "
            "stated above. Do NOT invent additional statistics, quotes, or historical claims."
        )
    else:
        grounding_instruction = (
            "No verified research context is available for this slide. "
            "You may use general, well-established knowledge about the topic. "
            "STRICTLY FORBIDDEN: invented statistics, made-up dates, fabricated quotes, "
            "fake source attributions, or hallucinated specifics."
        )

    # ── Determine the primary block type string for the prompt ───────────────
    if primary_family == "smart_layout":
        primary_block_instruction = (
            f'You MUST include exactly ONE `"type": "smart_layout"` block with `"variant": "{smart_layout_variant}"`'
            f" as the PRIMARY teaching block (primary_block_index)."
            f" It MUST contain {expected_items} items."
        )
        if smart_layout_variant == "relationshipMap":
            primary_block_instruction += (
                " Use exactly 3 items arranged as left circle, center circle, and right circle."
                " The first two items MUST include `icon_name` values so the renderer can place"
                " connector icons between the circles."
            )
        if smart_layout_variant == "ribbonFold":
            primary_block_instruction += (
                " Use exactly 4 items as folded vertical ribbons."
                " Each item SHOULD include an `icon_name` so every ribbon shows an icon badge."
            )
        if smart_layout_variant == "statsBadgeGrid":
            primary_block_instruction += (
                " Use exactly 4 compact stat tiles in a 2x2 grid."
                " Each item's heading SHOULD be the headline metric such as a percentage,"
                " and the description should be a short supporting line."
            )
        if smart_layout_variant == "solidBoxesWithIconsInside":
            primary_block_instruction += (
                " Every item MUST include `icon_name` with a valid Remix Icon class"
                " (examples: ri-lightbulb-line, ri-compass-3-line, ri-book-open-line)."
            )
    elif primary_family == "formula":
        primary_block_instruction = 'You MUST include exactly ONE `"type": "formula_block"` block as the PRIMARY teaching block.'
    elif primary_family == "comparison":
        primary_block_instruction = (
            'You MUST include exactly ONE `"type": "comparison_table"` OR a `"type": "smart_layout"` '
            f'block with variant "comparisonProsCons" as the PRIMARY teaching block. It MUST contain {expected_items} items/rows.'
        )
    elif primary_family == "process":
        primary_block_instruction = (
            'You MUST include exactly ONE `"type": "process_arrow_block"` OR a `"type": "smart_layout"` '
            f'block with variant "processSteps" as the PRIMARY teaching block. It MUST contain {expected_items} items.'
        )
    else:
        primary_block_instruction = (
            f"You MUST include exactly ONE structured primary teaching block "
            f'(variant "{smart_layout_variant}" is strongly preferred). '
            f"It MUST contain {expected_items} items/rows."
        )

    # Construct the dynamic schema for the primary block
    primary_block_schema = _get_primary_block_schema(
        primary_family, smart_layout_variant, expected_items
    )

    prompt = f"""You are generating a single GyML slide JSON object for an educational presentation.

HARD RULES (violations will cause rejection):
1. Return ONLY a valid JSON object. No markdown, no explanation.
2. {primary_block_instruction}
3. DO NOT include two smart_layout blocks on the same slide.
4. Max 5 content blocks per slide. Primary block carries 70% of visual weight.
5. EVERY slide MUST include ONE intro_paragraph block placed BEFORE the primary block.
   - Write it as a mentor speaking directly to the student.
   - It must bridge the slide title to the content below — do NOT just repeat the title.
   - Use natural phrasing: "Here's the key to understanding...", "Think of it this way...", "Before we dive in..."
   - Length: 1–2 sentences, 15–30 words.
6. For composition_style "{composition_style}":
    - primary_only: intro_paragraph + PRIMARY BLOCK only (no callout/annotation/outro)
    - context_then_primary: intro_paragraph + PRIMARY BLOCK + context_paragraph (analogy or grounding fact)
    - primary_then_callout: intro_paragraph + PRIMARY BLOCK + annotation_paragraph (key takeaway, conversational)
    - intro_then_primary: intro_paragraph + PRIMARY BLOCK (same as primary_only for extra blocks)
    NEVER place intro_paragraph and annotation_paragraph/outro_paragraph together UNLESS the style is primary_then_callout.
7. Do not include both an accentImagePrompt and block-embedded image prompts.
8. Respect selected_template and image policy (image_need: {image_need}, image_tier: {image_tier}).
9. Description length: each primary block item description MUST be 12–15 words (1 sentence). Keep it specific and meaningful.
10. Avoid generic filler. Every sentence must teach something concrete tied to the slide objective.

{grounding_instruction}

SLIDE CONTENT:
Title: {title}
Teacher objective: {plan_item.get('objective', '')}
Teaching intent: {plan_item.get('teaching_intent', '')}
Coverage scope: {plan_item.get('coverage_scope', '')}
Must cover: {json.dumps(plan_item.get('must_cover', []), ensure_ascii=True)}
Key facts: {json.dumps(plan_item.get('key_facts', []), ensure_ascii=True)}
Formulas: {json.dumps(plan_item.get('formulas', []), ensure_ascii=True)}
Assessment prompt: {plan_item.get('assessment_prompt', '')}

DESIGN PLAN:
Selected template: {selected_template}
Primary block family: {primary_family}
Primary smart_layout variant: {smart_layout_variant}
Composition style: {composition_style}
Slide density: {slide_density}
Expected items in primary block: {expected_items}

Designer blueprint (additional context):
{json.dumps(designer_blueprint, ensure_ascii=True)}

OUTPUT SCHEMA (JSON only):
{{
  "title": "string",
  "subtitle": "string or null",
  "intent": "introduce|explain|teach|compare|demo|prove|summarize|narrate|list",
  "layout": "right|left|top|bottom|blank",
  "image_layout": "right|left|top|bottom|blank",
  "contentBlocks": [
    {{
      "type": "intro_paragraph",
      "text": "A 1–2 sentence mentor-style bridge between the title and the content below."
    }},
    {primary_block_schema},
    {{
      "type": "annotation_paragraph",
      "text": "(Only if composition_style is primary_then_callout) A concise key takeaway in 1 sentence."
    }}
  ],
  "primary_block_index": 1,
  "accentImagePrompt": "optional string (only if image_tier=accent)",
  "heroImagePrompt": "optional string (only if image_tier=hero)"
}}
"""
    # Enforce scannability for the primary block descriptions even if the LLM overshoots.
    # This is intentionally conservative (only trims when exceeding the max word budget).

    payload = None
    try:
        llm = load_openai()
        response = llm.invoke([{"role": "user", "content": prompt}])
        payload = _safe_json_loads(str(response.content or ""))
    except Exception:
        payload = None

    if not isinstance(payload, dict):
        payload = _build_fallback_slide(plan_item)

    payload = _validate_payload(payload)

    # Enforce single-image policy.
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
    planned_layout = (
        str(
            plan_item.get("layout")
            or designer_blueprint.get("layout")
            or payload.get("layout")
            or "blank"
        )
        .strip()
        .lower()
    )
    payload["layout"] = planned_layout
    payload["image_layout"] = planned_layout

    # Enforce: non-title slides must have a structured primary block.
    # If the LLM only produced paragraphs/headings, inject a fallback smart_layout.
    _enforce_structured_primary(payload, plan_item, smart_layout_variant)

    # Enforce composition style and hard exclusion rule for intro+callout coexistence.
    _apply_composition_style(payload, plan_item, composition_style)

    # Keep primary smart_layout descriptions within the scannable word budget.
    _enforce_primary_description_word_budget(payload)

    # Hard rule: solid boxes primary must include at least one supporting paragraph block.
    _enforce_supporting_for_big_boxes(payload, plan_item)

    # Enforce: side-strip supporting text may only appear on blank image layout slides.
    _enforce_side_strip_only_on_blank_layout(payload)

    is_valid, errors, warnings = _validate_with_existing_validator(payload)
    if not is_valid:
        fallback = _build_fallback_slide(plan_item)
        fallback = _validate_payload(fallback)
        payload = fallback
        payload["validation_errors"] = errors
    if warnings:
        payload["validation_warnings"] = warnings

    payload["title"] = title
    payload["selected_template"] = selected_template
    payload["image_need"] = image_need
    payload["image_tier"] = image_tier
    payload["designer_blueprint"] = designer_blueprint
    payload["slide_density"] = slide_density
    payload["composition_style"] = composition_style
    return payload
