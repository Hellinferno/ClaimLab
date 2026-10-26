# Local Setup and Deployment

## Current state

This is a setup contract for the implementation. The archive contains Markdown documents, not a working codebase or dependency lockfiles. Commands below become usable after milestone M0 creates the referenced source structure and command interfaces.

## Development prerequisites

Use Git, Node 24, Python 3.12, and a container runtime capable of the selected Linux isolation profile. Ravi previously reported Windows, VS Code, Python 3.12.10, Node 24.12.0, and Git; verify the actual machine before relying on those versions. Linux containers through an appropriate local runtime are needed for the planned execution boundary.

A valid Meta account/key and access to the configured model are a separate prerequisite for live mode. This pack does not establish acceptance, credits, billing setup, or API access.

## Target source structure

| Path | Purpose |
| --- | --- |
| `frontend/` | React/TypeScript app, tests, npm scripts and lockfile |
| `backend/src/claimlab/` | API, worker, services, typed contracts, migrations integration |
| `backend/tests/` | Numerical, API, worker, and live opt-in tests |
| `backend/requirements.lock` | Resolved tested Python dependency pins |
| `contracts/` | Exported schema and generated TypeScript types |
| `infra/runner/` | Reviewed numerical runner image and entry point |
| `infra/parser/` | Restricted PDF parser image and entry point |
| `examples/` | Author-created source notes and rights metadata |
| `tests/e2e/` | Complete learning journeys and failure cases |
| `docs/` | This documentation and actual evidence updates |

These paths are target implementation paths, not files already supplied by this archive.

## Target install workflow

After those source files exist, create a virtual environment and install the committed locked dependencies. On PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend/requirements.lock
python -m pip install -e backend --no-deps
npm --prefix frontend ci
```

On a POSIX shell, activate with `source .venv/bin/activate` and use the same install commands. Do not weaken system execution/security settings merely to copy a command; use the local environment's supported activation workflow.

Store secrets in a local ignored environment file or the host's secret manager. The application should load configuration through validated settings. Supply the fields listed in [the technical spec](04_TECHNICAL_SPEC.md), resolve an absolute data directory, and run database migrations before the API/worker.

## Target local processes

The backend package must be installed before these module commands are available:

```bash
python -m uvicorn claimlab.api:app --host 127.0.0.1 --port 8000 --reload
python -m claimlab.worker
npm --prefix frontend run dev -- --host 127.0.0.1
```

Run in separate terminals. Configure the Vite development proxy for `/api` to the local backend. Use `PUBLIC_ORIGIN=http://127.0.0.1:5173` consistently; avoid mixing hostnames/cookie scopes. Production uses HTTPS and secure cookies. Never expose a development server or container runtime socket as the hosted product.

## Image/runtime setup

Build the reviewed parser and numerical images from their actual Dockerfiles after M0 creates them. Record immutable digests for release. Prove non-root, no-network, read-only, limits, and secret isolation through tests; an image tag alone is not evidence.

Do not skip execution isolation because the host cannot run it. Select a compatible host or document an alternative reviewed runner before release.

## Hosted topology

Use a small dedicated Linux VM or compatible container host with TLS termination, persistent disk, one API process, one trusted worker, and the selected restricted execution runtime. Build frontend assets and serve them through the same origin as FastAPI. Keep database/files private and outside the web asset directory.

Configure reverse-proxy streaming for SSE, private PDF responses, upload limits, and request deadlines. Readiness checks need database access, worker heartbeat, image availability, and configured model readiness; they must not trigger a paid model call on every health probe.

## Deployment verification

Verify the exact deployed commit, database migrations, owner isolation, a real Meta tool loop, one run of every recipe, progress/reconnect behavior, deletion/expiry, budget limits, and narrow-screen usability. Record actual URLs and test evidence only after they exist.

Choose access settings that let judges review the product under current event requirements. Publishing or granting access is a separate actual action governed by Ravi's instructions; preparation should be complete before requesting any required final approval.

## Rollback

Retain the last known-good image/commit and migration compatibility notes. Stop new job intake, cancel or drain work safely, restore a compatible application version, and verify state/health. Avoid irreversible migrations during the final demo window. See [operations](28_RELEASE_AND_OPERATIONS.md).
