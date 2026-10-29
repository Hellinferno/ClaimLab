"""Contracts for learning sessions and learner event submissions."""
from typing import Any, Dict, Optional
from pydantic import Field
import uuid
from claimlab.contracts.common import StrictModel, EvidenceCategory
from claimlab.contracts.whiteboard import SceneGraph
from claimlab.contracts.document import SourceSelectionResponse


class CreateSessionRequest(StrictModel):
    selection_id: str
    goal: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = Field(default_factory=dict)


class CreateSessionResponse(StrictModel):
    session_id: str
    revision: int
    initial_job_id: str


class SubmitLearnerEventRequest(StrictModel):
    schema_version: int = 1
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str
    expected_revision: int
    payload: Dict[str, Any]


class SubmitLearnerEventResponse(StrictModel):
    event_id: str
    current_revision: int
    tutor_job_id: str


class SessionStateResponse(StrictModel):
    session_id: str
    revision: int
    active_concept: Optional[str] = None
    active_job_id: Optional[str] = None
    board: SceneGraph
    evidence_summary: Dict[str, EvidenceCategory] = Field(default_factory=dict)
    active_task: Optional[Dict[str, Any]] = None
    latest_run_id: Optional[str] = None
    source_selection: Optional[SourceSelectionResponse] = None
    tutor_narration: Optional[str] = None
