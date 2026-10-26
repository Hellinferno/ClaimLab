# User Journeys and UX

## Workspace

Desktop: a source panel, a central shared whiteboard, and a compact teacher/experiment panel. These are synchronized views of one session. At narrow widths, use accessible tabs for Source, Board, Lab, and History; keep active concept and run status visible. Target 360–1440 CSS pixels, with core reading usable at 320 pixels.

The first screen explains the supported topic and accepts a PDF. Avoid a large dashboard of empty metrics. Show a seeded author-created example as an alternative to upload, with its provenance.

## Journey A — First lesson

1. Create a guest identity and explain that its history is tied to this browser.
2. Upload a native-text PDF; show filename, processing state, readable pages, and limits.
3. Select a page range and ask a focused question.
4. Show the proposed supported topic and a brief prerequisite check.
5. Begin a stepwise board explanation with source links.
6. Let the student answer a connection task or submit a prediction.
7. Run a supported experiment and reveal actual results.
8. Offer a changed explanation when evidence supports it, then a new application.
9. Summarize covered concepts and evidence without an unsupported mastery score.

## Journey B — Interrupt and revisit

Selecting a board object opens a labelled focus state. “Explain this” submits an event referencing its stable object ID and the current revision. The current sequence pauses. The teacher can add a prerequisite panel while preserving the earlier board, then return to it. A stale selection receives a clear refresh action.

## Journey C — Change an experiment

Inputs edit a local draft. Changing a draft marks the displayed old result “Earlier inputs.” Clicking Run or asking the tutor to run commits validated parameters and queues a job. Disable duplicate submission while showing progress and cancellation. A completed result lists the active parameters, assumptions, checks, and run ID in an expandable evidence view.

## Journey D — Student mistake

The feedback identifies an observable issue, offers a tentative interpretation, and asks a diagnostic question when necessary. It avoids statements about intelligence or fixed learning style. The next board step or experiment must reflect that issue. A follow-up example differs from the answered one.

## Journey E — Resume or delete

Reload restores committed state for the same owner. Explain that clearing the guest cookie loses access to that history; account recovery is outside scope. “Delete my data” removes the owner's content and invalidates work in progress. It is an ordinary product action with a clear consequence, not a hidden administrative process.

## Interaction design

- Use labelled controls, readable equations, direct chart labels, and keyboard alternatives for connect/move tasks.
- Store annotations but do not pretend to understand unrestricted handwriting.
- Keep general narration available as text. Optional speech must not be the sole way to understand a lesson.
- Respect reduced motion; reveal the same sequence instantly when animation is disabled.
- Do not use color alone to distinguish current/stale, correct/incorrect, or source/assumption.
- Show a concise progress message at model/tool boundaries. Do not expose raw private reasoning.
- Never show a successful numerical plot while its run is queued or failed.

## Required UI states

Empty, uploading, parsing, partially readable, unsupported material, lesson ready, tutor working, awaiting student input, experiment running, result ready, stale result, uncertain assessment, provider unavailable, job failed, cancelled, expired, and deleted. Each has an understandable next action or an explanation that the session has ended.

## Copy examples

Supported boundary: “This version can investigate softmax, attention scaling, and causal masking. Select a relevant passage or try the example note.”

Evidence-based feedback: “Your connections use the keys as the output values. Let's compare what keys and values contribute.”

Failure: “The experiment did not finish. Your lesson is saved; no result was produced.”

Source qualification: “This is an illustrative experiment using synthetic inputs. It does not reproduce the paper's benchmark.”
