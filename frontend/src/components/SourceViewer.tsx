import React, { useState } from 'react';
import type { DocumentStatus, SourceAnchor, DocumentPageDetail } from '../types';

interface SourceViewerProps {
  document: DocumentStatus | null;
  pages?: DocumentPageDetail[];
  anchors: SourceAnchor[];
  onSelectAnchor?: (anchor: SourceAnchor) => void;
  selectedAnchorId?: string | null;
  onUploadFile?: (file: File) => Promise<void>;
  isUploading?: boolean;
}

export const SourceViewer: React.FC<SourceViewerProps> = ({
  document,
  pages = [],
  anchors,
  onSelectAnchor,
  selectedAnchorId,
  onUploadFile,
  isUploading = false,
}) => {
  const [activePageNum, setActivePageNum] = useState<number>(2); // Default to Page 2 (Attention Scaling)

  const currentPageDetail = pages.find((p) => p.page_number === activePageNum);
  const pageAnchors = anchors.filter((a) => a.page_number === activePageNum);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0] && onUploadFile) {
      await onUploadFile(e.target.files[0]);
    }
  };

  return (
    <div className="panel source-panel">
      <div className="panel-header">
        <div className="title-row">
          <span className="icon">📄</span>
          <h3>Source Grounding</h3>
        </div>
        <div className="source-actions">
          {document && (
            <span className="badge success">
              {document.filename} ({document.page_count}p)
            </span>
          )}
          <label className="upload-btn" title="Upload custom PDF document">
            <span>{isUploading ? 'Uploading...' : '📁 Upload PDF'}</span>
            <input
              type="file"
              accept=".pdf"
              onChange={handleFileChange}
              disabled={isUploading}
              style={{ display: 'none' }}
            />
          </label>
        </div>
      </div>

      {/* Page Tabs */}
      <div className="page-tabs">
        {[1, 2, 3].map((num) => (
          <button
            key={num}
            className={`page-tab ${activePageNum === num ? 'active' : ''}`}
            onClick={() => setActivePageNum(num)}
          >
            Page {num}: {num === 1 ? 'Softmax' : num === 2 ? 'Attention' : 'Causal'}
          </button>
        ))}
      </div>

      {/* Page Content & Anchors */}
      <div className="source-content">
        <div className="section-summary">
          {currentPageDetail?.normalized_text ? (
            <div className="source-body">
              <h4>Extracted Document Text (Page {activePageNum})</h4>
              <p className="extracted-text">{currentPageDetail.normalized_text}</p>
            </div>
          ) : (
            <div className="source-body">
              {activePageNum === 1 && (
                <>
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
                </>
              )}

              {activePageNum === 2 && (
                <>
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
                </>
              )}

              {activePageNum === 3 && (
                <>
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
                </>
              )}
            </div>
          )}
        </div>

        {/* Grounding Anchors List */}
        <div className="anchors-container">
          <div className="anchors-header">
            <h5>Verified Grounding Anchors (Page {activePageNum})</h5>
            <span className="anchor-count">{pageAnchors.length} anchors</span>
          </div>

          {pageAnchors.length === 0 ? (
            <p className="dimmed">No active anchors on page {activePageNum}.</p>
          ) : (
            <div className="anchors-list">
              {pageAnchors.map((anc) => (
                <div
                  key={anc.id}
                  className={`anchor-item ${selectedAnchorId === anc.id ? 'selected' : ''}`}
                  onClick={() => onSelectAnchor?.(anc)}
                >
                  <div className="anchor-tag-row">
                    <span className="anchor-tag">#{anc.id}</span>
                    <span className="anchor-offsets">
                      chars {anc.start_offset}&ndash;{anc.end_offset}
                    </span>
                  </div>
                  <p className="anchor-quote">&ldquo;{anc.quote}&rdquo;</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
