import { useEffect, useMemo, useState } from 'react';
import type { ExperimentRun } from '../types';
import { Icon } from './Icon';

interface ExperimentPanelProps {
  activeRun: ExperimentRun | null;
  onRunRecipe: (recipeId: string, parameters: Record<string, unknown>) => Promise<void>;
  isLoading: boolean;
  disabled?: boolean;
  onStaleChange: (stale: boolean) => void;
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
  return <ExperimentDraft key={props.activeRun?.run_id || 'empty'} {...props}/>;
}
function ExperimentDraft({ activeRun, onRunRecipe, isLoading, disabled = false, onStaleChange }: ExperimentPanelProps) {
  const p = activeRun?.parameters || {};
  const [recipe, setRecipe] = useState(activeRun?.recipe_id || 'attention_scaling_v1');
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
  const stale = Boolean(activeRun && (recipe !== activeRun.recipe_id || !parsed.parameters || canonical(parsed.parameters) !== canonical(activeRun.parameters)));
  useEffect(() => { onStaleChange(stale); }, [stale, onStaleChange]);
  const selected = RECIPES.find(item => item.id === recipe)!;
  const verified = activeRun?.status === 'succeeded' && activeRun.output && activeRun.checks.length > 0 && activeRun.checks.every(check => check.status !== 'failed');
  const blockInputs = isLoading || disabled;

  return <div className="panel experiment-panel">
    <div className="panel-header"><div className="title-row"><Icon name="flask" size={18}/><h2>The experiment lab</h2></div><span className="panel-number">02</span></div>
    <p className="panel-description">A small experiment. A real observation.</p>
    <div className="recipe-tabs" role="group" aria-label="Experiment recipe">{RECIPES.map(item => <button key={item.id} className={'tab-btn ' + (recipe === item.id ? 'active' : '')} aria-pressed={recipe === item.id} onClick={() => { setRecipe(item.id); setRunError(null); }} disabled={isLoading}>{item.name}</button>)}</div>
    <p className="experiment-question">{selected.description}</p>
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
    {activeRun && <div className="run-results">
      <div className="results-header"><span className={'result-status ' + (stale ? 'stale' : verified ? 'verified' : 'failed')}><Icon name={verified && !stale ? 'check' : 'info'} size={14}/>{stale ? 'Earlier inputs' : verified ? 'Checked result' : 'Result unavailable'}</span><span className="run-id" title={activeRun.run_id}>Run {activeRun.run_id.slice(0, 8)}</span></div>
      {stale && <p className="stale-notice">These results use the earlier inputs. Run the experiment to update them.</p>}
      <span className="eyebrow">{RECIPES.find(item => item.id === activeRun.recipe_id)?.name} · OBSERVATION</span>
      {verified && activeRun.recipe_id === 'attention_scaling_v1' && <div className="table-wrapper"><table className="results-table"><caption className="visually-hidden">Score variance from the retained run</caption><thead><tr><th scope="col">dₖ</th><th scope="col">Unscaled</th><th scope="col">Scaled</th></tr></thead><tbody>{activeRun.output.results.map((row: { dimension: number; unscaled_variance: number; scaled_variance: number }) => <tr key={row.dimension}><th scope="row">{row.dimension}</th><td className="unscaled-value">{row.unscaled_variance.toFixed(2)}</td><td className="scaled-value">{row.scaled_variance.toFixed(3)}</td></tr>)}</tbody></table><p className="field-help">Score variance · both series use the same scale</p></div>}
      {verified && activeRun.recipe_id === 'softmax_sensitivity_v1' && <div className="result-stats"><div><span>Original entropy</span><strong>{activeRun.output.base_entropy.toFixed(3)} <small>nats</small></strong></div><div><span>Scaled entropy</span><strong>{activeRun.output.scaled_entropy.toFixed(3)} <small>nats</small></strong></div></div>}
      {verified && activeRun.recipe_id === 'causal_masking_v1' && <div className="table-wrapper"><table className="matrix-table"><caption>Attention weights · future positions excluded</caption><tbody>{activeRun.output.masked_weights.map((row: number[], i: number) => <tr key={i}>{row.map((value: number, j: number) => <td key={j} className={j > i ? 'cell-forbidden' : 'cell-allowed'}>{value.toFixed(3)}</td>)}</tr>)}</tbody></table></div>}
      {!verified && <p className="inline-error">This run did not produce a verified result. Try again with valid inputs.</p>}
      <details className="run-evidence"><summary><Icon name="shield" size={14}/>{activeRun.checks.filter(check => check.status === 'passed').length}/{activeRun.checks.filter(check => check.status !== 'not_applicable').length} checks passed{activeRun.checks.some(check => check.status === 'not_applicable') ? ` · ${activeRun.checks.filter(check => check.status === 'not_applicable').length} not applicable` : ''} · inspect evidence<Icon name="chevron" size={13}/></summary><div className="evidence-details"><h3>Numerical checks</h3>{activeRun.checks.map(check => <div key={check.name} className={'check-item ' + check.status}><strong>{check.status === 'passed' ? '✓' : check.status === 'failed' ? '×' : '—'} {check.name.replaceAll('_', ' ')}</strong><p>{check.detail}</p></div>)}<h3>Experiment assumptions</h3>{activeRun.assumptions.map(item => <p key={item}>{item}</p>)}<h3>Exact retained inputs</h3><pre>{JSON.stringify(activeRun.parameters, null, 2)}</pre><p>Run: <code>{activeRun.run_id}</code></p><p>Runner: <code>{activeRun.runner_digest}</code> · NumPy {activeRun.numpy_version}</p></div></details>
    </div>}
    <div className="lab-footnote"><Icon name="info" size={14}/><p>Synthetic inputs, real calculations. An illustration of the mechanism, not a paper’s benchmark.</p></div>
  </div>;
}
