"""Contracts for document upload, extraction, and source selection."""
from enum import Enum
from typing import List
from pydantic import Field
from claimlab.contracts.common import StrictModel


class PageExtractionStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SCANNED_ONLY = "scanned_only"


class DocumentPageMeta(StrictModel):
    page_number: int = Field(..., ge=1)
    char_count: int = Field(..., ge=0)
    extraction_status: PageExtractionStatus
    warnings: List[str] = Field(default_factory=list)


class DocumentStatusResponse(StrictModel):
    document_id: str
    filename: str
    page_count: int
    status: PageExtractionStatus
    pages: List[DocumentPageMeta] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class SourceAnchor(StrictModel):
    id: str
    document_id: str
    page_number: int
    start_offset: int
    end_offset: int
    quote: str
    text_hash: str


class CreateSelectionRequest(StrictModel):
    page_start: int = Field(..., ge=1, le=50)
    page_end: int = Field(..., ge=1, le=50)
    question: str = Field(..., min_length=3, max_length=1000)


class SourceSelectionResponse(StrictModel):
    selection_id: str
    document_id: str
    page_start: int
    page_end: int
    question: str
    anchors: List[SourceAnchor] = Field(default_factory=list)
    content_hash: str
    topic_assessment: str
