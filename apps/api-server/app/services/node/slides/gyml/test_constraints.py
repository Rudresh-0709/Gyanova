import unittest
from dataclasses import dataclass
from typing import List, Any
from gyml.fitness import SlideFitnessGate, FitnessException
from gyml.constraints import ConstraintRules
from gyml.definitions import (
    ComposedSlide,
    ComposedSection,
    ComposedBlock,
    Emphasis,
)


# Mock Classes for Testing
@dataclass
class MockSlide:
    total_words: int = 0
    blocks: int = 0
    has_image: bool = False

    def total_word_count(self):
        return self.total_words

    def block_count(self):
        return self.blocks

    @property
    def accent_image_url(self):
        return "img.jpg" if self.has_image else None


class TestConstraints(unittest.TestCase):

    def test_fitness_density_rejection(self):
        """Test that sparse slides are rejected."""
        # 10 words, 1 block, no image -> Very low density
        sparse_slide = MockSlide(total_words=10, blocks=1, has_image=False)

        is_valid, reason = SlideFitnessGate.validate_density(sparse_slide)
        self.assertFalse(is_valid, f"Should reject sparse slide. Reason: {reason}")

    def test_fitness_density_pass_with_image(self):
        """Test that adding an image saves a sparse slide."""
        # 10 words, 1 block, WITH image -> Should pass (salvageable)
        saved_slide = MockSlide(total_words=10, blocks=1, has_image=True)

        is_valid, reason = SlideFitnessGate.validate_density(saved_slide)
        self.assertTrue(
            is_valid, f"Should accept sparse slide with image. Reason: {reason}"
        )

    def test_fitness_density_pass_normal(self):
        """Test a normal density slide."""
        # 100 words -> Good density
        normal_slide = MockSlide(total_words=100, blocks=3, has_image=False)
        is_valid, _ = SlideFitnessGate.validate_density(normal_slide)
        self.assertTrue(is_valid)

    def test_layout_constraints(self):
        """Test strict item constraints for layouts."""

        # Timeline: Min 2 items
        try:
            SlideFitnessGate.validate_constraints(None, "timeline", ["One Item"])
            self.fail("Should have raised FitnessException for 1 item timeline")
        except FitnessException:
            pass  # Expected

        # Timeline: 3 items -> OK
        try:
            SlideFitnessGate.validate_constraints(None, "timeline", ["1", "2", "3"])
        except FitnessException as e:
            self.fail(f"Should allow 3 items for timeline. {e}")

    def test_word_count_per_item(self):
        """Test word count limits per item."""
        long_text = "word " * 120  # 120 words

        try:
            # Process Steps limit is 50 words
            SlideFitnessGate.validate_constraints(
                None, "processSteps", [long_text, "short", "short"]
            )
            self.fail("Should reject item with > 50 words")
        except FitnessException:
            pass


if __name__ == "__main__":
    unittest.main()
