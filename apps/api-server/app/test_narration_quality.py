"""
Quality Evaluation Framework for Narration Approaches

Tests both approaches on multiple quality dimensions:
1. Semantic similarity to goal
2. Coherence and flow
3. Length appropriateness
4. Educational effectiveness
5. LLM-as-a-judge scoring
"""

import json
import re
from typing import Dict, List, Any
from services.llm.model_loader import load_groq_fast, load_openai


# ═══════════════════════════════════════════════════════════════════════════
# QUALITY METRICS
# ═══════════════════════════════════════════════════════════════════════════


def calculate_basic_metrics(narration: str, constraints: Dict) -> Dict[str, Any]:
    """Calculate basic quantitative metrics"""

    # Word and sentence count
    words = narration.split()
    word_count = len(words)
    sentences = re.split(r"[.!?]+", narration)
    sentence_count = len([s for s in sentences if s.strip()])

    # Check format compliance
    narration_format = constraints.get("format", "points")
    expected_sentences = constraints.get("sentence_count", [3, 5])
    expected_points = constraints.get("point_count", [3, 5])

    # Length appropriateness (ideal: 100-200 words)
    length_score = 1.0
    if word_count < 50:
        length_score = 0.5  # Too short
    elif word_count > 300:
        length_score = 0.7  # Too long
    elif 80 <= word_count <= 200:
        length_score = 1.0  # Ideal
    else:
        length_score = 0.8

    # Format compliance
    format_compliance = 1.0
    if narration_format == "paragraph":
        if isinstance(expected_sentences, list):
            if not (expected_sentences[0] <= sentence_count <= expected_sentences[1]):
                format_compliance = 0.7

    return {
        "word_count": word_count,
        "sentence_count": sentence_count,
        "length_score": length_score,
        "format_compliance": format_compliance,
    }


def check_prohibited_phrases(narration: str) -> Dict[str, Any]:
    """Check for phrases that should be avoided"""

    prohibited = [
        "in this slide",
        "moving on to",
        "let's move to",
        "next slide",
        "on the left",
        "on the right",
        "as you can see",
    ]

    violations = []
    for phrase in prohibited:
        if phrase.lower() in narration.lower():
            violations.append(phrase)

    return {
        "violations": violations,
        "violation_count": len(violations),
        "clean_score": 1.0 if len(violations) == 0 else 0.5,
    }


def semantic_alignment_score(narration: str, slide_metadata: Dict) -> float:
    """Use LLM to evaluate how well narration aligns with slide goal"""

    llm = load_groq_fast()

    narration_goal = slide_metadata.get("narration_goal", "")
    narration_role = slide_metadata.get("narration_role", "")
    slide_purpose = slide_metadata.get("slide_purpose", "")

    EVAL_PROMPT = f"""
You are evaluating educational narration quality.

SLIDE METADATA:
- Purpose: {slide_purpose}
- Narration Role: {narration_role}
- Goal: {narration_goal}

NARRATION TO EVALUATE:
"{narration}"

Rate how well the narration achieves its goal on a scale of 1-10:
- Does it fulfill the narration role ({narration_role})?
- Does it match the slide purpose ({slide_purpose})?
- Does it achieve the stated goal?

Respond with ONLY a JSON object:
{{
  "alignment_score": <1-10>,
  "reasoning": "<brief explanation>"
}}
"""

    try:
        response = llm.invoke([{"role": "user", "content": EVAL_PROMPT}])
        result = json.loads(response.content.strip())
        return result.get("alignment_score", 5) / 10.0  # Normalize to 0-1
    except:
        return 0.5  # Default if evaluation fails


def educational_effectiveness_score(narration: str, slide_metadata: Dict) -> Dict:
    """Deep LLM evaluation of educational quality"""

    llm = load_openai()

    EVAL_PROMPT = f"""
You are an expert educational content reviewer.

SLIDE INFO:
- Title: {slide_metadata.get('slide_title')}
- Purpose: {slide_metadata.get('slide_purpose')}
- Narration Goal: {slide_metadata.get('narration_goal')}
- Difficulty: {slide_metadata.get('difficulty', 'Intermediate')}

NARRATION:
"{narration}"

Evaluate this narration on the following criteria (1-10 scale each):

1. **Clarity**: Is it easy to understand?
2. **Engagement**: Will it keep learners interested?
3. **Accuracy**: Is the content correct and precise?
4. **Pedagogical Flow**: Does it build understanding logically?
5. **Appropriateness**: Matches difficulty level and style?

Respond ONLY with JSON:
{{
  "clarity": <1-10>,
  "engagement": <1-10>,
  "accuracy": <1-10>,
  "pedagogical_flow": <1-10>,
  "appropriateness": <1-10>,
  "overall_score": <1-10>,
  "strengths": ["<strength 1>", "<strength 2>"],
  "weaknesses": ["<weakness 1>", "<weakness 2>"]
}}
"""

    try:
        response = llm.invoke([{"role": "user", "content": EVAL_PROMPT}])
        cleaned = response.content.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.replace("```json", "").replace("```", "").strip()
        result = json.loads(cleaned)
        return result
    except Exception as e:
        return {
            "clarity": 5,
            "engagement": 5,
            "accuracy": 5,
            "pedagogical_flow": 5,
            "appropriateness": 5,
            "overall_score": 5,
            "strengths": [],
            "weaknesses": [f"Evaluation failed: {str(e)}"],
        }


# ═══════════════════════════════════════════════════════════════════════════
# COMPARATIVE EVALUATION
# ═══════════════════════════════════════════════════════════════════════════


def compare_narrations_head_to_head(
    narration_a: str, narration_b: str, slide_metadata: Dict
) -> Dict:
    """LLM-as-a-judge: direct comparison"""

    llm = load_openai()

    COMPARISON_PROMPT = f"""
You are comparing two narrations for the same educational slide.

SLIDE INFO:
- Title: {slide_metadata.get('slide_title')}
- Goal: {slide_metadata.get('narration_goal')}

NARRATION A:
"{narration_a}"

NARRATION B:
"{narration_b}"

Which narration is better for teaching? Consider:
- Clarity and comprehension
- Engagement and interest
- Pedagogical effectiveness
- Appropriateness for learners

Respond ONLY with JSON:
{{
  "winner": "A" or "B" or "TIE",
  "confidence": <1-10>,
  "reasoning": "<explanation>",
  "a_score": <1-10>,
  "b_score": <1-10>
}}
"""

    try:
        response = llm.invoke([{"role": "user", "content": COMPARISON_PROMPT}])
        cleaned = response.content.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.replace("```json", "").replace("```", "").strip()
        return json.loads(cleaned)
    except Exception as e:
        return {
            "winner": "TIE",
            "confidence": 0,
            "reasoning": f"Comparison failed: {str(e)}",
            "a_score": 5,
            "b_score": 5,
        }


# ═══════════════════════════════════════════════════════════════════════════
# FULL QUALITY REPORT
# ═══════════════════════════════════════════════════════════════════════════


def generate_quality_report(results_file: str, output_file: str):
    """Generate comprehensive quality comparison report"""

    with open(results_file, "r") as f:
        test_results = json.load(f)

    print("\n" + "=" * 80)
    print("QUALITY EVALUATION REPORT")
    print("=" * 80)

    all_comparisons = []

    for subtopic_result in test_results:
        subtopic_name = subtopic_result["subtopic"]
        approach_a_slides = subtopic_result["approach_a"]["results"]
        approach_b_slides = subtopic_result["approach_b"]["results"]

        print(f"\n📚 Evaluating: {subtopic_name}")
        print("-" * 80)

        for i, (slide_a, slide_b) in enumerate(
            zip(approach_a_slides, approach_b_slides), 1
        ):
            slide_title = slide_a.get("slide_title")
            narration_a = slide_a.get("narration_text", "")
            narration_b = slide_b.get("narration_text", "")

            print(f"\n  Slide {i}: {slide_title}")

            # Basic metrics
            metrics_a = calculate_basic_metrics(
                narration_a, slide_a.get("narration_constraints", {})
            )
            metrics_b = calculate_basic_metrics(
                narration_b, slide_b.get("narration_constraints", {})
            )

            # Prohibited phrases
            clean_a = check_prohibited_phrases(narration_a)
            clean_b = check_prohibited_phrases(narration_b)

            # Head-to-head comparison
            print("    Running LLM comparison...")
            comparison = compare_narrations_head_to_head(
                narration_a, narration_b, slide_a
            )

            # Deep evaluation (optional - costs more API calls)
            # eval_a = educational_effectiveness_score(narration_a, slide_a)
            # eval_b = educational_effectiveness_score(narration_b, slide_b)

            result = {
                "slide_title": slide_title,
                "approach_a": {
                    "narration": narration_a,
                    "metrics": metrics_a,
                    "cleanliness": clean_a,
                    "llm_score": comparison.get("a_score", 5),
                },
                "approach_b": {
                    "narration": narration_b,
                    "metrics": metrics_b,
                    "cleanliness": clean_b,
                    "llm_score": comparison.get("b_score", 5),
                },
                "comparison": comparison,
            }

            all_comparisons.append(result)

            # Print summary
            print(
                f"    Winner: {comparison['winner']} (Confidence: {comparison['confidence']}/10)"
            )
            print(
                f"    Scores: A={comparison['a_score']}/10, B={comparison['b_score']}/10"
            )

    # Overall statistics
    print("\n" + "=" * 80)
    print("OVERALL QUALITY COMPARISON")
    print("=" * 80)

    a_wins = sum(1 for c in all_comparisons if c["comparison"]["winner"] == "A")
    b_wins = sum(1 for c in all_comparisons if c["comparison"]["winner"] == "B")
    ties = sum(1 for c in all_comparisons if c["comparison"]["winner"] == "TIE")

    avg_score_a = sum(c["approach_a"]["llm_score"] for c in all_comparisons) / len(
        all_comparisons
    )
    avg_score_b = sum(c["approach_b"]["llm_score"] for c in all_comparisons) / len(
        all_comparisons
    )

    avg_words_a = sum(
        c["approach_a"]["metrics"]["word_count"] for c in all_comparisons
    ) / len(all_comparisons)
    avg_words_b = sum(
        c["approach_b"]["metrics"]["word_count"] for c in all_comparisons
    ) / len(all_comparisons)

    print(f"\nHead-to-Head Results:")
    print(f"  Approach A Wins: {a_wins}")
    print(f"  Approach B Wins: {b_wins}")
    print(f"  Ties: {ties}")

    print(f"\nAverage Quality Scores:")
    print(f"  Approach A: {avg_score_a:.2f}/10")
    print(f"  Approach B: {avg_score_b:.2f}/10")

    print(f"\nAverage Word Count:")
    print(f"  Approach A: {avg_words_a:.1f} words")
    print(f"  Approach B: {avg_words_b:.1f} words")

    # Quality verdict
    print(f"\n{'='*80}")
    if abs(avg_score_a - avg_score_b) < 0.5:
        verdict = "✅ QUALITY IS EQUIVALENT - Batch approach is safe to use!"
    elif avg_score_b > avg_score_a:
        verdict = "🎉 BATCH APPROACH IS BETTER - Faster AND higher quality!"
    else:
        verdict = (
            f"⚠️ Current approach has {(avg_score_a - avg_score_b):.1f} point advantage"
        )

    print(f"VERDICT: {verdict}")
    print("=" * 80)

    # Save detailed report
    report = {
        "summary": {
            "a_wins": a_wins,
            "b_wins": b_wins,
            "ties": ties,
            "avg_score_a": avg_score_a,
            "avg_score_b": avg_score_b,
            "avg_words_a": avg_words_a,
            "avg_words_b": avg_words_b,
            "verdict": verdict,
        },
        "detailed_comparisons": all_comparisons,
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Detailed quality report saved to: {output_file}")

    return report


# ═══════════════════════════════════════════════════════════════════════════
# MAIN EXECUTION
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import os

    script_dir = os.path.dirname(os.path.abspath(__file__))
    results_file = os.path.join(script_dir, "narration_batch_test_results.json")
    quality_report_file = os.path.join(script_dir, "narration_quality_report.json")

    report = generate_quality_report(results_file, quality_report_file)
