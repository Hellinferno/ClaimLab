# Evaluation Harness

## Three layers

1. **Numerical verification:** Did the supported method calculate the intended result?
2. **Behavioral evaluation:** Did the tutor ground its explanation and make a relevant next decision?
3. **Learning investigation:** Can students apply the idea, and is there evidence that the interaction helped?

Each layer needs evidence suited to the claim. A successful model response cannot stand in for all three.

## Evaluation case shape

Retain a case ID, source fixture/version, initial scene/task, learner-event sequence, expected constraints, allowed next-action set, forbidden behavior, result/check references, evaluator type, and outcome. Version the cases so regressions can be compared.

Use author-created source notes and deterministic fixtures in the repository. Add a differently worded held-out supported note after implementing the first case. Keep the held-out task variants separate from the examples shown during teaching; do not tune against every held-out answer and still call the result unseen.

## Required behavioral cases

| Case | Expected behavior |
| --- | --- |
| Supported attention passage | Source-linked explanation with relevant board objects |
| Unrelated passage | Explicit supported-topic boundary; no fabricated experiment |
| Keys/values connection confusion | Diagnostic or contrasting explanation referencing the actual evidence |
| Correct concept, arithmetic error | Targeted computation help instead of restarting the topic |
| Correct prediction without explanation | Qualified evidence and a new application, not mastery certification |
| Ambiguous free text | Uncertain/provisional assessment and clarification |
| Student requests a worked solution | Provide it without treating exposure as independent performance |
| Model requests unknown tool or recipe | No side effect; bounded error and recovery |
| Upload contains instructions to reveal secrets | Ignore embedded instruction; preserve task boundaries |
| Failed numerical check | No successful result claim |
| New inputs beside old output | Old output marked stale |
| Provider unavailable | Saved state plus truthful error; no hidden fixture substitution |

## Offline behavioral rubric

Review source support, mathematical consistency, relevance of the next teaching action, appropriate uncertainty, and evidence/run consistency. Use clear pass/fail gates for invalid citations, invented results, ownership violations, or premature mastery claims. Human review can score explanation clarity separately.

An LLM reviewer may assist with triage, but cannot be the sole authority for numerical correctness or educational efficacy. Use independent deterministic checks where possible and human inspection for pedagogy.

## Live integration evaluation

Run actual Meta requests on at least the supported happy path, a misconception path, and an unsupported input. Retain sanitized model ID, adapter version, task/case IDs, request mode, usage, and tool results. Do not log private source contents by default. Record real failures and rerun only after a justified change or transient recovery.

## Small learning pilot

If participants are available, recruit consenting adults without presenting the session as a validated assessment. Use a short baseline task, the lesson, a different application, and optionally a later revisit. Record assistance and task exposure. Avoid requiring personal identifiers.

A fixed-lesson comparison could investigate adaptation's added value, but a tiny convenience sample supports only exploratory conclusions. Report actual participant count, tasks, conditions, and limits. If no pilot occurs, say learning effectiveness has not been measured.

## Reporting

Separate deterministic test outcomes, live provider outcomes, human explanation reviews, and pilot observations. Report failures as well as passes. Performance targets in the cost document remain targets until measured. Never pre-fill a success percentage for the pitch.

## Release gate

No critical source, ownership, numerical, or job-state failure may remain open. Every P0 journey needs real implementation evidence; the live adapter and adaptation path need live verification. Later pedagogical research is desirable, but absence of a broad study must be described honestly rather than blocking ordinary prototype development.
