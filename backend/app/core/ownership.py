from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.modules.auth.models import User


def get_owned_or_404(db: Session, model, obj_id: int, current_user: User, not_found_detail: str):
    """Fetch a row by id, 404ing unless it exists and belongs to current_user
    (admins can access any row). Shared by every module where a user manages
    their own rows of a model (backtest jobs, saved strategies, ...)."""
    obj = db.query(model).filter(model.id == obj_id).first()
    if obj is None or (obj.user_id != current_user.id and current_user.role != "admin"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=not_found_detail)
    return obj
