"""Tests for Live Meta Model integration (T-META-01, T-META-02).

These tests run only when MODEL_MODE=live and META_API_KEY is configured.
"""
import pytest
from datetime import datetime, timezone, timedelta
from claimlab.config import settings
from claimlab.database import SessionLocal, Base, engine
from claimlab.models import GuestOwner, LearningSession, Document, SourceAnchor, SourceSelection, Job
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
    import uuid
    uid = str(uuid.uuid4())
    expires = datetime.now(timezone.utc) + timedelta(days=1)
    owner = GuestOwner(
        id=uid,
        credential_hash=f"hash_{uid}",
        csrf_secret_hash=f"csrf_{uid}",
        expires_at=expires,
    )
    db.add(owner)
    db.commit()

    doc = Document(
        id=f"doc_{uid}",
        owner_id=owner.id,
        filename="live_probe.pdf",
        storage_key="/dev/null",
        sha256="fake-hash",
        size_bytes=100,
        extraction_status="completed",
        page_count=1,
        expires_at=expires,
    )
    db.add(doc)
    db.commit()

    anchor = SourceAnchor(
        id=f"anc_{uid}",
        document_id=doc.id,
        page_number=1,
        quote="Attention is all you need.",
        start_offset=0,
        end_offset=26,
        text_hash="hash_quote_1",
    )
    db.add(anchor)
    db.commit()

    sel = SourceSelection(
        id=f"sel_{uid}",
        owner_id=owner.id,
        document_id=doc.id,
        page_start=1,
        page_end=1,
        question="How does attention scaling work?",
        content_hash="hash_selection_1",
        topic_assessment="supported",
    )
    db.add(sel)
    db.commit()

    ls = LearningSession(
        id=f"sess_{uid}",
        owner_id=owner.id,
        selection_id=sel.id,
        goal="Verify live tutor loop",
        revision=1,
        active_concept="attention_scaling",
        expires_at=expires,
    )
    db.add(ls)
    db.commit()

    test_job = Job(
        id=f"job_{uid}",
        owner_id=owner.id,
        session_id=ls.id,
        kind="tutor_turn",
        status="running",
        deadline_seconds=180,
    )
    db.add(test_job)
    db.commit()

    orch = AgentOrchestrator(db)
    scene = SceneGraph(board_revision=1, objects=[])

    res = orch._execute_live_turn(
        session=ls,
        job_id=test_job.id,
        selection=None,
        anchors=[anchor],
        current_scene=scene,
        recent_events=[],
        evidence_list=[],
    )

    assert res["mode"] == "live", "Expected live execution mode"
    assert res["narration"] != "", "Expected non-empty narration from live model"
