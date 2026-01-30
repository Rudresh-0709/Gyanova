"""
Test Script: Narration Node - Current vs Batch Approach

Compares:
- Approach A (Current): 1 LLM call per slide
- Approach B (Batch): 1 LLM call per subtopic (all slides at once)

Measures: Time, API calls, and output quality
"""

import json
import time
from typing import Dict, Any, List
from services.llm.model_loader import load_openai, load_groq_fast
from services.node.narration_node import (
    generate_narration_for_slide,
    should_use_search,
    clean_json_output,
)
from tavily import TavilyClient
import os
from dotenv import load_dotenv

load_dotenv()
tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))


# ═══════════════════════════════════════════════════════════════════════════
# APPROACH A: CURRENT (Per-Slide)
# ═══════════════════════════════════════════════════════════════════════════


def approach_a_current(
    subtopic_data: Dict[str, Any], narration_style: str, difficulty: str
):
    """Current approach: 1 LLM call per slide"""
    subtopic_name = subtopic_data.get("subtopic_name")
    slides = subtopic_data.get("slides", [])

    start_time = time.time()
    api_calls = 0
    results = []

    for slide in slides:
        print(f"  [A] Generating narration for: {slide.get('slide_title')}")

        # Generate narration (this makes 1-2 LLM calls per slide)
        narration_data = generate_narration_for_slide(
            slide=slide,
            subtopic_name=subtopic_name,
            narration_style=narration_style,
            difficulty_level=difficulty,
        )

        api_calls += 1  # Main narration call

        # Check if fact-checking was used
        decision = should_use_search(slide, subtopic_name)
        if decision.get("needs_search", False):
            api_calls += 1  # Fact-check decision call

        results.append({**slide, **narration_data})

    elapsed = time.time() - start_time

    return {
        "approach": "A - Current (Per-Slide)",
        "api_calls": api_calls,
        "time_seconds": round(elapsed, 2),
        "slides_processed": len(slides),
        "avg_time_per_slide": round(elapsed / len(slides), 2),
        "results": results,
    }


# ═══════════════════════════════════════════════════════════════════════════
# APPROACH B: BATCH (Per-Subtopic)
# ═══════════════════════════════════════════════════════════════════════════


def approach_b_batch(
    subtopic_data: Dict[str, Any], narration_style: str, difficulty: str
):
    """Optimized approach: 1 LLM call for all slides in subtopic"""
    subtopic_name = subtopic_data.get("subtopic_name")
    slides = subtopic_data.get("slides", [])

    start_time = time.time()
    llm = load_openai()

    # Build batch prompt for all slides
    slides_info = []
    for i, slide in enumerate(slides, 1):
        slide_info = f"""
Slide {i}:
- Title: {slide.get('slide_title')}
- Purpose: {slide.get('slide_purpose')}
- Narration Role: {slide.get('narration_role')}
- Narration Goal: {slide.get('narration_goal')}
- Template: {slide.get('selected_template')}
- Format: {slide.get('narration_format', 'points')}
- Constraints: {slide.get('narration_constraints', {})}
"""
        slides_info.append(slide_info)

    BATCH_PROMPT = f"""
You are an expert teacher generating spoken narrations for multiple slides in a subtopic.

🎯 CONTEXT:
- Subtopic: {subtopic_name}
- Difficulty: {difficulty}
- Narration Style: {narration_style}
- Total Slides: {len(slides)}

📋 SLIDES TO NARRATE:
{chr(10).join(slides_info)}

🧩 REQUIREMENTS:
1. Generate narration for ALL {len(slides)} slides
2. Each narration should be SPOKEN text (what the teacher says)
3. Follow the narration role, goal, and format for each slide
4. Maintain consistency across slides
5. Don't say "In this slide" or mention slide transitions
6. Match the style: {narration_style}

OUTPUT FORMAT:
Return ONLY valid JSON with this structure:
{{
  "narrations": [
    {{
      "slide_number": 1,
      "slide_title": "...",
      "narration_text": "..."
    }},
    ...
  ]
}}
"""

    print(f"  [B] Generating batch narration for {len(slides)} slides...")

    response = llm.invoke(
        [
            {
                "role": "system",
                "content": "You are an expert educational content generator.",
            },
            {"role": "user", "content": BATCH_PROMPT},
        ]
    )

    elapsed = time.time() - start_time

    try:
        cleaned = clean_json_output(response.content)
        batch_result = json.loads(cleaned)
        narrations = batch_result.get("narrations", [])

        # Merge with original slide metadata
        results = []
        for i, slide in enumerate(slides):
            if i < len(narrations):
                narration_data = {
                    "slide_title": narrations[i].get(
                        "slide_title", slide.get("slide_title")
                    ),
                    "narration_text": narrations[i].get("narration_text", ""),
                }
            else:
                narration_data = {
                    "slide_title": slide.get("slide_title"),
                    "narration_text": "Narration generation failed.",
                }
            results.append({**slide, **narration_data})

    except Exception as e:
        print(f"  [B] Error parsing batch response: {e}")
        results = slides

    return {
        "approach": "B - Batch (Per-Subtopic)",
        "api_calls": 1,  # Only 1 call for entire subtopic
        "time_seconds": round(elapsed, 2),
        "slides_processed": len(slides),
        "avg_time_per_slide": round(elapsed / len(slides), 2),
        "results": results,
    }


# ═══════════════════════════════════════════════════════════════════════════
# TEST RUNNER
# ═══════════════════════════════════════════════════════════════════════════


def run_comparison_test(test_data: Dict[str, Any]):
    """Run both approaches and compare results"""

    print("\n" + "=" * 80)
    print("NARRATION NODE BATCH OPTIMIZATION TEST")
    print("=" * 80)

    narration_style = test_data.get("narration_style", "Clear and engaging")
    difficulty = test_data.get("difficulty", "Intermediate")
    slide_plan = test_data.get("slide_plan", {})

    all_results = []

    for sub_id, subtopic_data in slide_plan.items():
        subtopic_name = subtopic_data.get("subtopic_name")
        num_slides = len(subtopic_data.get("slides", []))

        print(f"\n📚 Testing Subtopic: {subtopic_name}")
        print(f"   Slides: {num_slides}")
        print("-" * 80)

        # Test Approach A
        print("\n🔵 APPROACH A (Current - Per Slide):")
        result_a = approach_a_current(subtopic_data, narration_style, difficulty)

        # Test Approach B
        print("\n🟢 APPROACH B (Batch - Per Subtopic):")
        result_b = approach_b_batch(subtopic_data, narration_style, difficulty)

        # Compare
        print("\n📊 COMPARISON:")
        print(
            f"   API Calls:  A = {result_a['api_calls']} | B = {result_b['api_calls']}"
        )
        print(
            f"   Time:       A = {result_a['time_seconds']}s | B = {result_b['time_seconds']}s"
        )
        print(
            f"   Speedup:    {round(result_a['time_seconds'] / result_b['time_seconds'], 2)}x faster"
            if result_b["time_seconds"] > 0
            else ""
        )
        print(
            f"   Savings:    {result_a['api_calls'] - result_b['api_calls']} fewer API calls"
        )

        all_results.append(
            {"subtopic": subtopic_name, "approach_a": result_a, "approach_b": result_b}
        )

    # Final Summary
    print("\n" + "=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)

    total_a_calls = sum(r["approach_a"]["api_calls"] for r in all_results)
    total_b_calls = sum(r["approach_b"]["api_calls"] for r in all_results)
    total_a_time = sum(r["approach_a"]["time_seconds"] for r in all_results)
    total_b_time = sum(r["approach_b"]["time_seconds"] for r in all_results)

    print(f"Total API Calls:  A = {total_a_calls} | B = {total_b_calls}")
    print(f"Total Time:       A = {total_a_time:.2f}s | B = {total_b_time:.2f}s")
    print(
        f"Overall Speedup:  {round(total_a_time / total_b_time, 2)}x"
        if total_b_time > 0
        else ""
    )
    print(
        f"Call Reduction:   {round((1 - total_b_calls/total_a_calls) * 100, 1)}%"
        if total_a_calls > 0
        else ""
    )

    return all_results


# ═══════════════════════════════════════════════════════════════════════════
# MAIN EXECUTION
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import os as os_module

    # Get absolute path to workflow output
    script_dir = os_module.path.dirname(os_module.path.abspath(__file__))
    workflow_file = os_module.path.join(
        script_dir, "computer_generations_workflow_output.json"
    )
    results_file = os_module.path.join(script_dir, "narration_batch_test_results.json")

    # Load test data from existing workflow output
    with open(workflow_file, "r") as f:
        workflow_output = json.load(f)

    # Extract slide plan (use only 1-2 subtopics for quick testing)
    test_state = {
        "narration_style": workflow_output.get(
            "narration_style", "Friendly and engaging"
        ),
        "difficulty": workflow_output.get("difficulty", "Intermediate"),
        "slide_plan": {},
    }

    # Take first 2 subtopics for testing
    slide_plan = workflow_output.get("slide_plan", {})
    for i, (sub_id, sub_data) in enumerate(slide_plan.items()):
        if i < 2:  # Test with 2 subtopics
            test_state["slide_plan"][sub_id] = sub_data

    # Run the test
    results = run_comparison_test(test_state)

    # Save detailed results
    with open("narration_batch_test_results.json", "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Detailed results saved to: narration_batch_test_results.json")
