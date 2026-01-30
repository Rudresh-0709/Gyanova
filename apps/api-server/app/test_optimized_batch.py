"""
Optimized Batch Narration Approach - Quality Improved

Implements best practices:
1. Few-shot examples
2. Explicit length requirements (150 words min)
3. Strong visual separators
4. Auto-quality gate with individual fallback
"""

import json
import time
from typing import Dict, Any, List
from services.llm.model_loader import load_openai, load_groq_fast
from services.node.narration_node import generate_narration_for_slide, clean_json_output
import os
from dotenv import load_dotenv

load_dotenv()


# ═══════════════════════════════════════════════════════════════════════════
# APPROACH C: OPTIMIZED BATCH (Best Practices)
# ═══════════════════════════════════════════════════════════════════════════


def approach_c_optimized_batch(
    subtopic_data: Dict[str, Any], narration_style: str, difficulty: str
):
    """Optimized batch approach with quality improvements"""
    subtopic_name = subtopic_data.get("subtopic_name")
    slides = subtopic_data.get("slides", [])

    start_time = time.time()
    llm = load_openai()

    # FEW-SHOT EXAMPLES (from high-quality outputs)
    FEW_SHOT_EXAMPLES = """
EXAMPLE 1 (Good Quality - 125 words):
Slide: "Introduction to Computer Generations"
Narration: "Understanding computer generations is like tracing the exciting journey of how technology has evolved over time. Each generation marks a significant leap in how computers are built and how they perform, reflecting breakthroughs in hardware and software. By exploring these generations, we not only appreciate the incredible progress made but also gain insight into the foundations of modern computing. This knowledge helps us see why today's devices work the way they do and inspires us to imagine what the future might hold."

EXAMPLE 2 (Good Quality - 143 words):
Slide: "What Are Vacuum Tubes?"
Narration: "Vacuum tubes are electronic components that played a crucial role in the earliest computers by controlling electric current flow. Essentially, they act like tiny switches or amplifiers, allowing or blocking the passage of electrons in a vacuum inside a sealed glass tube. This ability to switch and amplify signals made them the fundamental building blocks for processing information in first-generation computers. However, vacuum tubes were quite large, generated a lot of heat, and were prone to failure, which eventually led to the development of more reliable technologies. Understanding vacuum tubes helps us appreciate how early computing machines operated and the challenges engineers faced during that pioneering era."
"""

    # Build enhanced batch prompt with visual separators
    slides_info = []
    for i, slide in enumerate(slides, 1):
        slide_block = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 SLIDE {i} OF {len(slides)}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 METADATA:
- Title: {slide.get('slide_title')}
- Purpose: {slide.get('slide_purpose')}
- Narration Role: {slide.get('narration_role')}
- Narration Goal: {slide.get('narration_goal')}
- Template: {slide.get('selected_template')}
- Format: {slide.get('narration_format', 'points')}
- Constraints: {slide.get('narration_constraints', {})}

⚠️ CRITICAL REQUIREMENTS:
1. Generate 120-180 WORDS for this narration
2. Treat this slide INDEPENDENTLY (do not reference other slides)
3. Follow the narration role: {slide.get('narration_role')}
4. Match the style: {narration_style}

🎤 YOUR NARRATION FOR SLIDE {i}:
[Write 120-180 words here]
"""
        slides_info.append(slide_block)

    ENHANCED_BATCH_PROMPT = f"""
You are an expert teacher generating spoken narrations for multiple slides in a lesson.

🎯 CONTEXT:
- Subtopic: {subtopic_name}
- Difficulty: {difficulty}
- Narration Style: {narration_style}
- Total Slides: {len(slides)}

📚 FEW-SHOT EXAMPLES OF QUALITY NARRATIONS:
{FEW_SHOT_EXAMPLES}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚡ CRITICAL INSTRUCTIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. **LENGTH REQUIREMENT**: Each narration MUST be 120-180 words
   - DO NOT write short 50-word summaries
   - Provide COMPLETE, DETAILED explanations
   - Think of each as a 60-90 second spoken segment

2. **INDEPENDENCE**: Process each slide SEPARATELY
   - Don't say "as mentioned before" or "next we'll see"
   - Treat each as a standalone teaching moment
   
3. **QUALITY OVER SPEED**: Better to write one great narration than six mediocre ones
   - Be thorough, engaging, and pedagogically sound
   - Match the examples above in depth and quality

4. **STYLE CONSISTENCY**: Maintain "{narration_style}" throughout ALL narrations

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 SLIDES TO NARRATE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{chr(10).join(slides_info)}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

OUTPUT FORMAT (JSON):
{{
  "narrations": [
    {{
      "slide_number": 1,
      "slide_title": "...",
      "narration_text": "...",
      "word_count": <actual word count>
    }},
    ...
  ]
}}

REMEMBER: Each narration should be 120-180 words. DO NOT CUT CORNERS.
"""

    print(f"  [C] Generating optimized batch narration for {len(slides)} slides...")

    response = llm.invoke(
        [
            {
                "role": "system",
                "content": "You are an expert educational content generator focused on quality and depth.",
            },
            {"role": "user", "content": ENHANCED_BATCH_PROMPT},
        ]
    )

    batch_elapsed = time.time() - start_time

    # Parse batch results
    try:
        cleaned = clean_json_output(response.content)
        batch_result = json.loads(cleaned)
        narrations = batch_result.get("narrations", [])

        # AUTO-QUALITY GATE: Check quality and regenerate if needed
        results = []
        regeneration_count = 0

        for i, slide in enumerate(slides):
            if i < len(narrations):
                narration_text = narrations[i].get("narration_text", "")
                word_count = len(narration_text.split())

                # Quality check: word count threshold
                if word_count < 80:
                    print(
                        f"    ⚠️ Slide {i+1} too short ({word_count} words) - regenerating individually..."
                    )
                    regeneration_start = time.time()

                    # FALLBACK: Regenerate individually
                    individual_result = generate_narration_for_slide(
                        slide=slide,
                        subtopic_name=subtopic_name,
                        narration_style=narration_style,
                        difficulty_level=difficulty,
                    )
                    narration_data = {
                        "slide_title": individual_result.get(
                            "slide_title", slide.get("slide_title")
                        ),
                        "narration_text": individual_result.get("narration_text", ""),
                        "regenerated": True,
                        "regeneration_time": time.time() - regeneration_start,
                    }
                    regeneration_count += 1
                else:
                    narration_data = {
                        "slide_title": narrations[i].get(
                            "slide_title", slide.get("slide_title")
                        ),
                        "narration_text": narration_text,
                        "regenerated": False,
                    }
            else:
                # Missing narration - regenerate individually
                print(f"    ⚠️ Slide {i+1} missing from batch - regenerating...")
                individual_result = generate_narration_for_slide(
                    slide=slide,
                    subtopic_name=subtopic_name,
                    narration_style=narration_style,
                    difficulty_level=difficulty,
                )
                narration_data = {
                    "slide_title": individual_result.get(
                        "slide_title", slide.get("slide_title")
                    ),
                    "narration_text": individual_result.get("narration_text", ""),
                    "regenerated": True,
                }
                regeneration_count += 1

            results.append({**slide, **narration_data})

    except Exception as e:
        print(f"  [C] Error parsing batch response: {e}")
        # Full fallback: regenerate all individually
        results = []
        for slide in slides:
            individual_result = generate_narration_for_slide(
                slide=slide,
                subtopic_name=subtopic_name,
                narration_style=narration_style,
                difficulty_level=difficulty,
            )
            results.append({**slide, **individual_result, "regenerated": True})
        regeneration_count = len(slides)

    total_elapsed = time.time() - start_time

    # API call count: 1 batch + regenerations
    api_calls = 1 + regeneration_count

    print(f"    ✓ Regenerated {regeneration_count}/{len(slides)} slides individually")

    return {
        "approach": "C - Optimized Batch",
        "api_calls": api_calls,
        "time_seconds": round(total_elapsed, 2),
        "batch_time": round(batch_elapsed, 2),
        "regeneration_count": regeneration_count,
        "slides_processed": len(slides),
        "avg_time_per_slide": round(total_elapsed / len(slides), 2),
        "results": results,
    }


# ═══════════════════════════════════════════════════════════════════════════
# IMPORT PREVIOUS APPROACHES
# ═══════════════════════════════════════════════════════════════════════════

from test_narration_batch import approach_a_current


# ═══════════════════════════════════════════════════════════════════════════
# COMPREHENSIVE TEST
# ═══════════════════════════════════════════════════════════════════════════


def run_comprehensive_test(test_data: Dict[str, Any]):
    """Test all three approaches"""

    print("\n" + "=" * 80)
    print("COMPREHENSIVE NARRATION OPTIMIZATION TEST")
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

        # Test Approach A (Current - Baseline)
        print("\n🔵 APPROACH A (Current - Per Slide):")
        result_a = approach_a_current(subtopic_data, narration_style, difficulty)

        # Test Approach C (Optimized Batch)
        print("\n🟢 APPROACH C (Optimized Batch with Quality Gate):")
        result_c = approach_c_optimized_batch(
            subtopic_data, narration_style, difficulty
        )

        # Compare
        print("\n📊 COMPARISON:")
        print(
            f"   API Calls:     A = {result_a['api_calls']} | C = {result_c['api_calls']}"
        )
        print(
            f"   Time:          A = {result_a['time_seconds']}s | C = {result_c['time_seconds']}s"
        )
        print(
            f"   Speedup:       {round(result_a['time_seconds'] / result_c['time_seconds'], 2)}x"
            if result_c["time_seconds"] > 0
            else ""
        )
        print(f"   Regenerations: {result_c['regeneration_count']}/{num_slides}")

        # Word count comparison
        avg_words_a = sum(
            len(r.get("narration_text", "").split()) for r in result_a["results"]
        ) / len(result_a["results"])
        avg_words_c = sum(
            len(r.get("narration_text", "").split()) for r in result_c["results"]
        ) / len(result_c["results"])
        print(f"   Avg Words:     A = {avg_words_a:.0f} | C = {avg_words_c:.0f}")

        all_results.append(
            {"subtopic": subtopic_name, "approach_a": result_a, "approach_c": result_c}
        )

    # Final Summary
    print("\n" + "=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)

    total_a_calls = sum(r["approach_a"]["api_calls"] for r in all_results)
    total_c_calls = sum(r["approach_c"]["api_calls"] for r in all_results)
    total_a_time = sum(r["approach_a"]["time_seconds"] for r in all_results)
    total_c_time = sum(r["approach_c"]["time_seconds"] for r in all_results)

    print(f"Total API Calls:  A = {total_a_calls} | C = {total_c_calls}")
    print(f"Total Time:       A = {total_a_time:.2f}s | C = {total_c_time:.2f}s")
    print(
        f"Overall Speedup:  {round(total_a_time / total_c_time, 2)}x"
        if total_c_time > 0
        else ""
    )
    print(
        f"Call Reduction:   {round((1 - total_c_calls/total_a_calls) * 100, 1)}%"
        if total_a_calls > 0
        else ""
    )

    return all_results


# ═══════════════════════════════════════════════════════════════════════════
# MAIN EXECUTION
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import os as os_module

    script_dir = os_module.path.dirname(os_module.path.abspath(__file__))
    workflow_file = os_module.path.join(
        script_dir, "computer_generations_workflow_output.json"
    )
    results_file = os_module.path.join(script_dir, "optimized_batch_test_results.json")

    # Load test data
    with open(workflow_file, "r", encoding="utf-8") as f:
        workflow_output = json.load(f)

    test_state = {
        "narration_style": workflow_output.get(
            "narration_style", "Friendly and engaging"
        ),
        "difficulty": workflow_output.get("difficulty", "Intermediate"),
        "slide_plan": {},
    }

    # Test with 2 subtopics
    slide_plan = workflow_output.get("slide_plan", {})
    for i, (sub_id, sub_data) in enumerate(slide_plan.items()):
        if i < 2:
            test_state["slide_plan"][sub_id] = sub_data

    # Run test
    results = run_comprehensive_test(test_state)

    # Save results
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Results saved to: {results_file}")
    print("\n🔬 Next: Run quality evaluation to compare A vs C")
