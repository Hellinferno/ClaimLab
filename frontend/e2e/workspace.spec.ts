import { test, expect, type Page } from '@playwright/test';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { writeFileSync } from 'node:fs';
import type { ExperimentRun, SessionState } from '../src/types';

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const runtimeErrors = new WeakMap<Page, string[]>();

test.beforeEach(async ({ page }) => {
  const errors: string[] = [];
  runtimeErrors.set(page, errors);
  page.on('pageerror', error => errors.push(error.message));
  page.on('console', message => {
    // Handled HTTP failures are exercised deliberately; React and application errors are not.
    if (message.type() === 'error' && !message.text().startsWith('Failed to load resource:')) errors.push(message.text());
  });
  await page.addInitScript(() => {
    const errors: string[] = [];
    Object.defineProperty(window, '__claimlabBrowserErrors', { value: errors });
    window.addEventListener('error', event => { if (event.message) errors.push(event.message); });
    window.addEventListener('unhandledrejection', event => errors.push(String(event.reason)));
  });
});
test.afterEach(async ({ page }) => {
  expect(runtimeErrors.get(page) || [], 'The browser should not raise unhandled JavaScript errors').toEqual([]);
  if (!page.isClosed()) expect(await page.evaluate(() => (window as Window & { __claimlabBrowserErrors?: string[] }).__claimlabBrowserErrors || []), 'Window errors and promise rejections should be handled').toEqual([]);
});

async function readSession(page: Page): Promise<SessionState> {
  const active = await (await page.request.get('/api/v1/learning-sessions/active')).json();
  expect(active.active_session_id).toBeTruthy();
  const response = await page.request.get(`/api/v1/learning-sessions/${active.active_session_id}`);
  expect(response.ok()).toBeTruthy();
  return response.json();
}

async function readRun(page: Page): Promise<ExperimentRun> {
  const state = await readSession(page);
  const response = await page.request.get(`/api/v1/runs/${state.latest_run_id}`);
  expect(response.ok()).toBeTruthy();
  return response.json();
}

async function startExample(page: Page) {
  await page.goto('/');
  const start = page.getByRole('button', { name: 'Try the example lesson', exact: true });
  await expect(start).toBeEnabled();
  await start.click();
  await expect(page.locator('.task-prompt')).toContainText('12');
  await expect(page.getByLabel('Your answer')).toBeEnabled();
}

test('a guest sees an honest empty state and resumes the exact source, board, and run', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 960 });
  const errors: string[] = [];
  const mathRequests: string[] = [];
  page.on('pageerror', error => errors.push(error.message));
  page.on('request', request => { if (/\/Math\.tsx|\/katex[^/]*\.js/.test(request.url())) mathRequests.push(request.url()); });
  const welcomeStarted = Date.now();
  await page.goto('/');
  await expect(page.getByRole('button', { name: 'Try the example lesson', exact: true })).toBeEnabled();
  const welcomeMs = Date.now() - welcomeStarted;
  await expect(page.getByText('Fixture mode · offline teaching', { exact: true })).toBeVisible();
  await expect(page.locator('.extracted-text')).toHaveCount(0);
  expect(mathRequests).toHaveLength(0);
  await page.screenshot({ path: path.join(repoRoot, 'reports/ui-welcome.png'), fullPage: true });
  const ownerBefore = await (await page.request.get('/api/v1/me')).json();
  const lessonStarted = Date.now();
  await page.getByRole('button', { name: 'Try the example lesson', exact: true }).click();
  await expect(page.getByLabel('Your answer')).toBeEnabled();
  const exampleLessonMs = Date.now() - lessonStarted;
  await expect(page.locator('.katex').first()).toBeVisible();
  expect(mathRequests.length).toBeGreaterThan(0);
  await expect(page.locator('.extracted-text')).toContainText('Softmax');
  const stateBefore = await readSession(page);
  const runBefore = await readRun(page);
  expect(runBefore.status).toBe('succeeded');
  expect(runBefore.checks.every(check => check.status === 'passed' || check.status === 'not_applicable')).toBeTruthy();
  const reloadStarted = Date.now();
  await page.reload();
  await expect(page.getByLabel('Your answer')).toBeEnabled();
  const resumeMs = Date.now() - reloadStarted;
  const ownerAfter = await (await page.request.get('/api/v1/me')).json();
  const stateAfter = await readSession(page);
  expect(ownerAfter.guest_id).toBe(ownerBefore.guest_id);
  expect(stateAfter.session_id).toBe(stateBefore.session_id);
  expect(stateAfter.board).toEqual(stateBefore.board);
  expect(stateAfter.latest_run_id).toBe(runBefore.run_id);
  await expect(page.locator('.document-card')).toContainText('claimlab_attention_lab.pdf');
  await expect(page.locator('.extracted-text')).toContainText('Softmax');
  const equation = page.locator('.whiteboard-canvas .board-equation').first();
  await expect(equation.locator('.katex-html')).toBeVisible();
  await page.evaluate(() => document.fonts.ready);
  const formulaBounds = await equation.evaluate(element => {
    const clip = element.closest('foreignObject')!.getBoundingClientRect();
    const content = element.querySelector('.katex-html')!.getBoundingClientRect();
    return { left: content.left - clip.left, right: clip.right - content.right, top: content.top - clip.top, bottom: clip.bottom - content.bottom, text: element.querySelector('.katex-html')!.textContent };
  });
  expect(formulaBounds.left).toBeGreaterThanOrEqual(-1);
  expect(formulaBounds.right).toBeGreaterThanOrEqual(-1);
  expect(formulaBounds.top).toBeGreaterThanOrEqual(-1);
  expect(formulaBounds.bottom).toBeGreaterThanOrEqual(-1);
  expect(formulaBounds.text).toContain('Attention');
  expect(formulaBounds.text?.trim().endsWith('V')).toBeTruthy();
  await page.getByRole('button', { name: 'View board at readable size' }).click();
  await expect(page.getByRole('button', { name: 'View board at readable size' })).toHaveAttribute('aria-pressed', 'true');
  expect(await page.locator('.whiteboard-canvas').evaluate(element => element.getBoundingClientRect().width)).toBeGreaterThanOrEqual(780);
  expect(await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 1)).toBeFalsy();
  await page.getByRole('button', { name: 'Fit board to panel' }).click();
  await expect(page.getByRole('button', { name: 'Fit board to panel' })).toHaveAttribute('aria-pressed', 'true');
  const queryCard = page.getByRole('button', { name: /^Inspect Query/ });
  await queryCard.focus();
  await page.keyboard.press('Enter');
  await expect(queryCard).toHaveAttribute('aria-pressed', 'true');
  await expect(page.locator('.board-detail')).toContainText('Query');
  await page.screenshot({ path: path.join(repoRoot, 'reports/ui-workspace-desktop.png'), fullPage: true });
  writeFileSync(path.join(repoRoot, 'reports/ui-browser-metrics.json'), JSON.stringify({ measured_at_utc: new Date().toISOString(), model_mode: 'fixture', browser: 'Chrome', viewport: page.viewportSize(), samples: 1, welcome_to_interactive_ms: welcomeMs, example_to_task_ms: exampleLessonMs, reload_to_restored_task_ms: resumeMs, javascript_errors: errors, note: 'Single local headed-browser observations, not percentiles or live-model latency.' }, null, 2) + '\n');
  expect(errors).toEqual([]);
});

test('keyboard answers change teaching and a different application survives reload', async ({ page }) => {
  await startExample(page);
  const before = await readSession(page);
  await page.getByLabel('Your answer').fill('999');
  await page.getByLabel('Your answer').press('Enter');
  await expect.poll(async () => (await readSession(page)).revision).toBeGreaterThan(before.revision);
  await expect(page.locator('.tutor-body')).toContainText('sqrt(16) = 4');
  const wrong = await readSession(page);
  expect(wrong.evidence_summary.attention_scaling).toBe('needs_check');
  await page.getByLabel('Your answer').fill('3');
  await page.getByLabel('Your answer').press('Enter');
  await expect(page.locator('.task-prompt')).toContainText('15');
  const next = await readSession(page);
  expect(next.active_task?.task_variant).not.toBe(before.active_task?.task_variant);
  await page.reload();
  await expect(page.locator('.task-prompt')).toContainText('15');
  await page.getByLabel('Your answer').fill('999');
  await page.getByLabel('Your answer').press('Enter');
  await expect.poll(async () => (await readSession(page)).revision).toBeGreaterThan(next.revision);
  await expect(page.locator('.tutor-body')).not.toContainText('12');
});

test('single-page uploads use real pages and unsupported material does not become a lesson', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByLabel('Upload PDF', { exact: true })).toBeEnabled();
  await page.getByLabel('Upload PDF', { exact: true }).setInputFiles(path.join(repoRoot, 'examples/heldout_attention_note.pdf'));
  await expect(page.locator('.document-card')).toContainText('heldout_attention_note.pdf');
  await expect(page.getByLabel('Source page').locator('option')).toHaveCount(1);
  await expect(page.getByLabel('To page')).toHaveValue('1');
  await page.getByLabel('What would you like to understand?').fill('Why does attention divide scores by the square root of the key dimension?');
  await page.getByRole('button', { name: 'Explore this question' }).click();
  await expect(page.getByLabel('Your answer')).toBeEnabled();
  const supported = await readSession(page);
  await page.getByLabel('Upload PDF', { exact: true }).setInputFiles(path.join(repoRoot, 'examples/unsupported_sample.pdf'));
  await expect(page.locator('.document-card')).toContainText('unsupported_sample.pdf');
  await page.getByRole('button', { name: 'Explore this question' }).click();
  await expect(page.getByRole('status')).toContainText('outside the current labs');
  expect((await readSession(page)).session_id).toBe(supported.session_id);
  await expect(page.locator('.source-panel')).not.toContainText('Section B: Attention ingredients');
});

test('questions preserve evidence and recorded help prevents independent-credit inflation', async ({ page }) => {
  await startExample(page);
  await page.getByLabel('Your answer').fill('999');
  await page.getByLabel('Your answer').press('Enter');
  await expect(page.locator('.tutor-body')).toContainText('sqrt(16) = 4');
  const before = await readSession(page);
  await page.getByLabel('Something still unclear?').fill('What does the key dimension represent?');
  await page.route('**/api/v1/learning-sessions/*/events', route => route.fulfill({ status: 503, contentType: 'application/json', body: JSON.stringify({ error: { message: 'The tutor is temporarily unavailable.' } }) }));
  await page.getByRole('button', { name: 'Ask the tutor' }).click();
  await expect(page.getByRole('alert')).toContainText('temporarily unavailable');
  await expect(page.getByLabel('Something still unclear?')).toHaveValue('What does the key dimension represent?');
  const failed = await readSession(page);
  expect(failed.revision).toBe(before.revision);
  expect(failed.board).toEqual(before.board);
  expect(failed.latest_run_id).toBe(before.latest_run_id);
  expect(failed.active_task).toEqual(before.active_task);
  await page.unroute('**/api/v1/learning-sessions/*/events');
  await page.getByRole('button', { name: 'Ask the tutor' }).click();
  await expect.poll(async () => (await readSession(page)).revision).toBeGreaterThan(before.revision);
  const after = await readSession(page);
  expect(after.evidence_summary).toEqual(before.evidence_summary);
  expect(after.active_task).toEqual(before.active_task);
  await expect(page.locator('.tutor-body')).not.toContainText('sqrt(16) = 4');
  // Use a fresh lesson so this hint check is independent of the earlier wrong answer/question.
  await page.getByLabel('What would you like to understand?').fill('How does scaling change attention score variance?');
  await page.getByRole('button', { name: 'Explore this question' }).click();
  await expect.poll(async () => (await readSession(page)).session_id).not.toBe(after.session_id);
  await expect(page.getByLabel('Your answer')).toBeEnabled();
  const fresh = await readSession(page);
  expect(fresh.evidence_summary.attention_scaling).toBe('introduced');
  const hintResponsePromise = page.waitForResponse(response => response.url().endsWith('/events') && response.request().method() === 'POST' && response.request().postDataJSON()?.event_type === 'hint_requested');
  await page.getByRole('button', { name: 'A little help getting started?', exact: true }).click();
  const hintResponse = await hintResponsePromise;
  expect(hintResponse.ok()).toBeTruthy();
  expect(hintResponse.request().postDataJSON().payload.task_id).toBe(fresh.active_task?.task_id);
  expect(hintResponse.request().postDataJSON().payload.task_variant).toBe(fresh.active_task?.task_variant);
  await expect(page.locator('.task-hint-box')).toBeVisible();
  const helped = await readSession(page);
  expect(helped.active_task).toEqual(fresh.active_task);
  expect(helped.evidence_summary).toEqual(fresh.evidence_summary);
  await page.getByLabel('Your answer').fill('3');
  await page.getByLabel('Your answer').press('Enter');
  await expect(page.locator('.task-prompt')).toContainText('15');
  const secondApplication = await readSession(page);
  expect(secondApplication.evidence_summary.attention_scaling).toBe('supported_with_help');
  await page.getByLabel('Your answer').fill('3');
  await page.getByLabel('Your answer').press('Enter');
  await expect.poll(async () => (await readSession(page)).revision).toBeGreaterThan(secondApplication.revision);
  expect((await readSession(page)).evidence_summary.attention_scaling).toBe('supported_with_help');
});

test('lab drafts validate strictly, preserve earlier results on failure, and execute all three recipes', async ({ page }) => {
  await startExample(page);
  const initial = await readRun(page);
  await page.getByLabel('Key dimensions').fill('16oops, 64');
  await expect(page.getByRole('button', { name: 'Run experiment' })).toBeDisabled();
  await expect(page.locator('.experiment-panel .result-status')).toContainText('Earlier inputs');
  await page.getByLabel('Key dimensions').fill('4, 64, 256');
  await page.route('**/api/v1/learning-sessions/*/runs', route => route.fulfill({ status: 503, contentType: 'application/json', body: JSON.stringify({ error: { message: 'The numerical runner is temporarily unavailable.' } }) }));
  await page.getByRole('button', { name: 'Run experiment' }).click();
  await expect(page.locator('.experiment-panel').getByRole('alert')).toContainText('temporarily unavailable');
  await expect(page.locator('.experiment-panel .result-status')).toContainText('Earlier inputs');
  expect((await readRun(page)).run_id).toBe(initial.run_id);
  await page.unroute('**/api/v1/learning-sessions/*/runs');
  await page.getByRole('button', { name: 'Run experiment' }).click();
  await expect(page.locator('.experiment-panel .result-status')).toContainText('Checked result');
  const scaling = await readRun(page);
  expect(scaling.parameters.dimensions).toEqual([4, 64, 256]);
  expect(scaling.run_id).not.toBe(initial.run_id);
  const chart = page.locator(`[data-run-id="${scaling.run_id}"]`);
  await expect(chart).toHaveCount(1);
  const geometry = await chart.evaluate(group => {
    const baseline = Math.max(...Array.from(group.querySelectorAll('line')).map(line => Number(line.getAttribute('y1'))));
    const unscaled = Array.from(group.querySelectorAll('circle[data-series="unscaled"]')).map(mark => ({ value: Number(mark.getAttribute('data-value')), x: Number(mark.getAttribute('cx')), y: Number(mark.getAttribute('cy')) }));
    const scaled = Array.from(group.querySelectorAll('rect[data-series="scaled"]')).map(mark => ({ value: Number(mark.getAttribute('data-value')), x: Number(mark.getAttribute('x')) + 3, y: Number(mark.getAttribute('y')) + 3 }));
    return { baseline, unscaled, scaled };
  });
  expect(geometry.unscaled).toHaveLength(3);
  expect((geometry.unscaled[1].x - geometry.unscaled[0].x) / (geometry.unscaled[2].x - geometry.unscaled[0].x)).toBeCloseTo((64 - 4) / (256 - 4), 6);
  for (let index = 0; index < geometry.unscaled.length; index += 1) {
    const a = geometry.unscaled[index], b = geometry.scaled[index];
    expect(a.value).toBeCloseTo(scaling.output.results[index].unscaled_variance, 10);
    expect(b.value).toBeCloseTo(scaling.output.results[index].scaled_variance, 10);
    expect((geometry.baseline - a.y) / a.value).toBeCloseTo((geometry.baseline - b.y) / b.value, 8);
  }
  await page.getByLabel('Key dimensions').fill('16');
  await page.getByRole('button', { name: 'Run experiment' }).click();
  await expect(page.locator('.experiment-panel .result-status')).toContainText('Checked result');
  const single = await readRun(page);
  const singleChart = page.locator(`[data-run-id="${single.run_id}"]`);
  await expect(singleChart.locator('circle[data-series="unscaled"]')).toHaveCount(1);
  expect(Number(await singleChart.locator('circle[data-series="unscaled"]').getAttribute('cx'))).toBeGreaterThan(0);

  await page.getByRole('button', { name: 'Softmax', exact: true }).click();
  await page.getByLabel('Input scores').fill('0, 0');
  await page.getByRole('button', { name: 'Run experiment' }).click();
  await expect(page.locator('.experiment-panel .result-status')).toContainText('Checked result');
  const softmax = await readRun(page);
  expect(softmax.recipe_id).toBe('softmax_sensitivity_v1');
  expect(softmax.output.base_probabilities).toEqual([0.5, 0.5]);
  expect(softmax.output.scaled_probabilities).toEqual([0.5, 0.5]);
  await expect(page.locator(`[data-run-id="${softmax.run_id}"]`)).toHaveCount(1);

  await page.getByRole('button', { name: 'Masking', exact: true }).click();
  await page.getByLabel('Score matrix').fill('[[0,0,0],[0,0,0],[0,0,0]]');
  await page.getByRole('button', { name: 'Run experiment' }).click();
  await expect(page.locator('.experiment-panel .result-status')).toContainText('Checked result');
  const masking = await readRun(page);
  expect(masking.recipe_id).toBe('causal_masking_v1');
  expect(masking.output.masked_weights[0]).toEqual([1, 0, 0]);
  expect(masking.output.masked_weights[1]).toEqual([0.5, 0.5, 0]);
  expect(masking.output.masked_weights[2]).toEqual([1 / 3, 1 / 3, 1 / 3]);
  await expect(page.locator('.matrix-table tr').nth(1)).toHaveText('0.5000.5000.000');
  await expect(page.locator(`[data-run-id="${masking.run_id}"]`)).toHaveCount(1);
});

test('failed PDF uploads preserve the lesson and offer an inline error', async ({ page }) => {
  await startExample(page);
  const before = await readSession(page);
  await page.getByLabel('Upload PDF', { exact: true }).setInputFiles({ name: 'invalid.pdf', mimeType: 'application/pdf', buffer: Buffer.from('This is not a PDF') });
  await expect(page.getByRole('alert')).toBeVisible();
  await expect(page.getByRole('alert')).toContainText(/pdf|parse|invalid/i);
  await expect(page.locator('.document-card')).toContainText('claimlab_attention_lab.pdf');
  expect((await readSession(page)).session_id).toBe(before.session_id);
});

test('unavailable API shows recovery without invented source content', async ({ page }) => {
  await page.route('**/api/v1/guest-sessions', route => route.fulfill({ status: 503, contentType: 'application/json', body: JSON.stringify({ error: { message: 'The workspace is temporarily unavailable.' } }) }));
  await page.goto('/');
  await expect(page.getByRole('alert')).toContainText('temporarily unavailable');
  await expect(page.getByRole('button', { name: 'Retry connection' })).toBeVisible();
  await expect(page.locator('.document-card')).toHaveCount(0);
  await expect(page.locator('.extracted-text')).toHaveCount(0);
  await page.unroute('**/api/v1/guest-sessions');
  await page.getByRole('button', { name: 'Retry connection' }).click();
  await expect(page.getByRole('button', { name: 'Try the example lesson', exact: true })).toBeEnabled();
  await expect(page.getByRole('alert')).toHaveCount(0);
});

test('another browser cannot read a lesson and deleting data returns to an empty workspace', async ({ page, browser }) => {
  await startExample(page);
  const original = await readSession(page);
  const owner = await (await page.request.get('/api/v1/me')).json();
  const second = await browser.newContext({ baseURL: new URL(page.url()).origin });
  try {
    const other = await second.newPage();
    await other.goto('/');
    await expect(other.getByRole('button', { name: 'Try the example lesson', exact: true })).toBeEnabled();
    const otherOwner = await (await other.request.get('/api/v1/me')).json();
    expect(otherOwner.guest_id).not.toBe(owner.guest_id);
    expect((await other.request.get(`/api/v1/learning-sessions/${original.session_id}`)).status()).toBe(404);
    expect((await other.request.get(`/api/v1/runs/${original.latest_run_id}`)).status()).toBe(404);
  } finally { await second.close(); }
  await page.getByText('Your session', { exact: true }).click();
  page.once('dialog', dialog => dialog.dismiss());
  await page.getByRole('button', { name: 'Delete my data' }).click();
  expect((await page.request.get('/api/v1/me')).status()).toBe(200);
  expect((await readSession(page)).session_id).toBe(original.session_id);

  await page.route('**/api/v1/me/data', route => route.fulfill({ status: 503, contentType: 'application/json', body: JSON.stringify({ error: { message: 'Some uploaded files could not be removed. Please try deleting again.' } }) }));
  page.once('dialog', async dialog => {
    expect(dialog.message()).toContain('extracted text');
    expect(dialog.message()).toContain('learning history');
    await dialog.accept();
  });
  await page.getByRole('button', { name: 'Delete my data' }).click();
  await expect(page.getByRole('alert')).toContainText('try deleting again');
  expect((await page.request.get('/api/v1/me')).status()).toBe(200);
  expect((await readSession(page)).session_id).toBe(original.session_id);
  await page.unroute('**/api/v1/me/data');

  page.once('dialog', dialog => dialog.accept());
  await page.getByRole('button', { name: 'Delete my data' }).click();
  await expect(page.getByRole('button', { name: 'Try the example lesson', exact: true })).toBeEnabled();
  await expect(page.locator('.document-card')).toHaveCount(0);
  const replacement = await (await page.request.get('/api/v1/me')).json();
  expect(replacement.guest_id).not.toBe(owner.guest_id);
  expect((await page.request.get(`/api/v1/learning-sessions/${original.session_id}`)).status()).toBe(404);
});

test('mobile and reduced-motion layouts keep the learning flow in the viewport', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await startExample(page);
  const hasOverflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 1);
  expect(hasOverflow).toBeFalsy();
  await page.getByRole('button', { name: 'View board at readable size' }).click();
  expect(await page.locator('.whiteboard-canvas').evaluate(element => element.getBoundingClientRect().width)).toBeGreaterThanOrEqual(780);
  expect(await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 1)).toBeFalsy();
  await page.getByRole('button', { name: 'Fit board to panel' }).click();
  await page.getByRole('button', { name: 'Experiment', exact: true }).click();
  await expect(page.locator('#experiment')).toBeInViewport();
  await page.screenshot({ path: path.join(repoRoot, 'reports/ui-workspace-mobile.png'), fullPage: true });
  await page.getByRole('button', { name: 'Whiteboard', exact: true }).click();
  await expect(page.locator('#whiteboard')).toBeInViewport();
});
