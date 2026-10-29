// A disposable, visibly fixture-only browser preview. No existing guest data is used.
import { chromium } from '@playwright/test';
import { spawn } from 'node:child_process';
import { existsSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createServer } from 'node:net';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const frontend = path.join(root, 'frontend');
const python = path.join(root, '.venv', process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python');
const dataDir = path.join(root, 'data', 'e2e', `preview-${process.pid}`);
const baseURL = 'http://127.0.0.1:5174';
async function requireFreePort(port) {
  const probe = createServer();
  await new Promise((resolve, reject) => {
    probe.once('error', () => reject(new Error(`Preview port ${port} is in use; stop the other local preview before starting this one.`)));
    probe.listen(port, '127.0.0.1', () => probe.close(error => error ? reject(error) : resolve()));
  });
}
await Promise.all([requireFreePort(8081), requireFreePort(5174)]);
const api = spawn(existsSync(python) ? python : 'python', ['-m', 'uvicorn', 'claimlab.api:app', '--host', '127.0.0.1', '--port', '8081'], {
  cwd: root, stdio: 'inherit', windowsHide: true,
  env: { ...process.env, PYTHONPATH: path.join(root, 'backend/src'), MODEL_MODE: 'fixture', META_API_KEY: '', APP_ENV: 'development', PUBLIC_ORIGIN: baseURL, RUNNER_BACKEND: 'local', DATA_DIR: dataDir, DATABASE_URL: `sqlite:///${path.join(dataDir, 'claimlab.db').replaceAll('\\', '/')}`, SESSION_SECRET: 'disposable-browser-preview-only-secret' },
});
const vite = spawn(process.execPath, [path.join(frontend, 'node_modules/vite/bin/vite.js'), '--host', '127.0.0.1', '--port', '5174', '--strictPort'], {
  cwd: frontend, stdio: 'inherit', windowsHide: true,
  env: { ...process.env, VITE_API_TARGET: 'http://127.0.0.1:8081' },
});
let browser;
let finished = false;
async function cleanup() {
  if (finished) return;
  finished = true;
  await browser?.close().catch(() => undefined);
  api.kill(); vite.kill();
}
process.on('SIGINT', () => void cleanup());
process.on('SIGTERM', () => void cleanup());
async function waitReady(url) {
  const deadline = Date.now() + 30_000;
  while (Date.now() < deadline) {
    if (api.exitCode !== null || vite.exitCode !== null) throw new Error('Preview server could not start. Check that ports 8081 and 5174 are available.');
    try { if ((await fetch(url)).ok) return; } catch { /* server starting */ }
    await new Promise(resolve => setTimeout(resolve, 250));
  }
  throw new Error('Preview server readiness deadline exceeded.');
}
try {
  await waitReady('http://127.0.0.1:8081/health/live');
  await waitReady(baseURL);
  browser = await chromium.launch({ channel: process.env.E2E_BROWSER_CHANNEL || (process.platform === 'win32' ? 'chrome' : undefined), headless: false });
  const page = await browser.newPage({ viewport: { width: 1440, height: 960 } });
  await page.goto(baseURL);
  await page.getByRole('button', { name: 'Try the example lesson', exact: true }).click();
  await page.getByLabel('Your answer').waitFor();
  console.log(`Fixture preview open at ${baseURL}. Close the browser window to stop its isolated servers.`);
  await page.waitForEvent('close', { timeout: 0 });
} finally { await cleanup(); }
