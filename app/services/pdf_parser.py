import io
from typing import Optional

import fitz  


async def parse_pdf(file_content: bytes) -> Optional[str]:
    """
    Extract text from a PDF file using PyMuPDF.
    """
    try:
        with fitz.open(stream=file_content, filetype="pdf") as pdf:
            text = ""
            for page in pdf:
                text += page.get_text()
            return text.strip()
    except Exception as e:
        print(f"Error parsing PDF: {str(e)}")
        return None