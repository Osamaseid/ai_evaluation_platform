"""Tests for GradingRubric, RubricCriterion, and RubricEvaluation models."""

import pytest

from evaluator.exceptions import EntityValidationError
from evaluator.rubric import GradingRubric, RubricCriterion, RubricEvaluation


class TestRubricModels:
    def test_valid_rubric_creation(self):
        c1 = RubricCriterion("code_style", "Code Style", "PEP8 compliance", 10, 1.0)
        c2 = RubricCriterion("complexity", "Algorithmic Complexity", "O(n) time complexity", 15, 1.5)

        rubric = GradingRubric("rubric_w1", "Week 1 Rubric", (c1, c2))

        assert rubric.rubric_id == "rubric_w1"
        assert rubric.title == "Week 1 Rubric"
        assert rubric.max_score == 25
        assert len(rubric.criteria) == 2

    def test_duplicate_criterion_id_rejected(self):
        c1 = RubricCriterion("dup_id", "First", "Description", 5)
        c2 = RubricCriterion("dup_id", "Second", "Description", 10)

        with pytest.raises(EntityValidationError, match="unique"):
            GradingRubric("r1", "Title", (c1, c2))

    def test_invalid_max_points_rejected(self):
        with pytest.raises(EntityValidationError, match="greater than zero"):
            RubricCriterion("c1", "Name", "Desc", 0)

        with pytest.raises(TypeError, match="integer"):
            RubricCriterion("c1", "Name", "Desc", True)  # type: ignore

    def test_rubric_evaluation_model(self):
        eval_item = RubricEvaluation("code_style", 8.5, "Minor formatting issues on line 12.")
        assert eval_item.criterion_id == "code_style"
        assert eval_item.score == 8.5
        assert "Minor formatting" in eval_item.feedback

    def test_negative_rubric_score_rejected(self):
        with pytest.raises(EntityValidationError, match="non-negative"):
            RubricEvaluation("code_style", -1.0, "Negative score not allowed.")

