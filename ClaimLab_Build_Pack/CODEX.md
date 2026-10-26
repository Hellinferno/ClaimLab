# ClaimLab — Codex Handoff

Read [AGENTS.md](AGENTS.md), [the acceptance specification](docs/02_SCOPE_AND_ACCEPTANCE.md), and [current status](docs/25_STATUS_AND_HANDOFF.md). This file may need to be supplied explicitly; AGENTS.md is the shared project entry point.

## What to preserve

Make important claims traceable to actual actions. A numerical result needs a run record and checks; a source reference needs a verified anchor; a teaching change needs learner evidence. Treat the frontend/backend boundary and state transitions as contracts.

## First useful assignment

Inspect the repository and implement the next incomplete milestone. If starting from this documentation pack, begin M0. Avoid replacing the selected stack or expanding the scope before a complete supported learning loop works.

## Particularly important verification

- Controlled experiment inputs produce independently checked numerical outputs.
- Owner A cannot read or mutate owner B's documents, runs, jobs, or sessions.
- Repeated requests and tool calls do not duplicate runs or evidence.
- Changing parameters invalidates the old result's current status.
- A failed or cancelled job cannot later commit a successful result.
- Student evidence changes a subsequent teaching action in an end-to-end test.

Use [the test strategy](docs/14_TEST_STRATEGY.md) and report what actually ran. A schema check does not establish live provider compatibility; keep those results distinct.

## Handoff

Update status with implemented behavior, tests, actual model mode, and release limits. Include file references and concise reasons for material decisions. Do not invent PRs, hosted URLs, provider credits, or test outcomes.
