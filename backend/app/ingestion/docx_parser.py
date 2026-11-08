import io
from typing import List
import docx
from app.core.exceptions import ValidationError


class ParsedBlock:
    def __init__(self, text: str, page_number: int = 1, location: str = ""):
        self.text = text
        self.page_number = page_number
        self.location = location


def parse_docx(content: bytes) -> List[ParsedBlock]:
    """
    Extract structured paragraphs, headings, and table cells from DOCX bytes.
    Preserves document reading order and heading context.
    """
    try:
        doc = docx.Document(io.BytesIO(content))
    except Exception as e:
        raise ValidationError(f"Failed to open DOCX archive: {str(e)}")

    blocks: List[ParsedBlock] = []
    current_heading = "General"

    for element in doc.element.body:
        # Check if element is a paragraph
        if element.tag.endswith("p"):
            p = docx.text.paragraph.Paragraph(element, doc)
            text = p.text.strip()
            if not text:
                continue

            style_name = p.style.name.lower() if p.style and p.style.name else ""
            if "heading" in style_name:
                current_heading = text

            blocks.append(ParsedBlock(
                text=text,
                page_number=1,
                location=f"Section: {current_heading}"
            ))

        # Check if element is a table
        elif element.tag.endswith("tbl"):
            tbl = docx.table.Table(element, doc)
            table_rows = []
            for row in tbl.rows:
                row_cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if row_cells:
                    table_rows.append(" | ".join(row_cells))
            if table_rows:
                blocks.append(ParsedBlock(
                    text="\n".join(table_rows),
                    page_number=1,
                    location=f"Table under: {current_heading}"
                ))

    return blocks

