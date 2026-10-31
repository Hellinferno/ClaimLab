import { useRef, useState } from 'react';
import type { DocumentStatus, SourceAnchor, DocumentPageDetail, SourceSelection } from '../types';
import { Icon } from './Icon';

interface SourceViewerProps {
  document: DocumentStatus | null;
  pages: DocumentPageDetail[];
  anchors: SourceAnchor[];
  onUploadFile: (file: File) => Promise<void>;
  onTryExample: () => Promise<void>;
  onStartLesson: (start: number, end: number, question: string) => Promise<void>;
  isUploading: boolean;
  disabled: boolean;
  notice?: string | null;
  selectedRange?: SourceSelection | null;
}

export function SourceViewer(props: SourceViewerProps) {
  return <SourceContent key={(props.document?.document_id || 'empty') + '-' + (props.selectedRange?.selection_id || 'draft')} {...props}/>;
}

function SourceContent({ document, pages, anchors, onUploadFile, onTryExample, onStartLesson, isUploading, disabled, notice, selectedRange }: SourceViewerProps) {
  const fileInput = useRef<HTMLInputElement>(null);
  const [pageNumber, setPageNumber] = useState(selectedRange?.page_start || 1);
  const [start, setStart] = useState(selectedRange?.page_start || 1);
  const [end, setEnd] = useState(selectedRange?.page_end || Math.min(2, document?.page_count || 1));
  const [question, setQuestion] = useState(selectedRange?.question || 'What is the main idea here, and why does it work?');
  const [selectedAnchor, setSelectedAnchor] = useState<string | null>(null);
  const currentPage = pages.find(page => page.page_number === pageNumber);
  const pageAnchors = anchors.filter(anchor => anchor.page_number === pageNumber);
  const draftChanged = !selectedRange || start !== selectedRange.page_start || end !== selectedRange.page_end || question !== selectedRange.question;

  return <div className="panel source-panel">
    <div className="panel-header"><div className="title-row"><Icon name="book" size={17}/><h2>Your source</h2></div><span className="panel-number">01</span></div>
    <input ref={fileInput} className="visually-hidden" type="file" accept=".pdf,application/pdf" aria-label="Upload PDF" disabled={disabled} onChange={async event => {
      const file = event.currentTarget.files?.[0]; event.currentTarget.value = ''; if (file) await onUploadFile(file);
    }}/>
    {document ? <>
      <div className="document-card"><div className="document-icon">PDF</div><div><strong title={document.filename}>{document.filename}</strong><span>{document.page_count} {document.page_count === 1 ? 'page' : 'pages'} · {document.status === 'completed' ? 'Text extracted' : document.status}</span></div><button className="icon-button" title="Upload another PDF" aria-label="Upload another PDF" disabled={disabled} onClick={() => fileInput.current?.click()}><Icon name="upload" size={16}/></button></div>
      {!!document.warnings.length && <p className="source-warning" role="status">{document.warnings.join(' ')}</p>}
      <div className="source-reader-heading"><span className="eyebrow">THE ORIGINAL PASSAGE</span><select aria-label="Source page" value={pageNumber} onChange={event => { setPageNumber(Number(event.target.value)); setSelectedAnchor(null); }}>{pages.map(page => <option key={page.page_number} value={page.page_number}>Page {page.page_number}</option>)}</select></div>
      <div className="source-paper"><span className="source-page-number">PAGE {pageNumber.toString().padStart(2, '0')}</span>{currentPage?.normalized_text ? <p className="extracted-text">{currentPage.normalized_text}</p> : <p className="muted">This page has no readable text. Choose a page with native text or upload another PDF.</p>}</div>
      {pageAnchors.length > 0 && <details className="source-anchors"><summary>{pageAnchors.length} source {pageAnchors.length === 1 ? 'anchor' : 'anchors'} <Icon name="chevron" size={13}/></summary><div className="anchors-list">{pageAnchors.map(anchor => <button key={anchor.id} className={'anchor-item ' + (selectedAnchor === anchor.id ? 'selected' : '')} onClick={() => setSelectedAnchor(selectedAnchor === anchor.id ? null : anchor.id)} aria-expanded={selectedAnchor === anchor.id}><span className="eyebrow">SOURCE · PAGE {anchor.page_number}</span><q>{anchor.quote}</q>{selectedAnchor === anchor.id && <code>Characters {anchor.start_offset}–{anchor.end_offset} · {anchor.id}</code>}</button>)}</div></details>}
      <form className="lesson-form" onSubmit={async event => { event.preventDefault(); await onStartLesson(start, end, question.trim()); }}>
        <label htmlFor="learning-question">What would you like to understand?</label><textarea id="learning-question" value={question} onChange={event => setQuestion(event.target.value)} maxLength={1000} rows={3} disabled={disabled} required/>
        <div className="form-row page-range"><div className="form-group"><label htmlFor="page-start">From page</label><input id="page-start" type="number" min={1} max={document.page_count} value={start} onChange={event => setStart(Number(event.target.value))} disabled={disabled} required/></div><span>—</span><div className="form-group"><label htmlFor="page-end">To page</label><input id="page-end" type="number" min={start} max={Math.min(document.page_count, start + 4)} value={end} onChange={event => setEnd(Number(event.target.value))} disabled={disabled} required/></div></div>
        <button className={draftChanged ? 'secondary-button' : 'text-button lesson-current'} type="submit" disabled={disabled || !question.trim() || !Number.isInteger(start) || !Number.isInteger(end) || end < start || end - start > 4 || !draftChanged}>{draftChanged ? 'Explore this question' : 'Current lesson'}<Icon name={draftChanged ? 'arrow' : 'check'} size={15}/></button>
      </form>
      {notice && <div className="info-box source-warning" role="status">{notice}</div>}
    </> : <><div className="upload-zone"><div className="upload-symbol"><Icon name="book" size={27}/></div><h3>Start with a question.</h3><p>Add a paper or note you’d like to understand a little better.</p><button className="secondary-button" onClick={() => fileInput.current?.click()} disabled={disabled}><Icon name="upload" size={15}/>{isUploading ? 'Reading your PDF…' : 'Upload a PDF'}</button><span>Native-text PDF · up to 10 MiB</span></div><div className="example-note"><span className="eyebrow">A GOOD PLACE TO START</span><strong>Attention, made tangible</strong><p>A short note exploring scores, scaling, and causal masks.</p><button className="text-button" onClick={onTryExample} disabled={disabled}>Open example lesson <Icon name="arrow" size={15}/></button></div></>}
    <div className="source-footnote"><Icon name="shield" size={13}/><span>Your file stays private to this session.</span></div>
  </div>;
}
