# Test Strategy and Traceability

## Approach

Test consequential behavior at the lowest useful level, then verify the complete journey. Keep deterministic numerical checks independent from the production implementation. Fixtures make offline work reproducible; live Meta tests establish provider compatibility separately.

Tests described here are required implementation work, not already executed tests.

## Test catalog

| IDs | Layer | What must be verified |
| --- | --- | --- |
| T-AUTH-01 | API | Guest creation, hashed credential storage, CSRF, expiry, cookie attributes |
| T-AUTH-02 | API/e2e | Owner A cannot read/mutate B's documents, files, selections, sessions, runs, jobs, streams |
| T-PDF-01 | Integration | Native-text PDF yields ordered page text and stable normalized anchors |
| T-PDF-02 | Integration | Oversize/page-count/owner-quota rejection |
| T-PDF-03 | Integration | Malformed or encrypted PDF has bounded failure |
| T-PDF-04 | Integration | Scanned-only input is marked unreadable without invented extraction |
| T-PDF-05 | Worker | Resource-heavy parsing terminates under limits and cleans temporary artifacts |
| T-SRC-01 | Unit/integration | Quote offsets and hash match the selected document/page |
| T-SRC-02 | API | Unknown/cross-owner/out-of-range anchor rejected |
| T-TUTOR-01 | Offline + live | Supported topic selected; unsupported source receives an honest boundary |
| T-BOARD-01 | Unit/UI | Atomic command validation, IDs, limits, connector integrity, safe LaTeX/text |
| T-STATE-01 | API | Revision conflict and concurrent job conflict do not overwrite state |
| T-STATE-02 | e2e | Reload restores the correct owner/session board, tasks, runs, and evidence |
| T-NUM-01 | Unit | Softmax reference cases, translation invariance, equal logits, normalization |
| T-NUM-02 | Unit | Scaling shape/reference relation, reproducible seed, normalized distributions |
| T-NUM-03 | Unit | Mask zeros, row sums, exact 3×3 zero-score example |
| T-NUM-04 | Worker | Invalid/non-finite/excessive parameters rejected; output/schema limits enforced |
| T-RUN-01 | API/UI | Exact run IDs/parameters drive charts; input drafts mark old results stale |
| T-RUN-02 | Integration | Failed checks, timeout, or cancellation cannot appear as successful numerical output |
| T-LEARN-01 | e2e | Prediction retained before reveal; new application differs from exposed example |
| T-LEARN-02 | Offline | Different evidence selects relevant different next action and retains uncertainty |
| T-EVID-01 | UI | Source/background/assumption/observation/interpretation labels and check details are inspectable |
| T-JOB-01 | Integration | Provider timeout preserves state and produces a truthful bounded error |
| T-JOB-02 | Integration | Invalid tool output has no side effect; correction remains within limits |
| T-JOB-03 | Integration | Worker restart/lease expiry fails jobs without automatic duplicate side effects |
| T-JOB-04 | Integration | Cancel/delete fencing prevents late commits; SSE disconnect does not cancel |
| T-SEC-01 | Integration | Uploaded/source injection cannot grant unsupported tools or reveal secrets |
| T-SEC-02 | Runner | No network, no secrets, non-root, resource limits, no host mounts/runtime socket |
| T-SEC-03 | API | Origin/CSRF/rate-limit/budget enforcement on state-changing routes |
| T-SEC-04 | UI/build | XSS strings escape; unsafe LaTeX/markup rejected; no keys in built assets/logs |
| T-META-01 | Live | Real account accepts configured model, tool loop, output shape, and request parameters |
| T-META-02 | Live/e2e | Real model uses evidence to change a supported learning step; no fixture substitution |
| T-DATA-01 | Integration | Owner deletion invalidates work, removes content, and prevents recreation |
| T-DATA-02 | Integration | Expiry rejects access before sweeper; sweeper deletes all child artifacts |
| T-UX-01 | Browser | Keyboard connection answer, responsive layout, focus, reduced motion, clear failure states |
| T-IDEM-01 | Integration | Same key/input returns original job/run; changed input conflicts; tool call dedup works |

## Independent numerical oracles

Use hand-calculated small cases and a separately written scalar/reference implementation. A test that calls the production function twice is not an independent check. Avoid asserting noisy statistical monotonicity for all seeds. Compare within documented float64 tolerances.

## Test modes and commands

The implementation should provide `pytest`, frontend `npm run test`, `npm run typecheck`, `npm run lint`, and `npm run build`, plus a Playwright end-to-end command. Put paid/live provider tests behind an explicit opt-in marker such as `live_meta`; exclude them from ordinary offline CI.

These command interfaces are to be created in code. Their existence and success must be confirmed before calling them available. Local sandbox/container tests require the selected runtime and should fail clearly when it is missing rather than silently downgrade isolation.

## End-to-end release scenarios

Run the complete supported journey in live mode, a different supported source/parameter variant, unsupported input, a deliberate numerical/model failure, reload, second-owner access denial, and cancellation/deletion during work. Verify both state and visible UI behavior.

## Evidence recording

Record date, commit, environment, test command, result, failures, model mode, and relevant sanitized run IDs. Keep performance measurements separate from targets. If a live test cannot run because access is missing, report it as unverified, not passed.

## CI boundary

Run deterministic checks, schema generation drift checks, and the meaningful offline integration suite. Do not repeatedly call paid services on every commit. Broaden testing after new changes, failures, or unresolved concerns; avoid redundant reruns solely to inflate the checklist.
