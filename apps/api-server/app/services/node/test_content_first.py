"""
Content-First Pipeline Test Harness

Tests the full content-first generation pipeline on a SINGLE subtopic
across different subjects (science, history, geography, CS, math).

Usage:
  python test_content_first.py                  # runs "science" by default
  python test_content_first.py history           # runs the history test case
  python test_content_first.py all               # runs ALL test cases sequentially

Output:
  - Prints the full state dict as formatted JSON
  - Saves state to test_output_<subject>.json
"""

import json
import sys
import os

# Fix import paths — go from node/ up to api-server/
script_dir = os.path.dirname(os.path.abspath(__file__))
# node/ -> services/ -> app/ -> api-server/ (3 levels)
api_server_root = os.path.abspath(os.path.join(script_dir, "..", "..", ".."))
if api_server_root not in sys.path:
    sys.path.insert(0, api_server_root)

from app.services.node.content_generation_node import content_generation_node

# ═══════════════════════════════════════════════════════════════════════════
# TEST CASES — one subtopic per subject, with diverse slide plans
# ═══════════════════════════════════════════════════════════════════════════

TEST_CASES = {
    "science": {
        "topic": "Light and Optics",
        "subtopic": {
            "id": "sci-01",
            "name": "Refraction of Light",
            "difficulty": "Intermediate",
        },
        "plans": {
            "sci-01": [
                {
                    "title": "What is Refraction?",
                    "intent": "concept",
                    "purpose": "definition",
                    "selected_template": "Title with bullets",
                    "role": "Introduce",
                    "goal": "Define refraction and why light bends when passing between media",
                    "content_angle": "overview",
                },
                {
                    "title": "Snell's Law",
                    "intent": "concept",
                    "purpose": "explanation",
                    "selected_template": "Formula block",
                    "role": "Guide",
                    "goal": "Explain Snell's law formula and its variables",
                    "content_angle": "mechanism",
                },
                {
                    "title": "Total Internal Reflection",
                    "intent": "process",
                    "purpose": "visualization",
                    "selected_template": "Process steps",
                    "role": "Guide",
                    "goal": "Show how total internal reflection occurs step by step",
                    "content_angle": "mechanism",
                },
                {
                    "title": "Real-World Applications",
                    "intent": "example",
                    "purpose": "application",
                    "selected_template": "Card grid with icons",
                    "role": "Connector",
                    "goal": "Show practical uses like fiber optics, mirages, and lenses",
                    "content_angle": "application",
                },
                {
                    "title": "Key Takeaways",
                    "intent": "summary",
                    "purpose": "review",
                    "selected_template": "Title with bullets",
                    "role": "Summarizer",
                    "goal": "Summarize the key concepts of refraction",
                    "content_angle": "summary",
                },
            ]
        },
    },
    "history": {
        "topic": "World War II",
        "subtopic": {
            "id": "hist-01",
            "name": "Causes of World War II",
            "difficulty": "Intermediate",
        },
        "plans": {
            "hist-01": [
                {
                    "title": "The Treaty of Versailles",
                    "intent": "concept",
                    "purpose": "context",
                    "selected_template": "Title with bullets",
                    "role": "Introduce",
                    "goal": "Explain how the Treaty of Versailles created resentment in Germany",
                    "content_angle": "overview",
                },
                {
                    "title": "Rise of Fascism",
                    "intent": "process",
                    "purpose": "visualization",
                    "selected_template": "Timeline",
                    "role": "Guide",
                    "goal": "Show the chronological rise of fascism in Europe",
                    "content_angle": "mechanism",
                },
                {
                    "title": "Appeasement vs Confrontation",
                    "intent": "comparison",
                    "purpose": "analysis",
                    "selected_template": "Comparison",
                    "role": "Analyzer",
                    "goal": "Compare the appeasement and confrontation strategies",
                    "content_angle": "comparison",
                },
                {
                    "title": "Key Events Leading to War",
                    "intent": "process",
                    "purpose": "visualization",
                    "selected_template": "Timeline",
                    "role": "Guide",
                    "goal": "Timeline of key events from 1933 to 1939",
                    "content_angle": "mechanism",
                },
            ]
        },
    },
    "geography": {
        "topic": "Plate Tectonics",
        "subtopic": {
            "id": "geo-01",
            "name": "Tectonic Plate Boundaries",
            "difficulty": "Beginner",
        },
        "plans": {
            "geo-01": [
                {
                    "title": "What Are Tectonic Plates?",
                    "intent": "concept",
                    "purpose": "definition",
                    "selected_template": "Title with bullets",
                    "role": "Introduce",
                    "goal": "Define tectonic plates and their role in Earth's structure",
                    "content_angle": "overview",
                },
                {
                    "title": "Types of Plate Boundaries",
                    "intent": "comparison",
                    "purpose": "classification",
                    "selected_template": "Card grid with icons",
                    "role": "Guide",
                    "goal": "Compare convergent, divergent, and transform boundaries",
                    "content_angle": "comparison",
                },
                {
                    "title": "How Mountains Form",
                    "intent": "process",
                    "purpose": "visualization",
                    "selected_template": "Process steps",
                    "role": "Guide",
                    "goal": "Explain the process of mountain formation at convergent boundaries",
                    "content_angle": "mechanism",
                },
                {
                    "title": "Earthquake and Volcano Zones",
                    "intent": "data",
                    "purpose": "visualization",
                    "selected_template": "Stats with icons",
                    "role": "Connector",
                    "goal": "Show key statistics about earthquake zones and volcanic activity",
                    "content_angle": "visualization",
                },
            ]
        },
    },
    "cs": {
        "topic": "Data Structures",
        "subtopic": {
            "id": "cs-01",
            "name": "Binary Search Trees",
            "difficulty": "Intermediate",
        },
        "plans": {
            "cs-01": [
                {
                    "title": "What is a Binary Search Tree?",
                    "intent": "concept",
                    "purpose": "definition",
                    "selected_template": "Definition",
                    "role": "Introduce",
                    "goal": "Define BST and its core properties",
                    "content_angle": "overview",
                },
                {
                    "title": "BST Operations",
                    "intent": "process",
                    "purpose": "explanation",
                    "selected_template": "Process steps",
                    "role": "Guide",
                    "goal": "Explain insert, search, and delete operations",
                    "content_angle": "mechanism",
                },
                {
                    "title": "BST vs Other Data Structures",
                    "intent": "comparison",
                    "purpose": "analysis",
                    "selected_template": "Comparison",
                    "role": "Analyzer",
                    "goal": "Compare BST with arrays, linked lists, and hash tables",
                    "content_angle": "comparison",
                },
                {
                    "title": "Time Complexity Analysis",
                    "intent": "data",
                    "purpose": "analysis",
                    "selected_template": "Stats with icons",
                    "role": "Guide",
                    "goal": "Show best/average/worst case time complexities",
                    "content_angle": "visualization",
                },
            ]
        },
    },
    "math": {
        "topic": "Calculus",
        "subtopic": {
            "id": "math-01",
            "name": "Derivatives",
            "difficulty": "Intermediate",
        },
        "plans": {
            "math-01": [
                {
                    "title": "What is a Derivative?",
                    "intent": "concept",
                    "purpose": "definition",
                    "selected_template": "Title with bullets",
                    "role": "Introduce",
                    "goal": "Define the derivative as the rate of change",
                    "content_angle": "overview",
                },
                {
                    "title": "The Power Rule",
                    "intent": "concept",
                    "purpose": "explanation",
                    "selected_template": "Formula block",
                    "role": "Guide",
                    "goal": "Explain the power rule formula d/dx(x^n) = nx^(n-1)",
                    "content_angle": "mechanism",
                },
                {
                    "title": "Differentiation Rules",
                    "intent": "concept",
                    "purpose": "explanation",
                    "selected_template": "Key-Value list",
                    "role": "Guide",
                    "goal": "List the key differentiation rules: sum, product, quotient, chain",
                    "content_angle": "overview",
                },
                {
                    "title": "Real-World Applications of Derivatives",
                    "intent": "example",
                    "purpose": "application",
                    "selected_template": "Card grid with icons",
                    "role": "Connector",
                    "goal": "Show practical uses like velocity, optimization, and economics",
                    "content_angle": "application",
                },
            ]
        },
    },
}


def build_state(test_case: dict) -> dict:
    """Build initial state from a test case."""
    subtopic = test_case["subtopic"]
    return {
        "topic": test_case["topic"],
        "sub_topics": [subtopic],
        "difficulty": subtopic.get("difficulty", "Beginner"),
        "plans": test_case["plans"],
        "slides": {},
        "layout_history": [],
        "angle_history": [],
    }


def summarize_state(state: dict, subject: str):
    """Print a clean summary of the generated slides."""
    print("\n" + "=" * 70)
    print(f"  RESULTS: {subject.upper()} — {state.get('topic', 'N/A')}")
    print("=" * 70)

    for sub_id, slides in state.get("slides", {}).items():
        for i, slide in enumerate(slides):
            blocks = slide.get("gyml_content", {}).get("contentBlocks", [])
            block_types = [b.get("type", "?") for b in blocks]
            primary_idx = slide.get("primary_block_index", "?")
            primary_type = (
                blocks[primary_idx].get("type", "?")
                if isinstance(primary_idx, int) and primary_idx < len(blocks)
                else "?"
            )

            # Get variant if smart_layout
            if (
                primary_type == "smart_layout"
                and isinstance(primary_idx, int)
                and primary_idx < len(blocks)
            ):
                primary_type += f"/{blocks[primary_idx].get('variant', '?')}"

            narration_segments = len(
                [s for s in slide.get("narration_text", "").split("\n\n") if s.strip()]
            )

            print(f"\n  Slide {i+1}: {slide.get('title')}")
            print(f"    Intent:       {slide.get('intent', '?')}")
            print(f"    Angle:        {slide.get('content_angle', '?')}")
            print(f"    Template:     {slide.get('selected_template', '?')}")
            print(f"    Density:      {slide.get('slide_density', '?')}")
            print(f"    Blocks:       {' → '.join(block_types)}")
            print(f"    Primary:      [{primary_idx}] {primary_type}")
            print(
                f"    Animation:    {slide.get('animation_unit_count', '?')} x {slide.get('animation_unit', '?')}"
            )
            print(
                f"    Narration:    {narration_segments} segments, {len(slide.get('narration_text', ''))} chars"
            )

    print("\n" + "=" * 70)


def clean_state_for_output(state: dict) -> dict:
    """Create a slimmed-down version of state for JSON output."""
    output = {
        "topic": state.get("topic"),
        "slides": {},
    }
    for sub_id, slides in state.get("slides", {}).items():
        output["slides"][sub_id] = []
        for slide in slides:
            output["slides"][sub_id].append(
                {
                    "title": slide.get("title"),
                    "intent": slide.get("intent"),
                    "content_angle": slide.get("content_angle"),
                    "selected_template": slide.get("selected_template"),
                    "slide_density": slide.get("slide_density"),
                    "primary_block_index": slide.get("primary_block_index"),
                    "animation_unit": slide.get("animation_unit"),
                    "animation_unit_count": slide.get("animation_unit_count"),
                    "animated_block_index": slide.get("animated_block_index"),
                    "gyml_content": slide.get("gyml_content"),
                    "narration_text": slide.get("narration_text"),
                }
            )
    return output


def run_test(subject: str):
    """Run the content-first pipeline on a single subject."""
    if subject not in TEST_CASES:
        print(f"Unknown subject: {subject}. Available: {', '.join(TEST_CASES.keys())}")
        return

    test_case = TEST_CASES[subject]
    print(f"\n{'#' * 70}")
    print(f"# TESTING: {subject.upper()} — {test_case['topic']}")
    print(f"# Subtopic: {test_case['subtopic']['name']}")
    print(f"# Slides: {len(list(test_case['plans'].values())[0])}")
    print(f"{'#' * 70}\n")

    # Build and run
    state = build_state(test_case)

    # Run content generation for all slides (loop until all done)
    max_iterations = 10
    for iteration in range(max_iterations):
        state = content_generation_node(state)
        # Check if all slides are generated
        sub_id = test_case["subtopic"]["id"]
        planned = len(test_case["plans"][sub_id])
        generated = len(state.get("slides", {}).get(sub_id, []))
        if generated >= planned:
            break

    # Summary
    summarize_state(state, subject)

    # Save full state
    output = clean_state_for_output(state)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    out_path = os.path.join(script_dir, f"test_output_{subject}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\n  📁 Full state saved to: {out_path}")


if __name__ == "__main__":
    subject = sys.argv[1] if len(sys.argv) > 1 else "science"

    if subject == "all":
        for subj in TEST_CASES:
            run_test(subj)
    else:
        run_test(subject)
