from dataclasses import dataclass

@dataclass(frozen=True)
class ItemCountProfile:
    item_range: tuple[int, int]
    layout_variant: str
    height_class: str          # "full" | "compact" | "flexible"
    width_class: str           # "normal" | "wide"
    supported_layouts: tuple[str, ...]
    combinable: bool
    notes: str

@dataclass(frozen=True)
class BlockSpec:
    family: str
    variant: str
    display_name: str
    density_range: tuple[str, str]
    item_relationship_fit: tuple[str, ...]
    content_structure_fit: tuple[str, ...]
    requires_icons: bool
    is_primary_candidate: bool
    item_count_profiles: tuple[ItemCountProfile, ...]

DENSITY_ORDER = ["ultra_sparse", "sparse", "balanced", "standard", "dense", "super_dense"]

def satisfies_density(block: BlockSpec, density: str) -> bool:
    if density not in DENSITY_ORDER:
        return False
    start, end = block.density_range
    if start not in DENSITY_ORDER or end not in DENSITY_ORDER:
        return False
    return DENSITY_ORDER.index(start) <= DENSITY_ORDER.index(density) <= DENSITY_ORDER.index(end)