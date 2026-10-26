# Agent Orchestration

## Purpose

Use a real Meta model to interpret the selected passage and current student evidence, choose supported teaching actions, and investigate experiments. Deterministic application code enforces ownership, revisions, recipe limits, numerical checks, and task sequencing.

Logical roles are source interpreter, teacher, experiment planner, and evidence interpreter. Implement them through one bounded coordinator initially. Multiple named agents are not required to realize the idea.

## Context for a turn

Provide the learning goal, bounded selected text with trusted anchor IDs, active concept/prerequisites, board object summary, latest relevant run/checks, recent learner events, qualified concept evidence, and tool/budget limits. Separate system instructions from quoted source material and learner content.

Cap input at the configured 12,000-token budget. Summarize older session events with references to retained records. If source coverage must be narrowed, tell the student which passage remains active. Do not silently truncate the equation needed for the question.

## Bounded turn loop

1. Claim the tutor job; verify owner, expiry, fence, and deadline.
2. Assess structured learner events with deterministic rubrics where available. Give the model the assessment and its uncertainty.
3. Reserve budget and make a Meta Chat Completions request with typed tools.
4. Validate returned arguments and current state before any side effect.
5. Execute tools through application services, record results, and return them with matching provider tool-call IDs.
6. Continue until a concise student-facing response or the turn budget is reached.
7. Commit terminal job state. Retain already committed valid checkpoints if the final request fails.

Use at most four provider requests including retry attempts, eight total tool invocations, two recipe runs, and a 180-second overall deadline. These are hard ceilings, not a requirement to use every call. Prefer a compact teaching-step tool that groups related narration, board changes, and one task. If the budget is reached, preserve work and offer a next interaction rather than fabricating completion.

## Tool catalog

| Tool | Valid input | Effect and guard |
| --- | --- | --- |
| `get_source_excerpt` | Existing anchor IDs in this selection | Return bounded validated text; no URL fetching |
| `get_learning_state` | Current session only | Return qualified evidence and relevant task/run summaries |
| `present_teaching_step` | Narration blocks, atomic board patch, optional existing task variant, optional teaching decision | Validate all components and commit atomically; decision references owned evidence IDs |
| `propose_experiment` | Allowlisted recipe ID, strict parameters, question, assumptions | Save a bounded proposal; no execution implied |
| `run_experiment` | Existing supported proposal or validated recipe parameters | Execute through the same runner service as the API, within current user goal and limits |

The teacher can present a step, run a relevant experiment, and present a follow-up within the request ceiling. Use preloaded evidence rather than unnecessary lookup tools. `present_teaching_step` stores its decision and task in one valid checkpoint; it does not require separate model calls for each database row.

No tool accepts shell commands, freeform executable code, arbitrary paths, raw SVG/HTML, credentials, another owner ID, or arbitrary network URLs.

## Meta adapter

Candidate configuration: `META_BASE_URL=https://api.meta.ai/v1`, `META_MODEL=muse-spark-1.3`, Chat Completions through the compatible client. Confirm against the actual account before building around it. The current cookbook documents `tool_choice="auto"`; do not assume unsupported forced tool choices. Prefer `parallel_tool_calls=false` for mutation sequencing and verify that setting in the connectivity probe.

Use structured JSON output in a separate schema-constrained request when a final assessment object is needed; Chat Completions and Responses use different parameter names. The adapter owns protocol details so product logic does not depend on provider-specific response layouts. See [sources](24_SOURCE_REGISTER.md).

## Validation and recovery

Return a bounded tool error for invalid arguments so the model can correct them within the remaining request budget. Unknown tools, cross-owner references, stale board bases, and unsupported recipes cause no side effect. Dedupe by `(job_id, provider_tool_call_id)` and retain the result reference.

Retry at most once for a retryable timeout/rate-limit/transient error, respecting provider hints and the overall deadline. Retries count against call and cost limits. Do not retry schema incompatibility or authentication failures as if transient. Do not automatically switch models/providers and hide the change.

## Teaching decisions

A decision contains learner evidence IDs, a tentative gap, a selected action, a concise observable rationale, and a proposed follow-up. The server validates that the evidence exists in this session. Record outcomes after the follow-up, including unresolved cases.

The model cannot mark a concept mastered solely from its own explanation. It may state uncertainty and ask a diagnostic question. Student requests to see a worked answer can be honored without treating that exposure as independent success.

## Live and fixture modes

Fixture mode uses deterministic provider responses for offline development and tests, with a persistent visible label. Live mode records actual model ID, redacted request IDs, usage, and tool outcomes. A real live compatibility and adaptation test is required for release; fixtures cannot establish that Meta integration works.
