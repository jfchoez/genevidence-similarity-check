from fastapi import APIRouter, Depends, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.db import get_db
from app.models import SimilarityReport, User
from app.schemas import ReportOut
from app.services.pdf_report import PDFReportBuilder
from app.services.reporting import ReportGenerator, build_report_response, can_view_report


router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("/{document_id}/generate", response_model=ReportOut)
def generate_report(
    document_id: int,
    exclude_references: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReportOut:
    report = ReportGenerator(db).generate(document_id, current_user, exclude_references=exclude_references)
    return build_report_response(db, report, current_user)


@router.get("/{report_id}", response_model=ReportOut)
def get_report(
    report_id: int,
    source: str | None = Query(None),
    section: str | None = Query(None),
    match_type: str | None = Query(None),
    min_score: float | None = Query(None, ge=0, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReportOut:
    report = db.get(SimilarityReport, report_id)
    if not report or not can_view_report(current_user, report):
        from fastapi import HTTPException, status

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    return build_report_response(db, report, current_user, source, section, match_type, min_score)


@router.get("/{report_id}/pdf")
def get_report_pdf(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FileResponse:
    report = db.get(SimilarityReport, report_id)
    if not report or not can_view_report(current_user, report):
        from fastapi import HTTPException, status

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    path = PDFReportBuilder(db).build(report, current_user)
    return FileResponse(path, filename=f"genevidence_report_{report_id}.pdf", media_type="application/pdf")
