# Technical Specification

## Chosen first-release stack

| Area | Decision | Reason |
| --- | --- | --- |
| Frontend | React, TypeScript, Vite; npm lockfile | Direct interactive workspace with a small build surface |
| Board | React-rendered SVG scene graph; KaTeX for equations | Precise, inspectable objects and no generated executable markup |
| Charts | SVG components fed by checked run JSON | Values remain tied to computations |
| Backend | Python 3.12, FastAPI, Pydantic v2, HTTPX | Typed contracts and straightforward numerical integration |
| Persistence | SQLAlchemy, Alembic, SQLite WAL on a persistent volume | A single application/worker deployment without another managed service |
| Worker | Separate Python process with durable SQLite job claims | Long-running work survives request disconnects and has explicit state |
| Numerics | NumPy in a reviewed runner image | Reproducible small attention experiments |
| PDF | pypdf extraction; PDF.js display | Native-text ingestion and source viewing |
| Model | Meta Model API, Chat Completions adapter | Bounded tool loop; actual account compatibility is an M0 gate |
| Testing | pytest, Vitest, Playwright; Ruff and TypeScript checks | Numerical, API, state, and consequential UI verification |

Use Node 24 and Python 3.12 as project targets. Verify package compatibility, resolve exact versions, and commit lockfiles during bootstrap. This pack does not invent a set of already-tested package pins. Vite's current guide lists its Node prerequisites; selected packages must be checked against the actual installed runtime. See [sources](24_SOURCE_REGISTER.md).

## Deployment boundary

One frontend build served through FastAPI behind a TLS reverse proxy; one API process and one durable worker; one persistent volume. The worker creates per-job restricted containers from an immutable reviewed image. The API process does not receive Docker control. The worker is trusted infrastructure and is never directly exposed to the browser.

No serverless filesystem assumptions. No multiple API/worker replicas against SQLite. A hosted environment unable to run the selected isolated worker is a deployment blocker or requires a documented alternative runner, not a silent fallback to unrestricted subprocesses.

## Canonical schemas

Pydantic models are the server contract source. Export JSON Schema and generated TypeScript types; use compatible frontend runtime validation for user/model data. Do not hand-maintain divergent copies. Version the application contract as `schema_version: 1`. Strictly reject unknown fields for tool commands and experiment parameters.

## Proposed enforced limits

These are engineering defaults, not measured platform capabilities.

| Limit | First-release value |
| --- | --- |
| Upload | PDF only; 10 MiB per file; 50 pages |
| Owner storage | At most 3 documents / 30 MiB raw content |
| Selection | At most 5 pages and 30,000 normalized text characters |
| Owner sessions | At most 5 live learning sessions |
| PDF parsing | 30-second wall deadline, 512 MiB worker container memory |
| Extracted document text | 500,000 characters total; 50,000 per page; parser output at most 4 MiB |
| Board | 100 objects; 20 commands per atomic patch; labels at most 500 characters |
| Tutor response | 4 provider requests including retries; 8 total tool calls; 2 experiment runs |
| Model request | 25-second client deadline; at most 4,000 generated tokens; 12,000 input-token budget |
| Tutor job | 180-second wall deadline including tools and retries |
| Experiment | 20-second wall deadline; 1 CPU; 512 MiB; 64 processes; no network |
| Experiment data | At most 1 MiB JSON output; no arbitrary filesystem artifacts |
| Queue | One active mutation per learning session; at most 10 queued jobs per owner |
| Guest retention | 24 hours from guest creation; cookie and resource expiry share this boundary |
| Cleanup | Every 15 minutes; reject expired access immediately before physical cleanup |
| Rate limits | 10 tutor requests / minute / owner; 5 uploads / hour / owner; global configurable limits |

Start with these defaults. If profiling requires changes, update this table, tests, and all operational limits together. Never use UI-only validation as the enforcement boundary.

## Environment contract

Required configuration includes `APP_ENV`, `PUBLIC_ORIGIN`, `DATABASE_URL`, `DATA_DIR`, `SESSION_SECRET`, `META_API_KEY`, `META_BASE_URL`, `META_MODEL`, `MODEL_MODE`, `MODEL_INPUT_USD_PER_MILLION`, `MODEL_OUTPUT_USD_PER_MILLION`, `APP_AI_BUDGET_USD`, `RUNNER_IMAGE`, and `PDF_PARSER_IMAGE`.

`MODEL_MODE` is `live` or `fixture`. `META_MODEL=muse-spark-1.3` is the documented candidate; availability is not established until a real probe succeeds. Use the standard model variant for private uploads; do not silently opt users into a contributor/training mode. Budget values are deployment choices, not permission to incur charges.

Only non-sensitive UI configuration can use frontend-exposed environment variables. Provider keys and session secrets stay on the server. Do not log full environment values.

## Runtime conventions

Persistent resource IDs and client event IDs are UUIDs. Concept, task, variant, recipe, and board-object identifiers are bounded stable slugs, such as `attention_scaling` or `values`. Guest cookie credentials are cryptographically random opaque secrets stored as hashes server-side. Timestamps are UTC ISO 8601 in storage and API, rendered in the user's timezone. Dates in these planning documents use IST. Integers identify monotonic resource revisions. Numerical JSON contains finite values only. String enums, units, normalization conventions, and schema versions are explicit.

Package commands described elsewhere are target interfaces to implement. No setup command is claimed to run against a codebase that does not yet exist.
