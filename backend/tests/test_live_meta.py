"""Tests for Live Meta Model integration (T-META-01, T-META-02).

These tests run only when MODEL_MODE=live and META_API_KEY is configured.
"""
import pytest
from claimlab.config import settings
from claimlab.database import SessionLocal, Base, engine
from claimlab.models import LearningSession, Document, SourceAnchor
from claimlab.contracts.whiteboard import SceneGraph
from claimlab.services.agent_orchestrator import AgentOrchestrator


@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.mark.live_meta
def test_t_meta_01_provider_probe():
    """T-META-01: Verify live Meta model endpoint accepts configured model and tool loop."""
    if not settings.META_API_KEY or settings.MODEL_MODE != "live":
        pytest.skip("META_API_KEY is not set or MODEL_MODE != 'live'. Skipping live Meta API test.")

    import httpx
    headers = {
        "Authorization": f"Bearer {settings.META_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.META_MODEL,
        "messages": [
            {"role": "system", "content": "You are a test tutor."},
            {"role": "user", "content": "Hello! Reply with OK."}
        ],
        "max_tokens": 50,
    }
    with httpx.Client(timeout=20.0) as client:
        resp = client.post(
            f"{settings.META_BASE_URL.rstrip('/')}/chat/completions",
            headers=headers,
            json=payload,
        )
        assert resp.status_code == 200, f"Meta API responded with error: {resp.text}"
        data = resp.json()
        assert "choices" in data
        assert len(data["choices"]) > 0
        choice = data["choices"][0]
        assert "message" in choice


@pytest.mark.live_meta
def test_t_meta_02_orchestrator_live_turn(db):
    """T-META-02: Orchestrator executes live turn without falling back to fixture."""
    if not settings.META_API_KEY or settings.MODEL_MODE != "live":
        pytest.skip("META_API_KEY is not set or MODEL_MODE != 'live'. Skipping live Meta API test.")

    # Setup test learning session
    doc = Document(
        owner_id="live-tester",
        filename="live_probe.pdf",
        sha256="fake-hash",
        storage_path="/dev/null",
        status="parsed",
        page_count=1,
    )
    db.add(doc)
    db.commit()

    anchor = SourceAnchor(
        document_id=doc.id,
        page_number=1,
        anchor_id="anchor-1",
        quote="Attention is all you need.",
        char_start=0,
        char_end=26,
    )
    db.add(anchor)
    db.commit()

    ls = LearningSession(
        owner_id="live-tester",
        source_document_id=doc.id,
        goal="Verify live tutor loop",
        revision=1,
        active_concept="attention_scaling",
    )
    db.add(ls)
    db.commit()

    orch = AgentOrchestrator(db)
    scene = SceneGraph(board_revision=1, objects=[], connectors=[], groups=[])

    res = orch._execute_live_turn(
        session=ls,
        job_id="test-live-job-1",
        selection=None,
        anchors=[anchor],
        current_scene=scene,
        recent_events=[],
        evidence_list=[],
    )

    assert res["mode"] == "live", "Expected live execution mode"
    assert res["narration"] != "", "Expected non-empty narration from live model"
