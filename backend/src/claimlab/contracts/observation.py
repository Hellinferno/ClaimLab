"""Contracts for learning observation, evidence state, and teaching decisions."""
from typing import List, Optional
from pydantic import Field
from claimlab.contracts.common import StrictModel, EvidenceCategory, AssessmentStatus


class ConceptEvidenceState(StrictModel):
    concept_id: str
    state: EvidenceCategory
    assessment_status: AssessmentStatus
    evidence_ids: List[str] = Field(default_factory=list)
    rationale: str


class TeachingDecisionRecord(StrictModel):
    decision_id: str
    evidence_ids: List[str] = Field(default_factory=list)
    tentative_gap: Optional[str] = None
    selected_action: str
    rationale: str
    board_refs: List[str] = Field(default_factory=list)
    run_id: Optional[str] = None
    follow_up_task_id: Optional[str] = None
    outcome: Optional[str] = None
