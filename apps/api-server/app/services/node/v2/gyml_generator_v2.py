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

from .generation.llm_caller import _clean_json, _safe_json_loads
from .generation.post_processor import (
    _STRUCTURED_PRIMARY_TYPES,
    _SUPPORTING_ONLY_TYPES,
    _apply_composition_style,
    _build_callout_text,
    _build_context_text,
    _build_intro_text,
    _default_icon_name,
    _enforce_primary_description_word_budget,
    _enforce_side_strip_only_on_blank_layout,
    _enforce_structured_primary,
    _enforce_supporting_for_big_boxes,
    _find_primary_block_index,
    _has_structured_primary,
    _pick_best_supporting_fact,
)
from .generation.prompt_builder import (
    _COMPOSITION_STYLES,
    _build_image_prompt,
    _ensure_sentence,
    _intent_for_teacher,
    _join_limited,
    _normalize_layout,
    _resolve_composition_style,
)
from .generation.response_validator import (
    _MAX_ITEM_DESCRIPTION_WORDS,
    _MAX_ITEM_HEADING_LENGTH,
    _MIN_ITEM_DESCRIPTION_WORDS,
    _count_words,
    _slide_to_section,
    _trim_to_word_budget,
    _validate_payload,
    _validate_with_existing_validator,
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
    selected_block_variant = str(plan_item.get("selected_block_variant") or "bigBullets").strip()
    smart_layout_variant = selected_block_variant  # alias for the rest of the function

    content_blocks: List[Dict[str, Any]] = [
        {
            "type": "heading",
            "level": 1,
            "text": title,
        }
    ]

    family = (
        str(plan_item.get("primary_family") or "smart_layout")
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

        if smart_layout_variant == "branching_path":
            branch_source = sl_items[:4]
            if len(branch_source) < 2:
                branch_source = [
                    {
                        "heading": "Recognize",
                        "description": objective or "Choose this route when the condition is met.",
                    },
                    {
                        "heading": "Optimize",
                        "description": str(
                            plan_item.get("assessment_prompt")
                            or "Choose this route when more refinement is needed."
                        ),
                    },
                ]

            branches = []
            for idx, item in enumerate(branch_source[:4]):
                suffix = chr(65 + idx)
                label = str(item.get("heading") or f"Path {suffix}").strip()
                description = str(item.get("description") or "").strip()
                branches.append(
                    {
                        "edge_label": "Yes" if idx == 0 else ("No" if idx == 1 else f"Option {suffix}"),
                        "path_label": label[:30],
                        "path_description": description[:120],
                        "outcome_label": (
                            "Prediction Made" if idx == 0 else ("Retrain" if idx == 1 else f"Outcome {suffix}")
                        ),
                        "outcome_description": (
                            description[:120]
                            or "The learner follows this branch to a clear outcome."
                        ),
                    }
                )

            content_blocks.append(
                {
                    "type": "smart_layout",
                    "variant": "branching_path",
                    "density": "balanced",
                    "start": {
                        "label": "Data Input",
                        "description": objective[:120]
                        or "Raw information enters the decision flow.",
                    },
                    "decision": {
                        "label": "Pattern Found?",
                        "description": "Choose the branch that matches the current condition.",
                    },
                    "branches": branches,
                    "fallback": {
                        "label": "Re-evaluate",
                        "description": "Return to the decision if the result is not reliable.",
                        "style": "dashed",
                    },
                }
            )
        else:
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


def generate_gyml_v2(plan_item: Dict[str, Any]) -> Dict[str, Any]:
    from .generation.generator import generate_gyml_v2 as _generate_gyml_v2

    return _generate_gyml_v2(plan_item)
