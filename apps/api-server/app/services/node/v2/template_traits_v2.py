from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TemplateTraitsV2:
    name: str
    supports_concept_image: bool
    supports_side_image_in_dense: bool = False
    supports_wide_primary: bool = False
    forbidden_if_concept_image: tuple[str, ...] = ()


TEMPLATE_TRAITS: dict[str, TemplateTraitsV2] = {
    "Title card": TemplateTraitsV2(
        name="Title card",
        supports_concept_image=True,
        supports_wide_primary=True,
        forbidden_if_concept_image=("accent",),
    ),
    "Title with bullets": TemplateTraitsV2(
        name="Title with bullets",
        supports_concept_image=False,
        supports_wide_primary=True,
    ),
    "Title with bullets and image": TemplateTraitsV2(
        name="Title with bullets and image",
        supports_concept_image=True,
        supports_wide_primary=True,
        forbidden_if_concept_image=("accent",),
    ),
    "Image and text": TemplateTraitsV2(
        name="Image and text",
        supports_concept_image=True,
        supports_wide_primary=True,
        forbidden_if_concept_image=("accent",),
    ),
    "Text and image": TemplateTraitsV2(
        name="Text and image",
        supports_concept_image=True,
        supports_wide_primary=True,
        forbidden_if_concept_image=("accent",),
    ),
    "Two columns": TemplateTraitsV2(
        name="Two columns",
        supports_concept_image=False,
        supports_wide_primary=True,
    ),
    "Timeline": TemplateTraitsV2(
        name="Timeline",
        supports_concept_image=False,
        supports_wide_primary=True,
    ),
    "Icons with text": TemplateTraitsV2(
        name="Icons with text",
        supports_concept_image=False,
        supports_wide_primary=True,
    ),
    "Large bullet list": TemplateTraitsV2(
        name="Large bullet list",
        supports_concept_image=False,
        supports_wide_primary=True,
    ),
    "Comparison table": TemplateTraitsV2(
        name="Comparison table",
        supports_concept_image=False,
        supports_wide_primary=True,
    ),
    "Formula block": TemplateTraitsV2(
        name="Formula block",
        supports_concept_image=False,
        supports_wide_primary=False,
    ),
    "Process arrow block": TemplateTraitsV2(
        name="Process arrow block",
        supports_concept_image=False,
        supports_wide_primary=True,
    ),
    "Cyclic process block": TemplateTraitsV2(
        name="Cyclic process block",
        supports_concept_image=False,
        supports_wide_primary=True,
    ),
    "Feature showcase block": TemplateTraitsV2(
        name="Feature showcase block",
        supports_concept_image=True,
        supports_side_image_in_dense=True,
        supports_wide_primary=True,
        forbidden_if_concept_image=("accent",),
    ),
}
