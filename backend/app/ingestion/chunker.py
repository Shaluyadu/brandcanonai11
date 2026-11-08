"""
Paragraph-aware text chunker for brand knowledge documents.

Each chunk retains its source page number, source location (heading path),
and a SHA-256 content hash for deduplication.
"""
import hashlib
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ChunkResult:
    content: str
    chunk_index: int
    source_page: Optional[int]
    source_location: Optional[str]
    content_hash: str
    metadata: dict = field(default_factory=dict)


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def chunk_text(
    blocks: List[dict],
    chunk_size: int = 800,
    overlap: int = 100,
) -> List[ChunkResult]:
    """
    Split normalised document blocks into overlapping text chunks.

    Each `block` dict must have:
        - ``text`` (str): paragraph text
        - ``page`` (int | None): source page number
        - ``location`` (str | None): heading breadcrumb or section label

    Rules:
    - Never split in the middle of a paragraph — accumulate full paragraphs.
    - When accumulated text exceeds `chunk_size` characters, flush and begin
      the next chunk with an `overlap`-character tail of the flushed content.
    - Preserve the page and location of the first block in each chunk.
    - Return deterministic `ChunkResult` objects with SHA-256 hashes.
    """
    chunks: List[ChunkResult] = []
    current_text: str = ""
    current_page: Optional[int] = None
    current_location: Optional[str] = None

    def flush(text: str, page: Optional[int], location: Optional[str], index: int) -> ChunkResult:
        stripped = text.strip()
        return ChunkResult(
            content=stripped,
            chunk_index=index,
            source_page=page,
            source_location=location,
            content_hash=_sha256(stripped),
        )

    for block in blocks:
        para = block.get("text", "").strip()
        page = block.get("page")
        location = block.get("location")

        if not para:
            continue

        # Initialise anchor for new chunk
        if not current_text:
            current_page = page
            current_location = location

        # If page number changes, flush previous page content to preserve strict page citations
        if current_text and page is not None and current_page is not None and page != current_page:
            chunks.append(flush(current_text, current_page, current_location, len(chunks)))
            current_text = para
            current_page = page
            current_location = location
            continue

        # Try adding this paragraph
        separator = "\n\n" if current_text else ""
        candidate = current_text + separator + para

        if len(candidate) <= chunk_size:
            current_text = candidate
        else:
            # Flush current content if non-empty
            if current_text.strip():
                chunks.append(flush(current_text, current_page, current_location, len(chunks)))
                # Start next chunk with overlap tail
                tail = current_text[-overlap:] if len(current_text) > overlap else current_text
                current_text = tail.strip() + "\n\n" + para
                current_page = page
                current_location = location
            else:
                # Single paragraph exceeds chunk_size — split it by words
                words = para.split()
                word_buf: List[str] = []
                for word in words:
                    trial = " ".join(word_buf + [word])
                    if len(trial) <= chunk_size:
                        word_buf.append(word)
                    else:
                        if word_buf:
                            seg = " ".join(word_buf)
                            chunks.append(flush(seg, page, location, len(chunks)))
                            # overlap from end of segment
                            overlap_words = word_buf[-(overlap // 6):]  # ~6 chars per word avg
                            word_buf = overlap_words + [word]
                        else:
                            # Single word longer than chunk_size (unlikely)
                            chunks.append(flush(word, page, location, len(chunks)))
                            word_buf = []
                if word_buf:
                    current_text = " ".join(word_buf)
                    current_page = page
                    current_location = location
                else:
                    current_text = ""

    # Flush remaining text
    if current_text.strip():
        chunks.append(flush(current_text, current_page, current_location, len(chunks)))

    return chunks

