# Data Model and State Contracts

## Ownership and retention

Every private record has an `owner_id`, directly or through an enforced relationship. Resource lookups include ownership and expiry, not just a UUID. Guest records expire 24 hours after creation. Child records inherit that boundary. Expired access is rejected immediately; physical cleanup runs every 15 minutes.

Enable SQLite foreign keys, WAL, and a bounded busy timeout. Keep transactions short; never hold a database write transaction during a provider request or container run.

## Entities

| Entity | Important fields and constraints |
| --- | --- |
| GuestOwner | `id`, credential hash, CSRF secret/hash, `created_at`, `expires_at`, `deleted_at`; no raw cookie token |
| Document | `id`, `owner_id`, display filename, private storage key, SHA-256, size, page count, extraction status, expiry |
| DocumentPage | `document_id`, 1-based page number, normalized text, extraction quality/status; unique document/page |
| SourceAnchor | `id`, document/page, normalized start/end offsets, exact quote, text hash; offsets revalidated against stored page |
| SourceSelection | `id`, owner/document, inclusive page range, question, anchor IDs, immutable content hash |
| LearningSession | `id`, owner/selection, goal, preferences, active concept, revision, active job ID, fencing generation, expiry |
| BoardSnapshot | learning-session ID, revision, schema version, validated scene JSON; latest snapshot plus bounded checkpoints |
| LearnerEvent | `id`, owner/session, client event ID, type, validated payload, received sequence/revision, timestamp |
| ConceptEvidence | event/task IDs, concept, evidence category, assistance level, assessment status, concise observable rationale |
| TeachingDecision | evidence IDs, tentative gap, selected action, board/run references, follow-up task ID, outcome when available |
| ExperimentRun | `id`, owner/session, parent job ID, recipe/version, parameter JSON/hash, seed, execution state, output JSON/hash, checks |
| TaskAttempt | task/variant ID, learner-event ID, response, rubric version, hint count, attempt index, assessment status |
| Job | owner, optional session/document, kind, status, deadline, cancellation flag, lease, fencing generation, error code |
| JobEvent | job ID, monotonically increasing sequence, event type, redacted payload, timestamp |
| ToolInvocation | job ID and provider call ID, tool, argument hash, status, result reference; unique job/call ID |
| BudgetReservation | owner/global budget scope, request ID, reserved/settled amount, status, model/price version |
| IdempotencyRecord | owner, route scope, key, request fingerprint, response reference/status, expiry; unique owner/scope/key |

No public table contains private uploads or learner responses. Logs reference IDs and bounded metadata rather than duplicating document contents.

## Canonical event envelope

```json
{
  "schema_version": 1,
  "event_id": "11111111-1111-4111-8111-111111111111",
  "event_type": "prediction_submitted",
  "expected_revision": 7,
  "payload": {
    "task_id": "attention-scale-predict-01",
    "task_variant": "v1-a",
    "answer": "I expect the unscaled scores to spread further.",
    "assistance_level": "none"
  }
}
```

IDs in examples illustrate shape, not existing resources. The server supplies owner identity and authoritative timestamps. It validates task membership and assistance history; a client cannot grant itself an unassisted success.

## Revisions

`LearningSession.revision` increments for accepted semantic events and committed state changes. Board snapshots record the revision they represent. A mutation must match the latest expected revision and hold the active-job fence when performed by a worker.

Do not assume one revision increment per HTTP request: a tutor job can commit multiple meaningful checkpoints. Clients consume the returned current revision. Refresh after a conflict instead of retrying stale edits automatically.

## Evidence state

Per-concept summaries use categorical states: `not_assessed`, `introduced`, `needs_check`, `supported_with_help`, `supported_independently`, `needs_revisit`. These describe available evidence, not a permanent student label. A follow-up can revise the summary without deleting earlier attempts.

Record `assessment_status` as `checked`, `provisional`, or `uncertain`. Free-text model assessments remain provisional unless a suitable rubric/check supports them. Do not expose an uncalibrated numerical mastery score.

## Immutable run identity

Canonicalize recipe parameters with sorted keys and documented numeric types; hash the canonical JSON with the recipe version and seed. Retain the runner image digest and numerical library version with output. A plot references an actual `run_id` and output field, never a model-authored series.

## Delete and expiry semantics

Mark the owner deleted/expired and increment active fences before cleanup. Cancel queued/running jobs. Remove raw files, extracted text, snapshots, events, run output, and relevant logs/artifacts according to retention policy. A worker checks deletion and fencing immediately before every commit. Late model output cannot recreate deleted records.

Keep only aggregate non-identifying operational counts after content deletion when justified; do not retain raw answers under a vague analytics exception. Short-lived backups must follow the documented retention window and are excluded from claims of immediate physical erasure until purged.
