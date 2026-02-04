1. What GyML Is

Gyanova Markup Language (GyML) is a structural, semantic markup language used to describe slides after layout decisions are made but before rendering.

GyML is:

Declarative (describes structure, not styling)

Hierarchical (tree-based)

Responsive by design

Deterministic

Theme-agnostic

GyML does not decide:

Colors

Typography

Spacing

Breakpoints

Visual density

Variation across slides

Those are handled by the renderer + theme, not the markup 

Gamma Markup Language

.

2. Where GyML Sits in the Pipeline
Topic / Content
   ↓
Intent & Layout Decisions (AI / Editorial Logic)
   ↓
GyML (Structural Markup)        ← THIS FILE
   ↓
Renderer (Theme + Responsive Rules)
   ↓
Final Output (Web / Slide / Canvas)


Important:
GyML is the output of layout decisions, not the input.

3. Core Unit: Slide (Section)

Each slide is represented by a <section>.

<section id="auto-id" image-layout="right | left | top | behind | blank">
  <img class="accent-image" src="..." alt="..." />
  <div class="body">
    ...
  </div>
</section>

Rules

<section> is the atomic slide unit

Sections stack vertically

Sections have no awareness of neighboring slides

Slides expand/shrink based on content

Slides are portable and reorderable 

Gamma Markup Language

4. Body Container (Mandatory)
<div class="body">
  <!-- all visible content lives here -->
</div>


Rules:

Exactly one div.body per section

Everything visible (except accent images) lives inside body

Body is a vertical flow container

5. Hierarchy & Tree Structure

GyML is strictly hierarchical.

SECTION
 ├─ img.accent-image (optional)
 └─ div.body
     ├─ h1–h4
     ├─ p
     ├─ columns
     │   └─ div (column)
     ├─ smart-layout
     │   └─ smart-layout-item
     └─ img (inline)


Rules:

Every element has exactly one parent

No cross-references

No graph relationships

Order = render order 

Gamma Markup Language

6. Text Elements
<h1>Slide Title</h1>
<h2>Subheading</h2>
<h3>Section Heading</h3>
<p>Paragraph text</p>
<b>, <i>, <strong>, <em>


Rules:

Hierarchy is implicit via tag type

No enforced ordering (heading need not be first)

Renderer applies theme typography

No inline styles allowed

7. Columns (Parallel Layout)
<columns colwidths="[50,50]">
  <div>Column 1</div>
  <div>Column 2</div>
</columns>


Rules:

<columns> creates a horizontal layout

colwidths is a hard constraint

Children must be <div>

Responsive behavior handled by renderer

On mobile, columns stack vertically 

Gamma Markup Language

8. Smart Layouts (Explicit Structural Patterns)
<smart-layout cellsize="15" variant="solidBoxesWithIconsInside">
  <smart-layout-item>
    <icon alt="atom"></icon>
    <div>
      <h4>Title</h4>
      <p>Description</p>
    </div>
  </smart-layout-item>
</smart-layout>


Key properties:

Explicit tag, not inferred

variant encodes semantic intent (timeline, steps, comparison)

Items are equal peers

Renderer decides grid structure

Smart layouts are structural declarations, not visual guesses 

Gamma Markup Language

.

9. Media Handling (Critical Distinction)
9.1 Accent Images (Decorative)
<section image-layout="right">
  <img class="accent-image" src="..." />
  <div class="body">...</div>
</section>


Rules:

Sibling of body

Positioned relative to body

Decorative only

Does NOT affect layout structure

9.2 Inline Images (Structural)
<div>
  <img src="..." />
</div>


Rules:

Nested inside layout containers

Participates in flow

Affects layout dimensions

Can anchor columns or grids 

Gamma Markup Language

10. Ordering Rules

GyML enforces structure, not semantic order.

Elements render in the order written

No requirement that headings come first

No automatic reordering

Smart layouts expect specific children

Ordering discipline is the responsibility of the composition engine, not GyML.

11. Nesting Rules & Depth Limits

Allowed:

Columns inside body

Smart layouts inside body or columns

Text inside any content container

Constraints:

No smart-layout inside smart-layout

Columns inside columns discouraged

Recommended depth ≤ 4–5 levels

Renderer must degrade gracefully if violated 

Gamma Markup Language

.

12. What GyML Does NOT Encode

GyML intentionally omits:

Visual density

Content weight

Priority or emphasis flags

Soft constraints

Slide splitting rules

Repetition avoidance

Cross-slide awareness

These are handled before GyML generation or during rendering, never inside GyML 

Gamma Markup Language

.

13. Determinism Guarantees

Rendering is deterministic given:

Same GyML

Same theme

Same viewport size

Variation comes only from:

Responsive breakpoints

Theme changes

Image loading state

No randomness is encoded in GyML 

Gamma Markup Language

.

14. Renderer Responsibilities (Non-Negotiable)

A GyML renderer MUST:

Parse sections as atomic units

Resolve accent images separately from body

Treat columns as flex containers

Treat smart-layout as grid containers

Apply theme spacing & typography

Reflow layouts responsively

Never infer structure not in GyML

Gracefully handle malformed markup

15. Key Design Principle (From Gamma)

GyML describes what exists and how it is structured —
never how it should look.

Structure first.
Rendering second.
Styling last.