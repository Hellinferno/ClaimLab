"""FastAPI application implementing the complete ClaimLab REST API contracts."""
import asyncio
import hashlib
import json
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import uuid

from fastapi import (
    Depends,
    FastAPI,
    File,
    Header,
    HTTPException,
    Request,
    Response,
    UploadFile,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
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
    IdempotencyRecord,
    TaskAttempt,
    TeachingDecision,
    ToolInvocation,
    BudgetReservation,
)
from claimlab.numerics.runner import runner
from claimlab.contracts.experiment import RecipeId
from claimlab.learning.task_bank import TASK_REGISTRY
from claimlab.security import (
    GUEST_COOKIE_NAME,
    create_guest,
    get_current_guest,
    verify_csrf,
    hash_token,
)
from claimlab.services.pdf_service import extract_pdf_content, create_anchors_for_text
from claimlab.services.agent_orchestrator import (
    TASK_KEY_EVENT,
    AgentOrchestrator,
    ProviderUnavailableError,
    experiment_run_record,
    latest_tutor_step,
    lesson_kind_for,
)
from claimlab.services.lesson_builder import paginate_text
from claimlab.services.sandbox_runs import SandboxSpecError, execute_sandbox_experiment

# Exceeds a bounded live tool loop: research, sandbox runs, and the final lesson call.
TUTOR_TURN_LEASE = timedelta(seconds=300)

# Mechanism terms of the reviewed labs. A paper that merely uses an attention layer rarely names two;
# "key" alone is excluded because ordinary prose ("key findings") is full of it.
ATTENTION_LAB_TERMS = (
    "softmax", "query", "queries", "keys", "d_k", "dot product", "dot-product", "inner product",
    "causal mask", "masked", "self-attention", "scaled dot", "attention weight",
)


def assess_topic(text: str) -> str:
    """supported: the reviewed attention lab fits; open: the live tutor teaches it; unsupported otherwise."""
    lower = text.lower()
    if sum(term in lower for term in ATTENTION_LAB_TERMS) >= 2:
        return "supported"
    return "open" if settings.MODEL_MODE == "live" else "unsupported"

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


def handle_idempotency(
    db: Session,
    owner_id: str,
    route_scope: str,
    idempotency_key: Optional[str],
    payload_dict: Dict[str, Any],
) -> Optional[Tuple[int, Dict[str, Any]]]:
    """Checks for existing idempotency records or raises on conflict."""
    if not idempotency_key:
        return None

    fingerprint = hashlib.sha256(json.dumps(payload_dict, sort_keys=True).encode("utf-8")).hexdigest()
    record = (
        db.query(IdempotencyRecord)
        .filter(
            IdempotencyRecord.owner_id == owner_id,
            IdempotencyRecord.route_scope == route_scope,
            IdempotencyRecord.idempotency_key == idempotency_key,
        )
        .first()
    )
    if record:
        if record.request_fingerprint != fingerprint:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": "IDEMPOTENCY_CONFLICT", "message": "Idempotency key reused with different payload"},
            )
        return record.status_code, json.loads(record.response_json)
    return None


def record_idempotency(
    db: Session,
    owner_id: str,
    route_scope: str,
    idempotency_key: Optional[str],
    payload_dict: Dict[str, Any],
    status_code: int,
    response_data: Dict[str, Any],
) -> None:
    """Stores an idempotency record for a successful request."""
    if not idempotency_key:
        return

    fingerprint = hashlib.sha256(json.dumps(payload_dict, sort_keys=True).encode("utf-8")).hexdigest()
    now = datetime.now(timezone.utc)
    rec = IdempotencyRecord(
        owner_id=owner_id,
        route_scope=route_scope,
        idempotency_key=idempotency_key,
        request_fingerprint=fingerprint,
        status_code=status_code,
        response_json=json.dumps(response_data),
        created_at=now,
        expires_at=now + timedelta(hours=24),
    )
    db.add(rec)
    db.commit()


def execute_tutor_job(db: Session, session: LearningSession, job: Job, trigger_event_id: Optional[str] = None) -> None:
    """Keep job status and the session lock truthful after provider failures."""
    try:
        AgentOrchestrator(db).execute_tutor_turn(session.id, job.id, trigger_event_id)
    except Exception as exc:
        db.rollback()
        db.refresh(job)
        db.refresh(session)
        job.status = JobStatus.FAILED.value
        job.error_code = "PROVIDER_UNAVAILABLE" if isinstance(exc, ProviderUnavailableError) else "SERVICE_NOT_READY"
        job.error_message = "The tutor did not finish. Your saved lesson is available; try again."
        if session.active_job_id == job.id:
            session.active_job_id = None
        db.commit()
        raise HTTPException(status_code=503, detail={"code": job.error_code, "message": job.error_message}) from exc
    job.status = JobStatus.SUCCEEDED.value
    job.progress = 1.0
    if session.active_job_id == job.id:
        session.active_job_id = None
    db.commit()


def session_is_busy(db: Session, session: LearningSession) -> bool:
    """True while the session's mutation job may still be running.

    A turn whose lease has passed was orphaned (for example, by a restart
    mid-turn); it is failed and its lock released instead of blocking forever.
    """
    if not session.active_job_id:
        return False
    job = db.query(Job).filter(Job.id == session.active_job_id).first()
    if not job or job.status not in (JobStatus.QUEUED.value, JobStatus.RUNNING.value):
        return False
    lease = job.lease_expires_at
    if lease is None or lease.replace(tzinfo=timezone.utc) > datetime.now(timezone.utc):
        return True
    job.status = JobStatus.FAILED.value
    job.error_code = "WORKER_LOST"
    job.error_message = "The lesson update stopped before finishing."
    session.active_job_id = None
    session.fencing_generation += 1
    db.commit()
    return False


def discard_unstarted_session(db: Session, session_id: str) -> None:
    """Drop a lesson whose first tutor turn failed.

    It has nothing to resume, so it must neither hold session quota nor reopen
    as the active lesson. The failed job remains as the record of the attempt.
    """
    for model in (TaskAttempt, TeachingDecision, ConceptEvidence, BoardSnapshot, LearnerEvent, ExperimentRun):
        db.query(model).filter(model.session_id == session_id).delete(synchronize_session=False)
    db.query(LearningSession).filter(LearningSession.id == session_id).delete(synchronize_session=False)
    db.commit()


def remove_stored_upload(doc: DBDocument, document_root: Path) -> None:
    """Unlink an owner's stored PDF without ever touching unrelated files.

    Uploads live at <document_root>/<document id>.pdf. A stored key elsewhere
    predates a DATA_DIR change; that file is removed only when its name and
    digest prove it is this upload.
    """
    canonical = document_root / f"{doc.id}.pdf"
    targets = [canonical]
    if doc.storage_key:
        stored = Path(doc.storage_key).resolve()
        if (
            stored != canonical
            and stored.name == canonical.name
            and stored.is_file()
            and hashlib.sha256(stored.read_bytes()).hexdigest() == doc.sha256
        ):
            targets.append(stored)
    for target in targets:
        target.unlink(missing_ok=True)


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
def create_guest_session(request: Request, response: Response, db: Session = Depends(get_db)):
    origin = request.headers.get("origin")
    if origin and origin != settings.PUBLIC_ORIGIN and settings.APP_ENV != "development":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "ORIGIN_REJECTED", "message": f"Rejected origin: {origin}"},
        )

    # Reuse the browser's owner so bootstrap and reload can actually resume work.
    # The derived CSRF token remains stable across tabs without storing it raw.
    raw_cookie = request.cookies.get(GUEST_COOKIE_NAME)
    owner = None
    if raw_cookie:
        owner = db.query(GuestOwner).filter(
            GuestOwner.credential_hash == hash_token(raw_cookie),
            GuestOwner.deleted_at.is_(None),
            GuestOwner.expires_at > datetime.now(timezone.utc),
        ).first()
    if owner:
        raw_csrf = hash_token(f"csrf:{raw_cookie}")
        owner.csrf_secret_hash = hash_token(raw_csrf)
        db.commit()
    else:
        owner, raw_cookie, raw_csrf = create_guest(db)
    response.set_cookie(
        key=GUEST_COOKIE_NAME,
        value=raw_cookie,
        httponly=True,
        secure=settings.APP_ENV != "development",
        samesite="lax",
        max_age=max(0, int((owner.expires_at.replace(tzinfo=timezone.utc) - datetime.now(timezone.utc)).total_seconds())),
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
        web_research=settings.MODEL_MODE == "live" and bool(settings.TINYFISH_API_KEY),
    )


@app.delete("/api/v1/me/data", status_code=status.HTTP_202_ACCEPTED, response_model=DeleteDataResponse)
def delete_my_data(
    request: Request,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    guest: GuestOwner = Depends(get_current_guest),
    db: Session = Depends(get_db),
):
    verify_csrf(request, request.headers.get("X-CSRF-Token"), guest)

    cached = handle_idempotency(db, guest.id, "delete_data", idempotency_key, {})
    if cached:
        return cached[1]

    now = datetime.now(timezone.utc)
    guest.deleted_at = now
    db.flush()

    # Cancel active jobs and increment fencing generation
    sessions = db.query(LearningSession).filter(LearningSession.owner_id == guest.id).all()
    for s in sessions:
        s.fencing_generation += 1
        s.active_job_id = None

    jobs = db.query(Job).filter(Job.owner_id == guest.id, Job.status.in_(["queued", "running"])).all()
    for j in jobs:
        j.cancelled = True
        j.status = JobStatus.CANCELLED.value

    # A failed unlink must not be reported as successful erasure; rollback
    # keeps this guest authenticated so the same confirmed action can be retried.
    docs = db.query(DBDocument).filter(DBDocument.owner_id == guest.id).all()
    document_root = (settings.data_path / "documents").resolve()
    for doc in docs:
        try:
            remove_stored_upload(doc, document_root)
        except OSError as exc:
            db.rollback()
            raise HTTPException(status_code=503, detail={
                "code": "SERVICE_NOT_READY",
                "message": "Some uploaded files could not be removed. Your session is still active; please try deleting again.",
            }) from exc

    # Purge the authenticated owner's private content, children before parents.
    # Keep only the revoked guest and a content-free deletion receipt. No data
    # is erased merely by deploying this code: the guest must invoke this route.
    db.flush()
    session_ids = [s.id for s in sessions]
    document_ids = [doc.id for doc in docs]
    job_ids = [row[0] for row in db.query(Job.id).filter(Job.owner_id == guest.id).all()]
    for model in (ToolInvocation, JobEvent):
        db.query(model).filter(model.job_id.in_(job_ids)).delete(synchronize_session=False)
    for model in (TaskAttempt, TeachingDecision, ConceptEvidence, BoardSnapshot):
        db.query(model).filter(model.session_id.in_(session_ids)).delete(synchronize_session=False)
    db.query(LearnerEvent).filter(LearnerEvent.owner_id == guest.id).delete(synchronize_session=False)
    db.query(ExperimentRun).filter(ExperimentRun.owner_id == guest.id).delete(synchronize_session=False)
    db.query(BudgetReservation).filter(BudgetReservation.owner_id == guest.id).delete(synchronize_session=False)
    db.query(Job).filter(Job.owner_id == guest.id).delete(synchronize_session=False)
    db.query(LearningSession).filter(LearningSession.owner_id == guest.id).delete(synchronize_session=False)
    db.query(SourceSelection).filter(SourceSelection.owner_id == guest.id).delete(synchronize_session=False)
    for model in (DBSourceAnchor, DocumentPage):
        db.query(model).filter(model.document_id.in_(document_ids)).delete(synchronize_session=False)
    db.query(DBDocument).filter(DBDocument.owner_id == guest.id).delete(synchronize_session=False)
    db.query(IdempotencyRecord).filter(IdempotencyRecord.owner_id == guest.id).delete(synchronize_session=False)

    db.commit()

    res_data = {"deletion_id": str(uuid.uuid4()), "status": "deleted"}
    record_idempotency(db, guest.id, "delete_data", idempotency_key, {}, 202, res_data)
    return res_data


# --- Document Upload & Anchoring ---
@app.post("/api/v1/documents", status_code=status.HTTP_202_ACCEPTED)
def upload_document(
    request: Request,
    file: UploadFile = File(...),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    guest: GuestOwner = Depends(get_current_guest),
    db: Session = Depends(get_db),
):
    verify_csrf(request, request.headers.get("X-CSRF-Token"), guest)

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "UNSUPPORTED_DOCUMENT", "message": "Only native PDF files are supported"},
        )

    # A sync route runs parsing in FastAPI's thread pool, leaving the event loop
    # available for other students, progress requests, and cancellation.
    file_bytes = file.file.read(10 * 1024 * 1024 + 1)
    if len(file_bytes) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={"code": "UPLOAD_TOO_LARGE", "message": "Document exceeds 10 MiB limit"},
        )

    sha256 = hashlib.sha256(file_bytes).hexdigest()
    cached = handle_idempotency(db, guest.id, "upload_document", idempotency_key, {"sha256": sha256})
    if cached:
        return cached[1]

    # The same PDF is one document: uploading it again (for example, starting
    # the example lesson twice) returns it instead of consuming quota.
    existing = db.query(DBDocument).filter(DBDocument.owner_id == guest.id, DBDocument.sha256 == sha256).first()
    if existing:
        parse_job = db.query(Job).filter(Job.document_id == existing.id, Job.kind == JobKind.PARSE_DOCUMENT.value).first()
        res_data = {"document_id": existing.id, "job_id": parse_job.id}
        record_idempotency(db, guest.id, "upload_document", idempotency_key, {"sha256": sha256}, 202, res_data)
        return res_data

    # Check owner storage quota: max 3 documents
    doc_count = db.query(DBDocument).filter(DBDocument.owner_id == guest.id).count()
    if doc_count >= 3:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "PARAMETERS_INVALID",
                "message": "This guest workspace already holds 3 documents. Use Delete my data under Your session to start fresh.",
            },
        )

    doc_id = str(uuid.uuid4())
    job_id = str(uuid.uuid4())

    try:
        ext_result = extract_pdf_content(file_bytes)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "UNSUPPORTED_DOCUMENT", "message": f"Failed to parse PDF: {str(e)}"},
        )

    # Invalid uploads never become orphan files in private storage.
    storage_dir = settings.data_path / "documents"
    storage_dir.mkdir(parents=True, exist_ok=True)
    storage_path = storage_dir / f"{doc_id}.pdf"
    with open(storage_path, "wb") as f:
        f.write(file_bytes)

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

    res_data = {"document_id": doc_id, "job_id": job_id}
    record_idempotency(db, guest.id, "upload_document", idempotency_key, {"sha256": sha256}, 202, res_data)
    return res_data


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


@app.get("/api/v1/documents/{document_id}/pages")
def get_document_pages(
    document_id: str,
    guest: GuestOwner = Depends(get_current_guest),
    db: Session = Depends(get_db),
):
    """Returns extracted text and anchors for all pages in the document."""
    doc = db.query(DBDocument).filter(DBDocument.id == document_id, DBDocument.owner_id == guest.id).first()
    if not doc:
        raise HTTPException(status_code=404, detail={"code": "RESOURCE_NOT_FOUND", "message": "Document not found"})

    pages = db.query(DocumentPage).filter(DocumentPage.document_id == document_id).order_by(DocumentPage.page_number).all()
    anchors = db.query(DBSourceAnchor).filter(DBSourceAnchor.document_id == document_id).all()

    anchor_map: Dict[int, List[Dict[str, Any]]] = {}
    for a in anchors:
        anchor_map.setdefault(a.page_number, []).append({
            "id": a.id,
            "page_number": a.page_number,
            "quote": a.quote,
            "start_offset": a.start_offset,
            "end_offset": a.end_offset,
        })

    return [
        {
            "page_number": p.page_number,
            "normalized_text": p.normalized_text,
            "char_count": p.char_count,
            "anchors": anchor_map.get(p.page_number, []),
        }
        for p in pages
    ]


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
    request: Request,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    guest: GuestOwner = Depends(get_current_guest),
    db: Session = Depends(get_db),
):
    verify_csrf(request, request.headers.get("X-CSRF-Token"), guest)

    doc = db.query(DBDocument).filter(DBDocument.id == document_id, DBDocument.owner_id == guest.id).first()
    if not doc:
        raise HTTPException(status_code=404, detail={"code": "RESOURCE_NOT_FOUND", "message": "Document not found"})

    # Limits: max 5 pages per selection
    if (req.page_end - req.page_start + 1) > 5:
        raise HTTPException(status_code=422, detail={"code": "PARAMETERS_INVALID", "message": "Selection cannot exceed 5 pages"})

    if req.page_start > req.page_end or req.page_end > doc.page_count:
        raise HTTPException(status_code=422, detail={"code": "PARAMETERS_INVALID", "message": "Invalid page range"})

    pages = (
        db.query(DocumentPage)
        .filter(DocumentPage.document_id == document_id, DocumentPage.page_number.between(req.page_start, req.page_end))
        .order_by(DocumentPage.page_number)
        .all()
    )
    combined_text = "\n".join(p.normalized_text for p in pages)
    if not combined_text.strip():
        raise HTTPException(status_code=422, detail={"code": "SOURCE_UNREADABLE", "message": "Selected pages have no text"})

    if len(combined_text) > 30000:
        raise HTTPException(status_code=422, detail={"code": "PARAMETERS_INVALID", "message": "Selected text exceeds 30,000 characters limit"})

    # Topic assessment boundary check (T-TUTOR-01)
    topic_assessment = assess_topic(combined_text)

    content_hash = hashlib.sha256(combined_text.encode("utf-8")).hexdigest()
    cached = handle_idempotency(db, guest.id, "create_selection", idempotency_key, {"doc_id": document_id, "start": req.page_start, "end": req.page_end, "hash": content_hash, "question": req.question})
    if cached:
        return cached[1]

    sel_id = str(uuid.uuid4())
    selection = SourceSelection(
        id=sel_id,
        owner_id=guest.id,
        document_id=document_id,
        page_start=req.page_start,
        page_end=req.page_end,
        question=req.question,
        content_hash=content_hash,
        topic_assessment=topic_assessment,
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

    res_data = {
        "selection_id": sel_id,
        "document_id": document_id,
        "page_start": req.page_start,
        "page_end": req.page_end,
        "question": req.question,
        "anchors": [a.model_dump() for a in anchors],
        "content_hash": content_hash,
        "topic_assessment": topic_assessment,
    }
    record_idempotency(db, guest.id, "create_selection", idempotency_key, {"doc_id": document_id, "start": req.page_start, "end": req.page_end, "hash": content_hash, "question": req.question}, 201, res_data)
    return res_data


# --- Learning Sessions & Tutor Interaction ---
@app.post("/api/v1/learning-sessions", status_code=status.HTTP_202_ACCEPTED, response_model=CreateSessionResponse)
def create_learning_session(
    req: CreateSessionRequest,
    request: Request,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    guest: GuestOwner = Depends(get_current_guest),
    db: Session = Depends(get_db),
):
    verify_csrf(request, request.headers.get("X-CSRF-Token"), guest)

    cached = handle_idempotency(db, guest.id, "create_session", idempotency_key, req.model_dump(mode="json"))
    if cached:
        return cached[1]

    # Check session quota: max 5 sessions per owner
    sess_count = db.query(LearningSession).filter(LearningSession.owner_id == guest.id).count()
    if sess_count >= 5:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "PARAMETERS_INVALID",
                "message": "This guest workspace has reached its limit of 5 lessons. Continue the current lesson, or use Delete my data under Your session to start fresh.",
            },
        )

    selection = db.query(SourceSelection).filter(SourceSelection.id == req.selection_id, SourceSelection.owner_id == guest.id).first()
    if not selection:
        raise HTTPException(status_code=404, detail={"code": "RESOURCE_NOT_FOUND", "message": "Selection not found"})
    # Open lessons need the live tutor; fixture mode teaches only the reviewed attention lab.
    if selection.topic_assessment != "supported" and not (selection.topic_assessment == "open" and settings.MODEL_MODE == "live"):
        raise HTTPException(status_code=422, detail={
            "code": "UNSUPPORTED_DOCUMENT",
            "message": "This source is outside the supported attention, softmax, and causal masking labs. Choose a relevant passage or try the example note.",
        })

    session_id = str(uuid.uuid4())
    job_id = str(uuid.uuid4())

    new_session = LearningSession(
        id=session_id,
        owner_id=guest.id,
        selection_id=req.selection_id,
        goal=req.goal or selection.question,
        preferences_json=json.dumps(req.preferences or {}),
        active_concept="attention_scaling" if selection.topic_assessment == "supported" else None,
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
        lease_expires_at=datetime.now(timezone.utc) + TUTOR_TURN_LEASE,
    )
    db.add(init_job)
    db.commit()

    # Execute initial tutor turn
    try:
        execute_tutor_job(db, new_session, init_job)
    except HTTPException:
        discard_unstarted_session(db, session_id)
        raise

    res_data = {
        "session_id": session_id,
        "revision": new_session.revision,
        "initial_job_id": job_id,
    }
    record_idempotency(db, guest.id, "create_session", idempotency_key, req.model_dump(mode="json"), 202, res_data)
    return res_data


@app.get("/api/v1/learning-sessions/active")
def get_active_session_for_guest(
    guest: GuestOwner = Depends(get_current_guest),
    db: Session = Depends(get_db),
):
    """Resumes the latest active session for the authenticated guest on page reload."""
    latest_sess = (
        db.query(LearningSession)
        .filter(LearningSession.owner_id == guest.id)
        .order_by(LearningSession.created_at.desc())
        .first()
    )
    if not latest_sess:
        return {"active_session_id": None}
    return {"active_session_id": latest_sess.id}


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

    evidence = db.query(ConceptEvidence).filter(ConceptEvidence.session_id == session_id).order_by(ConceptEvidence.created_at).all()
    ev_summary = {e.concept_id: EvidenceCategory(e.category) for e in evidence}

    latest_run = db.query(ExperimentRun).filter(ExperimentRun.session_id == session_id).order_by(ExperimentRun.started_at.desc()).first()
    latest_step = latest_tutor_step(db, session_id)

    selection = db.query(SourceSelection).filter(
        SourceSelection.id == session.selection_id,
        SourceSelection.owner_id == guest.id,
    ).first()
    source_selection = None
    if selection:
        selected_anchors = db.query(DBSourceAnchor).filter(
            DBSourceAnchor.document_id == selection.document_id,
            DBSourceAnchor.page_number.between(selection.page_start, selection.page_end),
        ).order_by(DBSourceAnchor.page_number, DBSourceAnchor.start_offset).all()
        source_selection = SourceSelectionResponse(
            selection_id=selection.id,
            document_id=selection.document_id,
            page_start=selection.page_start,
            page_end=selection.page_end,
            question=selection.question,
            anchors=[SourceAnchorContract(
                id=a.id, document_id=a.document_id, page_number=a.page_number,
                start_offset=a.start_offset, end_offset=a.end_offset,
                quote=a.quote, text_hash=a.text_hash,
            ) for a in selected_anchors],
            content_hash=selection.content_hash,
            topic_assessment=selection.topic_assessment,
        )

    return SessionStateResponse(
        session_id=session.id,
        revision=session.revision,
        active_concept=session.active_concept,
        active_job_id=session.active_job_id,
        board=scene,
        evidence_summary=ev_summary,
        active_task=latest_step.get("active_task"),
        latest_run_id=latest_run.id if latest_run else None,
        source_selection=source_selection,
        tutor_narration=latest_step.get("narration"),
        tutor_steps=latest_step.get("steps") or paginate_text(latest_step.get("narration") or ""),
        tutor_turn=latest_step.get("turn"),
        web_sources=latest_step.get("web_sources") or [],
        lesson_kind=lesson_kind_for(selection),
    )


@app.post("/api/v1/learning-sessions/{session_id}/events", status_code=status.HTTP_202_ACCEPTED, response_model=SubmitLearnerEventResponse)
def submit_learner_event(
    session_id: str,
    req: SubmitLearnerEventRequest,
    request: Request,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    guest: GuestOwner = Depends(get_current_guest),
    db: Session = Depends(get_db),
):
    verify_csrf(request, request.headers.get("X-CSRF-Token"), guest)

    session = db.query(LearningSession).filter(LearningSession.id == session_id, LearningSession.owner_id == guest.id).first()
    if not session:
        raise HTTPException(status_code=404, detail={"code": "RESOURCE_NOT_FOUND", "message": "Session not found"})

    cached = handle_idempotency(db, guest.id, f"event_{session_id}", idempotency_key, req.model_dump(mode="json"))
    if cached:
        return cached[1]

    # Check for active running job mutex (409 SESSION_BUSY)
    if session_is_busy(db, session):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "SESSION_BUSY", "message": "A mutation job is currently executing on this session"},
        )

    if req.expected_revision != session.revision:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "REVISION_CONFLICT",
                "message": f"Expected revision {req.expected_revision} does not match current revision {session.revision}",
                "details": {"current_revision": session.revision},
            },
        )

    active_task = latest_tutor_step(db, session_id).get("active_task")
    if req.event_type in ("prediction_submitted", "explanation_submitted", "connection_submitted", "hint_requested"):
        if not active_task or any(req.payload.get(key) != active_task.get(key) for key in ("task_id", "task_variant")):
            raise HTTPException(status_code=422, detail={"code": "TASK_STALE", "message": "This task has changed. Refresh the lesson before answering."})

    payload = dict(req.payload)
    # Attribution is server state. Clients cannot move help to another task or
    # erase it by declaring hints_used=0 on their later answer.
    payload.pop("assistance_task", None)
    payload.pop("assistance_delivered", None)
    if active_task and req.event_type in ("hint_requested", "message_submitted", "object_question_submitted"):
        task_def = TASK_REGISTRY.get((active_task.get("task_id"), active_task.get("task_variant")))
        payload["assistance_task"] = {
            "task_id": active_task.get("task_id"),
            "task_variant": active_task.get("task_variant"),
            "concept_id": task_def.concept_id if task_def else session.active_concept,
        }
        payload["assistance_delivered"] = False

    job_id = str(uuid.uuid4())
    event_count = db.query(LearnerEvent).filter(LearnerEvent.session_id == session_id).count()

    event = LearnerEvent(
        id=req.event_id,
        owner_id=guest.id,
        session_id=session_id,
        client_event_id=req.event_id,
        event_type=req.event_type,
        payload_json=json.dumps(payload),
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
        lease_expires_at=datetime.now(timezone.utc) + TUTOR_TURN_LEASE,
    )
    db.add(tutor_job)
    session.active_job_id = job_id
    db.commit()

    # Execute tutor response turn
    execute_tutor_job(db, session, tutor_job, req.event_id)
    if "assistance_task" in payload:
        payload["assistance_delivered"] = True
        event.payload_json = json.dumps(payload)
        db.commit()

    res_data = {
        "event_id": req.event_id,
        "current_revision": session.revision,
        "tutor_job_id": job_id,
    }
    record_idempotency(db, guest.id, f"event_{session_id}", idempotency_key, req.model_dump(mode="json"), 202, res_data)
    return res_data


# --- Experiments ---
@app.post("/api/v1/learning-sessions/{session_id}/runs", status_code=status.HTTP_202_ACCEPTED)
def execute_session_run(
    session_id: str,
    req_body: Dict[str, Any],
    request: Request,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    guest: GuestOwner = Depends(get_current_guest),
    db: Session = Depends(get_db),
):
    verify_csrf(request, request.headers.get("X-CSRF-Token"), guest)

    session = db.query(LearningSession).filter(LearningSession.id == session_id, LearningSession.owner_id == guest.id).first()
    if not session:
        raise HTTPException(status_code=404, detail={"code": "RESOURCE_NOT_FOUND", "message": "Session not found"})

    recipe_id = req_body.get("recipe_id")
    parameters = req_body.get("parameters", {})
    if not recipe_id:
        raise HTTPException(status_code=422, detail={"code": "PARAMETERS_INVALID", "message": "recipe_id is required"})

    cached = handle_idempotency(db, guest.id, f"run_{session_id}", idempotency_key, req_body)
    if cached:
        return cached[1]

    if session_is_busy(db, session):
        raise HTTPException(status_code=409, detail={"code": "SESSION_BUSY", "message": "Wait for the current lesson update before running an experiment."})
    if "expected_revision" in req_body and req_body["expected_revision"] != session.revision:
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT", "message": "The lesson changed. Refresh before running an experiment."})

    if recipe_id == RecipeId.SANDBOX_PYTHON.value:
        # Learners change only the knobs a retained tutor experiment declared; code never comes from the client.
        base = db.query(ExperimentRun).filter(
            ExperimentRun.id == str(req_body.get("base_run_id") or ""),
            ExperimentRun.session_id == session_id,
            ExperimentRun.owner_id == guest.id,
            ExperimentRun.recipe_id == recipe_id,
        ).first()
        if not base:
            raise HTTPException(status_code=404, detail={"code": "RESOURCE_NOT_FOUND", "message": "Experiment not found"})
        spec = {key: value for key, value in json.loads(base.parameters_json).items() if key != "values"}
        try:
            run_res = execute_sandbox_experiment(spec, parameters if isinstance(parameters, dict) else {})
        except SandboxSpecError as e:
            raise HTTPException(status_code=422, detail={"code": "PARAMETERS_INVALID", "message": str(e)})
    else:
        try:
            run_res = runner.run(recipe_id, parameters)
        except Exception as e:
            raise HTTPException(status_code=422, detail={"code": "PARAMETERS_INVALID", "message": str(e)})

    job_id = str(uuid.uuid4())
    db.add(experiment_run_record(run_res, guest.id, session_id, job_id))
    db.add(Job(
        id=job_id, owner_id=guest.id, session_id=session_id,
        kind=JobKind.RUN_EXPERIMENT.value,
        status=JobStatus.SUCCEEDED.value if run_res.status == "succeeded" else JobStatus.FAILED.value,
        progress=1.0,
    ))
    db.commit()

    res_data = {
        "run_id": run_res.run_id,
        "current_revision": session.revision,
        "job_id": job_id,
    }
    record_idempotency(db, guest.id, f"run_{session_id}", idempotency_key, req_body, 202, res_data)
    return res_data


@app.get("/api/v1/runs/{run_id}", response_model=ExperimentRunResponse)
def get_run(
    run_id: str,
    guest: GuestOwner = Depends(get_current_guest),
    db: Session = Depends(get_db),
):
    run = db.query(ExperimentRun).filter(ExperimentRun.id == run_id, ExperimentRun.owner_id == guest.id).first()
    if not run:
        raise HTTPException(status_code=404, detail={"code": "RESOURCE_NOT_FOUND", "message": "Run not found"})

    stored_evidence = json.loads(run.checks_json)
    # Older records retained checks only; never invent their execution metadata.
    metadata = stored_evidence if isinstance(stored_evidence, dict) else {}
    checks = metadata.get("checks", []) if metadata else stored_evidence
    checks = [json.loads(c) if isinstance(c, str) else c for c in checks]
    return ExperimentRunResponse(
        run_id=run.id,
        recipe_id=run.recipe_id,
        parameters=json.loads(run.parameters_json),
        parameter_hash=run.parameter_hash,
        seed=run.seed,
        status=run.status,
        output=json.loads(run.output_json) if run.output_json else None,
        checks=checks,
        assumptions=metadata.get("assumptions", []),
        runner_digest=metadata.get("runner_digest", "not recorded"),
        numpy_version=metadata.get("numpy_version", "not recorded"),
        started_at=run.started_at.isoformat(),
        completed_at=run.completed_at.isoformat() if run.completed_at else None,
    )


# --- Jobs, SSE Events, and Cooperative Cancellation ---
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


@app.get("/api/v1/jobs/{job_id}/events")
async def stream_job_events(
    job_id: str,
    after: Optional[int] = None,
    guest: GuestOwner = Depends(get_current_guest),
    db: Session = Depends(get_db),
):
    """Server-Sent Events (SSE) endpoint streaming job events."""
    job = db.query(Job).filter(Job.id == job_id, Job.owner_id == guest.id).first()
    if not job:
        raise HTTPException(status_code=404, detail={"code": "RESOURCE_NOT_FOUND", "message": "Job not found"})

    async def event_generator():
        last_seq = after or 0
        while True:
            # Query new events
            events = (
                db.query(JobEvent)
                .filter(JobEvent.job_id == job_id, JobEvent.sequence > last_seq, JobEvent.event_type != TASK_KEY_EVENT)
                .order_by(JobEvent.sequence.asc())
                .all()
            )
            for ev in events:
                last_seq = ev.sequence
                yield f"id: {ev.sequence}\nevent: {ev.event_type}\ndata: {ev.payload_json}\n\n"

            # Check if job reached terminal status
            db.refresh(job)
            if job.status in (JobStatus.SUCCEEDED.value, JobStatus.FAILED.value, JobStatus.CANCELLED.value, JobStatus.TIMED_OUT.value):
                yield f"event: job_finished\ndata: {{\"status\": \"{job.status}\"}}\n\n"
                break

            await asyncio.sleep(0.5)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.post("/api/v1/jobs/{job_id}/cancel", status_code=status.HTTP_202_ACCEPTED)
def cancel_job(
    job_id: str,
    request: Request,
    guest: GuestOwner = Depends(get_current_guest),
    db: Session = Depends(get_db),
):
    verify_csrf(request, request.headers.get("X-CSRF-Token"), guest)

    job = db.query(Job).filter(Job.id == job_id, Job.owner_id == guest.id).first()
    if not job:
        raise HTTPException(status_code=404, detail={"code": "RESOURCE_NOT_FOUND", "message": "Job not found"})

    if job.status in [JobStatus.SUCCEEDED.value, JobStatus.FAILED.value, JobStatus.CANCELLED.value, JobStatus.TIMED_OUT.value]:
        return {"job_id": job.id, "status": job.status, "message": "Job is already terminal"}

    job.cancelled = True
    job.status = JobStatus.CANCELLED.value

    # Atomically advance session fence and clear active job slot
    if job.session_id:
        sess = db.query(LearningSession).filter(LearningSession.id == job.session_id).first()
        if sess and sess.active_job_id == job.id:
            sess.active_job_id = None
            sess.fencing_generation += 1

    db.commit()
    return {"job_id": job.id, "status": "cancelled", "message": "Cancellation accepted"}


# --- Static Assets & Frontend Mounting ---
examples_dir = Path(__file__).resolve().parent.parent.parent.parent / "examples"
if examples_dir.exists():
    app.mount("/examples", StaticFiles(directory=str(examples_dir)), name="examples")

frontend_dist = Path(__file__).resolve().parent.parent.parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")
