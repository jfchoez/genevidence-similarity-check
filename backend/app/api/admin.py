from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.dependencies import require_admin
from app.core.db import get_db
from app.models import CreditTransaction, Document, SimilarityReport, User
from app.schemas import AdminCreditGrant, AdminStatsOut, DocumentOut, ReportOut, UserOut
from app.services.billing import grant_credits
from app.services.reporting import build_report_response


router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats", response_model=AdminStatsOut)
def admin_stats(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> AdminStatsOut:
    consumed = (
        db.query(func.coalesce(func.sum(CreditTransaction.amount), 0))
        .filter(CreditTransaction.amount < 0)
        .scalar()
    )
    return AdminStatsOut(
        total_users=db.query(User).count(),
        total_documents=db.query(Document).count(),
        total_reports=db.query(SimilarityReport).count(),
        total_credit_consumed=abs(int(consumed or 0)),
    )


@router.get("/users", response_model=list[UserOut])
def admin_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> list[User]:
    return db.query(User).order_by(User.created_at.desc()).all()


@router.post("/users/{user_id}/credits")
def admin_grant_credits(
    user_id: int,
    payload: AdminCreditGrant,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> dict:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    transaction = grant_credits(db, user.id, payload.amount, payload.reason, admin.id)
    return {"transaction_id": transaction.id, "user_id": user.id, "amount": transaction.amount}


@router.get("/reports", response_model=list[ReportOut])
def admin_reports(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> list[ReportOut]:
    reports = db.query(SimilarityReport).order_by(SimilarityReport.created_at.desc()).limit(100).all()
    return [build_report_response(db, report, admin) for report in reports]


@router.get("/documents", response_model=list[DocumentOut])
def admin_documents(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> list[Document]:
    return db.query(Document).order_by(Document.created_at.desc()).limit(200).all()
