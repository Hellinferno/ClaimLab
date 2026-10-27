import React, { useEffect, useState } from 'react';
import type {
  DocumentStatus,
  DocumentPageDetail,
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
  const [csrfToken, setCsrfToken] = useState<string>('');
  const [document, setDocument] = useState<DocumentStatus | null>(null);
  const [docPages, setDocPages] = useState<DocumentPageDetail[]>([]);
  const [anchors, setAnchors] = useState<SourceAnchor[]>([]);
  const [session, setSession] = useState<SessionState | null>(null);
  const [activeRun, setActiveRun] = useState<ExperimentRun | null>(null);
  const [tutorNarration, setTutorNarration] = useState<string>('');

  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    bootstrap();
  }, []);

  const bootstrap = async () => {
    try {
      setIsLoading(true);
      setErrorMsg(null);

      // 1. Establish guest session (or check existing cookie)
      const guestRes = await fetch('/api/v1/guest-sessions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });

      let token = '';
      if (guestRes.ok) {
        const guestData = await guestRes.json();
        token = guestData.csrf_token;
        setCsrfToken(token);
      }

      // 2. Fetch /me
      const meRes = await fetch('/api/v1/me');
      if (meRes.ok) {
        const meData = await meRes.json();
        setMe(meData);
      }

      // 3. Check for existing active session to resume
      const activeRes = await fetch('/api/v1/learning-sessions/active');
      if (activeRes.ok) {
        const activeData = await activeRes.json();
        if (activeData.active_session_id) {
          await refreshSession(activeData.active_session_id);
          setIsLoading(false);
          return;
        }
      }

      // 4. Initial setup: upload default reference attention note if no active session
      let docId = '';
      const sampleBlob = await fetch('/examples/claimlab_attention_lab.pdf').then((r) => {
        if (!r.ok) return null;
        return r.blob();
      });

      if (sampleBlob) {
        const formData = new FormData();
        formData.append('file', sampleBlob, 'claimlab_attention_lab.pdf');
        const uploadRes = await fetch('/api/v1/documents', {
          method: 'POST',
          headers: {
            'X-CSRF-Token': token,
            'Idempotency-Key': crypto.randomUUID(),
          },
          body: formData,
        });
        if (uploadRes.ok) {
          const uploadData = await uploadRes.json();
          docId = uploadData.document_id;
        }
      }

      if (docId) {
        await loadDocumentAndStartSession(docId, token);
      } else {
        // Fallback demo state if running dev server isolated
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
      }
    } catch (err: any) {
      console.error('Bootstrap error:', err);
      setErrorMsg(err.message || 'Initialization failed');
    } finally {
      setIsLoading(false);
    }
  };

  const loadDocumentAndStartSession = async (docId: string, token: string) => {
    // Fetch document details
    const docRes = await fetch(`/api/v1/documents/${docId}`);
    if (docRes.ok) {
      const docData = await docRes.json();
      setDocument(docData);
    }

    // Fetch document pages text and anchors
    const pagesRes = await fetch(`/api/v1/documents/${docId}/pages`);
    if (pagesRes.ok) {
      const pagesData: DocumentPageDetail[] = await pagesRes.json();
      setDocPages(pagesData);
    }

    // Create selection on Page 1-2 (Attention Scaling)
    const selRes = await fetch(`/api/v1/documents/${docId}/selections`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRF-Token': token,
        'Idempotency-Key': crypto.randomUUID(),
      },
      body: JSON.stringify({
        page_start: 1,
        page_end: 2,
        question: 'Why is attention scaled by 1/sqrt(d_k)?',
      }),
    });

    if (selRes.ok) {
      const selData = await selRes.json();
      setAnchors(selData.anchors || []);

      // Create initial learning session
      const sessRes = await fetch('/api/v1/learning-sessions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRF-Token': token,
          'Idempotency-Key': crypto.randomUUID(),
        },
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
        headers: {
          'Content-Type': 'application/json',
          'X-CSRF-Token': csrfToken,
          'Idempotency-Key': crypto.randomUUID(),
        },
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
      } else {
        const err = await res.json();
        alert(`Recipe execution error: ${err.error?.message || 'Execution failed'}`);
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
        headers: {
          'Content-Type': 'application/json',
          'X-CSRF-Token': csrfToken,
          'Idempotency-Key': crypto.randomUUID(),
        },
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
        if (answer.trim() === '3') {
          setTutorNarration(
            '[Source] Based on Section B, dividing dot-product score by $\\sqrt{d_k} = \\sqrt{16} = 4$ yields $12 / 4 = 3$.\n' +
            '[Experiment] Notice how the scaled curve stabilizes score variance near 1.0! Progressing to next variant.'
          );
        } else {
          setTutorNarration(
            '[Source] Trace the arithmetic: $d_k = 16$, so $\\sqrt{d_k} = 4$. Dividing $12$ by $4$ gives $3$. Try recalculating this step.'
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

  const handleUploadDocument = async (file: File) => {
    try {
      setIsUploading(true);
      const formData = new FormData();
      formData.append('file', file, file.name);

      const res = await fetch('/api/v1/documents', {
        method: 'POST',
        headers: {
          'X-CSRF-Token': csrfToken,
          'Idempotency-Key': crypto.randomUUID(),
        },
        body: formData,
      });

      if (res.ok) {
        const uploadData = await res.json();
        await loadDocumentAndStartSession(uploadData.document_id, csrfToken);
      } else {
        const err = await res.json();
        alert(`Upload error: ${err.error?.message || 'Upload failed'}`);
      }
    } catch (err: any) {
      alert(`Upload failed: ${err.message}`);
    } finally {
      setIsUploading(false);
    }
  };

  const handleResetData = async () => {
    if (!window.confirm('Reset all your guest data, uploaded documents, and learning sessions?')) {
      return;
    }
    try {
      setIsLoading(true);
      await fetch('/api/v1/me/data', {
        method: 'DELETE',
        headers: {
          'X-CSRF-Token': csrfToken,
          'Idempotency-Key': crypto.randomUUID(),
        },
      });
      // Re-bootstrap fresh
      window.location.reload();
    } catch (err: any) {
      alert(`Reset failed: ${err.message}`);
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="loading-screen">
        <div className="spinner" />
        <h2>Initializing ClaimLab Workspace...</h2>
        <p>Connecting to Meta Model API &amp; loading verified numerical recipes</p>
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
            <span className="subtitle">Adaptive Whiteboard Teacher &amp; Experimentation Engine</span>
          </div>
        </div>

        <div className="navbar-status">
          <div className="status-item">
            <span className="dimmed">Meta Model:</span>
            <span className="model-tag">muse-spark-1.3</span>
          </div>
          <div className="status-item">
            <span className="dimmed">Mode:</span>
            <span className={`badge ${me?.model_mode === 'live' ? 'success' : 'info'}`}>
              {me?.model_mode === 'live' ? 'live' : 'fixture'}
            </span>
          </div>
          {session && (
            <div className="status-item">
              <span className="dimmed">Session Rev:</span>
              <span className="badge primary">#{session.revision}</span>
            </div>
          )}
          <button
            type="button"
            className="reset-btn"
            title="Purge session data per privacy contract"
            onClick={handleResetData}
          >
            Clear Data
          </button>
        </div>
      </header>

      {errorMsg && (
        <div className="banner error">
          <span>⚠️ {errorMsg}</span>
        </div>
      )}

      {/* Main Workspace Layout */}
      <main className="workspace-layout">
        {/* Left Column: Source Grounding */}
        <section className="col-source">
          <SourceViewer
            document={document}
            pages={docPages}
            anchors={anchors}
            onUploadFile={handleUploadDocument}
            isUploading={isUploading}
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
