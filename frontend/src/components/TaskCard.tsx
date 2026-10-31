import { useEffect, useState } from 'react';
import type { ActiveTask, TutorStep, WebSource } from '../types';
import { Icon } from './Icon';
import { InlineMarkdown, Markdown } from './Markdown';

interface TaskCardProps {
  task: ActiveTask | null;
  onSubmitAnswer: (answer: string) => Promise<boolean>;
  onAskQuestion: (message: string) => Promise<boolean>;
  onRequestHint: () => Promise<boolean>;
  isLoading: boolean;
  working?: boolean;
  steps: TutorStep[];
  stepIndex: number;
  onStepChange: (index: number) => void;
  webSources: WebSource[];
  hasSession: boolean;
}
const TAG_LABELS: Record<string, string> = { source: 'Source', background: 'Background', web: 'Web', experiment: 'Experiment', interpretation: 'Interpretation', assumption: 'Assumption' };
const HINTS: Record<string, string> = {
  vector: 'Work out each entry, then check whether the weights add to one. Enter the values separated by commas.',
  number: 'Write down the operation first. Calculate one step at a time, then check your units and the source.',
  choice: 'Rule out each option the board, the source, or the experiment contradicts. Then choose what remains.',
};
function hostname(url: string) {
  try { return new URL(url).hostname.replace(/^www\./, ''); } catch { return url; }
}

function LessonPager({ steps, stepIndex, onStepChange, webSources, hasTask }: { steps: TutorStep[]; stepIndex: number; onStepChange: (index: number) => void; webSources: WebSource[]; hasTask: boolean }) {
  const index = Math.min(stepIndex, steps.length - 1), step = steps[index], last = index === steps.length - 1;
  return <section className="tutor-speech lesson-pager" aria-label="Lesson steps" aria-roledescription="carousel"
    onKeyDown={event => { if (event.key === 'ArrowRight' && !last) onStepChange(index + 1); if (event.key === 'ArrowLeft' && index > 0) onStepChange(index - 1); }}>
    <div className="pager-head"><span className="eyebrow">STEP {index + 1} OF {steps.length}</span><span className={'epistemic-badge ' + step.tag + '-tag'}>{TAG_LABELS[step.tag] || 'Background'}</span></div>
    <div aria-live="polite">
      <h3 className="step-title"><InlineMarkdown text={step.title}/></h3>
      <div className="tutor-body"><Markdown text={step.body}/></div>
      {step.url && <p className="step-cite"><a href={step.url} target="_blank" rel="noopener noreferrer"><Icon name="book" size={12}/>{hostname(step.url)}</a></p>}
      {!step.url && step.anchor_id && <p className="step-cite"><Icon name="book" size={12}/>Quoted from your selected passage</p>}
    </div>
    {steps.length > 1 || hasTask ? <div className="pager-nav">
      <button type="button" className="text-button" onClick={() => onStepChange(index - 1)} disabled={index === 0}>Back</button>
      <div className="pager-dots">{steps.map((item, dot) => <button type="button" key={dot} className={'pager-dot' + (dot === index ? ' active' : dot < index ? ' seen' : '')} aria-label={`Step ${dot + 1}: ${item.title}`} aria-current={dot === index ? 'step' : undefined} onClick={() => onStepChange(dot)}/>)}</div>
      {!last ? <button type="button" className="secondary-button pager-next" onClick={() => onStepChange(index + 1)}>Next<Icon name="arrow" size={14}/></button>
        : hasTask ? <button type="button" className="secondary-button pager-next" onClick={() => (window.document.querySelector<HTMLElement>('#task-answer, .choice-option input'))?.focus()}>Your turn<Icon name="arrow" size={14}/></button> : <span className="pager-spacer"/>}
    </div> : null}
    {webSources.length > 0 && <details className="web-sources"><summary>Web pages the tutor read ({webSources.length})</summary><ul>{webSources.map(source => <li key={source.url}><a href={source.url} target="_blank" rel="noopener noreferrer">{source.title || hostname(source.url)}</a> <span>{hostname(source.url)}</span></li>)}</ul></details>}
  </section>;
}

function TutorWorking() {
  const [seconds, setSeconds] = useState(0);
  useEffect(() => {
    const timer = window.setInterval(() => setSeconds(value => value + 1), 1000);
    return () => window.clearInterval(timer);
  }, []);
  return <p className="tutor-working" role="status"><span className="dot working"/>The tutor is reading your pages and writing an answer… {seconds > 0 && <span>{seconds} s</span>}</p>;
}

export function TaskCard({ task, onSubmitAnswer, onAskQuestion, onRequestHint, isLoading, working, steps, stepIndex, onStepChange, webSources, hasSession }: TaskCardProps) {
  const [answer, setAnswer] = useState('');
  const [question, setQuestion] = useState('');
  const [showStrategy, setShowStrategy] = useState(false);
  const hint = HINTS[task?.expected_type || ''] || 'Trace what each object contributes. Use the source and the whiteboard to support your answer.';
  const choices = task?.expected_type === 'choice' ? task.choices || [] : [];
  return <div className="task-card">
    <div className="task-card-header"><div className="title-row"><span className="tutor-icon"><Icon name="spark" size={17}/></span><h2>Your thinking, next</h2></div><span className="paper-badge">{task ? 'YOUR TURN' : 'LET’S EXPLORE'}</span></div>
    {working && <TutorWorking/>}
    {steps.length > 0 && <LessonPager steps={steps} stepIndex={stepIndex} onStepChange={onStepChange} webSources={webSources} hasTask={Boolean(task)}/>}
    {task ? <div className="task-content"><span className="eyebrow">CHECK YOUR UNDERSTANDING</span><p className="task-prompt"><InlineMarkdown text={task.question}/></p><form onSubmit={async event => { event.preventDefault(); if (!answer.trim() || isLoading) return; await onSubmitAnswer(answer.trim()); }}>
      {choices.length ? <><fieldset className="choice-group" disabled={isLoading}><legend className="visually-hidden">Choose an answer</legend>{choices.map(choice => <label key={choice} className={'choice-option' + (answer === choice ? ' selected' : '')}><input type="radio" name="task-choice" value={choice} checked={answer === choice} onChange={() => setAnswer(choice)}/><span><InlineMarkdown text={choice}/></span></label>)}</fieldset><button className="primary-button choice-submit" type="submit" disabled={isLoading || !answer}>{isLoading ? 'Thinking…' : 'Check my thinking'}<Icon name="arrow" size={16}/></button></>
        : <><label className="visually-hidden" htmlFor="task-answer">Your answer</label><div className="input-group"><input id="task-answer" name="answer" placeholder={task.expected_type === 'vector' ? 'e.g. 0.5, 0.5' : task.expected_type === 'number' ? 'Your calculation…' : 'Explain your answer…'} value={answer} onChange={event => setAnswer(event.target.value)} disabled={isLoading} autoComplete="off" required/><button className="primary-button" type="submit" disabled={isLoading || !answer.trim()}>{isLoading ? 'Thinking…' : 'Check my thinking'}<Icon name="arrow" size={16}/></button></div></>}
    </form><button className="text-button hint-button" onClick={async () => { if (showStrategy) setShowStrategy(false); else if (await onRequestHint()) setShowStrategy(true); }} disabled={isLoading} aria-expanded={showStrategy}>{showStrategy ? 'Hide strategy' : 'A little help getting started?'}<Icon name="chevron" size={13}/></button>{showStrategy && <p className="task-hint-box"><span className="eyebrow">A STRATEGY, NOT AN ANSWER</span>{hint}</p>}</div>
      : <p className="no-task-msg">{hasSession ? 'Explore a lab, or ask about a connection on the board.' : 'The tutor will meet you here with a question, a drawing, and a next step shaped by your work.'}</p>}
    {hasSession && <form className="ask-form" onSubmit={async event => { event.preventDefault(); if (!question.trim() || isLoading) return; if (await onAskQuestion(question.trim())) setQuestion(''); }}><label htmlFor="tutor-question">Something still unclear?</label><div className="input-group"><input id="tutor-question" placeholder="Ask about this idea…" value={question} onChange={event => setQuestion(event.target.value)} maxLength={1000} required disabled={isLoading}/><button className="icon-button" aria-label="Ask the tutor" type="submit" disabled={isLoading || !question.trim()}><Icon name="arrow" size={18}/></button></div></form>}
  </div>;
}
