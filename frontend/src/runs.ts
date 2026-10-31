import type { ExperimentRun } from './types';

export const SANDBOX_RECIPE = 'sandbox_python_v1';

/** Tutor-written experiments may report a failed claim; only the sandbox's own checks gate display. */
export function isChecked(run: ExperimentRun | null): run is ExperimentRun & { status: 'succeeded' } {
  if (!run || run.status !== 'succeeded' || !run.output) return false;
  const gating = run.recipe_id === SANDBOX_RECIPE ? run.checks.filter((check) => !check.name.startsWith('claim: ')) : run.checks;
  return gating.some((check) => check.status === 'passed') && gating.every((check) => check.status !== 'failed');
}
