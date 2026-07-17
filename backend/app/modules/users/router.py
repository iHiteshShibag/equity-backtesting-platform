from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.deps import require_admin
from app.modules.auth.models import User
from app.modules.auth.router import _to_user_out
from app.modules.auth.schemas import UserCreate, UserOut, UserUpdate
from app.modules.auth.security import hash_password
from app.modules.orgs.models import Organization

router = APIRouter(prefix="/api/users", tags=["users"])

VALID_ROLES = {"admin", "member"}


@router.get("", response_model=list[UserOut])
def list_users(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    users = db.query(User).order_by(User.id).offset(offset).limit(limit).all()
    return [_to_user_out(u) for u in users]


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(
    req: UserCreate, db: Session = Depends(get_db), _: User = Depends(require_admin)
):
    if req.role not in VALID_ROLES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role")
    if db.query(User).filter(User.email == req.email).first() is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already in use")

    # Scaffolding for a future SaaS/multi-tenant pivot: every user belongs to
    # an org (tier drives rate limits, see app/core/rate_limit.py). No
    # workspace-picker UI yet, so new users just join a shared default org.
    default_org = db.query(Organization).order_by(Organization.id).first()

    user = User(
        email=req.email,
        hashed_password=hash_password(req.password),
        full_name=req.full_name,
        role=req.role,
        org_id=default_org.id if default_org else None,
    )
    db.add(user)
    db.commit()
    return _to_user_out(user)


@router.patch("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    req: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user.id == current_user.id and (
        (req.role is not None and req.role != "admin") or req.is_active is False
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot demote or deactivate your own account",
        )

    if req.role is not None:
        if req.role not in VALID_ROLES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role")
        user.role = req.role
    if req.full_name is not None:
        user.full_name = req.full_name
    if req.is_active is not None:
        user.is_active = req.is_active

    db.commit()
    return _to_user_out(user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    if user_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot delete your own account")

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    db.delete(user)
    db.commit()
