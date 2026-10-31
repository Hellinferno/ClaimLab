# Changelog

## 31 October 2026 — Workspace divided into pages

- The navigation rail now switches between four pages instead of scrolling one long page: Source, Whiteboard (board beside the tutor), Experiment, and Progress. Each page has its own heading and URL hash, so Back/Forward and reload keep your place.
- Uploading a PDF opens the Source page; starting a lesson opens the Whiteboard. The welcome board links to the Source page for your own PDF.
- Switching pages keeps unsent answers, lab inputs, and board state.
- The tutor panel sits beside both the Source and the Whiteboard pages, so an answer appears where you asked; asking from Source no longer jumps to the Whiteboard. While the tutor works, the panel says so and counts the seconds. The learning loop moved to Progress.
- Live tutor answers your question directly in the first step, with concrete, detailed steps (numbers, definitions, worked examples) instead of one-line notes. Steps no longer render as titles only when the model sends their text as a list or object.
- Faster live turns: no re-reading of a passage already in context, web research only when the passage leaves a gap, and feedback on an answer reuses the lesson's experiment (with its measured numbers) instead of writing a new one. On the pairs-trading paper: first turn 50 s → 23–36 s; wrong-answer feedback 36 s → 17 s when the check was a number.

## 29 October 2026 — Any paper: paged whiteboard lessons, sandboxed experiments, web research

- Open lessons: in live mode any readable paper can be taught; the reviewed attention lab is chosen only for passages about the attention mechanism itself (a paper that merely uses attention no longer gets the attention diagram).
- The tutor teaches in 2–5 short pages. Each page draws on the whiteboard (concept boxes with arrows, equations, verbatim source quotes, notes, measured plots) and the board reveals each page's drawing in turn. Markdown now renders instead of showing raw `**`.
- Tutor-written experiments: the tutor writes a small numpy experiment for the paper's own mechanism, which runs in an isolated sandbox (`python -m claimlab.scripts.setup_sandbox`). Learners see the code and checks and can re-run it with the knobs the tutor declared.
- Web research through TinyFish search and fetch when `TINYFISH_API_KEY` is set; web pages are cited and treated as untrusted data.
- Adaptation for open lessons: tutor-written number/choice checks are graded against a private key; written answers are judged by the tutor and recorded as provisional; the two-variant evidence policy applies. The learning trail shows the concepts the tutor actually checked.

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
