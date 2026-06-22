from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.db import get_db
from app.models import User
from app.schemas import BillingCreditsOut
from app.services.billing import get_credit_balance, get_user_plan_code


router = APIRouter(prefix="/billing", tags=["billing"])


@router.get("/credits", response_model=BillingCreditsOut)
def get_credits(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BillingCreditsOut:
    return BillingCreditsOut(
        user_id=current_user.id,
        available_credits=get_credit_balance(db, current_user.id),
        plan=get_user_plan_code(db, current_user.id),
    )
