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


def _join_limited(values: List[str], max_items: int = 4) -> str:
    cleaned = [str(v).strip() for v in values if str(v).strip()]
    return "; ".join(cleaned[:max_items])


def _intent_for_teacher(teacher_intent: str) -> str:
    intent = str(teacher_intent or "explain").strip().lower()
    return intent if intent in {"introduce", "explain", "teach", "compare", "demo", "prove", "summarize", "narrate", "list"} else "explain"


def _build_narration_text(plan_item: Dict[str, Any], slide_payload: Dict[str, Any]) -> str:
    title = str(plan_item.get("title") or slide_payload.get("title") or "This slide").strip()
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
    parts.append("Keep the explanation concise, accurate, and connected to the learner's objective.")

    sentences = [segment.strip() for segment in parts if segment.strip()]
    return "\n\n".join(sentences)


def _build_image_prompt(plan_item: Dict[str, Any]) -> str:
    title = str(plan_item.get("title") or "the topic").strip()
    objective = str(plan_item.get("objective") or "teach the concept clearly").strip()
    tier = str(plan_item.get("image_tier") or "none").strip().lower()
    if tier == "hero":
        return f"High-end editorial hero image for {title}, visually explaining {objective} with polished, premium composition."
    if tier == "accent":
        return f"Accent illustration for {title}, supporting {objective} with a clean instructional visual."
    return ""


def _normalize_layout(layout: str) -> str:
    value = str(layout or "blank").strip().lower()
    if value not in {"right", "left", "top", "bottom", "blank"}:
        return "blank"
    return value


def _build_fallback_slide(plan_item: Dict[str, Any]) -> Dict[str, Any]:
    title = str(plan_item.get("title") or "Untitled Slide").strip()
    intent = _intent_for_teacher(plan_item.get("teaching_intent", "explain"))
    template = str(plan_item.get("selected_template") or "Title with bullets").strip()
    designer_blueprint = plan_item.get("designer_blueprint", {}) if isinstance(plan_item.get("designer_blueprint"), dict) else {}
    primary = designer_blueprint.get("primary_block", {}) if isinstance(designer_blueprint.get("primary_block"), dict) else {}
    supporting_blocks = designer_blueprint.get("supporting_blocks", []) if isinstance(designer_blueprint.get("supporting_blocks"), list) else []
    image_need = str(plan_item.get("image_need") or "optional").strip().lower()
    image_tier = str(plan_item.get("image_tier") or "accent").strip().lower()
    layout = _normalize_layout(plan_item.get("selected_layout") or designer_blueprint.get("layout") or "blank")

    content_blocks: List[Dict[str, Any]] = [
        {
            "type": "heading",
            "level": 1,
            "text": title,
        }
    ]

    family = str(primary.get("family") or "overview").strip().lower()
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
                "caption": str(plan_item.get("objective") or "Comparison of key dimensions").strip(),
            }
        )
    elif family == "formula":
        formula_text = _join_limited(plan_item.get("formulas", []), max_items=2) or "y = f(x)"
        content_blocks.append(
            {
                "type": "formula_block",
                "expression": formula_text,
                "variables": [
                    {"name": "x", "meaning": "Input"},
                    {"name": "y", "meaning": "Output"},
                ],
                "example": str(plan_item.get("objective") or "Show how the formula applies.").strip(),
            }
        )
    elif family == "process":
        items = [
            {
                "label": "Step 1",
                "description": "Start with the core idea.",
                "imagePrompt": _build_image_prompt(plan_item) or f"Instructional process image for {title}",
                "color": "#4B5563",
            },
            {
                "label": "Step 2",
                "description": "Show how the idea develops.",
                "imagePrompt": _build_image_prompt(plan_item) or f"Instructional process image for {title}",
                "color": "#2563EB",
            },
            {
                "label": "Step 3",
                "description": "Close with the outcome.",
                "imagePrompt": _build_image_prompt(plan_item) or f"Instructional process image for {title}",
                "color": "#10B981",
            },
        ]
        content_blocks.append({"type": "process_arrow_block", "items": items})
    elif family == "recap":
        content_blocks.append(
            {
                "type": "numbered_list",
                "items": [
                    {"title": "Key idea", "description": str(plan_item.get("must_cover", [title])[0])},
                    {"title": "Key fact", "description": str(plan_item.get("key_facts", ["Remember the main idea."])[0])},
                    {"title": "Check", "description": str(plan_item.get("assessment_prompt") or "Explain it back in your own words.")},
                ],
            }
        )
    else:
        content_blocks.append(
            {
                "type": "smart_layout",
                "variant": "bigBullets",
                "items": [
                    {"heading": "Core idea", "description": str(plan_item.get("objective") or "Teach the concept clearly.")},
                    {"heading": "Must cover", "description": _join_limited(plan_item.get("must_cover", []), max_items=3) or "Key supporting points."},
                    {"heading": "Why it matters", "description": str(plan_item.get("assessment_prompt") or "Ask the learner to apply the idea.")},
                ],
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
        "slide_density": str(plan_item.get("slide_density") or "balanced").strip().lower(),
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
    layout = _normalize_layout(payload.get("layout") or payload.get("image_layout") or "blank")
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
                normalized_blocks.append({"type": "smart_layout", "variant": "bigBullets", "items": items})
                continue

        text_value = str(block.get("text") or block.get("description") or block.get("title") or title).strip()
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
        if block_type in {"paragraph", "intro_paragraph", "context_paragraph", "annotation_paragraph", "outro_paragraph", "caption"}:
            body_children.append(GyMLParagraph(text=str(block.get("text") or block.get("description") or "")))
        elif block_type == "comparison_table":
            body_children.append(GyMLComparisonTable(headers=list(block.get("headers", [])), rows=list(block.get("rows", [])), caption=block.get("caption")))
        elif block_type == "key_value_list":
            items = [GyMLKeyValueItem(key=str(item.get("key") or item.get("label") or "Key"), value=str(item.get("value") or item.get("description") or "Value")) for item in block.get("items", []) if isinstance(item, dict)]
            body_children.append(GyMLKeyValueList(items=items))
        elif block_type == "rich_text":
            body_children.append(GyMLRichText(paragraphs=[str(p) for p in block.get("paragraphs", [])]))
        elif block_type == "numbered_list":
            items = [GyMLNumberedListItem(title=str(item.get("title") or item.get("label") or "Item"), description=str(item.get("description") or "")) for item in block.get("items", []) if isinstance(item, dict)]
            body_children.append(GyMLNumberedList(items=items))
        elif block_type == "formula_block":
            variables = []
            for var in block.get("variables", []):
                if isinstance(var, dict):
                    variables.append({"name": str(var.get("name") or "x"), "meaning": str(var.get("meaning") or "")})
            body_children.append(GyMLFormulaBlock(expression=str(block.get("expression") or ""), variables=variables, example=str(block.get("example") or "")))
        elif block_type == "process_arrow_block":
            items = [GyMLProcessArrowItem(label=str(item.get("label") or "Step"), description=str(item.get("description") or ""), imagePrompt=str(item.get("imagePrompt") or ""), color=item.get("color")) for item in block.get("items", []) if isinstance(item, dict)]
            body_children.append(GyMLProcessArrowBlock(items=items))
        elif block_type == "cyclic_process_block":
            items = [GyMLCyclicProcessItem(label=str(item.get("label") or "Step"), description=str(item.get("description") or ""), imagePrompt=str(item.get("imagePrompt") or ""), icon_name=str(item.get("icon_name") or "ri-repeat-line")) for item in block.get("items", []) if isinstance(item, dict)]
            body_children.append(GyMLCyclicProcessBlock(items=items))
        elif block_type == "smart_layout":
            items = [GyMLSmartLayoutItem(**{k: v for k, v in item.items() if k in {"heading", "title", "description", "imagePrompt", "icon_name", "color"}}) for item in block.get("items", []) if isinstance(item, dict)]
            body_children.append(GyMLSmartLayout(variant=str(block.get("variant") or "bigBullets"), items=items))
        elif block_type == "image":
            body_children.append(GyMLImage(src=str(block.get("src") or block.get("imagePrompt") or ""), alt=str(block.get("alt") or slide_title), is_accent=bool(block.get("is_accent", False))))
        else:
            body_children.append(GyMLParagraph(text=str(block.get("text") or block.get("description") or slide_title)))

    section = GyMLSection(
        id=str(payload.get("title") or "slide").strip().replace(" ", "_"),
        image_layout=image_layout,
        body=GyMLBody(children=body_children),
        slide_density=str(payload.get("slide_density") or "balanced").strip().lower(),
    )
    return section


def _validate_with_existing_validator(payload: Dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
    validator = GyMLValidator()
    result = validator.validate(_slide_to_section(payload))
    return result.is_valid, list(result.errors), list(result.warnings)


def generate_gyml_v2(plan_item: Dict[str, Any]) -> Dict[str, Any]:
    title = str(plan_item.get("title") or "Untitled Slide").strip()
    selected_template = str(plan_item.get("selected_template") or "Title with bullets").strip()
    designer_blueprint = plan_item.get("designer_blueprint", {}) if isinstance(plan_item.get("designer_blueprint"), dict) else {}
    image_need = str(plan_item.get("image_need") or "optional").strip().lower()
    image_tier = str(plan_item.get("image_tier") or "accent").strip().lower()

    prompt = f"""
You are generating a single GyML slide JSON object.

Rules:
- Return JSON only.
- Keep content grounded in the teacher data.
- Do not include both accent image and block-embedded content image.
- Respect the selected template and image policy.

Teacher objective: {plan_item.get('objective', '')}
Teaching intent: {plan_item.get('teaching_intent', '')}
Coverage scope: {plan_item.get('coverage_scope', '')}
Must cover: {json.dumps(plan_item.get('must_cover', []), ensure_ascii=True)}
Key facts: {json.dumps(plan_item.get('key_facts', []), ensure_ascii=True)}
Formulas: {json.dumps(plan_item.get('formulas', []), ensure_ascii=True)}
Assessment prompt: {plan_item.get('assessment_prompt', '')}
Research raw text: {plan_item.get('research_raw_text', '')}
Factual confidence: {plan_item.get('factual_confidence', '')}

Designer blueprint:
{json.dumps(designer_blueprint, ensure_ascii=True)}

Selected template: {selected_template}
Image need: {image_need}
Image tier: {image_tier}

Output schema:
{{
  "title": "string",
  "subtitle": "string",
  "intent": "introduce|explain|teach|compare|demo|prove|summarize|narrate|list",
  "layout": "right|left|top|bottom|blank",
  "image_layout": "right|left|top|bottom|blank",
  "contentBlocks": [{{"type": "..."}}],
  "primary_block_index": 0,
  "imagePrompt": "optional",
  "accentImagePrompt": "optional",
  "heroImagePrompt": "optional"
}}
"""

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
    return payload
