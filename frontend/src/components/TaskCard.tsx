import React, { useState } from 'react';
import katex from 'katex';
import type { ActiveTask } from '../types';

interface TaskCardProps {
  task: ActiveTask | null;
  onSubmitAnswer: (answer: string) => Promise<void>;
  isLoading: boolean;
  tutorNarration?: string;
}

export const TaskCard: React.FC<TaskCardProps> = ({
  task,
  onSubmitAnswer,
  isLoading,
  tutorNarration,
}) => {
  const [answer, setAnswer] = useState<string>('');
  const [showHint, setShowHint] = useState<boolean>(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!answer.trim() || isLoading) return;
    await onSubmitAnswer(answer);
    setAnswer('');
    setShowHint(false);
  };

  const handleSelectChoice = async (val: string) => {
    if (isLoading) return;
    setAnswer(val);
    await onSubmitAnswer(val);
    setAnswer('');
    setShowHint(false);
  };

  // Helper to render mixed text with LaTeX ($...$)
  const renderMathText = (text: string) => {
    if (!text) return null;
    const parts = text.split(/(\$[^$]+\$)/g);
    return parts.map((part, index) => {
      if (part.startsWith('$') && part.endsWith('$')) {
        const formula = part.slice(1, -1);
        try {
          const html = katex.renderToString(formula, { throwOnError: false });
          return <span key={index} dangerouslySetInnerHTML={{ __html: html }} />;
        } catch {
          return <span key={index}>{part}</span>;
        }
      }
      return <span key={index}>{part}</span>;
    });
  };

  // Format tutor narration with epistemic badge highlighting
  const renderNarration = (narration: string) => {
    const lines = narration.split('\n');
    return lines.map((line, idx) => {
      let tagBadge = null;
      let cleanLine = line;

      if (line.startsWith('[Source]')) {
        tagBadge = <span className="epistemic-badge source-tag">[Source Grounded]</span>;
        cleanLine = line.replace('[Source]', '').trim();
      } else if (line.startsWith('[Experiment]')) {
        tagBadge = <span className="epistemic-badge experiment-tag">[Numerical Experiment]</span>;
        cleanLine = line.replace('[Experiment]', '').trim();
      } else if (line.startsWith('[Background]')) {
        tagBadge = <span className="epistemic-badge background-tag">[Prior Concept]</span>;
        cleanLine = line.replace('[Background]', '').trim();
      }

      return (
        <p key={idx} className="narration-line">
          {tagBadge} {renderMathText(cleanLine)}
        </p>
      );
    });
  };

  const isChoiceTask = task?.expected_type === 'text_choice';

  return (
    <div className="task-card">
      <div className="task-card-header">
        <div className="task-meta">
          <span className="task-badge">Interactive Task</span>
          {task && (
            <span className="variant-tag">
              {task.task_id} &bull; variant {task.task_variant}
            </span>
          )}
        </div>
        {task && (
          <button
            type="button"
            className="hint-toggle-btn"
            onClick={() => setShowHint(!showHint)}
          >
            {showHint ? 'Hide Hint' : '💡 Need a Hint?'}
          </button>
        )}
      </div>

      {/* Tutor Explanation / Feedback with Epistemic Grounding Tags */}
      {tutorNarration && (
        <div className="tutor-speech">
          <div className="tutor-avatar">🤖</div>
          <div className="tutor-message">
            <strong className="tutor-name">ClaimLab Adaptive Tutor:</strong>
            <div className="tutor-body">{renderNarration(tutorNarration)}</div>
          </div>
        </div>
      )}

      {showHint && task && (
        <div className="task-hint-box">
          <span className="hint-label">Guided Scaffold:</span>
          <p>
            Recall: $\sqrt{'{d_k}'} = \sqrt{'{16}'} = 4$. Dividing the raw dot-product score by 4 yields the scaled score.
          </p>
        </div>
      )}

      {task ? (
        <div className="task-content">
          <div className="task-prompt">{renderMathText(task.question)}</div>

          {isChoiceTask ? (
            <div className="choice-buttons-grid">
              <button
                type="button"
                className="choice-btn"
                disabled={isLoading}
                onClick={() => handleSelectChoice('query and keys')}
              >
                Query & Keys (dot product matching)
              </button>
              <button
                type="button"
                className="choice-btn"
                disabled={isLoading}
                onClick={() => handleSelectChoice('weights and values')}
              >
                Weights & Values (weighted combination)
              </button>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="task-form">
              <div className="input-group">
                <input
                  type="text"
                  placeholder="Enter your calculation result..."
                  value={answer}
                  onChange={(e) => setAnswer(e.target.value)}
                  disabled={isLoading}
                  className="task-input"
                  autoFocus
                />
                <button
                  type="submit"
                  disabled={isLoading || !answer.trim()}
                  className="submit-task-btn"
                >
                  {isLoading ? 'Checking...' : 'Submit Answer'}
                </button>
              </div>
            </form>
          )}
        </div>
      ) : (
        <p className="no-task-msg">
          No active task at this step. Feel free to explore the whiteboard or run an experiment!
        </p>
      )}
    </div>
  );
};
