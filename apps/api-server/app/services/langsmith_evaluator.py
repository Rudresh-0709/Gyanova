"""
LangSmith Evaluation Module

This module provides utilities for evaluating narration quality using LangSmith.

Features:
- Convert existing test results to LangSmith datasets
- Custom evaluators for length, format, and quality
- Batch evaluation and comparison tools
"""

import json
import os
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from langsmith import Client
from langsmith.schemas import Run, Example

load_dotenv()


class NarrationEvaluator:
    """Evaluator for AI-generated narration quality."""

    def __init__(self):
        """Initialize the evaluator with LangSmith client."""
        self.client = Client()
        self.project_name = os.getenv("LANGCHAIN_PROJECT", "AI-Teacher-App")

    def create_dataset_from_results(
        self, results_file: str, dataset_name: str, description: str = ""
    ) -> str:
        """
        Create a LangSmith dataset from existing test results.

        Args:
            results_file: Path to JSON file with test results
            dataset_name: Name for the dataset
            description: Optional description

        Returns:
            Dataset ID
        """
        print(f"\n📦 Creating dataset: {dataset_name}")

        # Load test results
        with open(results_file, "r", encoding="utf-8") as f:
            results = json.load(f)

        # Create dataset
        try:
            dataset = self.client.create_dataset(
                dataset_name=dataset_name, description=description
            )
            print(f"✓ Dataset created: {dataset.id}")
        except Exception as e:
            print(f"⚠️  Dataset may already exist, trying to read: {e}")
            dataset = self.client.read_dataset(dataset_name=dataset_name)

        # Add examples from results
        examples_added = 0

        if "results" in results:  # Format from test_narration_batch.py
            for result in results["results"]:
                example = self.client.create_example(
                    dataset_id=dataset.id,
                    inputs={
                        "slide_title": result.get("slide_title", ""),
                        "slide_purpose": result.get("slide_purpose", ""),
                        "narration_format": result.get("narration_format", ""),
                        "constraints": result.get("constraints", {}),
                    },
                    outputs={
                        "narration_text": result.get("narration_text", ""),
                        "word_count": result.get("word_count", 0),
                        "meets_length_req": result.get("meets_length_req", False),
                    },
                )
                examples_added += 1

        print(f"✓ Added {examples_added} examples to dataset")
        return dataset.id

    @staticmethod
    def evaluate_length_compliance(run: Run, example: Example) -> Dict[str, Any]:
        """
        Evaluator: Check if narration meets length requirements.

        Args:
            run: The LangSmith run
            example: The example being evaluated

        Returns:
            Evaluation result with score and feedback
        """
        narration = run.outputs.get("narration_text", "") if run.outputs else ""
        word_count = len(narration.split())

        # Get expected constraints from inputs
        constraints = example.inputs.get("constraints", {})
        word_range = constraints.get("word_count", [40, 100])

        min_words = word_range[0] if isinstance(word_range, list) else 40
        max_words = word_range[1] if isinstance(word_range, list) else 100

        # Check compliance
        is_compliant = min_words <= word_count <= max_words
        score = 1.0 if is_compliant else 0.0

        feedback = f"Word count: {word_count} (expected: {min_words}-{max_words})"

        return {"key": "length_compliance", "score": score, "comment": feedback}

    @staticmethod
    def evaluate_format_compliance(run: Run, example: Example) -> Dict[str, Any]:
        """
        Evaluator: Check if narration follows the required format.

        Args:
            run: The LangSmith run
            example: The example being evaluated

        Returns:
            Evaluation result with score and feedback
        """
        narration = run.outputs.get("narration_text", "") if run.outputs else ""
        expected_format = example.inputs.get("narration_format", "points")

        # Simple heuristic: check for bullet point markers or numbered lists
        has_bullets = any(
            line.strip().startswith(("•", "-", "*", "1.", "2.", "3."))
            for line in narration.split("\n")
        )

        if expected_format == "points":
            score = 1.0 if has_bullets else 0.5
            feedback = (
                "Format appears correct"
                if has_bullets
                else "May not follow point format"
            )
        elif expected_format == "paragraph":
            score = 1.0 if not has_bullets else 0.5
            feedback = (
                "Paragraph format" if not has_bullets else "Contains bullet points"
            )
        else:
            score = 0.8  # Neutral for other formats
            feedback = f"Format: {expected_format}"

        return {"key": "format_compliance", "score": score, "comment": feedback}

    def run_evaluation(self, dataset_name: str, evaluators: Optional[List] = None):
        """
        Run evaluation on a dataset.

        Args:
            dataset_name: Name of the dataset to evaluate
            evaluators: List of evaluator functions (uses defaults if None)
        """
        if evaluators is None:
            evaluators = [
                self.evaluate_length_compliance,
                self.evaluate_format_compliance,
            ]

        print(f"\n🔬 Running evaluation on dataset: {dataset_name}")
        print(f"   Evaluators: {len(evaluators)}")

        try:
            results = self.client.evaluate(
                lambda inputs: {"narration_text": inputs.get("narration_text", "")},
                data=dataset_name,
                evaluators=evaluators,
                experiment_prefix="narration-quality",
            )

            print(f"\n✓ Evaluation complete!")
            print(f"   View results in LangSmith dashboard")

            return results

        except Exception as e:
            print(f"\n✗ Evaluation failed: {e}")
            import traceback

            traceback.print_exc()
            return None


def main():
    """
    Demo: Create dataset and run evaluation from existing test results.
    """
    print("=" * 80)
    print("LANGSMITH NARRATION EVALUATION")
    print("=" * 80)

    evaluator = NarrationEvaluator()

    # Check if test results exist
    results_file = os.path.join(
        os.path.dirname(__file__), "..", "narration_batch_test_results.json"
    )

    if not os.path.exists(results_file):
        print(f"\n⚠️  Test results file not found: {results_file}")
        print("   Run test_narration_batch.py first to generate test data.")
        return

    # Create dataset
    dataset_id = evaluator.create_dataset_from_results(
        results_file=results_file,
        dataset_name="narration-quality-batch",
        description="Narration quality test results from batch generation",
    )

    print("\n" + "=" * 80)
    print("Dataset created successfully!")
    print("=" * 80)
    print(f"\nDataset ID: {dataset_id}")
    print("\nNext steps:")
    print("  1. View dataset in LangSmith dashboard")
    print("  2. Run evaluations on the dataset")
    print("  3. Compare different narration approaches")
    print("\nTo run evaluation programmatically:")
    print("  evaluator.run_evaluation('narration-quality-batch')")
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
