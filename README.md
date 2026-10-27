# ClaimLab — Build Documentation Pack

**Owner:** Ravi · **Prepared:** 27 October 2026 · **Version:** 1.0 · **Timezone:** Asia/Kolkata (IST)

ClaimLab combines an adaptive whiteboard teacher, small executable experiments, and an observation mechanism that changes the lesson using evidence from the student's work.

This archive contains planning and handoff documents. Application code, a deployed product, provider access, a competition acceptance, and passing implementation tests are **not yet established by this pack**.

## Start here

1. Read [the product requirements](docs/01_PRD.md) and [scope and acceptance criteria](docs/02_SCOPE_AND_ACCEPTANCE.md).
2. Read [project rules](RULES.md), [architecture](docs/05_ARCHITECTURE.md), and [the implementation plan](docs/15_IMPLEMENTATION_PLAN.md).
3. Give your coding assistant [AGENTS.md](AGENTS.md), then the relevant tool handoff file below.
4. Follow [daily tasks](docs/16_DAILY_TASKS.md), updating [status and handoff](docs/25_STATUS_AND_HANDOFF.md) with actual evidence.
5. Use [the definition of done](docs/23_DEFINITION_OF_DONE.md) to assess readiness. A document describing a feature does not establish that it works.

## The implementation decision

Build one responsive web application with a React/TypeScript interface, a Python/FastAPI backend, a durable job worker, and isolated numerical execution. Start with three supported experiment recipes: softmax sensitivity, attention scaling, and causal masking. The model chooses and parameterizes supported actions; reviewed numerical implementations calculate the results.

The first release uses one application instance and one worker. SQLite is suitable for that deployment boundary. A move to multiple instances requires a deliberate database and queue change. Voice, unrestricted generated code, arbitrary research reproduction, and broad textbook coverage are later scope.

## Quickstart & Local Execution

### Prerequisites
- Python 3.12+
- Node.js 20+ & npm

### 1. Backend Setup
```bash
# Activate virtual environment
.\.venv\Scripts\Activate.ps1   # On Windows (or source .venv/bin/activate on Linux/macOS)

# Run full test suite (18 unit & acceptance tests)
pytest backend/tests/ -v

# Start FastAPI application
python -m uvicorn claimlab.api:app --host 127.0.0.1 --port 8000 --reload
```

### 2. Frontend Setup
```bash
# Install dependencies
npm --prefix frontend install

# Build production bundle
npm --prefix frontend run build

# Start Vite dev server
npm --prefix frontend run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser.

### 3. Background Worker (Optional / Async Job Execution)
```bash
python -m claimlab.worker
```

### 4. Meta Model Configuration
By default, the application runs in verified deterministic `fixture` mode using `MODEL_MODE=fixture` and `META_MODEL=muse-spark-1.3`.
To connect to the live Meta API:
1. Copy `.env.example` to `.env`.
2. Set `MODEL_MODE=live` and enter your `META_API_KEY`.


## Documentation map

| Document | What it answers |
| --- | --- |
| [Idea vision](docs/00_IDEA_VISION.md) | What are we trying to create, from each stakeholder's perspective? |
| [PRD](docs/01_PRD.md) | Who is it for, what must it do, and what outcomes matter? |
| [Scope and acceptance](docs/02_SCOPE_AND_ACCEPTANCE.md) | What specifically counts as an implemented requirement? |
| [User journeys and UX](docs/03_USER_JOURNEYS_AND_UX.md) | How does the student move through a lesson? |
| [Technical specification](docs/04_TECHNICAL_SPEC.md) | What stack, limits, conventions, and runtime boundaries apply? |
| [Architecture](docs/05_ARCHITECTURE.md) | How do the components work together? |
| [Data model](docs/06_DATA_MODEL.md) | What is persisted, related, versioned, and deleted? |
| [API contracts](docs/07_API_CONTRACTS.md) | What are the endpoints, payloads, errors, and concurrency rules? |
| [Agent orchestration](docs/08_AGENT_ORCHESTRATION.md) | How does a real Meta-powered teaching turn execute? |
| [Whiteboard specification](docs/09_WHITEBOARD_SPEC.md) | How are drawings, equations, edits, and revisions represented? |
| [Experiment engine](docs/10_EXPERIMENT_ENGINE.md) | What runs, under which assumptions, and how is it verified? |
| [Learning observation](docs/11_LEARNING_OBSERVATION.md) | What evidence changes the next teaching action? |
| [Evaluation harness](docs/12_EVALUATION_HARNESS.md) | How do we evaluate correctness, behavior, and learning claims? |
| [Security and privacy](docs/13_SECURITY_AND_PRIVACY.md) | How do uploads, sessions, model access, and execution remain bounded? |
| [Test strategy](docs/14_TEST_STRATEGY.md) | Which meaningful tests establish readiness? |
| [Implementation plan](docs/15_IMPLEMENTATION_PLAN.md) | In what dependency order should the product be built? |
| [Daily tasks](docs/16_DAILY_TASKS.md) | What are the daily outputs and fallback decisions? |
| [Local setup and deployment](docs/17_LOCAL_SETUP_AND_DEPLOYMENT.md) | How should local development and the hosted application run? |
| [Cost and performance](docs/18_COST_AND_PERFORMANCE.md) | What budgets and performance targets should govern it? |
| [Hackathon rules](docs/19_HACKATHON_RULES.md) | Which supplied event conditions affect the project? |
| [Demo and pitch](docs/20_DEMO_AND_PITCH.md) | How does the three-minute story demonstrate the actual product? |
| [Submission checklist](docs/21_SUBMISSION_CHECKLIST.md) | What must be verified before submission? |
| [Decisions and risks](docs/22_DECISIONS_AND_RISKS.md) | What has been chosen, what remains unverified, and what can fail? |
| [Definition of done](docs/23_DEFINITION_OF_DONE.md) | What makes a milestone or release complete? |
| [Source register](docs/24_SOURCE_REGISTER.md) | Which external statements were checked, and where? |
| [Status and handoff](docs/25_STATUS_AND_HANDOFF.md) | What is actually complete and what should the next session do? |
| [Prompts and agent contracts](docs/26_PROMPTS_AND_AGENT_CONTRACTS.md) | What behavioral instructions and tool boundaries should the tutor use? |
| [Reference lessons](docs/27_REFERENCE_LESSONS.md) | What concrete tasks and expected results anchor the first experience? |
| [Release and operations](docs/28_RELEASE_AND_OPERATIONS.md) | How are jobs, incidents, backups, and rollback handled? |
| [Licenses and data rights](docs/29_LICENSE_AND_DATA_RIGHTS.md) | What may be distributed and what needs attribution? |
| [Documentation validation](docs/30_DOCUMENTATION_VALIDATION.md) | What was checked in this pack, and what remains implementation work? |

## Root files for coding tools

- [AGENTS.md](AGENTS.md): shared project guidance.
- [CLAUDE.md](CLAUDE.md): Claude Code handoff.
- [CODEX.md](CODEX.md): Codex handoff.
- [ANTIGRAVITY.md](ANTIGRAVITY.md): Antigravity handoff.
- [RULES.md](RULES.md): product and engineering invariants.
- [SECURITY.md](SECURITY.md): security scope and disclosure placeholder policy.
- [CHANGELOG.md](CHANGELOG.md): documented changes.

CODEX.md and ANTIGRAVITY.md are handoff documents; this pack does not assume that a particular application automatically loads them. Supply them explicitly when necessary. Tool-specific files all point to the same requirements and do not require simultaneous agents.

## Authority and conflicts

The agreed idea is preserved in [00_IDEA_VISION.md](docs/00_IDEA_VISION.md). The PRD defines product outcomes; the acceptance specification defines the release boundary; API/data/experiment specifications define their respective contracts. RULES.md contains cross-cutting invariants. If a concrete contradiction is found, record and resolve it in the decision log rather than silently implementing both alternatives.

Official event terms and later organizer notices govern the competition. The [supplied participant guide](references/PARTICIPANT_GUIDE_SUPPLIED.md) is an input snapshot, not independently verified legal advice or a guarantee of eligibility.

## Schedule

Plan from **27 October through 4 November 2026**. The supplied submission deadline is **5 November 2026, 07:30 IST**, equivalent to 4 November, 21:00 US Eastern Standard Time. The internal submission target is **4 November, 20:00 IST**. Dates are planning assumptions based on the supplied guide and should be rechecked against organizer updates.

This pack authorizes no spending, external messages, publication, or competition submission. It explains how to build and review the product; perform external actions only within Ravi's actual instructions.
