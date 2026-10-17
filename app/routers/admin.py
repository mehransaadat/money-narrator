from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..dependencies import get_current_admin

# Every route here requires an admin token (see get_current_admin).
router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(get_current_admin)])


@router.get("/stats", response_model=schemas.AdminStats)
def admin_stats(db: Session = Depends(get_db)):
    """Site-wide totals for the admin dashboard."""
    zero = 0
    total_income = (
        db.query(func.coalesce(func.sum(models.Transaction.amount), zero))
        .filter(models.Transaction.type == "income")
        .scalar()
    )
    total_expense = (
        db.query(func.coalesce(func.sum(models.Transaction.amount), zero))
        .filter(models.Transaction.type != "income")
        .scalar()
    )
    top = (
        db.query(models.Transaction.category, func.sum(models.Transaction.amount).label("t"))
        .filter(models.Transaction.type != "income")
        .group_by(models.Transaction.category)
        .order_by(func.sum(models.Transaction.amount).desc())
        .limit(8)
        .all()
    )
    return schemas.AdminStats(
        total_users=db.query(models.User).count(),
        total_admins=db.query(models.User).filter(models.User.is_admin.is_(True)).count(),
        total_transactions=db.query(models.Transaction).count(),
        total_income=total_income,
        total_expense=total_expense,
        top_expense_categories=[
            schemas.CategoryTotal(category=c, total=t) for c, t in top
        ],
    )


@router.get("/users", response_model=list[schemas.AdminUserOut])
def admin_users(db: Session = Depends(get_db)):
    """All registered users with how many transactions each has."""
    counts = dict(
        db.query(models.Transaction.user_id, func.count(models.Transaction.id))
        .group_by(models.Transaction.user_id)
        .all()
    )
    users = db.query(models.User).order_by(models.User.id).all()
    return [
        schemas.AdminUserOut(
            id=u.id,
            email=u.email,
            is_admin=bool(u.is_admin),
            created_at=u.created_at,
            transaction_count=counts.get(u.id, 0),
        )
        for u in users
    ]


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def admin_delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_current_admin),
):
    """Delete a user and all of their transactions. Admins can't delete themselves."""
    if user_id == admin.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "You cannot delete your own account.")
    user = db.get(models.User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found.")
    db.delete(user)
    db.commit()
