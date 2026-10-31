"""Learning adaptation policy engine implementing prerequisite checking and evidence progression."""
from typing import Any, Dict, Optional, Tuple
from sqlalchemy.orm import Session
import json

from claimlab.contracts.common import EvidenceCategory, AssessmentStatus, AssistanceLevel
from claimlab.models import (
    ConceptEvidence,
    TeachingDecision,
    TaskAttempt,
    LearnerEvent,
)
from claimlab.learning.task_bank import TASK_REGISTRY, RubricEvaluation, evaluate_task_submission


def recorded_assistance_count(
    db: Session, session_id: str, event: LearnerEvent, task_id: str, variant_id: str,
) -> int:
    """Derive help from server-attributed events and earlier checked feedback."""
    prior_errors = db.query(TaskAttempt).join(
        LearnerEvent, LearnerEvent.id == TaskAttempt.learner_event_id,
    ).filter(
        TaskAttempt.session_id == session_id,
        TaskAttempt.task_id == task_id,
        TaskAttempt.task_variant == variant_id,
        TaskAttempt.is_correct.is_(False),
        LearnerEvent.sequence < event.sequence,
    ).count()
    help_events = db.query(LearnerEvent).filter(
        LearnerEvent.session_id == session_id,
        LearnerEvent.sequence < event.sequence,
        LearnerEvent.event_type.in_(("hint_requested", "message_submitted", "object_question_submitted")),
    ).all()
    task_help = 0
    for help_event in help_events:
        payload = json.loads(help_event.payload_json)
        attribution = payload.get("assistance_task", {})
        if payload.get("assistance_delivered") is True and attribution.get("task_id") == task_id and attribution.get("task_variant") == variant_id:
            task_help += 1
    return prior_errors + task_help


def update_evidence_and_decide(
    db: Session,
    session_id: str,
    event: LearnerEvent,
    task_id: str,
    variant_id: str,
    answer_raw: Any,
) -> Tuple[ConceptEvidence, TeachingDecision, Optional[Dict[str, Any]]]:
    """
    Applies the 2-variant progression policy and records deterministic teaching decisions.
    """
    hints_used = recorded_assistance_count(db, session_id, event, task_id, variant_id)
    eval_result: RubricEvaluation = evaluate_task_submission(task_id, variant_id, answer_raw, hints_used)
    task_def = TASK_REGISTRY.get((task_id, variant_id))
    concept_id = task_def.concept_id if task_def else "attention_scaling"
    evidence = record_attempt_evidence(db, session_id, event, task_id, variant_id, concept_id, answer_raw, eval_result, hints_used)

    # Determine follow up task
    next_active_task = None
    if eval_result.next_task:
        next_tid, next_vid = eval_result.next_task
        next_tdef = TASK_REGISTRY.get((next_tid, next_vid))
        if next_tdef:
            next_active_task = {
                "task_id": next_tdef.task_id,
                "task_variant": next_tdef.variant_id,
                "question": next_tdef.question,
                "expected_type": next_tdef.expected_type,
            }

    decision = record_decision(db, session_id, evidence, eval_result, ["eq-scaling"], next_active_task["task_id"] if next_active_task else None)
    return evidence, decision, next_active_task


def record_open_task_attempt(
    db: Session,
    session_id: str,
    event: LearnerEvent,
    task_id: str,
    variant_id: str,
    concept_id: str,
    answer_raw: Any,
    is_correct: bool,
    assessment_status: str,
    gap: Optional[str],
    board_refs: list,
) -> ConceptEvidence:
    """Apply the same two-variant policy to a check the tutor wrote and keyed.

    Number and choice checks are graded deterministically ("checked"); explanations
    judged by the tutor stay "provisional".
    """
    hints_used = recorded_assistance_count(db, session_id, event, task_id, variant_id)
    eval_result = RubricEvaluation(
        is_correct=is_correct,
        confidence=assessment_status,
        feedback="",
        gap_identified=gap or (None if is_correct else "unidentified gap"),
        recommended_action="advance" if is_correct else "scaffold",
    )
    evidence = record_attempt_evidence(db, session_id, event, task_id, variant_id, concept_id, answer_raw, eval_result, hints_used)
    record_decision(db, session_id, evidence, eval_result, board_refs, None)
    return evidence


def record_attempt_evidence(
    db: Session,
    session_id: str,
    event: LearnerEvent,
    task_id: str,
    variant_id: str,
    concept_id: str,
    answer_raw: Any,
    eval_result: RubricEvaluation,
    hints_used: int,
) -> ConceptEvidence:
    """Persist the attempt and the evidence category it supports."""
    # Record TaskAttempt
    attempt_count = (
        db.query(TaskAttempt)
        .filter(TaskAttempt.session_id == session_id, TaskAttempt.task_id == task_id)
        .count()
    )
    attempt = TaskAttempt(
        session_id=session_id,
        task_id=task_id,
        task_variant=variant_id,
        learner_event_id=event.id,
        response_text=str(answer_raw),
        hint_count=hints_used,
        attempt_index=attempt_count + 1,
        assessment_status=eval_result.confidence,
        is_correct=eval_result.is_correct,
    )
    db.add(attempt)
    db.commit()

    # Query all successful distinct variants for this concept in this session
    successful_attempts = (
        db.query(TaskAttempt)
        .filter(
            TaskAttempt.session_id == session_id,
            TaskAttempt.task_id == task_id,
            TaskAttempt.is_correct.is_(True),
            TaskAttempt.hint_count == 0,
        )
        .all()
    )
    distinct_successful_variants = len(set(a.task_variant for a in successful_attempts))

    # Apply 2-variant progression policy from docs/11_LEARNING_OBSERVATION.md
    if eval_result.is_correct:
        if hints_used > 0:
            category = EvidenceCategory.SUPPORTED_WITH_HELP
            rationale = f"Student answered correctly after {hints_used} recorded help or feedback interaction(s) on variant {variant_id}."
        elif distinct_successful_variants >= 2:
            category = EvidenceCategory.SUPPORTED_INDEPENDENTLY
            rationale = f"Student independently solved 2 distinct application variants ({distinct_successful_variants} confirmed)."
        else:
            category = EvidenceCategory.SUPPORTED_WITH_HELP
            rationale = f"First independent success on variant {variant_id}. Advancing to second distinct application variant to confirm understanding."
    else:
        category = EvidenceCategory.NEEDS_CHECK
        rationale = f"Incorrect response '{answer_raw}' on variant {variant_id}. Gap identified: {eval_result.gap_identified or 'misconception'}."

    evidence = ConceptEvidence(
        session_id=session_id,
        event_id=event.id,
        task_id=task_id,
        concept_id=concept_id,
        category=category.value,
        assistance_level=AssistanceLevel.NONE.value if hints_used == 0 else AssistanceLevel.HINT_GIVEN.value,
        assessment_status=AssessmentStatus.PROVISIONAL.value if eval_result.confidence == "provisional" else AssessmentStatus.CHECKED.value,
        rationale=rationale,
    )
    db.add(evidence)
    db.commit()
    return evidence


def record_decision(
    db: Session,
    session_id: str,
    evidence: ConceptEvidence,
    eval_result: RubricEvaluation,
    board_refs: list,
    follow_up_task_id: Optional[str],
) -> TeachingDecision:
    decision = TeachingDecision(
        session_id=session_id,
        evidence_ids_json=json.dumps([evidence.id]),
        tentative_gap=eval_result.gap_identified,
        selected_action=eval_result.recommended_action,
        rationale=f"Observable check result: correct={eval_result.is_correct}. Action chosen: {eval_result.recommended_action}.",
        board_refs_json=json.dumps(board_refs),
        follow_up_task_id=follow_up_task_id,
    )
    db.add(decision)
    db.commit()
    return decision
