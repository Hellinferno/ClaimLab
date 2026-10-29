# ClaimLab frontend

React, TypeScript, and Vite render the source reader, shared SVG whiteboard,
three numerical labs, and learner evidence. See the concept in
[`docs/00_IDEA_VISION.md`](../docs/00_IDEA_VISION.md).

Run commands from this directory after installing the repository's backend
dependencies and running `npm ci`.

```powershell
npm run dev
npm run build
npm run lint
```

Development requests for `/api`, `/health`, and `/examples` proxy to
`http://127.0.0.1:8080`. To use a different local API in PowerShell:

```powershell
$env:VITE_API_TARGET = 'http://127.0.0.1:8000'
npm run dev
```

## Browser verification

```powershell
npm run test:e2e:headed
```

Playwright starts its own API on port 8081 and Vite on port 5174, using
disposable SQLite databases and uploads under ignored `data/e2e/`.
It explicitly uses fixture teaching, an empty provider key, and the local
reviewed numerical runner. It does not touch existing application data or
make live Meta calls. Keep those two test ports free.

Windows uses installed Google Chrome. Set `E2E_BROWSER_CHANNEL=msedge` to
use installed Edge. Other systems use Playwright Chromium; install it with
`npx playwright install chromium` if necessary. `npm run test:e2e` runs the
same suite without showing browser windows.

The suite covers owner/session/source/run restoration, keyboard answers
and board inspection, consequential teaching feedback, free tutor questions,
one-page and unsupported sources, malformed uploads, strict lab inputs,
failed-run stale state, all three numerical recipes, chart coordinates,
owner isolation, deletion, API recovery, and narrow-screen reduced motion.
It also checks that equation JavaScript loads only when needed.

Current screenshots and a single-sample local timing record are written to
`reports/ui-*.png` and `reports/ui-browser-metrics.json`. Test failure traces
and the HTML report remain in ignored `frontend/test-results/` and
`frontend/playwright-report/`. These checks do not establish live provider
behavior or restricted production runner isolation.

## Open a disposable preview

```powershell
npm run preview:fixture
```

This opens Chrome on the example lesson at `http://127.0.0.1:5174` with its
own isolated fixture data. Close that browser window to stop the preview
servers. It uses the same ports as browser tests, so run one at a time.
