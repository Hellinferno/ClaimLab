# ClaimLab workspace verification — 28 October 2026

Local working tree on `main`, based on `5aead92`. This report records implementation and offline verification; it does not establish deployment or current live Meta compatibility.

The concept in `docs/00_IDEA_VISION.md` was read before implementation. The source-grounded whiteboard, three executable attention labs, and evidence-based teaching loop were preserved. Work addresses the UI/accessibility and regression portions of M5.

## Result

- Rebuilt the workspace around a paper-and-green source reader, central teaching board, numerical lab, and learning trail, with responsive navigation and visible keyboard focus.
- Example lessons require an explicit action. Custom PDFs use actual pages and an editable question/range. Unsupported and unreadable sources produce an honest boundary, with no fabricated fallback source.
- Reload restores the same guest, selected source, narration, board, active task, evidence, and retained run. React development bootstrap is deduplicated, and task drafts/board caches reset correctly between distinct lessons.
- Numerical plots use checked retained output, matching run IDs, common variance scales, actual dimension spacing, and dynamic matrix/vector sizes. Failed runs retain earlier results and input labels. Exact inputs, assumptions, checks, and execution metadata are inspectable.
- Equations fit their measured width after fonts load. Full descriptions are available through keyboard board inspection. Fit/Readable size controls contain scrolling inside the board; resize observation produces no browser runtime errors in the tested flows.
- Feedback comes from retained server teaching rather than a hardcoded answer. Failed tutor requests keep the question draft. Live provider failures return 503 without silently switching to fixtures.
- The server records delivered assistance against the current task/variant. Help and previous incorrect attempts prevent corrected answers from counting as independent; two fresh unassisted variants still qualify. Historical pre-fix evidence is not retroactively relabelled.
- PDF parsing now runs in the request thread pool, with a bounded file read and no orphan file for malformed input. Idempotent retries, changed-answer conflicts, stale tasks, and actual run/job metadata have regression coverage.

## Verification

Environment: Windows, PowerShell, Python 3.12 virtual environment, Node 24, React/TypeScript/Vite, installed Google Chrome. Browser tests use an isolated SQLite database and upload directory under ignored `data/e2e/`, fixture teaching, empty provider key, and the reviewed local numerical runner. No live provider calls or changes to the existing application database were made.

| Check | Result |
| --- | --- |
| Backend `pytest backend/tests -m "not live_meta" -q` | 52 passed, 2 live tests deselected |
| Backend `ruff check backend` | Passed |
| `npm --prefix frontend run build` | Passed |
| `npm --prefix frontend run lint` | Passed |
| `npm --prefix frontend run test:e2e:headed` | 9/9 Chrome flows passed; final run about 1.1 minutes |
| Unexpected browser runtime/window/promise/React console errors | None in final suite; expected HTTP-negative-case resource messages excluded |
| `git diff --check` | Passed using repository line-ending settings |

The nine browser flows cover:

1. Honest empty state, deferred math loading, source/board/run/guest restoration, equation bounds, keyboard inspection, and board sizing.
2. Wrong/correct keyboard answers, consequential feedback, and a new retained application variant.
3. One-page heldout input, real page controls, unsupported material, and preservation of the earlier lesson.
4. Failed question draft recovery, ungraded questions, task-specific hint recording, and prevention of independent-credit inflation.
5. Strict parameter parsing, failed-run stale state, all three real numerical recipes, chart coordinates, nonuniform dimensions, and single-dimension plots.
6. Malformed PDF failure without replacing the current source/lesson.
7. API-down recovery without invented source content.
8. Second-owner denial and guest-access revocation (not complete database erasure).
9. 390×844 mobile layout, reduced motion, section navigation, readable board mode, and absence of document-wide horizontal overflow.

The backend suite includes independent numerical checks, the existing 12-case fixture benchmark, and 27 new workspace/assistance regression cases. CASE-12's wording now reflects its actual guest-revocation assertion; it does not establish complete erasure.

## Measured optimization

The initial production JavaScript changed from 529.57 kB to 272.51 kB in Vite output: about 49% smaller. Reported gzip changed from 160.38 kB to 84.03 kB. KaTeX is a deferred 260.69 kB chunk; the browser verifies that it is not requested on the empty welcome screen and does load when mathematics appears. This is a bundle measurement, not a claim of a 49% reduction in total page-load latency.

`ui-browser-metrics.json` retains one local headed-browser sample: welcome interactive 1,952 ms, example-to-task 3,166 ms, reload-to-restored-task 1,308 ms. These are single fixture observations, not percentiles, live-model timings, or a capacity benchmark.

## Artifacts and preview

- `reports/ui-welcome.png`
- `reports/ui-workspace-desktop.png` (1440×960 viewport)
- `reports/ui-workspace-mobile.png`
- `reports/ui-browser-metrics.json`
- Reusable tests: `frontend/e2e/workspace.spec.ts`, `backend/tests/test_workspace_regressions.py`
- Reopen a disposable visible preview with `npm --prefix frontend run preview:fixture`.

Chrome was left open on the example lesson at `http://127.0.0.1:5174`, using an isolated API on 8081. Closing its window stops those preview servers. The pre-existing Vite proxy default of API port 8080 was preserved, with `VITE_API_TARGET` added for tests and alternate local servers.

## Remaining limits

> **Update, 29 October 2026:** the owner purge was applied after this report was written. Deletion now erases the owner's database content as well as PDFs; it is regression-tested, and the browser deletion flow passed again. The live Meta tests (T-META-01/02) were rerun and passed. The two limit entries below are kept as written on 28 October. See `docs/25_STATUS_AND_HANDOFF.md` for current state.

- Complete database erasure is not implemented: the existing delete action removes PDF files and revokes access but retains extracted text and learning records. The session menu and confirmation disclose this. Automatic approval review rejected the broader owner-purge code change; `reports/proposed-owner-data-purge.patch` remains unapplied, with user approval requested.
- Live Meta tests were not run. Provider failure and assistance logic were checked using fixtures/mocked live responses; historical live-access claims were not revalidated.
- Tutor/recipe API routes still execute synchronously before returning 202. Restricted Docker execution, full worker/cancellation fencing, enforced cleanup, and deployment require separate M5 verification.
- Fixture teaching remains bounded and explicitly labelled. It is not a live answer to arbitrary questions, and no learning-gain or mastery claim was established.
- No commit, push, production deployment, or submission was performed.
