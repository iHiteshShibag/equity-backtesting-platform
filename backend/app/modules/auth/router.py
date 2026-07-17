from datetime import datetime, timezone

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.rate_limit import limiter
from app.db.session import get_db
from app.modules.auth.deps import get_current_user
from app.modules.auth.models import User
from app.modules.auth.schemas import ChangePasswordRequest, LoginRequest, MeUpdate, TokenResponse, UserOut
from app.modules.auth.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])

# Refresh token lives only in an httpOnly cookie, scoped to this router's own
# path, so it's never readable by JS (XSS-safe) and never sent to unrelated
# API routes.
REFRESH_COOKIE_NAME = "refresh_token"
REFRESH_COOKIE_PATH = "/api/auth"


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=settings.ENVIRONMENT == "production",
        samesite="lax",
        path=REFRESH_COOKIE_PATH,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )


def _to_user_out(user: User) -> UserOut:
    name = user.full_name or user.email
    initials = "".join(part[0] for part in name.split()[:2]).upper() or "U"
    return UserOut(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        initials=initials,
        role=user.role,
        is_active=user.is_active,
        tos_accepted_at=user.tos_accepted_at,
    )


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
def login(request: Request, req: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    if user is None or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Account is deactivated")

    _set_refresh_cookie(response, create_refresh_token(user.email))
    return TokenResponse(access_token=create_access_token(user.email))


@router.post("/refresh", response_model=TokenResponse)
def refresh(request: Request, response: Response, db: Session = Depends(get_db)):
    unauthorized = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")

    refresh_token = request.cookies.get(REFRESH_COOKIE_NAME)
    if not refresh_token:
        raise unauthorized

    try:
        payload = decode_token(refresh_token)
    except jwt.PyJWTError:
        raise unauthorized

    if payload.get("type") != "refresh":
        raise unauthorized

    user = db.query(User).filter(User.email == payload.get("sub")).first()
    if user is None or not user.is_active:
        raise unauthorized

    _set_refresh_cookie(response, create_refresh_token(user.email))
    return TokenResponse(access_token=create_access_token(user.email))


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(key=REFRESH_COOKIE_NAME, path=REFRESH_COOKIE_PATH)
    return {"detail": "logged out"}


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return _to_user_out(current_user)


@router.patch("/me", response_model=UserOut)
def update_me(req: MeUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if req.full_name is not None:
        current_user.full_name = req.full_name.strip() or None
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return _to_user_out(current_user)


@router.post("/change-password")
def change_password(
    req: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(req.current_password, current_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Current password is incorrect")
    current_user.hashed_password = hash_password(req.new_password)
    db.add(current_user)
    db.commit()
    return {"detail": "Password updated"}


@router.post("/accept-tos", response_model=UserOut)
def accept_tos(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    current_user.tos_accepted_at = datetime.now(timezone.utc)
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return _to_user_out(current_user)
