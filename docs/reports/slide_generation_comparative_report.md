# GYANova: Comparative Report on the Slide Generation Pipeline

> **Scope:** This document covers the complete slide generation pipeline from user input through to final HTML output. It provides a comparative breakdown of each phase's approach, design choices, trade-offs, and internal mechanisms. No code changes are made as part of this report.

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Architecture: Content-First vs. Script-First](#2-architecture-content-first-vs-script-first)
3. [Phase 1: Planning (The Slide Planner)](#3-phase-1-planning-the-slide-planner)
4. [Phase 2: Content Generation](#4-phase-2-content-generation)
5. [Phase 3: Composition (The Compiler Stage)](#5-phase-3-composition-the-compiler-stage)
6. [Phase 4: Rendering (GyML → HTML)](#6-phase-4-rendering-gyml--html)
7. [The GyML Intermediate Language](#7-the-gyml-intermediate-language)
8. [Visual Block Type Comparison](#8-visual-block-type-comparison)
9. [Layout Variant Comparison by Pedagogical Intent](#9-layout-variant-comparison-by-pedagogical-intent)
10. [Density Tier Comparison](#10-density-tier-comparison)
11. [Theme System Comparison](#11-theme-system-comparison)
12. [End-to-End Data Flow](#12-end-to-end-data-flow)
13. [Comparative Summary: Key Design Trade-offs](#13-comparative-summary-key-design-trade-offs)

---

## 1. System Overview

GYANova is an AI-powered educational platform that generates fully rendered, narrated, animated slide-based lessons. The complete pipeline transforms a single topic string into HTML slide decks with synchronized audio narration and AI-generated images.

### Technology Stack

| Layer | Technology | Role |
|---|---|---|
| **Frontend** | Next.js 15, React 19, Tailwind CSS, Framer Motion | Slide rendering, student interaction |
| **Backend Orchestration** | FastAPI + LangGraph | Stateful pipeline management, streaming |
| **LLM Providers** | OpenAI GPT-4, Groq, Google Gemini | Content and narration generation |
| **Image Generation** | Leonardo AI | Accent and inline slide images |
| **Text-to-Speech** | ElevenLabs | Narration audio synthesis |
| **Fact Checking** | Tavily Search API | Real-world fact validation |
| **Slide Markup** | GyML (Gyanova Markup Language) | Intermediate layout description language |

### Pipeline Phases at a Glance

```
 User Input (Topic + Level)
         │
         ▼
 ┌───────────────────┐
 │  Phase 1: PLAN    │  new_slide_planner.py
 │  Blueprint Design │  lesson_planning_node.py
 └────────┬──────────┘
          │ Slide Blueprints (JSON)
          ▼
 ┌───────────────────┐
 │  Phase 2: CONTENT │  content_generation_node.py
 │  GyML Generation  │  slides/gyml/generator.py
 └────────┬──────────┘
          │ Raw GyML Content (JSON)
          ▼
 ┌───────────────────┐
 │  Phase 3: COMPOSE │  slides/gyml/composer.py
 │  IR Compilation   │  slides/gyml/serializer.py
 └────────┬──────────┘
          │ ComposedSlide → GyMLSection
          ▼
 ┌───────────────────┐
 │  Phase 4: RENDER  │  rendering_node.py
 │  HTML Generation  │  slides/gyml/renderer.py
 └────────┬──────────┘
          │ HTML5 + CSS + data-segment attributes
          ▼
     Final HTML Slide
```

---

## 2. Architecture: Content-First vs. Script-First

GYANova's most consequential architectural decision is the **Content-First** approach. Understanding it requires comparing it to the alternative.

### Approach A: Script-First (Traditional / Most AI Tools)

```
User Topic
    │
    ▼
LLM generates a spoken script / outline
    │
    ▼
Visual design attempts to match the script
    │
    ▼
Slides end up as "illustrated narration" — visuals echo what's already spoken
```

**Problems with Script-First:**
- Visuals become redundant if they only repeat what narration says
- LLM optimizes for readable prose, not for visual teaching
- Animation synchronization requires retroactive counting of items
- Educational impact is reduced: the slide can't stand on its own

### Approach B: Content-First (GYANova's Design)

```
User Topic
    │
    ▼
LLM generates VISUAL content first (cards, timelines, diagrams)
    │
    ▼
Narration LLM is given the visual and writes audio to EXPLAIN it
    │
    ▼
Narration segments precisely match the number of visual elements
    │
    ▼
Animation syncs perfectly: each visual item is revealed as narrator speaks about it
```

**Advantages of Content-First:**
- Slides are cognitively complete without audio
- Narration adds context, not redundancy
- Animation synchronization is natural and exact
- Visual structures drive pedagogical quality, not afterthought

### Comparison Table

| Dimension | Script-First | Content-First (GYANova) |
|---|---|---|
| **Generation Order** | Script → Visuals | Visuals → Script |
| **Primary Medium** | Audio/Text | Visual Layout |
| **Narration Role** | Primary teaching | Explanation/elaboration |
| **Animation Sync** | Retroactive (hard) | Natural (item count known) |
| **Standalone Slides** | Often incomplete | Always complete |
| **LLM Prompt Focus** | Prose generation | Structural/visual design |
| **Cognitive Redundancy** | High (slides repeat narration) | Low (narration adds value) |

---

## 3. Phase 1: Planning (The Slide Planner)

**Core Files:** `new_slide_planner.py`, `lesson_planning_node.py`

This phase does not generate any content. Its sole purpose is to build a pedagogical blueprint: a structured array of slide metadata describing *what* to teach and *how* to visually represent it.

### 3.1 Planning Inputs

| Input | Source | Example |
|---|---|---|
| `topic` | User | "Computer Generations" |
| `sub_topics` | `sub_topic_node.py` LLM call | "First Generation", "VLSI Era", ... |
| `difficulty` | User | "Beginner", "Intermediate" |
| `teacher_profile` | Config | "Expert Teacher" |

### 3.2 The Template Registry

The planner uses over 40 predefined visual templates grouped by pedagogical category. The LLM must select a `selected_template` from this registry — it cannot invent new types.

| Category | Templates |
|---|---|
| **Hero / Title** | Title card |
| **Text & Explanation** | Title with bullets, Title with bullets and image, Image and text |
| **Columns & Comparisons** | Two columns, Three columns, Four columns, Comparison table |
| **Process & Flow** | Timeline, Arrows, Diagram, Process arrow block |
| **Lists & Summaries** | Icons with text, Large bullet list |
| **Data Layouts** | Column chart, Line chart, Pie chart |
| **Dense Knowledge** | Key-Value list, Rich text, Labeled diagram, Formula block, Split panel |

### 3.3 Blueprint Schema

Each slide blueprint contains these mandatory fields:

```json
{
  "title": "The Vacuum Tube Era",
  "content_angle": "mechanism",
  "intent": "process",
  "purpose": "intuition",
  "selected_template": "Timeline",
  "role": "Interpret",
  "goal": "Explain how vacuum tubes functioned in early computers",
  "reasoning": "A timeline helps visualize chronological development",
  "visual_required": true,
  "visual_type": "image"
}
```

### 3.4 Content Angle Progression

The planner is instructed to build lessons using a structured **angle progression**. This ensures a well-rounded learning arc across a subtopic's slides.

| Angle | Pedagogical Purpose | Common Templates Used |
|---|---|---|
| `overview` | Big picture orientation | Icons with text, Card grid |
| `mechanism` | How things work internally | Timeline, Process arrows |
| `example` | Concrete illustrations | Image + text, Card grid |
| `comparison` | Contrasting concepts | Two columns, Comparison table |
| `application` | Real-world usage | Bullets, Icons |
| `visualization` | Data or quantitative proof | Charts, Stats |
| `summary` | Reinforcement / recap | Large bullet list, Key-Value |

### 3.5 Validation and Diversity Enforcement

After the LLM outputs a raw plan, the Python backend (`lesson_planning_node.py`) runs a multi-step validation gauntlet:

**Step 1 — Angle Inference:** If the LLM hallucinates an unsupported angle, it is inferred from the template name:
```
"Timeline" → mechanism
"Comparison table" → comparison
"Arrows" → mechanism
```

**Step 2 — The Variety Category Enforcer:** Templates are mapped to broad visual categories. A set `used_categories` tracks which have already been used in the current subtopic:

```python
TEMPLATE_CATEGORIES = {
    "Timeline": "timeline",
    "Two columns": "comparison",
    "Comparison table": "comparison",
    "Icons with text": "card",
    "Three columns": "card",
}
```

If the LLM plans two "comparison" category slides in the same subtopic, the second is **rejected**. This guarantees that every 4–7 slides within a subtopic use geometrically distinct visual structures.

**Step 3 — Output Limiting:** Final plans are clamped to between 4 and 7 slides per subtopic to control lesson length.

### 3.6 What Phase 1 Does NOT Produce

At the end of Phase 1, **no actual content exists** — no text, no images, no narration. Only blueprints describing:
- What topic each slide covers
- What visual template to use
- What pedagogical angle to approach from
- Whether an image is required

This strict separation between planning and content generation is a deliberate design decision that improves quality and allows users to confirm or modify the plan before expensive LLM generation begins.

---

## 4. Phase 2: Content Generation

**Core Files:** `content_generation_node.py`, `slides/gyml/generator.py`

This phase reads the blueprints from Phase 1 and converts them into concrete GyML content JSON. It is the most computationally intensive part of the pipeline.

### 4.1 The GyML Content Generator (`generator.py`)

The `GyMLContentGenerator` class manages all LLM interactions for visual content production.

#### Variant Rotation (`pick_variant()`)

Even if two slides have the same `intent` or `content_angle`, they should look different. The variant rotation system prevents visual monotony by curating pools of UI components per angle:

| Angle / Intent | Variant Pool (Ordered) |
|---|---|
| `overview` | `cardGridIcon`, `bigBullets`, `cardGridSimple`, `bulletIcon`, `cardGridImage`, `bulletCheck` |
| `mechanism` / `narrate` | `timelineSequential`, `timelineIcon`, `processArrow`, `processSteps`, `processAccordion`, `timeline` |
| `example` | `cardGridImage`, `cardGridIcon`, `bulletIcon`, `bigBullets`, `cardGridSimple`, `timeline` |
| `comparison` / `compare` | `comparisonCards`, `comparisonProsCons`, `comparisonBeforeAfter`, `statsComparison`, `cardGridSimple` |
| `application` | `cardGridIcon`, `bulletIcon`, `processSteps`, `processArrow`, `bigBullets`, `cardGridImage` |
| `visualization` / `prove` | `stats`, `statsComparison`, `cardGridSimple`, `cardGridIcon`, `bigBullets` |
| `summary` / `summarize` | `bigBullets`, `bulletCheck`, `bulletIcon`, `cardGridSimple`, `cardGridIcon` |
| `list` | `bigBullets`, `bulletCheck`, `processSteps`, `bulletIcon`, `cardGridSimple`, `bulletCross` |
| `teach` | `cardGridIcon`, `processSteps`, `bulletIcon`, `bigBullets`, `cardGridSimple`, `processArrow` |
| `introduce` | `cardGridSimple`, `bigBullets`, `cardGridIcon`, `bulletIcon`, `cardGridImage` |
| `demo` | `processArrow`, `processSteps`, `processAccordion`, `timelineSequential`, `bulletIcon`, `timeline` |
| `explain` (fallback) | `cardGridIcon`, `cardGridSimple`, `bigBullets`, `bulletIcon`, `cardGridImage`, `processSteps` |

**Selection Algorithm:**
1. Look up the pool for `content_angle`; fall back to `intent` if angle is missing.
2. Filter out any variants used in the last 2 slides (`layout_history`).
3. Select deterministically: `variant = fresh_pool[slide_index % len(fresh_pool)]`

This guarantees rotation even within long lesson sequences.

#### Composition Styles (`pick_composition_style()`)

In addition to variant rotation, the **block structure recipe** itself is rotated to prevent every slide from having the same 3-block pattern:

| Style | Block Recipe | Purpose |
|---|---|---|
| `standard` | `intro → PRIMARY → annotation` | Classic teaching pattern |
| `visual_lead` | `PRIMARY → callout` | Immediate visual, minimal text |
| `context_heavy` | `context → PRIMARY` | Establishes WHY before WHAT |
| `minimal` | `PRIMARY only` | Clean, focused slides |
| `bookend` | `callout → PRIMARY → takeaway` | Opens and closes with emphasis |
| `narrative` | `intro → PRIMARY → annotation → outro` | Full four-act structure |

### 4.2 Auto-Balancing Image Layout Engine

The backend overrides LLM choices for image placement using deterministic rules:

```
Rule 1: Slide index == 0 (Intro Slide)
    → image_layout = "behind"   [Full-screen hero image]

Rule 2: Item count > 5 (Dense Content)
    → image_layout = "blank"    [No image; maximize text area]

Rule 3: Wide components (Timelines, Process Arrows)
    → image_layout = "top" (odd index) or "bottom" (even index)
    [Full-width layout avoids sidebars squishing wide content]

Rule 4: Standard Content
    → image_layout = "right" (odd) or "left" (even)
    [Creates visual rhythm as student scrolls through slides]
```

This override prevents the LLM from making poor layout choices (e.g., a sidebar image next to a wide process diagram).

### 4.3 Image Layout Comparison

| Layout | Visual Behavior | Best Use Case |
|---|---|---|
| `right` | Image floats on right; text on left | Standard text + accent image |
| `left` | Image floats on left; text on right | Alternating visual rhythm |
| `top` | Image spans top strip; content below | Wide diagrams (timelines, processes) |
| `bottom` | Image spans bottom strip; content above | Supporting illustration below |
| `behind` | Image fills slide background | Title/intro hero slides |
| `blank` | No image | Dense content; text-heavy slides |

### 4.4 GyML LLM Prompt Structure

The generator crafts a detailed prompt with mandatory directives injected:

```
System Prompt:
  - "You are generating VISUAL content for a slide."
  - "A narration will be generated AFTER to explain your visuals."
  - "DO NOT write narration text — only on-screen labels, headings, descriptions."

Mandatory Directives:
  - Selected variant: "cardGridIcon"      ← fixed, LLM cannot change
  - Image layout: "right"                 ← fixed, LLM cannot change
  - Composition style: "standard"         ← block structure blueprint

Supporting Context:
  - slide title, goal, intent, content_angle
  - composition_history (previous block types used)
  - layout_history (previous variants used)
  - search_context (Tavily fact-check results, if applicable)
  - JSON schema to produce valid output
```

### 4.5 Fact-Checking Integration (Tavily)

Before generating content, the system checks whether the slide warrants fact-checking:

```python
fact_check_keywords = [
    "generation", "history", "timeline", "year", "date",
    "version", "statistics", "data", "discovery", "invention", "founder"
]
```

If keywords match the slide title, purpose, or subtopic name, a Tavily search query is made and the results are passed to the LLM as `search_context`, grounding the output in real-world data.

### 4.6 Validation and Retry Logic

After LLM generation:
1. The JSON is parsed and validated against the GyML schema.
2. A **primary block** (the core teaching structure) is required. If missing, the system attempts to infer it or inject a fallback "Title with Bullets" structure.
3. On parse failure or invalid structure, the LLM call is retried up to **2 times** with error feedback appended to the prompt.

### 4.7 Synchronized Narration Generation

Narration is generated **after** visual content, in a separate LLM call:

1. `_count_primary_items(gyml_content)` counts the number of animated visual units (e.g., 4 timeline steps, 3 card grid items).
2. The narration LLM is prompted: *"Write exactly N narration segments to explain this visual."*
3. Each segment's `duration` estimate guides audio generation and animation timing.

This exact count alignment enables frame-perfect animation synchronization in Phase 4.

### 4.8 Density Classification

After content is generated, each slide is classified into one of six density tiers:

```python
def _classify_density(block_count, primary_item_count):
    total = block_count + primary_item_count
    if total >= 8:    return "super_dense"
    elif total >= 6:  return "dense"
    elif total >= 4:  return "standard"
    elif total >= 3:  return "balanced"
    elif total >= 2:  return "sparse"
    else:             return "ultra_sparse"
```

This classification is stored in `slide["slide_density"]` and influences Phase 3 composition and Phase 4 rendering.

---

## 5. Phase 3: Composition (The Compiler Stage)

**Core Files:** `slides/gyml/composer.py`, `slides/gyml/serializer.py`

The Composer acts as a **semantic compiler**. It takes the raw JSON from the LLM and transforms it into a strongly-typed, format-agnostic Intermediate Representation (IR). It does not know about HTML, CSS, or GyML syntax.

### 5.1 The 8-Step Composition Pipeline

```
LLM JSON Input
      │
      ▼
1. Intent Detection       → What is this slide trying to accomplish?
      │
      ▼
2. Concept Extraction     → What distinct ideas are present?
      │
      ▼
3. Concept Grouping       → Can ideas be merged? (≤1 idea per slide rule)
      │
      ▼
4. Slide Creation         → Build initial ComposedSlide object
      │
      ▼
5. Limit Enforcement      → Does this exceed cognitive/spatial limits? Split if so.
      │
      ▼
6. Block Ordering         → Apply block order grammar (Heading → Context → Main → Supplementary → Takeaway)
      │
      ▼
7. Emphasis Assignment    → Tag each block: PRIMARY / SECONDARY / TERTIARY
      │
      ▼
8. Visual Hierarchy       → Assign typography/spacing profile based on density
      │
      ▼
ComposedSlide IR (Output)
```

### 5.2 Intent Detection

Each slide is assigned a single `Intent` from the enum:

| Intent | Meaning | Preferred Block Types |
|---|---|---|
| `INTRODUCE` | First exposure to concept | card_grid, bullets |
| `EXPLAIN` | Mechanistic explanation | timeline, process_arrow |
| `NARRATE` | Story-like sequence | timeline, numbered_list |
| `COMPARE` | Side-by-side contrast | comparison_table, comparison_cards |
| `LIST` | Enumeration without hierarchy | bullet_list, card_grid |
| `PROVE` | Evidence-based argument | stats, key_value_list |
| `SUMMARIZE` | Recap and reinforce | big_bullets, bullet_check |
| `TEACH` | Instructional step-by-step | step_list, process_steps |
| `DEMO` | Demonstration of usage | process_arrow, code |

Intent is inferred from:
- Heading language ("What is…", "How to…", "Timeline of…")
- Dominant block type in the LLM output
- `content_angle` from the blueprint

### 5.3 Concept Grouping and Splitting Rules

The Composer enforces strict cognitive load limits. These limits are **non-negotiable**:

| Limit | Value |
|---|---|
| Max distinct concepts per slide | 4 |
| Ideal concept range | 2–3 |
| Soft text maximum | 300 words |
| Hard text maximum | 400 words |
| Max integrated visual elements | 5 |
| Max layout containers | 3 |
| Max nesting depth | 3 |

**Merge Conditions** (elements stay on same slide if):
- They explain the same underlying idea
- They are mutually dependent for comprehension
- They are parallel parts of a single whole
- Total cognitive load remains manageable

**Split Conditions** (elements are moved to a new slide if):
- They answer different conceptual questions
- They represent sequential ideas across topics
- Their visual structures differ significantly
- Any hard limit is exceeded

When splitting occurs, slides are named `"Title (1/2)"` and `"Title (2/2)"`.

### 5.4 Dense Content Reflow

For dense but not-quite-split-worthy slides, the Composer applies **content reflow**:

- The accent image is converted from a sidebar position into an **inline column block**
- The slide is restructured as two CSS columns: `40% image/intro` | `60% primary content`
- This frees vertical space without losing the image entirely

### 5.5 Block Ordering Grammar

All blocks must follow this sequential grammar. Deviations are corrected by the Composer:

```
[ Heading ]              ← Always first
  → [ Context / Framing ] ← Optional: Sets up the "why"
    → [ Main Content ]   ← 1–3 blocks: The core teaching structure
      → [ Supplementary ]← Optional: Examples, code, callouts
        → [ Takeaway ]   ← Always last if present
```

**Hard ordering rules:**
- Heading is always the first block
- Takeaway is always the last block
- Callouts never interrupt the main content flow
- Dividers only appear between content phases

### 5.6 Emphasis Assignment

Every `ComposedBlock` is tagged with one of three emphasis levels:

| Emphasis | Role | Example Blocks | Visual Effect |
|---|---|---|---|
| `PRIMARY` | Core teaching structure | comparison_table, timeline, card_grid | Larger font, highlighted background |
| `SECONDARY` | Supporting content | intro_paragraph, context_paragraph, callout | Normal weight, subdued |
| `TERTIARY` | Fine details, examples | annotation_paragraph, footnotes | Smaller font, de-emphasized |

Only **one PRIMARY** emphasis is allowed per slide.

### 5.7 Serialization: IR → GyML (`serializer.py`)

After composition, the `GyMLSerializer` converts the format-agnostic `ComposedSlide` IR into spec-compliant `GyMLSection` objects.

**Relationship Types** (how sections are arranged spatially):

| Relationship | Spatial Behavior | Typical Use |
|---|---|---|
| `FLOW` | Sequential vertical stacking | Default for most slides |
| `PARALLEL` | Side-by-side columns | Text + visual side-by-side |
| `ANCHORED` | Image-first then body | Image-led layouts |

The serializer maps each `ComposedBlock.type` to its corresponding `GyML*` dataclass (e.g., `BlockType.TIMELINE` → `GyMLSmartLayout` with `variant=SmartLayoutVariant.TIMELINE`).

---

## 6. Phase 4: Rendering (GyML → HTML)

**Core Files:** `rendering_node.py`, `slides/gyml/renderer.py`

This phase takes the fully composed, structured `GyMLSection` objects and converts them into final HTML5 with CSS custom properties and animation data attributes.

### 6.1 The Rendering Node Workflow (`rendering_node.py`)

The `rendering_node` orchestrates 4 sequential steps per batch of slides:

```
Step 1: Identify Pending Slides
    → Collect all slides with gyml_content but no html_content
    → Also re-render slides that have a prompt but no real image URL yet

Step 2: Synchronous Composition
    → For each pending slide: call composer.compose(gyml_content)
    → Store composed objects temporarily in slide["_composed_objs"]

Step 3: Parallel Image Generation
    → For each composed slide with an imagePrompt:
        - If image_layout != "blank" and no resolved URL exists:
          → Spawn async Leonardo AI call
    → For process_arrow / cyclic_process blocks with per-item imagePrompts:
        - Spawn per-item image generation (512×512, "simple_drawing" style)
    → Run ALL image tasks via asyncio.gather() with semaphore (limit: 1 concurrent)
    → Map results back to ComposedSlide.accent_image_url or item["image_url"]

Step 4: Serialization + Final Rendering
    → serializer.serialize_many(composed_objs) → List[GyMLSection]
    → renderer.render_complete(gyml_sections) → HTML string
    → slide["html_content"] = html_output
```

### 6.2 The GyML Renderer (`renderer.py`)

The `GyMLRenderer` is a **passive** renderer. It makes no semantic decisions — it only converts what's given to it into HTML. Semantic decisions happen in Phases 1–3.

**Constructor Parameters:**

| Parameter | Type | Effect |
|---|---|---|
| `theme` | `Theme` | Provides all CSS custom property values |
| `responsive_constraints` | `ResponsiveConstraints` | Controls breakpoints and max widths |
| `animated` | `bool` | If True, injects `data-segment` attributes for animation sync |

**Core Rendering Methods:**

| Method | Renders | Output |
|---|---|---|
| `render(section)` | Single GyML section | `<section>` HTML with CSS vars |
| `render_complete(sections)` | All sections as full document | Complete HTML5 document |
| `_render_body(body)` | All body nodes recursively | Inner slide HTML |
| `_render_heading(node)` | H1–H4 elements | Semantic heading HTML |
| `_render_paragraph(node)` | Body text with highlights | `<p>` with optional `<mark>` |
| `_render_columns(node)` | Side-by-side column layout | Flex-based column HTML |
| `_render_smart_layout(node)` | Grid/flex variant layout | Variant-specific grid HTML |
| `_render_comparison_table(node)` | Comparison subject/criterion table | Structured comparison HTML |
| `_render_process_arrow_block(node)` | Multi-step process with images | Process arrow flow HTML |
| `_render_cyclic_process_block(node)` | Circular process visualization | Cyclic ring HTML |
| `_render_hub_and_spoke_block(node)` | Central hub + radial spokes | Hub/radial grid HTML |
| `_render_hierarchy_tree(node)` | Recursive tree nodes | Nested tree HTML |
| `_render_formula_block(node)` | Math expressions + variable table | Formula display HTML |

### 6.3 Animation Integration

When `animated=True`, the renderer injects `data-segment` attributes on primary content blocks. These attributes synchronize visual reveals with narration audio chunks:

**Example — Animated Timeline:**
```html
<div class="smart-layout" data-variant="timelineSequential">
  <div class="timeline-item" data-segment="0">
    <div class="timeline-number">1</div>
    <div class="timeline-content">
      <h4>Light Absorption</h4>
      <p>Chlorophyll absorbs photons from sunlight...</p>
    </div>
  </div>
  <div class="timeline-item" data-segment="1">
    <div class="timeline-number">2</div>
    <div class="timeline-content">
      <h4>Water Splitting</h4>
      <p>H₂O molecules are split, releasing oxygen...</p>
    </div>
  </div>
</div>
```

**Animation Rules:**
- Only primary content blocks (smart_layout items) receive `data-segment` attributes
- Paragraphs, headings, columns, code blocks remain always visible
- Each `data-segment` value corresponds to a narration segment index
- Frontend JavaScript reveals each item when the corresponding audio segment begins

**Animated Block Types (receives `data-segment`):**

| Block Type | Animation Unit | Segment Count |
|---|---|---|
| `bigBullets` | Per bullet | n bullets |
| `timeline` / `timelineSequential` | Per step | n steps |
| `cardGrid` / `cardGridIcon` / `cardGridImage` | Per card | n cards |
| `processArrow` | Per step | n steps |
| `comparisonCards` | Per subject/card | n subjects |
| `stats` / `statsComparison` | Per stat | n stats |
| `bulletIcon` / `bulletCheck` / `bulletCross` | Per bullet | n bullets |

### 6.4 Rendered HTML Structure

A fully rendered slide has this HTML structure:

```html
<section id="slide_1" 
         image-layout="right" 
         data-density="standard"
         style="--h1-size: 2.4rem; --body-size: 1.125rem; --block-gap: 1.5rem; ...">
  
  <!-- Accent Image (if layout != blank) -->
  <img class="accent-image accent-image--right" 
       src="https://cdn.leonardo.ai/..." 
       alt="Generated image for Photosynthesis" />
  
  <!-- Main Body -->
  <div class="body">
    
    <!-- Context Paragraph (SECONDARY emphasis) -->
    <p class="intro-paragraph">
      When sunlight hits a leaf...
    </p>
    
    <!-- Primary Block (PRIMARY emphasis) -->
    <div class="smart-layout" data-variant="timelineSequential">
      <div class="timeline-item" data-segment="0">...</div>
      <div class="timeline-item" data-segment="1">...</div>
      <div class="timeline-item" data-segment="2">...</div>
    </div>
    
    <!-- Annotation (TERTIARY emphasis) -->
    <p class="annotation-paragraph">
      All of this happens in thylakoid membranes...
    </p>
    
  </div>
</section>
```

### 6.5 Visual Hierarchy in HTML

The Composer assigns a `VisualHierarchy` profile to each slide based on its density. The Renderer injects these as CSS custom properties via `style` attributes on the `<section>` element:

| CSS Variable | Purpose | Example Value |
|---|---|---|
| `--h1-size` | Heading font size | `2.4rem` |
| `--h2-size` | Subheading size | `2.0rem` |
| `--body-size` | Body text size | `1.125rem` |
| `--block-gap` | Vertical gap between blocks | `1.5rem` |
| `--card-gap` | Gap between grid cards | `1.25rem` |
| `--card-padding` | Internal card padding | `1.5rem` |
| `--section-padding` | Slide inner padding | `3rem` |
| `--column-gap` | Gap between columns | `2rem` |

---

## 7. The GyML Intermediate Language

GyML (Gyanova Markup Language) is the pivot point between semantic composition (Phase 3) and visual rendering (Phase 4). It is a declarative, hierarchical, theme-agnostic structure description.

### 7.1 Where GyML Sits

```
LLM Raw JSON
    │
    ▼ [Composer] — semantic decisions
ComposedSlide IR (Python dataclasses, format-agnostic)
    │
    ▼ [Serializer] — structural mapping
GyMLSection (spec-compliant GyML nodes)
    │
    ▼ [Renderer] — visual production
HTML5 + CSS + data attributes
```

### 7.2 GyML Does NOT Decide

GyML intentionally excludes visual decisions:
- Colors, gradients, shadows
- Typography choices (font family, weight)
- Spacing and padding values
- Breakpoints and responsive behavior
- Animation timing

These are handled exclusively by the Theme system and Renderer.

### 7.3 Key GyML Node Types

| Node Type | Represents | Key Fields |
|---|---|---|
| `GyMLSection` | A single slide | `id`, `image_layout`, `accent_image`, `body` |
| `GyMLBody` | Slide content container | `children: List[GyMLNode]` |
| `GyMLHeading` | H1–H4 heading | `level`, `text` |
| `GyMLParagraph` | Body text | `text`, `highlight` |
| `GyMLColumns` | Side-by-side columns | `colwidths`, `columns` |
| `GyMLSmartLayout` | Grid/flex layout | `variant`, `items`, `cellsize` |
| `GyMLComparisonTable` | Comparison grid | `criteria`, `subjects`, `conclusion` |
| `GyMLProcessArrowBlock` | Process steps with images | `steps: List[GyMLProcessArrowItem]` |
| `GyMLCyclicProcessBlock` | Circular process | `phases: List[GyMLCyclicProcessItem]` |
| `GyMLHubAndSpoke` | Hub-and-radial layout | `hub`, `spokes: List[GyMLHubAndSpokeItem]` |
| `GyMLHierarchyTree` | Tree structure | `root: GyMLTreeNode` |
| `GyMLFormulaBlock` | Math formula + variables | `formula`, `variables: List[GyMLFormulaVariable]` |
| `GyMLCode` | Code block | `language`, `code`, `role` |

---

## 8. Visual Block Type Comparison

The following table compares all primary block types available in the GyML system, across their pedagogical purpose, visual structure, and animation behavior:

| Block Type | Visual Form | Best For | Animation Unit | Max Items |
|---|---|---|---|---|
| `smart_layout: bigBullets` | Large text bullets | Lists, key points | Per bullet | 6 |
| `smart_layout: bulletIcon` | Icon + text bullets | Categorized lists | Per bullet | 6 |
| `smart_layout: bulletCheck` | Checkmark bullets | Benefits, completed steps | Per bullet | 8 |
| `smart_layout: bulletCross` | Cross bullets | Limitations, don'ts | Per bullet | 6 |
| `smart_layout: cardGridIcon` | Icon + title + description cards | Features, concepts | Per card | 6 |
| `smart_layout: cardGridSimple` | Title + description cards | Plain concept overviews | Per card | 6 |
| `smart_layout: cardGridImage` | Image + text cards | Visual concept collections | Per card | 4 |
| `smart_layout: timeline` | Numbered timeline entries | Historical events, phases | Per step | 12 |
| `smart_layout: timelineSequential` | Connected timeline | Ordered processes | Per step | 12 |
| `smart_layout: timelineIcon` | Icon-labeled timeline | Visual milestones | Per step | 8 |
| `smart_layout: processArrow` | Arrow-connected steps with images | Complex multi-image flows | Per step | 6 |
| `smart_layout: processSteps` | Numbered process steps | Instructional sequences | Per step | 8 |
| `smart_layout: processAccordion` | Collapsible process steps | Long procedures | Per step | 10 |
| `smart_layout: comparisonCards` | Side-by-side subject cards | 2–3 concept comparison | Per subject | 3 |
| `smart_layout: comparisonProsCons` | Pros vs. cons two-column | Advantage/disadvantage analysis | Per row | 5 |
| `smart_layout: comparisonBeforeAfter` | Before ↔ After contrast | State change comparison | Per side | 2 |
| `smart_layout: stats` | Large number + label stats | Quantitative impact | Per stat | 6 |
| `smart_layout: statsComparison` | Paired statistics | Comparative metrics | Per pair | 4 |
| `comparison_table` | Criterion × Subject table | 4+ subject comparison | Per row | 5 subjects |
| `hub_and_spoke` | Central hub + radial items | Concept relationships | Per spoke | 4–6 |
| `cyclic_process_block` | Circular phase flow | Repeating cycles | Per phase | 4–8 |
| `hierarchy_tree` | Root → branches → leaves | Taxonomies, org charts | Per node | Unlimited |
| `formula_block` | Formula display + variable table | Mathematical concepts | None | 8 variables |
| `key_value_list` | Label: value pairs | Definitions, properties | Per row | 10 |
| `numbered_list` | Sequential numbered items | Ordered procedures | Per item | 12 |
| `code` | Syntax-highlighted code | Programming examples | None | N/A |
| `image` | Standalone content image | Visual demonstrations | None | N/A |

### Comparison Types in Detail

The system has two distinct comparison rendering modes, selected automatically:

| Criterion | `comparisonCards` | `comparisonTable` |
|---|---|---|
| **Trigger** | ≤ 3 subjects | ≥ 4 subjects |
| **Visual Form** | Vertical subject cards | Grid table (criteria × subjects) |
| **Animation** | Card by card | Row by row |
| **Cognitive Style** | Qualitative, story-like | Analytical, systematic |
| **Max Subjects** | 3 | 5 |
| **Max Criteria** | 5 | 5 |
| **Words Per Value** | 6–14 | 6–14 |

---

## 9. Layout Variant Comparison by Pedagogical Intent

This table shows which visual variants are available for each pedagogical angle and intent, helping understand how content type maps to visual form:

| Intent / Angle | Primary Variants | When to Use This Intent |
|---|---|---|
| **overview** | Card grids, big bullets | First slide of a subtopic; orienting the learner |
| **mechanism** | Timelines, process arrows | Explaining *how* something works step-by-step |
| **example** | Image cards, icon bullets | Showing concrete instances of an abstract concept |
| **comparison** | Comparison cards, pros/cons, before/after | Contrasting two or more approaches/concepts |
| **application** | Icon bullets, process steps | Real-world usage scenarios and implementations |
| **visualization** | Stats, stats comparison | Quantitative backing; data-driven arguments |
| **summary** | Big bullets, check bullets, icon bullets | Lesson recap; reinforcing key takeaways |
| **teach** | Card grids, process steps, bullets | Instructional content with clear learning outcomes |
| **demo** | Process arrows, process steps, accordion | Step-by-step demonstration of a procedure |
| **introduce** | Simple card grids, big bullets | First introduction to a new topic |
| **explain** (fallback) | Card grids, big bullets | Fallback for general explanatory slides |
| **narrate** | Timeline, process arrow | Story-like sequential narration |
| **prove** | Stats, stats comparison | Evidence and data-backed arguments |
| **list** | Big bullets, check bullets, process steps | Enumeration without hierarchical structure |

---

## 10. Density Tier Comparison

Density is one of the most impactful dimensions of the slide system. It affects visual hierarchy, layout, font sizes, spacing, and whether an image is shown at all.

### The 6-Tier Scale

| Tier | Score Range | Block Count + Item Count | Typical Use |
|---|---|---|---|
| `ultra_sparse` | 0–1 | 0–1 total | Title slides, major section dividers |
| `sparse` | 2 | 1–2 total | Definitions, key quotes, impact statements |
| `balanced` | 3 | 3 total | Standard explanation, moderate lists |
| `standard` | 4 | 3–4 total | Detailed descriptions, comprehensive lists |
| `dense` | 5–6 | 4–5 total | Technical comparisons, complex diagrams |
| `super_dense` | 7+ | 6+ total | Architecture overviews, reference tables |

### Visual Hierarchy Profiles by Density

| Profile | H1 Size | Body Size | Block Gap | Section Padding | Use Case |
|---|---|---|---|---|---|
| `impact` | 3.5rem | 1.6rem | 2.5rem | 3.25rem | Ultra-sparse hero slides |
| `balanced` | 3.0rem | 1.4rem | 1.5rem | 2.25rem | Standard slides |
| `dense` | 2.6rem | 1.25rem | 1.0rem | 1.5rem | Dense content slides |
| `super_dense` | 2.2rem | 1.1rem | 0.5rem | 1.25rem | Maximum-content reference slides |

### Compositional Impact of Density

| Density | Image Layout Override | Auto-Split Triggered? | Reflow Applied? |
|---|---|---|---|
| `ultra_sparse` | `behind` (hero) | No | No |
| `sparse` | `right` or `left` | No | No |
| `balanced` | `right` or `left` | No | No |
| `standard` | `right` or `left` | No | No |
| `dense` | `blank` (no image) | Possible | Yes (40/60 column) |
| `super_dense` | `blank` (no image) | Yes | Yes (split slides) |

### Fitness Gate Validation

The `SlideFitnessGate` (`fitness.py`) validates that generated content won't overflow the slide viewport. It calculates an `estimated_height` (0.0 to 1.0+):

```
Estimated Height = Word Utilization + Structural Score + Image Utilization

Word Utilization:
  = Total Words / 250   [targeting 250 words = 100% fill]

Structural Score:
  = Sum of block weights × item scaling × text density multiplier

Item Scaling (diminishing returns):
  Items 1-3: 100% weight
  Items 4-6: 70% weight
  Items 7+:  40% weight
```

**Quality Thresholds:**
- `< 0.40`: Critical failure — slide is too empty, rejected
- `< 0.50` without an image: Soft failure — must have image to pass
- `> 1.0`: Potential overflow — may be split by Composer

---

## 11. Theme System Comparison

The theme system (`theme.py`) provides all visual styling via CSS custom properties. The renderer injects theme values without any hardcoded colors or spacing.

### Available Themes

| Theme | Background | Primary Color | Personality |
|---|---|---|---|
| `gamma_light` | White (#FFFFFF) | Blue (#0066cc) | Clean, professional, light |
| `gamma_dark` | Dark (#1a1a2e) | Blue (#4a9eff) | Modern dark mode |
| `midnight` | Deep navy (#0f0f1a) | Purple/blue | Premium, dramatic |

*(The `midnight` theme is the current default in `rendering_node.py`.)*

### Theme Properties Injected as CSS Variables

```
Color Group:
  --bg-primary, --bg-secondary, --text-primary, --text-secondary
  --accent, --border-color, --number-bg, --callout-bg, --icon-bg

Typography (static, defined by hierarchy profile):
  --h1-size, --h2-size, --h3-size, --h4-size
  --body-size, --small-size, --card-number-size
  --line-height-base, --line-height-heading

Spacing (dynamic, from hierarchy profile):
  --section-padding, --block-gap, --heading-gap
  --card-gap, --card-padding, --column-gap

Animation:
  --transition-fast, --transition-base, --transition-slow
  --easing-standard
```

---

## 12. End-to-End Data Flow

The following traces exactly what data exists at each stage of the pipeline for a single slide:

### Input

```json
{
  "topic": "Photosynthesis",
  "current_level": "High School",
  "granularity": "Detailed"
}
```

### After Phase 1 (Blueprint)

```json
{
  "title": "Light Reactions in Photosynthesis",
  "content_angle": "mechanism",
  "intent": "process",
  "purpose": "intuition",
  "selected_template": "Timeline",
  "role": "Interpret",
  "goal": "Explain how light energy drives the first stage of photosynthesis",
  "visual_required": true,
  "visual_type": "image"
}
```

### After Phase 2 (GyML Content JSON)

```json
{
  "title": "Light Reactions in Photosynthesis",
  "intent": "explain",
  "imageLayout": "right",
  "imagePrompt": "Cross-section of a chloroplast showing thylakoid membranes",
  "imageStyle": "detailed scientific illustration",
  "contentBlocks": [
    {
      "type": "context_paragraph",
      "text": "When sunlight hits a leaf, it triggers a rapid chain of chemical reactions."
    },
    {
      "type": "smart_layout",
      "variant": "timelineSequential",
      "items": [
        {"heading": "Light Absorption", "description": "Chlorophyll absorbs photons..."},
        {"heading": "Water Splitting", "description": "H₂O splits into O₂ and electrons..."},
        {"heading": "Energy Transfer", "description": "Electrons flow through transport chain..."},
        {"heading": "ATP Synthesis", "description": "Proton gradient drives ATP production..."}
      ],
      "primary_block_index": 1,
      "animation_unit": "step"
    },
    {
      "type": "annotation_paragraph",
      "text": "All reactions occur in the thylakoid membranes of chloroplasts."
    }
  ],
  "narration": {
    "segments": [
      {"text": "When sunlight hits a leaf...", "duration": 4.2},
      {"text": "First, chlorophyll absorbs photons...", "duration": 2.8},
      {"text": "This energy then splits water molecules...", "duration": 3.5},
      {"text": "Electrons flow through the chain generating ATP...", "duration": 4.1},
      {"text": "All of this occurs in the thylakoid membranes.", "duration": 2.5}
    ]
  },
  "slide_density": "standard",
  "animation_metadata": {
    "animation_unit": "step",
    "animation_unit_count": 4,
    "animated_block_index": 1
  }
}
```

### After Phase 3 (Composed IR → GyML Structure)

```
ComposedSlide:
  id: "slide_abc123"
  title: "Light Reactions in Photosynthesis"
  intent: Intent.EXPLAIN
  image_layout: "right"
  image_prompt: "Cross-section of a chloroplast..."
  image_style: "detailed scientific illustration"
  accent_image_url: "placeholder"
  sections:
    - ComposedSection:
        purpose: CONTEXT
        relationship: FLOW
        primary_block: None
        secondary_blocks:
          - ComposedBlock(type="intro_paragraph", emphasis=SECONDARY)
    - ComposedSection:
        purpose: MAIN
        relationship: FLOW
        primary_block: ComposedBlock(type="smart_layout", emphasis=PRIMARY,
                         content={"variant": "timelineSequential", "items": [...]})
        secondary_blocks: []
    - ComposedSection:
        purpose: SUPPLEMENTARY
        relationship: FLOW
        primary_block: None
        secondary_blocks:
          - ComposedBlock(type="annotation_paragraph", emphasis=TERTIARY)
  hierarchy: VisualHierarchy(name="balanced", ...)

[After Serialization → GyMLSection]

GyMLSection:
  id: "slide_abc123"
  image_layout: "right"
  accent_image: GyMLImage(src="placeholder", alt="...")
  body: GyMLBody(children=[
    GyMLParagraph(text="When sunlight hits a leaf..."),
    GyMLSmartLayout(
      variant=SmartLayoutVariant.TIMELINE_SEQUENTIAL,
      items=[
        GyMLSmartLayoutItem(heading="Light Absorption", description="..."),
        GyMLSmartLayoutItem(heading="Water Splitting", description="..."),
        GyMLSmartLayoutItem(heading="Energy Transfer", description="..."),
        GyMLSmartLayoutItem(heading="ATP Synthesis", description="...")
      ]
    ),
    GyMLParagraph(text="All reactions occur in thylakoid membranes...")
  ])
```

### After Phase 4 (Final HTML)

```html
<section id="slide_abc123"
         image-layout="right"
         data-density="standard"
         style="
           --h1-size: 3.0rem; --h2-size: 2.4rem;
           --body-size: 1.4rem; --block-gap: 1.5rem;
           --section-padding: 2.25rem; --card-gap: 1.25rem;
           --bg-primary: #0f0f1a; --text-primary: #e8e8f0;
           --accent: #7c6af7; ...
         ">

  <img class="accent-image accent-image--right"
       src="https://cdn.leonardo.ai/users/.../chloroplast.png"
       alt="Generated image for Light Reactions" />

  <div class="body">

    <p class="intro-paragraph">
      When sunlight hits a leaf, it triggers a rapid chain of chemical reactions.
    </p>

    <div class="smart-layout smart-layout--timeline-sequential">
      <div class="timeline-item" data-segment="0">
        <div class="timeline-connector"></div>
        <div class="timeline-dot"></div>
        <div class="timeline-content">
          <h4 class="timeline-heading">Light Absorption</h4>
          <p class="timeline-description">Chlorophyll absorbs photons...</p>
        </div>
      </div>
      <div class="timeline-item" data-segment="1">
        <div class="timeline-connector"></div>
        <div class="timeline-dot"></div>
        <div class="timeline-content">
          <h4 class="timeline-heading">Water Splitting</h4>
          <p class="timeline-description">H₂O splits into O₂ and electrons...</p>
        </div>
      </div>
      <div class="timeline-item" data-segment="2">...</div>
      <div class="timeline-item" data-segment="3">...</div>
    </div>

    <p class="annotation-paragraph">
      All reactions occur in the thylakoid membranes of chloroplasts.
    </p>

  </div>
</section>
```

---

## 13. Comparative Summary: Key Design Trade-offs

This section directly compares the key architectural decisions made in GYANova against alternative approaches.

### Trade-off 1: Content-First vs. Script-First

| Criterion | Content-First (GYANova) | Script-First (Alternative) |
|---|---|---|
| **Visual Independence** | Slides are standalone teaching tools | Slides depend on narration |
| **Narration Quality** | Narration adds context; not redundant | Narration repeats slide content |
| **Animation Sync** | Exact alignment (item count known) | Retroactive estimation |
| **LLM Complexity** | Two specialized calls (visual, then narration) | One combined call |
| **Content Quality** | Higher visual structure | Higher prose quality |

### Trade-off 2: Strict Schema vs. Free-form LLM Output

| Criterion | Strict JSON Schema (GYANova) | Free-form Generation |
|---|---|---|
| **Consistency** | High — always valid structure | Low — unpredictable format |
| **Creativity** | Limited to supported block types | Unlimited but unrenderable |
| **Reliability** | Retry logic on parse failure | Cascading failures |
| **Debuggability** | Full schema validation | Black box output |
| **Extensibility** | Add new block types to schema | N/A |

### Trade-off 3: Multi-Phase Pipeline vs. Single LLM Call

| Criterion | Multi-Phase (GYANova) | Single-Pass LLM |
|---|---|---|
| **Quality** | Each phase specialized for its task | Jack-of-all-trades |
| **Latency** | Higher (multiple LLM calls) | Lower |
| **Error Isolation** | Failures isolated to phases | Single point of failure |
| **Modularity** | Easy to swap any phase | Monolithic |
| **Cost** | Higher (more tokens) | Lower |

### Trade-off 4: IR + Serializer vs. Direct HTML Generation

| Criterion | IR + Serializer (GYANova) | Direct LLM → HTML |
|---|---|---|
| **Theme Independence** | Fully decoupled | Hardcoded in prompt |
| **Format Flexibility** | Can serialize to HTML, PDF, PPTX | HTML only |
| **Testing** | IR can be unit tested without rendering | Hard to test |
| **Debuggability** | Inspect IR at any stage | Binary pass/fail |
| **LLM Prompt Size** | Smaller (no HTML in prompt) | Huge prompts |

### Trade-off 5: Template Registry vs. Fully Dynamic Layouts

| Criterion | Template Registry (GYANova) | Fully Dynamic |
|---|---|---|
| **Visual Consistency** | High | Varies wildly |
| **Educational Suitability** | Guaranteed (curated templates) | Unpredictable |
| **LLM Hallucination Risk** | Low (constrained to registry) | High |
| **Design Quality** | Consistent Gamma-style | Random |
| **New Layout Addition** | Requires code update | N/A |

---

*End of Report*

**Report Generated From Source Files:**
- `apps/api-server/app/services/node/new_slide_planner.py`
- `apps/api-server/app/services/node/content_generation_node.py`
- `apps/api-server/app/services/node/slides/gyml/generator.py`
- `apps/api-server/app/services/node/slides/gyml/composer.py`
- `apps/api-server/app/services/node/slides/gyml/serializer.py`
- `apps/api-server/app/services/node/slides/gyml/renderer.py`
- `apps/api-server/app/services/node/slides/gyml/definitions.py`
- `apps/api-server/app/services/node/slides/gyml/constants.py`
- `apps/api-server/app/services/node/slides/gyml/hierarchy.py`
- `apps/api-server/app/services/node/slides/gyml/theme.py`
- `apps/api-server/app/services/node/slides/gyml/fitness.py`
- `apps/api-server/app/services/node/rendering_node.py`
- `apps/api-server/app/services/langgraphflow.py`
- `apps/api-server/slide_engine.md`
- `apps/api-server/gyanova_markup_language.md`
- `apps/api-server/app/services/node/slide_generation_architecture.md`
- `docs/reports/slide_density_report.md`
- `docs/reports/comparison_schema.md`
