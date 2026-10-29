import { useEffect, useRef, useState } from 'react';
import type { DocumentStatus, DocumentPageDetail, SessionState, ExperimentRun, Me, SourceSelection } from './types';
import { Whiteboard } from './components/Whiteboard';
import { ExperimentPanel } from './components/ExperimentPanel';
import { SourceViewer } from './components/SourceViewer';
import { TaskCard } from './components/TaskCard';
import { EvidencePanel } from './components/EvidencePanel';
import { Icon } from './components/Icon';

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, options);
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = body?.error ?? body?.detail;
    const message = typeof detail === 'string' ? detail : detail?.message;
    throw new Error(message || (response.status === 422 ? 'Please check the inputs and try again.' : `The request could not finish (${response.status}). Please try again.`));
  }
  return body as T;
}
const errorMessage = (error: unknown) => error instanceof Error ? error.message : 'Something went wrong. Please try again.';

export default function App() {
  const [me, setMe] = useState<Me | null>(null);
  const [csrfToken, setCsrfToken] = useState('');
  const [document, setDocument] = useState<DocumentStatus | null>(null);
  const [docPages, setDocPages] = useState<DocumentPageDetail[]>([]);
  const [selection, setSelection] = useState<SourceSelection | null>(null);
  const [session, setSession] = useState<SessionState | null>(null);
  const [activeRun, setActiveRun] = useState<ExperimentRun | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [isStale, setIsStale] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [sourceNotice, setSourceNotice] = useState<string | null>(null);
  const [activePane, setActivePane] = useState('whiteboard');
  // StrictMode replays effects; bootstrap must not create duplicate owners or lessons.
  const didBootstrap = useRef(false);
  const operationInFlight = useRef(false);
  const headers = (json = true) => ({ ...(json ? { 'Content-Type': 'application/json' } : {}), 'X-CSRF-Token': csrfToken, 'Idempotency-Key': crypto.randomUUID() });

  async function loadDocument(documentId: string) {
    const [doc, pages] = await Promise.all([
      request<DocumentStatus>(`/api/v1/documents/${documentId}`),
      request<DocumentPageDetail[]>(`/api/v1/documents/${documentId}/pages`),
    ]);
    setDocument(doc); setDocPages(pages);
    return doc;
  }

  async function refreshSession(sessionId: string, restoreSource = false) {
    const next = await request<SessionState>(`/api/v1/learning-sessions/${sessionId}`);
    const run = next.latest_run_id ? await request<ExperimentRun>(`/api/v1/runs/${next.latest_run_id}`) : null;
    if (restoreSource && next.source_selection) {
      await loadDocument(next.source_selection.document_id);
      setSelection(next.source_selection);
    }
    setSession(next); setActiveRun(run);
    return next;
  }

  async function bootstrap() {
    try {
      setIsLoading(true); setErrorMsg(null);
      const guest = await request<{ csrf_token: string }>('/api/v1/guest-sessions', { method: 'POST' });
      setCsrfToken(guest.csrf_token);
      const [owner, active] = await Promise.all([
        request<Me>('/api/v1/me'),
        request<{ active_session_id: string | null }>('/api/v1/learning-sessions/active'),
      ]);
      setMe(owner);
      if (active.active_session_id) await refreshSession(active.active_session_id, true);
    } catch (error) { setErrorMsg(`Could not open your workspace. ${errorMessage(error)}`); }
    finally { setIsLoading(false); }
  }
  useEffect(() => {
    if (!didBootstrap.current) { didBootstrap.current = true; void bootstrap(); }
  }, []);

  async function startLesson(docId: string, pageStart: number, pageEnd: number, question: string) {
    const source = await request<SourceSelection>(`/api/v1/documents/${docId}/selections`, {
      method: 'POST', headers: headers(), body: JSON.stringify({ page_start: pageStart, page_end: pageEnd, question }),
    });
    if (source.topic_assessment !== 'supported') {
      setSourceNotice('This passage is outside the current labs. Choose a passage about softmax, attention scaling, or causal masking, or try the example note.');
      return;
    }
    const created = await request<{ session_id: string }>('/api/v1/learning-sessions', {
      method: 'POST', headers: headers(), body: JSON.stringify({ selection_id: source.selection_id, goal: question }),
    });
    await refreshSession(created.session_id);
    setSelection(source); setSourceNotice(null); setIsStale(false);
  }

  async function withOperation(action: () => Promise<void>) {
    if (operationInFlight.current) return false;
    operationInFlight.current = true; setIsSubmitting(true); setErrorMsg(null);
    try { await action(); return true; } catch (error) { setErrorMsg(errorMessage(error)); return false; }
    finally { operationInFlight.current = false; setIsSubmitting(false); }
  }

  async function handleUploadDocument(file: File) {
    if (isUploading || isSubmitting) return;
    if (!file.name.toLowerCase().endsWith('.pdf') || file.size > 10 * 1024 * 1024) {
      setErrorMsg('Choose a PDF smaller than 10 MiB. Scanned pages are not supported yet.'); return;
    }
    setIsUploading(true); setErrorMsg(null); setSourceNotice(null);
    try {
      const form = new FormData(); form.append('file', file, file.name);
      const upload = await request<{ document_id: string }>('/api/v1/documents', { method: 'POST', headers: headers(false), body: form });
      await loadDocument(upload.document_id); setActivePane('source');
    } catch (error) { setErrorMsg(errorMessage(error)); }
    finally { setIsUploading(false); }
  }

  async function handleTryExample() {
    await withOperation(async () => {
      const response = await fetch('/examples/claimlab_attention_lab.pdf');
      if (!response.ok || !(response.headers.get('content-type') || '').includes('pdf')) throw new Error('The example PDF is unavailable. You can upload your own attention note.');
      const form = new FormData(); form.append('file', await response.blob(), 'claimlab_attention_lab.pdf');
      const upload = await request<{ document_id: string }>('/api/v1/documents', { method: 'POST', headers: headers(false), body: form });
      const doc = await loadDocument(upload.document_id);
      await startLesson(doc.document_id, 1, Math.min(2, doc.page_count), 'Why is attention scaled by 1/sqrt(d_k)?');
    });
  }

  async function handleRunRecipe(recipeId: string, parameters: Record<string, unknown>) {
    if (!session) return;
    // Failures propagate so the lab keeps its edited inputs and stale marker.
    if (operationInFlight.current) throw new Error('Please wait for the current step to finish.');
    operationInFlight.current = true; setIsSubmitting(true); setErrorMsg(null);
    try {
      await request(`/api/v1/learning-sessions/${session.session_id}/runs`, { method: 'POST', headers: headers(), body: JSON.stringify({ recipe_id: recipeId, parameters, expected_revision: session.revision }) });
      await refreshSession(session.session_id);
    } catch (error) { setErrorMsg(errorMessage(error)); throw error; }
    finally { operationInFlight.current = false; setIsSubmitting(false); }
  }

  async function submitEvent(eventType: string, payload: Record<string, unknown>) {
    if (!session) return false;
    return withOperation(async () => {
      try {
        await request(`/api/v1/learning-sessions/${session.session_id}/events`, {
          method: 'POST', headers: headers(), body: JSON.stringify({ schema_version: 1, event_id: crypto.randomUUID(), event_type: eventType, expected_revision: session.revision, payload }),
        });
      } catch (error) {
        await refreshSession(session.session_id).catch(() => undefined);
        throw error;
      }
      await refreshSession(session.session_id);
    });
  }

  async function handleResetData() {
    if (!window.confirm('Delete all your uploaded PDFs, extracted text, learning history, and sessions? This cannot be undone.')) return;
    await withOperation(async () => {
      await request('/api/v1/me/data', { method: 'DELETE', headers: headers(false) });
      window.location.reload();
    });
  }
  function navigate(pane: string) {
    setActivePane(pane);
    window.document.getElementById(pane)?.scrollIntoView({ behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth', block: 'start' });
  }
  const busy = isSubmitting || isUploading || isLoading;
  const hasLesson = Boolean(session);
  const sourceMatchesLesson = !selection || selection.document_id === document?.document_id;

  return (
    <div className="claimlab-app">
      <a className="skip-link" href="#whiteboard">Skip to whiteboard</a>
      <aside className="app-rail" aria-label="Workspace navigation">
        <a href="#" className="brand-mark" aria-label="ClaimLab home"><Icon name="flask" size={25}/></a>
        <div className="rail-links">{([{ id: 'source', icon: 'book', label: 'Source' }, { id: 'whiteboard', icon: 'board', label: 'Whiteboard' }, { id: 'experiment', icon: 'flask', label: 'Experiment' }, { id: 'progress', icon: 'chart', label: 'Progress' }] as const).map(item => (
          <button key={item.id} className={`rail-button ${activePane === item.id ? 'active' : ''}`} aria-label={item.label} title={item.label} aria-current={activePane === item.id ? 'location' : undefined} onClick={() => navigate(item.id)}><Icon name={item.icon}/><span>{item.label}</span></button>
        ))}</div>
        <span className="rail-bottom" title="Browser-bound private guest workspace"><Icon name="shield"/></span>
      </aside>
      <div className="app-body">
        <header className="navbar">
          <div className="navbar-brand"><span className="brand-name">ClaimLab<span className="brand-period">.</span></span><span className="nav-divider"/><span className="nav-location">Learning workspace</span></div>
          <div className="navbar-status"><span className="saved-status"><span className={`dot ${busy ? 'working' : ''}`}/>{busy ? 'Working on your lesson' : session ? 'Lesson saved' : 'Your space to explore'}</span>
            <details className="session-menu"><summary><span className="guest-avatar">Y</span><span>Your session</span><Icon name="chevron" size={14}/></summary><div className="session-menu-body"><strong>Private guest workspace</strong><p>History stays in this browser for 24 hours. Clearing its cookie loses access.</p><p>Teaching mode: <strong>{me?.model_mode === 'live' ? 'Live Meta model' : me ? 'Fixture · offline development' : 'Not connected'}</strong></p>{session && <p>Session revision {session.revision}</p>}<p>Delete your uploaded documents and learning history at any time. This also ends the guest session.</p><button className="text-button danger" onClick={handleResetData} disabled={busy || !me}>Delete my data</button></div></details>
          </div>
        </header>
        <main className="main-content">
          <div className="workspace-intro"><div><p className="eyebrow"><span className="tiny-line"/> A LITTLE CURIOSITY. A CLEARER PICTURE.</p><h1>{hasLesson ? 'Let’s make attention click.' : 'Big ideas, one clear step at a time.'}</h1><p className="intro-description">Read the source. See the idea. Test it for yourself.</p></div><div className={`mode-label ${me?.model_mode === 'live' ? 'live' : ''}`}><Icon name="spark" size={15}/>{me?.model_mode === 'live' ? 'Live Meta teaching' : me ? 'Fixture mode · offline teaching' : 'Connecting to workspace'}</div></div>
          {errorMsg && <div className="banner error" role="alert"><Icon name="info"/><span>{errorMsg}</span>{!me && <button className="text-button" onClick={() => void bootstrap()} disabled={isLoading}>Retry connection</button>}<button className="icon-button" onClick={() => setErrorMsg(null)} aria-label="Dismiss error"><Icon name="close" size={16}/></button></div>}
          <div className="workspace-layout" aria-busy={isLoading}>
            <section className="col-source" id="source" aria-label="Source material">
              <SourceViewer document={document} pages={docPages} anchors={sourceMatchesLesson ? selection?.anchors || [] : []} onUploadFile={handleUploadDocument} isUploading={isUploading} disabled={busy || !me} onTryExample={handleTryExample} onStartLesson={async (start, end, question) => { if (document) await withOperation(() => startLesson(document.document_id, start, end, question)); }} notice={sourceNotice || (!sourceMatchesLesson ? 'This is a new source. Explore a question to replace the current lesson on the board.' : null)} selectedRange={sourceMatchesLesson ? selection : null}/>
              <div className="learning-path"><p className="eyebrow">THE LEARNING LOOP</p><div className={document ? 'path-step complete' : 'path-step'}><span>01</span><div><strong>Start with the source</strong><p>A passage. A question. A starting point.</p></div></div><div className={hasLesson ? 'path-step complete' : 'path-step'}><span>02</span><div><strong>See it & experiment</strong><p>Connect the picture to real numbers.</p></div></div><div className={Object.values(session?.evidence_summary || {}).some(state => state !== 'introduced' && state !== 'not_assessed') ? 'path-step complete' : 'path-step'}><span>03</span><div><strong>Make it your own</strong><p>Your answers shape the next step.</p></div></div></div>
            </section>
            <section className="col-center" id="whiteboard" aria-label="Shared whiteboard" tabIndex={-1}>
              {selection && <div className="lesson-context"><span className="eyebrow">THE QUESTION WE’RE EXPLORING <span>· PAGES {selection.page_start}–{selection.page_end}</span></span><p>{selection.question}</p></div>}
              {!hasLesson ? <div className="welcome-board"><div className="welcome-board-header"><Icon name="board" size={17}/><span>Your shared whiteboard</span><span className="paper-badge">A space to think</span></div><div className="welcome-content"><div className="welcome-symbol"><Icon name="spark" size={35}/></div><span className="eyebrow">FROM “WHAT?” TO “AHA.”</span><h2>Don’t just read it.<br/><em>Reason through it.</em></h2><p>Bring a question about attention. We’ll draw the connections, try a small experiment, and work through what you notice.</p><button className="primary-button" disabled={busy || !me} onClick={handleTryExample}>{isLoading ? 'Opening your workspace…' : isSubmitting ? 'Preparing your lesson…' : 'Try the example lesson'}<Icon name="arrow" size={18}/></button><span className="welcome-caption">A short attention note · no upload needed</span></div><div className="welcome-footer"><span><Icon name="book" size={15}/> Source grounded</span><span><Icon name="flask" size={15}/> Real calculations</span><span><Icon name="chart" size={15}/> Learns from your work</span></div></div> : <Whiteboard key={'board-' + session!.session_id} scene={session!.board} activeRun={activeRun} isStale={isStale}/>}
              <TaskCard key={'task-' + (session?.session_id || 'empty') + '-' + (session?.active_task ? `${session.active_task.task_id}-${session.active_task.task_variant}` : 'none')} task={session?.active_task || null} onSubmitAnswer={answer => submitEvent('explanation_submitted', { task_id: session?.active_task?.task_id, task_variant: session?.active_task?.task_variant, answer })} onAskQuestion={message => submitEvent('message_submitted', { message })} onRequestHint={() => submitEvent('hint_requested', { task_id: session?.active_task?.task_id, task_variant: session?.active_task?.task_variant })} isLoading={busy} tutorNarration={session?.tutor_narration || ''} hasSession={hasLesson}/>
            </section>
            <section className="col-right" aria-label="Experiment and learning progress"><div id="experiment"><ExperimentPanel activeRun={activeRun} onRunRecipe={handleRunRecipe} isLoading={busy} disabled={!hasLesson} onStaleChange={setIsStale}/></div><div id="progress"><EvidencePanel evidenceSummary={session?.evidence_summary || {}}/></div></section>
          </div>
          <footer className="workspace-footer"><span>Built for understanding, with room for questions.</span><span><Icon name="shield" size={13}/> Private by default · 24-hour guest history</span></footer>
        </main>
      </div>
    </div>
  );
}
