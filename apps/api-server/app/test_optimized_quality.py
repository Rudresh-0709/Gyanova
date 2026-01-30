"""
Quality Evaluation: Approach A vs Approach C (Optimized Batch)
"""

import json
import sys

sys.path.append(".")

from test_narration_quality import (
    calculate_basic_metrics,
    check_prohibited_phrases,
    compare_narrations_head_to_head,
)


def evaluate_a_vs_c(results_file: str, output_file: str):
    """Compare quality between Approach A and Approach C"""

    with open(results_file, "r", encoding="utf-8") as f:
        test_results = json.load(f)

    print("\n" + "=" * 80)
    print("QUALITY EVALUATION: Approach A vs Approach C")
    print("=" * 80)

    all_comparisons = []

    for subtopic_result in test_results:
        subtopic_name = subtopic_result["subtopic"]
        approach_a_slides = subtopic_result["approach_a"]["results"]
        approach_c_slides = subtopic_result["approach_c"]["results"]

        print(f"\n📚 Evaluating: {subtopic_name}")
        print("-" * 80)

        for i, (slide_a, slide_c) in enumerate(
            zip(approach_a_slides, approach_c_slides), 1
        ):
            slide_title = slide_a.get("slide_title")
            narration_a = slide_a.get("narration_text", "")
            narration_c = slide_c.get("narration_text", "")

            print(f"\n  Slide {i}: {slide_title}")

            # Word counts
            words_a = len(narration_a.split())
            words_c = len(narration_c.split())
            print(f"    Words: A={words_a} | C={words_c}")

            # Head-to-head comparison
            print("    Running LLM comparison...")
            comparison = compare_narrations_head_to_head(
                narration_a, narration_c, slide_a
            )

            result = {
                "slide_title": slide_title,
                "approach_a": {
                    "narration": narration_a,
                    "word_count": words_a,
                    "llm_score": comparison.get("a_score", 5),
                },
                "approach_c": {
                    "narration": narration_c,
                    "word_count": words_c,
                    "llm_score": comparison.get("b_score", 5),
                    "regenerated": slide_c.get("regenerated", False),
                },
                "comparison": comparison,
            }

            all_comparisons.append(result)

            # Print summary
            print(
                f"    Winner: {comparison['winner']} (Confidence: {comparison['confidence']}/10)"
            )
            print(
                f"    Scores: A={comparison['a_score']}/10, C={comparison['b_score']}/10)"
            )

    # Overall statistics
    print("\n" + "=" * 80)
    print("OVERALL QUALITY COMPARISON")
    print("=" * 80)

    a_wins = sum(1 for c in all_comparisons if c["comparison"]["winner"] == "A")
    c_wins = sum(1 for c in all_comparisons if c["comparison"]["winner"] == "B")
    ties = sum(1 for c in all_comparisons if c["comparison"]["winner"] == "TIE")

    avg_score_a = sum(c["approach_a"]["llm_score"] for c in all_comparisons) / len(
        all_comparisons
    )
    avg_score_c = sum(c["approach_c"]["llm_score"] for c in all_comparisons) / len(
        all_comparisons
    )

    avg_words_a = sum(c["approach_a"]["word_count"] for c in all_comparisons) / len(
        all_comparisons
    )
    avg_words_c = sum(c["approach_c"]["word_count"] for c in all_comparisons) / len(
        all_comparisons
    )

    print(f"\nHead-to-Head Results:")
    print(f"  Approach A Wins: {a_wins}")
    print(f"  Approach C Wins: {c_wins}")
    print(f"  Ties: {ties}")

    print(f"\nAverage Quality Scores:")
    print(f"  Approach A: {avg_score_a:.2f}/10")
    print(f"  Approach C: {avg_score_c:.2f}/10")
    print(f"  Difference: {abs(avg_score_a - avg_score_c):.2f} points")

    print(f"\nAverage Word Count:")
    print(f"  Approach A: {avg_words_a:.1f} words")
    print(f"  Approach C: {avg_words_c:.1f} words")

    # Quality verdict
    print(f"\n{'='*80}")
    if abs(avg_score_a - avg_score_c) < 0.5:
        verdict = "✅ QUALITY IS EQUIVALENT - Optimized batch maintains quality!"
        status = "SUCCESS"
    elif avg_score_c > avg_score_a:
        verdict = f"🎉 OPTIMIZED BATCH IS BETTER - {(avg_score_c - avg_score_a):.1f} points higher!"
        status = "EXCELLENT"
    elif avg_score_a - avg_score_c < 1.0:
        verdict = f"✅ VERY CLOSE - Only {(avg_score_a - avg_score_c):.1f} point difference (acceptable)"
        status = "GOOD"
    else:
        verdict = (
            f"⚠️ Current approach has {(avg_score_a - avg_score_c):.1f} point advantage"
        )
        status = "NEEDS_IMPROVEMENT"

    print(f"VERDICT: {verdict}")
    print("=" * 80)

    # Save report
    report = {
        "summary": {
            "a_wins": a_wins,
            "c_wins": c_wins,
            "ties": ties,
            "avg_score_a": round(avg_score_a, 2),
            "avg_score_c": round(avg_score_c, 2),
            "score_difference": round(abs(avg_score_a - avg_score_c), 2),
            "avg_words_a": round(avg_words_a, 1),
            "avg_words_c": round(avg_words_c, 1),
            "verdict": verdict,
            "status": status,
        },
        "detailed_comparisons": all_comparisons,
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Detailed quality report saved to: {output_file}")

    return report


if __name__ == "__main__":
    import os

    script_dir = os.path.dirname(os.path.abspath(__file__))
    results_file = os.path.join(script_dir, "optimized_batch_test_results.json")
    quality_report = os.path.join(script_dir, "optimized_quality_report.json")

    evaluate_a_vs_c(results_file, quality_report)
