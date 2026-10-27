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


def update_evidence_and_decide(
    db: Session,
    session_id: str,
    event: LearnerEvent,
    task_id: str,
    variant_id: str,
    answer_raw: Any,
    hints_used: int = 0,
) -> Tuple[ConceptEvidence, TeachingDecision, Optional[Dict[str, Any]]]:
    """
    Applies the 2-variant progression policy and records deterministic teaching decisions.
    """
    eval_result: RubricEvaluation = evaluate_task_submission(task_id, variant_id, answer_raw, hints_used)
    task_def = TASK_REGISTRY.get((task_id, variant_id))
    concept_id = task_def.concept_id if task_def else "attention_scaling"

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
        )
        .all()
    )
    distinct_successful_variants = len(set(a.task_variant for a in successful_attempts))

    # Apply 2-variant progression policy from docs/11_LEARNING_OBSERVATION.md
    if eval_result.is_correct:
        if hints_used > 0:
            category = EvidenceCategory.SUPPORTED_WITH_HELP
            rationale = f"Student answered correctly using {hints_used} hint(s) on variant {variant_id}."
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
        assessment_status=AssessmentStatus.CHECKED.value,
        rationale=rationale,
    )
    db.add(evidence)
    db.commit()

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

    decision = TeachingDecision(
        session_id=session_id,
        evidence_ids_json=json.dumps([evidence.id]),
        tentative_gap=eval_result.gap_identified,
        selected_action=eval_result.recommended_action,
        rationale=f"Observable check result: correct={eval_result.is_correct}. Action chosen: {eval_result.recommended_action}.",
        board_refs_json=json.dumps(["eq-scaling"]),
        follow_up_task_id=next_active_task["task_id"] if next_active_task else None,
    )
    db.add(decision)
    db.commit()

    return evidence, decision, next_active_task
