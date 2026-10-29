import { lazy, Suspense, useState } from 'react';
import type { ActiveTask } from '../types';
import { Icon } from './Icon';

const LazyMathText = lazy(() => import('./Math').then(module => ({ default: module.MathText })));

interface TaskCardProps {
  task: ActiveTask | null;
  onSubmitAnswer: (answer: string) => Promise<boolean>;
  onAskQuestion: (message: string) => Promise<boolean>;
  onRequestHint: () => Promise<boolean>;
  isLoading: boolean;
  tutorNarration?: string;
  hasSession: boolean;
}
function MathText({ text }: { text: string }) {
  return text.split(/(\$[^$]+\$)/g).map((part, index) => {
    if (part.startsWith('$') && part.endsWith('$')) {
      return <Suspense key={index} fallback={<span>{part}</span>}><LazyMathText formula={part.slice(1, -1)}/></Suspense>;
    }
    return <span key={index}>{part}</span>;
  });
}
export function TaskCard({ task, onSubmitAnswer, onAskQuestion, onRequestHint, isLoading, tutorNarration, hasSession }: TaskCardProps) {
  const [answer, setAnswer] = useState('');
  const [question, setQuestion] = useState('');
  const [showStrategy, setShowStrategy] = useState(false);
  const hint = task?.expected_type === 'vector' ? 'Work out each entry, then check whether the weights add to one. Enter the values separated by commas.' : task?.expected_type === 'number' ? 'Write down the operation first. Calculate one step at a time, then check your units and the source.' : 'Trace what each object contributes to the operation. Use the source and whiteboard to support your answer.';
  return <div className="task-card">
    <div className="task-card-header"><div className="title-row"><span className="tutor-icon"><Icon name="spark" size={17}/></span><h2>Your thinking, next</h2></div><span className="paper-badge">{task ? 'YOUR TURN' : 'LET’S EXPLORE'}</span></div>
    {tutorNarration && <div className="tutor-speech" aria-live="polite"><span className="eyebrow">A NOTE FROM YOUR TUTOR</span><div className="tutor-body">{tutorNarration.split('\n').filter(Boolean).map((line, index) => {
      const tag = line.match(/^\[(Source|Background|Assumption|Observation|Interpretation|Experiment)\]\s*/i);
      return <p key={index} className="narration-line">{tag && <span className={'epistemic-badge ' + tag[1].toLowerCase() + '-tag'}>{tag[1]}</span>}<MathText text={tag ? line.slice(tag[0].length) : line}/></p>;
    })}</div></div>}
    {task ? <div className="task-content"><p className="task-prompt"><MathText text={task.question}/></p><form onSubmit={async event => { event.preventDefault(); if (!answer.trim() || isLoading) return; await onSubmitAnswer(answer.trim()); }}><label className="visually-hidden" htmlFor="task-answer">Your answer</label><div className="input-group"><input id="task-answer" name="answer" placeholder={task.expected_type === 'vector' ? 'e.g. 0.5, 0.5' : task.expected_type === 'number' ? 'Your calculation…' : 'Explain your answer…'} value={answer} onChange={event => setAnswer(event.target.value)} disabled={isLoading} autoComplete="off" required/><button className="primary-button" type="submit" disabled={isLoading || !answer.trim()}>{isLoading ? 'Thinking…' : 'Check my thinking'}<Icon name="arrow" size={16}/></button></div></form><button className="text-button hint-button" onClick={async () => { if (showStrategy) setShowStrategy(false); else if (await onRequestHint()) setShowStrategy(true); }} disabled={isLoading} aria-expanded={showStrategy}>{showStrategy ? 'Hide strategy' : 'A little help getting started?'}<Icon name="chevron" size={13}/></button>{showStrategy && <p className="task-hint-box"><span className="eyebrow">A STRATEGY, NOT AN ANSWER</span>{hint}</p>}</div> : <p className="no-task-msg">{hasSession ? 'Explore a lab, or ask about a connection on the board.' : 'The tutor will meet you here with a question, a drawing, and a next step shaped by your work.'}</p>}
    {hasSession && <form className="ask-form" onSubmit={async event => { event.preventDefault(); if (!question.trim() || isLoading) return; if (await onAskQuestion(question.trim())) setQuestion(''); }}><label htmlFor="tutor-question">Something still unclear?</label><div className="input-group"><input id="tutor-question" placeholder="Ask about this idea…" value={question} onChange={event => setQuestion(event.target.value)} maxLength={1000} required disabled={isLoading}/><button className="icon-button" aria-label="Ask the tutor" type="submit" disabled={isLoading || !question.trim()}><Icon name="arrow" size={18}/></button></div></form>}
  </div>;
}
