# Prompt Part 7: Dedicated v2 Planner Module

## Module Created
**File:** `apps/api-server/app/services/node/v2/slide_planner_v2.py` (390+ lines)

## Core Function

```python
def plan_slide_v2(
    teacher_brief: Dict[str, Any],
    state: Dict[str, Any],
    slide_index: int,
) -> Dict[str, Any]
```

## Flow Diagram

```
teacher_brief (3-tier density, intent, scope, image requirements)
    ↓
[1] Map density_tier (low|medium|high) → engine_density (6-tier token)
    ↓
[2] Derive image policy (required|optional|forbidden) & tier (hero|content|accent|none)
    ↓
[3] Derive primary family from teaching_intent + coverage_scope
    ↓
[4] Get template candidates (filtered by primary_family, image_need, density)
    ↓
[5] Select best template using _select_template_with_variety
    └─ Hard rules: disallow_consecutive if enabled
    └─ Penalties: template_penalty, family_penalty, variant_penalty, smart_layout_variant_penalty
    └─ Concept image support check (if required)
    ↓
[6] Select primary family using _select_primary_family_with_variety
    └─ Restricted to template's allowed_primary_families
    └─ Hard rules: family cap (max 2 in last 4 slides)
    └─ Penalties: family_penalty, variant_penalty
    ↓
[7] Compose blocks: primary spec + supporting specs per template density
    └─ Validate primary against template constraints
    └─ Filter supporting by image policy
    └─ Determine has_wide_block
    ↓
[8] Determine image_layout using determine_image_layout_v2
    └─ Density → float mapping for v1 ImageManager
    └─ Dense overrides (force top/bottom for dense+side)
    └─ History-aware corrections (avoid consecutive, rhythm after 2 sides)
    ↓
[9] Build designer_blueprint
    └─ Template metadata
    └─ Primary block blueprint
    └─ Supporting blocks blueprints
    ↓
[10] Compose content_blocks hints
    └─ Include concept_image block if required
    ↓
plan_item (compatible with generate_gyml_v2)
```

## Key Features

### 1. Density Mapping
- Teacher input: "low", "medium", "high" (3-tier)
- Engine output: "ultra_sparse", "sparse", "balanced", "standard", "dense", "super_dense" (6-tier)
- Parity-based alternation by slide index for smooth progression

### 2. Template Selection with Variety Penalties
- **Hard rules**: No consecutive template (if enabled)
- **Penalties**:
  - template_penalty: discourage recent templates
  - family_penalty: discourage recent primary families
  - variant_penalty: discourage recent variants
  - smart_layout_variant_penalty: discourage recent smart_layout variants
- **Concept image awareness**: 3.0x penalty if required but template doesn't support

### 3. Primary Family Selection with Variety Penalties
- **Constraints**: Must be in template's allowed_primary_families
- **Hard rules**: Max 2 same family in last 4 slides (if enabled)
- **Penalties**: Same as above but scoped to family pool
- **Preference**: Prefer requested family if tie

### 4. Block Composition
- Primary block validated against template constraints
- Supporting blocks limited by template.max_supporting_blocks
- Sparse templates allow only 1 supporting block
- Image policy filtering (no content images if forbidden)

### 5. Image Layout Determination (via adapter)
- Maps engine_density to float (0.25–1.25) for v1 ImageManager
- Post-processing:
  - Dense override: force top/bottom for dense+side layouts
  - History-aware correction: avoid consecutive same layout
  - Rhythm enforcement: alternate left/right after 2 consecutive sides

### 6. Output Format (generate_gyml_v2 compatible)
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
    
    # Planning result
    "slide_density": str (engine token),
    "selected_template": str,
    "layout": str (image_layout),
    "image_layout": str,
    "intent": str,
    "designer_blueprint": {
        "template": {...},
        "primary_block": {...},
        "supporting_blocks": [...],
        "image_need": str,
        "image_tier": str,
        "layout": str,
        "primary_family": str,
    },
    "image_need": str,
    "image_tier": str,
    "primary_supports_icons": bool,
    "primary_tags": List[str],
    "contentBlocks": List[Dict] (hints),
}
```

## Teacher Brief Input Structure

```python
{
    # Density and image requirements (teacher-facing)
    "density_tier": "low|medium|high",
    "concept_image_required": bool,
    "concept_image_prompt": str,
    "high_end_image_required": bool,
    
    # Teaching context
    "teaching_intent": str (explain, compare, demo, prove, summarize, narrate, list),
    "coverage_scope": str (foundation, mechanism, application, reinforcement, comparison),
    "title": str,
    "objective": str,
    
    # Content hints
    "must_cover": List[str],
    "key_facts": List[str],
    "formulas": List[str],
    "assessment_prompt": str,
    "research_raw_text": str,
    "factual_confidence": str,
}
```

## State Input Structure

```python
{
    # Histories from previous slides
    "layout_history": List[str],  # format: "template_name|layout"
    "variant_history": List[str],  # format: "family:variant" + "smart_layout:variant"
    
    # Feature flags (hard rules)
    "v2_no_consecutive_template": bool (default=True),
    "v2_family_cap_last4": bool (default=True),
}
```

## Integration Points

### 1. Usage in designer_slide_planning_v2_node
```python
for index, teacher_slide in enumerate(teacher_slides):
    plan = plan_slide_v2(teacher_slide, state, slide_index=index)
    # plan is ready for generate_gyml_v2(plan)
```

### 2. Output to generate_gyml_v2
```python
plan_item = plan_slide_v2(teacher_brief, state, slide_index)
gyml_slide = generate_gyml_v2(plan_item)
```

### 3. History Updates After Generation
```python
layout_history.append(f"{plan['selected_template']}|{plan['layout']}")
variant_history.append(f"{primary_family}:{variant}")
variant_history.extend(smart_layout_variant_tokens)
```

## Validation Results

✓ Syntax validation passed  
✓ Test 1: Low-density planning (sparse engine density)  
✓ Test 2: Medium-density with concept image (required content image)  
✓ Test 3: High-density with formula (dense engine density)  
✓ Test 4: Planning with history (variety penalties applied)  

## No Breaking Changes

- Does not modify BlockSpec, TemplateSpec, or BLOCK_CATALOG
- Does not modify existing v1 ImageManager
- Does not modify existing v1 image_generator or icon_selector
- Feature-flagged via caller discretion (not mandatory in existing nodes)

## Next Steps

1. **Wire into designer_slide_planning_v2_node**: Replace hardcoded planning with plan_slide_v2 calls
2. **Integrate image_manager_adapter_v2 in content_generation_v2_node**: Use determine_image_layout_v2 for deterministic layout selection
3. **Integrate media_enricher_v2 in content_generation_v2_node**: Generate images and fill icons after GyML generation
4. **End-to-end testing**: Full pipeline with real v1 generation services

---

**Context:** Prompt Part 7 of v2 infrastructure modernization.  
**Related:** Prompts 1–6 (density mapping, traits registries, variety policy, image adapter, media enricher).  
**Status:** Complete and validated.  
