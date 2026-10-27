"""Integration tests for ClaimLab API and end-to-end learning loop."""
import os
import pytest
from fastapi.testclient import TestClient

from claimlab.api import app
from claimlab.database import Base, engine


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield


def test_health_endpoints():
    client = TestClient(app)
    res = client.get("/health/live")
    assert res.status_code == 200
    assert res.json() == {"status": "alive"}

    res_ready = client.get("/health/ready")
    assert res_ready.status_code == 200
    data = res_ready.json()
    assert data["status"] == "ready"
    assert data["database"] == "ok"
    assert "attention_scaling_v1" in data["recipes"]


def test_guest_lifecycle_and_ownership():
    client = TestClient(app)

    # 1. Anonymous access to /api/v1/me fails with 401
    res = client.get("/api/v1/me")
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "GUEST_REQUIRED"

    # 2. Create guest session
    res = client.post("/api/v1/guest-sessions")
    assert res.status_code == 201
    assert "claimlab_guest" in res.cookies
    data = res.json()
    assert "csrf_token" in data
    assert "expires_at" in data

    # 3. Authenticated access to /api/v1/me succeeds
    res_me = client.get("/api/v1/me")
    assert res_me.status_code == 200
    assert res_me.json()["model_mode"] == "fixture"


def test_complete_learning_journey():
    client = TestClient(app)

    # 1. Create Guest Session
    res_guest = client.post("/api/v1/guest-sessions")
    assert res_guest.status_code == 201
    csrf_token = res_guest.json()["csrf_token"]
    assert csrf_token is not None

    # 2. Upload Document
    pdf_path = "examples/claimlab_attention_lab.pdf"
    assert os.path.exists(pdf_path)
    with open(pdf_path, "rb") as f:
        res_upload = client.post(
            "/api/v1/documents",
            headers={"X-CSRF-Token": csrf_token},
            files={"file": ("claimlab_attention_lab.pdf", f, "application/pdf")},
        )
    assert res_upload.status_code == 202
    upload_data = res_upload.json()
    doc_id = upload_data["document_id"]

    # Verify document details
    res_doc = client.get(f"/api/v1/documents/{doc_id}")
    assert res_doc.status_code == 200
    doc_info = res_doc.json()
    assert doc_info["page_count"] == 3
    assert doc_info["status"] == "completed"

    # Verify PDF file retrieval
    res_file = client.get(f"/api/v1/documents/{doc_id}/file")
    assert res_file.status_code == 200
    assert res_file.headers["content-type"] == "application/pdf"

    # 3. Create Source Selection (Pages 1 to 2)
    res_sel = client.post(
        f"/api/v1/documents/{doc_id}/selections",
        headers={"X-CSRF-Token": csrf_token},
        json={"page_start": 1, "page_end": 2, "question": "Why is attention scaled by 1/sqrt(d_k)?"},
    )
    assert res_sel.status_code == 201
    sel_data = res_sel.json()
    sel_id = sel_data["selection_id"]
    assert len(sel_data["anchors"]) > 0

    # 4. Create Learning Session
    res_session = client.post(
        "/api/v1/learning-sessions",
        headers={"X-CSRF-Token": csrf_token},
        json={"selection_id": sel_id, "goal": "Understand attention scaling"},
    )
    assert res_session.status_code == 202
    session_data = res_session.json()
    session_id = session_data["session_id"]
    assert session_data["revision"] >= 1  # Incremented after initial tutor turn

    # 5. Fetch Session State
    res_state = client.get(f"/api/v1/learning-sessions/{session_id}")
    assert res_state.status_code == 200
    state = res_state.json()
    assert state["active_concept"] == "attention_scaling"
    assert len(state["board"]["objects"]) >= 4
    assert state["latest_run_id"] is not None
    assert state["active_task"]["task_id"] == "attention-scale-apply-01"

    # 6. Verify Experiment Run Output
    run_id = state["latest_run_id"]
    res_run = client.get(f"/api/v1/runs/{run_id}")
    assert res_run.status_code == 200
    run_data = res_run.json()
    assert run_data["status"] == "succeeded"
    assert len(run_data["output"]["results"]) == 3  # dims 8, 32, 128

    # 7. Submit Correct Answer to Task
    current_rev = state["revision"]
    res_event = client.post(
        f"/api/v1/learning-sessions/{session_id}/events",
        headers={"X-CSRF-Token": csrf_token},
        json={
            "schema_version": 1,
            "event_type": "explanation_submitted",
            "expected_revision": current_rev,
            "payload": {
                "task_id": "attention-scale-apply-01",
                "task_variant": "v1-a",
                "answer": "3",
            },
        },
    )
    assert res_event.status_code == 202
    assert res_event.json()["current_revision"] == current_rev + 1

    # 8. Check updated state after tutor response (1st variant correct -> supported_with_help)
    res_updated_state = client.get(f"/api/v1/learning-sessions/{session_id}")
    updated_state = res_updated_state.json()
    assert updated_state["evidence_summary"]["attention_scaling"] == "supported_with_help"
    assert updated_state["active_task"]["task_variant"] == "v1-b"

    # 9. Complete 2nd variant to reach supported_independently (15 / sqrt(25) = 3)
    rev2 = updated_state["revision"]
    res_event2 = client.post(
        f"/api/v1/learning-sessions/{session_id}/events",
        headers={"X-CSRF-Token": csrf_token},
        json={
            "schema_version": 1,
            "event_type": "explanation_submitted",
            "expected_revision": rev2,
            "payload": {
                "task_id": "attention-scale-apply-01",
                "task_variant": "v1-b",
                "answer": "3",
            },
        },
    )
    assert res_event2.status_code == 202

    res_final_state = client.get(f"/api/v1/learning-sessions/{session_id}")
    final_state = res_final_state.json()
    assert final_state["evidence_summary"]["attention_scaling"] == "supported_independently"

    # 10. Verify Second Guest Cannot Access This Session (Ownership Isolation)
    client2 = TestClient(app)
    client2.post("/api/v1/guest-sessions")
    res_cross = client2.get(f"/api/v1/learning-sessions/{session_id}")
    assert res_cross.status_code == 404
    assert res_cross.json()["error"]["code"] == "RESOURCE_NOT_FOUND"
