# API Contracts

**Prefix:** `/api/v1` · **Schema:** 1 · **Transport:** same-origin HTTPS JSON, except multipart upload and PDF bytes

## Authentication and request rules

`POST /guest-sessions` creates an opaque guest cookie with `HttpOnly`, `Secure` in HTTPS environments, and `SameSite=Lax`; return a CSRF token in JSON. Require a same-origin `Origin` and JSON content type for this bootstrap. Mutating authenticated calls require an allowed Origin and CSRF header. Local development uses an explicitly configured loopback origin; no wildcard credentialed CORS.

Every private endpoint checks owner and expiry, including file, job, event stream, and result endpoints. Return a consistent `404 RESOURCE_NOT_FOUND` for another owner's resource. Ownership comes from the cookie, never a client `owner_id` field.

State-changing session requests include `expected_revision`; meaningful authenticated create/mutation calls require `Idempotency-Key`. Reuse with the same fingerprint returns the original result. Reuse with different input returns `409 IDEMPOTENCY_CONFLICT`. Guest bootstrap is the explicit exception because no owner identity exists yet.

## Endpoints

| Method and path | Request | Successful response |
| --- | --- | --- |
| POST `/guest-sessions` | Empty JSON | 201 guest expiry and CSRF token; cookie set |
| GET `/me` | Cookie | 200 expiry, limits, mode; no raw secret |
| DELETE `/me/data` | CSRF; idempotency key | 202 deletion ID; guest invalidated immediately |
| POST `/documents` | Multipart PDF; idempotency key | 202 document ID and parsing job ID |
| GET `/documents/{id}` | Owner cookie | 200 status, ordered page metadata, extraction warnings |
| GET `/documents/{id}/file` | Owner cookie | 200 PDF bytes, private/no-store headers |
| POST `/documents/{id}/selections` | Page range and question | 201 immutable selection, supported-topic assessment |
| POST `/learning-sessions` | Selection ID, goal, preferences | 202 session ID, revision, initial tutor job ID |
| GET `/learning-sessions/{id}` | Owner cookie | 200 committed snapshot, evidence summary, active job |
| POST `/learning-sessions/{id}/events` | Typed learner event envelope | 202 accepted event, current revision, tutor job ID |
| POST `/learning-sessions/{id}/runs` | Recipe parameters, expected revision | 202 run ID, current revision, job ID |
| GET `/runs/{id}` | Owner cookie | 200 run state, exact inputs, available output and checks |
| GET `/jobs/{id}` | Owner cookie | 200 state, progress, deadline, current session revision |
| GET `/jobs/{id}/events` | Owner cookie; `after` or Last-Event-ID | SSE ordered retained events |
| POST `/jobs/{id}/cancel` | CSRF; idempotency key | 202 cancellation requested or terminal state |
| GET `/health/live` | Public | 200 liveness only |
| GET `/health/ready` | Public | 200/503 dependencies ready; no secret values |

All writes validate length, content, owner quotas, and active-session fences on the server. Client-side rate limits are supplementary.

## Create a selection

```json
{
  "page_start": 1,
  "page_end": 3,
  "question": "Why is attention scaled?"
}
```

The range is 1-based and inclusive. The selection preserves content hash and extraction warnings. Reject an unreadable range with `422 SOURCE_UNREADABLE`; offer the supported example in the interface. Topic assessment may be provisional until the tutor evaluates the selected passage.

## Submit a learner event

```json
{
  "schema_version": 1,
  "event_id": "11111111-1111-4111-8111-111111111111",
  "event_type": "connection_submitted",
  "expected_revision": 7,
  "payload": {
    "task_id": "attention-connect-01",
    "task_variant": "v1-a",
    "edges": [{"from_object_id": "weights", "to_object_id": "values"}]
  }
}
```

Supported semantic types: `message_submitted`, `object_question_submitted`, `connection_submitted`, `prediction_submitted`, `explanation_submitted`, `hint_requested`, and `annotation_submitted`. High-frequency pointer movement is local UI state, not a stream of tutor calls. Every submitted semantic event queues a bounded tutor job after task/board validation. The agent may simply acknowledge an annotation when no new instruction is warranted.

## Run request

```json
{
  "expected_revision": 11,
  "recipe_id": "attention_scaling_v1",
  "parameters": {"dimensions": [8, 32, 128], "n_keys": 8, "trials": 100, "seed": 42}
}
```

Parameters must match the recipe schema. The server computes hashes and creates the immutable run record. Both this endpoint and the tutor's run tool invoke the same validated service. Results are obtained through jobs/runs; there is no public shell or container endpoint.

## Errors

```json
{
  "error": {
    "code": "REVISION_CONFLICT",
    "message": "The lesson changed. Refresh before submitting this answer.",
    "request_id": "22222222-2222-4222-8222-222222222222",
    "retryable": true,
    "details": {"current_revision": 12}
  }
}
```

| Status | Codes |
| --- | --- |
| 400 | `INVALID_REQUEST`, `INVALID_CSRF`, `ORIGIN_REJECTED` |
| 401 | `GUEST_REQUIRED`, `GUEST_EXPIRED` |
| 404 | `RESOURCE_NOT_FOUND` |
| 409 | `REVISION_CONFLICT`, `SESSION_BUSY`, `IDEMPOTENCY_CONFLICT` |
| 413 | `UPLOAD_TOO_LARGE`, `OUTPUT_TOO_LARGE` |
| 422 | `UNSUPPORTED_DOCUMENT`, `SOURCE_UNREADABLE`, `PARAMETERS_INVALID`, `TASK_STALE` |
| 429 | `RATE_LIMITED`, `OWNER_QUOTA`, `BUDGET_EXHAUSTED` |
| 503 | `PROVIDER_UNAVAILABLE`, `RUNNER_UNAVAILABLE`, `SERVICE_NOT_READY` |

Do not include stack traces, provider keys, filesystem paths, or another owner's metadata in errors.

## Streaming and replay

SSE envelopes contain `job_id`, monotonic `sequence`, `event_type`, timestamp, current revision, and a bounded data object. Types include `queued`, `running`, `board_updated`, `task_presented`, `run_started`, `run_completed`, `decision_recorded`, `failed`, and `terminal`.

Replay retained events after the provided sequence. The client deduplicates by job/sequence and fetches the latest session snapshot after reconnect. Streaming disconnects do not cancel jobs. If SSE is unavailable, poll job state every two seconds with backoff; do not submit a new job as a reconnection strategy.

## Cancellation and conflicts

Cancellation is idempotent. Already committed board steps remain; later work is fenced out. If the session is busy, the UI keeps a local draft and offers wait or cancel. It must not automatically send a stale mutation after the active job finishes. Refresh the revision and let the user submit the still-relevant action.

Deleting owner data invalidates the credential immediately. A subsequent request using that invalidated guest credential can return 401 rather than replay a cached deletion response; it must never recreate the deleted owner or content. The deletion itself remains safe against duplicate processing.
