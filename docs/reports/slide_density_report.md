# GYANova Slide Density System Report

This report documents the rules, logic, and architectural impact of the slide density system within the GYANova slide generation pipeline.

## 1. System Overview
The GYANova Slide Density System is a 6-tier classification framework used to balance cognitive load, visual aesthetics, and content integrity. It ensures that slides are neither too empty nor too crowded, and that the visual presentation adapts dynamically to the volume of information.

## 2. The 6-Tier Density Scale
The system uses the following tiers to categorize slides:

| Tier | Description | Typical Use Case |
| :--- | :--- | :--- |
| `ultra_sparse` | Near-empty slides. | Title slides, major section transitions. |
| `sparse` | Minimal content (1-2 items). | High-impact statements, definitions, intro slides. |
| `balanced` | Optimized white space (3-4 items). | Standard explanatory slides, moderate lists. |
| `standard` | Full content (4-5 items). | Detailed descriptions, comprehensive lists. |
| `dense` | Heavy content (5-6 items). | Technical details, complex comparisons. |
| `super_dense` | Maximum capacity (>6 items). | Architectural overviews, dense diagrams, tables. |

## 3. Classification Logic (`content_generation_node.py`)
Density is calculated in the `_classify_density` function based on two primary metrics:
- **Block Count**: The number of top-level content blocks (paragraphs, lists, images, etc.).
- **Primary Item Count**: The total number of sub-items within structural blocks (e.g., bullet points in a list, cards in a grid, steps in a timeline).

**Classification Thresholds**:
*   **Super Dense**: > 6 primary items OR > 4 blocks.
*   **Dense**: 5-6 primary items OR 4 blocks.
*   **Standard**: 4 items OR 3 blocks.
*   **Balanced**: 3 items.
*   **Sparse**: 1-2 items.
*   **Ultra Sparse**: 0 items (title only).

## 4. Planning & Diversity Constraints (`new_slide_planner.py`)
To prevent monotonous or overwhelming lessons, the `NewSlidePlanner` enforces density variety:
- **Mandatory Mix**: Every lesson must include at least one `sparse` and one `dense` slide to vary the cognitive pace.
- **Diversity Validation**: A validation rule ensures that **no more than 50%** of slides in a single subtopic target the same density tier.
- **Planner Intent**: The LLM specifies a `target_density` during the planning phase, which the downstream generator treats as a content volume constraint.

## 5. Height Estimation & Fitness Gate (`fitness.py`)
The `SlideFitnessGate` uses a heuristic "Fitness Math" to predict if content will overflow the screen. It calculates an `estimated_height` (0.0 to 1.0+):

### Height Calculation Formula:
`Estimated Height = Word Utilization + Structural Score + Image Utilization`

- **Word Utilization**: `Total Words / 250` (Targeting ~250 words for 100% fill).
- **Structural Score (Block Weights)**: Each block type contributes a base "vertical thirst" score:
    - **High Impact (0.30 - 0.55)**: `hub_and_spoke` (0.55), `cyclic_process` (0.35), `process_arrow` (0.30), `feature_showcase` (0.30).
    - **Medium Impact (0.15 - 0.25)**: `diagram` (0.25), `split_panel` (0.25), `code` (0.20), `comparison_table` (0.20), `table` (0.15), `smart_layout` (0.15).
    - **Low Impact (0.08 - 0.12)**: `card_grid` (0.12), `key_value_list` (0.12), `formula_block` (0.10), `hierarchy_tree` (0.10), `numbered_list` (0.08).

### Granular Scaling Rules:
1. **Item Weighting**: Beyond the base block weight, each sub-item adds to the score:
   - `0.03/item`: Process Arrows, Cyclic Processes.
   - `0.02/item`: Hierarchy Trees, Comparison Tables, Feature Showcases.
   - `0.015/item`: Numbered Lists, Card Grids, Key-Value Lists.
   - `0.01/item`: Standard Tables.

2. **Diminishing Returns**: To account for visual grouping, weight decreases as items increase:
   - **Items 1-3**: 100% weight.
   - **Items 4-6**: 70% weight.
   - **Items 7+**: 40% weight.

3. **Text Density Multiplier**:
   - `Weight = Calculated Weight * Text Density Factor`
   - Factor is `(avg words per item / 20.0)`, clamped between `1.0` and `2.0`.
   - *Example: A card with 40 words is 2x "taller" than a card with 10 words.*

### Component Limits (`constraints.py`):
| Component | Min Items | Max Items | Max Words/Item |
| :--- | :--- | :--- | :--- |
| `timeline` | 2 | 12 | 40 |
| `comparison` | 2 | 3 | 60 |
| `processSteps` | 3 | 12 | 50 |
| `hub_and_spoke` | 4 | 6 | 80 |
| `cardGrid` | 2 | 12 | 25 |

### Quality Thresholds:
- **Critical Failure**: Density < 0.40 (Slide is rejected as "too empty").
- **Soft Failure**: Density < 0.50 without an image (Valid only if an image is injected).

## 6. Compositional Impact (`composer.py`)
Density triggers significant structural changes during the composition phase:
- **Layout Enforcement**: Slides classified as `dense` or `super_dense` automatically force an `image_layout` of `blank`. This ensures that text has the full screen width and prevents image-induced overflow.
- **Dense Reflow**: For slides with >6 items, the composer attempts to reflow the layout:
    - The accent image is converted into an inline block.
    - The slide is split into two columns: 40% width for intro text/image, and 60% for the dense primary content.
- **Auto-Splitting**: If a slide exceeds maximum cognitive or spatial limits (e.g., word count or block count), the composer automatically splits it into two or more slides, naming them `Title (1/2)`, `Title (2/2)`, etc.

## 7. Visual Hierarchy & Rendering (`hierarchy.py`)
The system maps density tiers to specific CSS and Typography profiles to optimize readability:

| Profile | H1 Size | Body Size | Block Gap | Section Padding |
| :--- | :--- | :--- | :--- | :--- |
| `super_dense` | 2.2rem | 1.1rem | 0.5rem | 1.25rem |
| `dense` | 2.6rem | 1.25rem | 1.0rem | 1.5rem |
| `balanced` | 3.0rem | 1.4rem | 1.5rem | 2.25rem |
| `impact` | 3.5rem | 1.6rem | 2.5rem | 3.25rem |

The `RenderingNode` passes the `slide_density` to the HTML as a `data-density` attribute, allowing the front-end to scale components and whitespace dynamically.
