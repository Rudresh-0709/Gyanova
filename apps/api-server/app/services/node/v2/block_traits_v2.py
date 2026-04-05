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
    ("smart_layout", "cardGridSimple"): BlockTraitsV2(
        family="smart_layout",
        variant="cardGridSimple",
        tags=("card_grid", "wide_capable"),
        supports_width=("normal", "wide"),
        smart_layout_variant="cardGridSimple",
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
    ("feature_showcase_block", "normal"): BlockTraitsV2(
        family="feature_showcase_block",
        variant="normal",
        tags=("feature_highlight", "image_oriented", "wide_capable"),
        supports_width=("wide",),
        requires_image_prompt=True,
    ),
}
