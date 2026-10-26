"""FastAPI application implementing the ClaimLab REST API contracts."""
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict
import uuid

from fastapi import (
    Depends,
    FastAPI,
    File,
    HTTPException,
    Request,
    Response,
    UploadFile,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from claimlab.config import settings
from claimlab.contracts import (
    ErrorCode,
    ErrorDetail,
    GuestSessionResponse,
    MeResponse,
    DeleteDataResponse,
    PageExtractionStatus,
    DocumentPageMeta,
    DocumentStatusResponse,
    SourceAnchor as SourceAnchorContract,
    CreateSelectionRequest,
    SourceSelectionResponse,
    CreateSessionRequest,
    CreateSessionResponse,
    SubmitLearnerEventRequest,
    SubmitLearnerEventResponse,
    SessionStateResponse,
    ExperimentRunResponse,
    JobResponse,
    JobKind,
    JobStatus,
    EvidenceCategory,
)
from claimlab.database import Base, engine, get_db
from claimlab.models import (
    GuestOwner,
    Document as DBDocument,
    DocumentPage,
    SourceAnchor as DBSourceAnchor,
    SourceSelection,
    LearningSession,
    BoardSnapshot,
    LearnerEvent,
    ConceptEvidence,
    ExperimentRun,
    Job,
    JobEvent,
)
from claimlab.numerics.runner import runner
from claimlab.security import (
    GUEST_COOKIE_NAME,
    create_guest,
    get_current_guest,
    verify_csrf,
)
from claimlab.services.pdf_service import extract_pdf_content, create_anchors_for_text
from claimlab.services.agent_orchestrator import AgentOrchestrator

# Initialize database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="ClaimLab API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration for Vite dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.PUBLIC_ORIGIN, "http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Formats all HTTP errors into the canonical ErrorResponse schema."""
    if isinstance(exc.detail, dict) and "code" in exc.detail:
        detail = ErrorDetail(
            code=exc.detail.get("code", ErrorCode.INVALID_REQUEST),
            message=exc.detail.get("message", "An error occurred"),
            details=exc.detail.get("details"),
        )
    else:
        detail = ErrorDetail(
            code=ErrorCode.INVALID_REQUEST,
            message=str(exc.detail),
        )
    return JSONResponse(status_code=exc.status_code, content={"error": detail.model_dump()})


# --- Health Endpoints ---
@app.get("/health/live")
def health_live():
    return {"status": "alive"}


@app.get("/health/ready")
def health_ready(db: Session = Depends(get_db)):
    try:
        db.execute(Base.metadata.tables["guest_owners"].select().limit(1))
        db_status = "ok"
    except Exception as e:
        db_status = f"error: {str(e)}"
    return {
        "status": "ready" if db_status == "ok" else "degraded",
        "database": db_status,
        "model_mode": settings.MODEL_MODE,
        "meta_model": settings.META_MODEL,
        "recipes": ["softmax_sensitivity_v1", "attention_scaling_v1", "causal_masking_v1"],
    }


# --- Guest Identity & Session Lifecycle ---
@app.post("/api/v1/guest-sessions", status_code=status.HTTP_201_CREATED, response_model=GuestSessionResponse)
def create_guest_session(response: Response, db: Session = Depends(get_db)):
    owner, raw_cookie, raw_csrf = create_guest(db)
    response.set_cookie(
        key=GUEST_COOKIE_NAME,
        value=raw_cookie,
        httponly=True,
        secure=settings.APP_ENV != "development",
        samesite="lax",
        max_age=86400,
    )
    return GuestSessionResponse(
        expires_at=owner.expires_at.isoformat(),
        csrf_token=raw_csrf,
    )


@app.get("/api/v1/me", response_model=MeResponse)
def get_me(guest: GuestOwner = Depends(get_current_guest)):
    return MeResponse(
        guest_id=guest.id,
        expires_at=guest.expires_at.isoformat(),
        model_mode=settings.MODEL_MODE,
        limits={
            "max_documents": 3,
            "max_file_size_mib": 10,
            "max_pages": 50,
            "max_sessions": 5,
        },
    )


@app.delete("/api/v1/me/data", status_code=status.HTTP_202_ACCEPTED, response_model=DeleteDataResponse)
def delete_my_data(
    request: Request,
    guest: GuestOwner = Depends(get_current_guest),
    db: Session = Depends(get_db),
):
    verify_csrf(request, request.headers.get("X-CSRF-Token"), guest)
    now = datetime.now(timezone.utc)
    guest.deleted_at = now
    db.commit()
    return DeleteDataResponse(deletion_id=str(uuid.uuid4()), status="deleted")


# --- Document Upload & Anchoring ---
@app.post("/api/v1/documents", status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    guest: GuestOwner = Depends(get_current_guest),
    db: Session = Depends(get_db),
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "UNSUPPORTED_DOCUMENT", "message": "Only native PDF files are supported"},
        )

    file_bytes = await file.read()
    if len(file_bytes) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={"code": "UPLOAD_TOO_LARGE", "message": "Document exceeds 10 MiB limit"},
        )

    doc_id = str(uuid.uuid4())
    job_id = str(uuid.uuid4())
    sha256 = hashlib.sha256(file_bytes).hexdigest()

    storage_dir = settings.data_path / "documents"
    storage_dir.mkdir(parents=True, exist_ok=True)
    storage_path = storage_dir / f"{doc_id}.pdf"
    with open(storage_path, "wb") as f:
        f.write(file_bytes)

    try:
        ext_result = extract_pdf_content(file_bytes)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "UNSUPPORTED_DOCUMENT", "message": f"Failed to parse PDF: {str(e)}"},
        )

    doc = DBDocument(
        id=doc_id,
        owner_id=guest.id,
        filename=file.filename,
        storage_key=str(storage_path),
        sha256=sha256,
        size_bytes=len(file_bytes),
        page_count=ext_result.page_count,
        extraction_status="completed",
        warnings_json=json.dumps(ext_result.warnings),
        expires_at=guest.expires_at,
    )
    db.add(doc)

    # Save pages and anchors
    for page_num, text, page_status, page_warnings in ext_result.pages:
        db_page = DocumentPage(
            document_id=doc_id,
            page_number=page_num,
            normalized_text=text,
            char_count=len(text),
            extraction_status=page_status.value,
            warnings_json=json.dumps(page_warnings),
        )
        db.add(db_page)

        anchors = create_anchors_for_text(doc_id, page_num, text)
        for anc in anchors:
            db_anc = DBSourceAnchor(
                id=anc.id,
                document_id=doc_id,
                page_number=anc.page_number,
                start_offset=anc.start_offset,
                end_offset=anc.end_offset,
                quote=anc.quote,
                text_hash=anc.text_hash,
            )
            db.add(db_anc)

    parse_job = Job(
        id=job_id,
        owner_id=guest.id,
        document_id=doc_id,
        kind=JobKind.PARSE_DOCUMENT.value,
        status=JobStatus.SUCCEEDED.value,
        progress=1.0,
    )
    db.add(parse_job)
    db.commit()

    return {"document_id": doc_id, "job_id": job_id}


@app.get("/api/v1/documents/{document_id}", response_model=DocumentStatusResponse)
def get_document(
    document_id: str,
    guest: GuestOwner = Depends(get_current_guest),
    db: Session = Depends(get_db),
):
    doc = db.query(DBDocument).filter(DBDocument.id == document_id, DBDocument.owner_id == guest.id).first()
    if not doc:
        raise HTTPException(status_code=404, detail={"code": "RESOURCE_NOT_FOUND", "message": "Document not found"})

    pages = db.query(DocumentPage).filter(DocumentPage.document_id == document_id).order_by(DocumentPage.page_number).all()
    page_metas = [
        DocumentPageMeta(
            page_number=p.page_number,
            char_count=p.char_count,
            extraction_status=PageExtractionStatus(p.extraction_status),
            warnings=json.loads(p.warnings_json),
        )
        for p in pages
    ]
    return DocumentStatusResponse(
        document_id=doc.id,
        filename=doc.filename,
        page_count=doc.page_count,
        status=PageExtractionStatus(doc.extraction_status),
        pages=page_metas,
        warnings=json.loads(doc.warnings_json),
    )


@app.get("/api/v1/documents/{document_id}/file")
def get_document_file(
    document_id: str,
    guest: GuestOwner = Depends(get_current_guest),
    db: Session = Depends(get_db),
):
    doc = db.query(DBDocument).filter(DBDocument.id == document_id, DBDocument.owner_id == guest.id).first()
    if not doc or not os.path.exists(doc.storage_key):
        raise HTTPException(status_code=404, detail={"code": "RESOURCE_NOT_FOUND", "message": "File not found"})

    return FileResponse(
        path=doc.storage_key,
        media_type="application/pdf",
        headers={"Cache-Control": "private, no-store"},
    )


@app.post("/api/v1/documents/{document_id}/selections", status_code=status.HTTP_201_CREATED, response_model=SourceSelectionResponse)
def create_selection(
    document_id: str,
    req: CreateSelectionRequest,
    guest: GuestOwner = Depends(get_current_guest),
    db: Session = Depends(get_db),
):
    doc = db.query(DBDocument).filter(DBDocument.id == document_id, DBDocument.owner_id == guest.id).first()
    if not doc:
        raise HTTPException(status_code=404, detail={"code": "RESOURCE_NOT_FOUND", "message": "Document not found"})

    if req.page_start > req.page_end or req.page_end > doc.page_count:
        raise HTTPException(status_code=422, detail={"code": "PARAMETERS_INVALID", "message": "Invalid page range"})

    pages = (
        db.query(DocumentPage)
        .filter(DocumentPage.document_id == document_id, DocumentPage.page_number.between(req.page_start, req.page_end))
        .all()
    )
    combined_text = "\n".join(p.normalized_text for p in pages)
    if not combined_text.strip():
        raise HTTPException(status_code=422, detail={"code": "SOURCE_UNREADABLE", "message": "Selected pages have no text"})

    content_hash = hashlib.sha256(combined_text.encode("utf-8")).hexdigest()
    sel_id = str(uuid.uuid4())

    selection = SourceSelection(
        id=sel_id,
        owner_id=guest.id,
        document_id=document_id,
        page_start=req.page_start,
        page_end=req.page_end,
        question=req.question,
        content_hash=content_hash,
        topic_assessment="supported",
    )
    db.add(selection)
    db.commit()

    db_anchors = (
        db.query(DBSourceAnchor)
        .filter(DBSourceAnchor.document_id == document_id, DBSourceAnchor.page_number.between(req.page_start, req.page_end))
        .all()
    )
    anchors = [
        SourceAnchorContract(
            id=a.id,
            document_id=a.document_id,
            page_number=a.page_number,
            start_offset=a.start_offset,
            end_offset=a.end_offset,
            quote=a.quote,
            text_hash=a.text_hash,
        )
        for a in db_anchors
    ]

    return SourceSelectionResponse(
        selection_id=sel_id,
        document_id=document_id,
        page_start=req.page_start,
        page_end=req.page_end,
        question=req.question,
        anchors=anchors,
        content_hash=content_hash,
        topic_assessment="supported",
    )


# --- Learning Sessions & Tutor Interaction ---
@app.post("/api/v1/learning-sessions", status_code=status.HTTP_202_ACCEPTED, response_model=CreateSessionResponse)
def create_learning_session(
    req: CreateSessionRequest,
    guest: GuestOwner = Depends(get_current_guest),
    db: Session = Depends(get_db),
):
    selection = db.query(SourceSelection).filter(SourceSelection.id == req.selection_id, SourceSelection.owner_id == guest.id).first()
    if not selection:
        raise HTTPException(status_code=404, detail={"code": "RESOURCE_NOT_FOUND", "message": "Selection not found"})

    session_id = str(uuid.uuid4())
    job_id = str(uuid.uuid4())

    new_session = LearningSession(
        id=session_id,
        owner_id=guest.id,
        selection_id=req.selection_id,
        goal=req.goal or selection.question,
        preferences_json=json.dumps(req.preferences or {}),
        active_concept="attention_scaling",
        revision=1,
        active_job_id=job_id,
        expires_at=guest.expires_at,
    )
    db.add(new_session)

    init_job = Job(
        id=job_id,
        owner_id=guest.id,
        session_id=session_id,
        kind=JobKind.TUTOR_TURN.value,
        status=JobStatus.RUNNING.value,
        progress=0.1,
    )
    db.add(init_job)
    db.commit()

    # Execute initial tutor turn
    orchestrator = AgentOrchestrator(db)
    orchestrator.execute_tutor_turn(session_id, job_id)

    init_job.status = JobStatus.SUCCEEDED.value
    init_job.progress = 1.0
    new_session.active_job_id = None
    db.commit()

    return CreateSessionResponse(
        session_id=session_id,
        revision=new_session.revision,
        initial_job_id=job_id,
    )


@app.get("/api/v1/learning-sessions/{session_id}", response_model=SessionStateResponse)
def get_learning_session(
    session_id: str,
    guest: GuestOwner = Depends(get_current_guest),
    db: Session = Depends(get_db),
):
    session = db.query(LearningSession).filter(LearningSession.id == session_id, LearningSession.owner_id == guest.id).first()
    if not session:
        raise HTTPException(status_code=404, detail={"code": "RESOURCE_NOT_FOUND", "message": "Session not found"})

    snapshot = (
        db.query(BoardSnapshot)
        .filter(BoardSnapshot.session_id == session_id)
        .order_by(BoardSnapshot.revision.desc())
        .first()
    )
    scene = json.loads(snapshot.scene_json) if snapshot else {"schema_version": 1, "board_revision": 0, "objects": []}

    evidence = db.query(ConceptEvidence).filter(ConceptEvidence.session_id == session_id).all()
    ev_summary = {e.concept_id: EvidenceCategory(e.category) for e in evidence}

    # Find latest run
    latest_run = db.query(ExperimentRun).filter(ExperimentRun.session_id == session_id).order_by(ExperimentRun.started_at.desc()).first()

    # Find active task from recent job events
    recent_event = (
        db.query(JobEvent)
        .join(Job, JobEvent.job_id == Job.id)
        .filter(Job.session_id == session_id, JobEvent.event_type == "tutor_turn_completed")
        .order_by(JobEvent.created_at.desc(), JobEvent.id.desc())
        .first()
    )
    active_task = None
    if recent_event:
        payload = json.loads(recent_event.payload_json)
        active_task = payload.get("active_task")

    return SessionStateResponse(
        session_id=session.id,
        revision=session.revision,
        active_concept=session.active_concept,
        active_job_id=session.active_job_id,
        board=scene,
        evidence_summary=ev_summary,
        active_task=active_task,
        latest_run_id=latest_run.id if latest_run else None,
    )


@app.post("/api/v1/learning-sessions/{session_id}/events", status_code=status.HTTP_202_ACCEPTED, response_model=SubmitLearnerEventResponse)
def submit_learner_event(
    session_id: str,
    req: SubmitLearnerEventRequest,
    guest: GuestOwner = Depends(get_current_guest),
    db: Session = Depends(get_db),
):
    session = db.query(LearningSession).filter(LearningSession.id == session_id, LearningSession.owner_id == guest.id).first()
    if not session:
        raise HTTPException(status_code=404, detail={"code": "RESOURCE_NOT_FOUND", "message": "Session not found"})

    if req.expected_revision != session.revision:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "REVISION_CONFLICT",
                "message": f"Expected revision {req.expected_revision} does not match current revision {session.revision}",
                "details": {"current_revision": session.revision},
            },
        )

    job_id = str(uuid.uuid4())
    event_count = db.query(LearnerEvent).filter(LearnerEvent.session_id == session_id).count()

    event = LearnerEvent(
        id=req.event_id,
        owner_id=guest.id,
        session_id=session_id,
        client_event_id=req.event_id,
        event_type=req.event_type,
        payload_json=json.dumps(req.payload),
        expected_revision=req.expected_revision,
        sequence=event_count + 1,
    )
    db.add(event)

    tutor_job = Job(
        id=job_id,
        owner_id=guest.id,
        session_id=session_id,
        kind=JobKind.TUTOR_TURN.value,
        status=JobStatus.RUNNING.value,
        progress=0.2,
    )
    db.add(tutor_job)
    session.active_job_id = job_id
    db.commit()

    # Execute tutor response turn
    orchestrator = AgentOrchestrator(db)
    orchestrator.execute_tutor_turn(session_id, job_id, trigger_event_id=req.event_id)

    tutor_job.status = JobStatus.SUCCEEDED.value
    tutor_job.progress = 1.0
    session.active_job_id = None
    db.commit()

    return SubmitLearnerEventResponse(
        event_id=req.event_id,
        current_revision=session.revision,
        tutor_job_id=job_id,
    )


# --- Experiments ---
@app.post("/api/v1/learning-sessions/{session_id}/runs", status_code=status.HTTP_202_ACCEPTED)
def execute_session_run(
    session_id: str,
    req_body: Dict[str, Any],
    guest: GuestOwner = Depends(get_current_guest),
    db: Session = Depends(get_db),
):
    session = db.query(LearningSession).filter(LearningSession.id == session_id, LearningSession.owner_id == guest.id).first()
    if not session:
        raise HTTPException(status_code=404, detail={"code": "RESOURCE_NOT_FOUND", "message": "Session not found"})

    recipe_id = req_body.get("recipe_id")
    parameters = req_body.get("parameters", {})
    if not recipe_id:
        raise HTTPException(status_code=422, detail={"code": "PARAMETERS_INVALID", "message": "recipe_id is required"})

    try:
        run_res = runner.run(recipe_id, parameters)
    except Exception as e:
        raise HTTPException(status_code=422, detail={"code": "PARAMETERS_INVALID", "message": str(e)})

    job_id = str(uuid.uuid4())
    db_run = ExperimentRun(
        id=run_res.run_id,
        owner_id=guest.id,
        session_id=session_id,
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
    db.add(db_run)
    db.commit()

    return {
        "run_id": run_res.run_id,
        "current_revision": session.revision,
        "job_id": job_id,
    }


@app.get("/api/v1/runs/{run_id}", response_model=ExperimentRunResponse)
def get_run(
    run_id: str,
    guest: GuestOwner = Depends(get_current_guest),
    db: Session = Depends(get_db),
):
    run = db.query(ExperimentRun).filter(ExperimentRun.id == run_id, ExperimentRun.owner_id == guest.id).first()
    if not run:
        raise HTTPException(status_code=404, detail={"code": "RESOURCE_NOT_FOUND", "message": "Run not found"})

    checks = [json.loads(c) if isinstance(c, str) else c for c in json.loads(run.checks_json)]
    return ExperimentRunResponse(
        run_id=run.id,
        recipe_id=run.recipe_id,
        parameters=json.loads(run.parameters_json),
        parameter_hash=run.parameter_hash,
        seed=run.seed,
        status=run.status,
        output=json.loads(run.output_json) if run.output_json else None,
        checks=checks,
        assumptions=[],
        runner_digest="local-runner-v1",
        numpy_version="2.1.3",
        started_at=run.started_at.isoformat(),
        completed_at=run.completed_at.isoformat() if run.completed_at else None,
    )


@app.get("/api/v1/jobs/{job_id}", response_model=JobResponse)
def get_job(
    job_id: str,
    guest: GuestOwner = Depends(get_current_guest),
    db: Session = Depends(get_db),
):
    job = db.query(Job).filter(Job.id == job_id, Job.owner_id == guest.id).first()
    if not job:
        raise HTTPException(status_code=404, detail={"code": "RESOURCE_NOT_FOUND", "message": "Job not found"})

    return JobResponse(
        job_id=job.id,
        kind=JobKind(job.kind),
        status=JobStatus(job.status),
        deadline_seconds=job.deadline_seconds,
        progress=job.progress,
        error_code=job.error_code,
        error_message=job.error_message,
    )


# --- Static Assets & Frontend Mounting ---
examples_dir = Path(__file__).resolve().parent.parent.parent.parent / "examples"
if examples_dir.exists():
    app.mount("/examples", StaticFiles(directory=str(examples_dir)), name="examples")

frontend_dist = Path(__file__).resolve().parent.parent.parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")

