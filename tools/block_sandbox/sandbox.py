from __future__ import annotations

import importlib
import inspect
import json
import re
import sys
from dataclasses import dataclass
from html import escape
from pathlib import Path
from typing import Any, Callable

import streamlit as st
import streamlit.components.v1


REPO_ROOT = Path(__file__).resolve().parents[2]
API_ROOT = REPO_ROOT / "apps" / "api-server"
NODE_ROOT = API_ROOT / "app" / "services" / "node"
BLOCKS_ROOT = NODE_ROOT / "blocks"

for path in (API_ROOT, NODE_ROOT):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

from app.services.node.blocks.registry import ALL_BLOCKS
from app.services.node.blocks.shared.base_spec import BlockSpec, DENSITY_ORDER, ItemCountProfile
from app.services.node.blocks.shared.rule_registry import RULE_REGISTRY, RenderingRule
from app.services.node.blocks.shared.styles import get_slide_css
from app.services.node.slides.gyml.definitions import (
    ComposedBlock,
    GyMLBody,
    GyMLImage,
    GyMLSection,
)
from app.services.node.slides.gyml.renderer import GyMLRenderer
from app.services.node.slides.gyml.serializer import GyMLSerializer
from app.services.node.slides.gyml.theme import THEMES, Theme


DENSITIES = DENSITY_ORDER
IMAGE_LAYOUTS = ["blank", "left", "right", "top", "bottom"]
SUPPORTING_BLOCK_VARIANTS = [
    "intro_paragraph",
    "annotation_paragraph",
    "callout",
    "caption",
    "divider",
    "outro_paragraph",
    "rich_text",
    "definition",
    "myth_vs_fact",
    "summary_strip",
]

FAMILY_FOLDER_ALIASES = {
    "comparison_analytical": "comparison",
    "cyclic_feedback": "cyclic_feedback",
}

FAMILY_RENDER_FUNCTIONS = {
    "timeline": "render_timeline",
    "sequential_process": "render_sequential_process",
    "comparison": "render_comparison",
    "comparison_analytical": "render_comparison",
    "stats_quantitative": "render_stats_quantitative",
    "conceptual_relational": "render_conceptual_relational",
    "hierarchical_structural": "render_hierarchical_structural",
    "grid_container": "render_grid_container",
    "supporting_contextual": "render_supporting_contextual",
    "cyclic_feedback": "render_cyclic_feedback",
}

SMART_LAYOUT_VARIANTS = {
    "bigBullets",
    "bulletIcon",
    "cardGridDiamond",
    "cardGridImage",
    "cardGridSimple",
    "diamondGrid",
    "diamondRibbon",
    "ribbonFold",
    "bento_grid",
    "pillar_cards",
    "timeline",
    "timelineHorizontal",
    "timelineIcon",
    "timelineMilestone",
    "processAccordion",
    "processArrow",
    "processSteps",
    "sequentialSteps",
    "branching_path",
    "image_process",
    "input_process_output",
    "comparisonBeforeAfter",
    "comparisonProsCons",
    "ranking_ladder",
    "spectrum_scale",
    "venn_overlap",
    "interlockingArrows",
    "stats",
    "statsComparison",
    "statsPercentage",
    "diamondHub",
    "hubAndSpoke",
    "relationshipMap",
    "cause_effect_web",
    "dependency_chain",
    "ecosystem_map",
    "layer_stack",
    "sequentialOutput",
}

STANDALONE_TYPE_BY_VARIANT = {
    "comparison_table": "comparison_table",
    "split_panel": "split_panel",
    "formula_block": "formula_block",
    "feature_showcase": "feature_showcase_block",
    "hierarchy_tree": "hierarchy_tree",
    "cyclic_process_block": "cyclic_process_block",
    "intro_paragraph": "intro_paragraph",
    "quote": "quote",
    "annotation_paragraph": "annotation_paragraph",
    "callout": "callout",
    "caption": "caption",
    "divider": "divider",
    "image": "image",
    "outro_paragraph": "outro_paragraph",
    "rich_text": "rich_text",
    "definition": "definition",
    "myth_vs_fact": "callout",
    "summary_strip": "rich_text",
}


@dataclass
class SandboxRenderContext:
    variant: str
    density: str
    image_layout: str
    title: str
    item_count: int
    theme: Theme
    animated: bool = False
    _segment_counter: int = 0

    def _escape(self, raw: object) -> str:
        return escape("" if raw is None else str(raw), quote=True)


class FamilyRendererAdapter:
    def __init__(
        self,
        variant: str,
        family: str,
        render_fn: Callable[[str, Any, Any], str] | None,
    ) -> None:
        self.variant = variant
        self.family = family
        self.render_fn = render_fn
        self.fallback_renderer = GyMLRenderer()

    def render(self, layout_node: Any, context: SandboxRenderContext) -> str:
        if self.render_fn and hasattr(layout_node, "items"):
            return self.render_fn(self.variant, layout_node, context)
        if self.render_fn and type(layout_node).__name__ in {
            "GyMLComparisonTable",
            "GyMLSplitPanel",
            "GyMLSequentialOutput",
            "GyMLProcessArrowBlock",
            "GyMLCyclicProcessBlock",
            "GyMLHierarchyTree",
        }:
            return self.render_fn(self.variant, layout_node, context)
        return self.fallback_renderer._render_node(layout_node) or ""


def _family_folder(family: str) -> str:
    return FAMILY_FOLDER_ALIASES.get(family, family)


def _count_options(spec: BlockSpec) -> list[int]:
    options: set[int] = set()
    for profile in spec.item_count_profiles:
        lo, hi = profile.item_range
        options.update(range(lo, hi + 1))
    return sorted(options) or [1]


def _density_options(spec: BlockSpec) -> list[str]:
    start, end = spec.density_range
    if start not in DENSITY_ORDER or end not in DENSITY_ORDER:
        return list(DENSITY_ORDER)
    start_idx = DENSITY_ORDER.index(start)
    end_idx = DENSITY_ORDER.index(end)
    return DENSITY_ORDER[start_idx : end_idx + 1]


def _profiles_for_count(spec: BlockSpec, item_count: int) -> list[ItemCountProfile]:
    return [
        profile
        for profile in spec.item_count_profiles
        if profile.item_range[0] <= item_count <= profile.item_range[1]
    ]


def _active_profile(spec: BlockSpec, item_count: int) -> ItemCountProfile:
    profiles = _profiles_for_count(spec, item_count)
    if profiles:
        return profiles[0]

    # Defensive fallback for malformed specs; the registry should normally prevent this.
    return spec.item_count_profiles[0]


def _layout_options_for_count(spec: BlockSpec, item_count: int) -> list[str]:
    layouts: list[str] = []
    for profile in _profiles_for_count(spec, item_count):
        for layout in profile.supported_layouts:
            if layout not in layouts:
                layouts.append(layout)
    return layouts or list(_active_profile(spec, item_count).supported_layouts) or ["blank"]


def _is_combinable_for_count(spec: BlockSpec, item_count: int) -> bool:
    return any(profile.combinable for profile in _profiles_for_count(spec, item_count))


def _select_index(options: list[Any], preferred: Any, fallback: Any | None = None) -> int:
    if preferred in options:
        return options.index(preferred)
    if fallback in options:
        return options.index(fallback)
    return 0


def _load_family_renderer(variant: str) -> FamilyRendererAdapter:
    spec = ALL_BLOCKS[variant]
    family = spec.family
    folder = _family_folder(family)
    module_name = f"app.services.node.blocks.families.{folder}.renderer"
    fn_name = FAMILY_RENDER_FUNCTIONS.get(family) or FAMILY_RENDER_FUNCTIONS.get(folder)

    render_fn = None
    try:
        module = importlib.import_module(module_name)
        module = importlib.reload(module)
        render_fn = getattr(module, fn_name or "", None)
    except Exception as exc:
        st.warning(f"Could not import family renderer {module_name}: {exc}")

    if render_fn is None and variant == "cyclic_process_block":
        module = importlib.import_module(
            "app.services.node.blocks.families.supporting_contextual.renderer"
        )
        render_fn = getattr(module, "render_supporting_contextual", None)

    return FamilyRendererAdapter(variant=variant, family=family, render_fn=render_fn)


def _reload_sandbox_dependencies() -> None:
    """
    Reload key block/slide modules so renderer/spec/style Python edits appear
    without restarting the Streamlit process.
    """
    module_names = [
        "app.services.node.blocks.registry",
        "app.services.node.blocks.shared.rule_registry",
        "app.services.node.blocks.shared.styles",
        "app.services.node.slides.gyml.renderer",
        "app.services.node.slides.gyml.serializer",
        "app.services.node.slides.gyml.theme",
    ]

    for name in module_names:
        try:
            module = importlib.import_module(name)
            importlib.reload(module)
        except Exception:
            continue

    # Refresh global bindings to the newly reloaded modules.
    global ALL_BLOCKS, RULE_REGISTRY, get_slide_css, GyMLRenderer, GyMLSerializer, THEMES, Theme
    ALL_BLOCKS = importlib.import_module("app.services.node.blocks.registry").ALL_BLOCKS
    RULE_REGISTRY = importlib.import_module("app.services.node.blocks.shared.rule_registry").RULE_REGISTRY
    get_slide_css = importlib.import_module("app.services.node.blocks.shared.styles").get_slide_css
    gyml_renderer_mod = importlib.import_module("app.services.node.slides.gyml.renderer")
    GyMLRenderer = gyml_renderer_mod.GyMLRenderer
    gyml_serializer_mod = importlib.import_module("app.services.node.slides.gyml.serializer")
    GyMLSerializer = gyml_serializer_mod.GyMLSerializer
    gyml_theme_mod = importlib.import_module("app.services.node.slides.gyml.theme")
    THEMES = gyml_theme_mod.THEMES
    Theme = gyml_theme_mod.Theme


def _strip_markdown_fences(raw: str) -> str:
    text = raw.strip()
    fence = re.match(r"^```(?:json)?\s*(.*?)\s*```$", text, flags=re.DOTALL)
    return fence.group(1).strip() if fence else text


def _parse_json_response(response: Any) -> dict[str, Any]:
    raw = getattr(response, "content", response)
    text = _strip_markdown_fences(str(raw or ""))
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise
        parsed = json.loads(text[start : end + 1])
    if not isinstance(parsed, dict):
        raise ValueError("Groq returned JSON, but not a JSON object.")
    return parsed


def _load_prompt_builder() -> Callable[..., str] | None:
    candidates = [
        "app.services.node.generator_slide_planning_node",
        "app.services.node.v2.gyml_generator_v2",
    ]
    for module_name in candidates:
        try:
            module = importlib.import_module(module_name)
        except Exception:
            continue
        builder = getattr(module, "build_generator_prompt", None)
        if callable(builder):
            return builder
    return None


def _call_prompt_builder(
    builder: Callable[..., str] | None,
    *,
    variant: str,
    item_count: int,
    density: str,
    title: str,
) -> str:
    def _with_sandbox_instructions(base_prompt: str) -> str:
        """
        The upstream prompt builder is optimized for slide-fit brevity.
        In the sandbox we often want richer content to stress-test layouts.
        """
        extra = (
            "\n\nSandbox verbosity:\n"
            "- Generate richer content than normal (still slide-friendly).\n"
            "- For each item: heading 3-7 words.\n"
            "- Prefer 2 short sentences for `description` when used.\n"
        )

        # Variant-specific content shape rules (avoid pushing `points` everywhere).
        if variant == "processAccordion":
            return (
                f"{base_prompt}{extra}\n"
                "Additional strict rule for processAccordion:\n"
                "- Each item MUST include a `points` array with 4-6 strings (each 6-14 words).\n"
                "- Use `points` for the accordion body; do not rely on a single-sentence-only `description`.\n"
            )

        if variant == "processSteps":
            return (
                f"{base_prompt}{extra}\n"
                "Additional strict rule for processSteps:\n"
                "- Do NOT use `points`.\n"
                "- Use `description` (prefer 2 short sentences) for the body content.\n"
            )

        return f"{base_prompt}{extra}"

    if builder is None:
        return _with_sandbox_instructions(
            _build_fallback_prompt(variant, item_count, density, title)
        )

    plan_item = _build_plan_item(variant, item_count, density, title)
    signature = inspect.signature(builder)
    params = signature.parameters

    if len(params) == 1:
        return _with_sandbox_instructions(str(builder(plan_item)))

    kwargs: dict[str, Any] = {}
    for name in params:
        if name in {"variant", "selected_variant", "selected_block_variant", "block_variant"}:
            kwargs[name] = variant
        elif name in {"item_count", "estimated_items", "items"}:
            kwargs[name] = item_count
        elif name in {"density", "slide_density"}:
            kwargs[name] = density
        elif name == "title":
            kwargs[name] = title
        elif name in {"plan_item", "plan"}:
            kwargs[name] = plan_item
        elif name in {"designer_blueprint", "blueprint"}:
            kwargs[name] = {"sandbox": True, "selected_block_variant": variant}

    try:
        return _with_sandbox_instructions(str(builder(**kwargs)))
    except TypeError:
        return _with_sandbox_instructions(
            str(builder(variant, item_count, density, title))
        )


def _build_plan_item(
    variant: str,
    item_count: int,
    density: str,
    title: str,
) -> dict[str, Any]:
    spec = ALL_BLOCKS[variant]
    profile = _active_profile(spec, item_count)
    return {
        "title": title,
        "objective": f"Generate a concise educational slide about {title}.",
        "teaching_intent": "explain",
        "coverage_scope": "overview",
        "selected_block_variant": variant,
        "estimated_items": item_count,
        "slide_density": density,
        "image_need": "optional",
        "image_tier": "accent",
        "image_role": "none",
        "selected_template": "Block Sandbox",
        "block_constraints": {
            "item_min": item_count,
            "item_max": item_count,
            "requires_icons": spec.requires_icons,
            "width_class": profile.width_class,
            "supported_layouts": list(profile.supported_layouts),
            "layout_variant": profile.layout_variant,
        },
    }


def _build_fallback_prompt(
    variant: str,
    item_count: int,
    density: str,
    title: str,
) -> str:
    spec = ALL_BLOCKS[variant]
    block_type = _block_type_for_variant(variant)
    icon_rule = (
        "Every item must include icon_name with a valid Remix Icon class."
        if spec.requires_icons
        else "Do not add icon_name unless it is genuinely useful."
    )
    schema_hint = _schema_hint(variant, block_type)

    process_accordion_rule = ""
    if variant == "processAccordion":
        process_accordion_rule = """

ProcessAccordion rule:
- For every item in contentBlocks[0].items, include `points` with 3-4 concise strings.
- Prefer `points` over `description` for accordion body content.
"""

    return f"""You are generating a single GyML slide JSON object for an educational presentation.

Return ONLY valid JSON. No markdown fences, no commentary.

Slide title: {title}
Selected block variant: {variant}
Block type: {block_type}
Item count: exactly {item_count}
Density: {density}
Icon rule: {icon_rule}

Generate specific, classroom-ready content. In this sandbox, be more detailed than usual (still slide-friendly).
{process_accordion_rule}

Use this output shape:
{schema_hint}
"""


def _block_type_for_variant(variant: str) -> str:
    if variant in SMART_LAYOUT_VARIANTS:
        return "smart_layout"
    return STANDALONE_TYPE_BY_VARIANT.get(variant, "smart_layout")


def _schema_hint(variant: str, block_type: str) -> str:
    if block_type == "smart_layout":
        item_schema: dict[str, Any] = {
            "heading": "short heading",
            "description": "two short explanatory sentences",
            "icon_name": "ri-lightbulb-line",
        }
        if variant == "processAccordion":
            item_schema = {
                "heading": "step title",
                "points": [
                    "first concise point",
                    "second concise point",
                    "third concise point",
                    "fourth concise point",
                ],
                "icon_name": "ri-lightbulb-line",
            }
        return json.dumps(
            {
                "title": "string",
                "subtitle": None,
                "intent": "explain",
                "layout": "blank",
                "image_layout": "blank",
                "primary_block_index": 0,
                "contentBlocks": [
                    {
                        "type": "smart_layout",
                        "variant": variant,
                        "items": [
                            item_schema
                        ],
                    }
                ],
            },
            indent=2,
        )
    if block_type == "comparison_table":
        block = {
            "type": "comparison_table",
            "caption": "short caption",
            "headers": ["Dimension", "Option A", "Option B"],
            "rows": [["Dimension", "A detail", "B detail"]],
        }
    elif block_type == "split_panel":
        block = {
            "type": "split_panel",
            "leftPanel": {"title": "Before", "content": "concise panel text"},
            "rightPanel": {"title": "After", "content": "concise panel text"},
        }
    elif block_type == "formula_block":
        block = {
            "type": "formula_block",
            "expression": "E = mc^2",
            "variables": [{"name": "E", "definition": "Energy"}],
            "example": "A concise worked example.",
        }
    elif block_type == "cyclic_process_block":
        block = {
            "type": "cyclic_process_block",
            "items": [{"label": "Step", "description": "concise process text"}],
        }
    elif block_type == "hierarchy_tree":
        block = {
            "type": "hierarchy_tree",
            "root": {
                "label": "Main concept",
                "children": [{"label": "Sub concept", "children": []}],
            },
        }
    elif block_type == "feature_showcase_block":
        block = {
            "type": "feature_showcase_block",
            "title": "Core feature",
            "items": [{"label": "Feature", "description": "concise feature text"}],
        }
    elif block_type == "rich_text":
        block = {
            "type": "rich_text",
            "paragraphs": ["One concise paragraph.", "A second concise paragraph."],
        }
    elif block_type == "definition":
        block = {
            "type": "definition",
            "term": "Key term",
            "definition": "A clear, concise definition.",
        }
    elif block_type == "quote":
        block = {
            "type": "quote",
            "author": "Attribution",
            "text": "A short educational quote or framing sentence.",
        }
    elif block_type == "divider":
        block = {"type": "divider"}
    elif block_type == "image":
        block = {
            "type": "image",
            "src": "placeholder",
            "alt": "Image placeholder",
        }
    else:
        block = {"type": block_type, "text": "A concise supporting sentence."}

    return json.dumps(
        {
            "title": "string",
            "subtitle": None,
            "intent": "explain",
            "layout": "blank",
            "image_layout": "blank",
            "primary_block_index": 0,
            "contentBlocks": [block],
        },
        indent=2,
    )


def _normalize_generated_payload(
    payload: dict[str, Any],
    *,
    variant: str,
    item_count: int,
    density: str,
    title: str,
    image_layout: str,
) -> dict[str, Any]:
    payload = dict(payload)
    payload["title"] = payload.get("title") or title
    payload["layout"] = image_layout
    payload["image_layout"] = image_layout
    payload["primary_block_index"] = int(payload.get("primary_block_index") or 0)
    payload["slide_density"] = density

    blocks = payload.get("contentBlocks")
    if not isinstance(blocks, list) or not blocks:
        blocks = [_fallback_block(variant, item_count)]

    primary_idx = max(0, min(payload["primary_block_index"], len(blocks) - 1))
    primary = blocks[primary_idx] if isinstance(blocks[primary_idx], dict) else {}
    expected_type = _block_type_for_variant(variant)

    if expected_type == "smart_layout":
        primary = dict(primary)
        primary["type"] = "smart_layout"
        primary["variant"] = variant
        items = primary.get("items")
        if not isinstance(items, list) or not items:
            items = _fallback_items(item_count, ALL_BLOCKS[variant].requires_icons)
        primary["items"] = _resize_items(items, item_count, ALL_BLOCKS[variant].requires_icons)
    elif primary.get("type") != expected_type:
        primary = _fallback_block(variant, item_count)

    blocks[primary_idx] = primary
    payload["contentBlocks"] = blocks
    return payload


def _fallback_block(variant: str, item_count: int) -> dict[str, Any]:
    block_type = _block_type_for_variant(variant)
    if block_type == "smart_layout":
        return {
            "type": "smart_layout",
            "variant": variant,
            "items": _fallback_items(item_count, ALL_BLOCKS[variant].requires_icons),
        }
    if block_type == "comparison_table":
        return {
            "type": "comparison_table",
            "caption": "Generated comparison",
            "headers": ["Dimension", "Option A", "Option B"],
            "rows": [
                ["Purpose", "Shows one side clearly", "Contrasts the other side"],
                ["Best use", "Quick explanation", "Decision support"],
            ],
        }
    if block_type == "split_panel":
        return {
            "type": "split_panel",
            "leftPanel": {"title": "Before", "content": "The starting state is simple."},
            "rightPanel": {"title": "After", "content": "The final state is clearer."},
        }
    if block_type == "formula_block":
        return {
            "type": "formula_block",
            "expression": "rate = change / time",
            "variables": [
                {"name": "change", "definition": "Difference between two values"},
                {"name": "time", "definition": "Elapsed duration"},
            ],
            "example": "Use the formula to compare how quickly values move.",
        }
    if block_type == "cyclic_process_block":
        return {
            "type": "cyclic_process_block",
            "items": [
                {"label": f"Phase {i + 1}", "description": "One recurring part of the cycle."}
                for i in range(max(3, min(item_count, 4)))
            ],
        }
    if block_type == "hierarchy_tree":
        return {
            "type": "hierarchy_tree",
            "root": {
                "label": "Core idea",
                "children": [
                    {"label": "Part A", "children": []},
                    {"label": "Part B", "children": []},
                ],
            },
        }
    if block_type == "divider":
        return {"type": "divider"}
    return {"type": block_type, "text": "Generated sandbox content."}


def _supporting_block(variant: str, title: str) -> dict[str, Any]:
    topic = title or "this concept"
    if variant == "intro_paragraph":
        return {
            "type": "intro_paragraph",
            "text": f"Use this quick frame to connect {topic} to what learners already know.",
        }
    if variant == "annotation_paragraph":
        return {
            "type": "annotation_paragraph",
            "text": f"Context note: the main block above shows the core structure; this note adds one useful teaching cue.",
        }
    if variant == "callout":
        return {
            "type": "callout",
            "label": "Key idea",
            "text": f"Focus on the relationship between the parts of {topic}, not just the labels.",
        }
    if variant == "caption":
        return {
            "type": "caption",
            "text": "Caption: this supporting note should stay visually subordinate to the primary block.",
            "icon_name": "ri-information-line",
        }
    if variant == "divider":
        return {"type": "divider"}
    if variant == "outro_paragraph":
        return {
            "type": "outro_paragraph",
            "text": f"Takeaway: once the main pattern is clear, {topic} becomes easier to reason about.",
        }
    if variant == "rich_text":
        return {
            "type": "rich_text",
            "paragraphs": [
                "This supporting paragraph gives the slide a little more explanatory depth.",
                "It should combine with the primary block without stealing attention.",
            ],
        }
    if variant == "definition":
        return {
            "type": "definition",
            "term": "Supporting context",
            "definition": "Extra information that clarifies the main idea without becoming the primary visual.",
        }
    if variant == "myth_vs_fact":
        return {
            "type": "callout",
            "label": "Myth vs fact",
            "text": "Myth: more content always teaches more. Fact: one well-placed support block can clarify the main idea.",
        }
    if variant == "summary_strip":
        return {
            "type": "rich_text",
            "paragraphs": [
                "Summary: identify the main parts, compare their roles, then connect them back to the lesson goal."
            ],
        }
    return _fallback_block(variant, 1)


def _fallback_items(item_count: int, requires_icons: bool) -> list[dict[str, str]]:
    icons = [
        "ri-lightbulb-line",
        "ri-compass-3-line",
        "ri-book-open-line",
        "ri-shield-check-line",
        "ri-line-chart-line",
        "ri-flag-2-line",
        "ri-tools-line",
        "ri-sparkling-line",
    ]
    items = []
    for index in range(item_count):
        item = {
            "heading": f"Point {index + 1}",
            "description": "A concise generated explanation that fits inside the selected block.",
        }
        if requires_icons:
            item["icon_name"] = icons[index % len(icons)]
        items.append(item)
    return items


def _resize_items(
    items: list[Any],
    item_count: int,
    requires_icons: bool,
) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for item in items[:item_count]:
        if isinstance(item, dict):
            normalized.append(dict(item))
        else:
            normalized.append({"heading": str(item), "description": ""})

    if len(normalized) < item_count:
        normalized.extend(_fallback_items(item_count - len(normalized), requires_icons))

    if requires_icons:
        fallback = _fallback_items(item_count, True)
        for index, item in enumerate(normalized):
            item.setdefault("icon_name", fallback[index]["icon_name"])

    return normalized


def _primary_block(payload: dict[str, Any]) -> dict[str, Any]:
    blocks = payload.get("contentBlocks") or []
    idx = max(0, min(int(payload.get("primary_block_index") or 0), len(blocks) - 1))
    return blocks[idx]


def _layout_node_from_block(block: dict[str, Any]) -> Any:
    return GyMLSerializer()._serialize_block(
        ComposedBlock(type=block.get("type", "paragraph"), content=block)
    )


def _layout_node_from_payload(payload: dict[str, Any]) -> Any:
    return _layout_node_from_block(_primary_block(payload))


def _preview_blocks(payload: dict[str, Any]) -> list[tuple[dict[str, Any], Any]]:
    blocks = payload.get("contentBlocks") or []
    primary_idx = max(0, min(int(payload.get("primary_block_index") or 0), len(blocks) - 1))
    ordered_blocks = [blocks[primary_idx]]
    ordered_blocks.extend(block for index, block in enumerate(blocks) if index != primary_idx)

    rendered_blocks: list[tuple[dict[str, Any], Any]] = []
    for block in ordered_blocks:
        if isinstance(block, dict):
            node = _layout_node_from_block(block)
            if node is not None:
                rendered_blocks.append((block, node))
    return rendered_blocks


def _inline_css(family: str, theme: Theme) -> str:
    renderer = GyMLRenderer(theme=theme)
    css_parts = [
        get_slide_css("__all__", theme),
        renderer._get_responsive_styles(),
    ]

    css_parts.append(
        """
html, body {
    margin: 0;
    padding: 0;
    width: 100%;
    height: 100%;
    background: #020617;
    overflow: hidden;
}
.sandbox-viewer {
    width: 100%;
    height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 16px;
    overflow: hidden;
    box-sizing: border-box;
}
.mock-browser {
    width: min(100%, 1280px, calc((100vh - 32px) * 16 / 9));
    aspect-ratio: 16 / 9;
    height: auto;
    background: #0a0f1a;
    border: 1px solid #1e293b;
    border-radius: 12px;
    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5);
    overflow: hidden;
}
.slide-container {
    width: 100%;
    height: 100%;
    overflow-y: auto;
}
.gyml-deck {
    height: 100%;
}
.gyml-deck .slide-section {
    width: 100%;
    height: 100% !important;
    min-height: 100% !important;
    max-height: none;
}
"""
    )
    return "\n".join(css_parts)


def _preview_document(
    *,
    block_html: str,
    title: str,
    density: str,
    image_layout: str,
    css: str,
) -> str:
    escaped_title = escape(title or "Untitled slide")
    has_image = image_layout != "blank"
    accent = ""
    if has_image:
        accent = (
            '<div class="accent-image-placeholder">'
            '<div class="placeholder-content">'
            '<span class="placeholder-text">Accent image layout</span>'
            "</div></div>"
        )

    render_image_early = has_image and image_layout != "bottom"
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <link href="https://cdn.jsdelivr.net/npm/remixicon@4.2.0/fonts/remixicon.css" rel="stylesheet">
  <style>
  {css}
  .sandbox-fullscreen-toggle {{
    position: absolute;
    top: 10px;
    right: 10px;
    z-index: 50;
    border: 1px solid rgba(148, 163, 184, 0.35);
    border-radius: 999px;
    width: 34px;
    height: 34px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    background: rgba(2, 6, 23, 0.55);
    color: #e2e8f0;
    cursor: pointer;
    backdrop-filter: blur(6px);
  }}
  .sandbox-fullscreen-toggle:hover {{
    background: rgba(15, 23, 42, 0.85);
  }}
  .mock-browser {{
    position: relative;
  }}
  .mock-browser:fullscreen {{
    width: 100vw !important;
    height: 100vh !important;
    max-width: none !important;
    aspect-ratio: auto !important;
    border-radius: 0;
    border: none;
  }}
  </style>
</head>
<body>
  <div class="sandbox-viewer">
    <div class="mock-browser" id="sandbox-browser">
      <button
        class="sandbox-fullscreen-toggle"
        id="sandbox-fs-btn"
        title="Toggle fullscreen"
        aria-label="Toggle fullscreen"
      >
        <i class="ri-fullscreen-line" id="sandbox-fs-icon"></i>
      </button>
      <div class="gyml-deck">
        <div class="slide-container">
          <section id="sandbox-slide"
            class="slide-section"
            role="region"
            aria-label="Slide sandbox"
            data-image-layout="{image_layout}"
            data-density="{density}"
            data-has-image="{str(has_image).lower()}"
            style="--accent-width: 500px; --block-gap: 3rem;">
            {accent if render_image_early else ""}
            <div class="body">
              <h1>{escaped_title}</h1>
              {block_html}
            </div>
            {accent if has_image and not render_image_early else ""}
          </section>
        </div>
      </div>
    </div>
  </div>
  <script>
    (function () {{
      const btn = document.getElementById("sandbox-fs-btn");
      const icon = document.getElementById("sandbox-fs-icon");
      const target = document.getElementById("sandbox-browser");
      if (!btn || !icon || !target) return;

      function syncIcon() {{
        const fs = !!document.fullscreenElement;
        icon.className = fs ? "ri-fullscreen-exit-line" : "ri-fullscreen-line";
      }}

      btn.addEventListener("click", async function () {{
        try {{
          if (!document.fullscreenElement) {{
            await target.requestFullscreen();
          }} else {{
            await document.exitFullscreen();
          }}
        }} catch (e) {{
          // no-op
        }} finally {{
          syncIcon();
        }}
      }});

      document.addEventListener("fullscreenchange", syncIcon);
      syncIcon();
    }})();
  </script>
</body>
</html>"""


def _section_html_for_debug(
    block_html: str,
    payload: dict[str, Any],
    density: str,
    image_layout: str,
) -> str:
    section = GyMLSection(
        id="sandbox-slide",
        image_layout=image_layout,
        accent_image=(
            GyMLImage(src="placeholder", alt="Accent image layout", is_accent=True)
            if image_layout != "blank"
            else None
        ),
        slide_density=density,
        body=GyMLBody(children=[]),
    )
    title = escape(str(payload.get("title") or "Untitled slide"))
    return (
        f'<section id="{section.id}" class="slide-section" '
        f'data-image-layout="{section.image_layout}" data-density="{density}">\n'
        f'<div class="body">\n<h1>{title}</h1>\n{block_html}\n</div>\n</section>'
    )


def _active_rules(
    *,
    variant: str,
    family: str,
    layout_node: Any,
    context: SandboxRenderContext,
) -> list[RenderingRule]:
    real_family = _family_folder(family)
    families = {"__global__", family, real_family}
    item_count = len(getattr(layout_node, "items", []) or [])
    items = list(getattr(layout_node, "items", []) or [None])
    active: dict[str, RenderingRule] = {}

    for rule in RULE_REGISTRY.values():
        if rule.family not in families:
            continue
        for index, item in enumerate(items):
            icon_class = _icon_class(item)
            kwargs = {
                "variant": variant,
                "family": family,
                "block": layout_node,
                "block_type": type(layout_node).__name__,
                "context": context,
                "item": item,
                "index": index,
                "i": index,
                "n": item_count,
                "item_count": item_count,
                "icon_class": icon_class,
                "image_url": getattr(item, "image_url", None) if item is not None else None,
                "img_url": getattr(item, "image_url", None) if item is not None else None,
            }
            try:
                if rule.condition_fn(**kwargs):
                    active[rule.name] = rule
                    break
            except Exception:
                continue

    return list(active.values())


def _icon_class(item: Any) -> str:
    icon = getattr(item, "icon", None)
    return str(getattr(icon, "alt", "") or "").strip()


def _generate_content(
    *,
    variant: str,
    item_count: int,
    density: str,
    title: str,
    image_layout: str,
) -> dict[str, Any]:
    from app.services.llm.model_loader import load_groq

    builder = _load_prompt_builder()
    prompt = _call_prompt_builder(
        builder,
        variant=variant,
        item_count=item_count,
        density=density,
        title=title,
    )
    llm = load_groq()
    response = llm.invoke(prompt)
    payload = _parse_json_response(response)
    return _normalize_generated_payload(
        payload,
        variant=variant,
        item_count=item_count,
        density=density,
        title=title,
        image_layout=image_layout,
    )


def _render_current(
    *,
    payload: dict[str, Any],
    variant: str,
    density: str,
    image_layout: str,
    title: str,
    theme: Theme,
) -> tuple[str, str, list[RenderingRule]]:
    rendered_blocks = _preview_blocks(payload)
    context = SandboxRenderContext(
        variant=variant,
        density=density,
        image_layout=image_layout,
        title=title,
        item_count=0,
        theme=theme,
    )

    html_parts: list[str] = []
    primary_node = rendered_blocks[0][1] if rendered_blocks else None
    for block_index, (block, layout_node) in enumerate(rendered_blocks):
        block_variant = variant if block_index == 0 else str(block.get("variant") or block.get("type") or "")
        context.variant = block_variant
        context.item_count = len(getattr(layout_node, "items", []) or [])
        renderer = _load_family_renderer(block_variant) if block_variant in ALL_BLOCKS else FamilyRendererAdapter(
            variant=block_variant,
            family="supporting_contextual",
            render_fn=None,
        )
        html_parts.append(renderer.render(layout_node, context))

    block_html = "\n".join(part for part in html_parts if part)
    debug_html = _section_html_for_debug(block_html, payload, density, image_layout)
    rules = []
    if primary_node is not None:
        context.variant = variant
        context.item_count = len(getattr(primary_node, "items", []) or [])
        rules = _active_rules(
            variant=variant,
            family=ALL_BLOCKS[variant].family,
            layout_node=primary_node,
            context=context,
        )
    return block_html, debug_html, rules


st.set_page_config(page_title="GyML Block Sandbox", layout="wide")
st.title("GyML Block Sandbox")

# Streamlit re-runs this script, but imported modules can remain cached.
# Reload key dependencies so theme/renderer changes are reflected without
# restarting the Streamlit process.
_reload_sandbox_dependencies()

variant_options = sorted(ALL_BLOCKS.keys())

with st.sidebar:
    reload_modules = st.button(
        "Reload Python modules",
        help="Pick up renderer/spec Python edits without restarting Streamlit.",
    )
    if reload_modules:
        _reload_sandbox_dependencies()
        st.rerun()

    selected_variant = st.selectbox("Block variant", variant_options)
    spec = ALL_BLOCKS[selected_variant]
    count_options = _count_options(spec)
    density_options = _density_options(spec)

    theme_options = sorted(THEMES.keys())
    default_theme_index = (
        theme_options.index("midnight") if "midnight" in theme_options else 0
    )
    selected_theme_name = st.selectbox(
        "Theme",
        theme_options,
        index=default_theme_index,
    )
    item_count = int(
        st.selectbox(
            "Item count",
            count_options,
            index=_select_index(count_options, 3, count_options[0]),
        )
    )
    layout_options = _layout_options_for_count(spec, item_count)
    can_combine = _is_combinable_for_count(spec, item_count)
    density = st.selectbox(
        "Density",
        density_options,
        index=_select_index(density_options, "balanced", density_options[0]),
    )
    image_layout = st.selectbox(
        "Image layout",
        layout_options,
        index=_select_index(layout_options, "blank", layout_options[0]),
    )
    include_supporting_block = st.checkbox(
        "Include supporting block",
        value=False,
        disabled=not can_combine,
        help=(
            "Enabled only when the selected block's active item-count profile is combinable."
            if not can_combine
            else None
        ),
    )
    if not can_combine:
        include_supporting_block = False
    supporting_variant = st.selectbox(
        "Supporting block",
        SUPPORTING_BLOCK_VARIANTS,
        index=SUPPORTING_BLOCK_VARIANTS.index("callout"),
        disabled=not include_supporting_block,
    )
    title = st.text_input("Slide title", value="How Neural Networks Learn")
    generate = st.button("Generate", type="primary")

active_profile = _active_profile(spec, item_count)
st.caption(
    f"Family: `{spec.family}` -> renderer folder `{_family_folder(spec.family)}` | "
    f"Profile: `{active_profile.layout_variant}` | "
    f"Items: `{active_profile.item_range[0]}-{active_profile.item_range[1]}` | "
    f"Combinable: `{active_profile.combinable}`"
)

if generate:
    with st.spinner("Generating GyML content with Groq..."):
        try:
            st.session_state.generated_payload = _generate_content(
                variant=selected_variant,
                item_count=item_count,
                density=density,
                title=title,
                image_layout=image_layout,
            )
            st.session_state.controls = {
                "variant": selected_variant,
                "item_count": item_count,
                "theme_name": selected_theme_name,
                "density": density,
                "image_layout": image_layout,
                "include_supporting_block": include_supporting_block,
                "supporting_variant": supporting_variant,
                "title": title,
            }
        except Exception as exc:
            st.error(f"Generation failed: {exc}")

if "generated_payload" not in st.session_state:
    st.info("Choose a block variant and click Generate.")
    st.stop()

controls = st.session_state.get(
    "controls",
    {
        "variant": selected_variant,
        "item_count": item_count,
        "theme_name": selected_theme_name,
        "density": density,
        "image_layout": image_layout,
        "include_supporting_block": include_supporting_block,
        "supporting_variant": supporting_variant,
        "title": title,
    },
)
controls.setdefault("theme_name", selected_theme_name)
controls.setdefault("include_supporting_block", include_supporting_block)
controls.setdefault("supporting_variant", supporting_variant)
controls["include_supporting_block"] = include_supporting_block
controls["supporting_variant"] = supporting_variant

payload = _normalize_generated_payload(
    st.session_state.generated_payload,
    variant=controls["variant"],
    item_count=controls["item_count"],
    density=controls["density"],
    title=controls["title"],
    image_layout=controls["image_layout"],
)
if controls["include_supporting_block"]:
    payload = dict(payload)
    payload["contentBlocks"] = list(payload.get("contentBlocks") or [])
    payload["contentBlocks"].append(
        _supporting_block(controls["supporting_variant"], str(payload.get("title") or controls["title"]))
    )
selected_theme = THEMES[controls["theme_name"]]

try:
    block_html, rendered_html, active_rules = _render_current(
        payload=payload,
        variant=controls["variant"],
        density=controls["density"],
        image_layout=controls["image_layout"],
        title=controls["title"],
        theme=selected_theme,
    )
    css = _inline_css(ALL_BLOCKS[controls["variant"]].family, selected_theme)
    preview_html = _preview_document(
        block_html=block_html,
        title=str(payload.get("title") or controls["title"]),
        density=controls["density"],
        image_layout=controls["image_layout"],
        css=css,
    )
    st.components.v1.html(preview_html, height=820, scrolling=False)
except Exception as exc:
    st.error(f"Render failed: {exc}")
    st.stop()

with st.expander("Generated Content"):
    st.json(payload)

with st.expander("Rendered HTML"):
    st.code(rendered_html, language="html")

with st.expander("Active Rules"):
    if active_rules:
        st.dataframe(
            [
                {
                    "name": rule.name,
                    "family": rule.family,
                    "condition": rule.condition,
                    "effect": rule.effect_description,
                    "css_target": rule.css_target,
                    "risk": rule.breaking_change_risk,
                }
                for rule in active_rules
            ],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.write("No registered rules fired for this render.")
