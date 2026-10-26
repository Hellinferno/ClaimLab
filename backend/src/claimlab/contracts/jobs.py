"""Contracts for background jobs and real-time job events."""
from typing import Any, Dict, Optional
from pydantic import Field
from claimlab.contracts.common import StrictModel, JobKind, JobStatus


class JobResponse(StrictModel):
    job_id: str
    kind: JobKind
    status: JobStatus
    deadline_seconds: int
    progress: Optional[float] = None
    current_session_revision: Optional[int] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None


class JobEventPayload(StrictModel):
    job_id: str
    sequence: int
    event_type: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    timestamp: str
