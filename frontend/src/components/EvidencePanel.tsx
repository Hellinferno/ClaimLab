import React from 'react';
import type { EvidenceCategory } from '../types';

interface EvidencePanelProps {
  evidenceSummary: Record<string, EvidenceCategory>;
}

const CONCEPTS = [
  { id: 'attention_scaling', name: 'Attention Scaling (1/√d_k)' },
  { id: 'query_key_scores', name: 'Query-Key Dot Products' },
  { id: 'softmax_normalization', name: 'Softmax Normalization' },
  { id: 'causal_masking', name: 'Causal Lower-Triangular Mask' },
];

export const EvidencePanel: React.FC<EvidencePanelProps> = ({ evidenceSummary }) => {
  const getBadgeClass = (cat?: EvidenceCategory) => {
    switch (cat) {
      case 'supported_independently':
        return 'badge-green';
      case 'supported_with_help':
        return 'badge-purple';
      case 'needs_check':
        return 'badge-orange';
      case 'introduced':
        return 'badge-blue';
      default:
        return 'badge-grey';
    }
  };

  const getLabel = (cat?: EvidenceCategory) => {
    switch (cat) {
      case 'supported_independently':
        return 'Supported Independently';
      case 'supported_with_help':
        return 'Supported with Help';
      case 'needs_check':
        return 'Needs Check';
      case 'introduced':
        return 'Introduced';
      default:
        return 'Not Assessed';
    }
  };

  return (
    <div className="panel evidence-panel">
      <div className="panel-header">
        <div className="title-row">
          <span className="icon">📊</span>
          <h3>Learning Observation Record</h3>
        </div>
      </div>

      <p className="evidence-intro">
        Categorical progression updated dynamically from student actions and verified numerical checks.
      </p>

      <div className="concept-grid">
        {CONCEPTS.map((c) => {
          const status = evidenceSummary[c.id];
          return (
            <div key={c.id} className="concept-card">
              <span className="concept-name">{c.name}</span>
              <span className={`status-pill ${getBadgeClass(status)}`}>
                {getLabel(status)}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
};
