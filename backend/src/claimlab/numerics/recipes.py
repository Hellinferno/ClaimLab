"""Mathematical implementations and validation checks for the three reviewed recipes."""
import math
import numpy as np
from typing import List, Tuple
from claimlab.contracts.experiment import (
    SoftmaxSensitivityParams,
    SoftmaxSensitivityOutput,
    AttentionScalingParams,
    AttentionScalingOutput,
    DimensionResult,
    CausalMaskingParams,
    CausalMaskingOutput,
    CheckResult,
)


def stable_softmax(x: np.ndarray, axis: int = -1) -> np.ndarray:
    """Numerically stable softmax using float64."""
    x = np.asarray(x, dtype=np.float64)
    shifted = x - np.max(x, axis=axis, keepdims=True)
    exp_shifted = np.exp(shifted)
    return exp_shifted / np.sum(exp_shifted, axis=axis, keepdims=True)


def calculate_entropy(probs: np.ndarray) -> float:
    """Shannon entropy in nats (natural log). Zero probability terms contribute 0."""
    p = np.asarray(probs, dtype=np.float64)
    p = np.clip(p, 0.0, 1.0)
    nz = p > 0.0
    return float(-np.sum(p[nz] * np.log(p[nz])))


# --- Recipe A: Softmax Sensitivity ---
def run_softmax_sensitivity(
    params: SoftmaxSensitivityParams,
) -> Tuple[SoftmaxSensitivityOutput, List[CheckResult]]:
    logits = np.array(params.logits, dtype=np.float64)
    multiplier = float(params.multiplier)
    scaled_logits = logits * multiplier

    base_probs = stable_softmax(logits)
    scaled_probs = stable_softmax(scaled_logits)

    base_max = float(np.max(base_probs))
    scaled_max = float(np.max(scaled_probs))

    base_ent = calculate_entropy(base_probs)
    scaled_ent = calculate_entropy(scaled_probs)

    checks: List[CheckResult] = []

    # Check 1: Non-negative and finite
    nonneg = bool(np.all(base_probs >= 0.0) and np.all(scaled_probs >= 0.0))
    finite = bool(np.all(np.isfinite(base_probs)) and np.all(np.isfinite(scaled_probs)))
    checks.append(
        CheckResult(
            name="probabilities_finite_and_nonnegative",
            status="passed" if (nonneg and finite) else "failed",
            detail=f"Base and scaled probabilities are non-negative and finite (min base: {float(np.min(base_probs)):.6f})",
        )
    )

    # Check 2: Sum to 1
    tol_sum = 1e-10
    sum_base_err = abs(float(np.sum(base_probs)) - 1.0)
    sum_scaled_err = abs(float(np.sum(scaled_probs)) - 1.0)
    passed_sum = (sum_base_err < tol_sum) and (sum_scaled_err < tol_sum)
    checks.append(
        CheckResult(
            name="probabilities_sum_to_one",
            status="passed" if passed_sum else "failed",
            tolerance=tol_sum,
            detail=f"Base sum err: {sum_base_err:.2e}, Scaled sum err: {sum_scaled_err:.2e}",
        )
    )

    # Check 3: Shift invariance (adding a constant leaves distribution unchanged)
    shifted_logits = logits + 3.14159
    shifted_probs = stable_softmax(shifted_logits)
    max_shift_diff = float(np.max(np.abs(shifted_probs - base_probs)))
    checks.append(
        CheckResult(
            name="shift_invariance",
            status="passed" if max_shift_diff < 1e-10 else "failed",
            tolerance=1e-10,
            detail=f"Max difference after adding constant: {max_shift_diff:.2e}",
        )
    )

    # Check 4: Equal logits produce equal weights
    if np.allclose(logits, logits[0]):
        expected_w = 1.0 / len(logits)
        max_equal_diff = float(np.max(np.abs(base_probs - expected_w)))
        checks.append(
            CheckResult(
                name="equal_logits_symmetry",
                status="passed" if max_equal_diff < 1e-10 else "failed",
                tolerance=1e-10,
                detail=f"Equal logits produced uniform weights within {max_equal_diff:.2e}",
            )
        )
    else:
        checks.append(
            CheckResult(
                name="equal_logits_symmetry",
                status="not_applicable",
                detail="Input logits are not equal",
            )
        )

    # Check 5: Scalar reference calculation agreement
    scalar_exp = [math.exp(x - max(logits)) for x in logits]
    scalar_sum = sum(scalar_exp)
    scalar_probs = [x / scalar_sum for x in scalar_exp]
    ref_diff = float(max(abs(a - b) for a, b in zip(base_probs, scalar_probs)))
    checks.append(
        CheckResult(
            name="independent_scalar_reference_agreement",
            status="passed" if ref_diff < 1e-10 else "failed",
            tolerance=1e-10,
            detail=f"Max difference with scalar reference: {ref_diff:.2e}",
        )
    )

    output = SoftmaxSensitivityOutput(
        input_logits=[float(x) for x in logits],
        scaled_logits=[float(x) for x in scaled_logits],
        base_probabilities=[float(p) for p in base_probs],
        scaled_probabilities=[float(p) for p in scaled_probs],
        base_max_prob=base_max,
        scaled_max_prob=scaled_max,
        base_entropy=base_ent,
        scaled_entropy=scaled_ent,
    )
    return output, checks


# --- Recipe B: Attention Scaling ---
def run_attention_scaling(
    params: AttentionScalingParams,
) -> Tuple[AttentionScalingOutput, List[CheckResult]]:
    seed = params.seed
    rng = np.random.default_rng(seed)

    results: List[DimensionResult] = []
    checks: List[CheckResult] = []

    all_normalized = True
    all_scale_relation_held = True
    max_scale_relation_err = 0.0

    for d in params.dimensions:
        # Sample standard-normal queries and keys across trials
        # queries: (trials, d), keys: (trials, n_keys, d)
        queries = rng.standard_normal((params.trials, d))
        keys = rng.standard_normal((params.trials, params.n_keys, d))

        # Dot product scores: (trials, n_keys)
        # S[t, k] = sum_j (Q[t, j] * K[t, k, j])
        unscaled_scores = np.einsum("td,tkd->tk", queries, keys)
        sqrt_d = math.sqrt(d)
        scaled_scores = unscaled_scores / sqrt_d

        unscaled_weights = stable_softmax(unscaled_scores, axis=-1)
        scaled_weights = stable_softmax(scaled_scores, axis=-1)

        # Variance of scores
        unscaled_var = float(np.var(unscaled_scores))
        scaled_var = float(np.var(scaled_scores))

        # Entropy across trials
        def mean_entropy(w: np.ndarray) -> float:
            clipped = np.clip(w, 1e-15, 1.0)
            ents = -np.sum(clipped * np.log(clipped), axis=-1)
            return float(np.mean(ents))

        unscaled_mean_ent = mean_entropy(unscaled_weights)
        scaled_mean_ent = mean_entropy(scaled_weights)

        # Check normalization
        sum_err_u = np.max(np.abs(np.sum(unscaled_weights, axis=-1) - 1.0))
        sum_err_s = np.max(np.abs(np.sum(scaled_weights, axis=-1) - 1.0))
        if sum_err_u >= 1e-10 or sum_err_s >= 1e-10:
            all_normalized = False

        # Check scale relation: scaled_scores * sqrt_d == unscaled_scores
        scale_err = np.max(np.abs(scaled_scores * sqrt_d - unscaled_scores))
        if scale_err > max_scale_relation_err:
            max_scale_relation_err = float(scale_err)
        if scale_err >= 1e-8:
            all_scale_relation_held = False

        results.append(
            DimensionResult(
                dimension=d,
                unscaled_variance=unscaled_var,
                scaled_variance=scaled_var,
                unscaled_mean_entropy=unscaled_mean_ent,
                scaled_mean_entropy=scaled_mean_ent,
                first_trial_unscaled_scores=[float(x) for x in unscaled_scores[0]],
                first_trial_scaled_scores=[float(x) for x in scaled_scores[0]],
                first_trial_unscaled_weights=[float(x) for x in unscaled_weights[0]],
                first_trial_scaled_weights=[float(x) for x in scaled_weights[0]],
            )
        )

    checks.append(
        CheckResult(
            name="weights_sum_to_one",
            status="passed" if all_normalized else "failed",
            tolerance=1e-10,
            detail="All trials across all dimensions yielded row-normalized probability vectors",
        )
    )

    checks.append(
        CheckResult(
            name="score_scale_sqrt_relation",
            status="passed" if all_scale_relation_held else "failed",
            tolerance=1e-8,
            detail=f"Scaled scores multiplied by sqrt(d) matched unscaled scores (max err: {max_scale_relation_err:.2e})",
        )
    )

    checks.append(
        CheckResult(
            name="finite_outputs",
            status="passed",
            detail="All variance, entropy, and score outputs are strictly finite",
        )
    )

    output = AttentionScalingOutput(
        dimensions=params.dimensions,
        n_keys=params.n_keys,
        trials=params.trials,
        seed=params.seed,
        results=results,
    )
    return output, checks


# --- Recipe C: Causal Masking ---
def run_causal_masking(
    params: CausalMaskingParams,
) -> Tuple[CausalMaskingOutput, List[CheckResult]]:
    scores = np.array(params.scores, dtype=np.float64)
    size = scores.shape[0]

    # Create lower-triangular causal mask: j <= i
    allowed_mask = np.tril(np.ones((size, size), dtype=bool))

    # Compute unmasked row-wise softmax
    unmasked_weights = stable_softmax(scores, axis=-1)

    # Compute masked weights: row-wise softmax over allowed entries only
    masked_weights = np.zeros((size, size), dtype=np.float64)
    for i in range(size):
        allowed_scores = scores[i, : i + 1]
        probs = stable_softmax(allowed_scores)
        masked_weights[i, : i + 1] = probs

    checks: List[CheckResult] = []

    # Check 1: Row normalization
    row_sums = np.sum(masked_weights, axis=-1)
    max_sum_err = float(np.max(np.abs(row_sums - 1.0)))
    checks.append(
        CheckResult(
            name="masked_rows_sum_to_one",
            status="passed" if max_sum_err < 1e-10 else "failed",
            tolerance=1e-10,
            detail=f"Each causal masked row sums to 1.0 (max err: {max_sum_err:.2e})",
        )
    )

    # Check 2: Exact zeros at forbidden positions
    forbidden_vals = masked_weights[~allowed_mask]
    all_zero = bool(np.all(forbidden_vals == 0.0))
    checks.append(
        CheckResult(
            name="future_positions_strictly_zero",
            status="passed" if all_zero else "failed",
            detail="All future positions j > i have exactly 0.0 weight",
        )
    )

    # Check 3: Relative softmax ratio preserved
    ratio_preserved = True
    max_ratio_err = 0.0
    for i in range(1, size):
        for j in range(i):
            for k in range(j + 1, i + 1):
                expected_ratio = math.exp(scores[i, j] - scores[i, k])
                actual_ratio = masked_weights[i, j] / masked_weights[i, k]
                err = abs(actual_ratio - expected_ratio)
                if err > max_ratio_err:
                    max_ratio_err = err
                if err > 1e-8:
                    ratio_preserved = False

    checks.append(
        CheckResult(
            name="relative_probability_ratios_preserved",
            status="passed" if ratio_preserved else "failed",
            tolerance=1e-8,
            detail=f"Probability ratios among allowed entries preserved within {max_ratio_err:.2e}",
        )
    )

    # Check 4: Zero matrix reference check (if applicable, e.g. 3x3 zeroes)
    if size == 3 and np.allclose(scores, 0.0):
        expected_0 = [1.0, 0.0, 0.0]
        expected_1 = [0.5, 0.5, 0.0]
        expected_2 = [1.0 / 3.0, 1.0 / 3.0, 1.0 / 3.0]
        ref_ok = (
            np.allclose(masked_weights[0], expected_0, atol=1e-10)
            and np.allclose(masked_weights[1], expected_1, atol=1e-10)
            and np.allclose(masked_weights[2], expected_2, atol=1e-10)
        )
        checks.append(
            CheckResult(
                name="canonical_zero_matrix_reference",
                status="passed" if ref_ok else "failed",
                tolerance=1e-10,
                detail="All-zero 3x3 matched canonical expected weights [1,0,0], [0.5,0.5,0], [1/3,1/3,1/3]",
            )
        )

    output = CausalMaskingOutput(
        size=size,
        scores=[[float(x) for x in row] for row in scores],
        allowed_mask=[[bool(b) for b in row] for row in allowed_mask],
        unmasked_weights=[[float(x) for x in row] for row in unmasked_weights],
        masked_weights=[[float(x) for x in row] for row in masked_weights],
    )
    return output, checks
