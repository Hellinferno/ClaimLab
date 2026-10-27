"""SQLAlchemy models for ClaimLab entities."""
from datetime import datetime, timezone
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
import uuid
from claimlab.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class GuestOwner(Base):
    __tablename__ = "guest_owners"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    credential_hash = Column(String(64), nullable=False, unique=True, index=True)
    csrf_secret_hash = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)
    deleted_at = Column(DateTime, nullable=True)

    documents = relationship("Document", back_populates="owner", cascade="all, delete-orphan")
    sessions = relationship("LearningSession", back_populates="owner", cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_id = Column(String(36), ForeignKey("guest_owners.id"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    storage_key = Column(String(255), nullable=False)
    sha256 = Column(String(64), nullable=False)
    size_bytes = Column(Integer, nullable=False)
    page_count = Column(Integer, default=0, nullable=False)
    extraction_status = Column(String(32), default="pending", nullable=False)
    warnings_json = Column(Text, default="[]", nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)

    owner = relationship("GuestOwner", back_populates="documents")
    pages = relationship("DocumentPage", back_populates="document", cascade="all, delete-orphan")
    anchors = relationship("SourceAnchor", back_populates="document", cascade="all, delete-orphan")


class DocumentPage(Base):
    __tablename__ = "document_pages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False, index=True)
    page_number = Column(Integer, nullable=False)
    normalized_text = Column(Text, default="", nullable=False)
    char_count = Column(Integer, default=0, nullable=False)
    extraction_status = Column(String(32), default="pending", nullable=False)
    warnings_json = Column(Text, default="[]", nullable=False)

    __table_args__ = (UniqueConstraint("document_id", "page_number", name="uq_doc_page"),)
    document = relationship("Document", back_populates="pages")


class SourceAnchor(Base):
    __tablename__ = "source_anchors"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False, index=True)
    page_number = Column(Integer, nullable=False)
    start_offset = Column(Integer, nullable=False)
    end_offset = Column(Integer, nullable=False)
    quote = Column(Text, nullable=False)
    text_hash = Column(String(64), nullable=False)

    document = relationship("Document", back_populates="anchors")


class SourceSelection(Base):
    __tablename__ = "source_selections"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_id = Column(String(36), ForeignKey("guest_owners.id"), nullable=False, index=True)
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False, index=True)
    page_start = Column(Integer, nullable=False)
    page_end = Column(Integer, nullable=False)
    question = Column(Text, nullable=False)
    content_hash = Column(String(64), nullable=False)
    topic_assessment = Column(String(64), default="supported", nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)


class LearningSession(Base):
    __tablename__ = "learning_sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_id = Column(String(36), ForeignKey("guest_owners.id"), nullable=False, index=True)
    selection_id = Column(String(36), ForeignKey("source_selections.id"), nullable=False, index=True)
    goal = Column(Text, nullable=True)
    preferences_json = Column(Text, default="{}", nullable=False)
    active_concept = Column(String(64), nullable=True)
    revision = Column(Integer, default=1, nullable=False)
    active_job_id = Column(String(36), nullable=True)
    fencing_generation = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)

    owner = relationship("GuestOwner", back_populates="sessions")
    snapshots = relationship("BoardSnapshot", back_populates="session", cascade="all, delete-orphan")


class BoardSnapshot(Base):
    __tablename__ = "board_snapshots"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("learning_sessions.id"), nullable=False, index=True)
    revision = Column(Integer, nullable=False)
    schema_version = Column(Integer, default=1, nullable=False)
    scene_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    session = relationship("LearningSession", back_populates="snapshots")


class LearnerEvent(Base):
    __tablename__ = "learner_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_id = Column(String(36), ForeignKey("guest_owners.id"), nullable=False, index=True)
    session_id = Column(String(36), ForeignKey("learning_sessions.id"), nullable=False, index=True)
    client_event_id = Column(String(36), nullable=False)
    event_type = Column(String(64), nullable=False)
    payload_json = Column(Text, nullable=False)
    expected_revision = Column(Integer, nullable=False)
    sequence = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)


class ConceptEvidence(Base):
    __tablename__ = "concept_evidence"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("learning_sessions.id"), nullable=False, index=True)
    event_id = Column(String(36), nullable=True)
    task_id = Column(String(64), nullable=True)
    concept_id = Column(String(64), nullable=False, index=True)
    category = Column(String(32), nullable=False)
    assistance_level = Column(String(32), default="none", nullable=False)
    assessment_status = Column(String(32), default="provisional", nullable=False)
    rationale = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)


class TeachingDecision(Base):
    __tablename__ = "teaching_decisions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("learning_sessions.id"), nullable=False, index=True)
    evidence_ids_json = Column(Text, default="[]", nullable=False)
    tentative_gap = Column(Text, nullable=True)
    selected_action = Column(String(128), nullable=False)
    rationale = Column(Text, nullable=False)
    board_refs_json = Column(Text, default="[]", nullable=False)
    run_id = Column(String(36), nullable=True)
    follow_up_task_id = Column(String(64), nullable=True)
    outcome = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)


class ExperimentRun(Base):
    __tablename__ = "experiment_runs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_id = Column(String(36), ForeignKey("guest_owners.id"), nullable=False, index=True)
    session_id = Column(String(36), ForeignKey("learning_sessions.id"), nullable=True, index=True)
    parent_job_id = Column(String(36), nullable=True)
    recipe_id = Column(String(64), nullable=False)
    parameters_json = Column(Text, nullable=False)
    parameter_hash = Column(String(64), nullable=False, index=True)
    seed = Column(Integer, nullable=False)
    status = Column(String(32), nullable=False)
    output_json = Column(Text, nullable=True)
    checks_json = Column(Text, default="[]", nullable=False)
    started_at = Column(DateTime, default=utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)


class Job(Base):
    __tablename__ = "jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_id = Column(String(36), ForeignKey("guest_owners.id"), nullable=False, index=True)
    session_id = Column(String(36), nullable=True, index=True)
    document_id = Column(String(36), nullable=True, index=True)
    kind = Column(String(32), nullable=False)
    status = Column(String(32), default="queued", nullable=False, index=True)
    progress = Column(Float, default=0.0, nullable=False)
    deadline_seconds = Column(Integer, default=180, nullable=False)
    cancelled = Column(Boolean, default=False, nullable=False)
    lease_expires_at = Column(DateTime, nullable=True, index=True)
    fencing_generation = Column(Integer, default=1, nullable=False)
    error_code = Column(String(64), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    events = relationship("JobEvent", back_populates="job", cascade="all, delete-orphan")


class JobEvent(Base):
    __tablename__ = "job_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String(36), ForeignKey("jobs.id"), nullable=False, index=True)
    sequence = Column(Integer, nullable=False)
    event_type = Column(String(64), nullable=False)
    payload_json = Column(Text, default="{}", nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    job = relationship("Job", back_populates="events")


class IdempotencyRecord(Base):
    __tablename__ = "idempotency_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_id = Column(String(36), ForeignKey("guest_owners.id"), nullable=False, index=True)
    route_scope = Column(String(64), nullable=False)
    idempotency_key = Column(String(64), nullable=False)
    request_fingerprint = Column(String(64), nullable=False)
    status_code = Column(Integer, nullable=False)
    response_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)

    __table_args__ = (UniqueConstraint("owner_id", "route_scope", "idempotency_key", name="uq_idempotency"),)


class TaskAttempt(Base):
    __tablename__ = "task_attempts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("learning_sessions.id"), nullable=False, index=True)
    task_id = Column(String(64), nullable=False, index=True)
    task_variant = Column(String(32), nullable=False)
    learner_event_id = Column(String(36), nullable=False)
    response_text = Column(Text, nullable=False)
    rubric_version = Column(String(32), default="v1", nullable=False)
    hint_count = Column(Integer, default=0, nullable=False)
    attempt_index = Column(Integer, default=1, nullable=False)
    assessment_status = Column(String(32), default="checked", nullable=False)
    is_correct = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)


class ToolInvocation(Base):
    __tablename__ = "tool_invocations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String(36), ForeignKey("jobs.id"), nullable=False, index=True)
    provider_call_id = Column(String(64), nullable=False)
    tool_name = Column(String(64), nullable=False)
    argument_hash = Column(String(64), nullable=False)
    status = Column(String(32), default="completed", nullable=False)
    result_reference = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    __table_args__ = (UniqueConstraint("job_id", "provider_call_id", name="uq_tool_invocation"),)


class BudgetReservation(Base):
    __tablename__ = "budget_reservations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_id = Column(String(36), ForeignKey("guest_owners.id"), nullable=False, index=True)
    request_id = Column(String(64), nullable=False, index=True)
    reserved_amount_usd = Column(Float, default=0.0, nullable=False)
    settled_amount_usd = Column(Float, default=0.0, nullable=False)
    status = Column(String(32), default="reserved", nullable=False)
    model_name = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)

