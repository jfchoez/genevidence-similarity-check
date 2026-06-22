from __future__ import annotations

import re
import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.config import settings
from app.core.db import get_db
from app.models import Document, User
from app.schemas import DocumentDetail, DocumentOut
from app.services.indexing import process_document_task
from app.services.reporting import assert_document_access


router = APIRouter(prefix="/documents", tags=["documents"])


ALLOWED_FILE_TYPES = {"pdf", "docx"}


@router.post("/upload", response_model=DocumentOut)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Document:
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing filename")
    file_type = Path(file.filename).suffix.lower().lstrip(".")
    if file_type not in ALLOWED_FILE_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF and DOCX files are supported")

    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    content = await file.read()
    if len(content) > max_bytes:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File is too large")

    safe_stem = re.sub(r"[^a-zA-Z0-9_.-]+", "_", Path(file.filename).stem).strip("._") or "document"
    filename = f"{uuid.uuid4().hex}_{safe_stem}.{file_type}"
    storage_dir = Path(settings.STORAGE_DIR) / "documents" / str(current_user.id)
    storage_dir.mkdir(parents=True, exist_ok=True)
    storage_path = storage_dir / filename
    storage_path.write_bytes(content)

    document = Document(
        owner_id=current_user.id,
        title=Path(file.filename).stem,
        original_filename=file.filename,
        file_type=file_type,
        storage_path=str(storage_path),
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    background_tasks.add_task(process_document_task, document.id)
    return document


@router.get("", response_model=list[DocumentOut])
def list_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Document]:
    query = db.query(Document).order_by(Document.created_at.desc())
    if current_user.role != "admin":
        query = query.filter(Document.owner_id == current_user.id)
    return query.all()


@router.get("/{document_id}", response_model=DocumentDetail)
def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentDetail:
    document = assert_document_access(current_user, db.get(Document, document_id))
    return DocumentDetail(
        id=document.id,
        title=document.title,
        original_filename=document.original_filename,
        file_type=document.file_type,
        status=document.status,
        word_count=document.word_count,
        created_at=document.created_at,
        error_message=document.error_message,
        sections=[
            {
                "id": section.id,
                "section_name": section.section_name,
                "start_position": section.start_position,
                "end_position": section.end_position,
            }
            for section in document.sections
        ],
        reports=[
            {
                "id": report.id,
                "status": report.status,
                "global_similarity_score": report.global_similarity_score,
                "created_at": report.created_at.isoformat(),
            }
            for report in sorted(document.reports, key=lambda item: item.created_at, reverse=True)
            if current_user.role == "admin" or report.owner_id == current_user.id
        ],
    )
