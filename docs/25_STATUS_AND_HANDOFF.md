# Status and Handoff

**Updated:** 31 October 2026 IST · **Stage:** Local implementation verified offline and with the live model, including open lessons for any paper with sandboxed tutor-written experiments; deployment/release completion not established

## Completed in this deliverable

- Agreed combined idea preserved.
- PRD, acceptance criteria, architecture, technical/data/API contracts drafted.
- Whiteboard, experiment, observation, agent, evaluation, security, and test specifications provided.
- Dependency-ordered implementation plan, daily tasks, deployment/operations guidance, and hackathon preparation provided.
- Claude Code, Codex, and Antigravity handoff documents provided.

## Actual implementation status

| Item | State |
| --- | --- |
| Application repository and code | Implemented (FastAPI backend + React/TypeScript frontend + contracts) |
| Exact dependency locks | Resolved and locked (`backend/requirements.txt`, `backend/requirements.lock`, `frontend/package.json`) |
| Meta account/model access | 29 October: T-META-01/02 rerun and passed against `muse-spark-1.3`; a local live-mode browser lesson (start, answer, question, reload, delete) completed. Missing/failed live access returns 503 without fixtures |
| Runner runtime | Three reviewed recipes checked locally. Tutor-written experiments run in a dedicated `.sandbox-venv` interpreter with AST/import allowlists and, on Windows, a Job Object (verified locally); container/OS-level isolation and the Linux limits are not verified |
| Application tests | 29 October (evening): 112 offline tests passed, 2 live tests passed, 9/9 Chrome flows passed, plus a live-model browser walkthrough of an open lesson. See the latest dated entry |
| Behavioral Evaluation Benchmark | 12/12 fixture cases included in the offline suite. Owner DB erasure is covered separately by `test_delete_erases_all_owner_content_and_preserves_another_owner`. Live benchmark was not rerun |
| Frontend compilation | TypeScript + production Vite build pass; KaTeX deferred until mathematics is shown |
| Linter | Backend Ruff and frontend Oxlint pass |
| Public repository/submission | Pushed to GitHub `https://github.com/Hellinferno/ClaimLab.git` on branch `main` |

---

## Progress Entry: 27 October 2026 (Day 1 — Foundation & Core Loop Established)

### 1. Active Environment & Repository
- **OS:** Windows 11, Shell: PowerShell
- **Runtimes:** Python 3.12.10, Node v24.12.0, npm 11.6.2, Git 2.51.2
- **Git:** Initialized at repository root `D:\Meta hackathon`
- **Virtualenv:** `.venv` established and active with locked dependencies

### 2. Implemented Requirements & Changed Files
- **Backend Core:**
  - `backend/pyproject.toml`, `backend/requirements.txt`
  - `backend/src/claimlab/config.py`: Settings with Pydantic Settings v2
  - `backend/src/claimlab/database.py`: SQLite engine with automatic directory creation
  - `backend/src/claimlab/models.py`: 14 SQLAlchemy entities matching PRD data contracts
  - `backend/src/claimlab/security.py`: Guest cookie authentication, HMAC-SHA256, and CSRF protection
  - `backend/src/claimlab/contracts/`: Canonical schemas for auth, documents, whiteboard, experiments, sessions, observations, and jobs
  - `backend/src/claimlab/numerics/recipes.py`: All 3 reviewed numerical recipes (`softmax_sensitivity_v1`, `attention_scaling_v1`, `causal_masking_v1`)
  - `backend/src/claimlab/numerics/runner.py`: Numerical runner with canonical parameter hashing and check reports
  - `backend/src/claimlab/services/pdf_service.py`: PDF extraction, normalization, and source anchor generation
  - `backend/src/claimlab/services/generate_sample_pdf.py`: Creates `examples/claimlab_attention_lab.pdf` matching reference lessons
  - `backend/src/claimlab/services/agent_orchestrator.py`: Meta Model tutor orchestrator with deterministic teaching turns and learning adaptation
  - `backend/src/claimlab/api.py`: FastAPI endpoints for health, guest sessions, document upload, selections, learning sessions, learner events, runs, jobs, and static mounting
- **Frontend Core:**
  - `frontend/package.json`, `frontend/vite.config.ts`, `frontend/tsconfig.json`
  - `frontend/src/types.ts`: TypeScript interfaces matching backend contracts
  - `frontend/src/components/Whiteboard.tsx`: SVG whiteboard with KaTeX equation rendering and run-grounded variance plots
  - `frontend/src/components/ExperimentPanel.tsx`: Interactive lab with parameter controls, stale detection, results tables, and check lists
  - `frontend/src/components/SourceViewer.tsx`: Document reader with 3 sections and interactive source anchors
  - `frontend/src/components/TaskCard.tsx`: Task presentation, tutor feedback narration, and answer submission
  - `frontend/src/components/EvidencePanel.tsx`: Dynamic concept evidence badges (`introduced`, `needs_check`, `supported_independently`)
  - `frontend/src/App.tsx`, `frontend/src/index.css`: Full responsive workspace layout
- **Contracts Export:**
  - `contracts/types.ts`: Shared type definitions

### 3. Checks & Verification Evidence
- **Pytest Suite:** 11 passed in 2.28s (`backend/tests/test_numerics.py`, `backend/tests/test_api.py`)
  - Verified numerical invariant checks on all 3 recipes
  - Verified guest creation, CSRF, and cross-owner 404 isolation
  - Verified complete upload-to-selection-to-teaching loop
  - Verified student task submission, evaluation, and learning adaptation
- **Ruff Linter:** `ruff check backend/` passed with 0 errors
- **TypeScript Build:** `npm --prefix frontend run build` succeeded with 0 errors

### 4. Model Mode & Status
- Running in `fixture` mode (`MODEL_MODE=fixture`) with transparent label in UI
- Ready to switch to `live` mode as soon as `META_API_KEY` is provided in `.env`

### 5. Next Steps
- Verify live background worker queue execution (`python -m claimlab.worker`)
- Add end-to-end Playwright tests if browser automation is requested
- Prepare demo video walkthrough script

---

## Progress Entry: 27 October 2026 (Day 2 — Atomic Whiteboard Engine, Task Bank, Worker & Spec Verification Suite)

### 1. Active Environment & Repository
- **Remote:** `https://github.com/Hellinferno/ClaimLab.git` (tracked to `main`)
- **OS:** Windows 11, Shell: PowerShell
- **Runtimes:** Python 3.12.10, Node v24.12.0, npm 11.6.2, Git 2.51.2
- **Virtualenv:** `.venv` active with locked requirements in `backend/requirements.lock`

### 2. Implemented Components & Files
- **Atomic Whiteboard Patch Engine:**
  - `backend/src/claimlab/whiteboard/engine.py`: Implemented `apply_atomic_patch` supporting `add_object`, `update_object`, `add_connector`, `highlight_objects`, `remove_object` (with cascading connector removal), `set_active_group`, and `clear_highlights`. Enforces 100 max objects, 20 max commands, label length limits, and LaTeX/HTML injection filtering.
- **Task Bank & Learning Adaptation:**
  - `backend/src/claimlab/learning/task_bank.py`: Implemented 12 canonical tasks from `docs/27_REFERENCE_LESSONS.md` with deterministic evaluation rubrics (number tolerances, normalized vectors, choice matching).
  - `backend/src/claimlab/learning/adaptation.py`: Implemented two-variant progression rule before `supported_independently`, prerequisite scaffolding on error, and `TeachingDecision` recording.
- **Background Worker Loop:**
  - `backend/src/claimlab/worker.py`: Durable polling loop with leasing heartbeats, retry counts, error event logging, and cooperative cancellation.
- **Infrastructure & Additional Reference Notes:**
  - `examples/unsupported_sample.pdf`: Botany document to verify topic boundary classification.
  - `examples/heldout_attention_note.pdf`: Transfer test document.
  - `infra/runner/Dockerfile` & `infra/parser/Dockerfile`: Isolated container runner configurations.
- **Enhanced Frontend UI:**
  - `frontend/src/App.tsx`: Auto-resumes active session on reload (`/learning-sessions/active`), manages CSRF tokens, includes Idempotency-Key headers, supports custom PDF upload, and provides full data purge button.
  - `frontend/src/components/Whiteboard.tsx`: Renders all 3 recipe outputs (Recipe A probability distribution bar chart, Recipe B variance vs dimension line chart, Recipe C causal lower-triangular heatmap grid).
  - `frontend/src/components/TaskCard.tsx`: KaTeX math prompt rendering, choice button support, guided hint toggling, and epistemic tags (`[Source]`, `[Experiment]`, `[Background]`).
  - `frontend/src/components/SourceViewer.tsx`: Extracted page text display and file upload trigger.

### 3. Checks & Verification Evidence
- **Pytest Suite:** 18/18 tests passed in 5.55s (`backend/tests/test_numerics.py`, `backend/tests/test_api.py`, `backend/tests/test_complete_spec.py`)
  - `test_t_auth_01_guest_creation_and_cookie`: PASSED
  - `test_t_board_01_atomic_patch_engine`: PASSED
  - `test_t_tutor_01_unsupported_topic_boundary`: PASSED
  - `test_t_learn_two_variant_progression`: PASSED
  - `test_t_idem_01_idempotency_enforcement`: PASSED
  - `test_t_job_cancel_endpoint`: PASSED
  - `test_t_data_01_full_deletion_lifecycle`: PASSED
  - `test_complete_learning_journey`: PASSED
  - All 8 numerical recipe unit tests: PASSED
- **Ruff Linter:** Clean across `backend/` (0 errors)
- **Frontend Build:** `npm --prefix frontend run build` succeeded (486ms, 22 modules transformed, 0 TS errors)

---

## Progress Entry: 27 October 2026 (Day 3 — Live Meta Model Tool Loop Verified & Production Harness Complete)

### 1. Active Environment & Repository
- **Remote:** `https://github.com/Hellinferno/ClaimLab.git` (tracked to `main`)
- **OS:** Windows 11, Shell: PowerShell
- **Runtimes:** Python 3.12.10, Node v24.12.0, npm 11.6.2, Git 2.51.2
- **Virtualenv:** `.venv` active with locked requirements
- **Active Model Target:** Meta `muse-spark-1.3` in `live` mode

### 2. Implemented Requirements & Changed Files
- **Live Meta Model Adapter & Telemetry:**
  - `backend/src/claimlab/scripts/probe_meta_api.py`: Automated CLI verification probe for `T-META-01` with sanitized token/latency diagnostics.
  - `backend/tests/test_live_meta.py`: Acceptance tests for `T-META-01` (provider probe) and `T-META-02` (live orchestrator tool loop).
  - `backend/src/claimlab/services/agent_orchestrator.py`: Hardened live tool loop with parameter normalizations (`attention_scaling_v1`, `softmax_sensitivity_v1`, `causal_masking_v1`), safe board patch recovery, student evidence progression, and job event emission.
- **Test Invariant Separation:**
  - `backend/tests/test_api.py`, `backend/tests/test_complete_spec.py`, `backend/tests/test_evaluation_harness.py`: Wired deterministic fixtures for offline reproducibility, while `test_live_meta.py` exercises the real Meta API endpoint.
- **Evaluation Benchmark:**
  - `backend/src/claimlab/evaluation/benchmark.py`: 12/12 behavioral evaluation cases passing (100%) in both live and fixture modes.

### 3. Checks & Verification Evidence
- **Pytest Suite:** 27/27 tests PASSED in 16.87s
  - `test_t_meta_01_provider_probe`: PASSED against Meta API (HTTP 200, latency ~2.6s)
  - `test_t_meta_02_orchestrator_live_turn`: PASSED with tool loop execution (`run_experiment`, `present_teaching_step`)
  - All 25 complete spec and numerical recipe tests: PASSED
- **Behavioral Evaluation Benchmark:** 12/12 cases PASSED (100.0%) in 91.81s (`reports/evaluation_benchmark_report.json`)
- **Ruff Linter:** Clean across `backend/` (0 errors)
- **Frontend Build:** `npm --prefix frontend run build` succeeded (556ms, 0 TS errors)

## Next dependency-ready step

M5 remains open. Resolve complete owner erasure (approval pending for the prepared patch), verify isolated parser/recipe execution and durable job/cancellation behavior, then rerun a real supported Meta journey before claiming release readiness. A local fixture browser preview is development evidence; it is not a deployed/live-model demonstration.

## Handoff format for future sessions

Append a dated entry with:

1. Actual repository/branch/commit and active environment.
2. Implemented requirements and changed files.
3. Exact checks run, their results, and unresolved failures.
4. Model mode/ID and sanitized live evidence when applicable.
5. Actual supported recipes and known scope limits.
6. Decisions that changed a contract or dependency.
7. Current blocker and the next concrete independent/dependency-ready action.

Keep secrets, raw student documents, and private account information out of this handoff. No state should be marked live/deployed/submitted without supporting evidence.

## Default behavior when a new coding tool takes over

Read the actual repository and this status first. Preserve implemented working behavior. Do not restart the project merely because another tool authored it. Resolve a genuine specification conflict in the decision log and update affected contracts together.

---

## Progress Entry: 28 October 2026 — UI, headed-browser verification, and consequential regressions

**Repository/environment:** working tree on `main`, base commit `5aead92`; Windows/PowerShell, Python 3.12 virtual environment, Node 24, installed Google Chrome. No new commit, push, deployment, or submission. User's pre-existing Vite API port 8080 was preserved.

**Milestone:** M5 usability and regression work, preserving the detailed concept and all three product parts. Rebuilt the source/whiteboard/lab workspace; added explicit example start and actual PDF question/page selection; fixed source/narration/session restoration, stale results, chart geometry, equation clipping, keyboard inspection, provider-failure reporting, idempotent retries, task identity, and retained execution metadata. PDF parsing no longer blocks the async request loop. KaTeX now loads only when mathematics appears, reducing initial JavaScript by about 49% (529.57 → 272.51 kB in the production build).

**Learning evidence:** delivered hints/questions and incorrect-answer feedback are now retained as assistance for the same task/variant. Only two distinct correct unassisted variants qualify as independent evidence. Fresh variants remain eligible; pre-fix historical evidence is not retroactively relabelled. The strategy control records a hint event before revealing help, and failed tutor requests preserve drafts.

**Checks:** backend `pytest backend/tests -m "not live_meta" -q`: **52 passed, 2 deselected**; backend Ruff: passed. Frontend `npm run build`, `npm run lint`: passed. `npm --prefix frontend run test:e2e:headed`: **9/9 Chrome flows passed** including all three actual numerical recipes, exact run/plot binding, keyboard answers, assisted-credit handling, one-page and unsupported sources, failure recovery, owner isolation, reload, mobile/reduced motion, equation bounds, and no unexpected runtime/React console errors. `git diff --check`: passed. Expected HTTP-negative-case console messages are excluded from the unexpected-error assertion.

**Evidence:** [verification report](../reports/ui-verification.md), `reports/ui-*.png`, and `reports/ui-browser-metrics.json`. These use synthetic fixture data. The local timings are single observations, not percentiles or live-model measurements. Backend regression tests are in `backend/tests/test_workspace_regressions.py`; browser tests are in `frontend/e2e/workspace.spec.ts`.

**Mode and preview:** offline fixture teaching, empty provider key, reviewed local NumPy recipes. All three recipes were executed in browser tests. A visible disposable Chrome preview was opened at `http://127.0.0.1:5174` (isolated API 8081); reopen with `npm --prefix frontend run preview:fixture`. Closing that browser window stops its preview servers. This is local development, not hosting/deployment evidence.

**Genuine remaining limits:** live Meta compatibility was not rerun; isolated parser/runner containers, durable job/cancellation behavior, and cleanup still need M5 release verification. Complete owner erasure remains incomplete: existing deletion removes PDFs/revokes access but leaves database content. Automatic approval review rejected the broader purge change, and the prepared `reports/proposed-owner-data-purge.patch` is unapplied pending requested user approval. The UI discloses the current deletion limit. Do not mark P0-16 or M5 complete from these tests.

**Next step:** resolve the pending owner-erasure decision, then verify the release isolation/worker/failure boundaries and a real supported Meta journey. Do not substitute a fixture preview for that evidence.

> Superseded in part by the 29 October entry: the owner purge has since been applied and tested, and the live tests were rerun.

---

## Progress Entry: 29 October 2026 — Review fixes, live-model browser review, and judge-facing accuracy

**Repository/environment:** working tree on `main`, base commit `5aead92`, uncommitted (no commit, push, deployment, or submission). Windows/PowerShell, Python 3.12 venv, Node 24, Google Chrome. `.env` uses `MODEL_MODE=live` with a configured key (value not recorded).

**Input:** a cloud code review of the working-tree diff (10 findings), followed by user, judge, and developer passes.

**Review findings and outcome**

| Finding | Outcome |
| --- | --- |
| Icon.tsx, Math.tsx, e2e/, playwright.config.ts missing | Not a code defect: the files exist but are **untracked**. They must be added with the commit or the frontend build fails |
| Failed first tutor turn leaves an empty session that holds quota and reopens on reload | Fixed: such a session is removed; the failed job is kept (D-18) |
| Live answer graded before the provider call, so a retry is double-graded | Fixed: grading happens after the provider succeeds; the failed call's budget is `released` (D-19) |
| Guest reuse makes upload/session quotas permanent; repeated example uploads use up slots | Fixed: same-SHA-256 uploads return the existing document; quota messages explain the reset (D-18) |
| Deletion blocked forever when a stored key is outside the current document root | Fixed: uploads are removed by document identity; unrelated files are never touched (D-21) |
| Vite proxy 8080 vs documented uvicorn 8000 | Fixed in README and doc 17 (8080 was the user's existing local choice) |
| Live question resets the task to v1-a | Fixed: non-answer events carry the current task forward |
| Orphaned RUNNING job locks the lesson until expiry | Fixed: API tutor jobs carry a 180 s lease that the busy checks honour (D-20) |
| Duplicated "latest tutor step" query | Fixed: `latest_tutor_step` helper |
| Four hand-built ExperimentRun copies; drifted live seed run | Fixed: `experiment_run_record` helper; the seed run records its job and timestamps |

**Found in the live-model browser review** (isolated data directory, real `muse-spark-1.3`): model board commands were always dropped (invalid `concept_card` objects); the tutor note sometimes became a generic fallback (reasoning tokens exhausted `max_tokens=1500`, or an empty final reply overwrote the step narration); aliased recipe inputs failed strict validation; the seeded scaling plot could bind to a softmax run; the lab showed "4/5 checks passed" when one check was only not applicable. All fixed (D-22). After the fixes the live lesson showed model narration, a model note on the board, the second task variant after a correct answer, the same variant after a question, full restoration on reload, and complete deletion. Per-turn latency was 18–36 s (single observations).

**Judge-facing accuracy:** the README claimed 21/25 tests, `META_API_URL`/`MAX_TUTOR_TURNS` settings that do not exist, a `[fixture: …]` UI label, a sandboxed runner, and a PDF-only purge. These were corrected to observed facts. The stale "erasure not implemented" statements in docs 03 and 22, CHANGELOG, and the 28 October UI report were corrected or annotated: the purge (`reports/proposed-owner-data-purge.patch`, now superseded) was applied after the 28 October entry.

**Checks (29 October):**

- `pytest backend/tests -m "not live_meta"`: 66 passed, 2 deselected.
- `pytest backend/tests -m live_meta`: 2 passed.
- `ruff check backend/`: passed.
- `npm --prefix frontend run build` and `lint`: passed.
- `npx playwright test`: 9/9 passed.
- `git diff --check`: clean.

Each new regression was confirmed to fail with its fix reverted.

**Genuine remaining limits:**

- Retention sweeper for expired guests (T-DATA-02) is not implemented or verified, so P0-16 is not complete.
- Isolated parser/runner containers are not verified.
- Tutor/recipe routes are still synchronous.
- The live benchmark was not rerun.
- Live model behavior varies: it sometimes needs a second `run_experiment` after a rejected parameter set; the rejection is returned to the model, which corrected itself in every observed case.
- A board plot bound to an earlier run shows a placeholder until selected (existing exact-run design).

**Next step:** commit the change *including the untracked frontend files*, then implement and test the expiry sweeper (T-DATA-02) and verify container isolation before release.

---

## Progress Entry: 29 October 2026 (evening) — Any paper: paged whiteboard lessons, sandboxed experiments, web research

**Repository/environment:** working tree on `main` at `6d9ca73`, uncommitted (no commit, push, or deployment). Windows/PowerShell, Python 3.12.10, numpy 2.1.3, Node 24, Chrome. `.env` uses `MODEL_MODE=live` with a configured Meta key; `TINYFISH_API_KEY` is not set yet, so web research is off.

**Trigger:** a learner uploaded *Machine Learning-Enhanced Pairs Trading* (Hadad et al., 2024). The old keyword gate accepted it as an attention source ("attention", "key"), the board showed the attention diagram, the tutor note was one long block with raw `**` Markdown, and the only experiments were the three attention recipes. The user asked for paged responses, a teaching whiteboard, adaptation, web search (TinyFish), and experiments that follow the paper.

**Behaviour changed (decisions D-23 to D-27 in doc 22):**

- Topic assessment counts distinct attention-mechanism terms; other readable text becomes an `open` lesson in live mode (still `unsupported` in fixture mode). `SessionStateResponse` adds `lesson_kind`, `tutor_steps`, `tutor_turn`, `web_sources`; `/me` adds `web_research`.
- Live tutor tools: `present_lesson` (paged steps with board items and a check), `run_python_experiment`, `web_search` and `read_web_page` (only with a TinyFish key), `assess_answer` (only when a written answer awaits judgment), plus the existing `get_source_excerpt` and `run_experiment`. Up to 7 provider calls per turn; after 150 s only `present_lesson` is offered. The turn lease rose from 180 s to 300 s; `max_tokens` from 4096 to 8192. The context now carries up to 14,000 characters of the passage, the board, evidence, the session's runs, the previous steps, and the graded answer.
- `services/lesson_builder.py` lays out the board, connects arrows, drops quotes not verbatim in their anchor and plots without a retained run, accepts drifted keys for step prose and tags, turns inline "A) … B) …" options into choices, and keys tutor checks privately. `services/sandbox_runs.py` retains sandbox runs (`sandbox_python_v1`) and re-runs them with declared knobs via `POST /runs` with `base_run_id`. `services/web_research.py` wraps TinyFish search/fetch. `claimlab/sandbox/` is the isolated executor; `python -m claimlab.scripts.setup_sandbox` creates `.sandbox-venv`.
- Frontend: a paged tutor note with safe Markdown and citations, choice answers, a whiteboard that reveals and highlights each step's drawing, a sandbox chart, a "Tutor's lab" panel (knobs, metrics, table, claim checks, code, printed output), and a learning trail that lists the open lesson's concepts.

**Checks:**

- `pytest backend/tests -m "not live_meta"`: 112 passed, 2 deselected (66 earlier + 34 sandbox + 12 open-lesson); 120 after the 30 October sandbox fix (+8).
- `pytest backend/tests -m live_meta`: 2 passed.
- `ruff check backend/`: passed. `npm --prefix frontend run build` and `lint`: passed. `npx playwright test`: 9/9 passed.
- Live API smoke on the pairs-trading paper (pages 1–2): classified `open`; the tutor wrote a paper-specific experiment (profit per trade versus an abstain threshold, with cost and noise knobs) whose claim checks passed, drew a concept chain with labelled arrows, the paper's hedge-ratio equation, verified source quotes, and the measured plot over four pages. Turn latency 33–43 s across four single observations.
- Live browser walkthrough (headless Chrome, real model): steps revealed 1→3→5→7 board items with no console errors. After a wrong answer the tutor diagnosed a total-versus-average misconception, revisited the source claim, and set a new variant.

**Failures found and fixed during this work (kept as evidence):** the pager split leaked tag names (capturing group in `re.split`); one live turn sent step prose under a key other than `say`, so the pages rendered titles only; the radio inputs inherited `width: 100%`; the measured chart appeared under the board before its step; quote cards showed the start of a page-sized anchor instead of the claim; tags and inline choices were lost when the model drifted from the schema; the progress panel listed only the six attention concepts. Each has a fix and, where it is backend logic, a regression test.

**Security review (30 October, automated):** flagged the sandbox's in-process policy as a file-read escape. Confirmed: `import numpy.ma.mrecords` passed the policy and `openfile(path)` attempted to open the path (it failed only because the child's working directory is empty; an absolute path would have been read). `np.ma`, `np.rec`, `np.char`, and `np.show_config()` were also reachable. Fixed by allowing numpy only through `numpy.random`, `numpy.linalg`, `numpy.fft`, and `numpy.polynomial` (enforced by the static policy and by the child's runtime module guard), and blocking the configuration reports. Eight regression tests added; the same probes are now rejected before any process starts. The review's main recommendation, OS-level isolation, is **not** implemented (see Unresolved).

**Unresolved:**

- `GET /api/v1/jobs/{id}/events` (pre-existing): FastAPI 0.115 closes the request's DB session before the streaming body runs, so the stream sends its first events and then fails on `db.refresh(job)`. The frontend does not use it; the new answer-key event is filtered from it regardless.
- Sandbox: the Python-level policy is the only file-access barrier. On Windows the child runs as the user, so a policy bypass could read the user's files and the tutor could then send them out through `web_search`. There is no OS-level network block (`socket` is not importable). Linux rlimits and process-group kill are untested. Real OS isolation (container with no network, read-only root, separate UID; or an AppContainer on Windows, which needs ACL changes on the Python install) is required before any hosted or shared use.
- Live model output still varies: for example, a chart that mixed series on different scales, or a check tagged `background`. The prompt and the normalizers reduce this but do not eliminate it.
- `uvicorn --reload` on Windows hung once after an edit (it logged "Reloading" and kept serving old code), so the README now starts the API without `--reload`.
- Carried over: expiry sweeper (T-DATA-02), synchronous tutor/recipe routes, and the live benchmark was not rerun.

**Next dependency-ready step:** add the TinyFish key and run a live lesson with web research; then commit (including the untracked `sandbox/`, `services/lesson_builder.py`, `sandbox_runs.py`, `web_research.py`, tests, `Markdown.tsx`, and `runs.ts`) and verify sandbox isolation on Linux CI before any hosted release.

**Addendum (30 October): web research live.** `TINYFISH_API_KEY` was added to `.env` (value not recorded). Search and fetch were verified directly (6 results; page fetched and truncated to 6,000 characters). On the first live lesson the tutor did not call web tools, so the first-turn context now asks for one cited `web` step; afterwards the tutor called `web_search` and `read_web_page` and cited Wikipedia/QuestDB pages. Knobs are now a required argument of `run_python_experiment` (one run had declared none). Further live drift found and handled, each with a regression test: drawings under keys other than `draw`, `type` instead of `kind`, synonym tags (`Measured`), cited URLs differing from the fetched URL in scheme/`www`/trailing slash, steps flattened into a single board item (logged shape: `id, kind, from, relation, latex, run_id` beside `say, tag`), and pre-lettered choices. Steps that arrive without prose or drawings are now logged by key shape (never content). The sandbox chart's tick labels follow the axis range. Checks: 121 offline tests passed, 9/9 Chrome flows passed; a live browser walkthrough showed the board growing 2→3→5→7 items, a cited web step, and a diagnosed wrong answer, with no console errors. First-turn latency with research: 43–90 s across three single observations.

---

## Progress Entry: 31 October 2026 — Workspace divided into pages

**Repository/environment:** working tree on `main` at `6d9ca73`, still uncommitted (includes the 29–30 October work). Windows/PowerShell, Chrome.

**Trigger:** the user found everything crowded onto one long page; the rail buttons only scrolled.

**Behaviour changed (D-28 in doc 22, UX doc 03 updated):** `frontend/src/App.tsx` defines four pages (Source, Whiteboard, Experiment, Progress), switched from the rail and kept in the URL hash (`pushState` plus a `popstate` listener, so Back/Forward and reload work). Inactive pages carry the `hidden` attribute (`[hidden] { display: none !important }`) and are not unmounted, so drafts, lab inputs, and board selection survive switching. Each page has its own heading. The Whiteboard page shows the board and the tutor card side by side (tutor column 330–420 px), stacked below 1080 px; Source places the reader beside the learning loop; Experiment and Progress use a single 760 px column. Uploading opens Source, a successful lesson start opens Whiteboard, and the welcome board gained an "Or bring your own PDF" link to Source. The skip link targets the active page.

**Checks (31 October):**

- Before the change: `pytest backend/tests -m "not live_meta"` 121 passed, 2 deselected; `ruff check backend/` passed; frontend build passed.
- After: `npm --prefix frontend run build` and `oxlint` passed; `npx playwright test` 9/9 passed (run twice; the second run after the final layout edit). Two specs now click the rail before typing into the Source form and the lab inputs. The mobile spec asserts that only one page shows at a time and that Back returns to the previous page.
- Visual check: fixture-mode screenshots of all four pages at 1440 px and of the Whiteboard page at 1000 px, plus the regenerated `reports/ui-*.png`.

**Unresolved:** a lab run's chart is drawn on the Whiteboard page, not beside the lab's results table, so a learner switches pages to see it. Earlier unresolved items stand.

**Next dependency-ready step:** unchanged from the 29 October entry: commit the working tree (including the untracked sandbox files) and verify sandbox isolation on Linux CI before any hosted release.

### Follow-up (31 October): tutor beside the source; faster, direct, detailed live answers (D-29)

**User report:** answers were slow, abstract, and not to the point; a question asked on the Source page answered on the Whiteboard page.

**Evidence before the change (user's live session, `forecasting-06-00024-v2.pdf` pp. 1-4, "what is high frequency data", then the wrong answer "daily closes"):** turns took 33-50 s. The first turn made 6 sequential tool calls (web_search, get_source_excerpt, read_web_page, 2 x run_python_experiment, present_lesson). The second turn's narration was titles only (`Your gap: daily vs minute:` ...); the server logged `Lesson step without prose (keys=[..., 'say', ...])`, so `say` was present but not a non-empty string. The third turn was telegraphic ("Daily keeps 1 point per day."). The first-turn context said "introduce the passage's central idea" and never asked the tutor to answer the learner's question; the prompt capped steps at "1-3 plain sentences (under 60 words)".

**Behaviour changed:**

- Frontend: one tutor panel (`TaskCard`) rendered beside both Source and Whiteboard (`.workspace-pages.with-tutor`); starting a lesson no longer navigates. A `TutorWorking` status with elapsed seconds shows during lesson start and learner events. The learning loop moved to Progress. A "See this step drawn on the whiteboard" link appears under the tutor on Source.
- `agent_orchestrator.py`: "Answer first" rules (step 1 answers the question; concrete names, numbers, definitions, a worked example; no filler); 3-5 steps of 2-5 sentences (50-120 words); the first-turn context quotes the learner's question and asks for a direct answer; a learner message must be answered in step 1; web research optional on every turn; `get_source_excerpt` offered only when `passage_fits()` is false; feedback turns (answer or hint) with a succeeded run get no experiment tools; `run_digest()` adds each recent run's summary/metrics to the context; `assess_answer` asked to share a reply with `present_lesson`; `LIVE_TURN_SECONDS` 150 -> 60.
- `lesson_builder.py`: `step_prose()` recovers prose sent as a list or object; a step with no prose falls back to its concept/note labels as bullets (never quotes); body cap 900 -> 1500 characters; the warning now logs the text keys' types.

**Checks:**

- `pytest backend/tests -m "not live_meta"`: 123 passed, 2 deselected (new: `test_step_prose_survives_lists_objects_and_title_only_steps`, `test_source_excerpt_tool_is_offered_only_when_the_passage_was_cut`; extended: first-turn context and tool list, feedback-turn tools and measured run digest). `pytest -m live_meta`: 2 passed. `ruff check backend/`: passed.
- `npm --prefix frontend run build`, `oxlint`: passed. `npx playwright test`: 9/9 passed; the upload spec now asserts that asking from Source keeps Source visible with the tutor beside it.
- Live replays of the user's lesson as a throwaway guest (single observations each, data deleted afterwards):
  1. After prompt/tool changes: turn 1 36.1 s (run_python_experiment x2 -> present_lesson), turn 2 32.4 s; steps 46-90 words, step 1 answered directly.
  2. After the feedback-turn change: turn 1 27.8 s, turn 2 17.3 s (present_lesson only). Turn 2 invented run details ("20-minute dip of $1.50"; the run had a 10-minute 2% jump) because the context carried run ids only.
  3. After adding `run_digest`: turn 1 23.4 s, turn 2 45.8 s. Turn 2 quoted the run's real values (0.0279 vs 0.0106). It was slow because the check was free text: `assess_answer` (~22 s) and `present_lesson` (~23 s) came as separate replies. The same-reply instruction was added after this replay and **has not been observed live**.

**Unresolved:** live latency is still dominated by model generation (the final `present_lesson` reply takes 12-23 s); streaming the lesson or running turns as background jobs with progressive display would be the next step. The tutor sometimes repeats the same check after a wrong answer instead of a new variant. Turn times above are single observations, not percentiles.

**Next dependency-ready step:** observe a live written-answer turn to confirm `assess_answer` and `present_lesson` arrive in one reply; then commit the working tree and verify sandbox isolation on Linux CI before any hosted release.
