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
        "optional_blocks": ["intro_paragraph", "annotation_paragraph"],
        "forbidden_blocks": ["smart_layout", "bullet_list", "table", "numbered_list"],
        "instruction": (
            "Generate a formula_block with clear notation and visual structure. "
            "Optionally include an intro_paragraph above it to introduce the formula. "
            "No smart_layout, no lists, no tables. Formula should be visually prominent."
        ),
        "max_blocks": 3,
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


def get_narration_technique(template_name: str) -> Optional[Dict[str, Any]]:
    """
    Get the narration technique for a specific template.
    
    Args:
        template_name: Name of the slide template (e.g., "Title card", "Formula block")
    
    Returns:
        Dictionary with technique metadata or None if not found
    """
    return NARRATION_TECHNIQUES.get(template_name)


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
    technique = get_narration_technique(template_name)
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
    {f"Research Context: {context}" if context else ""}
    {segment_info}
    """
    
    return base_info + technique["prompt_directive"]


# =============================================================================
# SPARSE TEMPLATE LIST
# =============================================================================

SPARSE_TEMPLATES = list(NARRATION_TECHNIQUES.keys())
"""List of all sparse template names"""
