import { defineConfig, devices } from '@playwright/test';
import { existsSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const frontendRoot = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(frontendRoot, '..');
const python = path.join(repoRoot, '.venv', process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python');
const dataDir = path.join(repoRoot, 'data', 'e2e', String(process.pid));
const apiPort = 8081;
const uiPort = 5174;
const baseURL = `http://127.0.0.1:${uiPort}`;

export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  workers: 1,
  timeout: 30_000,
  expect: { timeout: 10_000 },
  reporter: [['list'], ['html', { open: 'never' }]],
  use: {
    ...devices['Desktop Chrome'],
    channel: process.env.E2E_BROWSER_CHANNEL || (process.platform === 'win32' ? 'chrome' : undefined),
    baseURL,
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
  webServer: [
    {
      command: `"${existsSync(python) ? python : 'python'}" -m uvicorn claimlab.api:app --host 127.0.0.1 --port ${apiPort}`,
      cwd: repoRoot,
      url: `http://127.0.0.1:${apiPort}/health/live`,
      reuseExistingServer: false,
      env: {
        PYTHONPATH: path.join(repoRoot, 'backend', 'src'),
        APP_ENV: 'development',
        PUBLIC_ORIGIN: baseURL,
        MODEL_MODE: 'fixture',
        META_API_KEY: '',
        RUNNER_BACKEND: 'local',
        DATA_DIR: dataDir,
        DATABASE_URL: `sqlite:///${path.join(dataDir, 'claimlab.db').replaceAll('\\', '/')}`,
        SESSION_SECRET: 'browser-test-only-fixture-secret-never-production',
      },
      timeout: 30_000,
    },
    {
      command: `npm run dev -- --host 127.0.0.1 --port ${uiPort} --strictPort`,
      cwd: frontendRoot,
      url: baseURL,
      reuseExistingServer: false,
      env: { VITE_API_TARGET: `http://127.0.0.1:${apiPort}` },
      timeout: 30_000,
    },
  ],
});
