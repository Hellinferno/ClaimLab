# ClaimLab — Claude Code Handoff

Read [AGENTS.md](AGENTS.md) and [the current handoff](docs/25_STATUS_AND_HANDOFF.md). Follow the same PRD and contracts as every other coding tool.

## What to preserve

The tutor is a stateful workflow. Source evidence, learner events, board objects, experiment runs, and teaching decisions are explicit objects. The agent selects supported tools; reviewed code performs calculations. A learning session must be able to pause, investigate a prerequisite, and return to its earlier context.

## First useful assignment

Start with milestone M0 in [the implementation plan](docs/15_IMPLEMENTATION_PLAN.md) if there is no existing implementation. Establish the real Meta connectivity probe, canonical schemas, and a thin local application slice. Continue milestone by milestone with relevant checks; a polished landing page is not the first milestone.

## Area reading

- Tutor and prompt work: [orchestration](docs/08_AGENT_ORCHESTRATION.md), [observation](docs/11_LEARNING_OBSERVATION.md), [prompts](docs/26_PROMPTS_AND_AGENT_CONTRACTS.md).
- Backend contracts: [data](docs/06_DATA_MODEL.md), [API](docs/07_API_CONTRACTS.md), [experiments](docs/10_EXPERIMENT_ENGINE.md).
- Interface work: [UX](docs/03_USER_JOURNEYS_AND_UX.md), [whiteboard](docs/09_WHITEBOARD_SPEC.md).

## Expected handoff after work

Describe actual behavior changed, affected requirements, relevant test commands/results, unresolved issues, and the next dependency-ready step. Update the central status document. Preserve failed-check evidence rather than replacing it with a narrative of success.

This document is project guidance. It does not assert a particular Claude Code version, command syntax, or integration capability. Use the installed tool's actual supported workflow.
