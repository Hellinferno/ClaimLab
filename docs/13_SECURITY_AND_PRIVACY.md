# Security and Privacy Design

## Scope

This is a design and verification specification, not a completed audit. Protect guest documents, student responses, provider credentials, execution infrastructure, and the integrity of lesson/run evidence.

## Ownership

Generate a cryptographically random opaque guest credential; store its hash and compare securely. The cookie is HttpOnly, Secure under HTTPS, SameSite=Lax, and expires with the server-side guest. Owner IDs alone are not authentication credentials.

All document, source, learning-session, run, job, event stream, and file lookups include owner and expiry checks. Verify both direct and relationship-based access. Unpredictable UUIDs supplement ownership; they do not replace it.

Use same-origin mutation checks and CSRF tokens. Do not allow wildcard credentialed CORS. Protect resource creation and deletion as well as lesson actions. Rotate deployment secrets through configuration; do not expose values in readiness endpoints.

## Upload boundary

Accept one PDF within byte/page/owner quotas. Check content signature and parser outcome rather than trusting the filename/MIME alone. Use generated storage keys; preserve the original filename only as escaped display text. Reject encrypted/password-required PDFs in the first release.

Parse inside a restricted profile with a read-only mount of only the submitted PDF. Enforce memory, wall time, output size, and character limits. Image-only pages receive an unreadable/OCR-needed status; OCR is outside P0. Embedded PDF actions, attachments, URLs, and scripts do not execute.

No arbitrary URL ingestion in P0. This avoids an unnecessary network-fetch surface and keeps source ownership clear.

## Prompt and tool boundary

Uploaded material and learner content are quoted data. They cannot change tool allowlists, reveal secrets, select other owners, or request arbitrary execution. System instructions state this, but server-side schema and authorization checks enforce it.

Pass the model only relevant excerpts and needed session summaries. Never include provider keys, storage credentials, raw guest tokens, or host configuration in model context. Validate citation IDs against stored source anchors and diagram IDs against the active scene.

## Numerical execution

Only reviewed recipes run. The numerical image receives validated JSON through stdin and no user code, raw source PDF, application database, secrets, host workspace, or Docker socket. It has no network and runs as a non-root user with read-only root, capped tmpfs, dropped capabilities, no-new-privileges, seccomp, and resource limits.

The trusted worker's container-runtime control is privileged infrastructure. Run it on a dedicated host/profile, keep its channel private, and never accept arbitrary container options through the application. Avoid treating a Python subprocess or a normal web process as a substitute security boundary.

## Rendering

Escape all user/model text. Render safe LaTeX with trusted extensions disabled. Do not use model HTML/SVG via unsafe injection. Allowlist board operations and chart output references. Serve uploaded PDFs privately with no-store caching and appropriate content-security policies. Keep viewer and parser dependencies current under locked versions.

## Data handling

Explain in the upload flow that relevant excerpts are processed by the configured model provider. Use the standard model variant and do not silently enable contributor/training mode. Describe actual provider terms after verification; do not promise zero retention without support.

P0 history is guest-bound and expires after 24 hours from creation. The user can delete earlier. Operational logs contain request/job IDs, state, timing, usage, and error codes; raw documents, answers, cookies, and secrets are excluded by default. Evidence needed for the student's session belongs in the private database, not general logs.

## Deletion and cleanup

Immediately invalidate access and active-job fences, then cancel work and delete content/artifacts. Cleanup runs every 15 minutes, with owner-expiry checks at every API/worker access. Include failed-job temporary files and container remnants. A worker must recheck deletion/fencing before commit.

Backups containing private content should not be enabled casually for this short-retention prototype. If enabled, encrypt them, define their expiry, and state the deletion limitation honestly. Prefer a reproducible demo fixture backup and infrastructure configuration backup without student content.

## Verification gates

Cross-owner tests, malicious PDF handling, injection attempts, output/argument schema rejection, missing CSRF, stale fencing after deletion, no-network runner checks, key scanning, and budget exhaustion must be covered. Do not claim these controls exist until verified in the deployed environment.

Security-sensitive features outside this plan need a fresh design decision. Ordinary code edits and tests remain within the user's requested build workflow; this document does not create blanket approval requirements for them.
