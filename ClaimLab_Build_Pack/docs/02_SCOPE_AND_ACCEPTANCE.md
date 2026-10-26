# Scope and Acceptance Criteria

This is the canonical first-release boundary. Proposed numeric limits are in [the technical specification](04_TECHNICAL_SPEC.md). All criteria below require implementation evidence; none is marked passed by this document.

| Requirement | Acceptance evidence | Relevant tests |
| --- | --- | --- |
| P0-01 | A new browser gets an opaque owner cookie; a second browser has a different owner | T-AUTH-01, T-AUTH-02 |
| P0-02 | Valid native-text PDF yields ordered pages; oversized, encrypted, malformed, and scanned-only input have explicit bounded outcomes | T-PDF-01 through T-PDF-05 |
| P0-03 | Every source citation resolves to the selected document/page; quoted spans match stored normalized text | T-SRC-01, T-SRC-02 |
| P0-04 | A supported question produces a concept path; unrelated material is labelled unsupported | T-TUTOR-01 |
| P0-05 | Agent tools add, connect, highlight, and revise stable board objects; revision conflicts do not overwrite work | T-BOARD-01, T-STATE-01 |
| P0-06 | Student can submit a connection answer and a text explanation using pointer or keyboard | T-UX-01 |
| P0-07 | Softmax, scaling, and masking run under recipe/parameter limits with independently checked expected results | T-NUM-01 through T-NUM-04 |
| P0-08 | Charts use retained run output; input changes mark results stale; failure never becomes a success chart | T-RUN-01, T-RUN-02 |
| P0-09 | Predictions precede result reveal when that task is active; a different follow-up task is retained | T-LEARN-01 |
| P0-10 | An error-pattern fixture and a live supported session select a relevant different teaching action, with evidence IDs | T-LEARN-02, T-META-02 |
| P0-11 | Reload restores source, board, active concept, completed results, and evidence for the same owner | T-STATE-02 |
| P0-12 | Evidence panel distinguishes source/background/assumption/observation/interpretation and exposes run checks | T-EVID-01 |
| P0-13 | Model timeout, malformed output, worker restart, and cancellation have recoverable, truthful UI states | T-JOB-01 through T-JOB-04 |
| P0-14 | Cross-owner access fails; execution has no keys or network; injected material cannot invoke unsupported tools | T-AUTH-02, T-SEC-01 through T-SEC-04 |
| P0-15 | A real Meta call and tool loop succeed; actual model ID, request mode, and redacted usage evidence are recorded | T-META-01, T-META-02 |
| P0-16 | Delete invalidates jobs immediately and removes content; retention sweeper removes expired records/artifacts | T-DATA-01, T-DATA-02 |

## Complete supported journey

An owner uploads a supported native-text PDF, selects up to five pages, and asks a question about attention. The tutor grounds its explanation, draws a diagram, asks for a prediction or relationship, runs a supported experiment, responds to an observed gap, and checks a new application. Reloading preserves the correct state. A second owner cannot access it.

The first journey can use an author-created technical note. A separate differently worded supported input must exercise the same capability without paper-specific cached answers. Unsupported uploads must fail gracefully.

## Required failure behavior

- A parsing problem identifies affected pages and provides a narrower upload/selection option.
- A provider failure preserves completed work and allows bounded explicit retry.
- An invalid board patch changes no objects.
- A failed experiment shows its error and check report, not fabricated output.
- A busy session rejects competing mutations rather than silently reordering them.
- Expired/deleted ownership does not expose content through job or file endpoints.

## Honest scope labels

“Supported experiment” means a reviewed recipe instantiated from validated parameters. The agent still chooses the recipe, explains its assumptions, and adapts the lesson. It does not generate arbitrary executable Python in this release. “Adaptation” means a recorded student event changes a later teaching action. “Evidence of progress” is not a certification of mastery.

## Scope cuts

Cut voice, OCR, broad subject support, elaborate animation, or account login first. Keep semantic student interaction, three numerical recipes, a real provider loop, source evidence, and failure handling. Any proposed reduction of a P0 requirement requires a documented product decision and a truthful change to the release description.
