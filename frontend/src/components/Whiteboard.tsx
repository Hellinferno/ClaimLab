import React, { useMemo } from 'react';
import katex from 'katex';
import type { BoardObject, SceneGraph, ExperimentRun } from '../types';

interface WhiteboardProps {
  scene: SceneGraph;
  activeRun: ExperimentRun | null;
  onSelectObject?: (obj: BoardObject) => void;
  selectedObjectId?: string | null;
}

export const Whiteboard: React.FC<WhiteboardProps> = ({
  scene,
  activeRun,
  onSelectObject,
  selectedObjectId,
}) => {
  const renderedObjects = useMemo(() => scene.objects || [], [scene]);

  return (
    <div className="whiteboard-container">
      <div className="whiteboard-header">
        <div className="whiteboard-title">
          <span className="dot active" />
          <span>Shared Whiteboard (Rev {scene.board_revision})</span>
        </div>
        <span className="object-count">{renderedObjects.length} active objects</span>
      </div>

      <svg
        viewBox="0 0 780 360"
        className="whiteboard-canvas"
        style={{ width: '100%', height: '360px', background: '#0f172a' }}
      >
        <defs>
          <marker
            id="arrow"
            viewBox="0 0 10 10"
            refX="6"
            refY="5"
            markerWidth="6"
            markerHeight="6"
            orient="auto-start-reverse"
          >
            <path d="M 0 0 L 10 5 L 0 10 z" fill="#64748b" />
          </marker>
        </defs>

        {/* Connectors / Edges */}
        {renderedObjects
          .filter((o) => o.type === 'connector')
          .map((c) => {
            const p = c.payload || {};
            const fromObj = renderedObjects.find((o) => o.id === p.from_object_id);
            const toObj = renderedObjects.find((o) => o.id === p.to_object_id);
            if (!fromObj || !toObj) return null;

            const x1 = fromObj.position.x + fromObj.dimensions.width / 2;
            const y1 = fromObj.position.y + fromObj.dimensions.height / 2;
            const x2 = toObj.position.x + toObj.dimensions.width / 2;
            const y2 = toObj.position.y + toObj.dimensions.height / 2;

            return (
              <g key={c.id}>
                <line
                  x1={x1}
                  y1={y1}
                  x2={x2}
                  y2={y2}
                  stroke="#64748b"
                  strokeWidth="2"
                  strokeDasharray="4 2"
                  markerEnd="url(#arrow)"
                />
                {p.relationship && (
                  <text
                    x={(x1 + x2) / 2}
                    y={(y1 + y2) / 2 - 8}
                    fill="#94a3b8"
                    fontSize="11"
                    textAnchor="middle"
                  >
                    {p.relationship}
                  </text>
                )}
              </g>
            );
          })}

        {/* Concept Nodes, Equations, Plot Refs */}
        {renderedObjects
          .filter((o) => o.type !== 'connector')
          .map((obj) => {
            const isSelected = selectedObjectId === obj.id;
            const { x, y } = obj.position;
            const { width, height } = obj.dimensions;

            if (obj.type === 'equation') {
              let html = '';
              try {
                html = katex.renderToString(obj.payload.latex || '', {
                  displayMode: true,
                  throwOnError: false,
                });
              } catch {
                html = obj.payload.latex || '';
              }

              return (
                <g
                  key={obj.id}
                  transform={`translate(${x}, ${y})`}
                  onClick={() => onSelectObject?.(obj)}
                  style={{ cursor: 'pointer' }}
                >
                  <rect
                    width={width}
                    height={height}
                    rx="8"
                    fill="#1e293b"
                    stroke={isSelected ? '#38bdf8' : '#334155'}
                    strokeWidth={isSelected ? 2 : 1}
                  />
                  <foreignObject width={width} height={height}>
                    <div
                      style={{
                        color: '#f8fafc',
                        padding: '10px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        height: '100%',
                        fontSize: '13px',
                      }}
                      dangerouslySetInnerHTML={{ __html: html }}
                    />
                  </foreignObject>
                </g>
              );
            }

            if (obj.type === 'plot_ref') {
              // Plot Reference rendered from actual run JSON output
              const runResults = activeRun?.output?.results || [];
              const maxVar = 140;

              return (
                <g
                  key={obj.id}
                  transform={`translate(${x}, ${y})`}
                  onClick={() => onSelectObject?.(obj)}
                  style={{ cursor: 'pointer' }}
                >
                  <rect
                    width={width}
                    height={height}
                    rx="8"
                    fill="#1e293b"
                    stroke={isSelected ? '#38bdf8' : '#334155'}
                    strokeWidth={isSelected ? 2 : 1}
                  />
                  <text x="14" y="24" fill="#38bdf8" fontSize="13" fontWeight="bold">
                    {obj.payload.title || 'Score Variance Plot'}
                  </text>
                  <text x="14" y="40" fill="#64748b" fontSize="10">
                    Run ID: {activeRun?.run_id?.slice(0, 8) || 'active'} | seed: {activeRun?.seed ?? 42}
                  </text>

                  {/* Chart axes */}
                  <line x1="40" y1="210" x2="290" y2="210" stroke="#475569" strokeWidth="1" />
                  <line x1="40" y1="60" x2="40" y2="210" stroke="#475569" strokeWidth="1" />
                  <text x="40" y="226" fill="#94a3b8" fontSize="10">d_k: 8</text>
                  <text x="150" y="226" fill="#94a3b8" fontSize="10">32</text>
                  <text x="260" y="226" fill="#94a3b8" fontSize="10">128</text>
                  <text x="14" y="65" fill="#94a3b8" fontSize="9">Var</text>

                  {/* Unscaled line (red) and Scaled line (green) */}
                  {runResults.length > 0 ? (
                    <>
                      {/* Unscaled line */}
                      <polyline
                        fill="none"
                        stroke="#f43f5e"
                        strokeWidth="2.5"
                        points={runResults
                          .map((r: any, idx: number) => {
                            const px = 60 + idx * 100;
                            const py = 210 - Math.min(150, (r.unscaled_variance / maxVar) * 150);
                            return `${px},${py}`;
                          })
                          .join(' ')}
                      />
                      {/* Scaled line */}
                      <polyline
                        fill="none"
                        stroke="#10b981"
                        strokeWidth="2.5"
                        points={runResults
                          .map((r: any, idx: number) => {
                            const px = 60 + idx * 100;
                            const py = 210 - Math.min(150, (r.scaled_variance / 2.0) * 15);
                            return `${px},${py}`;
                          })
                          .join(' ')}
                      />
                      {/* Legend */}
                      <circle cx="160" cy="72" r="4" fill="#f43f5e" />
                      <text x="170" y="76" fill="#f43f5e" fontSize="11">Unscaled Var</text>
                      <circle cx="240" cy="72" r="4" fill="#10b981" />
                      <text x="250" y="76" fill="#10b981" fontSize="11">Scaled Var (~1.0)</text>
                    </>
                  ) : (
                    <text x="90" y="140" fill="#64748b" fontSize="12">
                      Run experiment to view curve
                    </text>
                  )}
                </g>
              );
            }

            // Default: Concept Node / Box
            return (
              <g
                key={obj.id}
                transform={`translate(${x}, ${y})`}
                onClick={() => onSelectObject?.(obj)}
                style={{ cursor: 'pointer' }}
              >
                <rect
                  width={width}
                  height={height}
                  rx="6"
                  fill="#1e293b"
                  stroke={isSelected ? '#38bdf8' : '#475569'}
                  strokeWidth={isSelected ? 2 : 1}
                />
                <text x="14" y="24" fill="#f1f5f9" fontSize="13" fontWeight="600">
                  {obj.payload.title || obj.label}
                </text>
                {obj.payload.description && (
                  <text x="14" y="44" fill="#94a3b8" fontSize="11">
                    {obj.payload.description}
                  </text>
                )}
              </g>
            );
          })}
      </svg>
    </div>
  );
};
