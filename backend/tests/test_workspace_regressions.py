"""Regressions for consequential workspace actions, resume, and truthful failures."""
import json
import uuid
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from threading import Event
from datetime import datetime, timedelta, timezone

import httpx
import numpy as np
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from claimlab.api import app
from claimlab.config import settings
from claimlab.database import Base, get_db
from claimlab.models import ExperimentRun, Job, LearnerEvent, TaskAttempt
from claimlab.numerics.runner import runner
import claimlab.api as api_module
from claimlab import models


@pytest.fixture
def workspace(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "MODEL_MODE", "fixture")
    monkeypatch.setattr(settings, "DATA_DIR", str(tmp_path))
    isolated_engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool,
    )
    Base.metadata.create_all(isolated_engine)
    factory = sessionmaker(bind=isolated_engine)

    def isolated_db():
        with factory() as db:
            yield db

    app.dependency_overrides[get_db] = isolated_db
    client = TestClient(app)
    guest = client.post("/api/v1/guest-sessions")
    headers = {"X-CSRF-Token": guest.json()["csrf_token"]}
    try:
        yield client, headers, factory
    finally:
        client.close()
        app.dependency_overrides.pop(get_db, None)
        isolated_engine.dispose()


def distinct_pdf(index):
    """The example note with a trailing comment: same text, different document bytes."""
    return Path("examples/claimlab_attention_lab.pdf").read_bytes() + f"\n% copy {index}\n".encode()


class UnavailableProvider:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def post(self, *args, **kwargs):
        raise httpx.ConnectError("simulated provider outage")


def create_source(client, headers):
    content = Path("examples/claimlab_attention_lab.pdf").read_bytes()
    uploaded = client.post(
        "/api/v1/documents", headers=headers,
        files={"file": ("attention.pdf", content, "application/pdf")},
    )
    assert uploaded.status_code == 202
    document_id = uploaded.json()["document_id"]
    selected = client.post(
        f"/api/v1/documents/{document_id}/selections", headers=headers,
        json={"page_start": 2, "page_end": 2, "question": "Why scale attention scores?"},
    )
    assert selected.status_code == 201
    return selected.json()


def create_session(client, headers):
    source = create_source(client, headers)
    created = client.post("/api/v1/learning-sessions", headers=headers, json={"selection_id": source["selection_id"]})
    assert created.status_code == 202
    session_id = created.json()["session_id"]
    state = client.get(f"/api/v1/learning-sessions/{session_id}").json()
    return session_id, state, source


def test_bootstrap_preserves_owner_csrf_and_complete_resume(workspace):
    client, headers, _ = workspace
    session_id, before, source = create_session(client, headers)
    original_owner = client.get("/api/v1/me").json()
    original_cookie = client.cookies.get("claimlab_guest")

    reboot = client.post("/api/v1/guest-sessions")
    assert reboot.status_code == 201
    assert client.cookies.get("claimlab_guest") == original_cookie
    assert reboot.json()["csrf_token"] == headers["X-CSRF-Token"]
    assert client.get("/api/v1/me").json() == original_owner
    assert client.get("/api/v1/learning-sessions/active").json()["active_session_id"] == session_id
    restored = client.get(f"/api/v1/learning-sessions/{session_id}").json()
    assert restored["board"] == before["board"]
    assert restored["source_selection"] == source
    assert restored["tutor_narration"]
    assert all(anchor["page_number"] == 2 for anchor in restored["source_selection"]["anchors"])


def test_answer_retry_is_idempotent_and_changed_answer_conflicts(workspace):
    client, headers, factory = workspace
    session_id, state, _ = create_session(client, headers)
    event = {
        "event_id": str(uuid.uuid4()), "event_type": "explanation_submitted",
        "expected_revision": state["revision"],
        "payload": {"task_id": "attention-scale-apply-01", "task_variant": "v1-a", "answer": "3"},
    }
    keyed_headers = {**headers, "Idempotency-Key": str(uuid.uuid4())}
    url = f"/api/v1/learning-sessions/{session_id}/events"
    accepted = client.post(url, headers=keyed_headers, json=event)
    assert accepted.status_code == 202
    replayed = client.post(url, headers=keyed_headers, json=event)
    assert replayed.status_code == 202
    assert replayed.json() == accepted.json()
    event["payload"]["answer"] = "100"
    conflict = client.post(url, headers=keyed_headers, json=event)
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "IDEMPOTENCY_CONFLICT"
    with factory() as db:
        assert db.query(LearnerEvent).filter_by(session_id=session_id).count() == 1
        assert db.query(TaskAttempt).filter_by(session_id=session_id).count() == 1


def test_free_question_preserves_task_and_does_not_grade_understanding(workspace):
    client, headers, factory = workspace
    session_id, state, _ = create_session(client, headers)
    response = client.post(
        f"/api/v1/learning-sessions/{session_id}/events", headers=headers,
        json={"event_type": "message_submitted", "expected_revision": state["revision"],
              "payload": {"message": "What do the keys represent?"}},
    )
    assert response.status_code == 202
    after = client.get(f"/api/v1/learning-sessions/{session_id}").json()
    assert after["active_task"] == state["active_task"]
    assert after["evidence_summary"] == state["evidence_summary"]
    assert "Fixture mode" in after["tutor_narration"]
    with factory() as db:
        assert db.query(TaskAttempt).filter_by(session_id=session_id).count() == 0


def test_second_variant_wrong_answer_receives_its_own_hint(workspace):
    client, headers, _ = workspace
    session_id, state, _ = create_session(client, headers)
    url = f"/api/v1/learning-sessions/{session_id}/events"
    accepted = client.post(url, headers=headers, json={
        "event_type": "explanation_submitted", "expected_revision": state["revision"],
        "payload": {"task_id": "attention-scale-apply-01", "task_variant": "v1-a", "answer": "3"},
    })
    assert accepted.status_code == 202
    wrong = client.post(url, headers=headers, json={
        "event_type": "explanation_submitted", "expected_revision": accepted.json()["current_revision"],
        "payload": {"task_id": "attention-scale-apply-01", "task_variant": "v1-b", "answer": "6"},
    })
    assert wrong.status_code == 202
    narration = client.get(f"/api/v1/learning-sessions/{session_id}").json()["tutor_narration"]
    assert "25" in narration
    assert "16" not in narration


def test_stale_task_is_rejected_without_a_new_attempt(workspace):
    client, headers, factory = workspace
    session_id, state, _ = create_session(client, headers)
    response = client.post(f"/api/v1/learning-sessions/{session_id}/events", headers=headers, json={
        "event_type": "explanation_submitted", "expected_revision": state["revision"],
        "payload": {"task_id": "attention-scale-apply-01", "task_variant": "v1-b", "answer": "3"},
    })
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "TASK_STALE"
    with factory() as db:
        assert db.query(TaskAttempt).filter_by(session_id=session_id).count() == 0


@pytest.mark.parametrize("missing_key", [True, False])
def test_live_failure_never_substitutes_fixture_and_releases_lock(workspace, monkeypatch, missing_key):
    client, headers, factory = workspace
    session_id, state, _ = create_session(client, headers)
    monkeypatch.setattr(settings, "MODEL_MODE", "live")
    monkeypatch.setattr(settings, "META_API_KEY", "" if missing_key else "mock-test-key")
    monkeypatch.setattr(httpx, "Client", lambda **kwargs: UnavailableProvider())
    failed = client.post(f"/api/v1/learning-sessions/{session_id}/events", headers=headers, json={
        "event_type": "message_submitted", "expected_revision": state["revision"],
        "payload": {"message": "Explain the keys"},
    })
    assert failed.status_code == 503
    assert failed.json()["error"]["code"] == "PROVIDER_UNAVAILABLE"
    after = client.get(f"/api/v1/learning-sessions/{session_id}").json()
    assert after["board"] == state["board"]
    assert after["revision"] == state["revision"]
    assert after["tutor_narration"] == state["tutor_narration"]
    assert after["active_job_id"] is None
    with factory() as db:
        assert db.query(Job).filter_by(session_id=session_id, status="failed").count() == 1


def test_run_has_retrievable_job_canonical_parameters_and_retained_evidence(workspace):
    client, headers, _ = workspace
    session_id, state, _ = create_session(client, headers)
    run_response = client.post(f"/api/v1/learning-sessions/{session_id}/runs", headers=headers, json={
        "expected_revision": state["revision"], "recipe_id": "softmax_sensitivity_v1",
        "parameters": {"logits": [0, 1], "multiplier": 2},
    })
    assert run_response.status_code == 202
    run = client.get(f"/api/v1/runs/{run_response.json()['run_id']}").json()
    assert run["status"] == "succeeded"
    assert run["parameters"]["seed"] == 42
    assert run["numpy_version"] == np.__version__
    assert run["assumptions"]
    assert run["checks"]
    job = client.get(f"/api/v1/jobs/{run_response.json()['job_id']}")
    assert job.status_code == 200
    assert job.json()["kind"] == "run_experiment"
    assert job.json()["status"] == "succeeded"
    stale = client.post(f"/api/v1/learning-sessions/{session_id}/runs", headers=headers, json={
        "expected_revision": state["revision"] + 100, "recipe_id": "softmax_sensitivity_v1",
        "parameters": {"logits": [0, 1], "multiplier": 2},
    })
    assert stale.status_code == 409


def test_run_retry_replays_original_but_revised_request_conflicts(workspace):
    client, headers, _ = workspace
    session_id, state, _ = create_session(client, headers)
    headers = {**headers, "Idempotency-Key": str(uuid.uuid4())}
    request = {"expected_revision": state["revision"], "recipe_id": "softmax_sensitivity_v1",
               "parameters": {"logits": [0, 1], "multiplier": 2}}
    url = f"/api/v1/learning-sessions/{session_id}/runs"
    original = client.post(url, headers=headers, json=request)
    assert original.status_code == 202
    replayed = client.post(url, headers=headers, json=request)
    assert replayed.status_code == 202
    assert replayed.json() == original.json()
    request["expected_revision"] += 1
    conflict = client.post(url, headers=headers, json=request)
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "IDEMPOTENCY_CONFLICT"


def test_model_tool_run_is_persisted_and_owner_checked(workspace, monkeypatch):
    client, headers, factory = workspace
    session_id, state, _ = create_session(client, headers)
    monkeypatch.setattr(settings, "MODEL_MODE", "live")
    monkeypatch.setattr(settings, "META_API_KEY", "mock-test-key")
    replies = iter([
        {"choices": [{"message": {"role": "assistant", "tool_calls": [{
            "id": "mock-run-call", "type": "function", "function": {
                "name": "run_experiment", "arguments": json.dumps({
                    "recipe_id": "softmax_sensitivity_v1", "parameters": {"logits": [0, 1], "multiplier": 2},
                }),
            },
        }]}}]},
        {"choices": [{"message": {"role": "assistant", "content": "The retained softmax run is ready."}}]},
    ])

    class ProviderResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return next(replies)

    class MockProvider:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def post(self, *args, **kwargs):
            return ProviderResponse()

    monkeypatch.setattr(httpx, "Client", lambda **kwargs: MockProvider())
    response = client.post(f"/api/v1/learning-sessions/{session_id}/events", headers=headers, json={
        "event_type": "message_submitted", "expected_revision": state["revision"],
        "payload": {"message": "Run a softmax comparison"},
    })
    assert response.status_code == 202
    with factory() as db:
        retained = db.query(ExperimentRun).filter_by(session_id=session_id, recipe_id="softmax_sensitivity_v1").one()
        run_id = retained.id
    run = client.get(f"/api/v1/runs/{run_id}")
    assert run.status_code == 200
    assert run.json()["output"]["base_probabilities"] == pytest.approx([1 / (1 + np.e), np.e / (1 + np.e)])
    stranger = TestClient(app)
    stranger.post("/api/v1/guest-sessions")
    assert stranger.get(f"/api/v1/runs/{run_id}").status_code == 404
    stranger.close()


def test_implicit_and_explicit_numerical_defaults_have_the_same_identity():
    parameters = {"logits": [0, 1], "multiplier": 2}
    implicit = runner.run("softmax_sensitivity_v1", parameters)
    explicit = runner.run("softmax_sensitivity_v1", {**parameters, "seed": 42})
    assert implicit.parameters == explicit.parameters
    assert implicit.parameter_hash == explicit.parameter_hash


def test_invalid_upload_does_not_leave_a_private_orphan_file(workspace, tmp_path):
    client, headers, _ = workspace
    response = client.post("/api/v1/documents", headers=headers,
                           files={"file": ("broken.pdf", b"this is not a PDF", "application/pdf")})
    assert response.status_code == 422
    assert list(tmp_path.rglob("*.pdf")) == []


def test_upload_parsing_does_not_block_health_requests(workspace, monkeypatch):
    client, headers, _ = workspace
    parser_started, release_parser = Event(), Event()
    original_parser = api_module.extract_pdf_content

    def slow_parser(content):
        parser_started.set()
        assert release_parser.wait(5), "test failed to release the PDF parser"
        return original_parser(content)

    monkeypatch.setattr(api_module, "extract_pdf_content", slow_parser)
    content = Path("examples/claimlab_attention_lab.pdf").read_bytes()
    # A persistent client portal shares one ASGI event loop across requests.
    with client, ThreadPoolExecutor(max_workers=2) as pool:
        upload = pool.submit(client.post, "/api/v1/documents", headers=headers,
                             files={"file": ("attention.pdf", content, "application/pdf")})
        try:
            assert parser_started.wait(2)
            health = pool.submit(client.get, "/health/live")
            assert health.result(timeout=2).status_code == 200
        finally:
            release_parser.set()
        assert upload.result(timeout=3).status_code == 202


def test_upload_retry_at_owner_quota_returns_the_original_document(workspace):
    client, headers, _ = workspace
    content = Path("examples/claimlab_attention_lab.pdf").read_bytes()
    keyed_headers = {**headers, "Idempotency-Key": str(uuid.uuid4())}
    first = client.post("/api/v1/documents", headers=keyed_headers,
                        files={"file": ("attention.pdf", content, "application/pdf")})
    assert first.status_code == 202
    for index in range(2):
        assert client.post("/api/v1/documents", headers=headers,
                           files={"file": (f"attention-{index}.pdf", distinct_pdf(index), "application/pdf")}).status_code == 202
    assert client.post("/api/v1/documents", headers=headers,
                       files={"file": ("over.pdf", distinct_pdf(99), "application/pdf")}).status_code == 422
    replayed = client.post("/api/v1/documents", headers=keyed_headers,
                           files={"file": ("attention.pdf", content, "application/pdf")})
    assert replayed.status_code == 202
    assert replayed.json() == first.json()


def test_reuploading_the_same_pdf_returns_one_document_without_using_quota(workspace):
    client, headers, factory = workspace
    content = Path("examples/claimlab_attention_lab.pdf").read_bytes()
    first = client.post("/api/v1/documents", headers=headers,
                        files={"file": ("attention.pdf", content, "application/pdf")})
    assert first.status_code == 202
    for name in ("again.pdf", "claimlab_attention_lab.pdf", "third-try.pdf"):
        repeat = client.post("/api/v1/documents", headers=headers,
                             files={"file": (name, content, "application/pdf")})
        assert repeat.status_code == 202
        assert repeat.json() == first.json()
    with factory() as db:
        assert db.query(models.Document).count() == 1
    for index in range(2):
        assert client.post("/api/v1/documents", headers=headers,
                           files={"file": (f"note-{index}.pdf", distinct_pdf(index), "application/pdf")}).status_code == 202
    assert client.post("/api/v1/documents", headers=headers,
                       files={"file": ("over.pdf", distinct_pdf(99), "application/pdf")}).status_code == 422


def test_unsupported_source_cannot_start_an_unrelated_lesson(workspace):
    client, headers, _ = workspace
    content = Path("examples/unsupported_sample.pdf").read_bytes()
    uploaded = client.post("/api/v1/documents", headers=headers,
                           files={"file": ("botany.pdf", content, "application/pdf")})
    document_id = uploaded.json()["document_id"]
    selected = client.post(f"/api/v1/documents/{document_id}/selections", headers=headers,
                           json={"page_start": 1, "page_end": 1, "question": "What is chlorophyll?"})
    assert selected.json()["topic_assessment"] == "unsupported"
    created = client.post("/api/v1/learning-sessions", headers=headers,
                          json={"selection_id": selected.json()["selection_id"]})
    assert created.status_code == 422
    assert created.json()["error"]["code"] == "UNSUPPORTED_DOCUMENT"
    assert client.get("/api/v1/learning-sessions/active").json()["active_session_id"] is None


def use_mock_live_tutor(monkeypatch):
    """Exercise live pre-assessment and checkpoints without contacting a provider."""
    monkeypatch.setattr(settings, "MODEL_MODE", "live")
    monkeypatch.setattr(settings, "META_API_KEY", "mock-test-key")

    class ProviderResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {"choices": [{"message": {"role": "assistant", "content": "Inspect the current quantities one step at a time."}}]}

    class MockProvider:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def post(self, *args, **kwargs):
            return ProviderResponse()

    monkeypatch.setattr(httpx, "Client", lambda **kwargs: MockProvider())


def submit_task_answer(client, headers, session_id, state, variant, answer):
    accepted = client.post(f"/api/v1/learning-sessions/{session_id}/events", headers=headers, json={
        "event_type": "explanation_submitted", "expected_revision": state["revision"],
        "payload": {"task_id": "attention-scale-apply-01", "task_variant": variant,
                    "answer": answer, "hints_used": 0},
    })
    assert accepted.status_code == 202
    return client.get(f"/api/v1/learning-sessions/{session_id}").json()


@pytest.mark.parametrize("mode", ["fixture", "mock_live"])
@pytest.mark.parametrize("help_type", ["hint_requested", "message_submitted", "object_question_submitted"])
def test_recorded_help_cannot_be_erased_or_counted_as_independent(workspace, monkeypatch, mode, help_type):
    client, headers, factory = workspace
    session_id, state, _ = create_session(client, headers)
    if mode == "mock_live":
        use_mock_live_tutor(monkeypatch)
    help_payload = {
        "task_id": "attention-scale-apply-01", "task_variant": "v1-a",
        "message": "Help me understand this calculation",
        "assistance_task": {"task_id": "other-task", "task_variant": "v1-b"},
    }
    helped = client.post(f"/api/v1/learning-sessions/{session_id}/events", headers=headers, json={
        "event_type": help_type, "expected_revision": state["revision"], "payload": help_payload,
    })
    assert helped.status_code == 202
    after_help = client.get(f"/api/v1/learning-sessions/{session_id}").json()
    assert after_help["active_task"] == state["active_task"]
    assert after_help["evidence_summary"] == state["evidence_summary"]
    if mode == "fixture" and help_type == "hint_requested":
        assert "sqrt(16) = 4" in after_help["tutor_narration"]
        assert "12 divided by 4" in after_help["tutor_narration"]
    after_a = submit_task_answer(client, headers, session_id, after_help, "v1-a", "3")
    assert after_a["evidence_summary"]["attention_scaling"] == "supported_with_help"
    after_b = submit_task_answer(client, headers, session_id, after_a, "v1-b", "3")
    assert after_b["evidence_summary"]["attention_scaling"] == "supported_with_help"
    with factory() as db:
        attempts = db.query(TaskAttempt).filter_by(session_id=session_id).order_by(TaskAttempt.created_at).all()
        assert [(attempt.task_variant, attempt.hint_count) for attempt in attempts] == [("v1-a", 1), ("v1-b", 0)]
        recorded_help = db.query(LearnerEvent).filter_by(session_id=session_id, event_type=help_type).one()
        assert json.loads(recorded_help.payload_json)["assistance_task"] == {
            "task_id": "attention-scale-apply-01", "task_variant": "v1-a", "concept_id": "attention_scaling",
        }


@pytest.mark.parametrize("mode", ["fixture", "mock_live"])
def test_wrong_answer_feedback_prevents_later_retry_being_independent(workspace, monkeypatch, mode):
    client, headers, factory = workspace
    session_id, state, _ = create_session(client, headers)
    if mode == "mock_live":
        use_mock_live_tutor(monkeypatch)
    wrong = submit_task_answer(client, headers, session_id, state, "v1-a", "100")
    corrected = submit_task_answer(client, headers, session_id, wrong, "v1-a", "3")
    final = submit_task_answer(client, headers, session_id, corrected, "v1-b", "3")
    assert final["evidence_summary"]["attention_scaling"] == "supported_with_help"
    with factory() as db:
        attempts = db.query(TaskAttempt).filter_by(session_id=session_id).order_by(TaskAttempt.created_at).all()
        assert [(attempt.is_correct, attempt.hint_count) for attempt in attempts] == [(False, 0), (True, 1), (True, 0)]


@pytest.mark.parametrize("mode", ["fixture", "mock_live"])
def test_two_fresh_answers_still_provide_independent_evidence(workspace, monkeypatch, mode):
    client, headers, factory = workspace
    session_id, state, _ = create_session(client, headers)
    if mode == "mock_live":
        use_mock_live_tutor(monkeypatch)
    first = submit_task_answer(client, headers, session_id, state, "v1-a", "3")
    final = submit_task_answer(client, headers, session_id, first, "v1-b", "3")
    assert final["evidence_summary"]["attention_scaling"] == "supported_independently"
    with factory() as db:
        assert {attempt.hint_count for attempt in db.query(TaskAttempt).filter_by(session_id=session_id)} == {0}


def test_stale_hint_request_does_not_change_task_or_record_help(workspace):
    client, headers, factory = workspace
    session_id, state, _ = create_session(client, headers)
    rejected = client.post(f"/api/v1/learning-sessions/{session_id}/events", headers=headers, json={
        "event_type": "hint_requested", "expected_revision": state["revision"],
        "payload": {"task_id": "attention-scale-apply-01", "task_variant": "v1-b"},
    })
    assert rejected.status_code == 422
    assert rejected.json()["error"]["code"] == "TASK_STALE"
    assert client.get(f"/api/v1/learning-sessions/{session_id}").json()["active_task"] == state["active_task"]
    with factory() as db:
        assert db.query(LearnerEvent).filter_by(session_id=session_id).count() == 0


def test_unavailable_help_is_not_recorded_as_delivered(workspace, monkeypatch):
    client, headers, factory = workspace
    session_id, state, _ = create_session(client, headers)
    monkeypatch.setattr(settings, "MODEL_MODE", "live")
    monkeypatch.setattr(settings, "META_API_KEY", "")
    rejected = client.post(f"/api/v1/learning-sessions/{session_id}/events", headers=headers, json={
        "event_type": "hint_requested", "expected_revision": state["revision"],
        "payload": {"task_id": "attention-scale-apply-01", "task_variant": "v1-a", "assistance_delivered": True},
    })
    assert rejected.status_code == 503
    with factory() as db:
        requested = db.query(LearnerEvent).filter_by(session_id=session_id, event_type="hint_requested").one()
        assert json.loads(requested.payload_json)["assistance_delivered"] is False
    monkeypatch.setattr(settings, "MODEL_MODE", "fixture")
    first = submit_task_answer(client, headers, session_id, state, "v1-a", "3")
    final = submit_task_answer(client, headers, session_id, first, "v1-b", "3")
    assert final["evidence_summary"]["attention_scaling"] == "supported_independently"


def _seed_private_deletion_records(factory, owner_id, session_id):
    with factory() as db:
        job = db.query(Job).filter_by(session_id=session_id).first()
        db.add(models.ToolInvocation(
            job_id=job.id, provider_call_id="deletion-test-call",
            tool_name="present_teaching_step", argument_hash="f" * 64,
            result_reference="private teaching context",
        ))
        db.add(models.BudgetReservation(
            owner_id=owner_id, request_id=str(uuid.uuid4()),
            model_name="fixture", reserved_amount_usd=0,
        ))
        db.add(models.IdempotencyRecord(
            owner_id=owner_id, route_scope="private-fixture",
            idempotency_key=str(uuid.uuid4()), request_fingerprint="e" * 64,
            status_code=200, response_json='{"private":"retained source context"}',
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        ))
        db.commit()


def _content_ids(factory):
    with factory() as db:
        return {
            table.name: {row["id"] for row in db.execute(table.select()).mappings()}
            for table in Base.metadata.sorted_tables
            if table.name not in ("guest_owners", "idempotency_records")
        }


def test_delete_erases_all_owner_content_and_preserves_another_owner(workspace):
    client, headers, factory = workspace
    with factory() as db:
        db.execute(text("PRAGMA foreign_keys=ON"))
        db.commit()

    owner_id = client.get("/api/v1/me").json()["guest_id"]
    session_id, state, source = create_session(client, headers)
    answered = client.post(
        f"/api/v1/learning-sessions/{session_id}/events", headers=headers,
        json={"event_id": str(uuid.uuid4()), "event_type": "explanation_submitted",
              "expected_revision": state["revision"],
              "payload": {"task_id": state["active_task"]["task_id"],
                          "task_variant": state["active_task"]["task_variant"], "answer": "999"}},
    )
    assert answered.status_code == 202
    _seed_private_deletion_records(factory, owner_id, session_id)
    with factory() as db:
        own_pdf = Path(db.get(models.Document, source["document_id"]).storage_key)
        queued = Job(owner_id=owner_id, session_id=session_id, kind="tutor_turn", status="queued")
        db.add(queued)
        db.flush()
        db.add(models.JobEvent(job_id=queued.id, sequence=1, event_type="queued",
                               payload_json='{"private":"queued student context"}'))
        db.commit()
        assert db.query(models.TaskAttempt).count() > 0
        assert db.query(models.TeachingDecision).count() > 0
        own_jobs = [row.id for row in db.query(Job).filter_by(owner_id=owner_id)]
    own_ids = _content_ids(factory)

    other = TestClient(app)
    try:
        other_guest = other.post("/api/v1/guest-sessions").json()
        other_headers = {"X-CSRF-Token": other_guest["csrf_token"]}
        other_owner = other.get("/api/v1/me").json()["guest_id"]
        other_session, _, other_source = create_session(other, other_headers)
        _seed_private_deletion_records(factory, other_owner, other_session)
        with factory() as db:
            other_pdf = Path(db.get(models.Document, other_source["document_id"]).storage_key)
            other_budget_ids = {row.id for row in db.query(models.BudgetReservation).filter_by(owner_id=other_owner)}
            other_idempotency_ids = {row.id for row in db.query(models.IdempotencyRecord).filter_by(owner_id=other_owner)}
        all_ids = _content_ids(factory)
        assert own_pdf.exists() and other_pdf.exists()

        deleted = client.delete("/api/v1/me/data", headers={
            **headers, "Idempotency-Key": str(uuid.uuid4()),
        })
        assert deleted.status_code == 202
        assert deleted.json()["status"] == "deleted"
        assert not own_pdf.exists()
        assert other_pdf.exists()
        assert _content_ids(factory) == {
            table_name: ids - own_ids[table_name] for table_name, ids in all_ids.items()
        }
        with factory() as db:
            assert db.get(models.GuestOwner, owner_id).deleted_at is not None
            assert db.query(models.BudgetReservation).filter_by(owner_id=owner_id).count() == 0
            receipts = db.query(models.IdempotencyRecord).filter_by(owner_id=owner_id).all()
            assert len(receipts) == 1 and receipts[0].route_scope == "delete_data"
            assert set(json.loads(receipts[0].response_json)) == {"deletion_id", "status"}
            assert {row.id for row in db.query(models.BudgetReservation).filter_by(owner_id=other_owner)} == other_budget_ids
            assert {row.id for row in db.query(models.IdempotencyRecord).filter_by(owner_id=other_owner)} == other_idempotency_ids

        assert client.get("/api/v1/me").status_code == 401
        assert client.delete("/api/v1/me/data", headers=headers).status_code == 401
        replacement = client.post("/api/v1/guest-sessions")
        assert replacement.status_code == 201
        assert client.get("/api/v1/me").json()["guest_id"] != owner_id
        for url in (f"/api/v1/documents/{source['document_id']}",
                    f"/api/v1/learning-sessions/{session_id}",
                    f"/api/v1/runs/{state['latest_run_id']}",
                    *(f"/api/v1/jobs/{job_id}" for job_id in own_jobs)):
            assert client.get(url).status_code == 404
        assert other.get(f"/api/v1/learning-sessions/{other_session}").status_code == 200
        assert other.get(f"/api/v1/documents/{other_source['document_id']}/file").status_code == 200
    finally:
        other.close()


def test_delete_file_failure_is_truthful_and_retryable(workspace, monkeypatch):
    client, headers, factory = workspace
    owner_id = client.get("/api/v1/me").json()["guest_id"]
    session_id, _, source = create_session(client, headers)
    with factory() as db:
        stored_path = Path(db.get(models.Document, source["document_id"]).storage_key).resolve()
    original_unlink = Path.unlink

    def locked_file(path, *args, **kwargs):
        if path.resolve() == stored_path:
            raise PermissionError("private path must not appear in the API error")
        return original_unlink(path, *args, **kwargs)

    with monkeypatch.context() as patcher:
        patcher.setattr(Path, "unlink", locked_file)
        failed = client.delete("/api/v1/me/data", headers=headers)
        assert failed.status_code == 503
        assert failed.json()["error"]["code"] == "SERVICE_NOT_READY"
        assert "private path" not in failed.text and str(stored_path) not in failed.text
        assert client.get("/api/v1/me").status_code == 200
        assert client.get(f"/api/v1/learning-sessions/{session_id}").status_code == 200
        with factory() as db:
            assert db.get(models.GuestOwner, owner_id).deleted_at is None
            assert db.get(models.Document, source["document_id"]) is not None
        assert stored_path.exists()
    assert client.delete("/api/v1/me/data", headers=headers).status_code == 202
    assert not stored_path.exists()


def test_delete_never_removes_files_outside_private_documents(workspace, tmp_path):
    client, headers, factory = workspace
    _, _, source = create_session(client, headers)
    unrelated = tmp_path / "unrelated.pdf"
    unrelated.write_bytes(b"unrelated data must remain")
    upload = tmp_path / "documents" / f"{source['document_id']}.pdf"
    assert upload.exists()
    with factory() as db:
        db.get(models.Document, source["document_id"]).storage_key = str(unrelated)
        db.commit()
    response = client.delete("/api/v1/me/data", headers=headers)
    assert response.status_code == 202
    assert unrelated.read_bytes() == b"unrelated data must remain"
    assert not upload.exists()
    assert client.get("/api/v1/me").status_code == 401


def test_delete_removes_an_upload_stored_under_an_earlier_data_dir(workspace, tmp_path):
    client, headers, factory = workspace
    _, _, source = create_session(client, headers)
    with factory() as db:
        doc = db.get(models.Document, source["document_id"])
        earlier = tmp_path / "earlier-volume" / Path(doc.storage_key).name
        earlier.parent.mkdir()
        Path(doc.storage_key).replace(earlier)
        doc.storage_key = str(earlier)
        db.commit()
    assert client.delete("/api/v1/me/data", headers=headers).status_code == 202
    assert not earlier.exists()


@pytest.mark.parametrize("missing_key", [True, False])
def test_failed_first_turn_leaves_no_lesson_or_quota_behind(workspace, monkeypatch, missing_key):
    client, headers, factory = workspace
    source = create_source(client, headers)
    monkeypatch.setattr(settings, "MODEL_MODE", "live")
    monkeypatch.setattr(settings, "META_API_KEY", "" if missing_key else "mock-test-key")
    monkeypatch.setattr(httpx, "Client", lambda **kwargs: UnavailableProvider())
    for _ in range(6):
        failed = client.post("/api/v1/learning-sessions", headers=headers,
                             json={"selection_id": source["selection_id"]})
        assert failed.status_code == 503
    assert client.get("/api/v1/learning-sessions/active").json()["active_session_id"] is None
    with factory() as db:
        assert db.query(models.LearningSession).count() == 0
        assert db.query(Job).filter_by(kind="tutor_turn", status="failed").count() == 6
    monkeypatch.setattr(settings, "MODEL_MODE", "fixture")
    created = client.post("/api/v1/learning-sessions", headers=headers,
                          json={"selection_id": source["selection_id"]})
    assert created.status_code == 202
    assert client.get("/api/v1/learning-sessions/active").json()["active_session_id"] == created.json()["session_id"]


def test_live_answer_is_graded_once_when_the_provider_fails_first(workspace, monkeypatch):
    client, headers, factory = workspace
    session_id, state, _ = create_session(client, headers)
    monkeypatch.setattr(settings, "MODEL_MODE", "live")
    monkeypatch.setattr(settings, "META_API_KEY", "mock-test-key")
    monkeypatch.setattr(httpx, "Client", lambda **kwargs: UnavailableProvider())
    failed = client.post(f"/api/v1/learning-sessions/{session_id}/events", headers=headers, json={
        "event_type": "explanation_submitted", "expected_revision": state["revision"],
        "payload": {"task_id": "attention-scale-apply-01", "task_variant": "v1-a", "answer": "100"},
    })
    assert failed.status_code == 503
    with factory() as db:
        assert db.query(TaskAttempt).filter_by(session_id=session_id).count() == 0
        failed_job = db.query(Job).filter_by(session_id=session_id, status="failed").one()
        assert db.query(models.BudgetReservation).filter_by(request_id=failed_job.id).one().status == "released"
    after_failure = client.get(f"/api/v1/learning-sessions/{session_id}").json()
    assert after_failure["active_task"] == state["active_task"]
    use_mock_live_tutor(monkeypatch)
    first = submit_task_answer(client, headers, session_id, after_failure, "v1-a", "3")
    final = submit_task_answer(client, headers, session_id, first, "v1-b", "3")
    assert final["evidence_summary"]["attention_scaling"] == "supported_independently"
    with factory() as db:
        attempts = db.query(TaskAttempt).filter_by(session_id=session_id).order_by(TaskAttempt.created_at).all()
        assert [(attempt.task_variant, attempt.hint_count) for attempt in attempts] == [("v1-a", 0), ("v1-b", 0)]


def test_live_question_keeps_the_current_task_variant(workspace, monkeypatch):
    client, headers, _ = workspace
    session_id, state, _ = create_session(client, headers)
    on_second = submit_task_answer(client, headers, session_id, state, "v1-a", "3")
    assert on_second["active_task"]["task_variant"] == "v1-b"
    use_mock_live_tutor(monkeypatch)
    asked = client.post(f"/api/v1/learning-sessions/{session_id}/events", headers=headers, json={
        "event_type": "message_submitted", "expected_revision": on_second["revision"],
        "payload": {"message": "Why does the square root appear?"},
    })
    assert asked.status_code == 202
    assert client.get(f"/api/v1/learning-sessions/{session_id}").json()["active_task"] == on_second["active_task"]


def test_live_seed_run_is_traceable_to_its_job(workspace, monkeypatch):
    client, headers, factory = workspace
    use_mock_live_tutor(monkeypatch)
    source = create_source(client, headers)
    created = client.post("/api/v1/learning-sessions", headers=headers, json={"selection_id": source["selection_id"]})
    assert created.status_code == 202
    state = client.get(f"/api/v1/learning-sessions/{created.json()['session_id']}").json()
    with factory() as db:
        seed_run = db.get(ExperimentRun, state["latest_run_id"])
        assert seed_run.parent_job_id == created.json()["initial_job_id"]
        assert seed_run.completed_at is not None
    run = client.get(f"/api/v1/runs/{state['latest_run_id']}").json()
    assert run["parameters"] == runner.run("attention_scaling_v1", run["parameters"]).parameters
    assert run["numpy_version"] == np.__version__


def test_live_model_notes_aliases_and_narration_reach_the_lesson(workspace, monkeypatch):
    """Mirrors observed muse-spark-1.3 output: action/label/text notes, aliased recipe inputs, empty final reply."""
    client, headers, _ = workspace
    monkeypatch.setattr(settings, "MODEL_MODE", "live")
    monkeypatch.setattr(settings, "META_API_KEY", "mock-test-key")

    def call(name, arguments):
        return {"choices": [{"finish_reason": "tool_calls", "message": {"role": "assistant", "content": "", "tool_calls": [{
            "id": f"call-{name}", "type": "function", "function": {"name": name, "arguments": json.dumps(arguments)},
        }]}}]}

    replies = iter([
        call("present_teaching_step", {"narration": "Source statement: scores are divided by sqrt(d_k).", "board_commands": [
            {"action": "write", "label": "Source", "text": "Scaled dot-product attention divides scores by sqrt(d_k)"},
            {"action": "write", "label": "Formula", "text": "Attention = softmax(Q K^T / sqrt(d_k)) V"},
            {"action": "draw_unicorn"},
        ]}),
        call("run_experiment", {"recipe_id": "softmax_sensitivity_v1", "parameters": {"scores": [0, 1], "temperature": 2}}),
        {"choices": [{"finish_reason": "stop", "message": {"role": "assistant", "content": None}}]},
    ])

    class ProviderResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return next(replies)

    class MockProvider:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def post(self, *args, **kwargs):
            return ProviderResponse()

    monkeypatch.setattr(httpx, "Client", lambda **kwargs: MockProvider())
    source = create_source(client, headers)
    created = client.post("/api/v1/learning-sessions", headers=headers, json={"selection_id": source["selection_id"]})
    assert created.status_code == 202
    state = client.get(f"/api/v1/learning-sessions/{created.json()['session_id']}").json()
    assert state["tutor_narration"] == "Source statement: scores are divided by sqrt(d_k)."
    objects = state["board"]["objects"]
    notes = [o for o in objects if o["type"] == "text"]
    assert [(n["label"], n["payload"]["text"]) for n in notes] == [
        ("Source", "Scaled dot-product attention divides scores by sqrt(d_k)"),
        ("Formula", "Attention = softmax(Q K^T / sqrt(d_k)) V"),
    ]
    assert {o["id"] for o in objects} >= {"node-q", "node-k", "node-scores", "eq-scaling", "plot-scaling-var"}
    plot = next(o for o in objects if o["id"] == "plot-scaling-var")
    assert client.get(f"/api/v1/runs/{plot['payload']['run_id']}").json()["recipe_id"] == "attention_scaling_v1"
    assert state["latest_run_id"] == plot["payload"]["run_id"]
    with workspace[2]() as db:
        softmax = db.query(ExperimentRun).filter_by(recipe_id="softmax_sensitivity_v1").one()
        assert json.loads(softmax.parameters_json)["logits"] == [0, 1]
        assert json.loads(softmax.parameters_json)["multiplier"] == pytest.approx(0.5)


def test_recipe_aliases_are_mapped_without_leftover_fields():
    from claimlab.services.agent_orchestrator import normalize_recipe_parameters
    scaling = normalize_recipe_parameters("attention_scaling_v1", {"d_k": 32, "keys": 6, "samples": 5000})
    assert scaling == {"dimensions": [32], "n_keys": 6, "trials": 200}
    assert runner.run("attention_scaling_v1", scaling).status == "succeeded"
    softmax = normalize_recipe_parameters("softmax_sensitivity_v1", {"logits": [1, 2], "scores": [9, 9], "scale": 3})
    assert softmax == {"logits": [1, 2], "multiplier": 3}
    assert runner.run("softmax_sensitivity_v1", softmax).status == "succeeded"


def test_orphaned_turn_stops_blocking_the_lesson_after_its_lease(workspace):
    client, headers, factory = workspace
    owner_id = client.get("/api/v1/me").json()["guest_id"]
    session_id, state, _ = create_session(client, headers)
    with factory() as db:
        orphan = Job(owner_id=owner_id, session_id=session_id, kind="tutor_turn", status="running",
                     lease_expires_at=datetime.now(timezone.utc) + timedelta(minutes=1))
        db.add(orphan)
        db.flush()
        orphan_id = orphan.id
        db.get(models.LearningSession, session_id).active_job_id = orphan_id
        db.commit()
    run_request = {"expected_revision": state["revision"], "recipe_id": "softmax_sensitivity_v1",
                   "parameters": {"logits": [0, 1], "multiplier": 2}}
    question = {"event_type": "message_submitted", "expected_revision": state["revision"],
                "payload": {"message": "Explain the keys"}}
    busy_run = client.post(f"/api/v1/learning-sessions/{session_id}/runs", headers=headers, json=run_request)
    assert busy_run.status_code == 409 and busy_run.json()["error"]["code"] == "SESSION_BUSY"
    busy_event = client.post(f"/api/v1/learning-sessions/{session_id}/events", headers=headers, json=question)
    assert busy_event.status_code == 409 and busy_event.json()["error"]["code"] == "SESSION_BUSY"
    with factory() as db:
        db.get(Job, orphan_id).lease_expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        db.commit()
    assert client.post(f"/api/v1/learning-sessions/{session_id}/runs", headers=headers, json=run_request).status_code == 202
    assert client.post(f"/api/v1/learning-sessions/{session_id}/events", headers=headers, json=question).status_code == 202
    with factory() as db:
        expired = db.get(Job, orphan_id)
        assert (expired.status, expired.error_code) == ("failed", "WORKER_LOST")


def test_delete_empty_guest_does_not_erase_other_guests(workspace):
    client, headers, factory = workspace
    other = TestClient(app)
    try:
        other_headers = {"X-CSRF-Token": other.post("/api/v1/guest-sessions").json()["csrf_token"]}
        other_session, _, _ = create_session(other, other_headers)
        before = _content_ids(factory)
        assert client.delete("/api/v1/me/data", headers=headers).status_code == 202
        assert _content_ids(factory) == before
        assert other.get(f"/api/v1/learning-sessions/{other_session}").status_code == 200
    finally:
        other.close()
