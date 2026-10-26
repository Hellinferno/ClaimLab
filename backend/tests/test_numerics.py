"""Tests for ClaimLab numerical recipes and runner."""
import pytest
import numpy as np
from pydantic import ValidationError

from claimlab.contracts.experiment import (
    RecipeId,
    SoftmaxSensitivityParams,
    AttentionScalingParams,
    CausalMaskingParams,
)
from claimlab.numerics.recipes import (
    run_softmax_sensitivity,
    run_attention_scaling,
    run_causal_masking,
)
from claimlab.numerics.runner import NumericalRunner, compute_parameter_hash


def test_softmax_sensitivity_normal():
    params = SoftmaxSensitivityParams(logits=[0.0, 1.0, 2.0], multiplier=1.5, seed=42)
    output, checks = run_softmax_sensitivity(params)

    assert len(output.base_probabilities) == 3
    assert len(output.scaled_probabilities) == 3
    assert abs(sum(output.base_probabilities) - 1.0) < 1e-10
    assert abs(sum(output.scaled_probabilities) - 1.0) < 1e-10

    # Multiplier > 1 sharpens the distribution, increasing max prob and decreasing entropy
    assert output.scaled_max_prob > output.base_max_prob
    assert output.scaled_entropy < output.base_entropy

    # All checks passed
    for c in checks:
        assert c.status in ("passed", "not_applicable")


def test_softmax_sensitivity_equal_logits():
    params = SoftmaxSensitivityParams(logits=[2.0, 2.0, 2.0, 2.0], multiplier=2.0)
    output, checks = run_softmax_sensitivity(params)

    for p in output.base_probabilities:
        assert abs(p - 0.25) < 1e-10
    for p in output.scaled_probabilities:
        assert abs(p - 0.25) < 1e-10

    # Equal logits check should be passed
    eq_check = next(c for c in checks if c.name == "equal_logits_symmetry")
    assert eq_check.status == "passed"


def test_softmax_sensitivity_validation():
    # Out of range logit > 20
    with pytest.raises(ValidationError):
        SoftmaxSensitivityParams(logits=[0.0, 25.0], multiplier=1.0)

    # Multiplier too small < 0.25
    with pytest.raises(ValidationError):
        SoftmaxSensitivityParams(logits=[0.0, 1.0], multiplier=0.1)


def test_attention_scaling_computation():
    params = AttentionScalingParams(dimensions=[8, 32, 128], n_keys=8, trials=100, seed=42)
    output, checks = run_attention_scaling(params)

    assert len(output.results) == 3

    # Unscaled variance should generally grow with dimension
    # (dim 8 < dim 32 < dim 128)
    unscaled_vars = [r.unscaled_variance for r in output.results]
    assert unscaled_vars[0] < unscaled_vars[1] < unscaled_vars[2]

    # Scaled variance should hover around 1.0 across dimensions
    scaled_vars = [r.scaled_variance for r in output.results]
    for sv in scaled_vars:
        assert 0.5 < sv < 1.8

    # Check that scaled * sqrt(d) matches unscaled in first trial
    for r in output.results:
        sqrt_d = np.sqrt(r.dimension)
        for s_scaled, s_unscaled in zip(r.first_trial_scaled_scores, r.first_trial_unscaled_scores):
            assert abs(s_scaled * sqrt_d - s_unscaled) < 1e-8

    # All checks passed
    for c in checks:
        assert c.status == "passed"


def test_attention_scaling_validation():
    # Duplicate dimensions
    with pytest.raises(ValidationError):
        AttentionScalingParams(dimensions=[16, 16], n_keys=4, trials=50)

    # Invalid dimension (> 256)
    with pytest.raises(ValidationError):
        AttentionScalingParams(dimensions=[512], n_keys=4, trials=50)


def test_causal_masking_zero_reference():
    # Canonical 3x3 all zero scores
    params = CausalMaskingParams(scores=[[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]])
    output, checks = run_causal_masking(params)

    assert output.size == 3
    # Row 0: [1.0, 0.0, 0.0]
    assert output.masked_weights[0] == pytest.approx([1.0, 0.0, 0.0], abs=1e-10)
    # Row 1: [0.5, 0.5, 0.0]
    assert output.masked_weights[1] == pytest.approx([0.5, 0.5, 0.0], abs=1e-10)
    # Row 2: [1/3, 1/3, 1/3]
    assert output.masked_weights[2] == pytest.approx([1/3, 1/3, 1/3], abs=1e-10)

    # Reference check must pass
    ref_check = next(c for c in checks if c.name == "canonical_zero_matrix_reference")
    assert ref_check.status == "passed"


def test_causal_masking_arbitrary():
    scores = [
        [1.0, 2.0, 3.0],
        [-1.0, 0.5, 2.5],
        [4.0, -2.0, 1.0],
    ]
    params = CausalMaskingParams(scores=scores)
    output, checks = run_causal_masking(params)

    # Future positions must be exactly 0.0
    assert output.masked_weights[0][1] == 0.0
    assert output.masked_weights[0][2] == 0.0
    assert output.masked_weights[1][2] == 0.0

    # Row 0 allowed is only position 0, so weight is 1.0
    assert output.masked_weights[0][0] == 1.0

    # All checks passed
    for c in checks:
        assert c.status == "passed"


def test_runner_execution_and_hashing():
    runner = NumericalRunner()

    params = {"logits": [1.0, 2.0, 3.0], "multiplier": 1.0, "seed": 42}
    h1 = compute_parameter_hash(RecipeId.SOFTMAX_SENSITIVITY.value, params)
    h2 = compute_parameter_hash(RecipeId.SOFTMAX_SENSITIVITY.value, {"multiplier": 1.0, "seed": 42, "logits": [1.0, 2.0, 3.0]})
    # Hash is key-order independent
    assert h1 == h2

    res = runner.run(RecipeId.SOFTMAX_SENSITIVITY.value, params)
    assert res.status == "succeeded"
    assert res.recipe_id == RecipeId.SOFTMAX_SENSITIVITY
    assert res.parameter_hash == h1
    assert len(res.checks) > 0
    assert res.output is not None
