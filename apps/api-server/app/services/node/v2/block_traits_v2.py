from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BlockTraitsV2:
    family: str
    variant: str
    tags: tuple[str, ...]
    supports_width: tuple[str, ...]
    requires_image_prompt: bool = False
    supports_icons: bool = False
    smart_layout_variant: str | None = None


BLOCK_TRAITS: dict[tuple[str, str], BlockTraitsV2] = {
    ("supporting_image", "normal"): BlockTraitsV2(
        family="supporting_image",
        variant="normal",
        tags=("concept_image", "image_oriented", "vertical", "wide_capable"),
        supports_width=("normal", "wide"),
        requires_image_prompt=True,
    ),
    ("concept_image", "normal"): BlockTraitsV2(
        family="concept_image",
        variant="normal",
        tags=("concept_image", "image_oriented", "vertical", "wide_capable"),
        supports_width=("normal", "wide"),
        requires_image_prompt=True,
    ),
    ("smart_layout", "bigBullets"): BlockTraitsV2(
        family="smart_layout",
        variant="bigBullets",
        tags=("card_grid", "icon_oriented", "wide_capable"),
        supports_width=("normal", "wide"),
        supports_icons=True,
        smart_layout_variant="bigBullets",
    ),
    ("smart_layout", "cardGridIcon"): BlockTraitsV2(
        family="smart_layout",
        variant="cardGridIcon",
        tags=("card_grid", "icon_oriented", "wide_capable"),
        supports_width=("normal", "wide"),
        supports_icons=True,
        smart_layout_variant="cardGridIcon",
    ),
    ("smart_layout", "cardGridImage"): BlockTraitsV2(
        family="smart_layout",
        variant="cardGridImage",
        tags=("card_grid", "image_oriented", "wide_capable"),
        supports_width=("normal", "wide"),
        requires_image_prompt=True,
        smart_layout_variant="cardGridImage",
    ),
    ("smart_layout", "cardGridSimple"): BlockTraitsV2(
        family="smart_layout",
        variant="cardGridSimple",
        tags=("card_grid", "wide_capable"),
        supports_width=("normal", "wide"),
        smart_layout_variant="cardGridSimple",
    ),
    ("smart_layout", "cardGridDiamond"): BlockTraitsV2(
        family="smart_layout",
        variant="cardGridDiamond",
        tags=("card_grid", "icon_oriented", "wide_capable"),
        supports_width=("normal", "wide"),
        supports_icons=True,
        smart_layout_variant="cardGridDiamond",
    ),
    ("smart_layout", "relationshipMap"): BlockTraitsV2(
        family="smart_layout",
        variant="relationshipMap",
        tags=("flow", "icon_oriented", "wide_capable"),
        supports_width=("wide",),
        supports_icons=True,
        smart_layout_variant="relationshipMap",
    ),
    ("smart_layout", "ribbonFold"): BlockTraitsV2(
        family="smart_layout",
        variant="ribbonFold",
        tags=("flow", "icon_oriented", "wide_capable"),
        supports_width=("wide",),
        supports_icons=True,
        smart_layout_variant="ribbonFold",
    ),
    ("smart_layout", "statsBadgeGrid"): BlockTraitsV2(
        family="smart_layout",
        variant="statsBadgeGrid",
        tags=("wide_capable",),
        supports_width=("wide",),
        smart_layout_variant="statsBadgeGrid",
    ),
    ("smart_layout", "diamondRibbon"): BlockTraitsV2(
        family="smart_layout",
        variant="diamondRibbon",
        tags=("card_grid", "icon_oriented", "wide_capable"),
        supports_width=("wide",),
        supports_icons=True,
        smart_layout_variant="diamondRibbon",
    ),
    ("smart_layout", "diamondGrid"): BlockTraitsV2(
        family="smart_layout",
        variant="diamondGrid",
        tags=("card_grid", "icon_oriented", "wide_capable"),
        supports_width=("wide",),
        supports_icons=True,
        smart_layout_variant="diamondGrid",
    ),
    ("smart_layout", "diamondHub"): BlockTraitsV2(
        family="smart_layout",
        variant="diamondHub",
        tags=("card_grid", "icon_oriented", "wide_capable"),
        supports_width=("wide",),
        supports_icons=True,
        smart_layout_variant="diamondHub",
    ),
    ("smart_layout", "hubAndSpoke"): BlockTraitsV2(
        family="smart_layout",
        variant="hubAndSpoke",
        tags=("card_grid", "icon_oriented", "wide_capable"),
        supports_width=("wide",),
        supports_icons=True,
        smart_layout_variant="hubAndSpoke",
    ),
    ("smart_layout", "featureShowcase"): BlockTraitsV2(
        family="smart_layout",
        variant="featureShowcase",
        tags=("feature_highlight", "image_oriented", "wide_capable"),
        supports_width=("wide",),
        requires_image_prompt=True,
        smart_layout_variant="featureShowcase",
    ),
    ("smart_layout", "cyclicBlock"): BlockTraitsV2(
        family="smart_layout",
        variant="cyclicBlock",
        tags=("cycle", "icon_oriented", "wide_capable"),
        supports_width=("wide",),
        supports_icons=True,
        smart_layout_variant="cyclicBlock",
    ),
    ("smart_layout", "sequentialOutput"): BlockTraitsV2(
        family="smart_layout",
        variant="sequentialOutput",
        tags=("code", "step_sequence"),
        supports_width=("normal", "wide"),
        smart_layout_variant="sequentialOutput",
    ),
    ("cyclic_process_block", "normal"): BlockTraitsV2(
        family="cyclic_process_block",
        variant="normal",
        tags=("cycle", "icon_oriented", "wide_capable"),
        supports_width=("normal", "wide"),
        supports_icons=True,
    ),
    ("process_arrow_block", "default"): BlockTraitsV2(
        family="process_arrow_block",
        variant="default",
        tags=("flow", "step_sequence", "wide_capable"),
        supports_width=("wide",),
    ),
    ("smart_layout", "processAccordion"): BlockTraitsV2(
        family="smart_layout",
        variant="processAccordion",
        tags=("step_sequence", "dense_capable"),
        supports_width=("normal", "wide"),
        smart_layout_variant="processAccordion",
    ),
    ("smart_layout", "bulletIcon"): BlockTraitsV2(
        family="smart_layout",
        variant="bulletIcon",
        tags=("list", "icon_oriented"),
        supports_width=("normal", "wide"),
        supports_icons=True,
        smart_layout_variant="bulletIcon",
    ),
    ("smart_layout", "bulletCheck"): BlockTraitsV2(
        family="smart_layout",
        variant="bulletCheck",
        tags=("list",),
        supports_width=("normal", "wide"),
        smart_layout_variant="bulletCheck",
    ),
    ("smart_layout", "timelineIcon"): BlockTraitsV2(
        family="smart_layout",
        variant="timelineIcon",
        tags=("timeline", "icon_oriented"),
        supports_width=("normal", "wide"),
        supports_icons=True,
        smart_layout_variant="timelineIcon",
    ),
    ("smart_layout", "timelineHorizontal"): BlockTraitsV2(
        family="smart_layout",
        variant="timelineHorizontal",
        tags=("timeline", "wide_capable"),
        supports_width=("wide",),
        smart_layout_variant="timelineHorizontal",
    ),
    ("smart_layout", "timelineSequential"): BlockTraitsV2(
        family="smart_layout",
        variant="timelineSequential",
        tags=("timeline", "step_sequence"),
        supports_width=("normal", "wide"),
        smart_layout_variant="timelineSequential",
    ),
    ("smart_layout", "processArrow"): BlockTraitsV2(
        family="smart_layout",
        variant="processArrow",
        tags=("step_sequence", "wide_capable"),
        supports_width=("wide",),
        smart_layout_variant="processArrow",
    ),
    ("smart_layout", "comparisonProsCons"): BlockTraitsV2(
        family="smart_layout",
        variant="comparisonProsCons",
        tags=("comparison", "wide_capable"),
        supports_width=("wide",),
        smart_layout_variant="comparisonProsCons",
    ),
    ("smart_layout", "comparisonBeforeAfter"): BlockTraitsV2(
        family="smart_layout",
        variant="comparisonBeforeAfter",
        tags=("comparison", "wide_capable"),
        supports_width=("wide",),
        smart_layout_variant="comparisonBeforeAfter",
    ),
    ("smart_layout", "statsComparison"): BlockTraitsV2(
        family="smart_layout",
        variant="statsComparison",
        tags=("stats", "comparison", "wide_capable"),
        supports_width=("wide",),
        smart_layout_variant="statsComparison",
    ),
    ("feature_showcase_block", "normal"): BlockTraitsV2(
        family="feature_showcase_block",
        variant="normal",
        tags=("feature_highlight", "image_oriented", "wide_capable"),
        supports_width=("wide",),
        requires_image_prompt=True,
    ),
    ("smart_layout", "solidBoxesWithIconsInside"): BlockTraitsV2(
        family="smart_layout",
        variant="solidBoxesWithIconsInside",
        tags=("card_grid", "icon_oriented", "wide_capable"),
        supports_width=("wide",),
        supports_icons=True,
        smart_layout_variant="solidBoxesWithIconsInside",
    ),
}
