"""PDF extraction and source anchor generation service."""
import hashlib
import io
import re
from typing import List, Tuple
from pypdf import PdfReader

from claimlab.contracts.document import PageExtractionStatus, SourceAnchor

MAX_PDF_BYTES = 10 * 1024 * 1024  # 10 MiB
MAX_PAGES = 50
MAX_DOC_CHARS = 500_000
MAX_PAGE_CHARS = 50_000


def normalize_text(text: str) -> str:
    """Normalize whitespace and control characters."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Collapse consecutive spaces but preserve paragraphs
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]
    return "\n".join(lines).strip()


class PDFExtractionResult:
    def __init__(self, page_count: int, pages: List[Tuple[int, str, PageExtractionStatus, List[str]]], warnings: List[str]):
        self.page_count = page_count
        self.pages = pages  # list of (page_num, normalized_text, status, warnings)
        self.warnings = warnings


def extract_pdf_content(file_bytes: bytes) -> PDFExtractionResult:
    """Extracts text per-page from raw PDF bytes."""
    if len(file_bytes) > MAX_PDF_BYTES:
        raise ValueError("Upload exceeds maximum size of 10 MiB")

    reader = PdfReader(io.BytesIO(file_bytes))
    page_count = len(reader.pages)

    if page_count == 0:
        raise ValueError("PDF contains no pages")
    if page_count > MAX_PAGES:
        raise ValueError(f"PDF exceeds maximum page limit of {MAX_PAGES} (found {page_count})")

    extracted_pages: List[Tuple[int, str, PageExtractionStatus, List[str]]] = []
    doc_warnings: List[str] = []
    total_chars = 0

    for idx, page in enumerate(reader.pages, start=1):
        page_warnings: List[str] = []
        try:
            raw_text = page.extract_text() or ""
        except Exception as e:
            raw_text = ""
            page_warnings.append(f"Text extraction failed: {str(e)}")

        norm_text = normalize_text(raw_text)
        char_count = len(norm_text)
        total_chars += char_count

        if char_count == 0:
            status = PageExtractionStatus.SCANNED_ONLY
            page_warnings.append("Page has no native text (scanned or image-only)")
        elif char_count > MAX_PAGE_CHARS:
            status = PageExtractionStatus.COMPLETED
            norm_text = norm_text[:MAX_PAGE_CHARS]
            page_warnings.append(f"Page text truncated to {MAX_PAGE_CHARS} characters")
        else:
            status = PageExtractionStatus.COMPLETED

        extracted_pages.append((idx, norm_text, status, page_warnings))

    if total_chars > MAX_DOC_CHARS:
        doc_warnings.append(f"Total document text exceeds {MAX_DOC_CHARS} chars")

    return PDFExtractionResult(page_count, extracted_pages, doc_warnings)


def create_anchors_for_text(doc_id: str, page_number: int, text: str) -> List[SourceAnchor]:
    """Generates sentence/paragraph level source anchors with exact offsets and hashes."""
    anchors: List[SourceAnchor] = []
    paragraphs = [p for p in text.split("\n\n") if p.strip()]

    current_offset = 0
    anchor_idx = 1
    for p in paragraphs:
        start = text.find(p, current_offset)
        if start == -1:
            start = current_offset
        end = start + len(p)
        current_offset = end

        anchor_id = f"anc-{doc_id[:8]}-p{page_number}-{anchor_idx}"
        text_hash = hashlib.sha256(p.encode("utf-8")).hexdigest()

        anchors.append(
            SourceAnchor(
                id=anchor_id,
                document_id=doc_id,
                page_number=page_number,
                start_offset=start,
                end_offset=end,
                quote=p,
                text_hash=text_hash,
            )
        )
        anchor_idx += 1

    return anchors
