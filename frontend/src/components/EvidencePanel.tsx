import React from 'react';
import type { EvidenceCategory } from '../types';
import { Icon } from './Icon';

interface EvidencePanelProps {
  evidenceSummary: Record<string, EvidenceCategory>;
}

const CONCEPTS = [
  { id: 'attention_scaling', name: 'Attention scaling' },
  { id: 'query_key_scores', name: 'Queries & keys' },
  { id: 'softmax_normalization', name: 'Softmax normalization' },
  { id: 'softmax_score_scale', name: 'Score sensitivity' },
  { id: 'value_weighted_sum', name: 'Weighted values' },
  { id: 'causal_masking', name: 'Causal masking' },
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
      case 'needs_revisit':
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
        return 'Independent evidence';
      case 'supported_with_help':
        return 'With help';
      case 'needs_check':
        return 'Let’s check';
      case 'needs_revisit':
        return 'Revisit';
      case 'introduced':
        return 'Introduced';
      default:
        return 'Not explored';
    }
  };

  return (
    <div className="panel evidence-panel">
      <div className="panel-header">
        <div className="title-row">
          <Icon name="chart" size={17}/>
          <h2>Your learning trail</h2>
        </div>
      </div>

      <p className="evidence-intro">
        A picture of your thinking, shaped by your attempts. There’s no score to chase.
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
      <p className="evidence-note">One answer is a starting point. New examples help check what carries over.</p>
    </div>
  );
};
