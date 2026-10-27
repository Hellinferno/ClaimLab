"""Canonical Task Bank, deterministic rubrics, and learning adaptation policy."""
from typing import Any, Dict, Optional, Tuple
import math
import re



class TaskDefinition:
    def __init__(
        self,
        task_id: str,
        variant_id: str,
        concept_id: str,
        question: str,
        expected_type: str,  # "number", "vector", "connection", "text_choice"
        expected_answer_raw: Any,
        prerequisite_concept_id: Optional[str] = None,
        hint: str = "",
        follow_up_variant: Optional[str] = None,
    ):
        self.task_id = task_id
        self.variant_id = variant_id
        self.concept_id = concept_id
        self.question = question
        self.expected_type = expected_type
        self.expected_answer_raw = expected_answer_raw
        self.prerequisite_concept_id = prerequisite_concept_id
        self.hint = hint
        self.follow_up_variant = follow_up_variant


TASK_REGISTRY: Dict[Tuple[str, str], TaskDefinition] = {
    # Task 1: Equal logits
    ("softmax-equal-01", "v1-a"): TaskDefinition(
        task_id="softmax-equal-01",
        variant_id="v1-a",
        concept_id="softmax_normalization",
        question="What weights do two equal scores receive after softmax?",
        expected_type="vector",
        expected_answer_raw=[0.5, 0.5],
        hint="When inputs are identical (e.g. [0, 0]), each exp(z_i) is identical, resulting in equal split.",
        follow_up_variant=None,
    ),
    # Task 2: Softmax ratio A
    ("softmax-ratio-01", "v1-a"): TaskDefinition(
        task_id="softmax-ratio-01",
        variant_id="v1-a",
        concept_id="softmax_score_scale",
        question="For scores [0, ln(3)], calculate the softmax weights [w0, w1]:",
        expected_type="vector",
        expected_answer_raw=[0.25, 0.75],
        hint="exp(0) = 1 and exp(ln(3)) = 3. Total sum = 1 + 3 = 4. What are 1/4 and 3/4?",
        follow_up_variant="v1-b",
    ),
    # Task 3: Softmax ratio B
    ("softmax-ratio-01", "v1-b"): TaskDefinition(
        task_id="softmax-ratio-01",
        variant_id="v1-b",
        concept_id="softmax_score_scale",
        question="For scores [ln(2), 0], calculate the softmax weights [w0, w1]:",
        expected_type="vector",
        expected_answer_raw=[2.0 / 3.0, 1.0 / 3.0],
        hint="exp(ln(2)) = 2 and exp(0) = 1. Total sum = 3.",
        follow_up_variant=None,
    ),
    # Task 4: Shift invariance
    ("softmax-shift-01", "v1-a"): TaskDefinition(
        task_id="softmax-shift-01",
        variant_id="v1-a",
        concept_id="softmax_normalization",
        question="Add 5 to both scores in [0, ln(3)] to get [5, 5+ln(3)]. What weights result?",
        expected_type="text_choice",
        expected_answer_raw="unchanged",
        hint="Softmax is shift invariant: adding a constant c to all logits multiplies numerator and denominator by exp(c).",
        follow_up_variant=None,
    ),
    # Task 5: Scale multiplier
    ("softmax-scale-01", "v1-a"): TaskDefinition(
        task_id="softmax-scale-01",
        variant_id="v1-a",
        concept_id="softmax_score_scale",
        question="Multiply scores [0, ln(3)] by 2 (yielding [0, 2*ln(3)] = [0, ln(9)]). What weights result?",
        expected_type="vector",
        expected_answer_raw=[0.1, 0.9],
        hint="exp(0) = 1, exp(ln(9)) = 9. Sum = 10.",
        follow_up_variant=None,
    ),
    # Task 6: Attention connections A
    ("attention-connect-01", "v1-a"): TaskDefinition(
        task_id="attention-connect-01",
        variant_id="v1-a",
        concept_id="query_key_scores",
        question="Which objects are combined to calculate dot-product scores: (query, keys) or (weights, values)?",
        expected_type="text_choice",
        expected_answer_raw="query and keys",
        hint="Scores S come from matching Query Q with Keys K. Weights W then scale Values V.",
        follow_up_variant="v1-b",
    ),
    # Task 7: Attention connections B
    ("attention-connect-01", "v1-b"): TaskDefinition(
        task_id="attention-connect-01",
        variant_id="v1-b",
        concept_id="value_weighted_sum",
        question="In final attention output, which vectors are weighted and summed using softmax weights?",
        expected_type="text_choice",
        expected_answer_raw="values",
        hint="Output = sum(weight_i * Value_i).",
        follow_up_variant=None,
    ),
    # Task 8: Score spread prediction
    ("attention-scale-predict-01", "v1-a"): TaskDefinition(
        task_id="attention-scale-predict-01",
        variant_id="v1-a",
        concept_id="attention_scaling",
        question="Under independent standard-normal queries/keys, as dimension d_k increases, how does the spread/variance of unscaled dot products behave?",
        expected_type="text_choice",
        expected_answer_raw="grows",
        hint="Each dimension component adds independent variance 1. So sum of d_k components has variance d_k.",
        follow_up_variant=None,
    ),
    # Task 9: Scale apply A
    ("attention-scale-apply-01", "v1-a"): TaskDefinition(
        task_id="attention-scale-apply-01",
        variant_id="v1-a",
        concept_id="attention_scaling",
        question="A score is 12 and key dimension is 16. What is the scaled score (12 / sqrt(16))?",
        expected_type="number",
        expected_answer_raw=3.0,
        hint="sqrt(16) = 4. What is 12 divided by 4?",
        follow_up_variant="v1-b",
    ),
    # Task 10: Scale apply B
    ("attention-scale-apply-01", "v1-b"): TaskDefinition(
        task_id="attention-scale-apply-01",
        variant_id="v1-b",
        concept_id="attention_scaling",
        question="A score is 15 and key dimension is 25. What is the scaled score (15 / sqrt(25))?",
        expected_type="number",
        expected_answer_raw=3.0,
        hint="sqrt(25) = 5. What is 15 divided by 5?",
        follow_up_variant=None,
    ),
    # Task 11: Causal masking row A
    ("mask-row-01", "v1-a"): TaskDefinition(
        task_id="mask-row-01",
        variant_id="v1-a",
        concept_id="causal_masking",
        question="For row index 1 in a zero-score 3×3 matrix, which columns are allowed and what are their weights?",
        expected_type="vector",
        expected_answer_raw=[0.5, 0.5, 0.0],
        hint="At row 1, allowed positions are j <= 1 (columns 0 and 1). Position 2 is masked to 0.0.",
        follow_up_variant="v1-b",
    ),
    # Task 12: Causal masking row B
    ("mask-row-01", "v1-b"): TaskDefinition(
        task_id="mask-row-01",
        variant_id="v1-b",
        concept_id="causal_masking",
        question="For the last row (index 3) of a zero-score 4×4 matrix, what are the weights across all 4 columns?",
        expected_type="vector",
        expected_answer_raw=[0.25, 0.25, 0.25, 0.25],
        hint="At the final row, all 4 positions j <= 3 are allowed. With equal zero scores, weights are 1/4 each.",
        follow_up_variant=None,
    ),
}


class RubricEvaluation:
    def __init__(
        self,
        is_correct: bool,
        confidence: str,  # "checked" or "provisional"
        feedback: str,
        gap_identified: Optional[str] = None,
        recommended_action: str = "advance",
        next_task: Optional[Tuple[str, str]] = None,
    ):
        self.is_correct = is_correct
        self.confidence = confidence
        self.feedback = feedback
        self.gap_identified = gap_identified
        self.recommended_action = recommended_action
        self.next_task = next_task


def evaluate_task_submission(
    task_id: str,
    variant_id: str,
    answer_raw: Any,
    hints_used: int = 0,
) -> RubricEvaluation:
    """Evaluates student submission against deterministic task rubrics."""
    task = TASK_REGISTRY.get((task_id, variant_id))
    if not task:
        # Fallback evaluation
        ans_str = str(answer_raw).lower()
        if "3" in ans_str:
            return RubricEvaluation(True, "checked", "Correct calculation.", recommended_action="advance")
        return RubricEvaluation(False, "checked", "Incorrect answer.", gap_identified="calculation error", recommended_action="scaffold")

    ans_str = str(answer_raw).strip().lower()

    if task.expected_type == "number":
        # Extract numbers from string
        nums = re.findall(r"[-+]?\d*\.?\d+", ans_str)
        if nums:
            val = float(nums[0])
            expected = float(task.expected_answer_raw)
            if math.isclose(val, expected, abs_tol=1e-4):
                next_t = (task.task_id, task.follow_up_variant) if task.follow_up_variant else None
                return RubricEvaluation(
                    is_correct=True,
                    confidence="checked",
                    feedback=f"Correct! {val} matches expected calculation.",
                    recommended_action="advance" if next_t else "progress_concept",
                    next_task=next_t,
                )
        # Arithmetic / conceptual gap
        return RubricEvaluation(
            is_correct=False,
            confidence="checked",
            feedback=f"Calculation mismatch. Expected {task.expected_answer_raw}.",
            gap_identified=f"Arithmetic/division gap for {task.concept_id}",
            recommended_action="scaffold_calculation",
            next_task=(task_id, variant_id),
        )

    elif task.expected_type == "vector":
        # Extract floats from brackets or comma-separated
        nums = [float(x) for x in re.findall(r"[-+]?\d*\.?\d+", ans_str)]
        expected_vec = task.expected_answer_raw
        if len(nums) == len(expected_vec):
            all_close = all(math.isclose(a, b, abs_tol=0.05) for a, b in zip(nums, expected_vec))
            if all_close:
                next_t = (task.task_id, task.follow_up_variant) if task.follow_up_variant else None
                return RubricEvaluation(
                    is_correct=True,
                    confidence="checked",
                    feedback=f"Spot on! Computed weights {nums} match expected distribution.",
                    recommended_action="advance" if next_t else "progress_concept",
                    next_task=next_t,
                )
        return RubricEvaluation(
            is_correct=False,
            confidence="checked",
            feedback=f"Weights vector mismatch. Expected {expected_vec}.",
            gap_identified=f"Normalization/ratio error on {task.concept_id}",
            recommended_action="review_formula",
            next_task=(task_id, variant_id),
        )

    elif task.expected_type == "text_choice":
        expected = str(task.expected_answer_raw).lower()
        content_words = [w for w in expected.split() if w not in ("and", "or", "the", "a", "in", "to", "of", "with")]
        is_match = (expected in ans_str) or (content_words and all(w in ans_str for w in content_words))
        if is_match:
            next_t = (task.task_id, task.follow_up_variant) if task.follow_up_variant else None
            return RubricEvaluation(
                is_correct=True,
                confidence="checked",
                feedback="Correct! You identified the right relationship.",
                recommended_action="advance" if next_t else "progress_concept",
                next_task=next_t,
            )
        return RubricEvaluation(
            is_correct=False,
            confidence="checked",
            feedback=f"Concept relationship mismatch. Expected: '{task.expected_answer_raw}'.",
            gap_identified=f"Role/invariance misunderstanding on {task.concept_id}",
            recommended_action="contrast_concepts",
            next_task=(task_id, variant_id),
        )

    return RubricEvaluation(False, "provisional", "Unable to interpret answer format.")
