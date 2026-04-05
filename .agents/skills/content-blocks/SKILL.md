---
name: "gyanova-content-blocks"
description: "Guide for creating, extending, and wiring content blocks in the Gyanova v2 slide generation engine. Covers BlockSpec, BlockTraits, BLOCK_CATALOG, smart_layout variants, template compatibility, density rules, and variety policy."
version: 1.0.0
tags:
  - gyanova
  - slides
  - content-blocks
  - gyml
  - v2
---

# Gyanova Content Blocks Skill

This skill covers everything you need to know to **add, modify, or audit content blocks** in the Gyanova v2 slide engine.

---

## Architecture Overview

Content blocks flow through four interconnected layers:

```
1. BlockSpec (block_catalog_v2.py)        ← What blocks exist + their metadata
2. BlockTraitsV2 (block_traits_v2.py)     ← Renderer-level traits (icons, image prompts)
3. TemplateSpec (template_registry_v2.py) ← How templates host blocks
4. GyML Renderer (slides/gyml/renderer.py)← How blocks become HTML
```

The designer node (`designer_slide_planning_v2_node.py`) selects blocks at plan time. The generator (`gyml_generator_v2.py`) serializes the plan into a JSON payload the renderer consumes.

---

## 1. BlockSpec — The Block Catalog

**File:** `apps/api-server/app/services/node/v2/block_catalog_v2.py`

### The `BlockSpec` dataclass

```python
@dataclass(frozen=True)
class BlockSpec:
    family: str                          # Logical family name (e.g. "smart_layout", "formula")
    variant: str                         # Variant within family (e.g. "bigBullets", "normal")
    width_class: str                     # "wide" or "normal"
    has_content_image: bool = False      # Block contains an embedded image slot
    implies_content_image: bool = False  # Block REQUIRES generating an image prompt
    density_ok: Tuple[str, ...] = ()     # Density levels this block is valid for
    is_primary_candidate: bool = True    # Is this eligible as a slide's primary block?
    smart_layout_variant: str = ""       # The GyML renderer variant string
    intent_fit: Tuple[str, ...] = ()     # Teaching intents this block naturally fits
```

### Block Families

| Family | Role | Notes |
|---|---|---|
| `smart_layout` | Rich structured primary blocks | Most common; mapped to a GyML variant |
| `title` | Hero title slides | `ultra_sparse` to `balanced` only |
| `overview` | Intro overview panels | Wide; multiple variants |
| `definition` | Concept definition | `ultra_sparse` to `balanced` |
| `formula` | Math/science formulas | Renders KaTeX via `formula_block` |
| `recap` | Summary/recap panels | Maps to `numbered_list` |
| `process` | Legacy alias for process steps | Maps to `processSteps` or `processArrow` |
| `comparison` | Legacy alias for comparisons | Maps to `comparisonProsCons` |
| `supporting_text` | Non-primary paragraph | Not a primary candidate |
| `supporting_callout` | Non-primary callout box | Not a primary candidate |
| `supporting_image` | Non-primary image | Requires image prompt |
| `concept_image` | Primary block; full-image slide | Requires image prompt |

### smart_layout Variants Reference

#### Bullets
| Variant | Description | Best Density |
|---|---|---|
| `bigBullets` | Large numbered bullet list | `ultra_sparse` → `standard` |
| `bulletIcon` | Bullets with RemixIcons | `sparse` → `standard` |
| `bulletCheck` | Checkmark list | `sparse` → `standard` |

#### Timelines
| Variant | Description | Best Density |
|---|---|---|
| `timeline` | Vertical event timeline | `sparse` → `dense` |
| `timelineIcon` | Timeline with icons | `sparse` → `standard` |
| `timelineHorizontal` | Horizontal alternating timeline | `sparse` → `standard` |
| `timelineSequential` | Numbered sequential steps | `balanced` → `dense` |

#### Card Grids
| Variant | Description | Has Image | Best Density |
|---|---|---|---|
| `cardGrid` | Default numbered cards | No | `sparse` → `standard` |
| `cardGridIcon` | Cards with RemixIcons | No | `sparse` → `standard` |
| `cardGridSimple` | Minimalist heading+text cards | No | `ultra_sparse` → `balanced` |
| `cardGridImage` | Cards with embedded images | **Yes** | `ultra_sparse` → `balanced` |

#### Process / Steps
| Variant | Description | Best Density |
|---|---|---|
| `processSteps` | Vertical steps with arrows | `sparse` → `dense` |
| `processArrow` | Interlocking arrow flow | `balanced` → `dense` |
| `processAccordion` | Expandable step panels | `standard` → `super_dense` |

#### Comparisons
| Variant | Description | Best Density |
|---|---|---|
| `comparisonProsCons` | Two-sided pros/cons cards | `balanced` → `dense` |
| `comparisonBeforeAfter` | Before → After cards | `balanced` → `standard` |

#### Stats
| Variant | Description | Best Density |
|---|---|---|
| `stats` | Large number display | `sparse` → `standard` |
| `statsComparison` | Side-by-side stat comparison | `balanced` → `standard` |

### Intent → Scope → Variant Mapping

The `_INTENT_SCOPE_TO_VARIANT` dict drives automatic variant selection:

```python
(teaching_intent, coverage_scope) → smart_layout_variant

("narrate", "sequence")    → "timeline"
("narrate", "mechanism")   → "timelineSequential"
("teach",   "mechanism")   → "processSteps"
("teach",   "application") → "processArrow"
("demo",    "mechanism")   → "processArrow"
("demo",    "application") → "processAccordion"
("compare", "comparison")  → "comparisonProsCons"
("explain", "foundation")  → "bigBullets"
("explain", "overview")    → "cardGridIcon"
("prove",   "data")        → "stats"
("prove",   "comparison")  → "statsComparison"
```

---

## 2. BlockTraitsV2 — Renderer Traits

**File:** `apps/api-server/app/services/node/v2/block_traits_v2.py`

Traits supplement `BlockSpec` with renderer-level information:

```python
@dataclass(frozen=True)
class BlockTraitsV2:
    family: str
    variant: str
    tags: tuple[str, ...]              # Semantic tags (e.g. "icon_oriented", "wide_capable")
    supports_width: tuple[str, ...]    # Width classes supported
    requires_image_prompt: bool        # Must generate an imagePrompt
    supports_icons: bool               # Can receive ri-* icon names
    smart_layout_variant: str | None   # GyML variant string
```

### Trait Tags
- `card_grid` — Grid-style card layout
- `icon_oriented` — Requires/supports RemixIcon names
- `wide_capable` — Can span full width
- `image_oriented` — Requires an image prompt for generation
- `cycle` — Circular flow layout
- `flow` — Linear flow/sequence layout
- `step_sequence` — Ordered step sequence
- `feature_highlight` — Central hub with orbiting feature cards

---

## 3. Density System

**File:** `apps/api-server/app/services/node/v2/density_mapping_v2.py`

### Density Levels (coarse → engine)

| Engine Level | Meaning | Typical Items |
|---|---|---|
| `ultra_sparse` | Single concept, max visual impact | 2 |
| `sparse` | Light content, breathing room | 2–3 |
| `balanced` | Standard teaching slide | 3–4 |
| `standard` | Slightly denser, more detail | 4–5 |
| `dense` | Heavy content, multi-point | 5–6 |
| `super_dense` | Accordion/structured data | 5–6 |

### Coarse Input Aliases
| Input | Maps To |
|---|---|
| `low` | `sparse` / `ultra_sparse` (alternates by slide index) |
| `medium` | `balanced` / `standard` |
| `high` | `dense` / `super_dense` |

### Image Policy from Density
```python
density in {"ultra_sparse", "sparse", "balanced"} → image_need="optional", image_tier="accent"
density in {"standard", "dense", "super_dense"}    → image_need="forbidden", image_tier="none"
high_end_image_required=True                       → image_need="required",  image_tier="hero"
```

---

## 4. Template Registry

**File:** `apps/api-server/app/services/node/v2/template_registry_v2.py`

### `TemplateSpec` Fields

```python
name: str                                    # Display name (used as key)
is_sparse: bool                              # True = title/formula/large-bullet only
image_mode_capability: str                   # "hero" | "content" | "accent" | "none"
image_mode_required: str | None              # Force image tier when set
max_blocks: int                              # Hard cap on total content blocks
max_supporting_blocks: int                   # Cap on non-primary blocks
allowed_primary_families: Tuple[str, ...]    # Which block families are allowed as primary
allowed_accent_placements: Tuple[str, ...]   # Where accent images can sit
allowed_layouts: Tuple[str, ...]             # Valid image_layout values
supports_high_end_image: bool                # Eligible for hero image generation
density_ok: Tuple[str, ...]                  # Valid density levels
preferred_smart_layout_variants: Tuple[str, ...]  # Scorer-boosted variants
```

### Template → Best Smart Layout Variant Mapping

| Template | Preferred Variants |
|---|---|
| Title card | any |
| Title with bullets | bigBullets, bulletIcon, bulletCheck |
| Image and text | bigBullets, cardGridSimple, cardGridImage |
| Two columns | comparisonProsCons, comparisonBeforeAfter |
| Comparison table | comparisonProsCons, statsComparison |
| Timeline | timeline, timelineIcon, timelineHorizontal, timelineSequential |
| Icons with text | cardGridIcon, bulletIcon, processSteps |
| Card grid | cardGrid, cardGridIcon, cardGridSimple |
| Process arrow block | processArrow, processSteps |
| Process steps | processSteps, processArrow, processAccordion |
| Stats block | stats, statsComparison |
| Feature showcase block | cardGridIcon, processSteps, bigBullets |

---

## 5. Variety Policy

**File:** `apps/api-server/app/services/node/v2/variety_policy_v2.py`

The variety policy is **purely functional** — it never mutates state. All functions return penalties or bonuses.

### Constants
```python
RECENT_WINDOW = 4            # Inspect last 4 slides
PENALTY_IMMEDIATE_REPEAT = 30  # Used immediately before → heavy penalty
PENALTY_RECENT_REPEAT = 15    # Used within window → moderate penalty
BONUS_FRESH = 10              # Not used in window → bonus
```

### Key Functions

| Function | Purpose |
|---|---|
| `score_against_history(candidate, history)` | Returns penalty for repeating a candidate |
| `fresh_bonus(candidate, history)` | Returns bonus if candidate is fresh |
| `pick_smart_layout_variant(preferred, allowed, history)` | Picks freshest best variant |
| `pick_layout(allowed, layout_history, image_need, density)` | Picks freshest best layout |
| `rank_templates(candidates, variant_history)` | Re-ranks templates by variety score |

---

## 6. Content Generation JSON Schema

**File:** `apps/api-server/app/services/node/v2/gyml_generator_v2.py`

The LLM must return this JSON structure:

```json
{
  "title": "Slide Title",
  "subtitle": "Optional subtitle or null",
  "intent": "introduce|explain|teach|compare|demo|prove|summarize|narrate|list",
  "layout": "right|left|top|bottom|blank",
  "image_layout": "right|left|top|bottom|blank",
  "primary_block_index": 0,
  "accentImagePrompt": "Optional: only if image_tier=accent",
  "heroImagePrompt": "Optional: only if image_tier=hero",
  "contentBlocks": [
    {
      "type": "smart_layout",
      "variant": "cardGridIcon",
      "items": [
        {
          "heading": "Short heading (max 60 chars)",
          "description": "1–2 sentence description",
          "icon_name": "ri-lightbulb-line"
        }
      ]
    }
  ]
}
```

### Valid `contentBlocks` Types

| `type` | Primary? | Key Fields |
|---|---|---|
| `smart_layout` | ✅ | `variant`, `items[].{heading, description, icon_name}` |
| `comparison_table` | ✅ | `headers[]`, `rows[][]`, `caption` |
| `key_value_list` | ✅ | `items[].{key, value}` |
| `numbered_list` | ✅ | `items[].{title, description}` |
| `formula_block` | ✅ | `expression`, `variables[].{name, meaning}`, `example` |
| `process_arrow_block` | ✅ | `items[].{label, description, imagePrompt, color}` |
| `cyclic_process_block` | ✅ | `items[].{label, description, imagePrompt, icon_name}` |
| `rich_text` | ✅ | `paragraphs[]` |
| `heading` | ❌ | `level`, `text` |
| `paragraph` | ❌ | `text` |
| `intro_paragraph` | ❌ | `text` |
| `annotation_paragraph` | ❌ | `text` |
| `outro_paragraph` | ❌ | `text` |
| `caption` | ❌ | `text` |
| `image` | ❌ | `src`, `alt`, `is_accent` |

### Hard Rules (from generator prompt)
1. Return ONLY valid JSON — no markdown fences, no explanation.
2. Include exactly **one** structured primary block (the one at `primary_block_index`).
3. **Never** include two `smart_layout` blocks.
4. Max **7 content blocks** per slide. Primary carries 70% visual weight.
5. Block ordering: `[optional intro_paragraph] → PRIMARY BLOCK → [optional callout/annotation]`.
6. Do not mix `accentImagePrompt` with embedded image prompts inside blocks.
7. Respect `image_need` and `image_tier` from the plan.

---

## 7. How to Add a New Content Block

### Step 1 — Add a `BlockSpec` to `BLOCK_CATALOG`

```python
# block_catalog_v2.py
("smart_layout", "myNewVariant"): BlockSpec(
    family="smart_layout",
    variant="myNewVariant",
    width_class="wide",
    density_ok=("balanced", "standard"),
    is_primary_candidate=True,
    smart_layout_variant="myNewVariant",
    intent_fit=("explain", "teach"),
),
```

### Step 2 — Add `BlockTraitsV2` (if renderer-specific traits needed)

```python
# block_traits_v2.py
("smart_layout", "myNewVariant"): BlockTraitsV2(
    family="smart_layout",
    variant="myNewVariant",
    tags=("card_grid", "icon_oriented", "wide_capable"),
    supports_width=("normal", "wide"),
    supports_icons=True,
    smart_layout_variant="myNewVariant",
),
```

### Step 3 — Wire into `_INTENT_SCOPE_TO_VARIANT` (optional)

```python
# block_catalog_v2.py
("explain", "new_scope"): "myNewVariant",
```

### Step 4 — Add to relevant `TemplateSpec.preferred_smart_layout_variants`

```python
# template_registry_v2.py
"Some Template": TemplateSpec(
    ...
    preferred_smart_layout_variants=("existingVariant", "myNewVariant"),
),
```

### Step 5 — Add CSS to the renderer

```python
# slides/gyml/renderer.py → _get_gamma_styles()
# Add CSS class rules for .smart-layout[data-variant="myNewVariant"]
```

### Step 6 — Add the `type` to `_STRUCTURED_PRIMARY_TYPES` if it's a new non-smart_layout block type

```python
# gyml_generator_v2.py
_STRUCTURED_PRIMARY_TYPES = {
    ...
    "my_new_block_type",
}
```

### Step 7 — Handle in `_slide_to_section()` and `_validate_payload()`

Add the new block type string to the allowed set in `_validate_payload` and add deserialization logic in `_slide_to_section`.

---

## 8. Best Practices

### Block Selection
- **Never hardcode variants in prompts** — always resolve through `get_smart_layout_variant(intent, scope)` and then pass through `pick_smart_layout_variant()` for variety.
- **Always check `density_ok`** before selecting a block. A `processAccordion` on a `sparse` slide will overflow.
- **`cardGridImage` and `supporting_image` imply image generation** — only use when `image_need != "forbidden"`.
- **At most one `smart_layout` per slide.** This is a hard constraint validated at render time.

### Density Discipline
- `ultra_sparse` / `sparse` → simple blocks (bigBullets, cardGridSimple, title/overview).
- `balanced` / `standard` → the widest variety is available; most blocks work.
- `dense` / `super_dense` → prefer `processAccordion`, `comparison_table`, `timelineSequential`; avoid image-heavy blocks.

### Image Policy
- **`hero` tier** (high-end images): Use `Title card` or `Feature showcase block`. Only one per lesson.
- **`accent` tier** (standard AI images): Use sidebar (`left`, `right`) or banner (`top`, `bottom`) layouts. Remove from `supporting_specs` if primary is also generating images.
- **`none` tier**: Force `layout="blank"`. Strip all image prompts from payload.
- Never mix `accentImagePrompt` at root level with `imagePrompt` inside `process_arrow_block` items on the same slide.

### Variety Policy
- Append both the **template name** AND the **smart_layout variant** to `local_variant_history` after each slide.
- Append the **layout** to `local_layout_history`.
- Use `pick_smart_layout_variant()` and `pick_layout()` — never select variants raw.
- History window is 4 slides; an immediate repeat is penalized 30 points.

### LLM Prompting
- Always inject `primary_block_instruction` into the prompt — the LLM **must** be told which block type and variant to use.
- Cap `research_context` at 800 characters in the prompt to stay within token limits.
- Always include the `SMART LAYOUT VARIANT REFERENCE` section in the prompt so the LLM knows valid names.
- If LLM returns invalid JSON, fall back to `_build_fallback_slide(plan_item)`.
- Even after LLM generation, always call `_enforce_structured_primary()` to guarantee at least one structured block exists.

### Validation Chain
The correct sequence is always:
```
LLM output → _validate_payload() → _enforce_structured_primary() → _validate_with_existing_validator()
```
If the existing validator fails, use `_build_fallback_slide()` and attach `validation_errors` to the payload for debugging.

---

## 9. Quick Reference: File Locations

| Purpose | File |
|---|---|
| Block catalog + selection logic | `apps/api-server/app/services/node/v2/block_catalog_v2.py` |
| Renderer-level block traits | `apps/api-server/app/services/node/v2/block_traits_v2.py` |
| Template definitions | `apps/api-server/app/services/node/v2/template_registry_v2.py` |
| Variety scoring | `apps/api-server/app/services/node/v2/variety_policy_v2.py` |
| Density mapping | `apps/api-server/app/services/node/v2/density_mapping_v2.py` |
| Designer planning node | `apps/api-server/app/services/node/v2/designer_slide_planning_v2_node.py` |
| GyML generator (LLM + fallback) | `apps/api-server/app/services/node/v2/gyml_generator_v2.py` |
| GyML HTML renderer + block CSS | `apps/api-server/app/services/node/slides/gyml/renderer.py` |
| GyML type definitions | `apps/api-server/app/services/node/slides/gyml/definitions.py` |
| Structural validator | `apps/api-server/app/services/node/slides/gyml/validator.py` |
