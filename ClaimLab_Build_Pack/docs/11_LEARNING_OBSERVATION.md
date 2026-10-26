# Learning Observation and Adaptation

## Purpose

Use observable student work to choose a relevant next teaching step. The first release adapts within a retained learning session and resumes that evidence under the same guest identity. A general cross-course learner model is later scope.

## Evidence categories

| Evidence | What it can support | Important qualification |
| --- | --- | --- |
| Structured connection answer | A specific relationship may be understood or confused | Confirm task and diagram version |
| Prediction plus explanation | The student can reason about an intervention | A lucky guess is weak evidence |
| Numerical/application answer | Correctness on a new instance | Record hints and exposure to solutions |
| Free-text explanation | Possible conceptual strengths/gaps | Model assessment remains provisional |
| Hint request | Current task needs support | It does not diagnose permanent ability |
| Annotation or focused question | Which part the student wants to inspect | Clarify ambiguous meaning |
| Pause or inactivity | Session context only | Do not infer confusion or engagement from timing alone |

## Supported concepts

Start with `softmax_normalization`, `softmax_score_scale`, `query_key_scores`, `value_weighted_sum`, `attention_scaling`, and `causal_masking`. Dependencies are explicit. For example, interpreting scaling needs some understanding of scores and softmax; interpreting a weighted output needs the value relationship.

The source selection establishes which concepts are relevant. A generic list of all concepts must not become an invented personalized curriculum.

## Evidence state and transitions

Use categorical summaries from the data model. A concept begins `not_assessed`; exposure can mark it `introduced`. A task attempt can yield `needs_check`, `supported_with_help`, or `supported_independently` depending on the actual evidence. A later contradiction can mark `needs_revisit` while preserving earlier attempts.

A single correct answer does not certify lasting mastery. The initial progression policy requires two distinct application variants with at least one independently completed before labelling the available evidence `supported_independently`. State descriptions remain about this session's evidence, not a validated educational measurement scale.

Hints, displayed worked answers, repeated variants, and explicitly requested solutions are recorded. A client cannot self-report zero hints after the server served them.

## Decision policy

1. If evidence is ambiguous, ask a short diagnostic question.
2. If a specific prerequisite gap is supported, offer a small prerequisite lesson and connect it back.
3. If the concept appears sound but arithmetic fails, reveal the relevant calculation step.
4. If recall succeeds but prediction fails, run a controlled comparison after asking for a prediction.
5. If two distinct applications support understanding, progress or increase difficulty.
6. If the student requests a different representation, honor it and observe the next attempt.

This policy guides model decisions and server guardrails. It does not dictate identical wording for every student.

## Decision record

Retain `evidence_ids`, `concept_id`, `assessment_status`, `tentative_gap`, `selected_action`, concise rationale, linked board/run IDs, follow-up task, and later outcome. Rationale describes observable reasons; private internal model reasoning is not collected or shown.

A valid example: a student connects weights to keys on two differently arranged tasks; a diagnostic response confirms confusion about the output; the teacher contrasts keys and values, then offers a new weighted-sum task. Preserve uncertainty when that confirmation is absent.

## Preferences and student control

Language, pace, mathematical detail, and desired representation are explicit preferences. They are not inferred learning-style labels. The student can correct preferences and review/reset retained history. New sessions do not silently inherit broad assumptions from unrelated material.

## What demonstrates adaptation

The observation harness must show a difference in subsequent teaching actions for meaningfully different evidence. Saving a transcript or displaying a progress bar is not sufficient. Assess both helpful and unhelpful interventions, and retain unresolved outcomes.

## Learning claims

The mechanism is a proposed method to improve teaching relevance. Evaluate it with transparent tasks and assistance records before claiming better learning. Short pilot results are exploratory and should not be described as broad causal proof.
