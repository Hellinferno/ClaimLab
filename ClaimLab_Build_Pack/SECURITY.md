# ClaimLab — Security Scope

**Status:** Design guidance for a product to be implemented. No security audit or production certification is claimed.

## Properties that must hold

- A guest can access only resources belonging to its server-side owner identity.
- Uploaded PDFs and model output cannot grant additional execution privileges.
- The browser never receives provider credentials or direct worker control.
- The first release executes reviewed numerical recipes only, with enforced limits.
- A cancelled, expired, or deleted session cannot be resurrected by a late job.
- Public source and demonstrations exclude secrets and private student data.

The detailed design and verification cases are in [security and privacy](docs/13_SECURITY_AND_PRIVACY.md) and [the test strategy](docs/14_TEST_STRATEGY.md).

## Reporting an issue

Before public release, Ravi must publish an actual private reporting contact or enable the repository host's private vulnerability reporting if available. No contact address or reporting URL has been established in this pack. Until then, report concerns privately to the project owner through the existing project communication channel; avoid publishing credentials or private student data.

## Review scope

Review API ownership, file handling, model/tool boundaries, worker isolation, budget enforcement, data deletion, and deployment secrets. Numerical and instructional correctness belong in the evaluation plan as well. This file does not authorize offensive testing against third-party services.
