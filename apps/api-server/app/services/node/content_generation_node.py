"""
Content Generation Node (Content-First Architecture)

Generates structured visual content and then spoken narration.

Flow (Content-First):
- Input: Slide plan with title, goal, template, content_angle
- Step 1: Generate GyML visual content from learning objectives
- Step 2: Generate narration AFTER to explain the generated visuals
- Output: Structured content + narration, ready for rendering
"""

import json
import re
from typing import Dict, Any, List
import os
import sys  # Need this for all path manipulations
from dotenv import load_dotenv
from tavily import TavilyClient

try:
    from ..llm.model_loader import load_groq, load_groq_fast, load_openai, load_gemini
    from ..state import TutorState
except ImportError:
    # Fallback for direct script execution
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from llm.model_loader import load_groq, load_groq_fast, load_openai, load_gemini
    from state import TutorState

# Import segment counting for narration↔content alignment
try:
    from .audio_generation_node import segment_narration
except ImportError:
    from audio_generation_node import segment_narration

# Import icon selector
try:
    from ..icon_selector import select_icons_batch
    from .slides.gyml.generator import GyMLContentGenerator
except ImportError:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from icon_selector import select_icons_batch
    from services.node.slides.gyml.generator import GyMLContentGenerator

load_dotenv()
tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

# Initialize generator
gyml_generator = GyMLContentGenerator()


# ═══════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════


def should_fact_check(slide_title: str, slide_purpose: str, subtopic_name: str) -> bool:
    """Determines if this slide needs Tavily fact-checking."""
    fact_check_keywords = [
        "generation",
        "history",
        "timeline",
        "evolution",
        "year",
        "date",
        "version",
        "release",
        "statistics",
        "data",
        "percentage",
        "number",
        "event",
        "discovery",
        "invention",
        "founder",
        "origin",
    ]

    combined = f"{slide_title} {slide_purpose} {subtopic_name}".lower()
    return any(keyword in combined for keyword in fact_check_keywords)


def load_llm_schema() -> str:
    """Load the LLM content schema."""
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        schema_path = os.path.join(current_dir, "slides", "gyml", "llm_schema.json")
        with open(schema_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"   ⚠ Failed to load LLM schema: {e}")
        return "{}"


def _summarize_content_for_narration(gyml_content: Dict[str, Any]) -> str:
    """
    Extract a concise summary of the generated visual content
    so the narration LLM knows what is on the slide.
    """
    blocks = gyml_content.get("contentBlocks", [])
    primary_idx = gyml_content.get("primary_block_index", 0)
    summary_parts = []

    for i, block in enumerate(blocks):
        block_type = block.get("type", "unknown")
        is_primary = "(PRIMARY)" if i == primary_idx else ""

        if block_type in (
            "paragraph",
            "intro_paragraph",
            "context_paragraph",
            "annotation_paragraph",
            "outro_paragraph",
            "caption",
        ):
            text = block.get("text", "")
            summary_parts.append(f"  [{block_type}] {text[:80]}...")
        elif block_type == "smart_layout":
            variant = block.get("variant", "unknown")
            items = block.get("items", [])
            item_headings = [
                item.get("heading", item.get("description", ""))[:40]
                for item in items[:6]
            ]
            summary_parts.append(
                f"  [{block_type}/{variant}] {is_primary} {len(items)} items: {', '.join(item_headings)}"
            )
        elif block_type in ("key_value_list", "numbered_list"):
            items = block.get("items", [])
            summary_parts.append(f"  [{block_type}] {is_primary} {len(items)} items")
        elif block_type == "formula_block":
            expr = block.get("expression", "")
            summary_parts.append(f"  [{block_type}] {is_primary} {expr}")
        elif block_type in ("comparison", "comparison_table"):
            summary_parts.append(f"  [{block_type}] {is_primary}")
        elif block_type in ("hierarchy_tree", "labeled_diagram", "split_panel"):
            summary_parts.append(f"  [{block_type}] {is_primary}")
        else:
            summary_parts.append(f"  [{block_type}] {is_primary}")

    return "\n".join(summary_parts) if summary_parts else "No content blocks found."


def _count_primary_items(gyml_content: Dict[str, Any]) -> int:
    """Count the number of items in the primary block for narration alignment."""
    blocks = gyml_content.get("contentBlocks", [])
    primary_idx = gyml_content.get("primary_block_index", 0)

    if not blocks or primary_idx >= len(blocks):
        return 1

    primary = blocks[primary_idx]
    block_type = primary.get("type", "")

    if block_type == "smart_layout":
        return len(primary.get("items", []))
    elif block_type in ("key_value_list", "numbered_list", "bullet_list", "step_list"):
        return len(primary.get("items", []))
    elif block_type in ("comparison", "comparison_table"):
        return len(primary.get("rows", primary.get("items", []))) or 2
    elif block_type == "hierarchy_tree":
        root = primary.get("root", {})
        return len(root.get("children", [])) or 1
    elif block_type == "formula_block":
        return len(primary.get("variables", [])) + 1  # formula + variables
    else:
        return 1


# ═══════════════════════════════════════════════════════════════════════════
# ANIMATION METADATA
# ═══════════════════════════════════════════════════════════════════════════

# Maps block type (or smart_layout variant) to a semantic animation unit name
BLOCK_TYPE_TO_ANIMATION_UNIT = {
    # Smart layout variants
    "bigBullets": "bullet",
    "bulletIcon": "bullet",
    "bulletCheck": "bullet",
    "bulletCross": "bullet",
    "timeline": "step",
    "timelineHorizontal": "step",
    "timelineSequential": "step",
    "timelineMilestone": "step",
    "cardGrid": "card",
    "cardGridIcon": "card",
    "cardGridSimple": "card",
    "cardGridImage": "card",
    "processSteps": "step",
    "processArrow": "step",
    "processAccordion": "step",
    "comparison": "side",
    "comparisonProsCons": "side",
    "comparisonBeforeAfter": "side",
    "stats": "stat",
    "statsComparison": "stat",
    "statsPercentage": "stat",
    "quote": "quote",
    "quoteTestimonial": "quote",
    "quoteCitation": "quote",
    "definition": "definition",
    "codeSnippet": "line",
    "codeComparison": "line",
    "diagramFlowchart": "node",
    "diagramHierarchy": "node",
    "diagramCycle": "node",
    "diagramPyramid": "layer",
    "table": "row",
    "tableStriped": "row",
    "tableHighlight": "row",
    # Top-level block types
    "bullet_list": "bullet",
    "numbered_list": "item",
    "key_value_list": "pair",
    "step_list": "step",
    "comparison_table": "row",
    "hierarchy_tree": "node",
    "labeled_diagram": "label",
    "formula_block": "term",
    "split_panel": "panel",
    "rich_text": "paragraph",
    "hub_and_spoke": "spoke",
    "process_arrow_block": "step",
    "cyclic_process_block": "phase",
    "feature_showcase_block": "feature",
}


def _generate_animation_metadata(gyml_content: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate animation metadata from the primary block.
    Only the primary block gets animated; other blocks appear statically.

    Returns:
        {
            "animation_unit": "bullet" | "step" | "card" | ...,
            "animation_unit_count": int,
            "animated_block_index": int
        }
    """
    blocks = gyml_content.get("contentBlocks", [])
    primary_idx = gyml_content.get("primary_block_index", 0)

    if not blocks or primary_idx >= len(blocks):
        return {
            "animation_unit": "item",
            "animation_unit_count": 1,
            "animated_block_index": 0,
        }

    primary = blocks[primary_idx]
    block_type = primary.get("type", "")
    item_count = _count_primary_items(gyml_content)

    # Determine animation unit
    if block_type == "smart_layout":
        variant = primary.get("variant", "cardGrid")
        animation_unit = BLOCK_TYPE_TO_ANIMATION_UNIT.get(variant, "item")
    else:
        animation_unit = BLOCK_TYPE_TO_ANIMATION_UNIT.get(block_type, "item")

    return {
        "animation_unit": animation_unit,
        "animation_unit_count": item_count,
        "animated_block_index": primary_idx,
    }


# ═══════════════════════════════════════════════════════════════════════════
# PRIMARY BLOCK VALIDATION
# ═══════════════════════════════════════════════════════════════════════════

# Canonical set of block types that qualify as a primary teaching structure
VALID_PRIMARY_BLOCK_TYPES = {
    # Smart layout (always valid — variant determines the animation unit)
    "smart_layout",
    # Top-level structured blocks
    "bullet_list",
    "numbered_list",
    "numbered_steps",
    "step_list",
    "timeline",
    "comparison_table",
    "comparison",
    "icon_grid",
    "card_grid",
    "cards",
    "diagram",
    "labeled_diagram",
    "hierarchy_tree",
    "key_value_list",
    "stats",
    "split_panel",
    "formula_block",
    "rich_text",
    "table",
    "hub_and_spoke",
    "process_arrow_block",
    "cyclic_process_block",
    "feature_showcase_block",
    "code",
}


def _validate_and_ensure_primary_block(
    generated_content: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Validate that the generated content has a valid primary block.

    Returns:
        The content dict with a corrected primary_block_index, or
        None if no structured blocks exist (signals regeneration needed).
    """
    blocks = generated_content.get("contentBlocks", [])
    idx = generated_content.get("primary_block_index")

    # ── Check 1: Does primary_block_index exist and point to a valid block? ──
    if (
        idx is not None
        and isinstance(idx, int)
        and 0 <= idx < len(blocks)
        and blocks[idx].get("type") in VALID_PRIMARY_BLOCK_TYPES
    ):
        print(f"    ✓ Primary block valid: [{idx}] {blocks[idx].get('type')}")
        return generated_content

    # ── Check 2: Infer — find the first structured block ──
    for i, block in enumerate(blocks):
        if block.get("type") in VALID_PRIMARY_BLOCK_TYPES:
            print(
                f"    ⚠ Primary block inferred: [{i}] {block.get('type')} (was idx={idx})"
            )
            generated_content["primary_block_index"] = i
            return generated_content

    # ── Check 3: No structured blocks at all — signal regeneration ──
    print("    ✗ No valid primary block found. Regeneration needed.")
    return None


def _extract_primary_items_detail(gyml_content: Dict[str, Any]) -> List[str]:
    """
    Extract a list of item labels/headings from the primary block
    so the narration LLM can write one segment per item.
    """
    blocks = gyml_content.get("contentBlocks", [])
    primary_idx = gyml_content.get("primary_block_index", 0)

    if not blocks or primary_idx >= len(blocks):
        return ["Main content"]

    primary = blocks[primary_idx]
    block_type = primary.get("type", "")
    items_detail = []

    if block_type == "smart_layout":
        for item in primary.get("items", []):
            heading = item.get("heading", item.get("label", item.get("title", "")))
            desc = item.get("description", "")
            items_detail.append(f"{heading}: {desc[:60]}" if heading else desc[:80])
    elif block_type in ("key_value_list",):
        for item in primary.get("items", []):
            items_detail.append(f"{item.get('key', '')}: {item.get('value', '')[:60]}")
    elif block_type in ("numbered_list", "bullet_list", "step_list"):
        for item in primary.get("items", []):
            title = item.get("title", item.get("text", ""))
            items_detail.append(title[:80])
    elif block_type in ("comparison", "comparison_table"):
        for row in primary.get("rows", primary.get("items", [])):
            items_detail.append(str(row)[:80])
    elif block_type == "hierarchy_tree":
        root = primary.get("root", {})
        for child in root.get("children", []):
            items_detail.append(child.get("label", "")[:80])
    elif block_type == "formula_block":
        items_detail.append(f"Formula: {primary.get('expression', '')}")
        for var in primary.get("variables", []):
            items_detail.append(
                f"{var.get('name', '')}: {var.get('definition', '')[:60]}"
            )
    else:
        items_detail.append("Main content")

    return items_detail if items_detail else ["Main content"]


def generate_narration(
    title: str,
    goal: str,
    role: str,
    subtopic_name: str,
    gyml_content: Dict[str, Any],
    context: str = "",
    template_name: str = "",
) -> str:
    """
    Generates spoken narration for a slide AFTER the visual content is created.
    Produces exactly N segments (one per primary block item), separated by double newlines.
    """
    llm = load_openai()

    # Extract primary block details
    primary_item_count = _count_primary_items(gyml_content)
    primary_items = _extract_primary_items_detail(gyml_content)
    animation_meta = _generate_animation_metadata(gyml_content)
    animation_unit = animation_meta["animation_unit"]

    # Build item listing for the prompt
    items_listing = "\n".join(
        [
            f"  {animation_unit.upper()} {i+1}: {item}"
            for i, item in enumerate(primary_items)
        ]
    )

    # Define sparse templates
    SPARSE_TEMPLATES = [
        "Title card",
        "Image and text",
        "Text and image",
        "Rich text",
        "Formula block",
        "Definition",
        "Quote",
    ]
    is_sparse = template_name in SPARSE_TEMPLATES

    prompt = f"""
    You are an expert teacher. Write the spoken narration for a slide.
    The slide's visual content has already been designed. Your job is to EXPLAIN what the student sees.
    
    CONTEXT:
    - Subtopic: {subtopic_name}
    - Slide Title: {title}
    - Slide Goal: {goal}
    - Teacher Role: {role}
    - Slide Template: {template_name}
    {f"📚 RESEARCH CONTEXT:\\n{context}" if context else ""}

    {"" if is_sparse else f"""═══════════════════════════════════════════════
    PRIMARY BLOCK ITEMS (the animated content the student sees one-by-one):
    ═══════════════════════════════════════════════
{items_listing}
    """}

    {f'''STRUCTURE RULES (SPARSE TEMPLATE):
    1. Write a SINGLE, high-impact, engaging paragraph.
    2. Length: 40-70 words.
    3. Focus on a broad overview or a strong takeaway.
    4. Do NOT split into multiple segments.''' if is_sparse else f'''STRUCTURE RULES (SEGMENT-ALIGNED):
    The slide has {primary_item_count} animated {animation_unit}s that appear one-by-one.
    You MUST write EXACTLY {primary_item_count} narration segments — one per {animation_unit}.

    CRITICAL FORMAT RULES:
    1. Write EXACTLY {primary_item_count} segments.
    2. SEPARATE each segment with exactly TWO newlines (blank line between segments).
    3. Each segment should be 25-40 words long.
    4. Segment 1 explains {animation_unit.upper()} 1, Segment 2 explains {animation_unit.upper()} 2, etc.
    5. Total length: {primary_item_count * 30}-{primary_item_count * 45} words.

    EXAMPLE FORMAT ({primary_item_count} segments):
    [Explanation of {animation_unit} 1 — adds context, insight, or analogy beyond the on-screen text]

    [Explanation of {animation_unit} 2 — explains why this matters or how it connects]

    [Explanation of {animation_unit} 3 — provides deeper understanding]
    {"..." if primary_item_count > 3 else ""}'''}

    CONTENT RULES:
    1. Write exactly what the teacher would say out loud.
    2. EXPLAIN each item — don't just read the on-screen text. Add WHY, analogies, and real-world context.
    3. Be engaging, clear, and pedagogically sound.
    4. NO markdown, NO "In this slide", NO "Moving on".
    5. Do NOT use transition markers like "First,", "Second,", "Third,", "Next,", or "Finally,".
    6. Each segment should stand on its own as a mini-explanation of its corresponding {animation_unit}.
    """

    resp = llm.invoke([{"role": "user", "content": prompt}])

    # DEBUG: Show raw narration output
    print("\n--- [DEBUG] NARRATION LLM OUTPUT ---")
    print(resp.content)
    print("--------------------------------------\n")

    narration = resp.content.strip()

    # Post-generation validation: ensure correct segment count
    if not is_sparse:
        segments = [s.strip() for s in narration.split("\n\n") if s.strip()]
        if len(segments) != primary_item_count:
            print(
                f"    ⚠ Segment mismatch: expected {primary_item_count}, got {len(segments)}"
            )
            # Pad if too few
            while len(segments) < primary_item_count:
                segments.append(
                    f"This {animation_unit} continues the explanation of {title}."
                )
            # Truncate if too many
            segments = segments[:primary_item_count]
            narration = "\n\n".join(segments)

    return narration


# ═══════════════════════════════════════════════════════════════════════════
# CORE GENERATION LOGIC (CONTENT-FIRST)
# ═══════════════════════════════════════════════════════════════════════════


def content_generation_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Content-First Generation Node.
    Step 1: Generate GyML visual content from learning objectives.
    Step 2: Generate narration to explain the generated visuals.
    """
    BATCH_SIZE = 2

    sub_topics = state.get("sub_topics", [])
    difficulty = state.get("difficulty", "Beginner")
    plans = state.get("plans", {})

    if "slides" not in state:
        state["slides"] = {}
    if "layout_history" not in state:
        state["layout_history"] = []
    if "angle_history" not in state:
        state["angle_history"] = []

    # ── Find the next subtopic + slide offset to generate ────────────
    next_subtopic = None
    start_offset = 0

    for sub in sub_topics:
        sub_id = sub["id"]
        planned_count = len(plans.get(sub_id, []))
        generated_count = len(state["slides"].get(sub_id, []))
        if generated_count < planned_count:
            next_subtopic = sub
            start_offset = generated_count
            break

    if not next_subtopic:
        print("✅ [Content Gen] All slides already have content.")
        return state

    sub_id = next_subtopic.get("id")
    subtopic_name = next_subtopic.get("name")
    sub_difficulty = next_subtopic.get("difficulty", difficulty)

    slide_concepts = plans.get(sub_id, [])

    # Initialize slides list for this subtopic if needed
    if sub_id not in state["slides"]:
        state["slides"][sub_id] = []

    # Determine batch range
    end_offset = min(start_offset + BATCH_SIZE, len(slide_concepts))

    print(
        f"\n🎬 [Batch Gen] Subtopic: {subtopic_name} | Slides {start_offset + 1}-{end_offset} of {len(slide_concepts)}"
    )
    layout_history = state["layout_history"]
    angle_history = state["angle_history"]

    for i in range(start_offset, end_offset):
        concept = slide_concepts[i]
        title = concept.get("title")
        goal = concept.get("goal")

        print(f"  📝 Generating Slide {i + 1}: {title}")

        # ── STEP 1: Fact Check if needed ──
        search_context = ""
        if should_fact_check(title, "explanation", subtopic_name):
            try:
                search_query = f"{subtopic_name} {title} verified facts and details"
                search_results = tavily.search(query=search_query, max_results=3)
                search_context = json.dumps(search_results.get("results", []), indent=2)
            except Exception as e:
                print(f"    ⚠ Search failed: {e}")

        # ── STEP 2: Generate GyML Content (CONTENT-FIRST) + Validate ──
        selected_template = concept.get("selected_template", "")
        MAX_RETRIES = 2
        generated_content = None

        for attempt in range(MAX_RETRIES):
            raw_content = gyml_generator.generate(
                title=title,
                goal=goal,
                purpose=concept.get("purpose", "explain"),
                subtopic=subtopic_name,
                content_angle=concept.get("content_angle", "overview"),
                context=search_context,
                layout_history=layout_history,
                template_name=selected_template,
            )

            validated = _validate_and_ensure_primary_block(raw_content)
            if validated is not None:
                generated_content = validated
                break
            else:
                if attempt < MAX_RETRIES - 1:
                    print(
                        f"    🔄 Regenerating slide (attempt {attempt + 2}/{MAX_RETRIES})..."
                    )

        # Final fallback if all retries failed
        if generated_content is None:
            print("    ✗ All retries failed. Using fallback slide.")
            generated_content = {
                "title": title,
                "intent": "explain",
                "contentBlocks": [
                    {
                        "type": "intro_paragraph",
                        "text": f"Let's explore {title}.",
                    },
                    {
                        "type": "smart_layout",
                        "variant": "bigBullets",
                        "items": [{"heading": "Key Point", "description": goal}],
                    },
                ],
                "primary_block_index": 1,
                "imagePrompt": f"Abstract educational illustration representing {subtopic_name}",
            }

        primary_items = _count_primary_items(generated_content)
        print(
            f"    → Content generated: {len(generated_content.get('contentBlocks', []))} blocks, primary has {primary_items} items"
        )

        # ── STEP 3: Generate Narration (AFTER content) ──
        role = concept.get("role", "Guide")
        narration = generate_narration(
            title=title,
            goal=goal,
            role=role,
            subtopic_name=subtopic_name,
            gyml_content=generated_content,
            context=search_context,
            template_name=selected_template,
        )

        # Update layout history
        blocks = generated_content.get("contentBlocks", [])
        smart_layout = next(
            (b for b in blocks if b.get("type") == "smart_layout"), None
        )
        if smart_layout:
            layout_history.append(smart_layout.get("variant", "unknown"))
        else:
            layout_history.append(generated_content.get("intent", "explain"))

        # Update angle history
        angle_history.append(concept.get("content_angle", "overview"))

        if len(layout_history) > 10:
            layout_history.pop(0)
        if len(angle_history) > 10:
            angle_history.pop(0)

        state["layout_history"] = layout_history
        state["angle_history"] = angle_history

        # ── STEP 4: Generate Animation Metadata ──
        animation_meta = _generate_animation_metadata(generated_content)
        print(
            f"    → Animation: {animation_meta['animation_unit_count']} x {animation_meta['animation_unit']}"
        )

        # ── STEP 5: Store ──
        slide_obj = {
            **concept,
            "subtopic_name": subtopic_name,
            "narration_text": narration,
            "gyml_content": generated_content,
            "visual_content": generated_content,
            "primary_block_index": generated_content.get("primary_block_index", 0),
            "animation_unit": animation_meta["animation_unit"],
            "animation_unit_count": animation_meta["animation_unit_count"],
            "animated_block_index": animation_meta["animated_block_index"],
        }
        state["slides"][sub_id].append(slide_obj)

    return state
