from typing import Optional, Tuple

from fastapi import HTTPException, UploadFile

from app.services.pdf_parser import parse_pdf
from app.services.docx_parser import parse_docx


async def get_file_type(filename: str) -> str:
    """
    Determine file type from filename.
    """
    if filename.lower().endswith(".pdf"):
        return "pdf"
    elif filename.lower().endswith(".docx"):
        return "docx"
    else:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Only PDF and DOCX files are supported."
        )


async def parse_contract_text(file: UploadFile) -> Tuple[str, str]:
    """
    Parse contract text from an uploaded file.
    Returns a tuple of (file_type, extracted_text)
    """

    file_type = await get_file_type(file.filename)

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")

    if file_type == "pdf":
        text = await parse_pdf(content)
    elif file_type == "docx":
        text = await parse_docx(content)
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type")
    
    if text is None or text == "":
        raise HTTPException(status_code=422, detail="Could not extract text from file")

    await file.seek(0)
    
    return file_type, text