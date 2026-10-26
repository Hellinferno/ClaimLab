import React, { useState } from 'react';
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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!answer.trim() || isLoading) return;
    await onSubmitAnswer(answer);
    setAnswer('');
  };

  return (
    <div className="task-card">
      <div className="task-card-header">
        <span className="task-badge">Interactive Task</span>
        {task && <span className="variant-tag">{task.task_id} ({task.task_variant})</span>}
      </div>

      {/* Tutor Explanation / Feedback */}
      {tutorNarration && (
        <div className="tutor-speech">
          <div className="tutor-avatar">🤖</div>
          <div className="tutor-message">
            <strong>ClaimLab Tutor:</strong>
            <p>{tutorNarration}</p>
          </div>
        </div>
      )}

      {task ? (
        <form onSubmit={handleSubmit} className="task-form">
          <p className="task-prompt">{task.question}</p>
          <div className="input-group">
            <input
              type="text"
              placeholder="Enter your calculation or prediction..."
              value={answer}
              onChange={(e) => setAnswer(e.target.value)}
              disabled={isLoading}
              className="task-input"
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
      ) : (
        <p className="no-task-msg">No active task at this step. Feel free to explore the whiteboard or run an experiment!</p>
      )}
    </div>
  );
};
