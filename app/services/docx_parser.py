import io
from typing import Optional

from docx import Document


async def parse_docx(file_content: bytes) -> Optional[str]:
    """
    Extract text from a DOCX file using python-docx.
    """
    try:
        doc = Document(io.BytesIO(file_content))
        text = []
        for paragraph in doc.paragraphs:
            text.append(paragraph.text)
        return "\n".join(text).strip()
    except Exception as e:
        print(f"Error parsing DOCX: {str(e)}")
        return None