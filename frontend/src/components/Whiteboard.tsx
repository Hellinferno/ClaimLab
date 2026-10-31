import React, { lazy, memo, Suspense, useEffect, useId, useMemo, useRef, useState } from 'react';
import type { BoardObject, SceneGraph, ExperimentRun, SandboxOutput, SandboxSeries } from '../types';
import { isChecked, SANDBOX_RECIPE } from '../runs';

const LazyBoardEquation = lazy(() => import('./Math').then(module => ({ default: module.BoardEquation })));

interface WhiteboardProps {
  scene: SceneGraph;
  activeRun: ExperimentRun | null;
  isStale?: boolean;
  onSelectObject?: (obj: BoardObject) => void;
  selectedObjectId?: string | null;
  /** Lesson pacing: the latest turn's drawings appear step by step. */
  revealTurn?: string | null;
  revealStep?: number;
  focusIds?: string[];
}

const INK = '#243d35', MUTED = '#667a70', GREEN = '#377b60', AMBER = '#b88250', LINE = '#dde4de';
const SERIES_COLORS = [GREEN, AMBER, '#4f6fa8', '#9a5a8c', '#5f8f8a', '#8a7a4f'];
function sandboxSeries(output: SandboxOutput | undefined): SandboxSeries[] {
  return (output?.series || []).filter((series) => finiteArray(series.x) && finiteArray(series.y) && series.x.length === series.y.length);
}
function finiteArray(value: unknown): value is number[] {
  return Array.isArray(value) && value.length > 0
    && value.every((item) => typeof item === 'number' && Number.isFinite(item));
}
function numberLabel(value: number): string {
  const size = Math.abs(value);
  if (size !== 0 && (size >= 1e5 || size < 1e-3)) return value.toExponential(1);
  return size >= 100 ? value.toFixed(0) : size >= 10 ? value.toFixed(1) : value.toFixed(2);
}

function matchesPlot(object: BoardObject, run: ExperimentRun | null): run is ExperimentRun & { status: 'succeeded' } {
  if (!isChecked(run) || object.payload.run_id !== run.run_id) return false;
  const fields: Record<string, string[]> = {
    attention_scaling_v1: ['results'],
    softmax_sensitivity_v1: ['base_probabilities', 'scaled_probabilities'],
    causal_masking_v1: ['masked_weights'],
    [SANDBOX_RECIPE]: ['series'],
  };
  return fields[run.recipe_id]?.includes(object.payload.field) === true;
}

const Equation = ({ latex }: { latex: string }) => <Suspense fallback={<div className="board-equation">{latex}</div>}><LazyBoardEquation latex={latex}/></Suspense>;
interface VarianceRow { dimension: number; unscaled_variance: number; scaled_variance: number }
function varianceRows(output: ExperimentRun['output']): VarianceRow[] {
  if (!Array.isArray(output?.results)) return [];
  if (!output.results.every((row: VarianceRow) => row && Number.isFinite(row.dimension)
    && Number.isFinite(row.unscaled_variance) && Number.isFinite(row.scaled_variance)
    && row.unscaled_variance >= 0 && row.scaled_variance >= 0)) return [];
  return [...output.results].sort((a: VarianceRow, b: VarianceRow) => a.dimension - b.dimension);
}
function runSummary(run: ExperimentRun): string {
  if (run.recipe_id === SANDBOX_RECIPE) {
    const output = run.output as SandboxOutput;
    const series = sandboxSeries(output).map((item) => `${item.name}: ${item.y.length} points, from ${numberLabel(item.y[0])} to ${numberLabel(item.y[item.y.length - 1])}`);
    const metrics = Object.entries(output.metrics || {}).map(([name, value]) => `${name} ${typeof value === 'number' ? numberLabel(value) : String(value)}`);
    return [output.summary, ...series, ...metrics].filter(Boolean).join('. ') || 'No reported values.';
  }
  if (run.recipe_id === 'attention_scaling_v1') return varianceRows(run.output).map((row) =>
    `Dimension ${row.dimension}: unscaled variance ${numberLabel(row.unscaled_variance)}, scaled variance ${numberLabel(row.scaled_variance)}`).join('. ');
  if (run.recipe_id === 'softmax_sensitivity_v1') {
    const { base_probabilities: base, scaled_probabilities: scaled } = run.output || {};
    if (!finiteArray(base) || !finiteArray(scaled)) return 'No valid probability data.';
    return base.map((value, index) => `Item ${index + 1}: base ${(value * 100).toFixed(1)}%, scaled ${((scaled[index] ?? 0) * 100).toFixed(1)}%`).join('. ');
  }
  const weights = run.output?.masked_weights;
  if (!Array.isArray(weights) || !weights.every(finiteArray)) return 'No valid matrix data.';
  return weights.map((row: number[], index: number) => `Row ${index + 1}: ${row.map((value) => value.toFixed(3)).join(', ')}`).join('. ');
}

// Coordinates derive from retained output; both series share each axis.
const RunChart = memo(({ run, width, height, earlier = false }: { run: ExperimentRun; width: number; height: number; earlier?: boolean }) => {
  const left = 43, right = width - 23, top = 65, bottom = height - 48;
  const chartHeight = Math.max(40, bottom - top);
  if (run.recipe_id === SANDBOX_RECIPE) {
    const output = run.output as SandboxOutput, series = sandboxSeries(output).slice(0, SERIES_COLORS.length);
    const title = output.chart?.title || String(run.parameters.title || 'Measured result');
    if (!series.length) return <g data-run-id={run.run_id}><text x="18" y="25" fill={INK} fontSize="13" fontWeight="650">{title}</text><text x="18" y="60" fill={MUTED} fontSize="11">{output.summary || 'This run reported numbers, not a series. See the lab panel.'}</text></g>;
    const xs = series.flatMap((item) => item.x), ys = series.flatMap((item) => item.y);
    const bars = output.chart?.kind === 'bar';
    const minX = Math.min(...xs), maxX = Math.max(...xs);
    const minY = Math.min(bars ? 0 : Infinity, ...ys), maxY = Math.max(bars ? 0 : -Infinity, ...ys);
    const spanY = maxY - minY || Math.abs(maxY) || 1, lowY = minY - (bars ? 0 : spanY * 0.05), highY = maxY + spanY * 0.05;
    const x = (value: number) => maxX === minX ? (left + right) / 2 : left + (value - minX) / (maxX - minX) * (right - left);
    const y = (value: number) => bottom - (value - lowY) / (highY - lowY) * chartHeight;
    // Tick precision follows each axis's range, so a 0.002–0.009 profit axis does not read 0.00, 0.00, 0.01.
    const tick = (span: number) => (value: number) => Math.abs(span) >= 1e5 ? value.toExponential(1)
      : value.toFixed(Math.min(6, Math.max(0, Math.ceil(-Math.log10(Math.abs(span) || 1)) + 1)));
    const yTick = tick(highY - lowY), xTick = tick(maxX - minX);
    const band = (right - left) / Math.max(1, series[0].x.length), barWidth = Math.max(2, band * 0.8 / series.length);
    return <g role="img" aria-label={`${title}. ${runSummary(run)}`} data-run-id={run.run_id}>
      <title>{title}</title>
      <text x="18" y="25" fill={INK} fontSize="13" fontWeight="650">{title.slice(0, 70)}</text>
      <text x="18" y="43" fill={MUTED} fontSize="10">{earlier ? 'Earlier run' : 'Run'} {run.run_id.slice(0, 8)} · tutor-written sandbox experiment</text>
      {[0, 0.5, 1].map((fraction) => { const value = lowY + (highY - lowY) * fraction; return <g key={fraction}>
        <line x1={left} x2={right} y1={y(value)} y2={y(value)} stroke={LINE} strokeDasharray="3 4" />
        <text x={left - 6} y={y(value) + 3} textAnchor="end" fill={MUTED} fontSize="9">{yTick(value)}</text>
      </g>; })}
      <line x1={left} x2={right} y1={bottom} y2={bottom} stroke={LINE} />
      <text x={left} y={bottom + 15} fill={MUTED} fontSize="9">{xTick(minX)}</text>
      <text x={right} y={bottom + 15} fill={MUTED} fontSize="9" textAnchor="end">{xTick(maxX)}</text>
      {output.chart?.x_label && <text x={(left + right) / 2} y={bottom + 15} fill={MUTED} fontSize="9" textAnchor="middle">{output.chart.x_label.slice(0, 50)}</text>}
      {output.chart?.y_label && <text x={left} y={top - 8} fill={MUTED} fontSize="9">{output.chart.y_label.slice(0, 50)}</text>}
      {series.map((item, index) => bars
        ? <g key={item.name} data-series={item.name}>{item.y.map((value, point) => <rect key={point} x={left + band * point + band * 0.1 + barWidth * index} y={Math.min(y(value), y(0))} width={barWidth} height={Math.abs(y(value) - y(0))} fill={SERIES_COLORS[index]} rx="1"><title>{item.name}: {value}</title></rect>)}</g>
        : <polyline key={item.name} data-series={item.name} fill="none" stroke={SERIES_COLORS[index]} strokeWidth="2" strokeDasharray={index % 2 ? '5 3' : undefined} points={item.x.map((value, point) => `${x(value)},${y(item.y[point])}`).join(' ')}><title>{item.name}</title></polyline>)}
      {series.map((item, index) => <g key={item.name} transform={`translate(${18 + (index % 3) * Math.min(190, (width - 36) / 3)}, ${height - 14 - Math.floor(index / 3) * 13})`}>
        <rect y="-6" width="10" height="4" fill={SERIES_COLORS[index]} rx="1" /><text x="14" y="-2" fontSize="9" fill={INK}>{item.name.slice(0, 26)}</text>
      </g>)}
    </g>;
  }
  if (run.recipe_id === 'attention_scaling_v1') {
    const rows = varianceRows(run.output);
    if (!rows.length) return <text x="18" y="90" fill={MUTED} fontSize="12">No valid variance output to display.</text>;
    const largest = Math.max(...rows.flatMap((row) => [row.unscaled_variance, row.scaled_variance]), 1);
    const magnitude = 10 ** Math.floor(Math.log10(largest));
    const maxY = Math.ceil(largest / magnitude) * magnitude;
    const minX = rows[0].dimension, maxX = rows[rows.length - 1].dimension;
    const x = (dimension: number) => maxX === minX ? (left + right) / 2 : left + (dimension - minX) / (maxX - minX) * (right - left);
    const y = (variance: number) => bottom - variance / maxY * chartHeight;
    return <g role="img" aria-label={`Score variance by key dimension. ${runSummary(run)}`} data-run-id={run.run_id}>
      <title>Score variance by key dimension, same vertical scale for both series</title>
      <text x="18" y="25" fill={INK} fontSize="13" fontWeight="650">Score variance by dimension</text>
      <text x="18" y="43" fill={MUTED} fontSize="10">{earlier ? 'Earlier run' : 'Run'} {run.run_id.slice(0, 8)} · seed {run.seed}</text>
      {[0, 0.25, 0.5, 0.75, 1].map((fraction) => <g key={fraction}>
        <line x1={left} x2={right} y1={y(maxY * fraction)} y2={y(maxY * fraction)} stroke={LINE} strokeDasharray="3 4" />
        <text x={left - 8} y={y(maxY * fraction) + 3} textAnchor="end" fill={MUTED} fontSize="9">{numberLabel(maxY * fraction)}</text>
      </g>)}
      <line x1={left} x2={right} y1={bottom} y2={bottom} stroke={LINE} />
      {rows.map((row) => <text key={row.dimension} x={x(row.dimension)} y={bottom + 17} fill={MUTED} textAnchor="middle" fontSize="10">{row.dimension}</text>)}
      <polyline data-series="unscaled" fill="none" stroke={AMBER} strokeWidth="2.5" strokeDasharray="5 3" points={rows.map((row) => `${x(row.dimension)},${y(row.unscaled_variance)}`).join(' ')} />
      <polyline data-series="scaled" fill="none" stroke={GREEN} strokeWidth="2.5" points={rows.map((row) => `${x(row.dimension)},${y(row.scaled_variance)}`).join(' ')} />
      {rows.map((row) => <g key={row.dimension}>
        <circle data-series="unscaled" data-value={row.unscaled_variance} cx={x(row.dimension)} cy={y(row.unscaled_variance)} r="3.5" fill={AMBER}><title>Unscaled: {row.unscaled_variance}</title></circle>
        <rect data-series="scaled" data-value={row.scaled_variance} x={x(row.dimension) - 3} y={y(row.scaled_variance) - 3} width="6" height="6" rx="1" fill={GREEN}><title>Scaled: {row.scaled_variance}</title></rect>
      </g>)}
      <text x={right} y={bottom + 34} textAnchor="end" fill={MUTED} fontSize="9">Key dimension dₖ</text>
      <circle cx="20" cy={height - 14} r="3" fill={AMBER} /><text x="29" y={height - 11} fontSize="10" fill={INK}>Unscaled</text>
      <rect x="100" y={height - 17} width="6" height="6" fill={GREEN} rx="1" /><text x="111" y={height - 11} fontSize="10" fill={INK}>Scaled</text>
    </g>;
  }
  if (run.recipe_id === 'softmax_sensitivity_v1') {
    const { base_probabilities: base, scaled_probabilities: scaled } = run.output || {};
    if (!finiteArray(base) || !finiteArray(scaled) || base.length !== scaled.length) return <text x="18" y="90" fill={MUTED} fontSize="12">No valid probability output to display.</text>;
    const band = (right - left) / base.length, barWidth = Math.max(2, band * 0.3);
    return <g role="img" aria-label={`Softmax probabilities. ${runSummary(run)}`} data-run-id={run.run_id}>
      <title>Base and scaled probability distribution</title>
      <text x="18" y="25" fill={INK} fontSize="13" fontWeight="650">A different distribution</text>
      <text x="18" y="43" fill={MUTED} fontSize="10">{earlier ? 'Earlier run' : 'Run'} {run.run_id.slice(0, 8)} · multiplier {run.parameters.multiplier}×</text>
      {[0, 0.5, 1].map((fraction) => <g key={fraction}>
        <line x1={left} x2={right} y1={bottom - fraction * chartHeight} y2={bottom - fraction * chartHeight} stroke={LINE} strokeDasharray="3 4" />
        <text x={left - 6} y={bottom - fraction * chartHeight + 3} textAnchor="end" fill={MUTED} fontSize="9">{fraction * 100}%</text>
      </g>)}
      {base.map((probability, index) => {
        const x = left + band * index + band * 0.15;
        return <g key={index}>
          <rect x={x} y={bottom - probability * chartHeight} width={barWidth} height={probability * chartHeight} rx="2" fill={AMBER}><title>Base item {index + 1}: {probability}</title></rect>
          <rect x={x + barWidth + 2} y={bottom - scaled[index] * chartHeight} width={barWidth} height={scaled[index] * chartHeight} rx="2" fill={GREEN}><title>Scaled item {index + 1}: {scaled[index]}</title></rect>
          <text x={left + band * (index + 0.5)} y={bottom + 17} textAnchor="middle" fill={MUTED} fontSize="9">{index + 1}</text>
        </g>;
      })}
      <text x={right} y={bottom + 34} textAnchor="end" fill={MUTED} fontSize="9">Item</text>
      <circle cx="20" cy={height - 14} r="3" fill={AMBER} /><text x="29" y={height - 11} fontSize="10" fill={INK}>Base</text>
      <rect x="83" y={height - 17} width="6" height="6" fill={GREEN} rx="1" /><text x="94" y={height - 11} fontSize="10" fill={INK}>Scaled</text>
    </g>;
  }
  const weights = run.output?.masked_weights, mask = run.output?.allowed_mask;
  if (!Array.isArray(weights) || !weights.length || !weights.every(finiteArray)
    || weights.some((row) => row.length !== weights.length) || !Array.isArray(mask)
    || mask.length !== weights.length || mask.some((row) => !Array.isArray(row) || row.length !== weights.length || row.some((value) => typeof value !== 'boolean'))) {
    return <text x="18" y="90" fill={MUTED} fontSize="12">No valid masking output to display.</text>;
  }
  const count = weights.length, cell = Math.min((right - left) / count, (height - top - 24) / count);
  const originX = left + ((right - left) - cell * count) / 2;
  return <g role="img" aria-label={`Causal attention weights. ${runSummary(run)}`} data-run-id={run.run_id}>
    <title>Retained causal attention weights; crossed cells exclude future tokens</title>
    <text x="18" y="25" fill={INK} fontSize="13" fontWeight="650">Only the present and the past</text>
    <text x="18" y="43" fill={MUTED} fontSize="10">{earlier ? 'Earlier run' : 'Run'} {run.run_id.slice(0, 8)} · {count} × {count} matrix</text>
    {weights.map((row: number[], rowIndex: number) => <g key={rowIndex}>
      <text x={originX - 9} y={top + (rowIndex + 0.5) * cell + 3} fill={MUTED} fontSize="9" textAnchor="end">{rowIndex + 1}</text>
      {row.map((value, colIndex) => {
        const allowed = mask[rowIndex][colIndex] === true, x = originX + colIndex * cell, y = top + rowIndex * cell;
        return <g key={colIndex}>
          {rowIndex === 0 && <text x={x + cell / 2} y={top - 7} fill={MUTED} fontSize="9" textAnchor="middle">{colIndex + 1}</text>}
          <rect x={x + 1} y={y + 1} width={cell - 3} height={cell - 3} rx="3" fill={allowed ? GREEN : '#edf0ec'} fillOpacity={allowed ? 0.1 + value * 0.9 : 1} />
          {!allowed && <line x1={x + 5} y1={y + cell - 5} x2={x + cell - 5} y2={y + 5} stroke="#d2dbd4" />}
          <text x={x + (cell - 1) / 2} y={y + cell / 2 + 3} fill={allowed && value > 0.55 ? '#fff' : INK} textAnchor="middle" fontSize={Math.min(11, cell * 0.32)}>{value.toFixed(2)}</text>
          <title>Row {rowIndex + 1}, column {colIndex + 1}: {value}{allowed ? '' : ', future token excluded'}</title>
        </g>;
      })}
    </g>)}
  </g>;
});

export const Whiteboard: React.FC<WhiteboardProps> = ({ scene, activeRun, isStale = false, onSelectObject, selectedObjectId, revealTurn = null, revealStep = Number.POSITIVE_INFINITY, focusIds }) => {
  const markerId = useId().replace(/:/g, '');
  const surfaceRef = useRef<HTMLDivElement>(null);
  const [localSelection, setLocalSelection] = useState<string | null>(null);
  const [retainedRuns, setRetainedRuns] = useState<Record<string, ExperimentRun>>({});
  const [lookupError, setLookupError] = useState('');
  const [readableSize, setReadableSize] = useState(false);
  const allObjects = useMemo(() => scene.objects || [], [scene]);
  // Drawings for later steps of the current lesson stay hidden until the learner reaches them.
  const objects = useMemo(() => {
    const hidden = new Set(allObjects.filter((object) => revealTurn && object.payload.turn === revealTurn
      && typeof object.payload.step === 'number' && object.payload.step > revealStep).map((object) => object.id));
    return allObjects.filter((object) => !hidden.has(object.id) && !(object.type === 'connector'
      && (hidden.has(object.payload.from_object_id) || hidden.has(object.payload.to_object_id))));
  }, [allObjects, revealTurn, revealStep]);
  const focusKey = (focusIds || []).join('\n');
  const focused = useMemo(() => new Set(focusKey ? focusKey.split('\n') : []), [focusKey]);
  const byId = useMemo(() => new Map(objects.map((object) => [object.id, object])), [objects]);
  // Bring the current step's drawing into view inside the board, without moving the page.
  useEffect(() => {
    const surface = surfaceRef.current, first = focusKey.split('\n')[0];
    const target = first ? surface?.querySelector(`[data-object-id="${CSS.escape(first)}"]`) : null;
    if (!surface || !target) return;
    const offset = target.getBoundingClientRect().top - surface.getBoundingClientRect().top;
    if (offset < 0 || offset > surface.clientHeight - 60) {
      surface.scrollTo({ top: surface.scrollTop + offset - 24, behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth' });
    }
  }, [focusKey]);
  const selection = selectedObjectId === undefined ? localSelection : selectedObjectId;
  const selectedObject = selection ? byId.get(selection) : undefined;
  const bounds = useMemo(() => {
    // The board grows with the drawing, the way a teacher fills it in.
    const shapes = objects.filter((object) => object.type !== 'connector');
    const minX = Math.min(0, ...shapes.map((object) => object.position.x - 18)), minY = Math.min(0, ...shapes.map((object) => object.position.y - 18));
    const maxX = Math.max(780, ...shapes.map((object) => object.position.x + object.dimensions.width + 18));
    const maxY = Math.max(355, ...shapes.map((object) => object.position.y + object.dimensions.height + 18));
    return `${minX} ${minY} ${maxX - minX} ${maxY - minY}`;
  }, [objects]);
  const checked = isChecked(activeRun);
  // A plot waiting for a later step still owns its run: do not reveal the result early below the board.
  const sceneHasCurrentRun = checked && allObjects.some((object) => object.type === 'plot_ref' && matchesPlot(object, activeRun));
  const select = (object: BoardObject) => {
    setLocalSelection(object.id);
    setLookupError('');
    onSelectObject?.(object);
    const runId = object.payload.run_id;
    if (object.type === 'plot_ref' && typeof runId === 'string' && runId !== activeRun?.run_id && !retainedRuns[runId]) {
      void fetch(`/api/v1/runs/${encodeURIComponent(runId)}`).then(async (response) => {
        if (!response.ok) throw new Error('The earlier run could not be loaded. Select the card to retry.');
        const run: ExperimentRun = await response.json();
        if (run.run_id !== runId || !isChecked(run)) throw new Error('This earlier run has no checked output to display.');
        setRetainedRuns((previous) => ({ ...previous, [runId]: run }));
      }).catch((error: unknown) => setLookupError(error instanceof Error ? error.message : 'The earlier run could not be loaded.'));
    }
  };
  return <div className="whiteboard-container">
    <div className="whiteboard-header">
      <div className="whiteboard-title"><span className="board-kicker">01 / EXPLORE</span><h3>Shared whiteboard</h3></div>
      <span className="board-status">{isStale ? 'Earlier inputs' : 'Saved board'} · rev {scene.board_revision}</span>
    </div>
    <div className="whiteboard-surface" ref={surfaceRef}>
      {objects.length ? <svg viewBox={bounds} className="whiteboard-canvas" style={readableSize ? { minWidth: `${bounds.split(' ')[2]}px` } : undefined} role="group" aria-label="Shared whiteboard diagram">
        <defs><marker id={markerId} viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M 0 1 L 9 5 L 0 9" fill="none" stroke={GREEN} strokeWidth="1.5" /></marker></defs>
        {objects.filter((object) => object.type === 'connector').map((connector) => {
          const from = byId.get(connector.payload.from_object_id), to = byId.get(connector.payload.to_object_id);
          if (!from || !to) return null;
          const fromX = from.position.x + from.dimensions.width / 2, fromY = from.position.y + from.dimensions.height / 2;
          const toX = to.position.x + to.dimensions.width / 2, toY = to.position.y + to.dimensions.height / 2;
          const vertical = Math.abs(toY - fromY) >= Math.abs(toX - fromX);
          const x1 = vertical ? fromX : fromX + Math.sign(toX - fromX) * from.dimensions.width / 2;
          const y1 = vertical ? fromY + Math.sign(toY - fromY) * from.dimensions.height / 2 : fromY;
          const x2 = vertical ? toX : toX - Math.sign(toX - fromX) * to.dimensions.width / 2;
          const y2 = vertical ? toY - Math.sign(toY - fromY) * to.dimensions.height / 2 : toY;
          return <g key={connector.id} aria-label={connector.label}>
            <line x1={x1} y1={y1} x2={x2} y2={y2} stroke={GREEN} strokeOpacity="0.6" strokeWidth="1.5" markerEnd={`url(#${markerId})`} />
            {connector.payload.relationship && <text x={(x1 + x2) / 2 + 5} y={(y1 + y2) / 2 - 7} fill={MUTED} fontSize="9" textAnchor="middle">{String(connector.payload.relationship)}</text>}
          </g>;
        })}
        {objects.filter((object) => object.type !== 'connector').map((object) => {
          const { width, height } = object.dimensions, selected = object.id === selection, isFocused = focused.has(object.id);
          const plotRun = object.payload.run_id === activeRun?.run_id ? activeRun : retainedRuns[object.payload.run_id] || null;
          const plotRunMatches = object.type === 'plot_ref' && matchesPlot(object, plotRun);
          const quote = object.payload.kind === 'quote', tutorItem = object.payload.author === 'tutor';
          return <g key={object.id} data-object-id={object.id} className={isFocused ? 'board-focus' : undefined} transform={`translate(${object.position.x}, ${object.position.y})`}
            role="button" tabIndex={0} aria-label={`Inspect ${object.label}`} aria-pressed={selected}
            onClick={() => select(object)} onKeyDown={(event) => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); select(object); } }} style={{ cursor: 'pointer' }}>
            <title>{object.label}</title>
            <rect width={width} height={height} rx="12" fill={object.type === 'equation' ? '#e8f2ec' : quote ? '#f7f3e6' : '#fffefb'} stroke={selected ? GREEN : isFocused ? AMBER : LINE} strokeWidth={selected || isFocused ? 2 : 1} />
            {quote && <rect x="0" y="12" width="4" height={Math.max(0, height - 24)} rx="2" fill={AMBER} />}
            {object.type === 'equation' ? <foreignObject x="10" y="4" width={Math.max(1, width - 20)} height={Math.max(1, height - 8)}><Equation latex={String(object.payload.latex || '')} /></foreignObject>
              : object.type === 'plot_ref' ? plotRunMatches ? <RunChart run={plotRun} width={width} height={height} earlier={plotRun.run_id !== activeRun?.run_id} />
                : <foreignObject x="18" y="18" width={Math.max(1, width - 36)} height={Math.max(1, height - 36)}><div className="board-plot-placeholder">
                  <strong>{String(object.payload.title || object.label)}</strong><p>{object.payload.run_id ? `Earlier run ${String(object.payload.run_id).slice(0, 8)}` : 'No retained run attached'}</p>
                  <p>{object.payload.run_id ? 'Select this card to inspect its saved result.' : 'Run an experiment to inspect checked numerical output.'}</p>
                </div></foreignObject>
              : <foreignObject x={quote ? 16 : 10} y="7" width={Math.max(1, width - (quote ? 26 : 20))} height={Math.max(1, height - 14)}><div className={'board-node-content' + (tutorItem ? ' tutor-item' : '') + (quote ? ' board-quote' : '')}>
                <strong>{quote ? ['From the source', object.label].filter((part, index) => index === 0 || part !== 'From the source').join(' · ') : String(object.payload.title || object.label)}</strong>{object.payload.description && <p>{String(object.payload.description)}</p>}{object.payload.text && <p>{quote ? `“${String(object.payload.text)}”` : String(object.payload.text)}</p>}
              </div></foreignObject>}
          </g>;
        })}
      </svg> : <div className="board-empty"><span className="board-kicker">A SPACE TO THINK</span><h3>Your next idea starts here.</h3><p>Choose a passage from your source to begin a visual lesson.</p></div>}
    </div>
    <div className="board-toolbar"><span>{objects.filter((object) => object.type !== 'connector').length} objects · Select a card to inspect it</span><div className="board-view-controls" role="group" aria-label="Whiteboard view"><button type="button" aria-label="Fit board to panel" aria-pressed={!readableSize} onClick={() => setReadableSize(false)}>Fit</button><button type="button" aria-label="View board at readable size" aria-pressed={readableSize} onClick={() => setReadableSize(true)}>Readable size</button></div></div>
    {selectedObject && <div className="board-detail" aria-live="polite"><strong>{selectedObject.label}</strong>
      {selectedObject.type === 'equation' ? <Equation latex={String(selectedObject.payload.latex || '')} /> : <p>{String(selectedObject.payload.description || selectedObject.payload.text || selectedObject.payload.title || selectedObject.label)}</p>}
      {selectedObject.concept_id && <span>Concept: {selectedObject.concept_id.replaceAll('_', ' ')}</span>}
      {selectedObject.type === 'plot_ref' && retainedRuns[selectedObject.payload.run_id] && <p>{runSummary(retainedRuns[selectedObject.payload.run_id])}</p>}
      {lookupError && <p role="status">{lookupError}</p>}
    </div>}
    {checked && !sceneHasCurrentRun && <div className="board-current-run"><div className="board-current-run-header"><span className="board-kicker">MEASURED OBSERVATION</span><span className="board-status">{isStale ? 'Earlier inputs' : 'Current run'} · {activeRun.run_id.slice(0, 8)}</span></div>
      <div className="board-current-run-scroll"><svg viewBox="0 0 620 300" className="board-current-chart" style={readableSize ? { minWidth: '620px' } : undefined} aria-label="Current experiment output"><RunChart run={activeRun} width={620} height={300} /></svg></div>
    </div>}
    {checked && (!sceneHasCurrentRun || objects.some((object) => object.type === 'plot_ref' && object.payload.run_id === activeRun.run_id)) && <details className="board-data-summary"><summary>Read chart values · run {activeRun.run_id.slice(0, 8)}{isStale ? ' · Earlier inputs' : ''}</summary><p>{runSummary(activeRun)}</p></details>}
    {activeRun && !checked && <p className="board-detail" role="status">Experiment {activeRun.status}. Checked numerical output is not available for this run.</p>}
  </div>;
};
