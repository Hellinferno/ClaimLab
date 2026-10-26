import React, { useState } from 'react';
import type { DocumentStatus, SourceAnchor } from '../types';

interface SourceViewerProps {
  document: DocumentStatus | null;
  anchors: SourceAnchor[];
  onSelectAnchor?: (anchor: SourceAnchor) => void;
  selectedAnchorId?: string | null;
}

export const SourceViewer: React.FC<SourceViewerProps> = ({
  document,
  anchors,
  onSelectAnchor,
  selectedAnchorId,
}) => {
  const [activePage, setActivePage] = useState<number>(2); // Default to Section B (page 2)

  const pageAnchors = anchors.filter((a) => a.page_number === activePage);

  return (
    <div className="panel source-panel">
      <div className="panel-header">
        <div className="title-row">
          <span className="icon">📄</span>
          <h3>Source Material</h3>
        </div>
        {document && (
          <span className="badge success">
            {document.filename} ({document.page_count} pages)
          </span>
        )}
      </div>

      {/* Page Tabs */}
      <div className="page-tabs">
        <button
          className={`page-tab ${activePage === 1 ? 'active' : ''}`}
          onClick={() => setActivePage(1)}
        >
          Page 1: Softmax
        </button>
        <button
          className={`page-tab ${activePage === 2 ? 'active' : ''}`}
          onClick={() => setActivePage(2)}
        >
          Page 2: Attention
        </button>
        <button
          className={`page-tab ${activePage === 3 ? 'active' : ''}`}
          onClick={() => setActivePage(3)}
        >
          Page 3: Causal Masking
        </button>
      </div>

      {/* Page Content & Anchors */}
      <div className="source-content">
        <div className="section-summary">
          {activePage === 1 && (
            <div className="source-body">
              <h4>Section A: From scores to weights</h4>
              <p>
                Softmax turns a finite vector of scores into nonnegative weights summing to one.
                Increasing all scores by the same amount preserves the weights. Multiplying unequal scores
                changes their relative influence. Equal scores receive equal weights.
              </p>
              <p>
                A numerical investigation can compare score vectors before and after multiplication.
                Its inputs and results should be visible so the learner can explain the relationship
                rather than memorize a picture.
              </p>
            </div>
          )}

          {activePage === 2 && (
            <div className="source-body">
              <h4>Section B: Attention ingredients</h4>
              <p>
                In a small attention example, a query is compared with keys to produce scores.
                A normalization step produces weights. Those weights combine values to produce an output.
                The objects participating in scoring and those contributing output information have different roles.
              </p>
              <p>
                A synthetic dot-product experiment can investigate the effect of score scaling under stated
                assumptions. Synthetic vectors do not represent a trained model's learned behavior or
                reproduce a translation benchmark.
              </p>
            </div>
          )}

          {activePage === 3 && (
            <div className="source-body">
              <h4>Section C: Which positions may contribute?</h4>
              <p>
                In a causal attention illustration, a position can use its current and earlier positions
                while future positions are excluded. A mask changes which entries contribute before
                row-wise normalization. Each row in this example retains at least one allowed entry.
              </p>
              <p>
                This explains one operation. A full language-model training procedure includes additional
                design choices and should not be inferred from the illustration alone.
              </p>
            </div>
          )}
        </div>

        {/* Anchors List */}
        <div className="anchors-container">
          <h5>Grounding Anchors on Page {activePage}</h5>
          {pageAnchors.length === 0 ? (
            <p className="dimmed">Loading anchors for page {activePage}...</p>
          ) : (
            <div className="anchors-list">
              {pageAnchors.map((anc) => (
                <div
                  key={anc.id}
                  className={`anchor-item ${selectedAnchorId === anc.id ? 'selected' : ''}`}
                  onClick={() => onSelectAnchor?.(anc)}
                >
                  <span className="anchor-tag">{anc.id}</span>
                  <p className="anchor-quote">“{anc.quote}”</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
