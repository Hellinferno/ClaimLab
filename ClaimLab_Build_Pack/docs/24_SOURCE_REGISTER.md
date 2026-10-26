# Source Register and Verification Notes

**Prepared:** 27 October 2026 IST. External pages were consulted during documentation preparation. Account access, actual provider behavior, exact package locks, and later rule changes still need empirical verification.

## Source register

| ID | Source | Used for | Status and boundary |
| --- | --- | --- | --- |
| S-01 | Ravi's agreed ClaimLab idea, preserved in [00_IDEA_VISION.md](00_IDEA_VISION.md) | Product vision and stakeholder meaning | Current saved idea read before preparing this pack |
| S-02 | [Supplied participant guide](../references/PARTICIPANT_GUIDE_SUPPLIED.md) | Judging weights, project categories, public repository, video, team and deadline conditions | User-supplied snapshot; later official updates may supersede it |
| S-03 | [Public event page](https://events.cerebralvalley.ai/e/meta-ai-developer-hackathon) | Theme/track descriptions and public submission schedule | Public page retrieved; participant-only details not independently accessed |
| S-04 | [Meta model documentation](https://dev.meta.ai/docs/models) | Candidate model and documented modalities | Documentation retrieved; actual account compatibility untested |
| S-05 | [Meta tool/function cookbook](https://dev.meta.ai/docs/cookbook/tool-function-calling) | Chat Completions tool loop and supported tool-choice behavior | Documentation retrieved; adapter must probe actual parameters |
| S-06 | [Meta structured output](https://dev.meta.ai/docs/cookbook/structured-output) | Schema-constrained response pattern | Previously retrieved in this conversation; verify exact adapter behavior in M0 |
| S-07 | [Meta Responses protocol](https://dev.meta.ai/docs/protocols/responses) | Distinction between Responses and Chat Completions formatting | Consulted to avoid mixing protocol parameters; Responses is not the default adapter |
| S-08 | [Vite guide](https://vite.dev/guide/) | Project scaffolding/runtime prerequisites | Retrieved; resolve and lock tested package versions at bootstrap |
| S-09 | [FastAPI background tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/) | Avoid relying on an in-request/background callback for durable computational jobs | Retrieved; our durable-worker design is a project decision |
| S-10 | [pypdf text extraction](https://pypdf.readthedocs.io/en/stable/user/extract-text.html) | Native-text extraction limits, scanned-page and resource caveats | Retrieved; no claim that all PDF layouts/equations are interpreted reliably |
| S-11 | [Docker run reference](https://docs.docker.com/reference/cli/docker/container/run/) | Isolation configuration vocabulary | Retrieved; actual host enforcement requires verification |
| S-12 | [Docker user namespaces](https://docs.docker.com/engine/security/userns-remap/) | Non-root/user-namespace context | Retrieved; ordinary containers are not a guarantee of absolute isolation |
| S-13 | [Attention Is All You Need](https://arxiv.org/html/1706.03762v7), Section 3.2.1 and decoder discussion | Attention/scaling/masking reference context | Retrieved during the idea-document work; synthetic labs are illustrative, not benchmark reproductions |

## Verified statements versus design choices

Documented public facts include event wording, the supplied rubric/requirements, current model documentation, and framework documentation. The stack, limits, budgets, architecture, test cases, daily schedule, and teaching policy in this pack are proposed engineering choices. They are not source-reported performance findings.

Numerical toy examples are mathematical reference cases designed for this product. Hypothetical learner mistakes and successful follow-ups are scenarios, not observed participants or measured outcomes.

## Required refreshes before release

Check current official event terms and portal fields; actual model availability and pricing; package compatibility and licenses; host execution controls; and any intended contributor/training data mode. Record actual results and dates in the handoff.

Do not add citations to unvisited URLs or present search snippets as a passed integration test. Keep private account information, signed URLs, and credentials out of this register.
