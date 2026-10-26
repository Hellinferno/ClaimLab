import React, { useState } from 'react';
import type { ExperimentRun } from '../types';

interface ExperimentPanelProps {
  activeRun: ExperimentRun | null;
  onRunRecipe: (recipeId: string, parameters: Record<string, any>) => Promise<void>;
  isLoading: boolean;
}

export const ExperimentPanel: React.FC<ExperimentPanelProps> = ({
  activeRun,
  onRunRecipe,
  isLoading,
}) => {
  const [selectedRecipe, setSelectedRecipe] = useState<string>('attention_scaling_v1');
  const [isStale, setIsStale] = useState<boolean>(false);

  // Recipe B parameters
  const [dimensions, setDimensions] = useState<string>('8, 32, 128');
  const [nKeys, setNKeys] = useState<number>(8);
  const [trials, setTrials] = useState<number>(50);
  const [seed, setSeed] = useState<number>(42);

  // Recipe A parameters
  const [logits, setLogits] = useState<string>('0.0, 1.0, 2.0');
  const [multiplier, setMultiplier] = useState<number>(1.5);

  const handleParamChange = (updater: () => void) => {
    updater();
    setIsStale(true);
  };

  const handleExecute = async () => {
    let params: Record<string, any> = {};

    if (selectedRecipe === 'attention_scaling_v1') {
      const parsedDims = dimensions
        .split(',')
        .map((s) => parseInt(s.trim(), 10))
        .filter((n) => !isNaN(n));
      params = {
        dimensions: parsedDims,
        n_keys: nKeys,
        trials: trials,
        seed: seed,
      };
    } else if (selectedRecipe === 'softmax_sensitivity_v1') {
      const parsedLogits = logits
        .split(',')
        .map((s) => parseFloat(s.trim()))
        .filter((n) => !isNaN(n));
      params = {
        logits: parsedLogits,
        multiplier: multiplier,
        seed: seed,
      };
    } else if (selectedRecipe === 'causal_masking_v1') {
      params = {
        scores: [
          [1.0, 2.0, 3.0],
          [-1.0, 0.5, 2.5],
          [4.0, -2.0, 1.0],
        ],
        seed: seed,
      };
    }

    await onRunRecipe(selectedRecipe, params);
    setIsStale(false);
  };

  return (
    <div className="panel experiment-panel">
      <div className="panel-header">
        <div className="title-row">
          <span className="icon">🔬</span>
          <h3>Numerical Experiment Lab</h3>
        </div>
        {isStale && <span className="badge warning">Stale Results</span>}
      </div>

      {/* Recipe Tabs */}
      <div className="recipe-tabs">
        <button
          className={`tab-btn ${selectedRecipe === 'attention_scaling_v1' ? 'active' : ''}`}
          onClick={() => {
            setSelectedRecipe('attention_scaling_v1');
            setIsStale(true);
          }}
        >
          Attention Scaling
        </button>
        <button
          className={`tab-btn ${selectedRecipe === 'softmax_sensitivity_v1' ? 'active' : ''}`}
          onClick={() => {
            setSelectedRecipe('softmax_sensitivity_v1');
            setIsStale(true);
          }}
        >
          Softmax Sensitivity
        </button>
        <button
          className={`tab-btn ${selectedRecipe === 'causal_masking_v1' ? 'active' : ''}`}
          onClick={() => {
            setSelectedRecipe('causal_masking_v1');
            setIsStale(true);
          }}
        >
          Causal Masking
        </button>
      </div>

      {/* Parameter Controls */}
      <div className="params-form">
        {selectedRecipe === 'attention_scaling_v1' && (
          <>
            <div className="form-group">
              <label>Dimensions d_k (comma separated):</label>
              <input
                type="text"
                value={dimensions}
                onChange={(e) => handleParamChange(() => setDimensions(e.target.value))}
              />
            </div>
            <div className="form-row">
              <div className="form-group">
                <label>Key Count (n_keys):</label>
                <input
                  type="number"
                  min="2"
                  max="16"
                  value={nKeys}
                  onChange={(e) => handleParamChange(() => setNKeys(parseInt(e.target.value, 10)))}
                />
              </div>
              <div className="form-group">
                <label>Trials:</label>
                <input
                  type="number"
                  min="20"
                  max="200"
                  value={trials}
                  onChange={(e) => handleParamChange(() => setTrials(parseInt(e.target.value, 10)))}
                />
              </div>
              <div className="form-group">
                <label>Seed:</label>
                <input
                  type="number"
                  value={seed}
                  onChange={(e) => handleParamChange(() => setSeed(parseInt(e.target.value, 10)))}
                />
              </div>
            </div>
          </>
        )}

        {selectedRecipe === 'softmax_sensitivity_v1' && (
          <>
            <div className="form-group">
              <label>Input Logits:</label>
              <input
                type="text"
                value={logits}
                onChange={(e) => handleParamChange(() => setLogits(e.target.value))}
              />
            </div>
            <div className="form-group">
              <label>Scale Multiplier ({multiplier.toFixed(2)}x):</label>
              <input
                type="range"
                min="0.25"
                max="4.0"
                step="0.25"
                value={multiplier}
                onChange={(e) => handleParamChange(() => setMultiplier(parseFloat(e.target.value)))}
              />
            </div>
          </>
        )}

        {selectedRecipe === 'causal_masking_v1' && (
          <div className="info-box">
            <p>Illustrates causal lower-triangular masking on 3x3 score matrix.</p>
            <p className="dimmed">Forbidden positions j &gt; i receive strict 0.0 weight.</p>
          </div>
        )}

        <button
          className="run-button"
          onClick={handleExecute}
          disabled={isLoading}
        >
          {isLoading ? 'Executing Runner...' : '▶ Run Numerical Recipe'}
        </button>
      </div>

      {/* Output & Checks */}
      {activeRun && (
        <div className="run-results">
          <div className="results-meta">
            <span>Status: <strong className={activeRun.status === 'succeeded' ? 'text-green' : 'text-red'}>{activeRun.status}</strong></span>
            <span>Digest: <code>{activeRun.runner_digest}</code></span>
            <span>NumPy: {activeRun.numpy_version}</span>
          </div>

          {/* Results Table for Attention Scaling */}
          {activeRun.recipe_id === 'attention_scaling_v1' && activeRun.output?.results && (
            <div className="table-wrapper">
              <table className="results-table">
                <thead>
                  <tr>
                    <th>d_k</th>
                    <th>Unscaled Var</th>
                    <th>Scaled Var</th>
                    <th>Scaled Mean Entropy</th>
                  </tr>
                </thead>
                <tbody>
                  {activeRun.output.results.map((r: any) => (
                    <tr key={r.dimension}>
                      <td><strong>{r.dimension}</strong></td>
                      <td className="text-red">{r.unscaled_variance.toFixed(2)}</td>
                      <td className="text-green">{r.scaled_variance.toFixed(3)}</td>
                      <td>{r.scaled_mean_entropy.toFixed(3)} nats</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Results for Softmax Sensitivity */}
          {activeRun.recipe_id === 'softmax_sensitivity_v1' && activeRun.output && (
            <div className="softmax-results">
              <div className="result-stat">
                <span>Base Entropy: {activeRun.output.base_entropy.toFixed(3)} nats</span>
                <span>Scaled Entropy: {activeRun.output.scaled_entropy.toFixed(3)} nats</span>
              </div>
              <div className="result-stat">
                <span>Base Max Prob: {(activeRun.output.base_max_prob * 100).toFixed(1)}%</span>
                <span>Scaled Max Prob: {(activeRun.output.scaled_max_prob * 100).toFixed(1)}%</span>
              </div>
            </div>
          )}

          {/* Results for Causal Masking */}
          {activeRun.recipe_id === 'causal_masking_v1' && activeRun.output && (
            <div className="masking-results">
              <h4>Masked Attention Weight Matrix</h4>
              <table className="matrix-table">
                <tbody>
                  {activeRun.output.masked_weights.map((row: number[], i: number) => (
                    <tr key={i}>
                      {row.map((w: number, j: number) => (
                        <td key={j} className={j > i ? 'cell-forbidden' : 'cell-allowed'}>
                          {w.toFixed(3)}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Verification Checks */}
          <div className="checks-list">
            <h4>Numerical Checks & Invariants</h4>
            {activeRun.checks.map((c, i) => (
              <div key={i} className={`check-item ${c.status}`}>
                <span className="check-badge">{c.status === 'passed' ? '✓' : '✗'}</span>
                <span className="check-name">{c.name}</span>
                <span className="check-detail">{c.detail}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
