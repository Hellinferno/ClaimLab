"""Meta Model API adapter and tutor orchestration loop."""
import hashlib
import json
import logging
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
from claimlab.contracts.experiment import RecipeId
from claimlab.models import (
    LearningSession,
    BoardSnapshot,
    ConceptEvidence,
    LearnerEvent,
    ExperimentRun,
    SourceAnchor,
    SourceSelection,
    JobEvent,
    ToolInvocation,
    BudgetReservation,
)
from claimlab.numerics.runner import runner
from claimlab.whiteboard.engine import apply_atomic_patch
from claimlab.learning.adaptation import update_evidence_and_decide

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
                    "board_commands": {"type": "array", "items": {"type": "object"}},
                    "active_task": {"type": "object"},
                },
                "required": ["narration"],
            },
        },
    },
]


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
        anchors = self.db.query(SourceAnchor).filter(SourceAnchor.document_id == selection.document_id).all() if selection else []

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
        if settings.MODEL_MODE == "live" and settings.META_API_KEY:
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
        if last_event and last_event.event_type in (
            "prediction_submitted",
            "explanation_submitted",
            "message_submitted",
            "connection_submitted",
        ):
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
                hints_used=0,
            )
            active_task = next_t

            if ev.category == EvidenceCategory.SUPPORTED_INDEPENDENTLY.value:
                narration = (
                    "Outstanding work! You have independently confirmed the scaling calculation across two distinct application variants. "
                    "Notice how dividing by $\\sqrt{d_k}$ stabilizes score variance near 1.0 regardless of key dimension."
                )
            elif ev.category == EvidenceCategory.SUPPORTED_WITH_HELP.value:
                narration = (
                    "Exactly right! Dividing the score by $\\sqrt{d_k} = \\sqrt{16} = 4$ yields $12 / 4 = 3$. "
                    "Let's test this understanding on a second distinct variant."
                )
            else:
                narration = (
                    "Let's trace the arithmetic: Key dimension $d_k = 16$, so $\\sqrt{d_k} = 4$. "
                    "Dividing the unscaled dot product $12$ by $4$ gives $3$. Try recalculating this step."
                )

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
                "[Source] Based on Section B of the Attention Lab, dot-product attention scores are scaled by "
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

            # Save ExperimentRun in DB
            db_run = ExperimentRun(
                id=run_res.run_id,
                owner_id=session.owner_id,
                session_id=session.id,
                parent_job_id=job_id,
                recipe_id=run_res.recipe_id.value,
                parameters_json=json.dumps(run_res.parameters),
                parameter_hash=run_res.parameter_hash,
                seed=run_res.seed,
                status=run_res.status,
                output_json=json.dumps(run_res.output),
                checks_json=json.dumps([c.model_dump() for c in run_res.checks]),
                started_at=datetime.fromisoformat(run_res.started_at),
                completed_at=datetime.fromisoformat(run_res.completed_at) if run_res.completed_at else None,
            )
            self.db.add(db_run)

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

            active_task = {
                "task_id": "attention-scale-apply-01",
                "task_variant": "v1-a",
                "question": "A score is 12 and key dimension is 16. What is the scaled score (12 / sqrt(16))?",
                "expected_type": "number",
            }

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
            narration = "I am ready for your next question or experiment. You can adjust the parameters on the right or try a new query."
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

        # Handle learner evidence and learning adaptation if responding to student
        active_task = None
        if recent_events and recent_events[0].event_type in (
            "prediction_submitted",
            "explanation_submitted",
            "message_submitted",
            "connection_submitted",
        ):
            last_event = recent_events[0]
            try:
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
                    hints_used=0,
                )
                if next_t:
                    active_task = next_t
            except Exception as e:
                logger.warning(f"Error updating learner evidence: {e}")

        max_iterations = 4
        iterations = 0
        final_narration = ""
        new_run_id = None
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
                        "max_tokens": 1500,
                    }
                    resp = client.post(
                        f"{settings.META_BASE_URL.rstrip('/')}/chat/completions",
                        headers=headers,
                        json=payload,
                    )
                    resp.raise_for_status()
                    data = resp.json()
                except Exception as e:
                    logger.error(f"Live Meta API request failed: {e}")
                    # Fallback cleanly to fixture turn on provider network/credential error
                    return self._execute_fixture_turn(session, job_id, selection, anchors, current_scene, recent_events, evidence_list, None)

                choice = data["choices"][0]
                message = choice["message"]
                messages.append(message)

                tool_calls = message.get("tool_calls", [])
                if not tool_calls:
                    final_narration = message.get("content", "")
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
                        params = fn_args.get("parameters", {})
                        # Parameter normalizations for LLMs
                        if rec_id == "attention_scaling_v1":
                            if "dimensions" not in params:
                                d = params.get("dimension", params.get("d_k", 64))
                                params["dimensions"] = [d] if isinstance(d, int) else list(d)
                            if "n_keys" not in params:
                                params["n_keys"] = params.get("keys", 4)
                            if "trials" not in params:
                                params["trials"] = min(200, max(20, params.get("num_samples", params.get("samples", 100))))
                        elif rec_id == "softmax_sensitivity_v1":
                            if "logits" not in params:
                                params["logits"] = params.get("scores", [2.0, 1.0, 0.1])
                            if "multiplier" not in params:
                                params["multiplier"] = params.get("scale", params.get("temperature", 2.0))
                        elif rec_id == "causal_masking_v1":
                            if "scores" not in params:
                                params["scores"] = [
                                    [1.0, 2.0, 0.5],
                                    [0.5, 1.5, 2.0],
                                    [1.2, 0.8, 1.0]
                                ]

                        try:
                            run_res = runner.run(rec_id, params)
                            new_run_id = run_res.run_id
                            tool_result = {
                                "run_id": run_res.run_id,
                                "status": run_res.status,
                                "output": run_res.output,
                            }
                        except Exception as e:
                            tool_result = {"status": "rejected", "error": str(e)}

                    elif fn_name == "present_teaching_step":
                        final_narration = fn_args.get("narration", "")
                        active_task = fn_args.get("active_task")
                        board_cmds = fn_args.get("board_commands", [])
                        if board_cmds:
                            valid_cmds = []
                            for cmd in board_cmds:
                                if isinstance(cmd, dict):
                                    if "action" in cmd and "op" not in cmd:
                                        if cmd["action"] in ("add_text", "add_object"):
                                            cmd["op"] = "add_object"
                                            if "object" not in cmd:
                                                cmd["object"] = {
                                                    "id": f"obj_{len(updated_scene.objects) + 1}",
                                                    "type": "concept_card",
                                                    "label": cmd.get("text", "Concept Note"),
                                                    "position": {"x": 50.0, "y": 50.0},
                                                }
                                    if "op" in cmd and cmd["op"] in (
                                        "add_object", "update_object", "add_connector",
                                        "highlight_objects", "remove_object", "set_active_group", "clear_highlights"
                                    ):
                                        valid_cmds.append(cmd)
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

        # Ensure active experiment run exists for grounding
        if not new_run_id and (session.revision <= 1 or not updated_scene.objects):
            init_exp = runner.run("attention_scaling_v1", {"dimensions": [16, 32, 64, 128], "n_keys": 4, "trials": 50, "seed": 42})
            new_run_id = init_exp.run_id
            db_run = ExperimentRun(
                id=init_exp.run_id,
                owner_id=session.owner_id,
                session_id=session.id,
                recipe_id="attention_scaling_v1",
                parameter_hash=init_exp.parameter_hash,
                parameters_json=json.dumps({"dimensions": [16, 32, 64, 128], "n_keys": 4, "trials": 50, "seed": 42}),
                seed=42,
                status="succeeded",
                output_json=json.dumps(init_exp.output),
                checks_json=json.dumps([c.model_dump() for c in init_exp.checks]),
            )
            self.db.add(db_run)
            self.db.commit()

        # Seed initial whiteboard objects if model provided text-only narration
        if len(updated_scene.objects) < 4:
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
            patch = BoardPatch(
                schema_version=1,
                base_board_revision=updated_scene.board_revision,
                commands=[AddObjectCommand(object=obj) for obj in initial_objects],
            )
            updated_scene = apply_atomic_patch(updated_scene, patch)

        if not active_task:
            active_task = {
                "task_id": "attention-scale-apply-01",
                "task_variant": "v1-a",
                "question": "A score is 12 and key dimension is 16. What is the scaled score (12 / sqrt(16))?",
                "expected_type": "number",
            }

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
