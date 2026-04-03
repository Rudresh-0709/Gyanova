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

    family = str(primary.get("family") or plan_item.get("primary_family") or "smart_layout").strip().lower()

    # Build content-rich primary block based on planned family
    must_cover = [str(v).strip() for v in plan_item.get("must_cover", []) if str(v).strip()]
    key_facts = [str(v).strip() for v in plan_item.get("key_facts", []) if str(v).strip()]
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
                "description": must_cover[0] if must_cover else "Start with the core idea.",
                "imagePrompt": _build_image_prompt(plan_item) or f"Instructional process image for {title}",
                "color": "#4B5563",
            },
            {
                "label": "Step 2",
                "description": must_cover[1] if len(must_cover) > 1 else "Show how the idea develops.",
                "imagePrompt": _build_image_prompt(plan_item) or f"Instructional process image for {title}",
                "color": "#2563EB",
            },
            {
                "label": "Step 3",
                "description": must_cover[2] if len(must_cover) > 2 else "Close with the outcome.",
                "imagePrompt": _build_image_prompt(plan_item) or f"Instructional process image for {title}",
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
        items_recap.append({"title": "Check", "description": str(plan_item.get("assessment_prompt") or "Explain it back in your own words.")})
        content_blocks.append({"type": "numbered_list", "items": items_recap})
    else:
        # Default: rich smart_layout with the planned variant
        sl_items = []
        all_points = must_cover[:4] + key_facts[:2]
        if all_points:
            for i, point in enumerate(all_points[:4]):
                sl_items.append({"heading": f"Point {i + 1}", "description": point})
        else:
            sl_items = [
                {"heading": "Core idea", "description": objective or "Teach the concept clearly."},
                {"heading": "Must cover", "description": _join_limited(must_cover, max_items=3) or "Key supporting points."},
                {"heading": "Why it matters", "description": str(plan_item.get("assessment_prompt") or "Ask the learner to apply the idea.")},
            ]
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


# Block types that count as structured primary blocks (non-trivial teaching content)
_STRUCTURED_PRIMARY_TYPES = {
    "smart_layout",
    "comparison_table",
    "key_value_list",
    "numbered_list",
    "formula_block",
    "process_arrow_block",
    "cyclic_process_block",
    "step_list",
    "rich_text",
}

# Block types that are only acceptable as *supporting* blocks (never primary)
_SUPPORTING_ONLY_TYPES = {"heading", "paragraph", "intro_paragraph", "context_paragraph", "annotation_paragraph", "outro_paragraph", "caption", "image"}

# Maximum characters for a smart_layout item heading (keeps cards readable at typical font sizes)
_MAX_ITEM_HEADING_LENGTH = 60


def _has_structured_primary(blocks: List[Dict[str, Any]]) -> bool:
    """Return True if any block in the list qualifies as a structured primary block."""
    return any(str(b.get("type") or "").strip().lower() in _STRUCTURED_PRIMARY_TYPES for b in blocks if isinstance(b, dict))


def _enforce_structured_primary(payload: Dict[str, Any], plan_item: Dict[str, Any], smart_layout_variant: str) -> None:
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
    selected_template = str(payload.get("selected_template") or plan_item.get("selected_template") or "").strip()
    sparse_templates = {"Title card", "Formula block", "Large bullet list"}
    if selected_template in sparse_templates:
        return

    if _has_structured_primary(blocks):
        return

    # Build a minimal smart_layout block from plan_item content
    title = str(plan_item.get("title") or "The Topic").strip()
    objective = str(plan_item.get("objective") or "").strip()
    must_cover = [str(v).strip() for v in plan_item.get("must_cover", []) if str(v).strip()]
    key_facts = [str(v).strip() for v in plan_item.get("key_facts", []) if str(v).strip()]

    items = []
    # Use must_cover points as items
    for point in (must_cover + key_facts)[:6]:
        items.append({"heading": point[:_MAX_ITEM_HEADING_LENGTH], "description": point})
    # Ensure at least 2 items
    if len(items) < 2:
        items = [
            {"heading": "Key Concept", "description": objective or title},
            {"heading": "Why It Matters", "description": str(plan_item.get("assessment_prompt") or "Reflect on what you learned.")},
        ]

    fallback_block: Dict[str, Any] = {
        "type": "smart_layout",
        "variant": smart_layout_variant or "bigBullets",
        "items": items[:6],
    }

    # Insert after the first heading/paragraph block (or at position 1)
    insert_at = 1
    for i, block in enumerate(blocks):
        if isinstance(block, dict) and str(block.get("type") or "").strip().lower() not in _SUPPORTING_ONLY_TYPES:
            break
        insert_at = i + 1

    blocks.insert(insert_at, fallback_block)
    payload["contentBlocks"] = blocks
    # Update primary_block_index to point to the injected block
    payload["primary_block_index"] = insert_at


def generate_gyml_v2(plan_item: Dict[str, Any]) -> Dict[str, Any]:
    title = str(plan_item.get("title") or "Untitled Slide").strip()
    selected_template = str(plan_item.get("selected_template") or "Title with bullets").strip()
    designer_blueprint = plan_item.get("designer_blueprint", {}) if isinstance(plan_item.get("designer_blueprint"), dict) else {}
    image_need = str(plan_item.get("image_need") or "optional").strip().lower()
    image_tier = str(plan_item.get("image_tier") or "accent").strip().lower()

    # ── Planned primary block info ───────────────────────────────────────────
    primary_family = str(plan_item.get("primary_family") or designer_blueprint.get("primary_family") or "smart_layout").strip().lower()
    primary_variant = str(plan_item.get("primary_variant") or designer_blueprint.get("primary_variant") or "bigBullets").strip()
    smart_layout_variant = str(plan_item.get("smart_layout_variant") or designer_blueprint.get("smart_layout_variant") or "bigBullets").strip()
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
    research_context = str(plan_item.get("research_context") or plan_item.get("research_raw_text") or "").strip()
    factual_confidence = str(plan_item.get("factual_confidence") or "low").strip().lower()

    if research_context:
        grounding_instruction = (
            f"RESEARCH CONTEXT (use this as primary source for facts, dates, and names):\n{research_context[:800]}\n"
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
    elif primary_family == "formula":
        primary_block_instruction = (
            'You MUST include exactly ONE `"type": "formula_block"` block as the PRIMARY teaching block.'
        )
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
            f'You MUST include exactly ONE structured primary teaching block '
            f'(smart_layout variant "{smart_layout_variant}" is strongly preferred). '
            f"It MUST contain {expected_items} items."
        )

    prompt = f"""You are generating a single GyML slide JSON object for an educational presentation.

HARD RULES (violations will cause rejection):
1. Return ONLY a valid JSON object. No markdown, no explanation.
2. {primary_block_instruction}
3. DO NOT include two smart_layout blocks on the same slide.
4. Max 7 content blocks per slide. Primary block carries 70% of visual weight.
5. Content ordering: [optional intro_paragraph] → PRIMARY BLOCK → [optional callout/annotation_paragraph].
6. Do not include both an accentImagePrompt and block-embedded image prompts.
7. Respect selected_template and image policy (image_need: {image_need}, image_tier: {image_tier}).

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
Slide density: {slide_density}
Expected items in primary block: {expected_items}

Designer blueprint (additional context):
{json.dumps(designer_blueprint, ensure_ascii=True)}

SMART LAYOUT VARIANT REFERENCE:
  TIMELINES: timeline, timelineHorizontal, timelineSequential, timelineMilestone, timelineIcon
  CARD GRIDS: cardGrid, cardGridIcon, cardGridSimple, cardGridImage
  STATS: stats, statsComparison, statsPercentage
  BULLETS: bigBullets, bulletIcon, bulletCheck, bulletCross
  PROCESS STEPS: processSteps, processArrow, processAccordion
  COMPARISONS: comparison, comparisonProsCons, comparisonBeforeAfter

OUTPUT SCHEMA (JSON only):
{{
  "title": "string",
  "subtitle": "string or null",
  "intent": "introduce|explain|teach|compare|demo|prove|summarize|narrate|list",
  "layout": "right|left|top|bottom|blank",
  "image_layout": "right|left|top|bottom|blank",
  "contentBlocks": [
    {{
      "type": "smart_layout",
      "variant": "{smart_layout_variant}",
      "items": [
        {{"heading": "...", "description": "...", "icon_name": "ri-...(optional)"}}
      ]
    }}
  ],
  "primary_block_index": 0,
  "accentImagePrompt": "optional string (only if image_tier=accent)",
  "heroImagePrompt": "optional string (only if image_tier=hero)"
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

    # Enforce: non-title slides must have a structured primary block.
    # If the LLM only produced paragraphs/headings, inject a fallback smart_layout.
    _enforce_structured_primary(payload, plan_item, smart_layout_variant)

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
    return payload
