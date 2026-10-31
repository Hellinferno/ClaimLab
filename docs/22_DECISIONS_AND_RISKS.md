# Decisions and Risks

## Selected implementation defaults

These are practical defaults for the requested build pack, not claims that code already implements them. Change a decision when evidence warrants it, and update the dependent contracts.

| ID | Decision | Reason and consequence |
| --- | --- | --- |
| D-01 | One combined whiteboard/lab/observation product | Preserves Ravi's agreed vision |
| D-02 | Attention-related AI/ML methods first | A coherent domain with small checkable experiments |
| D-03 | Three reviewed recipes; no arbitrary generated code | Makes execution dependable within the build window. **Superseded 29 October by D-23** for papers the recipes do not cover; the recipes remain the reviewed path for the attention lab |
| D-04 | React/TypeScript and FastAPI/Python | Fits interactive UI plus numerical services |
| D-05 | Structured SVG board and data-backed charts | Stable object identity and precise representations |
| D-06 | One API instance, one durable worker, SQLite WAL | Reduces infrastructure while preserving explicit jobs |
| D-07 | Separate restricted parser/numerical profiles | Bounds file parsing and numerical execution |
| D-08 | Real Meta adapter with visible fixture mode | Keeps development productive and live claims honest |
| D-09 | Guest owner, browser-bound history, 24-hour retention | Small authentication scope with actual isolation |
| D-10 | Categorical evidence states and explicit uncertainty | Avoids an uncalibrated mastery score |
| D-11 | Selected source range and native-text PDFs | Keeps source interpretation bounded |
| D-12 | No voice/OCR/full-paper reproduction in P0 | Protects time for the complete essential loop |
| D-13 | Explicit example start, actual PDF page selection, stable browser owner | 28 October: avoids hidden model work, fabricated fallback content, and lost history on reload; stacked mobile sections use accessible bottom navigation |
| D-14 | Load KaTeX only when mathematics is displayed | 28 October: measured initial JavaScript reduction of about 49%; safe rendering and escaped loading fallbacks remain |
| D-15 | Retain execution metadata in a versioned checks envelope | 28 October: avoids a database migration while preserving assumptions, runtime identity, canonical inputs, and older check-only records; unknown old metadata is labelled unrecorded |
| D-16 | Live provider errors remain live failures | 28 October: silent fixture substitution was removed; failed jobs release the matching session lock and return a recoverable 503 |
| D-17 | Two independently completed variants for independent evidence | 28 October: helped variants previously counted despite server-provided hints/incorrect-answer feedback. Preserve assistance by task/variant and exclude assisted attempts from the independent threshold; a fresh variant remains eligible |
| D-18 | Identical uploads are one document; failed first turns leave no lesson | 29 October: a reused guest owner made quotas last the whole 24 h, so repeat example starts or provider outages could lock a learner out. Same-SHA-256 uploads return the existing document; a session whose initial turn fails is removed |
| D-19 | Grade live answers after the provider turn succeeds | 29 October: grading before the provider call left committed attempts behind on failure, so the retry was graded twice and downgraded to helped |
| D-20 | Leased API tutor jobs | 29 October: an orphaned RUNNING job locked the lesson until guest expiry. API turns now carry a 180 s lease that the busy checks and worker sweep honour |
| D-22 | Declared note schema for live board commands | 29 October: live browser review showed muse-spark-1.3 inventing board-command shapes, and the old normalizer built an invalid `concept_card` object, so every model board change was dropped. `present_teaching_step` now declares `{action: "add_text", label, text}` notes; the server lays them out as validated text objects below the reviewed diagram. `max_tokens` raised 1500 → 4096 because reasoning tokens truncated a first turn to an empty reply. Recipe aliases are mapped and removed before strict validation (`temperature` becomes a 1/T multiplier). The seeded scaling plot is always bound to a scaling run |
| D-23 | Tutor-written experiments run in an isolated sandbox | 29 October, user decision: experiments must follow each paper's own mechanism, which three attention recipes cannot. The live tutor may write a small numpy experiment (`run_python_experiment`). Code passes an AST allowlist (numpy only through `numpy.random`, `numpy.linalg`, `numpy.fft`, `numpy.polynomial`, and pure stdlib maths; no `_` names, file, eval, getattr, or `with`; 30 October: a security review showed `numpy.ma.mrecords.openfile` could open any path, so numpy subpackages are now allowed by name instead of blocked by name), then runs in a separate interpreter from a dedicated `.sandbox-venv` (numpy only) with a scrubbed environment (no API keys), a temp working directory, restricted builtins and a guarded import, a 10 s timeout, and on Windows a Job Object (memory cap, one process, kill on close). Results are labelled tutor-written and unreviewed; code, inputs, and checks are shown to the learner. Learners re-run with declared numeric knobs only; code never comes from the client. No OS-level network block exists; `socket` is simply unimportable |
| D-24 | Open lessons for any readable paper in live mode | 29 October: a pairs-trading paper passed the old keyword gate ("attention", "key") and was taught with the attention diagram. Topic assessment now counts distinct attention-mechanism terms (two or more → reviewed attention lab); other readable text is an `open` lesson in live mode and still `unsupported` in fixture mode. The attention diagram seeds only an attention lab the tutor did not draw |
| D-25 | Paged lessons drawn by the tutor; the server lays out the board | 29 October: the tutor note was one long block with raw Markdown and the board ignored the paper. `present_lesson` sends 2–5 short steps, each with a tag and 1–3 board items (concept, equation, quote, note, plot). The server places items in a flow layout, links `from` arrows, drops quotes that are not verbatim in their anchor and plots without a retained run, and records which step drew what. The UI pages through steps and reveals each step's drawing in turn; Markdown renders as React elements (no HTML injection). Earlier single-note `present_teaching_step` replies are still honoured |
| D-26 | TinyFish web research behind a key | 29 October: `web_search` and `read_web_page` are offered only when `TINYFISH_API_KEY` is set (max 4 calls per turn, page text capped at 6000 characters, labelled untrusted data). A `web` step may cite only a URL that research returned this turn; otherwise it is re-tagged background |
| D-27 | Tutor-written checks keep a private answer key | 29 October: open lessons have no task bank. The tutor's check is stored with a server-only key (a separate `task_key_recorded` job event, excluded from the job stream and session state). Number and choice answers are graded deterministically (`checked`); written answers are judged by the tutor's `assess_answer` and stay `provisional`. Both use the D-17 two-variant policy; a missed check stays open until the tutor sets a new one |
| D-28 | Workspace split into four pages | 31 October, user request: everything sat on one long page and the rail only scrolled. The rail now switches pages (Source, Whiteboard, Experiment, Progress) via the URL hash. Pages are hidden rather than unmounted so in-progress answers, lab drafts, and board selection persist. The tutor panel sits beside both Source and Whiteboard (revised the same day: asking from Source had jumped the learner to the Whiteboard). Trade-off: a lab run's chart appears on the Whiteboard page, not beside the lab's table |
| D-29 | Live tutor answers first, in detail, with fewer round trips | 31 October, user report: answers were slow, abstract, and not to the point. Causes found: the first turn was told to "introduce the central idea" instead of answering the learner's question; steps were capped at "1-3 sentences, under 60 words"; step prose sent in a non-string shape was dropped (title-only pages); every turn re-read a passage already in context; the first turn had to do web research. Now: step 1 answers the question; steps are 2-5 concrete sentences (50-120 words); list/object prose is recovered (else the step's concept/note labels); `get_source_excerpt` is offered only when the passage was cut for length; web research is optional; answer/hint feedback turns get no experiment tools when a run exists, and the context carries each run's measured summary/metrics so the tutor quotes real numbers; `assess_answer` is asked to share a reply with `present_lesson`; the soft turn deadline fell from 150 s to 60 s. Trade-off: longer lessons take more output tokens per final call |
| D-21 | Erase uploads by document identity, not stored path | 29 October: a stored key outside the current document root (DATA_DIR changed) blocked deletion forever. The canonical `<root>/<id>.pdf` is removed; an older-location file is removed only when its name and SHA-256 match; unrelated files are never touched |

## Unverified external facts

Ravi's acceptance/track status, provider account access, credits, billing configuration, deployment host capability, actual team size, exact package locks, and current participant-only rule updates require real verification. They are not invitations to pause all independent work; record blockers and continue work that does not depend on them.

## Risk register

| Risk | Trigger or evidence | Response |
| --- | --- | --- |
| Entry resembles discouraged education chatbot | Demo only summarizes or lectures | Demonstrate actual experiments, interactions, and adaptation; confirm organizer interpretation |
| Model access unavailable | Authentication/model probe fails | Diagnose actual account compatibility; use labelled fixtures for independent UI work; retain live-release blocker |
| Runner host incompatible | Isolation profile cannot run | Choose a compatible dedicated host or document a reviewed alternative; no unrestricted fallback |
| Scope exceeds available time | Complete loop absent by 1 November | Cut later scope and polish; reassess P0 honestly |
| Formula/source extraction wrong | Quote or equation cannot be validated | Narrow selection, mark uncertainty, or use supported author-created example |
| Agent assessment unreliable | Free-text rubric disagreements | Prefer structured tasks and clarification; retain provisional status |
| Statistics overinterpreted | One sample described as a universal law | Show seeds/assumptions and separate deterministic checks from observed trends |
| State inconsistency | Old plot shown with new inputs | Immutable run IDs, revisions, stale labels, integration tests |
| Unexpected spend | Usage exceeds reservation or credits absent | Enforce request/budget caps, reconcile uncertain usage, verify current rates |
| Data exposure | Cross-owner route or public private-data artifact | Fix ownership; remove exposure; rotate affected credentials if needed; reverify before release |
| Late submission | Core work continues into deadline margin | Freeze features and target buffered submission |
| Unproven learning claim | Pitch reports improvement without a study | Report actual evidence and its limits; say unmeasured when appropriate |
| Sandbox escape by generated code | Model-written code (possibly steered by injected PDF or web text) reaches files, network, secrets, or the host. Chain to watch: a file read inside the sandbox, returned to the tutor, then sent out in a web_search query | The in-process policy is defence in depth, not the boundary: it is a denylist over an allowlisted surface, and one escape was found and closed on 30 October. Never pass secrets to the child; keep the allowlist minimal. Before any hosted or shared deployment, run the child in real OS isolation (container or nsjail/gVisor with no network, read-only root holding only the numpy venv, no app or DATA_DIR mount, separate unprivileged UID, seccomp). Locally on Windows the child still runs as the user and can read what the user can read if the policy is bypassed |
| Prompt injection through sources | PDF or web text instructs the tutor | Source and web text are labelled data, never instructions; quotes are verified verbatim; URLs must come from research results; tools have bounded effects |
| Incomplete owner erasure | Expired guests are not swept; hosted/backup erasure unverified | User-invoked deletion now purges the owner's files and database content (regression-tested 28–29 October). Implement and verify the retention sweeper (T-DATA-02) before claiming full P0-16 completion |

## Decision record format

For a change, retain date, issue, evidence, decision, affected documents/contracts, migration or test implications, and actual owner. Do not silently leave conflicting stack/API definitions in the pack after a decision.

## Decisions currently reserved for later evidence

Whether to add more method families, OCR, speech, account login, cross-course profiling, or horizontal scale. (Model-generated code was decided on 29 October: D-23.) No default promise to add them before submission is made.
