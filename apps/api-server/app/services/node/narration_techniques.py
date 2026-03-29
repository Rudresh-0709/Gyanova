"""
Narration Techniques for Different Slide Templates

This module defines specialized narration generation strategies for sparse templates
that don't have primary teaching blocks (structure data like lists, tables, etc.).

Each template gets a custom prompt directive and segment structure to optimize
the spoken explanation of visual content.
"""

from typing import Dict, Any, List, Optional

# =============================================================================
# NARRATION TECHNIQUE REGISTRY
# =============================================================================

NARRATION_TECHNIQUES: Dict[str, Dict[str, Any]] = {
    # ─────────────────────────────────────────────────────────────────────
    # TITLE CARD
    # ─────────────────────────────────────────────────────────────────────
    "Title card": {
        "segments": 1,
        "structure": ["engagement"],
        "description": "Opening narration that sets context and creates engagement",
        "prompt_directive": """
        NARRATION GOAL: Write an ENGAGING OPENING that sets context.
        
        STRUCTURE (single paragraph):
        1. Hook: Start with a compelling statement or question about the topic
        2. Relevance: Explain why this matters or where it appears in the real world
        3. Preview: Give a brief hint about what's coming next
        
        CONSTRAINTS:
        - Length: 50-80 words
        - Tone: Engaging and conversational, not robotic
        - Do NOT include: Transition phrases, meta-commentary, or "In this slide"
        - Focus on building curiosity and motivation
        """,
    },
    # ─────────────────────────────────────────────────────────────────────
    # IMAGE AND TEXT
    # ─────────────────────────────────────────────────────────────────────
    "Image and text": {
        "segments": 3,
        "structure": ["visual_context", "interpretation", "application"],
        "description": "Explain visual elements and connect them to concepts",
        "prompt_directive": """
        NARRATION GOAL: Explain the visual and connect it to learning objectives.
        
        STRUCTURE (3 segments):
        Segment 1 [VISUAL CONTEXT]: Describe what the student sees and focus their attention
        Segment 2 [INTERPRETATION]: Explain what this shows and why it matters
        Segment 3 [APPLICATION]: Connect the visual to real-world use or next concept
        
        CONSTRAINTS:
        - Exactly 3 segments separated by double newlines
        - Each segment: 30-45 words
        - Guide the visual explanation, don't just read text
        - Build a narrative arc: See → Understand → Apply
        """,
    },
    # ─────────────────────────────────────────────────────────────────────
    # TEXT AND IMAGE
    # ─────────────────────────────────────────────────────────────────────
    "Text and image": {
        "segments": 3,
        "structure": ["concept_intro", "visual_explanation", "synthesis"],
        "description": "Introduce concept first, then explain visual representation",
        "prompt_directive": """
        NARRATION GOAL: Build understanding through concept first, visual second.
        
        STRUCTURE (3 segments):
        Segment 1 [CONCEPT INTRO]: Introduce the main idea or principle
        Segment 2 [VISUAL EXPLANATION]: Explain how the visual demonstrates the concept
        Segment 3 [SYNTHESIS]: Connect both elements and show significance
        
        CONSTRAINTS:
        - Exactly 3 segments separated by double newlines
        - Each segment: 30-45 words
        - Layer information: Abstract → Concrete → Integrated
        - Create coherence between text and image
        """,
    },
    # ─────────────────────────────────────────────────────────────────────
    # FORMULA BLOCK
    # ─────────────────────────────────────────────────────────────────────
    "Formula block": {
        "segments": 5,
        "structure": ["intro", "components", "interpretation", "application", "significance"],
        "description": "Systematically explain formula, components, and applications",
        "prompt_directive": """
        NARRATION GOAL: Systematically explain the formula and its meaning.
        
        STRUCTURE (5 segments):
        Segment 1 [FORMULA INTRO]: What is this formula called? Why was it developed? What problems does it solve?
        Segment 2 [COMPONENT BREAKDOWN]: What do the variables/symbols represent? What do they measure?
        Segment 3 [INTERPRETATION]: What does the formula tell us? What's the relationship between components?
        Segment 4 [HOW TO USE]: Walk through a concrete example or step-by-step usage
        Segment 5 [SIGNIFICANCE]: Why is this important? Where is it used? What would change if we modified it?
        
        CONSTRAINTS:
        - Exactly 5 segments separated by double newlines
        - Each segment: 35-50 words (segments can be slightly longer for formulas)
        - DO NOT just read the formula aloud
        - Include practical context and intuition
        - Make it relatable with examples or analogies
        """,
    },
}

# Extended narration techniques for richer style variation.
# Keep this separate from NARRATION_TECHNIQUES so sparse-template detection
# remains stable and backward-compatible.
NARRATION_TECHNIQUE_LIBRARY: Dict[str, Dict[str, Any]] = {
    **NARRATION_TECHNIQUES,
    "Title card - question hook": {
        "segments": 1,
        "structure": ["question_hook"],
        "description": "Open with a thought-provoking question and practical relevance",
        "prompt_directive": """
        NARRATION GOAL: Open with a direct question that triggers curiosity.

        STRUCTURE (single paragraph):
        1. Ask one sharp question tied to the topic
        2. Explain why answering it matters in practical terms
        3. Preview what the learner will gain

        CONSTRAINTS:
        - Length: 45-75 words
        - Conversational, energetic tone
        - Avoid generic fillers and meta phrases
        """,
    },
    "Title card - scenario hook": {
        "segments": 1,
        "structure": ["scenario_hook"],
        "description": "Open with a concrete scenario before introducing the lesson",
        "prompt_directive": """
        NARRATION GOAL: Use a mini real-world scenario as the opening hook.

        STRUCTURE (single paragraph):
        1. Describe a quick scenario the learner can picture
        2. Connect that scenario to the lesson topic
        3. Preview the core skill or insight

        CONSTRAINTS:
        - Length: 50-80 words
        - Keep scenario concrete and relatable
        - No "in this slide" phrasing
        """,
    },
    "Image and text - analytical": {
        "segments": 3,
        "structure": ["observe", "analyze", "apply"],
        "description": "Analytical visual walkthrough with evidence-focused interpretation",
        "prompt_directive": """
        NARRATION GOAL: Guide the learner from observation to evidence-based interpretation.

        STRUCTURE (3 segments):
        Segment 1 [OBSERVE]: Direct attention to key visual elements
        Segment 2 [ANALYZE]: Explain patterns/relationships shown in the visual
        Segment 3 [APPLY]: Translate the insight into a practical takeaway

        CONSTRAINTS:
        - Exactly 3 segments separated by double newlines
        - Each segment: 30-45 words
        - Prioritize interpretation over description
        """,
    },
    "Image and text - misconception fix": {
        "segments": 3,
        "structure": ["common_mistake", "correction", "transfer"],
        "description": "Correct a common misunderstanding using the visual as evidence",
        "prompt_directive": """
        NARRATION GOAL: Correct a common misconception with visual evidence.

        STRUCTURE (3 segments):
        Segment 1 [COMMON MISTAKE]: State a likely misunderstanding
        Segment 2 [CORRECTION]: Use the visual to correct it clearly
        Segment 3 [TRANSFER]: Show where this corrected understanding applies

        CONSTRAINTS:
        - Exactly 3 segments separated by double newlines
        - Each segment: 30-45 words
        - Keep tone supportive, never judgmental
        """,
    },
    "Text and image - concept ladder": {
        "segments": 3,
        "structure": ["core_idea", "worked_visual", "rule_of_thumb"],
        "description": "Move from concept to visual grounding and end with a rule-of-thumb",
        "prompt_directive": """
        NARRATION GOAL: Build a concept ladder from abstract idea to practical rule.

        STRUCTURE (3 segments):
        Segment 1 [CORE IDEA]: Define the principle in plain language
        Segment 2 [WORKED VISUAL]: Explain how the image makes the principle concrete
        Segment 3 [RULE OF THUMB]: Give a short reusable heuristic

        CONSTRAINTS:
        - Exactly 3 segments separated by double newlines
        - Each segment: 30-45 words
        - Favor clarity and transferability
        """,
    },
    "Text and image - case bridge": {
        "segments": 3,
        "structure": ["setup", "visual_case", "decision"],
        "description": "Bridge concept into a mini case and practical decision",
        "prompt_directive": """
        NARRATION GOAL: Use a mini case to bridge concept and action.

        STRUCTURE (3 segments):
        Segment 1 [SETUP]: Introduce the concept and why it matters
        Segment 2 [VISUAL CASE]: Use the image as a concrete case example
        Segment 3 [DECISION]: State the decision or action informed by this concept

        CONSTRAINTS:
        - Exactly 3 segments separated by double newlines
        - Each segment: 30-45 words
        - Keep examples practical and concise
        """,
    },
    "Formula block - intuition first": {
        "segments": 5,
        "structure": ["intuition", "symbols", "relationship", "example", "boundary"],
        "description": "Explain formula with intuition-first teaching flow",
        "prompt_directive": """
        NARRATION GOAL: Teach the formula through intuition before notation.

        STRUCTURE (5 segments):
        Segment 1 [INTUITION]: Explain the core idea in plain language
        Segment 2 [SYMBOLS]: Map variables to real meanings
        Segment 3 [RELATIONSHIP]: Explain how variables influence each other
        Segment 4 [EXAMPLE]: Work through one concrete use case
        Segment 5 [BOUNDARY]: Explain when the formula is less reliable

        CONSTRAINTS:
        - Exactly 5 segments separated by double newlines
        - Each segment: 35-50 words
        - Avoid reading symbols without interpretation
        """,
    },
    "Formula block - compare and choose": {
        "segments": 5,
        "structure": ["problem", "formula_choice", "components", "worked_example", "tradeoff"],
        "description": "Position formula as a decision tool among alternatives",
        "prompt_directive": """
        NARRATION GOAL: Present the formula as a choice tool, not just a rule.

        STRUCTURE (5 segments):
        Segment 1 [PROBLEM]: State the decision/problem context
        Segment 2 [FORMULA CHOICE]: Explain why this formula fits that context
        Segment 3 [COMPONENTS]: Clarify each component's role
        Segment 4 [WORKED EXAMPLE]: Walk a practical numeric/example case
        Segment 5 [TRADEOFF]: Mention one limitation or tradeoff

        CONSTRAINTS:
        - Exactly 5 segments separated by double newlines
        - Each segment: 35-50 words
        - Keep decision framing practical
        """,
    },
    "Comparison table": {
        "segments": 4,
        "structure": ["comparison_goal", "criteria_walkthrough", "pattern", "decision"],
        "description": "Criteria-by-criteria comparison ending with decision guidance",
        "prompt_directive": """
        NARRATION GOAL: Explain a comparison table without reading every cell.

        STRUCTURE (4 segments):
        Segment 1 [COMPARISON GOAL]: What are we comparing and why?
        Segment 2 [CRITERIA WALKTHROUGH]: Explain 2-3 most important criteria
        Segment 3 [PATTERN]: Highlight the main pattern/tradeoff in the table
        Segment 4 [DECISION]: Recommend when to choose each option

        CONSTRAINTS:
        - Exactly 4 segments separated by double newlines
        - Each segment: 30-45 words
        - Do not read full rows verbatim
        """,
    },
    "Process flow": {
        "segments": 4,
        "structure": ["entry", "step_logic", "failure_point", "execution_tip"],
        "description": "Walk through process logic with bottleneck awareness",
        "prompt_directive": """
        NARRATION GOAL: Teach process flow with causality and execution tips.

        STRUCTURE (4 segments):
        Segment 1 [ENTRY]: Where the process starts and trigger conditions
        Segment 2 [STEP LOGIC]: Why the sequence is ordered this way
        Segment 3 [FAILURE POINT]: Typical bottleneck or mistake and prevention
        Segment 4 [EXECUTION TIP]: Practical tip for smoother execution

        CONSTRAINTS:
        - Exactly 4 segments separated by double newlines
        - Each segment: 30-45 words
        - Emphasize cause-and-effect transitions
        """,
    },
    "Data insight": {
        "segments": 4,
        "structure": ["signal", "evidence", "implication", "action"],
        "description": "Narration optimized for stats and comparative evidence",
        "prompt_directive": """
        NARRATION GOAL: Turn data into insight and action.

        STRUCTURE (4 segments):
        Segment 1 [SIGNAL]: State the key metric shift or pattern
        Segment 2 [EVIDENCE]: Explain the evidence behind that signal
        Segment 3 [IMPLICATION]: What this means in practical terms
        Segment 4 [ACTION]: What a learner/practitioner should do next

        CONSTRAINTS:
        - Exactly 4 segments separated by double newlines
        - Each segment: 30-45 words
        - Avoid metric dumping; focus on meaning
        """,
    },
    "Structural overview": {
        "segments": 4,
        "structure": ["map", "major_nodes", "links", "navigation_tip"],
        "description": "Narration for hierarchy and hub-and-spoke style structures",
        "prompt_directive": """
        NARRATION GOAL: Help learners navigate a structure map efficiently.

        STRUCTURE (4 segments):
        Segment 1 [MAP]: Big-picture structure and purpose
        Segment 2 [MAJOR NODES]: Explain the key nodes/components
        Segment 3 [LINKS]: Explain critical relationships between nodes
        Segment 4 [NAVIGATION TIP]: How to use this structure for problem-solving

        CONSTRAINTS:
        - Exactly 4 segments separated by double newlines
        - Each segment: 30-45 words
        - Emphasize relationships over isolated definitions
        """,
    },
}

# Variant options by template. Selection is deterministic per slide context
# to keep outputs stable and low-latency while increasing style diversity.
NARRATION_TECHNIQUE_VARIANTS: Dict[str, List[str]] = {
    "Title card": [
        "Title card",
        "Title card - question hook",
        "Title card - scenario hook",
    ],
    "Image and text": [
        "Image and text",
        "Image and text - analytical",
        "Image and text - misconception fix",
    ],
    "Text and image": [
        "Text and image",
        "Text and image - concept ladder",
        "Text and image - case bridge",
    ],
    "Formula block": [
        "Formula block",
        "Formula block - intuition first",
        "Formula block - compare and choose",
    ],
    "Comparison table": ["Comparison table"],
    "Process flow": ["Process flow"],
    "Data insight": ["Data insight"],
    "Structural overview": ["Structural overview"],
}

# =============================================================================
# SPARSE TEMPLATE SCHEMAS (STRUCTURE REQUIREMENTS)
# =============================================================================
# These schemas define what block types sparse templates should produce.
# This is the single source of truth used by both the generator and validator.

SPARSE_TEMPLATE_SCHEMAS: Dict[str, Dict[str, Any]] = {
    "Title card": {
        "required_blocks": ["intro_paragraph"],
        "optional_blocks": ["annotation_paragraph"],
        "forbidden_blocks": ["smart_layout", "bullet_list", "table", "numbered_list"],
        "instruction": (
            "Generate ONLY a single intro_paragraph block. "
            "This is a title card — one powerful engagement hook sentence or short paragraph. "
            "No lists, no tables, no smart_layout, no structured content. Just the intro."
        ),
        "max_blocks": 2,
    },
    "Image and text": {
        "required_blocks": ["image"],
        "optional_blocks": ["rich_text", "annotation_paragraph"],
        "forbidden_blocks": ["smart_layout", "bullet_list", "table", "numbered_list"],
        "instruction": (
            "Generate an image block with descriptive alt text and a clear visual description, "
            "followed by optional rich_text block that explains or narrates the visual content. "
            "No smart_layout, no lists, no tables."
        ),
        "max_blocks": 4,
    },
    "Text and image": {
        "required_blocks": ["intro_paragraph", "image"],
        "optional_blocks": ["rich_text", "annotation_paragraph"],
        "forbidden_blocks": ["smart_layout", "bullet_list", "table", "numbered_list"],
        "instruction": (
            "Generate an intro_paragraph that explains the concept first, "
            "then an image block as visual reinforcement with descriptive alt text. "
            "No smart_layout, no lists, no tables."
        ),
        "max_blocks": 4,
    },
    "Formula block": {
        "required_blocks": ["formula_block"],
        "optional_blocks": ["intro_paragraph"],
        "forbidden_blocks": ["smart_layout", "bullet_list", "table", "numbered_list"],
        "instruction": (
            "Generate a formula_block with clear notation and visual structure. "
            "Optionally include an intro_paragraph above it to introduce the formula. "
            "No smart_layout, no lists, no tables. Formula should be visually prominent."
        ),
        "max_blocks": 2,
        "requires_wide_block": True,
        "allowed_layouts": ["top", "bottom"],
    },
    "Comparison table": {
        "required_blocks": ["comparison_table"],
        "optional_blocks": ["intro_paragraph"],
        "forbidden_blocks": ["smart_layout", "bullet_list", "table", "numbered_list"],
        "instruction": (
            "Generate a comparison_table as the primary wide block. "
            "Optionally include one intro_paragraph above it for context. "
            "Keep total content blocks to at most 2."
        ),
        "max_blocks": 2,
        "requires_wide_block": True,
        "allowed_layouts": ["top", "bottom"],
    },
    "Split panel": {
        "required_blocks": ["split_panel"],
        "optional_blocks": ["intro_paragraph"],
        "forbidden_blocks": ["smart_layout", "bullet_list", "table", "numbered_list"],
        "instruction": (
            "Generate a split_panel as the primary wide block. "
            "Optionally include one intro_paragraph above it for context. "
            "Keep total content blocks to at most 2."
        ),
        "max_blocks": 2,
        "requires_wide_block": True,
        "allowed_layouts": ["top", "bottom"],
    },
    "Hierarchy tree": {
        "required_blocks": ["hierarchy_tree"],
        "optional_blocks": ["intro_paragraph"],
        "forbidden_blocks": ["smart_layout", "bullet_list", "table", "numbered_list"],
        "instruction": (
            "Generate a hierarchy_tree as the primary wide block. "
            "Optionally include one intro_paragraph above it for context. "
            "Keep total content blocks to at most 2."
        ),
        "max_blocks": 2,
        "requires_wide_block": True,
        "allowed_layouts": ["top", "bottom"],
    },
    "Hub and spoke": {
        "required_blocks": ["hub_and_spoke"],
        "optional_blocks": ["intro_paragraph"],
        "forbidden_blocks": ["smart_layout", "bullet_list", "table", "numbered_list"],
        "instruction": (
            "Generate a hub_and_spoke as the primary wide block. "
            "Optionally include one intro_paragraph above it for context. "
            "Keep total content blocks to at most 2."
        ),
        "max_blocks": 2,
        "requires_wide_block": True,
        "allowed_layouts": ["top", "bottom"],
    },
    "Process arrow block": {
        "required_blocks": ["process_arrow_block"],
        "optional_blocks": ["intro_paragraph"],
        "forbidden_blocks": ["smart_layout", "bullet_list", "table", "numbered_list"],
        "instruction": (
            "Generate a process_arrow_block as the primary wide block. "
            "Optionally include one intro_paragraph above it for context. "
            "Keep total content blocks to at most 2."
        ),
        "max_blocks": 2,
        "requires_wide_block": True,
        "allowed_layouts": ["top", "bottom"],
    },
    "Cyclic process block": {
        "required_blocks": ["cyclic_process_block"],
        "optional_blocks": ["intro_paragraph"],
        "forbidden_blocks": ["smart_layout", "bullet_list", "table", "numbered_list"],
        "instruction": (
            "Generate a cyclic_process_block as the primary wide block. "
            "Optionally include one intro_paragraph above it for context. "
            "Keep total content blocks to at most 2."
        ),
        "max_blocks": 2,
        "requires_wide_block": True,
        "allowed_layouts": ["top", "bottom"],
    },
    "Feature showcase block": {
        "required_blocks": ["feature_showcase_block"],
        "optional_blocks": ["intro_paragraph"],
        "forbidden_blocks": ["smart_layout", "bullet_list", "table", "numbered_list"],
        "instruction": (
            "Generate a feature_showcase_block as the primary wide block. "
            "Optionally include one intro_paragraph above it for context. "
            "Keep total content blocks to at most 2."
        ),
        "max_blocks": 2,
        "requires_wide_block": True,
        "allowed_layouts": ["top", "bottom"],
    },
    "Code": {
        "required_blocks": ["code"],
        "optional_blocks": ["intro_paragraph"],
        "forbidden_blocks": ["smart_layout", "bullet_list", "table", "numbered_list"],
        "instruction": (
            "Generate a code block as the primary wide block. "
            "Optionally include one intro_paragraph above it for context. "
            "Keep total content blocks to at most 2."
        ),
        "max_blocks": 2,
        "requires_wide_block": True,
        "allowed_layouts": ["top", "bottom"],
    },
}

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def get_sparse_template_schema(template_name: str) -> Optional[Dict[str, Any]]:
    """
    Returns the sparse template schema if template_name is a sparse template.
    Returns None if it's a standard template.
    Case-insensitive matching.
    
    Args:
        template_name: Name of the template
    
    Returns:
        Schema dict or None if not found
    """
    if not template_name:
        return None
    normalized = template_name.strip().lower()
    for key, schema in SPARSE_TEMPLATE_SCHEMAS.items():
        if key.lower() == normalized:
            return schema
    return None


def is_sparse_template_schema(template_name: str) -> bool:
    """Quick check if a template is sparse (has a predefined schema)."""
    return get_sparse_template_schema(template_name) is not None


def _stable_variant_index(seed_text: str, n: int) -> int:
    """Deterministic low-cost index used for technique variation."""
    if n <= 1:
        return 0
    return sum(ord(ch) for ch in seed_text) % n


def _resolve_technique_key(
    template_name: str,
    title: str = "",
    goal: str = "",
    subtopic: str = "",
) -> Optional[str]:
    """Resolve the concrete technique key for a template with deterministic variation."""
    if not template_name:
        return None

    options = NARRATION_TECHNIQUE_VARIANTS.get(template_name)
    if not options:
        return template_name if template_name in NARRATION_TECHNIQUE_LIBRARY else None

    seed = f"{template_name}|{title}|{goal}|{subtopic}"
    idx = _stable_variant_index(seed, len(options))
    return options[idx]


def get_narration_technique(
    template_name: str,
    title: str = "",
    goal: str = "",
    subtopic: str = "",
) -> Optional[Dict[str, Any]]:
    """
    Get the narration technique for a specific template.
    
    Args:
        template_name: Name of the slide template (e.g., "Title card", "Formula block")
    
    Returns:
        Dictionary with technique metadata or None if not found
    """
    technique_key = _resolve_technique_key(template_name, title, goal, subtopic)
    if not technique_key:
        return None
    return NARRATION_TECHNIQUE_LIBRARY.get(technique_key)


def is_sparse_template(template_name: str) -> bool:
    """
    Check if a template is sparse (doesn't have a primary teaching block).
    
    Args:
        template_name: Name of the slide template
    
    Returns:
        True if the template is sparse, False otherwise
    """
    return template_name in NARRATION_TECHNIQUES


def get_segment_count(template_name: str) -> int:
    """
    Get the expected number of narration segments for a template.
    
    Args:
        template_name: Name of the slide template
    
    Returns:
        Number of segments expected, or 1 if not found
    """
    technique = get_narration_technique(template_name)
    return technique["segments"] if technique else 1


def build_technique_prompt(
    template_name: str, title: str, goal: str, subtopic: str, context: str = ""
) -> str:
    """
    Build a narration prompt using the technique for a specific template.
    
    Args:
        template_name: Name of the slide template
        title: Slide title
        goal: Slide learning goal
        subtopic: Current subtopic
        context: Optional research context
    
    Returns:
        Formatted prompt directive for the LLM
    """
    technique_key = _resolve_technique_key(template_name, title, goal, subtopic)
    technique = get_narration_technique(template_name, title, goal, subtopic)
    if not technique:
        return ""
    
    segment_info = f"\nExpected: {technique['segments']} segment(s)"
    if technique["segments"] > 1:
        segment_info += f"\nSegment structure: {', '.join(technique['structure'])}"
    
    base_info = f"""
    Slide Title: {title}
    Slide Goal: {goal}
    Subtopic: {subtopic}
    Template: {template_name}
    Technique Variant: {technique_key or template_name}
    {f"Research Context: {context}" if context else ""}
    {segment_info}
    """
    
    return base_info + technique["prompt_directive"]


# =============================================================================
# SPARSE TEMPLATE LIST
# =============================================================================

SPARSE_TEMPLATES = list(NARRATION_TECHNIQUES.keys())
"""List of all sparse template names"""
