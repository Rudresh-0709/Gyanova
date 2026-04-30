from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List

try:
    from app.services.node.blocks.shared.schema_loader import load_schema
except ImportError:
    from ...blocks.shared.schema_loader import load_schema  # type: ignore


def _join_limited(values: List[str], max_items: int = 4) -> str:
    cleaned = [str(v).strip() for v in values if str(v).strip()]
    return "; ".join(cleaned[:max_items])


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


def _ensure_sentence(text: str) -> str:
    cleaned = str(text or "").strip()
    if not cleaned:
        return ""
    if cleaned[-1] in {".", "!", "?"}:
        return cleaned
    return f"{cleaned}."


def _schema_fields(item_schema: Dict[str, Any], section: str) -> Dict[str, Any]:
    fields = item_schema.get(section, {})
    return fields if isinstance(fields, dict) else {}


def _format_schema_fields(item_schema: Dict[str, Any]) -> str:
    required_fields = _schema_fields(item_schema, "required_fields")
    optional_fields = _schema_fields(item_schema, "optional_fields")
    lines: List[str] = []

    for label, fields in (("Required", required_fields), ("Optional", optional_fields)):
        if not fields:
            continue
        lines.append(f"{label} item fields:")
        for name, field_schema in fields.items():
            if not isinstance(field_schema, dict):
                lines.append(f"- {name}")
                continue
            field_type = str(field_schema.get("type") or "value")
            description = str(field_schema.get("description") or "").strip()
            example = field_schema.get("example")
            min_words = field_schema.get("min_words")
            max_words = field_schema.get("max_words")
            word_limit = ""
            if min_words is not None and max_words is not None:
                word_limit = f" ({min_words}-{max_words} words)"
            elif min_words is not None:
                word_limit = f" (minimum {min_words} words)"
            elif max_words is not None:
                word_limit = f" (maximum {max_words} words)"
            example_text = (
                f" Example: {json.dumps(example, ensure_ascii=True)}"
                if example is not None
                else ""
            )
            detail = f"{field_type}{word_limit}"
            if description:
                detail = f"{detail} - {description}"
            lines.append(f"- {name}: {detail}.{example_text}")

    return "\n".join(lines) if lines else "No item-level field contract is defined."


def _format_block_schema_fields(block_schema: Dict[str, Any]) -> str:
    if not isinstance(block_schema, dict) or not block_schema:
        return "No block-level field contract is defined."

    lines: List[str] = []
    for name, field_schema in block_schema.items():
        if name in {"type", "variant"}:
            lines.append(f"- {name}: must be {json.dumps(field_schema, ensure_ascii=True)}.")
            continue
        if not isinstance(field_schema, dict):
            lines.append(f"- {name}: {json.dumps(field_schema, ensure_ascii=True)}.")
            continue

        field_type = str(field_schema.get("type") or "value")
        description = str(field_schema.get("description") or "").strip()
        example = field_schema.get("example")
        example_text = (
            f" Example: {json.dumps(example, ensure_ascii=True)}"
            if example is not None
            else ""
        )
        detail = f"{field_type}"
        constraints: List[str] = []
        min_items = field_schema.get("min_items")
        max_items = field_schema.get("max_items")
        if min_items is not None:
            constraints.append(f"min_items={min_items}")
        if max_items is not None:
            constraints.append(f"max_items={max_items}")
        min_length = field_schema.get("min_length")
        max_length = field_schema.get("max_length")
        if min_length is not None:
            constraints.append(f"min_length={min_length}")
        if max_length is not None:
            constraints.append(f"max_length={max_length}")
        if constraints:
            detail = f"{detail} ({', '.join(constraints)})"
        if description:
            detail = f"{detail} - {description}"
        lines.append(f"- {name}: {detail}.{example_text}")

        nested_item_schema = field_schema.get("item_schema")
        if isinstance(nested_item_schema, dict) and nested_item_schema:
            lines.append(f"  {name} item fields:")
            for item_name, item_field_schema in nested_item_schema.items():
                if not isinstance(item_field_schema, dict):
                    lines.append(f"  - {item_name}")
                    continue
                item_type = str(item_field_schema.get("type") or "value")
                item_constraints: List[str] = []
                item_min_length = item_field_schema.get("min_length")
                item_max_length = item_field_schema.get("max_length")
                if item_min_length is not None:
                    item_constraints.append(f"min_length={item_min_length}")
                if item_max_length is not None:
                    item_constraints.append(f"max_length={item_max_length}")
                if item_field_schema.get("optional"):
                    item_constraints.append("optional")
                suffix = (
                    f" ({', '.join(item_constraints)})"
                    if item_constraints
                    else ""
                )
                lines.append(f"  - {item_name}: {item_type}{suffix}.")

    return "\n".join(lines)


def _format_validation_rules(validation_rules: Any) -> str:
    if not isinstance(validation_rules, list) or not validation_rules:
        return "No variant-specific validation rules are defined."
    return "\n".join(
        f"- {str(rule).strip()}" for rule in validation_rules if str(rule).strip()
    )


def _format_word_limit_instruction(item_schema: Dict[str, Any]) -> str:
    rules: List[str] = []
    for fields in (
        _schema_fields(item_schema, "required_fields"),
        _schema_fields(item_schema, "optional_fields"),
    ):
        for name, field_schema in fields.items():
            if not isinstance(field_schema, dict):
                continue
            min_words = field_schema.get("min_words")
            max_words = field_schema.get("max_words")
            if min_words is not None and max_words is not None:
                rules.append(f"`{name}` MUST be {min_words}-{max_words} words")
            elif min_words is not None:
                rules.append(f"`{name}` MUST be at least {min_words} words")
            elif max_words is not None:
                rules.append(f"`{name}` MUST be at most {max_words} words")

    if not rules:
        return (
            "Follow the selected variant schema field descriptions; keep text concise "
            "and specific."
        )
    return "; ".join(rules) + "."


def _schema_requires_field(item_schema: Dict[str, Any], field_name: str) -> bool:
    return field_name in _schema_fields(item_schema, "required_fields")


def _build_slide_output_example(
    selected_block_variant: str,
    prompt_example: Any,
    image_tier: str,
) -> str:
    content_block = (
        prompt_example
        if isinstance(prompt_example, dict) and prompt_example
        else {"type": "smart_layout", "variant": selected_block_variant}
    )
    slide_example: Dict[str, Any] = {
        "title": "string",
        "subtitle": "string or null",
        "intent": "introduce|explain|teach|compare|demo|prove|summarize|narrate|list",
        "layout": "right|left|top|bottom|blank",
        "image_layout": "right|left|top|bottom|blank",
        "contentBlocks": [content_block],
        "primary_block_index": 0,
    }
    if image_tier == "accent":
        slide_example["accentImagePrompt"] = "optional string (only if image_tier=accent)"
    elif image_tier == "hero":
        slide_example["heroImagePrompt"] = "optional string (only if image_tier=hero)"
    else:
        slide_example["accentImagePrompt"] = "optional string (only if image_tier=accent)"
        slide_example["heroImagePrompt"] = "optional string (only if image_tier=hero)"
    return json.dumps(slide_example, ensure_ascii=True, indent=2)


@dataclass
class PromptBuildResult:
    prompt: str
    title: str
    selected_template: str
    designer_blueprint: Dict[str, Any]
    composition_style: str
    image_need: str
    image_tier: str
    selected_block_variant: str
    supported_layouts: List[str]
    smart_layout_variant: str
    slide_density: str


def build_generation_prompt(plan_item: Dict[str, Any]) -> PromptBuildResult:
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

    # Block variant is now set by the designer node - do not re-derive it here
    selected_block_variant = str(
        plan_item.get("selected_block_variant") or "bigBullets"
    ).strip()
    variant_schema = load_schema(selected_block_variant)
    item_schema = (
        variant_schema.get("item_schema", {})
        if isinstance(variant_schema.get("item_schema", {}), dict)
        else {}
    )
    block_schema = (
        variant_schema.get("block_schema", {})
        if isinstance(variant_schema.get("block_schema", {}), dict)
        else {}
    )
    schema_field_contract = _format_schema_fields(item_schema)
    block_field_contract = _format_block_schema_fields(block_schema)
    schema_validation_rules = _format_validation_rules(
        variant_schema.get("validation_rules", [])
    )
    schema_word_instruction = _format_word_limit_instruction(item_schema)
    output_schema_example = _build_slide_output_example(
        selected_block_variant,
        variant_schema.get("prompt_example", {}),
        image_tier,
    )
    block_constraints = plan_item.get("block_constraints") or {}

    item_min = int(block_constraints.get("item_min", 2))
    item_max = int(block_constraints.get("item_max", 6))
    requires_icons = _schema_requires_field(item_schema, "icon_name")
    width_class = str(block_constraints.get("width_class", "normal"))
    supported_layouts = list(block_constraints.get("supported_layouts", ["blank"]))
    layout_variant = str(block_constraints.get("layout_variant", "default"))

    # Clamp estimated_items to block's supported range
    try:
        estimated_items = int(plan_item.get("estimated_items", 4))
        estimated_items = max(item_min, min(item_max, estimated_items))
    except (TypeError, ValueError):
        estimated_items = max(item_min, min(item_max, 4))

    # Keep smart_layout_variant as an alias for backward compat with composition/enforcement helpers
    smart_layout_variant = selected_block_variant

    # selected_template is legacy - keep for fallback helpers that still reference it
    selected_template = str(plan_item.get("selected_template") or "Title with bullets").strip()

    slide_density = str(plan_item.get("slide_density") or "balanced").strip().lower()

    expected_items = str(estimated_items)  # exact count from designer

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

    icon_instruction = (
        " Every item MUST include `icon_name` as required by the selected variant schema."
        if requires_icons else ""
    )

    if selected_block_variant == "branching_path":
        primary_block_instruction = (
            f'You MUST include exactly ONE `"type": "smart_layout"` block '
            f'with `"variant": "branching_path"` as the PRIMARY teaching block '
            f'(primary_block_index). It MUST contain `start`, `decision`, and exactly '
            f'{estimated_items} `branches` (min {item_min}, max {item_max}); do NOT use '
            f'peer `items` for this variant.'
        )
        item_count_label = "Branch count"
    else:
        primary_block_instruction = (
            f'You MUST include exactly ONE `"type": "smart_layout"` block '
            f'with `"variant": "{selected_block_variant}"` as the PRIMARY teaching block '
            f'(primary_block_index). It MUST contain exactly {estimated_items} items '
            f'(min {item_min}, max {item_max}).{icon_instruction}'
        )
        item_count_label = "Item count"

    prompt = f"""You are generating a single GyML slide JSON object for an educational presentation.

HARD RULES (violations will cause rejection):
1. Return ONLY a valid JSON object. No markdown, no explanation.
2. {primary_block_instruction}
3. DO NOT include two smart_layout blocks on the same slide.
4. Max 7 content blocks per slide. Primary block carries 70% of visual weight.
5. Enforce composition_style exactly: {composition_style}.
    - primary_only: PRIMARY BLOCK only (no intro/context/annotation/outro blocks)
    - context_then_primary: context_paragraph → PRIMARY BLOCK
    - primary_then_callout: PRIMARY BLOCK → annotation_paragraph
    - intro_then_primary: intro_paragraph → PRIMARY BLOCK (no annotation/outro/takeaway block)
    NEVER place intro_paragraph and annotation_paragraph/outro_paragraph together on the same slide.
6. Do not include both an accentImagePrompt and block-embedded image prompts.
7. Respect selected_template and image policy (image_need: {image_need}, image_tier: {image_tier}).
8. {schema_word_instruction}
9. Avoid one-line generic text. Prefer specific, explanatory sentences tied to the objective.

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
Selected block variant: {selected_block_variant}
{item_count_label}: exactly {estimated_items} (min {item_min}, max {item_max})
Requires icons: {requires_icons}
Width class: {width_class}
Layout variant: {layout_variant}
Supported image layouts: {supported_layouts}
Composition style: {composition_style}
Slide density: {slide_density}

Designer blueprint (additional context):
{json.dumps(designer_blueprint, ensure_ascii=True)}

SELECTED VARIANT SCHEMA CONTRACT:
Block fields:
{block_field_contract}

Item fields:
{schema_field_contract}

SELECTED VARIANT VALIDATION RULES:
{schema_validation_rules}

SMART LAYOUT VARIANT REFERENCE:
  TIMELINES: timeline, timelineHorizontal, timelineSequential, timelineMilestone, timelineIcon
  CARD GRIDS: cardGrid, cardGridIcon, cardGridSimple, cardGridImage
  RELATIONSHIPS: relationshipMap
  RIBBONS: ribbonFold
  STAT TILES: statsBadgeGrid
  STATS: stats, statsComparison, statsPercentage
  BULLETS: bigBullets, bulletIcon, bulletCheck, bulletCross
  PROCESS STEPS: processSteps, processArrow, processAccordion
  COMPARISONS: comparison, comparisonProsCons, comparisonBeforeAfter

OUTPUT SCHEMA (JSON only):
{output_schema_example}
"""

    return PromptBuildResult(
        prompt=prompt,
        title=title,
        selected_template=selected_template,
        designer_blueprint=designer_blueprint,
        composition_style=composition_style,
        image_need=image_need,
        image_tier=image_tier,
        selected_block_variant=selected_block_variant,
        supported_layouts=supported_layouts,
        smart_layout_variant=smart_layout_variant,
        slide_density=slide_density,
    )
