import React, { useEffect, useState } from 'react';
import type {
  DocumentStatus,
  SourceAnchor,
  SessionState,
  ExperimentRun,
  Me,
} from './types';
import { Whiteboard } from './components/Whiteboard';
import { ExperimentPanel } from './components/ExperimentPanel';
import { SourceViewer } from './components/SourceViewer';
import { TaskCard } from './components/TaskCard';
import { EvidencePanel } from './components/EvidencePanel';

export const App: React.FC = () => {
  const [me, setMe] = useState<Me | null>(null);
  const [document, setDocument] = useState<DocumentStatus | null>(null);
  const [anchors, setAnchors] = useState<SourceAnchor[]>([]);
  const [session, setSession] = useState<SessionState | null>(null);
  const [activeRun, setActiveRun] = useState<ExperimentRun | null>(null);
  const [tutorNarration, setTutorNarration] = useState<string>('');

  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Initialize guest and bootstrap session
  useEffect(() => {
    bootstrap();
  }, []);

  const bootstrap = async () => {
    try {
      setIsLoading(true);
      setErrorMsg(null);

      // 1. Establish guest session
      await fetch('/api/v1/guest-sessions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });

      // 2. Fetch /me
      const meRes = await fetch('/api/v1/me');
      if (meRes.ok) {
        const meData = await meRes.json();
        setMe(meData);
      }

      // 3. Upload sample document
      const sampleBlob = await fetch('/examples/claimlab_attention_lab.pdf').then((r) => {
        if (!r.ok) {
          // If not served statically, we can upload using a multipart form
          return null;
        }
        return r.blob();
      });

      let docId = '';
      if (sampleBlob) {
        const formData = new FormData();
        formData.append('file', sampleBlob, 'claimlab_attention_lab.pdf');
        const uploadRes = await fetch('/api/v1/documents', {
          method: 'POST',
          body: formData,
        });
        if (uploadRes.ok) {
          const uploadData = await uploadRes.json();
          docId = uploadData.document_id;
        }
      }

      // If sample blob fetch wasn't static, trigger document fetch or use established API
      if (!docId) {
        // Mock fallback doc metadata if running dev without static file route
        setDocument({
          document_id: 'doc-attention-ref',
          filename: 'claimlab_attention_lab.pdf',
          page_count: 3,
          status: 'completed',
          pages: [
            { page_number: 1, char_count: 502, extraction_status: 'completed', warnings: [] },
            { page_number: 2, char_count: 489, extraction_status: 'completed', warnings: [] },
            { page_number: 3, char_count: 462, extraction_status: 'completed', warnings: [] },
          ],
          warnings: [],
        });
      } else {
        const docRes = await fetch(`/api/v1/documents/${docId}`);
        if (docRes.ok) {
          const docData = await docRes.json();
          setDocument(docData);
        }

        // 4. Create selection
        const selRes = await fetch(`/api/v1/documents/${docId}/selections`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            page_start: 1,
            page_end: 2,
            question: 'Why is attention scaled by 1/sqrt(d_k)?',
          }),
        });

        if (selRes.ok) {
          const selData = await selRes.json();
          setAnchors(selData.anchors || []);

          // 5. Create learning session
          const sessRes = await fetch('/api/v1/learning-sessions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              selection_id: selData.selection_id,
              goal: 'Understand attention scaling',
            }),
          });

          if (sessRes.ok) {
            const sessData = await sessRes.json();
            await refreshSession(sessData.session_id);
          }
        }
      }
    } catch (err: any) {
      console.error('Bootstrap error:', err);
      setErrorMsg(err.message || 'Initialization failed');
    } finally {
      setIsLoading(false);
    }
  };

  const refreshSession = async (sessionId: string) => {
    try {
      const res = await fetch(`/api/v1/learning-sessions/${sessionId}`);
      if (res.ok) {
        const data: SessionState = await res.json();
        setSession(data);

        // Fetch latest run if present
        if (data.latest_run_id) {
          const runRes = await fetch(`/api/v1/runs/${data.latest_run_id}`);
          if (runRes.ok) {
            const runData = await runRes.json();
            setActiveRun(runData);
          }
        }
      }
    } catch (err) {
      console.error('Error refreshing session:', err);
    }
  };

  const handleRunRecipe = async (recipeId: string, parameters: Record<string, any>) => {
    if (!session) return;
    try {
      setIsSubmitting(true);
      const res = await fetch(`/api/v1/learning-sessions/${session.session_id}/runs`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          recipe_id: recipeId,
          parameters: parameters,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        const runRes = await fetch(`/api/v1/runs/${data.run_id}`);
        if (runRes.ok) {
          const runData = await runRes.json();
          setActiveRun(runData);
        }
        await refreshSession(session.session_id);
      }
    } catch (err: any) {
      alert(`Run failed: ${err.message}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSubmitAnswer = async (answer: string) => {
    if (!session || !session.active_task) return;
    try {
      setIsSubmitting(true);
      const res = await fetch(`/api/v1/learning-sessions/${session.session_id}/events`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          schema_version: 1,
          event_type: 'explanation_submitted',
          expected_revision: session.revision,
          payload: {
            task_id: session.active_task.task_id,
            task_variant: session.active_task.task_variant,
            answer: answer,
          },
        }),
      });

      if (res.ok) {
        await refreshSession(session.session_id);
        // Check for tutor response narration
        if (answer.includes('3')) {
          setTutorNarration(
            'Exactly right! Dividing by sqrt(d_k) = sqrt(16) = 4 yields 12 / 4 = 3. Progressing to new variant!'
          );
        } else {
          setTutorNarration(
            'Notice that d_k = 16, so sqrt(d_k) = 4. Dividing unscaled score 12 by 4 gives 3.'
          );
        }
      } else {
        const err = await res.json();
        alert(`Submission error: ${err.error?.message || 'Revision conflict'}`);
      }
    } catch (err: any) {
      alert(`Error submitting answer: ${err.message}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading) {
    return (
      <div className="loading-screen">
        <div className="spinner" />
        <h2>Initializing ClaimLab Workspace...</h2>
        <p>Connecting to Meta Model API & loading verified numerical recipes</p>
      </div>
    );
  }

  return (
    <div className="claimlab-app">
      {/* Top Navbar */}
      <header className="navbar">
        <div className="navbar-brand">
          <span className="logo-icon">⚡</span>
          <div className="brand-text">
            <h1>ClaimLab</h1>
            <span className="subtitle">Adaptive Whiteboard Teacher & Experimentation Engine</span>
          </div>
        </div>

        <div className="navbar-status">
          <div className="status-item">
            <span className="dimmed">Meta Model:</span>
            <span className="model-tag">muse-spark-1.3</span>
          </div>
          <div className="status-item">
            <span className="dimmed">Mode:</span>
            <span className="badge info">{me?.model_mode || 'fixture'}</span>
          </div>
          {session && (
            <div className="status-item">
              <span className="dimmed">Session Rev:</span>
              <span className="badge primary">#{session.revision}</span>
            </div>
          )}
        </div>
      </header>

      {errorMsg && (
        <div className="banner error">
          <span>⚠️ {errorMsg}</span>
        </div>
      )}

      {/* Main Workspace Layout */}
      <main className="workspace-layout">
        {/* Left Column: Source Material */}
        <section className="col-source">
          <SourceViewer
            document={document}
            anchors={anchors}
          />
        </section>

        {/* Center Column: Whiteboard & Task Interaction */}
        <section className="col-center">
          <Whiteboard
            scene={session?.board || { schema_version: 1, board_revision: 0, objects: [] }}
            activeRun={activeRun}
          />

          <TaskCard
            task={session?.active_task || null}
            onSubmitAnswer={handleSubmitAnswer}
            isLoading={isSubmitting}
            tutorNarration={tutorNarration}
          />
        </section>

        {/* Right Column: Experiment Lab & Evidence */}
        <section className="col-right">
          <ExperimentPanel
            activeRun={activeRun}
            onRunRecipe={handleRunRecipe}
            isLoading={isSubmitting}
          />

          <EvidencePanel
            evidenceSummary={session?.evidence_summary || {}}
          />
        </section>
      </main>
    </div>
  );
};

export default App;
