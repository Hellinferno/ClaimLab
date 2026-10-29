"""Meta Model API adapter and tutor orchestration loop."""
import hashlib
import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
import httpx
from sqlalchemy.orm import Session

from claimlab.config import settings
from claimlab.contracts.common import EvidenceCategory, AssessmentStatus, AssistanceLevel
from claimlab.contracts.whiteboard import (
    SceneGraph,
    BoardObject,
    ObjectType,
    Position,
    Dimensions,
    BoardPatch,
    AddObjectCommand,
)
from claimlab.contracts.experiment import ExperimentRunResponse, RecipeId
from claimlab.models import (
    LearningSession,
    BoardSnapshot,
    ConceptEvidence,
    LearnerEvent,
    ExperimentRun,
    SourceAnchor,
    SourceSelection,
    Job,
    JobEvent,
    ToolInvocation,
    BudgetReservation,
)
from claimlab.numerics.runner import runner, serialize_run_evidence
from claimlab.whiteboard.engine import apply_atomic_patch
from claimlab.learning.adaptation import update_evidence_and_decide
from claimlab.learning.task_bank import TASK_REGISTRY

logger = logging.getLogger(__name__)

META_SYSTEM_PROMPT = """You are ClaimLab's teaching coordinator for one supported learning session.
Help the student understand the selected technical material through clear whiteboard steps, supported computational investigations, and relevant follow-up tasks.
Use the supplied source anchors and current session state.
Distinguish source statements, added background, assumptions, measured results, and interpretations.
Never invent an experiment result or a source citation.
Use observable learner evidence when changing the lesson, retain uncertainty, and ask a short diagnostic question when needed.
Do not certify mastery from passive exposure or a single answer.
Keep explanations concise and make one meaningful next step clear."""

TOOLS_SPEC = [
    {
        "type": "function",
        "function": {
            "name": "get_source_excerpt",
            "description": "Fetch validated quote for existing anchor IDs in this selection",
            "parameters": {
                "type": "object",
                "properties": {
                    "anchor_ids": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["anchor_ids"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_experiment",
            "description": "Execute one of the three reviewed numerical recipes",
            "parameters": {
                "type": "object",
                "properties": {
                    "recipe_id": {
                        "type": "string",
                        "enum": ["softmax_sensitivity_v1", "attention_scaling_v1", "causal_masking_v1"],
                    },
                    "parameters": {"type": "object"},
                },
                "required": ["recipe_id", "parameters"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "present_teaching_step",
            "description": "Atomic teaching step containing narration blocks, board commands, and optional task",
            "parameters": {
                "type": "object",
                "properties": {
                    "narration": {"type": "string"},
                    "board_commands": {
                        "type": "array",
                        "description": "Short whiteboard notes added beside the reviewed diagram",
                        "items": {
                            "type": "object",
                            "properties": {
                                "action": {"type": "string", "enum": ["add_text"]},
                                "label": {"type": "string", "description": "Note title, a few words"},
                                "text": {"type": "string", "description": "One short sentence"},
                            },
                            "required": ["action", "label"],
                        },
                    },
                    "active_task": {"type": "object"},
                },
                "required": ["narration"],
            },
        },
    },
]


ANSWER_EVENTS = ("prediction_submitted", "explanation_submitted", "connection_submitted")

DEFAULT_TASK = {
    "task_id": "attention-scale-apply-01",
    "task_variant": "v1-a",
    "question": "A score is 12 and key dimension is 16. What is the scaled score (12 / sqrt(16))?",
    "expected_type": "number",
}


RECIPE_PARAM_ALIASES = {
    "attention_scaling_v1": {
        "dimension": "dimensions", "d_k": "dimensions", "d_k_values": "dimensions",
        "keys": "n_keys", "num_samples": "trials", "samples": "trials",
    },
    "softmax_sensitivity_v1": {"scores": "logits", "scale": "multiplier", "temperature": "multiplier"},
}

BOARD_OPS = ("add_object", "update_object", "add_connector", "highlight_objects", "remove_object", "set_active_group", "clear_highlights")
TEXT_BOARD_ACTIONS = ("add_text", "add_object", "add_note", "write")


class ProviderUnavailableError(RuntimeError):
    """A live teaching turn failed; fixture substitution is never implicit."""


def normalize_recipe_parameters(recipe_id: Optional[str], params: Dict[str, Any]) -> Dict[str, Any]:
    """Map common model spellings onto a recipe's schema and fill reviewed defaults.

    Alias keys are removed, since strict validation rejects any extra field.
    """
    params = dict(params)
    for alias, field in RECIPE_PARAM_ALIASES.get(recipe_id, {}).items():
        if alias in params:
            value = params.pop(alias)
            if alias == "temperature" and isinstance(value, (int, float)) and value > 0:
                value = 1 / value  # softmax(s / T) multiplies scores by 1/T
            params.setdefault(field, value)
    if recipe_id == "attention_scaling_v1":
        dimensions = params.get("dimensions", 64)
        params["dimensions"] = [dimensions] if isinstance(dimensions, int) else list(dimensions)
        params.setdefault("n_keys", 4)
        params["trials"] = min(200, max(20, params.get("trials", 100)))
    elif recipe_id == "softmax_sensitivity_v1":
        params.setdefault("logits", [2.0, 1.0, 0.1])
        params.setdefault("multiplier", 2.0)
    elif recipe_id == "causal_masking_v1":
        params.setdefault("scores", [[1.0, 2.0, 0.5], [0.5, 1.5, 2.0], [1.2, 0.8, 1.0]])
    return params


def normalize_board_command(cmd: Any, note_index: int) -> Optional[Dict[str, Any]]:
    """Accept a board patch command, turning a simple text-style action into a valid text note.

    Models often send {"action": "write", "label": ..., "text": ...}. Notes are laid
    out in two columns below the reviewed diagram; the patch engine still
    validates every command before it reaches the board.
    """
    if not isinstance(cmd, dict):
        return None
    if "op" not in cmd and cmd.get("action") in TEXT_BOARD_ACTIONS:
        if "object" in cmd:
            cmd = {**cmd, "op": "add_object"}
        else:
            text = str(cmd.get("text") or cmd.get("content") or "").strip()
            label = str(cmd.get("label") or text or "Concept note").strip()
            cmd = {"op": "add_object", "object": {
                "id": f"note-{uuid.uuid4().hex[:8]}",
                "type": ObjectType.TEXT.value,
                "label": label[:120],
                "position": {"x": 50.0 + 370.0 * (note_index % 2), "y": 350.0 + 95.0 * (note_index // 2)},
                "dimensions": {"width": 350.0, "height": 80.0},
                "payload": {"text": text[:300]} if text and text != label else {},
            }}
    return cmd if cmd.get("op") in BOARD_OPS else None


def latest_tutor_step(db: Session, session_id: str) -> Dict[str, Any]:
    """Payload of the session's latest completed tutor turn: its narration and active task."""
    step = (
        db.query(JobEvent)
        .join(Job, Job.id == JobEvent.job_id)
        .filter(Job.session_id == session_id, JobEvent.event_type == "tutor_turn_completed")
        .order_by(JobEvent.created_at.desc(), JobEvent.id.desc())
        .first()
    )
    return json.loads(step.payload_json) if step else {}


def experiment_run_record(
    run: ExperimentRunResponse, owner_id: str, session_id: str, parent_job_id: str,
) -> ExperimentRun:
    """Retained run row built from the runner's canonical result."""
    return ExperimentRun(
        id=run.run_id,
        owner_id=owner_id,
        session_id=session_id,
        parent_job_id=parent_job_id,
        recipe_id=run.recipe_id.value,
        parameters_json=json.dumps(run.parameters),
        parameter_hash=run.parameter_hash,
        seed=run.seed,
        status=run.status,
        output_json=json.dumps(run.output),
        checks_json=serialize_run_evidence(run),
        started_at=datetime.fromisoformat(run.started_at),
        completed_at=datetime.fromisoformat(run.completed_at) if run.completed_at else None,
    )


class AgentOrchestrator:
    """Coordinates tutor turns between Meta Model API (or fixture) and application state."""

    def __init__(self, db: Session):
        self.db = db

    def execute_tutor_turn(
        self,
        session_id: str,
        job_id: str,
        trigger_event_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Runs a complete bounded tutor turn."""
        learning_session = self.db.query(LearningSession).filter(LearningSession.id == session_id).first()
        if not learning_session:
            raise ValueError(f"Session {session_id} not found")

        selection = self.db.query(SourceSelection).filter(SourceSelection.id == learning_session.selection_id).first()
        anchors = self.db.query(SourceAnchor).filter(
            SourceAnchor.document_id == selection.document_id,
            SourceAnchor.page_number.between(selection.page_start, selection.page_end),
        ).order_by(SourceAnchor.page_number, SourceAnchor.start_offset).all() if selection else []

        latest_snapshot = (
            self.db.query(BoardSnapshot)
            .filter(BoardSnapshot.session_id == session_id)
            .order_by(BoardSnapshot.revision.desc())
            .first()
        )
        current_scene_dict = (
            json.loads(latest_snapshot.scene_json)
            if latest_snapshot
            else {"schema_version": 1, "board_revision": 0, "objects": []}
        )
        current_scene = SceneGraph(**current_scene_dict)

        recent_events = (
            self.db.query(LearnerEvent)
            .filter(LearnerEvent.session_id == session_id)
            .order_by(LearnerEvent.sequence.desc())
            .limit(5)
            .all()
        )

        evidence_list = (
            self.db.query(ConceptEvidence)
            .filter(ConceptEvidence.session_id == session_id)
            .all()
        )

        # Decide whether to execute live Meta API or deterministic fixture
        if settings.MODEL_MODE == "live":
            if not settings.META_API_KEY:
                raise ProviderUnavailableError("Live tutor is not configured. Your saved work is available.")
            return self._execute_live_turn(learning_session, job_id, selection, anchors, current_scene, recent_events, evidence_list)
        else:
            return self._execute_fixture_turn(learning_session, job_id, selection, anchors, current_scene, recent_events, evidence_list, trigger_event_id)

    def _execute_fixture_turn(
        self,
        session: LearningSession,
        job_id: str,
        selection: Optional[SourceSelection],
        anchors: List[SourceAnchor],
        current_scene: SceneGraph,
        recent_events: List[LearnerEvent],
        evidence_list: List[ConceptEvidence],
        trigger_event_id: Optional[str],
    ) -> Dict[str, Any]:
        """Deterministic teaching turn producing reviewed whiteboard steps and experiments."""
        last_event = recent_events[0] if recent_events else None
        next_revision = session.revision + 1

        narration = ""
        active_task = None
        new_run_id = None
        updated_scene = current_scene

        # Check if responding to student event
        if last_event and last_event.event_type in ANSWER_EVENTS:
            payload = json.loads(last_event.payload_json)
            answer = payload.get("answer", payload.get("edges", ""))
            task_id = payload.get("task_id", "attention-scale-apply-01")
            task_variant = payload.get("task_variant", "v1-a")

            ev, dec, next_t = update_evidence_and_decide(
                self.db,
                session.id,
                last_event,
                task_id,
                task_variant,
                answer,
            )
            active_task = next_t

            if ev.category == EvidenceCategory.SUPPORTED_INDEPENDENTLY.value:
                narration = (
                    "Outstanding work! You have independently confirmed the scaling calculation across two distinct application variants. "
                    "Notice how dividing by $\\sqrt{d_k}$ stabilizes score variance near 1.0 regardless of key dimension."
                )
            elif ev.category == EvidenceCategory.SUPPORTED_WITH_HELP.value:
                narration = (
                    "Your answer matches the task's checked rubric. "
                    "Let's test this understanding on a different application."
                )
            else:
                task_def = TASK_REGISTRY.get((task_id, task_variant))
                hint = task_def.hint if task_def else "Check the current task's quantities and try again."
                narration = f"[Background] Let's inspect this step together. {hint}"

            # Advance board revision
            updated_scene = SceneGraph(
                schema_version=current_scene.schema_version,
                board_revision=next_revision,
                objects=current_scene.objects,
                active_group=current_scene.active_group,
            )

        elif not current_scene.objects:
            # Initial Turn: Run attention scaling recipe and populate board via atomic patch
            narration = (
                "[Background] This fixture lesson illustrates attention scaling. Dot-product attention scores are scaled by "
                "$\\frac{1}{\\sqrt{d_k}}$ to prevent extreme growth with large vector dimensions.\n"
                "[Experiment] Below, the whiteboard charts simulated score variances across dimensions 8, 32, and 128. "
                "Notice that unscaled variance increases linearly with $d_k$, while scaled variance remains stable near 1.0."
            )

            # Execute real attention scaling recipe
            run_res = runner.run(RecipeId.ATTENTION_SCALING.value, {
                "dimensions": [8, 32, 128],
                "n_keys": 8,
                "trials": 50,
                "seed": 42,
            })
            new_run_id = run_res.run_id
            self.db.add(experiment_run_record(run_res, session.owner_id, session.id, job_id))

            # Build whiteboard objects through atomic patch engine
            initial_objects = [
                BoardObject(
                    id="node-q",
                    type=ObjectType.CONCEPT_NODE,
                    position=Position(x=50, y=60),
                    dimensions=Dimensions(width=140, height=60),
                    label="Query Vector (Q)",
                    concept_id="query_key_scores",
                    payload={"title": "Query (Q)", "description": "Current token representation"},
                ),
                BoardObject(
                    id="node-k",
                    type=ObjectType.CONCEPT_NODE,
                    position=Position(x=230, y=60),
                    dimensions=Dimensions(width=140, height=60),
                    label="Key Vectors (K)",
                    concept_id="query_key_scores",
                    payload={"title": "Keys (K)", "description": "Context tokens representations"},
                ),
                BoardObject(
                    id="node-scores",
                    type=ObjectType.CONCEPT_NODE,
                    position=Position(x=140, y=160),
                    dimensions=Dimensions(width=160, height=60),
                    label="Raw Scores S = Q·K^T",
                    concept_id="attention_scaling",
                    payload={"title": "Raw Dot Products", "description": "Var(S) grows proportionally to d_k"},
                ),
                BoardObject(
                    id="eq-scaling",
                    type=ObjectType.EQUATION,
                    position=Position(x=80, y=250),
                    dimensions=Dimensions(width=280, height=70),
                    label="Scaled Attention Formula",
                    concept_id="attention_scaling",
                    payload={"latex": r"\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{Q K^T}{\sqrt{d_k}}\right) V"},
                ),
                BoardObject(
                    id="plot-scaling-var",
                    type=ObjectType.PLOT_REF,
                    position=Position(x=420, y=60),
                    dimensions=Dimensions(width=320, height=260),
                    label="Variance vs Key Dimension",
                    concept_id="attention_scaling",
                    payload={
                        "run_id": new_run_id,
                        "field": "results",
                        "title": "Score Variance: Scaled vs Unscaled",
                        "x_label": "Key Dimension (d_k)",
                        "y_label": "Variance",
                    },
                ),
            ]

            patch_cmds = [AddObjectCommand(object=obj) for obj in initial_objects]
            patch = BoardPatch(
                schema_version=1,
                base_board_revision=current_scene.board_revision,
                commands=patch_cmds,
            )
            updated_scene = apply_atomic_patch(current_scene, patch)

            active_task = dict(DEFAULT_TASK)

            ev_init = ConceptEvidence(
                session_id=session.id,
                concept_id="attention_scaling",
                category=EvidenceCategory.INTRODUCED.value,
                assistance_level=AssistanceLevel.NONE.value,
                assessment_status=AssessmentStatus.CHECKED.value,
                rationale="Introduced attention scaling formula and simulated variance comparison experiment.",
            )
            self.db.add(ev_init)
            self.db.commit()

        else:
            # Asking for help is context, not a failed numerical assessment.
            active_task = latest_tutor_step(self.db, session.id).get("active_task")
            if last_event and last_event.event_type == "hint_requested" and active_task:
                task_def = TASK_REGISTRY.get((active_task.get("task_id"), active_task.get("task_variant")))
                narration = f"[Background] Try this strategy: {task_def.hint}" if task_def else "[Background] Break the current task into one calculation at a time."
            else:
                narration = (
                    "[Background] Fixture mode offers a fixed explanation rather than a live answer to your question. "
                    "Queries and keys produce scores; dividing by the square root of key dimension controls their scale. "
                    "Softmax turns scores into weights, which combine the values. Your current task is still available."
                )
            updated_scene = SceneGraph(
                schema_version=current_scene.schema_version,
                board_revision=next_revision,
                objects=current_scene.objects,
                active_group=current_scene.active_group,
            )

        # Save new board snapshot
        snapshot = BoardSnapshot(
            session_id=session.id,
            revision=updated_scene.board_revision,
            schema_version=1,
            scene_json=json.dumps(updated_scene.model_dump()),
        )
        self.db.add(snapshot)

        # Update session
        session.revision = updated_scene.board_revision
        session.active_concept = "attention_scaling"
        session.active_job_id = None
        self.db.commit()

        # Emit job event
        event_count = self.db.query(JobEvent).filter(JobEvent.job_id == job_id).count()
        event = JobEvent(
            job_id=job_id,
            sequence=event_count + 1,
            event_type="tutor_turn_completed",
            payload_json=json.dumps({
                "narration": narration,
                "revision": updated_scene.board_revision,
                "active_task": active_task,
                "run_id": new_run_id,
            }),
        )
        self.db.add(event)
        self.db.commit()

        return {
            "narration": narration,
            "revision": updated_scene.board_revision,
            "scene": updated_scene.model_dump(),
            "active_task": active_task,
            "run_id": new_run_id,
            "mode": "fixture",
        }

    def _execute_live_turn(
        self,
        session: LearningSession,
        job_id: str,
        selection: Optional[SourceSelection],
        anchors: List[SourceAnchor],
        current_scene: SceneGraph,
        recent_events: List[LearnerEvent],
        evidence_list: List[ConceptEvidence],
    ) -> Dict[str, Any]:
        """Executes a bounded live tool loop against the Meta Model API."""
        headers = {
            "Authorization": f"Bearer {settings.META_API_KEY}",
            "Content-Type": "application/json",
        }

        # Bounded token context construction
        anchor_summary = "\n".join(f"[{a.id}] (Page {a.page_number}): \"{a.quote[:200]}\"" for a in anchors[:10])
        scene_summary = json.dumps([{"id": o.id, "type": o.type, "label": o.label} for o in current_scene.objects])
        evidence_summary = json.dumps({e.concept_id: e.category for e in evidence_list})

        user_content = (
            f"Learning Goal: {session.goal or 'Understand selected attention mechanisms'}\n"
            f"Current Revision: {session.revision}\n"
            f"Grounding Anchors:\n{anchor_summary}\n"
            f"Active Whiteboard Objects: {scene_summary}\n"
            f"Learner Evidence: {evidence_summary}\n"
        )
        if recent_events:
            last_ev = recent_events[0]
            user_content += f"Latest Learner Event: {last_ev.event_type} - {last_ev.payload_json}\n"

        messages = [
            {"role": "system", "content": META_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]

        # Budget reservation (tracking expected costs)
        budget = BudgetReservation(
            owner_id=session.owner_id,
            request_id=job_id,
            reserved_amount_usd=0.01,
            status="reserved",
            model_name=settings.META_MODEL,
        )
        self.db.add(budget)
        self.db.commit()

        last_event = recent_events[0] if recent_events else None
        requested_hint = bool(last_event and last_event.event_type == "hint_requested")
        answered = bool(last_event and last_event.event_type in ANSWER_EVENTS)
        previous_task = latest_tutor_step(self.db, session.id).get("active_task")
        model_task = None
        if requested_hint:
            messages[0]["content"] += " The learner requested a hint: offer one scaffold without revealing the full answer, and keep the current task active."

        max_iterations = 4
        iterations = 0
        final_narration = ""
        new_run_id = None
        scaling_run_id = None
        next_revision = session.revision + 1
        updated_scene = current_scene.model_copy(deep=True)
        updated_scene.board_revision = next_revision

        with httpx.Client(timeout=25.0) as client:
            while iterations < max_iterations:
                iterations += 1
                try:
                    payload = {
                        "model": settings.META_MODEL,
                        "messages": messages,
                        "tools": TOOLS_SPEC,
                        "tool_choice": "auto",
                        # Reasoning tokens count against this limit; 1500 truncated
                        # replies to empty content without a tool call.
                        "max_tokens": 4096,
                    }
                    resp = client.post(
                        f"{settings.META_BASE_URL.rstrip('/')}/chat/completions",
                        headers=headers,
                        json=payload,
                    )
                    resp.raise_for_status()
                    data = resp.json()
                except Exception as e:
                    logger.error("Live Meta API request failed (%s)", type(e).__name__)
                    budget.status = "released"
                    self.db.commit()
                    raise ProviderUnavailableError(
                        "The live tutor is unavailable. Your saved lesson is available; try again."
                    ) from e

                choice = data["choices"][0]
                message = choice["message"]
                messages.append(message)

                tool_calls = message.get("tool_calls") or []
                if not tool_calls:
                    final_narration = message.get("content") or final_narration
                    if not final_narration:
                        logger.warning("Live tutor reply had no narration (finish_reason=%s)", choice.get("finish_reason"))
                    break

                for tc in tool_calls:
                    fn_name = tc["function"]["name"]
                    fn_args = json.loads(tc["function"].get("arguments", "{}"))
                    call_id = tc["id"]

                    # Deduplicate ToolInvocation
                    arg_hash = hashlib.sha256(json.dumps(fn_args, sort_keys=True).encode("utf-8")).hexdigest()
                    tool_inv = ToolInvocation(
                        job_id=job_id,
                        provider_call_id=call_id,
                        tool_name=fn_name,
                        argument_hash=arg_hash,
                        status="executing",
                    )
                    self.db.add(tool_inv)
                    self.db.commit()

                    tool_result: Any = {}
                    if fn_name == "get_source_excerpt":
                        requested_ids = set(fn_args.get("anchor_ids", []))
                        matched = [a.quote for a in anchors if a.id in requested_ids]
                        tool_result = {"excerpts": matched}

                    elif fn_name == "run_experiment":
                        rec_id = fn_args.get("recipe_id")
                        try:
                            run_res = runner.run(rec_id, normalize_recipe_parameters(rec_id, fn_args.get("parameters") or {}))
                            new_run_id = run_res.run_id
                            if run_res.recipe_id == RecipeId.ATTENTION_SCALING:
                                scaling_run_id = run_res.run_id
                            self.db.add(experiment_run_record(run_res, session.owner_id, session.id, job_id))
                            tool_result = {
                                "run_id": run_res.run_id,
                                "status": run_res.status,
                                "output": run_res.output,
                            }
                        except Exception as e:
                            tool_result = {"status": "rejected", "error": str(e)}

                    elif fn_name == "present_teaching_step":
                        final_narration = fn_args.get("narration", "")
                        model_task = fn_args.get("active_task")
                        board_cmds = fn_args.get("board_commands") or []
                        if board_cmds:
                            notes = sum(1 for o in updated_scene.objects if o.type == ObjectType.TEXT)
                            valid_cmds = []
                            for cmd in board_cmds:
                                normalized = normalize_board_command(cmd, notes + len(valid_cmds))
                                if normalized:
                                    valid_cmds.append(normalized)
                                else:
                                    logger.warning(
                                        "Ignored model board command (action=%s, keys=%s)",
                                        cmd.get("action") if isinstance(cmd, dict) else None,
                                        sorted(cmd) if isinstance(cmd, dict) else type(cmd).__name__,
                                    )
                            if valid_cmds:
                                try:
                                    patch = BoardPatch(
                                        schema_version=1,
                                        base_board_revision=updated_scene.board_revision,
                                        commands=valid_cmds,
                                    )
                                    updated_scene = apply_atomic_patch(updated_scene, patch)
                                except Exception as e:
                                    logger.warning(f"Skipping invalid model board commands: {e}")
                        tool_result = {"status": "step_committed", "revision": updated_scene.board_revision}

                    tool_inv.status = "completed"
                    tool_inv.result_reference = json.dumps(tool_result)[:500]
                    self.db.commit()

                    messages.append({
                        "role": "tool",
                        "tool_call_id": call_id,
                        "content": json.dumps(tool_result),
                    })

        budget.status = "settled"
        budget.settled_amount_usd = 0.005
        self.db.commit()

        graded_task = None
        if answered:
            # Grade only after the provider turn succeeded: a failed turn leaves no
            # attempt behind, so the learner's retry is assessed exactly once.
            try:
                payload = json.loads(last_event.payload_json)
                _, _, graded_task = update_evidence_and_decide(
                    self.db,
                    session.id,
                    last_event,
                    payload.get("task_id", "attention-scale-apply-01"),
                    payload.get("task_variant", "v1-a"),
                    payload.get("answer", payload.get("edges", "")),
                )
            except Exception as e:
                logger.warning(f"Error updating learner evidence: {e}")
                graded_task = previous_task

        # Ensure initial concept evidence exists
        ev_exists = self.db.query(ConceptEvidence).filter(
            ConceptEvidence.session_id == session.id,
            ConceptEvidence.concept_id == "attention_scaling",
        ).first()
        if not ev_exists:
            ev_init = ConceptEvidence(
                session_id=session.id,
                concept_id="attention_scaling",
                category=EvidenceCategory.INTRODUCED.value,
                assistance_level=AssistanceLevel.NONE.value,
                assessment_status=AssessmentStatus.CHECKED.value,
                rationale="Introduced attention scaling formula and simulated variance comparison experiment.",
            )
            self.db.add(ev_init)
            self.db.commit()

        # The seeded diagram's scaling plot needs a retained scaling run, whatever
        # recipe the model chose; the first turn always grounds on a run.
        seed_board = sum(1 for o in updated_scene.objects if o.type != ObjectType.TEXT) < 4
        if (seed_board and not scaling_run_id) or (not new_run_id and (session.revision <= 1 or not updated_scene.objects)):
            init_exp = runner.run("attention_scaling_v1", {"dimensions": [16, 32, 64, 128], "n_keys": 4, "trials": 50, "seed": 42})
            new_run_id = scaling_run_id = init_exp.run_id
            self.db.add(experiment_run_record(init_exp, session.owner_id, session.id, job_id))
            self.db.commit()

        # Seed the reviewed diagram when the model's notes left the board without one
        if seed_board:
            initial_objects = [
                BoardObject(
                    id="node-q",
                    type=ObjectType.CONCEPT_NODE,
                    position=Position(x=50, y=60),
                    dimensions=Dimensions(width=140, height=60),
                    label="Query Vector (Q)",
                    concept_id="query_key_scores",
                    payload={"title": "Query (Q)", "description": "Current token representation"},
                ),
                BoardObject(
                    id="node-k",
                    type=ObjectType.CONCEPT_NODE,
                    position=Position(x=230, y=60),
                    dimensions=Dimensions(width=140, height=60),
                    label="Key Vectors (K)",
                    concept_id="query_key_scores",
                    payload={"title": "Keys (K)", "description": "Context tokens representations"},
                ),
                BoardObject(
                    id="node-scores",
                    type=ObjectType.CONCEPT_NODE,
                    position=Position(x=140, y=160),
                    dimensions=Dimensions(width=160, height=60),
                    label="Raw Scores S = Q·K^T",
                    concept_id="attention_scaling",
                    payload={"title": "Raw Dot Products", "description": "Var(S) grows proportionally to d_k"},
                ),
                BoardObject(
                    id="eq-scaling",
                    type=ObjectType.EQUATION,
                    position=Position(x=80, y=250),
                    dimensions=Dimensions(width=280, height=70),
                    label="Scaled Attention Formula",
                    concept_id="attention_scaling",
                    payload={"latex": r"\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{Q K^T}{\sqrt{d_k}}\right) V"},
                ),
                BoardObject(
                    id="plot-scaling-var",
                    type=ObjectType.PLOT_REF,
                    position=Position(x=420, y=60),
                    dimensions=Dimensions(width=320, height=260),
                    label="Variance vs Key Dimension",
                    concept_id="attention_scaling",
                    payload={
                        "run_id": scaling_run_id,
                        "field": "results",
                        "title": "Score Variance: Scaled vs Unscaled",
                        "x_label": "Key Dimension (d_k)",
                        "y_label": "Variance",
                    },
                ),
            ]
            existing_ids = {o.id for o in updated_scene.objects}
            patch = BoardPatch(
                schema_version=1,
                base_board_revision=updated_scene.board_revision,
                commands=[AddObjectCommand(object=obj) for obj in initial_objects if obj.id not in existing_ids],
            )
            updated_scene = apply_atomic_patch(updated_scene, patch)

        if requested_hint:
            active_task = previous_task
        elif answered:
            # Reviewed task-bank progression decides what follows an answer; none
            # remains once the sequence is complete, as in fixture turns.
            active_task = graded_task or model_task
        else:
            # Questions and other help keep the learner's current task.
            active_task = model_task or previous_task or dict(DEFAULT_TASK)

        if not final_narration:
            final_narration = "Let us examine how scaling dot products stabilizes variance across dimensions."

        # Save snapshot
        snapshot = BoardSnapshot(
            session_id=session.id,
            revision=updated_scene.board_revision,
            schema_version=1,
            scene_json=json.dumps(updated_scene.model_dump()),
        )
        self.db.add(snapshot)
        session.revision = updated_scene.board_revision
        session.active_job_id = None
        self.db.commit()

        # Emit job event
        event_count = self.db.query(JobEvent).filter(JobEvent.job_id == job_id).count()
        event = JobEvent(
            job_id=job_id,
            sequence=event_count + 1,
            event_type="tutor_turn_completed",
            payload_json=json.dumps({
                "narration": final_narration,
                "revision": updated_scene.board_revision,
                "active_task": active_task,
                "run_id": new_run_id,
            }),
        )
        self.db.add(event)
        self.db.commit()

        return {
            "narration": final_narration,
            "revision": updated_scene.board_revision,
            "scene": updated_scene.model_dump(),
            "active_task": active_task,
            "run_id": new_run_id,
            "mode": "live",
        }
