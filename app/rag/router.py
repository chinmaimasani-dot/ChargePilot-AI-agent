
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from app.rag.service import KNOWLEDGE_BASE, generate_answer

router = APIRouter(
    prefix="/api/v1/rag",
    tags=["RAG Information Agent"],
)

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}
MAX_FILE_SIZE = 10 * 1024 * 1024


class RAGQuestion(BaseModel):
    question: str = Field(min_length=3, max_length=1000)


@router.post("/documents")
async def upload_document(file: UploadFile = File(...)):
    filename = Path(file.filename or "").name
    extension = Path(filename).suffix.lower()

    if not filename or extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Only PDF, DOCX and TXT files are supported.",
        )

    content = await file.read()

    if not content:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is empty.",
        )

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="Maximum file size is 10 MB.",
        )

    KNOWLEDGE_BASE.mkdir(parents=True, exist_ok=True)

    destination = KNOWLEDGE_BASE / filename
    destination.write_bytes(content)

    return {
        "message": "Document uploaded successfully.",
        "filename": filename,
        "size_bytes": len(content),
    }


@router.post("/ask")
def ask_question(payload: RAGQuestion):
    try:
        return generate_answer(payload.question)

    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    except Exception:
        raise HTTPException(
            status_code=502,
            detail="The RAG service could not generate an answer. Check Groq configuration and connectivity.",
        )
