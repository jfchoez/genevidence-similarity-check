from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import CreditTransaction, Plan, Subscription, User


DEFAULT_PLANS = [
    {"code": "free", "name": "Free", "monthly_credits": settings.FREE_PLAN_CREDITS},
    {"code": "professional", "name": "Professional", "monthly_credits": 50},
    {"code": "institutional", "name": "Institutional", "monthly_credits": 500},
]


def seed_default_plans(db: Session) -> None:
    for plan_data in DEFAULT_PLANS:
        plan = db.query(Plan).filter(Plan.code == plan_data["code"]).first()
        if not plan:
            db.add(Plan(**plan_data))
    db.commit()


def ensure_free_subscription(db: Session, user: User) -> None:
    seed_default_plans(db)
    free_plan = db.query(Plan).filter(Plan.code == "free").one()
    existing = db.query(Subscription).filter(Subscription.user_id == user.id).first()
    if not existing:
        db.add(Subscription(user_id=user.id, plan_id=free_plan.id))
    if get_credit_balance(db, user.id) == 0 and settings.FREE_PLAN_CREDITS > 0:
        db.add(
            CreditTransaction(
                user_id=user.id,
                amount=settings.FREE_PLAN_CREDITS,
                reason="initial_free_plan_credits",
            )
        )
    db.commit()


def get_credit_balance(db: Session, user_id: int) -> int:
    value = (
        db.query(func.coalesce(func.sum(CreditTransaction.amount), 0))
        .filter(CreditTransaction.user_id == user_id)
        .scalar()
    )
    return int(value or 0)


def get_user_plan_code(db: Session, user_id: int) -> str:
    subscription = (
        db.query(Subscription)
        .join(Plan, Plan.id == Subscription.plan_id)
        .filter(Subscription.user_id == user_id, Subscription.status == "active")
        .order_by(Subscription.id.desc())
        .first()
    )
    return subscription.plan.code if subscription else "free"


def deduct_report_credit(db: Session, user_id: int, report_id: int) -> None:
    db.add(
        CreditTransaction(
            user_id=user_id,
            amount=-1,
            reason="similarity_report_generated",
            report_id=report_id,
        )
    )


def grant_credits(db: Session, user_id: int, amount: int, reason: str, admin_id: int) -> CreditTransaction:
    transaction = CreditTransaction(
        user_id=user_id,
        amount=amount,
        reason=reason,
        created_by_id=admin_id,
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction
