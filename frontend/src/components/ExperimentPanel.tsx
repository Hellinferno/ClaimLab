import { useEffect, useMemo, useState } from 'react';
import type { ExperimentRun, SandboxOutput, SandboxParameterSpec } from '../types';
import { Icon } from './Icon';
import { isChecked, SANDBOX_RECIPE } from '../runs';

interface ExperimentPanelProps {
  activeRun: ExperimentRun | null;
  onRunRecipe: (recipeId: string, parameters: Record<string, unknown>, baseRunId?: string) => Promise<void>;
  isLoading: boolean;
  disabled?: boolean;
  onStaleChange: (stale: boolean) => void;
  lessonKind?: 'attention_lab' | 'open';
}
function formatValue(value: unknown): string {
  if (typeof value !== 'number') return String(value);
  const size = Math.abs(value);
  return Number.isInteger(value) && size < 1e6 ? String(value) : size !== 0 && (size >= 1e5 || size < 1e-3) ? value.toExponential(2) : value.toFixed(size >= 100 ? 1 : 3);
}

function RunEvidence({ run }: { run: ExperimentRun }) {
  return <details className="run-evidence"><summary><Icon name="shield" size={14}/>{run.checks.filter(check => check.status === 'passed').length}/{run.checks.filter(check => check.status !== 'not_applicable').length} checks passed{run.checks.some(check => check.status === 'not_applicable') ? ` · ${run.checks.filter(check => check.status === 'not_applicable').length} not applicable` : ''} · inspect evidence<Icon name="chevron" size={13}/></summary><div className="evidence-details"><h3>{run.recipe_id === SANDBOX_RECIPE ? 'Checks' : 'Numerical checks'}</h3>{run.checks.map(check => <div key={check.name} className={'check-item ' + check.status}><strong>{check.status === 'passed' ? '✓' : check.status === 'failed' ? '×' : '—'} {check.name.replaceAll('_', ' ')}</strong><p>{check.detail}</p></div>)}<h3>Experiment assumptions</h3>{run.assumptions.map(item => <p key={item}>{item}</p>)}<h3>Exact retained inputs</h3><pre>{JSON.stringify(run.recipe_id === SANDBOX_RECIPE ? run.parameters.values : run.parameters, null, 2)}</pre><p>Run: <code>{run.run_id}</code></p><p>Runner: <code>{run.runner_digest}</code> · NumPy {run.numpy_version}</p></div></details>;
}

function parseKnobs(specs: SandboxParameterSpec[], draft: Record<string, string>): { values: Record<string, number> | null; error: string | null } {
  const values: Record<string, number> = {};
  for (const spec of specs) {
    const text = draft[spec.name] ?? '', value = Number(text), label = spec.label || spec.name;
    if (!text.trim() || !Number.isFinite(value) || value < spec.min || value > spec.max) return { values: null, error: `${label} must be from ${spec.min} to ${spec.max}.` };
    if (spec.integer && !Number.isInteger(value)) return { values: null, error: `${label} must be a whole number.` };
    values[spec.name] = value;
  }
  return { values, error: null };
}

/** A tutor-written experiment: the learner turns its declared knobs and re-runs the same code. */
function SandboxLab({ run, onRun, blockInputs, onStale }: { run: ExperimentRun; onRun: (values: Record<string, number>) => Promise<void>; blockInputs: boolean; onStale: (stale: boolean) => void }) {
  const specs: SandboxParameterSpec[] = run.parameters.parameter_specs || [];
  const values: Record<string, number> = run.parameters.values || {};
  const [draft, setDraft] = useState<Record<string, string>>(() => Object.fromEntries(specs.map(spec => [spec.name, String(values[spec.name] ?? spec.value)])));
  const [runError, setRunError] = useState<string | null>(null);
  const parsed = parseKnobs(specs, draft);
  const stale = !parsed.values || specs.some(spec => parsed.values![spec.name] !== values[spec.name]);
  useEffect(() => { onStale(stale); }, [stale, onStale]);
  const output = (run.output || {}) as SandboxOutput, verified = isChecked(run);
  const claims = run.checks.filter(check => check.name.startsWith('claim: '));
  return <>
    <p className="experiment-question"><strong className="sandbox-title">{String(run.parameters.title || 'Experiment')}</strong>{String(run.parameters.question || '')}</p>
    {specs.length > 0 && <form className="params-form" onSubmit={async event => {
      event.preventDefault(); if (!parsed.values || blockInputs) return;
      setRunError(null);
      try { await onRun(parsed.values); } catch (error) { setRunError(error instanceof Error ? error.message : 'The experiment did not finish. Earlier results still use their original inputs.'); }
    }}>
      <fieldset disabled={blockInputs}><div className="knob-grid">{specs.map(spec => <div className="form-group" key={spec.name}><label htmlFor={`knob-${spec.name}`}>{spec.label || spec.name.replaceAll('_', ' ')} <span>{spec.min}–{spec.max}</span></label><input id={`knob-${spec.name}`} type="number" min={spec.min} max={spec.max} step={spec.step ?? (spec.integer ? 1 : 'any')} value={draft[spec.name] ?? ''} onChange={event => setDraft(previous => ({ ...previous, [spec.name]: event.target.value }))} required/></div>)}</div></fieldset>
      {parsed.error && <p className="inline-error" role="status">{parsed.error}</p>}
      <button className="run-button" type="submit" disabled={blockInputs || !parsed.values}><Icon name={blockInputs ? 'spark' : 'play'} size={16}/>{blockInputs ? 'Working…' : 'Run with my settings'}<Icon name="arrow" size={16}/></button>
      {runError && <p className="inline-error" role="alert">{runError}</p>}
    </form>}
    <div className="run-results">
      <div className="results-header"><span className={'result-status ' + (stale && specs.length ? 'stale' : verified ? 'verified' : 'failed')}><Icon name={verified && !stale ? 'check' : 'info'} size={14}/>{stale && specs.length ? 'Earlier inputs' : verified ? 'Measured result' : 'Run did not finish'}</span><span className="run-id" title={run.run_id}>Run {run.run_id.slice(0, 8)}</span></div>
      {stale && specs.length > 0 && <p className="stale-notice">These results use the earlier inputs. Run the experiment to update them.</p>}
      {verified ? <>
        {output.summary && <p className="sandbox-summary">{output.summary}</p>}
        {Object.keys(output.metrics || {}).length > 0 && <div className="result-stats sandbox-metrics">{Object.entries(output.metrics || {}).slice(0, 8).map(([name, value]) => <div key={name}><span>{name.replaceAll('_', ' ')}</span><strong>{formatValue(value)}</strong></div>)}</div>}
        {output.table && output.table.rows.length > 0 && <div className="table-wrapper"><table className="results-table"><thead><tr>{output.table.columns.map(column => <th scope="col" key={column}>{column}</th>)}</tr></thead><tbody>{output.table.rows.map((row, index) => <tr key={index}>{row.map((cell, cellIndex) => cellIndex === 0 ? <th scope="row" key={cellIndex}>{formatValue(cell)}</th> : <td key={cellIndex}>{formatValue(cell)}</td>)}</tr>)}</tbody></table></div>}
        {claims.length > 0 && <ul className="claim-list">{claims.map(claim => <li key={claim.name} className={claim.status}><strong>{claim.status === 'passed' ? '✓' : '×'} {claim.name.slice(7)}</strong>{claim.detail && <span>{claim.detail}</span>}</li>)}</ul>}
      </> : <p className="inline-error">{output.error || 'This run did not produce a result.'}</p>}
      <details className="run-evidence"><summary><Icon name="flask" size={14}/>See the experiment code<Icon name="chevron" size={13}/></summary><pre className="code-block"><code>{String(run.parameters.code || '')}</code></pre></details>
      {output.stdout && <details className="run-evidence"><summary><Icon name="info" size={14}/>Printed output<Icon name="chevron" size={13}/></summary><pre className="code-block">{output.stdout}</pre></details>}
      <RunEvidence run={run}/>
    </div>
  </>;
}
const RECIPES = [
  { id: 'attention_scaling_v1', name: 'Scaling', description: 'What happens to score variance as the key dimension grows?' },
  { id: 'softmax_sensitivity_v1', name: 'Softmax', description: 'How does multiplying scores change their attention weights?' },
  { id: 'causal_masking_v1', name: 'Masking', description: 'Which positions can contribute when future tokens are masked?' },
];
const defaultScores = [[1, 2, 3], [-1, 0.5, 2.5], [4, -2, 1]];
function canonical(value: unknown): string {
  if (Array.isArray(value)) return '[' + value.map(canonical).join(',') + ']';
  if (value && typeof value === 'object') return '{' + Object.entries(value).sort(([a], [b]) => a.localeCompare(b)).map(([key, item]) => JSON.stringify(key) + ':' + canonical(item)).join(',') + '}';
  return JSON.stringify(value);
}
function integer(text: string, min: number, max: number, label: string) {
  const value = Number(text);
  if (!text.trim() || !Number.isInteger(value) || value < min || value > max) throw new Error(label + ' must be a whole number from ' + min + ' to ' + max + '.');
  return value;
}
export function ExperimentPanel(props: ExperimentPanelProps) {
  // A committed new run initializes the draft from its retained parameters.
  return <ExperimentDraft key={(props.activeRun?.run_id || 'empty') + (props.lessonKind || '')} {...props}/>;
}
function ExperimentDraft({ activeRun, onRunRecipe, isLoading, disabled = false, onStaleChange, lessonKind = 'attention_lab' }: ExperimentPanelProps) {
  const sandboxRun = activeRun?.recipe_id === SANDBOX_RECIPE ? activeRun : null;
  const reviewedRun = sandboxRun ? null : activeRun;
  const p = reviewedRun?.parameters || {};
  const [recipe, setRecipe] = useState(activeRun?.recipe_id || (lessonKind === 'open' ? SANDBOX_RECIPE : 'attention_scaling_v1'));
  const [sandboxStale, setSandboxStale] = useState(false);
  const tabs = [...(sandboxRun ? [{ id: SANDBOX_RECIPE, name: 'Tutor’s lab', description: '' }] : []), ...(lessonKind === 'open' ? [] : RECIPES)];
  const [dimensions, setDimensions] = useState<string>((p.dimensions || [8, 32, 128]).join(', '));
  const [nKeys, setNKeys] = useState(String(p.n_keys ?? 8));
  const [trials, setTrials] = useState(String(p.trials ?? 50));
  const [seed, setSeed] = useState(String(p.seed ?? 42));
  const [logits, setLogits] = useState<string>((p.logits || [0, 1, 2]).join(', '));
  const [multiplier, setMultiplier] = useState(String(p.multiplier ?? 1.5));
  const [scores, setScores] = useState(JSON.stringify(p.scores || defaultScores));
  const [runError, setRunError] = useState<string | null>(null);
  const parsed = useMemo(() => {
    try {
      const parameters: Record<string, unknown> = { seed: integer(seed, 0, 4294967295, 'Seed') };
      if (recipe === 'attention_scaling_v1') {
        const tokens = dimensions.split(',');
        if (!dimensions.trim() || tokens.length > 4) throw new Error('Enter one to four unique dimensions, separated by commas.');
        const values = tokens.map(token => integer(token, 1, 256, 'Each dimension'));
        if (new Set(values).size !== values.length) throw new Error('Dimensions must be unique.');
        Object.assign(parameters, { dimensions: values, n_keys: integer(nKeys, 2, 16, 'Keys'), trials: integer(trials, 20, 200, 'Trials') });
      } else if (recipe === 'softmax_sensitivity_v1') {
        const tokens = logits.split(',');
        if (tokens.length < 2 || tokens.length > 12) throw new Error('Enter 2–12 scores separated by commas.');
        const values = tokens.map(token => { const value = Number(token); if (!token.trim() || !Number.isFinite(value) || value < -20 || value > 20) throw new Error('Scores must be finite numbers from −20 to 20.'); return value; });
        const scale = Number(multiplier);
        if (!multiplier.trim() || !Number.isFinite(scale) || scale < 0.25 || scale > 4) throw new Error('Multiplier must be from 0.25 to 4.');
        Object.assign(parameters, { logits: values, multiplier: scale });
      } else {
        let matrix: unknown;
        try { matrix = JSON.parse(scores); } catch { throw new Error('Use a JSON matrix, for example [[0,0],[0,0]].'); }
        if (!Array.isArray(matrix) || matrix.length < 2 || matrix.length > 8 || matrix.some(row => !Array.isArray(row) || row.length !== (matrix as unknown[]).length || row.some((value: unknown) => typeof value !== 'number' || !Number.isFinite(value) || value < -20 || value > 20))) throw new Error('Use a square 2×2 to 8×8 matrix with scores from −20 to 20.');
        parameters.scores = matrix;
      }
      return { parameters, error: null };
    } catch (error) { return { parameters: null, error: error instanceof Error ? error.message : 'Check your inputs.' }; }
  }, [recipe, dimensions, nKeys, trials, seed, logits, multiplier, scores]);
  const inSandbox = recipe === SANDBOX_RECIPE;
  const stale = inSandbox ? sandboxStale : Boolean(activeRun && (recipe !== activeRun.recipe_id || !parsed.parameters || canonical(parsed.parameters) !== canonical(activeRun.parameters)));
  useEffect(() => { onStaleChange(stale); }, [stale, onStaleChange]);
  const selected = RECIPES.find(item => item.id === recipe) || RECIPES[0];
  const verified = reviewedRun?.status === 'succeeded' && reviewedRun.output && reviewedRun.checks.length > 0 && reviewedRun.checks.every(check => check.status !== 'failed');
  const blockInputs = isLoading || disabled;

  return <div className="panel experiment-panel">
    <div className="panel-header"><div className="title-row"><Icon name="flask" size={18}/><h2>The experiment lab</h2></div><span className="panel-number">02</span></div>
    <p className="panel-description">A small experiment. A real observation.</p>
    {tabs.length > 1 && <div className="recipe-tabs" role="group" aria-label="Experiment recipe">{tabs.map(item => <button key={item.id} className={'tab-btn ' + (recipe === item.id ? 'active' : '')} aria-pressed={recipe === item.id} onClick={() => { setRecipe(item.id); setRunError(null); }} disabled={isLoading}>{item.name}</button>)}</div>}
    {inSandbox ? (sandboxRun ? <SandboxLab run={sandboxRun} blockInputs={blockInputs} onStale={setSandboxStale} onRun={values => onRunRecipe(SANDBOX_RECIPE, values, sandboxRun.run_id)}/>
      : <p className="experiment-question">{disabled ? 'Open a lesson to start experimenting.' : 'The tutor builds a small experiment for this paper as the lesson goes. Ask it to test an idea you are unsure about.'}</p>)
    : <><p className="experiment-question">{selected.description}</p>
    <form className="params-form" onSubmit={async event => {
      event.preventDefault(); if (!parsed.parameters || blockInputs) return;
      setRunError(null);
      try { await onRunRecipe(recipe, parsed.parameters); }
      catch (error) { setRunError(error instanceof Error ? error.message : 'The experiment did not finish. Earlier results still use their original inputs.'); }
    }}>
      <fieldset disabled={blockInputs}>
        {recipe === 'attention_scaling_v1' && <><div className="form-group"><label htmlFor="dimensions">Key dimensions <span>dₖ</span></label><input id="dimensions" value={dimensions} onChange={event => setDimensions(event.target.value)} required aria-describedby="dimensions-help"/><span id="dimensions-help" className="field-help">1–4 unique values, from 1 to 256</span></div><div className="form-row"><div className="form-group"><label htmlFor="key-count">Keys</label><input id="key-count" type="number" min={2} max={16} step={1} value={nKeys} onChange={event => setNKeys(event.target.value)} required/></div><div className="form-group"><label htmlFor="trials">Trials</label><input id="trials" type="number" min={20} max={200} step={1} value={trials} onChange={event => setTrials(event.target.value)} required/></div></div></>}
        {recipe === 'softmax_sensitivity_v1' && <><div className="form-group"><label htmlFor="logits">Input scores</label><input id="logits" value={logits} onChange={event => setLogits(event.target.value)} required/><span className="field-help">2–12 numbers, from −20 to 20</span></div><div className="form-group"><label htmlFor="multiplier">Score multiplier <span>{Number(multiplier).toFixed(2)}×</span></label><input id="multiplier" type="range" min={0.25} max={4} step={0.25} value={multiplier} onChange={event => setMultiplier(event.target.value)}/><div className="range-labels"><span>0.25× · gentler</span><span>4× · sharper</span></div></div></>}
        {recipe === 'causal_masking_v1' && <div className="form-group"><label htmlFor="scores">Score matrix</label><textarea id="scores" className="matrix-input" value={scores} onChange={event => setScores(event.target.value)} rows={3} required/><span className="field-help">Square JSON matrix · 2–8 positions</span></div>}
        <div className="form-group seed-field"><label htmlFor="seed">Random seed <span>Repeatable inputs</span></label><input id="seed" type="number" min={0} max={4294967295} step={1} value={seed} onChange={event => setSeed(event.target.value)} required/></div>
      </fieldset>
      {parsed.error && <p className="inline-error" role="status">{parsed.error}</p>}
      <button className="run-button" type="submit" disabled={blockInputs || !parsed.parameters}><Icon name={isLoading ? 'spark' : 'play'} size={16}/>{isLoading ? 'Working…' : 'Run experiment'}<Icon name="arrow" size={16}/></button>
      {disabled && <p className="field-help centered">Open a lesson to start experimenting.</p>}
      {runError && <p className="inline-error" role="alert">{runError}</p>}
    </form>
    {reviewedRun && <div className="run-results">
      <div className="results-header"><span className={'result-status ' + (stale ? 'stale' : verified ? 'verified' : 'failed')}><Icon name={verified && !stale ? 'check' : 'info'} size={14}/>{stale ? 'Earlier inputs' : verified ? 'Checked result' : 'Result unavailable'}</span><span className="run-id" title={reviewedRun.run_id}>Run {reviewedRun.run_id.slice(0, 8)}</span></div>
      {stale && <p className="stale-notice">These results use the earlier inputs. Run the experiment to update them.</p>}
      <span className="eyebrow">{RECIPES.find(item => item.id === reviewedRun.recipe_id)?.name} · OBSERVATION</span>
      {verified && reviewedRun.recipe_id === 'attention_scaling_v1' && <div className="table-wrapper"><table className="results-table"><caption className="visually-hidden">Score variance from the retained run</caption><thead><tr><th scope="col">dₖ</th><th scope="col">Unscaled</th><th scope="col">Scaled</th></tr></thead><tbody>{reviewedRun.output.results.map((row: { dimension: number; unscaled_variance: number; scaled_variance: number }) => <tr key={row.dimension}><th scope="row">{row.dimension}</th><td className="unscaled-value">{row.unscaled_variance.toFixed(2)}</td><td className="scaled-value">{row.scaled_variance.toFixed(3)}</td></tr>)}</tbody></table><p className="field-help">Score variance · both series use the same scale</p></div>}
      {verified && reviewedRun.recipe_id === 'softmax_sensitivity_v1' && <div className="result-stats"><div><span>Original entropy</span><strong>{reviewedRun.output.base_entropy.toFixed(3)} <small>nats</small></strong></div><div><span>Scaled entropy</span><strong>{reviewedRun.output.scaled_entropy.toFixed(3)} <small>nats</small></strong></div></div>}
      {verified && reviewedRun.recipe_id === 'causal_masking_v1' && <div className="table-wrapper"><table className="matrix-table"><caption>Attention weights · future positions excluded</caption><tbody>{reviewedRun.output.masked_weights.map((row: number[], i: number) => <tr key={i}>{row.map((value: number, j: number) => <td key={j} className={j > i ? 'cell-forbidden' : 'cell-allowed'}>{value.toFixed(3)}</td>)}</tr>)}</tbody></table></div>}
      {!verified && <p className="inline-error">This run did not produce a verified result. Try again with valid inputs.</p>}
      <RunEvidence run={reviewedRun}/>
    </div>}</>}
    <div className="lab-footnote"><Icon name="info" size={14}/><p>{inSandbox ? 'Tutor-written code, run in an isolated sandbox you can inspect. Synthetic inputs, real calculations: an illustration of the mechanism, not the paper’s benchmark.' : 'Synthetic inputs, real calculations. An illustration of the mechanism, not a paper’s benchmark.'}</p></div>
  </div>;
}
