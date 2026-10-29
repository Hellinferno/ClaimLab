"""Common types, enums, and base models for ClaimLab contracts."""
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, Field
import uuid


class ErrorCode(str, Enum):
    INVALID_REQUEST = "INVALID_REQUEST"
    INVALID_CSRF = "INVALID_CSRF"
    ORIGIN_REJECTED = "ORIGIN_REJECTED"
    GUEST_REQUIRED = "GUEST_REQUIRED"
    GUEST_EXPIRED = "GUEST_EXPIRED"
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    REVISION_CONFLICT = "REVISION_CONFLICT"
    SESSION_BUSY = "SESSION_BUSY"
    IDEMPOTENCY_CONFLICT = "IDEMPOTENCY_CONFLICT"
    UPLOAD_TOO_LARGE = "UPLOAD_TOO_LARGE"
    OUTPUT_TOO_LARGE = "OUTPUT_TOO_LARGE"
    UNSUPPORTED_DOCUMENT = "UNSUPPORTED_DOCUMENT"
    SOURCE_UNREADABLE = "SOURCE_UNREADABLE"
    PARAMETERS_INVALID = "PARAMETERS_INVALID"
    TASK_STALE = "TASK_STALE"
    WORKER_LOST = "WORKER_LOST"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    SERVICE_NOT_READY = "SERVICE_NOT_READY"


class ErrorDetail(BaseModel):
    code: ErrorCode
    message: str
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    retryable: bool = False
    details: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    error: ErrorDetail


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class JobKind(str, Enum):
    PARSE_DOCUMENT = "parse_document"
    TUTOR_TURN = "tutor_turn"
    RUN_EXPERIMENT = "run_experiment"


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"


class EvidenceCategory(str, Enum):
    NOT_ASSESSED = "not_assessed"
    INTRODUCED = "introduced"
    NEEDS_CHECK = "needs_check"
    SUPPORTED_WITH_HELP = "supported_with_help"
    SUPPORTED_INDEPENDENTLY = "supported_independently"
    NEEDS_REVISIT = "needs_revisit"


class AssessmentStatus(str, Enum):
    CHECKED = "checked"
    PROVISIONAL = "provisional"
    UNCERTAIN = "uncertain"


class AssistanceLevel(str, Enum):
    NONE = "none"
    HINT_GIVEN = "hint_given"
    SOLUTION_EXPOSED = "solution_exposed"
