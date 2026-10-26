# Implementation Plan

## Execution principle

Build dependency-ready vertical slices. A stage is complete only with its acceptance evidence. Use the [daily schedule](16_DAILY_TASKS.md) as an estimate; preserve the product's three essential parts if later scope must be cut.

## M0 — Establish the foundation

**Inputs:** This pack; available local tools; an actual Meta account/key if supplied.

**Work:** Inspect the repository, establish React/TypeScript and Python projects, create canonical schemas, set configuration/secret boundaries, add health endpoints, and run a minimal real Meta request plus one tool round-trip. Resolve exact package versions and commit lockfiles. Build a minimal restricted runner image and prove it accepts one reviewed numerical recipe.

**Output:** A local shell, typed contracts, provider probe evidence, and numerical runner proof. Fixture mode can unblock UI development while missing access remains explicit.

**Exit:** T-META-01 verified when access exists; no secret exposure; runner isolation probe. Missing provider access is recorded as a release blocker, not a reason to mislabel fixture work.

## M1 — Source and owner foundation

**Dependencies:** M0 contracts and runtime.

**Work:** Guest identity, CSRF/Origin checks, private storage, bounded parsing jobs, per-page extraction status, selections/anchors, durable worker claims, and cleanup lifecycle.

**Output:** A student can upload a supported note and view selected source text without another owner seeing it.

**Exit:** Relevant authentication, PDF, source, job, idempotency, and expiry tests pass.

## M2 — A real visual lab

**Dependencies:** M0 runner and M1 state.

**Work:** Shared scene schema, safe renderer, atomic board patches, the three reviewed recipes, check reports, actual-output charts, parameter controls, and stale-result behavior.

**Output:** A working lab workspace with traceable results and meaningful board objects.

**Exit:** Numerical/reference tests, board validation, run/plot binding, and keyboard task interaction pass. Static hardcoded results cannot satisfy this stage.

## M3 — Meta-powered teaching loop

**Dependencies:** M1 source anchors and M2 actions.

**Work:** Bounded context construction, typed tool dispatch, teaching-step checkpoints, task presentation, model usage reservations, error recovery, and job progress events with polling fallback.

**Output:** A real model explains selected material, draws relevant content, selects/runs a supported experiment, and asks for student participation.

**Exit:** Live and fixture modes are distinct; source IDs validate; limits and failure states work; a tool loop succeeds without hidden canned responses.

## M4 — Observation and adaptation

**Dependencies:** M3 and task bank.

**Work:** Learner-event persistence, deterministic assessment for structured tasks, qualified free-text interpretation, concept evidence states, decision records, and new application variants.

**Output:** An observed misconception changes a later explanation or experiment, followed by an independent task.

**Exit:** T-LEARN-01/02 and a live supported adaptation path pass. Demonstrate different next actions for different evidence.

## M5 — Integration and dependable release

**Dependencies:** Complete supported learning loop.

**Work:** Resume, cancellation/deletion fencing, provider/worker failures, ownership across every route, UI accessibility, source rights, deployment, budget enforcement, and release checklist.

**Output:** A hosted testable product with stated limits and reproducible demo material.

**Exit:** All P0 criteria pass in the chosen environment, including real provider and restricted execution tests. Deployment/publication actions remain subject to Ravi's actual authorization.

## M6 — Evidence and submission

**Dependencies:** M5.

**Work:** Optional small learning pilot if participants are available, three-minute recording, accurate methodology/limitations, public repository preparation, attribution, and portal field verification.

**Output:** A reviewable submission whose claims match actual behavior.

**Exit:** Links, accessibility, video duration, contributor details, current official terms, and newly built work are verified. Do not mark submitted until the portal returns confirmation.

## If the schedule slips

First remove later features and cosmetic work. Reduce animation to clear step reveals and simplify layout while preserving accessibility. Keep supported methods bounded. If a core P0 feature cannot be completed, document the reduced product honestly rather than claiming the complete ClaimLab experience.

No stage requires three simultaneous coding tools, a custom-trained model, vector infrastructure, or microservices.
