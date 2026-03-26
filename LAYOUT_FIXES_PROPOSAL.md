# Layout & Visual Variety Fixes Proposal

This proposal aligns with the current analysis in [LAYOUT_LIMITATIONS_ANALYSIS.md](LAYOUT_LIMITATIONS_ANALYSIS.md), including your latest direction:
- keep the solved/acceptable layout concerns out of scope for now
- focus on real creativity bottlenecks that still remain

Scope covers 4 active issues:
1. Intent variant redundancy
2. Timeline monotony
3. Aggressive blank layout logic
4. Narrow narration-technique logic

---

## 1. Fix Intent Variant Redundancy (Primary Priority)

### Problem
`INTENT_VARIANTS` in `apps/api-server/app/services/node/slides/gyml/generator.py` overuses the same families (card/bullet/process) across multiple content angles. This makes different angles look visually similar.

### Target Outcome
- Each angle has a distinct visual signature.
- No family dominates consecutive slides.
- Underused structures become first-class options.

### Concrete Implementation Plan

#### Phase A: Introduce Variant Families
Add a `VARIANT_FAMILIES` map in `generator.py` and tag every variant.

Example families:
- `cards`: cardGridIcon, cardGridSimple, cardGridImage
- `bullets`: bigBullets, bulletIcon, bulletCheck, bulletCross
- `timelines`: timeline, timelineHorizontal, timelineSequential, timelineMilestone, timelineIcon
- `process`: processSteps, processArrow, processAccordion
- `comparison`: comparisonCards, comparisonProsCons, comparisonBeforeAfter
- `data`: stats, statsComparison
- `structure`: hierarchy_tree, hub_and_spoke, diagramFlowchart, diagramHierarchy
- `technical`: table, comparison_table, codeSnippet, codeComparison

Deliverable:
- Helper function `get_variant_family(variant: str) -> str`.

#### Phase B: Rebuild `INTENT_VARIANTS` Pools by Signature
Redefine each content angle so at least 50% of its pool is signature family content.

Signature examples:
- `overview` -> cards + structure
- `mechanism` -> timelines + process
- `comparison` -> comparison + data
- `visualization` -> data + structure
- `teach` -> structure + technical

Rule:
- Keep 1-2 cross-family options per angle for flexibility.

#### Phase C: Add Family-Level Anti-Repetition in `pick_variant`
Current logic only limits exact variants. Add family-level controls:
- `max_same_family_streak = 2`
- if last 2 selected variants are same family, downweight that family heavily
- prefer unseen families in the recent 4-slide window

Pseudo logic:
1. Resolve pool.
2. Build eligible variants (existing max-usage rules).
3. Compute recent family history.
4. Apply family penalties/bonuses.
5. Select weighted variant.

#### Phase D: Add Deterministic Diversity Metrics
After selection, compute and log:
- `family_entropy_last_8`
- `max_family_streak`
- `unique_families_last_8`

Acceptance thresholds:
- `unique_families_last_8 >= 4`
- `max_family_streak <= 2`

### Files to Modify
- `apps/api-server/app/services/node/slides/gyml/generator.py`

### Rollout Strategy
1. Ship behind a feature flag (example: `ENABLE_FAMILY_VARIETY=true`).
2. Compare baseline vs flag-on across 30 generated lessons.
3. Promote to default after thresholds pass.

---

## 2. Enable Horizontal Timeline as a First-Class Variant

### Problem
`timelineHorizontal` exists but is underused and not consistently rendered as a distinct responsive layout.

### Proposed Fix
1. Add `timelineHorizontal` to high-probability pools (`mechanism`, `narrate`, optional `example`).
2. Ensure renderer has dedicated styling for horizontal timeline behavior.
3. Update selection constraints so multiple distinct timeline styles can appear in a lesson without hard suppression.

### Files to Modify
- `apps/api-server/app/services/node/slides/gyml/generator.py`
- `apps/api-server/app/services/node/slides/gyml/renderer.py`

---

## 3. Make Blank Layout Logic Role-Aware

### Problem
`FORCED_BLANK_VARIANTS` can block useful imagery even when a slide has pedagogical reasons to include visual support.

### Proposed Fix
1. Extend `pick_layout` to accept `image_role` explicitly.
2. Apply forcing rule only when appropriate:
- force blank when `image_role == "none"`
- for `image_role == "content"`, never hard-force blank by variant alone
- for `image_role == "accent"`, allow selective blank fallback for dense variants
3. Review/remove over-aggressive entries in `FORCED_BLANK_VARIANTS`.

### Files to Modify
- `apps/api-server/app/services/node/slides/gyml/generator.py`

---

## 4. Expand Narration Technique Inventory and Variation

### Problem
`apps/api-server/app/services/node/narration_techniques.py` uses a small, fixed technique set, causing repetitive cadence and similar narrative flow.

### Proposed Fix
1. Add new technique families:
- comparison-analytic
- process-walkthrough
- evidence-interpretation
- structure-explainer
- misconception-correction
- story-led context
2. Add context-aware selection inputs:
- intent
- difficulty level
- slide position in lesson arc
- recent narration-style history
3. Add anti-repetition rotation:
- prevent same narration family more than 2 times in last 5 slides
- vary segment pattern templates inside each family

### Files to Modify
- `apps/api-server/app/services/node/narration_techniques.py`
- `apps/api-server/app/services/node/slides/gyml/generator.py` (if passing richer narration metadata)

---

## Verification Plan

### Automated Checks
1. Variant-family diversity test:
```bash
python apps/api-server/app/services/node/slides/gyml/test_variants.py
```
Expected:
- `unique_families_last_8 >= 4`
- `max_family_streak <= 2`

2. Timeline rendering regression test:
- verify `timelineHorizontal` desktop and mobile fallback behavior.

3. Blank-layout role test:
- `image_role="content"` should not be auto-forced to blank solely by variant type.

4. Narration rotation test:
- ensure no repeated narration family streak above configured limit.

### Manual Verification
1. Generate 10+ lesson decks from mixed domains (science, history, coding, business).
2. Review each deck for:
- visual family diversity
- timeline style diversity
- narration rhythm diversity
3. Validate that uniqueness improves without reducing clarity.

---

## Success Criteria

This proposal is complete when all are true:
1. Visual repetition is measurably reduced at family level.
2. Horizontal timelines appear regularly where semantically appropriate.
3. Blank layout is applied intentionally, not globally.
4. Narration style feels varied across long lessons while staying pedagogically coherent.
