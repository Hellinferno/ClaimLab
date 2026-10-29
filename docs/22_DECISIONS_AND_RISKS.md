# Decisions and Risks

## Selected implementation defaults

These are practical defaults for the requested build pack, not claims that code already implements them. Change a decision when evidence warrants it, and update the dependent contracts.

| ID | Decision | Reason and consequence |
| --- | --- | --- |
| D-01 | One combined whiteboard/lab/observation product | Preserves Ravi's agreed vision |
| D-02 | Attention-related AI/ML methods first | A coherent domain with small checkable experiments |
| D-03 | Three reviewed recipes; no arbitrary generated code | Makes execution dependable within the build window |
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
| Incomplete owner erasure | Expired guests are not swept; hosted/backup erasure unverified | User-invoked deletion now purges the owner's files and database content (regression-tested 28–29 October). Implement and verify the retention sweeper (T-DATA-02) before claiming full P0-16 completion |

## Decision record format

For a change, retain date, issue, evidence, decision, affected documents/contracts, migration or test implications, and actual owner. Do not silently leave conflicting stack/API definitions in the pack after a decision.

## Decisions currently reserved for later evidence

Whether to add more method families, OCR, speech, model-generated code, account login, cross-course profiling, or horizontal scale. No default promise to add them before submission is made.
