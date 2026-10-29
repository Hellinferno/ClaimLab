# Changelog

## 29 October 2026 — Review fixes

- Re-uploading the same PDF returns the existing document instead of consuming quota; quota messages explain how to start fresh.
- A lesson whose first tutor turn fails is removed, so outages no longer consume session quota or reopen as an empty lesson.
- Live answers are graded only after the provider succeeds; failed provider calls release their budget reservation.
- Live questions keep the current task variant instead of resetting to the first task.
- API tutor jobs carry a lease; an orphaned turn no longer locks answers and experiments until the guest expires.
- Data deletion removes uploads by document identity, so a changed `DATA_DIR` cannot block erasure, and unrelated files are never touched.
- Shared helpers for the latest tutor step and retained run records; the live seed run now records its job and timestamps.
- README and setup docs: backend port 8080 matches the Vite proxy; corrected test counts, settings names, and fixture labelling.
- Live tutor (found in a live-model browser review): model whiteboard notes now reach the board, a truncated or empty closing reply no longer replaces the model's narration with a generic sentence, aliased recipe inputs no longer fail strict validation, and the seeded scaling plot always shows a scaling run.
- The lab's check summary no longer counts not-applicable checks as failures ("4/4 checks passed · 1 not applicable").

## 28 October 2026 — Workspace usability and regression fixes

- Rebuilt the local workspace with a light source reader, focused teaching board, responsive navigation, numerical lab, and learning trail.
- Added explicit example start, real PDF page/question selection, truthful inline failures, and retained source/narration/run restoration.
- Corrected chart scales, run identity, dynamic dimensions/matrices, stale-result handling, clipped equations, and keyboard board inspection.
- Deferred KaTeX until mathematics appears, reducing initial JavaScript by about 49%; moved PDF parsing off the async request loop.
- Fixed owner bootstrap, idempotent retries, stale tasks, ungraded questions, live-provider failure reporting, and retained numerical execution metadata.
- Added isolated headed Chrome regressions and backend workspace regressions. See `docs/25_STATUS_AND_HANDOFF.md` for final results and remaining release gaps.
- Owner deletion purges the owner's files and database content (applied after the first draft of this entry; regression-tested).

## 1.0 — 27 October 2026

- Preserved the agreed idea as a reference document.
- Defined the first supported learning loop and acceptance criteria.
- Selected a single-instance architecture with a shared board, durable worker, and reviewed numerical recipes.
- Documented data, API, agent, experiment, observation, evaluation, privacy, and deployment contracts.
- Added coding-tool handoffs, daily tasks, and hackathon demonstration/submission guidance.

This entry records documentation created. It does not record a completed implementation or deployment.
