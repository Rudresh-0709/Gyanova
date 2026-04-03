# slide_planner_v2 API Reference

## Main Function

### `plan_slide_v2(teacher_brief, state, slide_index) → Dict[str, Any]`

Single-slide planning orchestrator. Consolidates density mapping, template/family selection with variety penalties, block composition, and image layout determination.

**Arguments:**
- `teacher_brief: Dict[str, Any]` – Teacher's slide specification
- `state: Dict[str, Any]` – Planner state with histories and feature flags
- `slide_index: int` – Zero-based slide position (used for parity-based density alternation)

**Returns:** `Dict[str, Any]` plan_item compatible with `generate_gyml_v2(plan_item)`

---

## Input Types

### Teacher Brief Keys

```python
{
    # Density tier (teacher-facing 3-tier)
    "density_tier": "low" | "medium" | "high",
    
    # Image requirements
    "concept_image_required": bool,
    "concept_image_prompt": str | None,  # optional, ignored if concept_image_required=False
    "high_end_image_required": bool,
    
    # Teaching context
    "teaching_intent": "explain" | "compare" | "demo" | "prove" | "summarize" | "narrate" | "list",
    "coverage_scope": "foundation" | "mechanism" | "application" | "reinforcement" | "comparison",
    "title": str,
    "objective": str,
    
    # Content hints for GyML generation
    "must_cover": List[str] | None,
    "key_facts": List[str] | None,
    "formulas": List[str] | None,
    "assessment_prompt": str | None,
    "research_raw_text": str | None,
    "factual_confidence": "high" | "medium" | "low" | None,
}
```

### State Keys

```python
{
    # Histories from previous slides (for variety penalties)
    "layout_history": List[str],  # ["template_name|layout", ...], can be empty
    "variant_history": List[str],  # ["family:variant", "smart_layout:variant", ...], can be empty
    
    # Feature flags (hard rules for variety)
    "v2_no_consecutive_template": bool,  # default=True, prevents same template twice in a row
    "v2_family_cap_last4": bool,  # default=True, prevents same family >2 times in last 4 slides
}
```

---

## Output Type

### plan_item (Dict[str, Any])

```python
{
    # Teacher input pass-through
    "title": str,
    "objective": str,
    "teaching_intent": str,
    "coverage_scope": str,
    "must_cover": List[str],
    "key_facts": List[str],
    "formulas": List[str],
    "assessment_prompt": str,
    "research_raw_text": str,
    "factual_confidence": str,
    "high_end_image_required": bool,
    "concept_image_required": bool,
    "concept_image_prompt": str,
    
    # Planning results
    "slide_density": str,  # engine token: "ultra_sparse"|"sparse"|"balanced"|"standard"|"dense"|"super_dense"
    "selected_template": str,  # template name from TEMPLATE_REGISTRY
    "layout": str,  # "top"|"left"|"right"|"bottom"|"blank"
    "image_layout": str,  # same as "layout", alias for generate_gyml_v2
    "intent": str,  # same as teaching_intent
    
    # Designer blueprint (metadata for generators)
    "designer_blueprint": {
        "template": {
            "name": str,
            "is_sparse": bool,
            "image_mode_capability": "hero"|"accent"|"content"|"none",
            "image_mode_required": str | None,
            "max_blocks": int,
            "max_supporting_blocks": int,
            "allowed_primary_families": List[str],
            "allowed_accent_placements": List[str],
            "allowed_layouts": List[str],
            "supports_high_end_image": bool,
        },
        "primary_block": {
            "family": str,
            "variant": str,
            "width_class": str,
            "has_content_image": bool,
            "is_primary_candidate": bool,
        },
        "supporting_blocks": List[{family, variant, width_class, has_content_image, is_primary_candidate}],
        "image_need": "required"|"optional"|"forbidden",
        "image_tier": "hero"|"content"|"accent"|"none",
        "layout": str,
        "primary_family": str,
    },
    
    # Image metadata
    "image_need": "required"|"optional"|"forbidden",
    "image_tier": "hero"|"content"|"accent"|"none",
    
    # Block capability hints
    "primary_supports_icons": bool,
    "primary_tags": List[str],  # e.g., ["icon_oriented", "wide_capable", ...]
    
    # Content block hints (for generate_gyml_v2)
    "contentBlocks": [
        {
            "type": "image",
            "imagePrompt": str,
            "is_accent": False,  # if concept_image_required
        },
        ...
    ],
}
```

---

## Internal Helper Functions

### `_derive_image_policy(density, concept_image_required, high_end_image_required) → Tuple[str, str]`

Derives image_need and image_tier from density and requirements.

**Returns:** `(image_need, image_tier)` where:
- `image_need ∈ {"required", "optional", "forbidden"}`
- `image_tier ∈ {"hero", "content", "accent", "none"}`

### `_derive_primary_family(teacher_brief) → str`

Maps teaching_intent and coverage_scope to primary block family.

**Returns:** Family name safe for BLOCK_CATALOG lookup (e.g., "overview", "process", "formula", "comparison", "recap")

### `_compose_planned_blocks(...) → Tuple[BlockSpec, List[BlockSpec], bool]`

Selects primary and supporting blocks respecting template constraints.

**Returns:** `(primary_spec, supporting_specs, has_wide_block)`

### `_select_template_with_variety(...) → TemplateSpec`

Selects best template using variety penalties and hard rules.

**Key features:**
- Hard rule: disallow_consecutive (if enabled) → prevents same template twice in a row
- Penalties applied: template_penalty, family_penalty, variant_penalty, smart_layout_variant_penalty
- Concept image awareness: 3.0x penalty if required but template doesn't support
- Returns: Lowest-penalty TemplateSpec

### `_select_primary_family_with_variety(...) → str`

Selects best primary family restricted to template's allowed_primary_families.

**Key features:**
- Hard rule: family_cap (if enabled) → max 2 same family in last 4 slides
- Penalties applied: family_penalty, variant_penalty
- Preference for requested_family if tie
- Returns: Best family name

---

## Imports Required

```python
# From v2 infrastructure built in Prompts 1–6
from app.services.node.v2.density_mapping_v2 import map_brief_density_to_engine
from app.services.node.v2.block_catalog_v2 import (
    BLOCK_CATALOG, BlockSpec, block_to_blueprint,
    select_primary_block, select_supporting_blocks,
)
from app.services.node.v2.template_registry_v2 import (
    TEMPLATE_REGISTRY, TemplateSpec,
    candidate_templates, get_template_spec, template_allows_layout,
)
from app.services.node.v2.variety_policy_v2 import (
    family_allowed_by_hard_rule, family_penalty,
    smart_layout_variant_penalty, template_allowed_by_hard_rule,
    template_penalty, variant_penalty,
)
from app.services.node.v2.block_traits_v2 import BLOCK_TRAITS, BlockTraitsV2
from app.services.node.v2.template_traits_v2 import TEMPLATE_TRAITS, TemplateTraitsV2
from app.services.node.v2.image_manager_adapter_v2 import determine_image_layout_v2
```

---

## History Token Formats

After planning and generation, caller should update histories with:

### layout_history
Format: `"{template_name}|{image_layout}"`

Example: `["Title with bullets|top", "Image and text|left", "Feature showcase block|blank"]`

### variant_history
Format: `"{family}:{variant}"` for primary blocks + `"smart_layout:{variant}"` for smart_layout blocks

Example: `["overview:normal", "example:normal", "smart_layout:cardGridIcon", "comparison:wide"]`

---

## Density Mapping Reference

| Teacher Tier | Engine Token (Parity 0) | Engine Token (Parity 1) |
|---|---|---|
| low | sparse (0.45) | ultra_sparse (0.25) |
| medium | balanced (0.65) | standard (0.90) |
| high | dense (1.05) | super_dense (1.25) |

- Parity = `slide_index % 2`
- Floats used by v1 ImageManager for image layout selection
- Engine tokens used throughout v2 planning and generation

---

## Example Usage

```python
from app.services.node.v2.slide_planner_v2 import plan_slide_v2
from app.services.node.v2.gyml_generator_v2 import generate_gyml_v2

# Plan the slide
teacher_input = {
    "density_tier": "medium",
    "concept_image_required": True,
    "concept_image_prompt": "Visual representation of photosynthesis",
    "teaching_intent": "teach",
    "coverage_scope": "mechanism",
    "title": "The Photosynthesis Process",
    "objective": "Students understand how plants convert light to chemical energy",
    "must_cover": ["sunlight", "chlorophyll", "glucose", "oxygen"],
    "key_facts": ["Plants capture light energy"],
    "formulas": [],
    "assessment_prompt": "What are the inputs and outputs of photosynthesis?",
    "research_raw_text": "Photosynthesis converts light energy to chemical energy...",
    "factual_confidence": "high",
}

state = {
    "layout_history": ["Title card|top"],
    "variant_history": ["title:normal", "overview:normal"],
    "v2_no_consecutive_template": True,
    "v2_family_cap_last4": True,
}

plan = plan_slide_v2(teacher_input, state, slide_index=1)

# Generate GyML from plan
gyml_slide = generate_gyml_v2(plan)

# Update histories for next slide
state["layout_history"].append(f"{plan['selected_template']}|{plan['layout']}")
state["variant_history"].append(f"{plan['designer_blueprint']['primary_family']}:normal")
```

---

## Testing

**File:** `apps/api-server/app/services/node/v2/test_slide_planner_v2.py`

**Tests included:**
1. Low-density planning (sparse engine density)
2. Medium-density with concept image (content image required)
3. High-density with formula (dense engine density)
4. Variety penalties with history accumulation

**Run:** 
```bash
python apps/api-server/app/services/node/v2/test_slide_planner_v2.py
```

---

## Status

✓ Implemented  
✓ Syntax validated  
✓ Unit tests pass  
✓ Ready for integration into designer_slide_planning_v2_node  
✓ No modifications to existing BlockSpec, TemplateSpec, v1 ImageManager  

**Integration required:** Wire plan_slide_v2 calls into designer_slide_planning_v2_node to replace hardcoded planning logic.
