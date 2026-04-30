from dataclasses import dataclass
from typing import Callable

from blocks.shared.base_renderer import RenderContext


@dataclass
class RenderingRule:
    name: str
    family: str
    condition: str
    condition_fn: Callable[..., bool]
    effect_description: str
    css_mechanism: str
    css_target: str
    reason: str
    breaking_change_risk: str


RULE_REGISTRY: dict[str, RenderingRule] = {}


def _r(rule: RenderingRule):
    RULE_REGISTRY[rule.name] = rule


def _animated(context: RenderContext | None = None, **_: object) -> bool:
    return bool(getattr(context, "animated", False))


def _block_type(block: object = None, **_: object) -> str:
    return type(block).__name__ if block is not None else ""


def _has_icon(item: object = None, **_: object) -> bool:
    return bool(getattr(item, "icon", None))


def _icon_alt(item: object = None, **_: object) -> str:
    icon = getattr(item, "icon", None)
    return str(getattr(icon, "alt", "") or "").strip()


def _has_points(item: object = None, **_: object) -> bool:
    return bool(getattr(item, "points", None))


def _has_dimension_points(item: object = None, **_: object) -> bool:
    points = getattr(item, "points", None) or []
    return len(points) > 0 and all(":" in str(point) for point in points)


def _has_title(item: object = None, **_: object) -> bool:
    return bool(getattr(item, "heading", None) or getattr(item, "label", None))


def _has_description(item: object = None, **_: object) -> bool:
    return bool(getattr(item, "description", None))


def _needs_ri_prefix(item: object = None, icon_class: str | None = None, **_: object) -> bool:
    value = icon_class if icon_class is not None else _icon_alt(item)
    return bool(value) and not value.startswith("ri-")


def _needs_ri_suffix(item: object = None, icon_class: str | None = None, **_: object) -> bool:
    value = icon_class if icon_class is not None else _icon_alt(item)
    return bool(value) and value.startswith("ri-") and not (
        value.endswith("-line") or value.endswith("-fill")
    )


def _concept_icon_needs_line(item: object = None, icon_class: str | None = None, **_: object) -> bool:
    value = icon_class if icon_class is not None else _icon_alt(item)
    concept_bases = ["brain", "pencil", "link", "shield", "star", "heart"]
    return _needs_ri_suffix(icon_class=value) and (
        any(base in value for base in concept_bases)
        or not any(char.isdigit() for char in value[-2:])
    )


# --- Register rules below ---
# __global__ rules first, then per-family

_r(RenderingRule(
    name="global_animated_card_segment",
    family="__global__",
    condition="context.animated",
    condition_fn=_animated,
    effect_description="Adds an animation class plus data-segment to rendered cards or output rows.",
    css_mechanism="data_attribute",
    css_target='section[data-animated="true"] [data-segment], .anim-slide-up, .anim-fade',
    reason="Animated decks hide segment-marked content until the slide animator reveals each card in narration order.",
    breaking_change_risk="high",
))

_r(RenderingRule(
    name="global_item_icon_present",
    family="__global__",
    condition="item.icon",
    condition_fn=_has_icon,
    effect_description="Reads item.icon.alt and may emit a card-icon wrapper with a RemixIcon class.",
    css_mechanism="class",
    css_target=".card-icon i",
    reason="Icon-aware variants use a visual symbol as the leading affordance for each card.",
    breaking_change_risk="medium",
))

_r(RenderingRule(
    name="global_icon_add_ri_prefix",
    family="__global__",
    condition='icon_class and not icon_class.startswith("ri-")',
    condition_fn=_needs_ri_prefix,
    effect_description="Normalizes bare icon names to ri-*-line classes before rendering the i element.",
    css_mechanism="class",
    css_target=".card-icon i",
    reason="Renderer input may provide short names while the CSS/icon font expects RemixIcon class names.",
    breaking_change_risk="medium",
))

_r(RenderingRule(
    name="global_icon_add_line_suffix",
    family="__global__",
    condition='icon_class starts with "ri-" but lacks "-line" or "-fill" and matches concept/number heuristic',
    condition_fn=_concept_icon_needs_line,
    effect_description="Adds -line to concept-style RemixIcon names that are unlikely to be valid as-is.",
    css_mechanism="class",
    css_target=".card-icon i",
    reason="Most concept icons in RemixIcon require a style suffix; the guard avoids changing numbered or brand-like names unnecessarily.",
    breaking_change_risk="medium",
))

_r(RenderingRule(
    name="global_card_icon_rendered",
    family="__global__",
    condition="icon_class",
    condition_fn=lambda icon_class=None, **_: bool(icon_class),
    effect_description="Emits <div class=\"card-icon\"><i class=\"...\"></i></div> before card content.",
    css_mechanism="class",
    css_target=".card-icon",
    reason="Card/icon variants reserve a styled icon slot that CSS sizes, colors, and positions per variant.",
    breaking_change_risk="medium",
))

_r(RenderingRule(
    name="global_card_title_rendered",
    family="__global__",
    condition="item.heading or item.label",
    condition_fn=_has_title,
    effect_description="Emits an h4.card-title for the item heading/label.",
    css_mechanism="class",
    css_target=".card-title",
    reason="Structured cards need a consistent title hook for typography, spacing, and variant-specific emphasis.",
    breaking_change_risk="low",
))

_r(RenderingRule(
    name="global_points_choose_list_region",
    family="__global__",
    condition="item.points",
    condition_fn=_has_points,
    effect_description="Renders item points instead of the fallback description paragraph.",
    css_mechanism="class",
    css_target=".card-list, .card-comparison-grid",
    reason="Point arrays represent scannable subcontent and should not be collapsed into body copy.",
    breaking_change_risk="medium",
))

_r(RenderingRule(
    name="global_dimension_points_grid",
    family="__global__",
    condition='all(":" in str(p) for p in item.points) and len(item.points) > 0',
    condition_fn=_has_dimension_points,
    effect_description="Renders colon-delimited points as card-comparison-row pairs inside card-comparison-grid.",
    css_mechanism="class",
    css_target=".card-comparison-grid, .card-comparison-row, .card-comparison-subject, .card-comparison-value",
    reason="Dimension-centric comparison data needs aligned subject/value rows rather than bullet markers.",
    breaking_change_risk="medium",
))

_r(RenderingRule(
    name="global_plain_points_list",
    family="__global__",
    condition="item.points and not is_dim_centric",
    condition_fn=lambda item=None, **_: _has_points(item=item) and not _has_dimension_points(item=item),
    effect_description="Renders ordinary points as li elements inside ul.card-list.",
    css_mechanism="class",
    css_target=".card-list",
    reason="Non-paired point content is styled as a compact list with variant-colored markers.",
    breaking_change_risk="medium",
))

_r(RenderingRule(
    name="global_description_fallback",
    family="__global__",
    condition="not item.points and item.description",
    condition_fn=lambda item=None, **_: (not _has_points(item=item)) and _has_description(item=item),
    effect_description="Renders item.description as p.card-text, preserving line breaks as <br>.",
    css_mechanism="class",
    css_target=".card-text",
    reason="Description-only cards still need a consistent body-text hook when no point list is present.",
    breaking_change_risk="low",
))

_r(RenderingRule(
    name="legacy_diamond_grid_2d_rotation",
    family="__global__",
    condition='fallback variant == "diamondGrid" and item_count == 4 and _diamond_idx is odd',
    condition_fn=lambda variant=None, item_count=None, diamond_idx=0, **_: variant == "diamondGrid" and item_count == 4 and diamond_idx % 2 == 1,
    effect_description='Adds class "grid-2d" to the smart-layout container in the monolithic fallback.',
    css_mechanism="class",
    css_target='.smart-layout[data-variant="diamondGrid"].grid-2d[data-item-count="4"]',
    reason="The fallback rotates four-item diamond grids between a horizontal row and a 2x2 arrangement for visual variety.",
    breaking_change_risk="medium",
))

_r(RenderingRule(
    name="legacy_diamond_grid_diagonal_rotation",
    family="__global__",
    condition='fallback variant == "diamondGrid" and item_count in {3, 5} and _diamond_idx is odd',
    condition_fn=lambda variant=None, item_count=None, diamond_idx=0, **_: variant == "diamondGrid" and item_count in {3, 5} and diamond_idx % 2 == 1,
    effect_description='Adds class "diagonal" to the smart-layout container in the monolithic fallback.',
    css_mechanism="class",
    css_target='.smart-layout[data-variant="diamondGrid"].diagonal',
    reason="The fallback rotates three- and five-item diamond grids into a diagonal flow to avoid repeated stack layouts.",
    breaking_change_risk="medium",
))

_r(RenderingRule(
    name="legacy_number_badge_variants",
    family="__global__",
    condition='fallback variant in ["bigBullets", "cardGrid", "timelineSequential"]',
    condition_fn=lambda variant=None, **_: variant in ["bigBullets", "cardGrid", "timelineSequential"],
    effect_description="Emits card-number with the one-based item index.",
    css_mechanism="class",
    css_target=".card-number",
    reason="These fallback variants use ordered badges as their primary visual hierarchy.",
    breaking_change_risk="medium",
))

_r(RenderingRule(
    name="legacy_generic_icon_enabled",
    family="__global__",
    condition='fallback variant not in {"timeline", "timelineHorizontal", "timelineSequential", "timelineMilestone"}',
    condition_fn=lambda variant=None, **_: variant not in {"timeline", "timelineHorizontal", "timelineSequential", "timelineMilestone"},
    effect_description="Enables the fallback generic auto-icon path for non-timeline variants.",
    css_mechanism="class",
    css_target=".card-icon",
    reason="Timeline variants draw dots, badges, or axis markers, while other fallback variants may use regular icon boxes.",
    breaking_change_risk="medium",
))

_r(RenderingRule(
    name="legacy_default_solid_box_icons",
    family="__global__",
    condition='fallback variant == "solidBoxesWithIconsInside" and not item.icon',
    condition_fn=lambda variant=None, item=None, **_: variant == "solidBoxesWithIconsInside" and not _has_icon(item=item),
    effect_description="Chooses a rotating default RemixIcon for the card-icon slot.",
    css_mechanism="class",
    css_target='.smart-layout[data-variant="solidBoxesWithIconsInside"] .card-icon',
    reason="Solid icon boxes depend on every card having an icon, so the fallback fills missing authoring data.",
    breaking_change_risk="medium",
))

_r(RenderingRule(
    name="legacy_bullet_check_icon",
    family="__global__",
    condition='fallback variant == "bulletCheck" and not item.icon',
    condition_fn=lambda variant=None, item=None, **_: variant == "bulletCheck" and not _has_icon(item=item),
    effect_description='Uses "ri-check-line" as the card icon.',
    css_mechanism="class",
    css_target='.smart-layout[data-variant="bulletCheck"] .card-icon',
    reason="Check-list bullets communicate positive/completed items with a consistent success icon.",
    breaking_change_risk="medium",
))

_r(RenderingRule(
    name="legacy_bullet_cross_icon",
    family="__global__",
    condition='fallback variant == "bulletCross" and not item.icon',
    condition_fn=lambda variant=None, item=None, **_: variant == "bulletCross" and not _has_icon(item=item),
    effect_description='Uses "ri-close-line" as the card icon.',
    css_mechanism="class",
    css_target='.smart-layout[data-variant="bulletCross"] .card-icon',
    reason="Cross-list bullets communicate excluded or negative items with a consistent danger icon.",
    breaking_change_risk="medium",
))

# timeline

_r(RenderingRule(
    name="timeline_icon_badge",
    family="timeline",
    condition='variant == "timelineIcon"',
    condition_fn=lambda variant=None, **_: variant == "timelineIcon",
    effect_description="Emits card-number timeline-icon-badge with an icon instead of the generic title-leading icon.",
    css_mechanism="class",
    css_target='.smart-layout[data-variant="timelineIcon"] .timeline-icon-badge',
    reason="TimelineIcon places the icon on the vertical axis so each event marker is visually tied to the timeline line.",
    breaking_change_risk="medium",
))

_r(RenderingRule(
    name="timeline_icon_custom_badge",
    family="timeline",
    condition='variant == "timelineIcon" and item.icon',
    condition_fn=lambda variant=None, item=None, **_: variant == "timelineIcon" and _has_icon(item=item),
    effect_description="Uses item.icon.alt for the timeline badge icon.",
    css_mechanism="class",
    css_target=".timeline-icon-badge i",
    reason="Author-provided icons let each timeline event have a semantically distinct marker.",
    breaking_change_risk="low",
))

_r(RenderingRule(
    name="timeline_icon_badge_prefix",
    family="timeline",
    condition='variant == "timelineIcon" and item.icon and not icon_cls.startswith("ri-")',
    condition_fn=lambda variant=None, item=None, **_: variant == "timelineIcon" and _needs_ri_prefix(item=item),
    effect_description="Prefixes custom timelineIcon badge names with ri- and appends -line.",
    css_mechanism="class",
    css_target=".timeline-icon-badge i",
    reason="The timeline badge uses the same RemixIcon font contract as regular card icons.",
    breaking_change_risk="low",
))

_r(RenderingRule(
    name="timeline_vertical_content_mode",
    family="timeline",
    condition='variant == "timeline"',
    condition_fn=lambda variant=None, **_: variant == "timeline",
    effect_description="Renders timeline-specific year and description content instead of generic title/points content.",
    css_mechanism="data_attribute",
    css_target='.smart-layout[data-variant="timeline"] .card-year, .smart-layout[data-variant="timeline"] .card-text',
    reason="The vertical timeline is date-led, with year labels aligned to timeline dots rather than card titles.",
    breaking_change_risk="medium",
))

_r(RenderingRule(
    name="timeline_year_label",
    family="timeline",
    condition='variant == "timeline" and item.year',
    condition_fn=lambda variant=None, item=None, **_: variant == "timeline" and bool(getattr(item, "year", None)),
    effect_description="Emits div.card-year before timeline description text.",
    css_mechanism="class",
    css_target=".card-year",
    reason="Year labels are styled separately so chronology is visually prominent.",
    breaking_change_risk="low",
))

_r(RenderingRule(
    name="timeline_description_text",
    family="timeline",
    condition='variant == "timeline" and item.description',
    condition_fn=lambda variant=None, item=None, **_: variant == "timeline" and _has_description(item=item),
    effect_description="Emits p.card-text for the event description.",
    css_mechanism="class",
    css_target='.smart-layout[data-variant="timeline"] .card-text',
    reason="Timeline event copy uses compact text sizing distinct from generic cards.",
    breaking_change_risk="low",
))

# sequential_process

_r(RenderingRule(
    name="sequential_output_block_route",
    family="sequential_process",
    condition='block_type == "GyMLSequentialOutput"',
    condition_fn=lambda block=None, **_: _block_type(block=block) == "GyMLSequentialOutput",
    effect_description="Renders output-line rows inside sequential-output-container.",
    css_mechanism="class",
    css_target=".sequential-output-container, .output-line",
    reason="Sequential output blocks imitate terminal-style line-by-line output rather than cards.",
    breaking_change_risk="high",
))

_r(RenderingRule(
    name="sequential_output_animated_typewriter",
    family="sequential_process",
    condition='block_type == "GyMLSequentialOutput" and context.animated',
    condition_fn=lambda block=None, context=None, **_: _block_type(block=block) == "GyMLSequentialOutput" and _animated(context=context),
    effect_description="Adds anim-typewriter and data-segment to each output-line.",
    css_mechanism="data_attribute",
    css_target=".output-line.anim-typewriter[data-segment]",
    reason="Terminal output is revealed one line at a time during animated narration.",
    breaking_change_risk="medium",
))

_r(RenderingRule(
    name="process_arrow_block_route",
    family="sequential_process",
    condition='block_type == "GyMLProcessArrowBlock"',
    condition_fn=lambda block=None, **_: _block_type(block=block) == "GyMLProcessArrowBlock",
    effect_description="Renders pa-container-min columns with image, arrow label, and optional description.",
    css_mechanism="class",
    css_target=".pa-container-min, .pa-col-min",
    reason="Standalone process arrow blocks use a bespoke horizontal arrow-card layout rather than generic smart-layout cards.",
    breaking_change_risk="high",
))

_r(RenderingRule(
    name="process_arrow_color_fallback",
    family="sequential_process",
    condition="not item.color",
    condition_fn=lambda item=None, **_: not bool(getattr(item, "color", None)),
    effect_description="Uses a rotating blue palette value for --item-color.",
    css_mechanism="inline_style",
    css_target="--item-color",
    reason="The arrow layout always needs a color token for image placeholders and arrow fills.",
    breaking_change_risk="low",
))

_r(RenderingRule(
    name="process_arrow_image_placeholder",
    family="sequential_process",
    condition='not image_url or image_url == "null"',
    condition_fn=lambda image_url=None, item=None, **_: not (image_url if image_url is not None else getattr(item, "image_url", None)) or (image_url if image_url is not None else getattr(item, "image_url", None)) == "null",
    effect_description='Emits pa-img-minimal placeholder with inline "--item-color" instead of an img tag.',
    css_mechanism="inline_style",
    css_target=".pa-img-minimal.placeholder[style*='--item-color']",
    reason="Missing process imagery still occupies the image slot and inherits the step color.",
    breaking_change_risk="medium",
))

_r(RenderingRule(
    name="process_arrow_first_class",
    family="sequential_process",
    condition="i == 0",
    condition_fn=lambda index=None, i=None, **_: (i if i is not None else index) == 0,
    effect_description='Adds "is-first" to the first pa-col-min item.',
    css_mechanism="class",
    css_target=".pa-col-min.is-first .pa-arrow-min",
    reason="The first arrow column has distinct edge treatment in the minimalist process arrow CSS.",
    breaking_change_risk="low",
))

_r(RenderingRule(
    name="process_arrow_last_class",
    family="sequential_process",
    condition="i == n - 1",
    condition_fn=lambda index=None, i=None, n=None, **_: n is not None and (i if i is not None else index) == n - 1,
    effect_description='Adds "is-last" to the last pa-col-min item.',
    css_mechanism="class",
    css_target=".pa-col-min.is-last .pa-arrow-min",
    reason="The last arrow column has distinct edge treatment and no outgoing arrow continuation.",
    breaking_change_risk="low",
))

_r(RenderingRule(
    name="process_arrow_description",
    family="sequential_process",
    condition="item.description",
    condition_fn=_has_description,
    effect_description="Emits div.pa-desc-min below the arrow label.",
    css_mechanism="class",
    css_target=".pa-desc-min",
    reason="Standalone arrow steps support short explanatory copy with dedicated spacing and typography.",
    breaking_change_risk="low",
))

_r(RenderingRule(
    name="process_arrow_animated_fade",
    family="sequential_process",
    condition='block_type == "GyMLProcessArrowBlock" and context.animated',
    condition_fn=lambda block=None, context=None, **_: _block_type(block=block) == "GyMLProcessArrowBlock" and _animated(context=context),
    effect_description="Adds anim-fade and data-segment to each process arrow column.",
    css_mechanism="data_attribute",
    css_target=".pa-col-min.anim-fade[data-segment]",
    reason="Process arrow columns reveal step-by-step without changing the arrow geometry.",
    breaking_change_risk="medium",
))

_r(RenderingRule(
    name="process_smart_number_badges",
    family="sequential_process",
    condition='variant in ["processSteps", "processArrow"]',
    condition_fn=lambda variant=None, **_: variant in ["processSteps", "processArrow"],
    effect_description="Emits card-number badges for smart-layout process cards.",
    css_mechanism="class",
    css_target='.smart-layout[data-variant="processSteps"] .card-number, .smart-layout[data-variant="processArrow"] .card-number',
    reason="Process step variants communicate ordered progression with visible step numbers.",
    breaking_change_risk="medium",
))

# comparison

_r(RenderingRule(
    name="comparison_table_route",
    family="comparison",
    condition='block_type == "GyMLComparisonTable"',
    condition_fn=lambda block=None, **_: _block_type(block=block) == "GyMLComparisonTable",
    effect_description="Renders comparison-table-wrapper with refined-comparison-table instead of cards.",
    css_mechanism="class",
    css_target=".comparison-table-wrapper, .refined-comparison-table",
    reason="Comparison tables need fixed tabular alignment and horizontal scrolling separate from card layouts.",
    breaking_change_risk="high",
))

_r(RenderingRule(
    name="comparison_table_caption",
    family="comparison",
    condition="block.caption",
    condition_fn=lambda block=None, **_: bool(getattr(block, "caption", None)),
    effect_description="Emits h3.comparison-table-title above the table.",
    css_mechanism="class",
    css_target=".comparison-table-title",
    reason="Captions become visible table headings with their own spacing and emphasis.",
    breaking_change_risk="low",
))

_r(RenderingRule(
    name="comparison_table_headers",
    family="comparison",
    condition="block.headers",
    condition_fn=lambda block=None, **_: bool(getattr(block, "headers", None)),
    effect_description="Emits thead/tr/th cells for comparison table headers.",
    css_mechanism="class",
    css_target=".refined-comparison-table th",
    reason="Headers are styled as uppercase column labels and define the body column count.",
    breaking_change_risk="medium",
))

_r(RenderingRule(
    name="comparison_table_rows",
    family="comparison",
    condition="block.rows",
    condition_fn=lambda block=None, **_: bool(getattr(block, "rows", None)),
    effect_description="Emits tbody rows and pads cells to the header-derived column count.",
    css_mechanism="class",
    css_target=".refined-comparison-table td",
    reason="Rows carry the comparison data and must preserve column alignment even when source rows are short.",
    breaking_change_risk="medium",
))

_r(RenderingRule(
    name="comparison_animated_side_reveal",
    family="comparison",
    condition='context.animated and variant == "comparison"',
    condition_fn=lambda variant=None, context=None, **_: variant == "comparison" and _animated(context=context),
    effect_description="Uses anim-slide-left for the first card and anim-slide-right for later cards.",
    css_mechanism="class",
    css_target=".anim-slide-left, .anim-slide-right",
    reason="Base comparison cards enter from opposing sides to reinforce contrast between compared subjects.",
    breaking_change_risk="medium",
))

_r(RenderingRule(
    name="comparison_animated_default_reveal",
    family="comparison",
    condition='context.animated and variant != "comparison"',
    condition_fn=lambda variant=None, context=None, **_: variant != "comparison" and _animated(context=context),
    effect_description="Uses anim-slide-up for non-base comparison smart-layout cards.",
    css_mechanism="class",
    css_target=".anim-slide-up",
    reason="Pros/cons and before/after variants keep the standard card reveal while preserving their layout-specific CSS.",
    breaking_change_risk="low",
))

_r(RenderingRule(
    name="comparison_generic_icon_enabled",
    family="comparison",
    condition='variant not in {"comparison"}',
    condition_fn=lambda variant=None, **_: variant != "comparison",
    effect_description="Enables auto-icon rendering for comparison variants other than the base comparison layout.",
    css_mechanism="class",
    css_target='.smart-layout[data-variant="comparisonProsCons"] .card-icon, .smart-layout[data-variant="comparisonBeforeAfter"] .card-icon',
    reason="The base comparison layout relies on nth-child accent colors, while the other comparison variants support icon-led cards.",
    breaking_change_risk="medium",
))

_r(RenderingRule(
    name="comparison_pros_cons_default_icons",
    family="comparison",
    condition='variant == "comparisonProsCons" and not item.icon',
    condition_fn=lambda variant=None, item=None, **_: variant == "comparisonProsCons" and not _has_icon(item=item),
    effect_description='Uses ri-check-line for the first card and ri-close-line for subsequent cards.',
    css_mechanism="class",
    css_target='.smart-layout[data-variant="comparisonProsCons"] .card-icon',
    reason="Pros/cons cards need conventional positive and negative symbols even when the input omitted icons.",
    breaking_change_risk="medium",
))

# stats_quantitative

_r(RenderingRule(
    name="stats_value_label_mode",
    family="stats_quantitative",
    condition='variant == "stats"',
    condition_fn=lambda variant=None, **_: variant == "stats",
    effect_description="Enables stat-specific value and label markup before the generic card title/content.",
    css_mechanism="data_attribute",
    css_target='.smart-layout[data-variant="stats"] .card-value, .smart-layout[data-variant="stats"] .card-label',
    reason="Stats slides elevate numeric values above ordinary card text.",
    breaking_change_risk="medium",
))

_r(RenderingRule(
    name="stats_card_value",
    family="stats_quantitative",
    condition='variant == "stats" and item.value',
    condition_fn=lambda variant=None, item=None, **_: variant == "stats" and bool(getattr(item, "value", None)),
    effect_description="Emits div.card-value for the stat number.",
    css_mechanism="class",
    css_target=".card-value",
    reason="The numeric value is the primary visual object and receives large display typography.",
    breaking_change_risk="medium",
))

_r(RenderingRule(
    name="stats_card_label",
    family="stats_quantitative",
    condition='variant == "stats" and item.label',
    condition_fn=lambda variant=None, item=None, **_: variant == "stats" and bool(getattr(item, "label", None)),
    effect_description="Emits div.card-label for the stat label.",
    css_mechanism="class",
    css_target=".card-label",
    reason="Stat labels are uppercase supporting text under the displayed number.",
    breaking_change_risk="low",
))

# grid_container

_r(RenderingRule(
    name="grid_comparison_table_route",
    family="grid_container",
    condition='block_type == "GyMLComparisonTable"',
    condition_fn=lambda block=None, **_: _block_type(block=block) == "GyMLComparisonTable",
    effect_description="Delegates to the grid family comparison-table renderer.",
    css_mechanism="class",
    css_target=".comparison-table-wrapper, .refined-comparison-table",
    reason="Grid/container can host standalone comparison tables that need tabular structure instead of cards.",
    breaking_change_risk="high",
))

_r(RenderingRule(
    name="grid_split_panel_route",
    family="grid_container",
    condition='block_type == "GyMLSplitPanel"',
    condition_fn=lambda block=None, **_: _block_type(block=block) == "GyMLSplitPanel",
    effect_description="Renders split-panel with left and right panel-half children.",
    css_mechanism="class",
    css_target=".split-panel, .panel-half.left, .panel-half.right",
    reason="Split panels need two fixed columns rather than the generic smart-layout grid.",
    breaking_change_risk="high",
))

_r(RenderingRule(
    name="grid_table_caption",
    family="grid_container",
    condition="block.caption",
    condition_fn=lambda block=None, **_: bool(getattr(block, "caption", None)),
    effect_description="Emits h3.comparison-table-title in grid-hosted comparison tables.",
    css_mechanism="class",
    css_target=".comparison-table-title",
    reason="Grid-hosted tables use the same caption styling as analytical comparison tables.",
    breaking_change_risk="low",
))

_r(RenderingRule(
    name="grid_table_headers",
    family="grid_container",
    condition="block.headers",
    condition_fn=lambda block=None, **_: bool(getattr(block, "headers", None)),
    effect_description="Emits thead/tr/th cells in grid-hosted comparison tables.",
    css_mechanism="class",
    css_target=".refined-comparison-table th",
    reason="Header markup activates the refined table header styling and determines row padding.",
    breaking_change_risk="medium",
))

_r(RenderingRule(
    name="grid_table_rows",
    family="grid_container",
    condition="block.rows",
    condition_fn=lambda block=None, **_: bool(getattr(block, "rows", None)),
    effect_description="Emits tbody/tr/td cells in grid-hosted comparison tables.",
    css_mechanism="class",
    css_target=".refined-comparison-table td",
    reason="Rows provide the visible table data and maintain alignment with optional headers.",
    breaking_change_risk="medium",
))

_r(RenderingRule(
    name="grid_diamond_2d_rotation",
    family="grid_container",
    condition='variant == "diamondGrid" and item_count == 4 and context._diamond_idx is odd',
    condition_fn=lambda variant=None, item_count=None, context=None, **_: variant == "diamondGrid" and item_count == 4 and getattr(context, "_diamond_idx", 0) % 2 == 1,
    effect_description='Adds class "grid-2d" to the smart-layout container.',
    css_mechanism="class",
    css_target='.smart-layout[data-variant="diamondGrid"].grid-2d[data-item-count="4"]',
    reason="Four-item diamond grids alternate between horizontal and 2x2 compositions for variety.",
    breaking_change_risk="medium",
))

_r(RenderingRule(
    name="grid_diamond_diagonal_rotation",
    family="grid_container",
    condition='variant == "diamondGrid" and item_count in {3, 5} and context._diamond_idx is odd',
    condition_fn=lambda variant=None, item_count=None, context=None, **_: variant == "diamondGrid" and item_count in {3, 5} and getattr(context, "_diamond_idx", 0) % 2 == 1,
    effect_description='Adds class "diagonal" to the smart-layout container.',
    css_mechanism="class",
    css_target='.smart-layout[data-variant="diamondGrid"].diagonal',
    reason="Three- and five-item diamond grids alternate into a diagonal flow to prevent repeated vertical stacks.",
    breaking_change_risk="medium",
))

_r(RenderingRule(
    name="grid_number_badge_variants",
    family="grid_container",
    condition='variant in {"bigBullets", "cardGrid"}',
    condition_fn=lambda variant=None, **_: variant in {"bigBullets", "cardGrid"},
    effect_description="Emits card-number with the one-based item index.",
    css_mechanism="class",
    css_target='.smart-layout[data-variant="bigBullets"] .card-number, .smart-layout[data-variant="cardGrid"] .card-number',
    reason="Big bullets and numbered card grids use ordered badges as the main scanning cue.",
    breaking_change_risk="medium",
))

_r(RenderingRule(
    name="grid_solid_box_default_icons",
    family="grid_container",
    condition='variant == "solidBoxesWithIconsInside" and not item.icon',
    condition_fn=lambda variant=None, item=None, **_: variant == "solidBoxesWithIconsInside" and not _has_icon(item=item),
    effect_description="Chooses a rotating default icon from the solid-box icon palette.",
    css_mechanism="class",
    css_target='.smart-layout[data-variant="solidBoxesWithIconsInside"] .card-icon',
    reason="The solid-box layout expects every tile to have an icon for its visual rhythm.",
    breaking_change_risk="medium",
))

# conceptual_relational

_r(RenderingRule(
    name="conceptual_generic_icon_enabled",
    family="conceptual_relational",
    condition='variant not in {"relationshipMap"}',
    condition_fn=lambda variant=None, **_: variant != "relationshipMap",
    effect_description="Enables generic card-icon rendering for conceptual variants other than relationshipMap.",
    css_mechanism="class",
    css_target=".card-icon",
    reason="Most conceptual layouts can use generic icon boxes, while relationshipMap reserves icon semantics for connectors.",
    breaking_change_risk="medium",
))

_r(RenderingRule(
    name="conceptual_relationship_connector",
    family="conceptual_relational",
    condition='variant == "relationshipMap" and index < 2',
    condition_fn=lambda variant=None, index=0, **_: variant == "relationshipMap" and index < 2,
    effect_description="Emits relationship-connector with a RemixIcon arrow between the first two cards.",
    css_mechanism="class",
    css_target='.smart-layout[data-variant="relationshipMap"] .relationship-connector',
    reason="Only the first two relationship nodes draw connectors to form the intended three-node map flow.",
    breaking_change_risk="medium",
))

_r(RenderingRule(
    name="conceptual_relationship_connector_custom_icon",
    family="conceptual_relational",
    condition='variant == "relationshipMap" and index < 2 and item.icon',
    condition_fn=lambda variant=None, index=0, item=None, **_: variant == "relationshipMap" and index < 2 and _has_icon(item=item),
    effect_description="Uses item.icon.alt for the relationship connector icon.",
    css_mechanism="class",
    css_target=".relationship-connector i",
    reason="RelationshipMap repurposes item icons as connector semantics rather than node icons.",
    breaking_change_risk="low",
))

_r(RenderingRule(
    name="conceptual_relationship_connector_prefix",
    family="conceptual_relational",
    condition='relationshipMap connector icon does not start with "ri-"',
    condition_fn=lambda variant=None, index=0, item=None, **_: variant == "relationshipMap" and index < 2 and _needs_ri_prefix(item=item),
    effect_description="Prefixes bare relationship connector icon names with ri- and appends -line.",
    css_mechanism="class",
    css_target=".relationship-connector i",
    reason="Connector icons use the RemixIcon font and must be normalized when input supplies short names.",
    breaking_change_risk="low",
))

# supporting_contextual

_r(RenderingRule(
    name="supporting_sequential_output_route",
    family="supporting_contextual",
    condition='variant == "sequentialOutput" or block_type == "GyMLSequentialOutput"',
    condition_fn=lambda variant=None, block=None, **_: variant == "sequentialOutput" or _block_type(block=block) == "GyMLSequentialOutput",
    effect_description="Delegates to the sequential_process renderer instead of rendering supporting cards.",
    css_mechanism="class",
    css_target=".sequential-output-container, .output-line",
    reason="Sequential output has terminal-style structure owned by the sequential process family.",
    breaking_change_risk="high",
))

_r(RenderingRule(
    name="supporting_cyclic_process_route",
    family="supporting_contextual",
    condition='block_type == "GyMLCyclicProcessBlock"',
    condition_fn=lambda block=None, **_: _block_type(block=block) == "GyMLCyclicProcessBlock",
    effect_description="Renders cyclic-process-container, cp-items-row, cp-item circles, and SVG arrow overlay.",
    css_mechanism="class",
    css_target=".cyclic-process-container, .cp-items-row, .cp-arrows-overlay",
    reason="Cyclic process blocks need a horizontal row of circular image nodes with overlaid loop arrows.",
    breaking_change_risk="high",
))

_r(RenderingRule(
    name="supporting_cyclic_image_placeholder",
    family="supporting_contextual",
    condition='not img_url or img_url == "null"',
    condition_fn=lambda img_url=None, item=None, **_: not (img_url if img_url is not None else getattr(item, "image_url", None)) or (img_url if img_url is not None else getattr(item, "image_url", None)) == "null",
    effect_description="Emits cp-circle-placeholder with ri-image-line instead of an img tag.",
    css_mechanism="class",
    css_target=".cp-circle-placeholder",
    reason="The circular process layout keeps every step's circle occupied even when no image was generated.",
    breaking_change_risk="medium",
))

_r(RenderingRule(
    name="supporting_cyclic_arc_top",
    family="supporting_contextual",
    condition="i % 2 == 0",
    condition_fn=lambda i=0, index=None, **_: (i if index is None else index) % 2 == 0,
    effect_description="Uses sweep=1 when building the SVG arc path for even-indexed cycle arrows.",
    css_mechanism="class",
    css_target=".cp-arrows-overlay path",
    reason="Alternating top and bottom semicircles prevents the cycle arrows from stacking on one side of the circles.",
    breaking_change_risk="medium",
))

_r(RenderingRule(
    name="supporting_cyclic_arc_bottom",
    family="supporting_contextual",
    condition="i % 2 != 0",
    condition_fn=lambda i=0, index=None, **_: (i if index is None else index) % 2 != 0,
    effect_description="Uses sweep=0 when building the SVG arc path for odd-indexed cycle arrows.",
    css_mechanism="class",
    css_target=".cp-arrows-overlay path",
    reason="Bottom arcs alternate with top arcs to make the cycle direction legible across adjacent circles.",
    breaking_change_risk="medium",
))

# hierarchical_structural

_r(RenderingRule(
    name="hierarchical_tree_route",
    family="hierarchical_structural",
    condition='block_type == "GyMLHierarchyTree"',
    condition_fn=lambda block=None, **_: _block_type(block=block) == "GyMLHierarchyTree",
    effect_description="Renders hierarchy-tree-container using nested tree-node markup instead of smart-layout cards.",
    css_mechanism="class",
    css_target=".hierarchy-tree-container, .tree-node",
    reason="Hierarchy trees need nested list connectors and node boxes to show parent-child structure.",
    breaking_change_risk="high",
))

_r(RenderingRule(
    name="hierarchical_tree_children",
    family="hierarchical_structural",
    condition="node.children",
    condition_fn=lambda node=None, **_: bool(getattr(node, "children", None)),
    effect_description="Emits a nested ul of child li nodes under the current tree-node.",
    css_mechanism="class",
    css_target=".hierarchy-tree-container ul, .hierarchy-tree-container li",
    reason="Nested child lists activate connector lines that communicate hierarchy depth.",
    breaking_change_risk="medium",
))


def validate_rule_registry():
    for name, rule in RULE_REGISTRY.items():
        assert name == rule.name, f"Key mismatch: {name}"
        assert rule.reason, f"Rule {name} has no documented reason"
        assert rule.breaking_change_risk in ("low", "medium", "high"), f"Invalid risk level: {name}"
        assert rule.css_mechanism in ("class", "data_attribute", "inline_style"), f"Invalid mechanism: {name}"


validate_rule_registry()
