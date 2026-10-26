# Reference Lessons, Tasks, and Expected Results

## Purpose and provenance

These are author-created teaching examples and mathematical reference cases for ClaimLab. They are not measured student sessions. Convert the short source note below into a clearly labelled example PDF during implementation, preserving author attribution and source status.

The real paper can motivate an investigation, but the first reproducible demo should not depend on redistributing an entire third-party PDF. The source note is a supported teaching fixture; a separately worded supported note and different parameters exercise transfer beyond the first example.

## Example source note — ClaimLab Attention Lab

### Section A: From scores to weights

Softmax turns a finite vector of scores into nonnegative weights summing to one. Increasing all scores by the same amount preserves the weights. Multiplying unequal scores changes their relative influence. Equal scores receive equal weights.

A numerical investigation can compare score vectors before and after multiplication. Its inputs and results should be visible so the learner can explain the relationship rather than memorize a picture.

### Section B: Attention ingredients

In a small attention example, a query is compared with keys to produce scores. A normalization step produces weights. Those weights combine values to produce an output. The objects participating in scoring and those contributing output information have different roles.

A synthetic dot-product experiment can investigate the effect of score scaling under stated assumptions. Synthetic vectors do not represent a trained model's learned behavior or reproduce a translation benchmark.

### Section C: Which positions may contribute?

In a causal attention illustration, a position can use its current and earlier positions while future positions are excluded. A mask changes which entries contribute before row-wise normalization. Each row in this example retains at least one allowed entry.

This explains one operation. A full language-model training procedure includes additional design choices and should not be inferred from the illustration alone.

## Concept path

`softmax_normalization` supports `softmax_score_scale`. `query_key_scores` plus normalization support `attention_scaling`. `value_weighted_sum` establishes how output is formed. These concepts support a focused `causal_masking` investigation.

The teacher can enter at the concept relevant to the selected question and assess a prerequisite briefly. It should not require every student to repeat the whole path.

## Task bank

| Task ID / variant | Student-facing task | Checked answer or interpretation |
| --- | --- | --- |
| `softmax-equal-01` / `v1-a` | What weights do two equal scores receive? | [0.5, 0.5] |
| `softmax-ratio-01` / `v1-a` | For scores [0, ln(3)], calculate the weights | [0.25, 0.75] |
| `softmax-ratio-01` / `v1-b` | For scores [ln(2), 0], calculate the weights | [2/3, 1/3] |
| `softmax-shift-01` / `v1-a` | Add 5 to both scores in [0, ln(3)]. What changes? | Weights remain [0.25, 0.75] |
| `softmax-scale-01` / `v1-a` | Multiply [0, ln(3)] by 2. What weights result? | [0.1, 0.9] |
| `attention-connect-01` / `v1-a` | Connect query and keys to scoring, then weights to the data combined for output | Scores come from query/key comparison; output combines values using weights |
| `attention-connect-01` / `v1-b` | Repeat with renamed/rearranged objects and a new small numerical example | Same semantic relationship; positions/names alone are not the answer |
| `attention-scale-predict-01` / `v1-a` | Predict how unscaled scores may vary as dimension grows under independent unit-variance synthetic inputs | A reasoned prediction about score spread; free-text explanation remains qualified |
| `attention-scale-apply-01` / `v1-a` | A score is 12 and key dimension is 16. What is the scaled score? | 3 |
| `attention-scale-apply-01` / `v1-b` | A score is 15 and key dimension is 25. What is the scaled score? | 3; requires a new calculation despite the same resulting value |
| `mask-row-01` / `v1-a` | For row index 1 in a zero-score 3×3 matrix, which columns are allowed and what are their weights? | Columns 0 and 1; [0.5, 0.5, 0] |
| `mask-row-01` / `v1-b` | For the last row of a zero-score 4×4 matrix, what weights result? | [0.25, 0.25, 0.25, 0.25] |

Use the exact mathematical constants in oracle calculations, not rounded text values. Accept documented numeric tolerances and equivalent semantic answers. Do not mark a free-text prediction correct merely because it contains a keyword.

## Example lesson sequence

1. Select Section B and ask why a score is scaled.
2. Use a connection task to check score/output roles.
3. Explain the relevant operation on the board, with source/background labels.
4. Ask a prediction, then run `attention_scaling_v1` with a recorded seed.
5. Interpret actual output, including assumptions and sample context.
6. If a misconception is supported, use a targeted softmax or role-contrast example.
7. Offer an unexposed application variant and retain assistance history.

This is a supported path, not a fixed answer script. Different student evidence should produce relevant different next steps.

## Rubric examples

**Concept versus arithmetic:** Correctly describing division by the square root but calculating the square root incorrectly suggests calculation support, not automatically a conceptual restart.

**Keys versus values:** A wrong connection is evidence about one task. Ask a diagnostic follow-up before generalizing, especially if the diagram was ambiguous.

**Scaling versus uniformity:** A student who says every scaled output must be identical needs a counterexample and a check distinguishing normalization, scaling, and actual input values.

## Held-out cases

Create at least one separately worded supported source and new task variants after the first lesson works. Do not expose those answers during teaching before evaluating the attempt. Public test material can contain oracles for reproducibility, but the student-facing flow should not reveal a worked answer prematurely.

Hold-out status concerns evaluation procedure, not obscurity: if the system has been tuned against a case repeatedly, label it a regression fixture rather than an unseen test.
