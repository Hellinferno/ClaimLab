# ClaimLab — Project Rules

These rules govern the planned product. Competition rules are separately documented in [the hackathon guide](docs/19_HACKATHON_RULES.md).

## Product rules

1. Every session has one selected source range and a focused learning goal.
2. Teaching actions must connect to that goal, an identified prerequisite, or observed student work.
3. The shared board and experiment represent the same active concept and inputs.
4. A student can interrupt, ask for another explanation, and submit an interaction that changes the next step.
5. Adaptation refers to observable evidence. Preferences, elapsed time, and a single mistake are not permanent ability labels.
6. A result is displayed as measured only after actual execution and validation. A stale run remains labelled stale.
7. Distinguish source statements, added background, experiment assumptions, measured observations, and interpretations.
8. Describe synthetic experiments as illustrations. Do not claim full paper reproduction or improved learning without appropriate evidence.

## Engineering rules

- Keep the first release within the exact supported recipes and limits in the technical and experiment specifications.
- Validate model arguments and outputs before side effects. Tool availability never grants authority outside the current owner/session.
- A single durable worker claims jobs; one mutation job per learning session. Every state-changing request uses an expected revision and idempotency key where specified.
- Treat document text, learner messages, file metadata, and model output as untrusted data.
- No secrets in frontend assets, logs, prompts to an experiment container, or public examples.
- No arbitrary uploaded code execution. A subprocess by itself is not a sandbox.
- Log evidence and identifiers with bounded payloads; avoid raw documents and student answers in general operational logs.
- Deletions invalidate queued jobs and prevent late outputs from recreating data.
- Reserve model budget before a call; bound output tokens, retries, calls, and experiment resources.
- Update contracts and their tests together. Avoid independently maintained duplicate schemas.

## Honest operation

Development fixtures are allowed for offline tests and UI work. The application must visibly show fixture mode, and the competition demonstration must identify any recorded or cached segment. A live failure stays a failure until corrected and rerun.

Keep a record of newly built work and third-party sources. Do not call the app production-ready because a happy path passed once. Use the release criteria and document remaining limits.

## Change control

Clarify a genuine unresolved product conflict with Ravi when it would materially change the agreed vision. Resolve routine implementation details autonomously and record meaningful decisions. Ask for new external actions only when they exceed existing authorization; do not invent additional approval gates for ordinary code edits or tests.
