1. Purpose

This document defines a block-based slide composition engine inspired by responsive, narrative-driven systems (e.g., Gamma), but without templates or fixed layouts.

The goal is to generate slides that:

Feel visually complete (not empty, not overcrowded)

Support multiple content types in a single slide

Maintain narrative flow and visual variety

Are deterministic, debuggable, and extensible

2. Core Mental Model
Slide (Card)

A slide is a responsive narrative content unit, not a fixed canvas.

A slide:

Answers one conceptual question

Contains multiple blocks

Is part of a larger narrative sequence

Can stand alone but gains meaning in sequence

Section

A semantic grouping of blocks inside a slide.

Sections:

Represent intent (e.g., introduction, explanation, summary)

Do NOT represent layout

May contain multiple block types

Block

The atomic unit of content.

Blocks:

Are semantic, not visual

Flow vertically by default

Can be nested inside containers (e.g., columns)

Never assume absolute positioning

3. High-Level Pipeline
Topic
  ↓
Intent Detection
  ↓
Concept Extraction
  ↓
Concept Grouping (≤ 1 idea per slide)
  ↓
Slide Creation
  ↓
Section Creation
  ↓
Block Composition
  ↓
Block Ordering
  ↓
Emphasis Assignment
  ↓
Implicit Limit Checks
  ↓
Variety Checks
  ↓
Render

4. Intent Detection

Each slide must have one primary intent.

Supported intents:

EXPLAIN

SUMMARIZE

COMPARE

NARRATE

PERSUADE

REFERENCE

Intent is inferred from:

Heading language (“What is…”, “Why…”, “How…”, “Timeline of…”)

Content structure (lists, sequences, comparisons)

Narrative position in the deck

Intent influences:

Block choice

Ordering rules

Density limits

5. Concept Grouping Rules (Slide Boundaries)

A slide must represent one coherent idea.

MERGE content into the same slide if:

Elements explain the same idea

Elements are mutually dependent

Elements are parallel parts of a whole

Cognitive load remains manageable

SPLIT content into multiple slides if:

Elements answer different questions

Elements are sequential across concepts

Visual structures differ significantly

Cognitive load exceeds limits

6. Implicit Limits (Hard Rules)

These are non-negotiable constraints.

Cognitive Load

Max distinct concepts per slide: 4

Ideal range: 2–3

Text Density

Soft max: 300 words

Hard max: 400 words

Visual Elements

Max integrated visual elements: 5
(images, icons, callouts, diagrams combined)

Structural Complexity

Max layout containers per slide: 3

Max nesting depth: 3

If any limit is exceeded → split slide.

7. Block Types (Canonical Set)
Core Blocks

heading

paragraph

bullet_list

step_list

card_grid

image

stat

takeaway

callout

divider

8. Block Ordering Grammar (Mandatory)

Blocks must follow this grammar:

[ Heading ]
  → [ Context / Framing (optional) ]
    → [ Main Content Blocks (1–3) ]
      → [ Supplementary Blocks (optional) ]
        → [ Takeaway / Closing (optional) ]

Hard Rules

Heading is always first

Takeaway is always last

Callouts never interrupt main content

Divider only appears between content phases

9. Emphasis Model

Each slide has three emphasis levels.

Primary Emphasis

Always the heading OR

A dominant visual structure (cards, timeline)

Secondary Emphasis

Supporting blocks (lists, cards, steps)

Tertiary Emphasis

Details, examples, callouts, images

Only one primary emphasis is allowed per slide.

10. Block Interaction Rules
Flow Rules

Blocks flow top-to-bottom

Columns create parallel flows

Nested layouts contain peer items

Image Rules

Accent images do NOT interrupt flow

Inline images participate in flow

Image-first only if image and text are mutually dependent

Supplementary Blocks

Callouts and blockquotes are additive

Never appear before main content

11. Text → Structure Promotion Rules

When content is purely textual:

Condition	Promote To
3–4 parallel items	bullet_list or card_grid
Sequential steps	step_list
Historical sequence	timeline (step_list variant)
Quantitative comparison	stat
Structural taxonomy	card_grid
Single abstract concept	paragraph
12. Variety Enforcement (Deck-Level)

The engine MUST track previous slides.

Enforced Rules

No two consecutive slides share the same dominant block pattern

Avoid repeating:

Same block type

Same block count

Same orientation

Alternate density:

Dense → Light → Medium → Dense

If violation detected → recompose blocks.

13. Split & Merge Automation
Auto-Split Triggers

Exceeds any implicit limit

Requires >3 main content blocks

Multiple unrelated block types competing for emphasis

Auto-Merge Triggers

Two adjacent slides:

Same intent

Same concept

Combined load within limits

14. LLM → Engine Contract
LLM Responsibilities

Output intent

Output sections

Compose blocks semantically

Respect block grammar

Engine Responsibilities

Enforce limits

Enforce ordering

Enforce variety

Split / merge when needed

Renderer Responsibilities

Never infer intent

Never reorder blocks

Never change structure

15. Failure & Fallback Strategy

If composition fails:

Reduce block count

Remove supplementary blocks

Convert visuals → text

Fall back to:

heading
→ paragraph
→ takeaway


A slide must always render.

16. Non-Goals (Explicitly Out of Scope)

Fixed templates

Absolute positioning

Manual layout selection

Design-time assumptions

Slide-specific CSS logic

17. Key Principle (Do Not Violate)

Slides are composed, not designed.
Layouts emerge from rules, not templates.