"""Comprehensive acceptance test suite covering all ClaimLab test strategy specifications."""
import pytest
from fastapi.testclient import TestClient

from claimlab.api import app
from claimlab.database import Base, engine
from claimlab.contracts.whiteboard import (
    BoardObject,
    ObjectType,
    Position,
    Dimensions,
    BoardPatch,
    AddObjectCommand,
    AddConnectorCommand,
    RemoveObjectCommand,
    SceneGraph,
)
from claimlab.whiteboard.engine import apply_atomic_patch, WhiteboardValidationError


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield


def test_t_auth_01_guest_creation_and_cookie():
    client = TestClient(app)
    res = client.post("/api/v1/guest-sessions")
    assert res.status_code == 201
    assert "claimlab_guest" in res.cookies
    data = res.json()
    assert "csrf_token" in data
    assert "expires_at" in data

    # Verify /me
    res_me = client.get("/api/v1/me")
    assert res_me.status_code == 200
    assert res_me.json()["limits"]["max_documents"] == 3


def test_t_board_01_atomic_patch_engine():
    scene = SceneGraph(schema_version=1, board_revision=0, objects=[])

    obj1 = BoardObject(
        id="n1",
        type=ObjectType.CONCEPT_NODE,
        position=Position(x=10, y=10),
        dimensions=Dimensions(width=100, height=50),
        label="Node 1",
    )
    obj2 = BoardObject(
        id="n2",
        type=ObjectType.CONCEPT_NODE,
        position=Position(x=150, y=10),
        dimensions=Dimensions(width=100, height=50),
        label="Node 2",
    )

    # 1. Successful patch: add 2 objects and 1 connector
    patch1 = BoardPatch(
        schema_version=1,
        base_board_revision=0,
        commands=[
            AddObjectCommand(object=obj1),
            AddObjectCommand(object=obj2),
            AddConnectorCommand(
                connector_id="c1",
                from_object_id="n1",
                to_object_id="n2",
                relationship="connects_to",
            ),
        ],
    )
    new_scene = apply_atomic_patch(scene, patch1)
    assert new_scene.board_revision == 1
    assert len(new_scene.objects) == 3

    # 2. Duplicate object ID rejected atomically
    dup_patch = BoardPatch(
        schema_version=1,
        base_board_revision=1,
        commands=[AddObjectCommand(object=obj1)],
    )
    with pytest.raises(WhiteboardValidationError, match="Duplicate object ID"):
        apply_atomic_patch(new_scene, dup_patch)

    # 3. Connector with non-existent endpoint rejected
    dangling_patch = BoardPatch(
        schema_version=1,
        base_board_revision=1,
        commands=[
            AddConnectorCommand(
                connector_id="c2",
                from_object_id="n1",
                to_object_id="missing_node",
                relationship="invalid",
            )
        ],
    )
    with pytest.raises(WhiteboardValidationError, match="Connector endpoint"):
        apply_atomic_patch(new_scene, dangling_patch)

    # 4. Unsafe LaTeX rejected
    unsafe_eq = BoardObject(
        id="eq_bad",
        type=ObjectType.EQUATION,
        position=Position(x=0, y=0),
        dimensions=Dimensions(width=100, height=50),
        label="Malicious Eq",
        payload={"latex": r"\write18{rm -rf /}"},
    )
    unsafe_patch = BoardPatch(
        schema_version=1,
        base_board_revision=1,
        commands=[AddObjectCommand(object=unsafe_eq)],
    )
    with pytest.raises(WhiteboardValidationError, match="Forbidden LaTeX"):
        apply_atomic_patch(new_scene, unsafe_patch)

    # 5. Cascading connector removal on object removal
    remove_patch = BoardPatch(
        schema_version=1,
        base_board_revision=1,
        commands=[RemoveObjectCommand(object_id="n1")],
    )
    after_remove = apply_atomic_patch(new_scene, remove_patch)
    assert after_remove.board_revision == 2
    # n1 and c1 (which connected n1 to n2) are both gone, leaving only n2
    assert len(after_remove.objects) == 1
    assert after_remove.objects[0].id == "n2"


def test_t_tutor_01_unsupported_topic_boundary():
    client = TestClient(app)
    res_guest = client.post("/api/v1/guest-sessions")
    csrf = res_guest.json()["csrf_token"]

    # Upload unsupported sample (Photosynthesis botany paper)
    with open("examples/unsupported_sample.pdf", "rb") as f:
        res_up = client.post(
            "/api/v1/documents",
            headers={"X-CSRF-Token": csrf},
            files={"file": ("unsupported_sample.pdf", f, "application/pdf")},
        )
    assert res_up.status_code == 202
    doc_id = res_up.json()["document_id"]

    # Create selection on unsupported botany paper
    res_sel = client.post(
        f"/api/v1/documents/{doc_id}/selections",
        headers={"X-CSRF-Token": csrf},
        json={"page_start": 1, "page_end": 1, "question": "What is the Calvin cycle?"},
    )
    assert res_sel.status_code == 201
    # Boundary verified: marked unsupported!
    assert res_sel.json()["topic_assessment"] == "unsupported"


def test_t_learn_two_variant_progression():
    client = TestClient(app)
    res_guest = client.post("/api/v1/guest-sessions")
    csrf = res_guest.json()["csrf_token"]

    # Upload Attention Lab PDF
    with open("examples/claimlab_attention_lab.pdf", "rb") as f:
        res_up = client.post(
            "/api/v1/documents",
            headers={"X-CSRF-Token": csrf},
            files={"file": ("claimlab_attention_lab.pdf", f, "application/pdf")},
        )
    doc_id = res_up.json()["document_id"]

    # Selection & Session
    res_sel = client.post(
        f"/api/v1/documents/{doc_id}/selections",
        headers={"X-CSRF-Token": csrf},
        json={"page_start": 2, "page_end": 2, "question": "Attention Scaling"},
    )
    sel_id = res_sel.json()["selection_id"]

    res_sess = client.post(
        "/api/v1/learning-sessions",
        headers={"X-CSRF-Token": csrf},
        json={"selection_id": sel_id, "goal": "Scaling"},
    )
    sess_id = res_sess.json()["session_id"]
    rev = res_sess.json()["revision"]

    # 1. First attempt: Wrong answer
    res_wrong = client.post(
        f"/api/v1/learning-sessions/{sess_id}/events",
        headers={"X-CSRF-Token": csrf},
        json={
            "schema_version": 1,
            "event_type": "explanation_submitted",
            "expected_revision": rev,
            "payload": {
                "task_id": "attention-scale-apply-01",
                "task_variant": "v1-a",
                "answer": "100",
            },
        },
    )
    assert res_wrong.status_code == 202
    rev = res_wrong.json()["current_revision"]

    state_after_wrong = client.get(f"/api/v1/learning-sessions/{sess_id}").json()
    assert state_after_wrong["evidence_summary"]["attention_scaling"] == "needs_check"

    # 2. Second attempt: First correct independent answer (variant v1-a)
    res_correct_1 = client.post(
        f"/api/v1/learning-sessions/{sess_id}/events",
        headers={"X-CSRF-Token": csrf},
        json={
            "schema_version": 1,
            "event_type": "explanation_submitted",
            "expected_revision": rev,
            "payload": {
                "task_id": "attention-scale-apply-01",
                "task_variant": "v1-a",
                "answer": "3",
            },
        },
    )
    assert res_correct_1.status_code == 202
    rev = res_correct_1.json()["current_revision"]

    state_after_c1 = client.get(f"/api/v1/learning-sessions/{sess_id}").json()
    # One variant passed independently: advances to variant v1-b, marked supported_with_help/provisional
    assert state_after_c1["active_task"]["task_variant"] == "v1-b"

    # 3. Third attempt: Second correct independent answer (variant v1-b: score 15, dim 25 -> 3)
    res_correct_2 = client.post(
        f"/api/v1/learning-sessions/{sess_id}/events",
        headers={"X-CSRF-Token": csrf},
        json={
            "schema_version": 1,
            "event_type": "explanation_submitted",
            "expected_revision": rev,
            "payload": {
                "task_id": "attention-scale-apply-01",
                "task_variant": "v1-b",
                "answer": "3",
            },
        },
    )
    assert res_correct_2.status_code == 202

    # Two distinct variants independently confirmed: marks supported_independently!
    state_after_c2 = client.get(f"/api/v1/learning-sessions/{sess_id}").json()
    assert state_after_c2["evidence_summary"]["attention_scaling"] == "supported_independently"


def test_t_idem_01_idempotency_enforcement():
    client = TestClient(app)
    res_guest = client.post("/api/v1/guest-sessions")
    csrf = res_guest.json()["csrf_token"]

    idempotency_key = "test-key-12345"
    with open("examples/claimlab_attention_lab.pdf", "rb") as f:
        content = f.read()

    # First request
    res1 = client.post(
        "/api/v1/documents",
        headers={"X-CSRF-Token": csrf, "Idempotency-Key": idempotency_key},
        files={"file": ("claimlab_attention_lab.pdf", content, "application/pdf")},
    )
    assert res1.status_code == 202
    doc_id = res1.json()["document_id"]

    # Duplicate request with same idempotency key and same file: returns cached response
    res2 = client.post(
        "/api/v1/documents",
        headers={"X-CSRF-Token": csrf, "Idempotency-Key": idempotency_key},
        files={"file": ("claimlab_attention_lab.pdf", content, "application/pdf")},
    )
    assert res2.status_code == 202
    assert res2.json()["document_id"] == doc_id

    # Reused key with different payload: 409 IDEMPOTENCY_CONFLICT
    with open("examples/unsupported_sample.pdf", "rb") as f2:
        diff_content = f2.read()

    res3 = client.post(
        "/api/v1/documents",
        headers={"X-CSRF-Token": csrf, "Idempotency-Key": idempotency_key},
        files={"file": ("unsupported_sample.pdf", diff_content, "application/pdf")},
    )
    assert res3.status_code == 409
    assert res3.json()["error"]["code"] == "IDEMPOTENCY_CONFLICT"


def test_t_job_cancel_endpoint():
    client = TestClient(app)
    res_guest = client.post("/api/v1/guest-sessions")
    csrf = res_guest.json()["csrf_token"]

    # Upload document to create job
    with open("examples/claimlab_attention_lab.pdf", "rb") as f:
        res_up = client.post(
            "/api/v1/documents",
            headers={"X-CSRF-Token": csrf},
            files={"file": ("claimlab_attention_lab.pdf", f, "application/pdf")},
        )
    job_id = res_up.json()["job_id"]

    # Cancel job
    res_cancel = client.post(
        f"/api/v1/jobs/{job_id}/cancel",
        headers={"X-CSRF-Token": csrf},
    )
    assert res_cancel.status_code == 202
    assert res_cancel.json()["status"] in ["cancelled", "succeeded"]


def test_t_data_01_full_deletion_lifecycle():
    client = TestClient(app)
    res_guest = client.post("/api/v1/guest-sessions")
    csrf = res_guest.json()["csrf_token"]

    with open("examples/claimlab_attention_lab.pdf", "rb") as f:
        res_up = client.post(
            "/api/v1/documents",
            headers={"X-CSRF-Token": csrf},
            files={"file": ("claimlab_attention_lab.pdf", f, "application/pdf")},
        )
    doc_id = res_up.json()["document_id"]

    # Document file exists
    assert client.get(f"/api/v1/documents/{doc_id}").status_code == 200

    # Delete my data
    res_del = client.delete("/api/v1/me/data", headers={"X-CSRF-Token": csrf})
    assert res_del.status_code == 202
    assert res_del.json()["status"] == "deleted"

    # Guest is immediately rejected
    assert client.get("/api/v1/me").status_code == 401
