from typing import List, Tuple
import pymupdf
from app.core.exceptions import ValidationError

class ScannedDocumentError(Exception):
    """Raised when PDF has valid structure but contains zero extractable text (e.g. image-only scan)."""
    pass


class PDFParsedPage:
    def __init__(self, page_number: int, text: str):
        self.page_number = page_number
        self.text = text


def parse_pdf(content: bytes) -> Tuple[List[PDFParsedPage], int]:
    """
    Extract page-wise text from PDF bytes using PyMuPDF.
    Returns (pages, total_pages).
    Raises ScannedDocumentError if document contains no extractable text.
    """
    try:
        doc = pymupdf.open(stream=content, filetype="pdf")
    except Exception as e:
        raise ValidationError(f"Failed to parse PDF document structure: {str(e)}")

    total_pages = doc.page_count
    if total_pages == 0:
        raise ValidationError("PDF document contains 0 pages")

    pages: List[PDFParsedPage] = []
    total_text_length = 0

    for idx in range(total_pages):
        page = doc.load_page(idx)
        # Extract text using PyMuPDF standard layout extraction
        page_text = page.get_text("text").strip()
        pages.append(PDFParsedPage(page_number=idx + 1, text=page_text))
        total_text_length += len(page_text)

    doc.close()

    # Detect scanned documents without OCR
    if total_text_length == 0:
        raise ScannedDocumentError(
            "PDF contains no extractable digital text. Document appears to be a scanned image without embedded OCR."
        )

    return pages, total_pages

