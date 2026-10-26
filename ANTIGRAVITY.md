# ClaimLab — Antigravity Handoff

Read [AGENTS.md](AGENTS.md), [user journeys](docs/03_USER_JOURNEYS_AND_UX.md), [whiteboard behavior](docs/09_WHITEBOARD_SPEC.md), and [current status](docs/25_STATUS_AND_HANDOFF.md). Supply this document manually if the tool does not automatically load project guidance.

## What to preserve

The student experiences one workspace: source, teacher, board, experiment, and learning record. All panels reference the same active session and run. The interface must communicate readiness, uncertainty, failure, and stale results without exposing unnecessary implementation details.

## First useful assignment

Implement or continue the next incomplete milestone. Start with a functional learning workspace and real contracts. Use fixture mode for local interface development only when clearly labelled and backed by the same schemas.

## Consequential interactions

The student can select a source passage, inspect a board object, submit a prediction or relationship, run a supported experiment, change an input, and see a subsequent lesson change. Keyboard alternatives should exist for diagram tasks. Reduced-motion mode should preserve the content and sequence.

## Validation

If browser-testing capabilities are available in the actual environment, verify the complete journey and failure states at desktop and narrow widths. If unavailable, report that limitation and run the checks that are available. This file does not assume any specific browser or deployment capability.

Keep visual assertions connected to real data. A chart shown during a live run must use that run's output, and a success indicator must reflect the backend state. Update the shared handoff with actual evidence.
