# Release and Operations Runbook

## Deployment invariant

One API instance, one worker, one SQLite volume, private files, and separate restricted parser/numerical profiles. Do not add replicas before changing the database/job architecture. Keep the worker/runtime control channel private.

## Startup

Validate required configuration without printing secrets. Apply compatible database migrations once before admitting traffic. Verify the data directory permissions, runner/parser image digests, and worker heartbeat. A missing provider key, invalid rates, unavailable image, or unwritable database yields an explicit not-ready state.

The worker reconciles old leases at startup. Mark abandoned nonterminal jobs failed with `WORKER_LOST`; do not replay unknown external effects automatically. Retain already committed checkpoints and permit explicit retries with new request identity.

## Health and monitoring

Liveness checks establish process responsiveness. Readiness checks establish database access, required configuration, worker heartbeat, and runtime/image availability. Keep paid model probes separate from frequent health checks.

Track queue depth/wait, job state counts, worker heartbeat age, provider latency/errors, numerical check failures, runner timeouts, cost reservations/usage, expiry/deletion backlog, and private disk use. Record bounded IDs and error codes, not raw source text, answers, or keys.

## Cancellation and orphan work

Cancellation sets a flag and fences future writes. The worker terminates local runner containers promptly and checks flags around every model/tool step. Late remote output is discarded. Reap temporary files and container instances even on failure. Keep the cancellation and cleanup events for operational diagnosis without retaining private payloads after deletion.

## Retention sweeper

Every 15 minutes, find expired owners and invalidate access/fences before physical cleanup. Remove raw files, extracted pages, sessions, board snapshots, task attempts, decisions, run outputs, and child events. Reconcile temporary artifacts and abandoned job resources. API checks enforce expiry even if the sweeper is delayed.

A sweep failure is an operational error to repair and measure. Do not claim complete physical deletion while artifacts remain. The user-facing deletion request should invalidate access immediately and show that cleanup is in progress when it is asynchronous.

## Incident examples

| Symptom | Response |
| --- | --- |
| Provider errors spike | Stop unnecessary retries, preserve sessions, inspect actual account/protocol status |
| Budget exhausted | Reject new paid work, reconcile pending reservations, explain the limit |
| Numerical checks fail | Suppress validated-result claims; investigate recipe/version/input differences |
| Worker missing | Fail readiness, reconcile leases, restart deliberately without automatic replay |
| Cross-owner exposure | Stop affected access, fix authorization, assess exposed data and credentials, reverify |
| Disk/cleanup backlog | Stop new uploads if needed, repair cleanup, verify all retained paths |
| Old output shown as current | Correct run/revision binding and recheck the release journey |

## Backups

Prefer backups of code, lockfiles, image identities, and author-created demo material. Private student-content backups are disabled by default for the short-retention prototype. If enabled later, document encryption, access, expiry, restore isolation, and deletion implications before promising erasure behavior.

## Release procedure

Choose a tested commit and image digest, verify migrations, stop/drain intake as appropriate, deploy, run focused hosted checks, then enable ordinary traffic. Verify ownership, one live Meta turn, every recipe, source/evidence links, cancellation, and expiry. Record actual version and results in the handoff.

## Rollback

Stop new intake, fence/cancel active jobs safely, restore a compatible known-good application/worker image, and verify the database schema matches. Preserve private data boundaries. Avoid destructive schema changes during the final submission window; migration rollback must be designed rather than assumed.

## Judging availability

Retain the submitted version and a compatible runtime through judging under the event's actual requirements. Monitor the approved budget and health. Clearly disclose any permitted fixes or method changes. Do not silently replace a live service with a cached demo while presenting it as the same evaluated behavior.
