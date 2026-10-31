/**
 * ClaimLab frontend TypeScript interfaces matching canonical backend contracts.
 */

export interface GuestSession {
  expires_at: string;
  csrf_token: string;
}

export interface Me {
  guest_id: string;
  expires_at: string;
  model_mode: string;
  limits: {
    max_documents: number;
    max_file_size_mib: number;
    max_pages: number;
    max_sessions: number;
  };
  web_research?: boolean;
}

export interface DocumentPageMeta {
  page_number: number;
  char_count: number;
  extraction_status: 'pending' | 'processing' | 'completed' | 'failed' | 'scanned_only';
  warnings: string[];
}

export interface DocumentPageDetail {
  page_number: number;
  normalized_text: string;
  char_count: number;
  anchors: SourceAnchor[];
}

export interface DocumentStatus {
  document_id: string;
  filename: string;
  page_count: number;
  status: string;
  pages: DocumentPageMeta[];
  warnings: string[];
}

export interface SourceAnchor {
  id: string;
  document_id: string;
  page_number: number;
  start_offset: number;
  end_offset: number;
  quote: string;
  text_hash: string;
}

export interface SourceSelection {
  selection_id: string;
  document_id: string;
  page_start: number;
  page_end: number;
  question: string;
  anchors: SourceAnchor[];
  content_hash: string;
  topic_assessment: string;
}

export type BoardObjectType =
  | 'text'
  | 'equation'
  | 'concept_node'
  | 'matrix'
  | 'connector'
  | 'plot_ref'
  | 'group'
  | 'annotation';

export interface BoardObject {
  id: string;
  type: BoardObjectType;
  position: { x: number; y: number };
  dimensions: { width: number; height: number };
  label: string;
  concept_id?: string;
  source_refs?: string[];
  payload: Record<string, any>;
  highlight_style?: string;
}

export interface SceneGraph {
  schema_version: number;
  board_revision: number;
  objects: BoardObject[];
  active_group?: string;
}

export type EvidenceCategory =
  | 'not_assessed'
  | 'introduced'
  | 'needs_check'
  | 'supported_with_help'
  | 'supported_independently'
  | 'needs_revisit';

export interface ActiveTask {
  task_id: string;
  task_variant: string;
  question: string;
  expected_type: string;
  choices?: string[];
}

export type StepTag = 'source' | 'background' | 'web' | 'experiment' | 'interpretation' | 'assumption';

/** One page of the tutor's lesson; object_ids are the board items it draws or points at. */
export interface TutorStep {
  title: string;
  body: string;
  tag: StepTag;
  object_ids: string[];
  anchor_id?: string;
  url?: string;
}

export interface WebSource {
  title: string;
  url: string;
}

export interface SandboxParameterSpec {
  name: string;
  label: string;
  value: number;
  min: number;
  max: number;
  step?: number | null;
  integer: boolean;
}

export interface SandboxSeries {
  name: string;
  x: number[];
  y: number[];
}

export interface SandboxOutput {
  summary?: string;
  metrics?: Record<string, number | string | boolean>;
  chart?: { title: string; x_label?: string; y_label?: string; kind?: 'line' | 'bar' } | null;
  series?: SandboxSeries[];
  table?: { columns: string[]; rows: (number | string | boolean | null)[][] } | null;
  checks?: { name: string; passed: boolean; detail?: string }[];
  stdout?: string;
  error?: string;
}

export interface SessionState {
  session_id: string;
  revision: number;
  active_concept?: string;
  active_job_id?: string;
  board: SceneGraph;
  evidence_summary: Record<string, EvidenceCategory>;
  active_task?: ActiveTask | null;
  latest_run_id?: string | null;
  source_selection?: SourceSelection | null;
  tutor_narration?: string | null;
  tutor_steps?: TutorStep[];
  tutor_turn?: string | null;
  web_sources?: WebSource[];
  lesson_kind?: 'attention_lab' | 'open';
}

export interface CheckResult {
  name: string;
  status: 'passed' | 'failed' | 'not_applicable';
  tolerance?: number;
  detail: string;
}

export interface ExperimentRun {
  run_id: string;
  recipe_id: string;
  parameters: Record<string, any>;
  parameter_hash: string;
  seed: number;
  status: string;
  output?: any;
  checks: CheckResult[];
  assumptions: string[];
  runner_digest: string;
  numpy_version: string;
  started_at: string;
  completed_at?: string;
}
