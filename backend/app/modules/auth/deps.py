import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.rate_limit import current_user_org_tier
from app.db.session import get_db
from app.modules.auth.models import User
from app.modules.auth.security import decode_token

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise unauthorized

    try:
        payload = decode_token(credentials.credentials)
    except jwt.PyJWTError:
        raise unauthorized

    if payload.get("type") != "access":
        raise unauthorized

    user = db.query(User).filter(User.email == payload.get("sub")).first()
    if user is None or not user.is_active:
        raise unauthorized

    # Stashed for app.core.rate_limit.org_tier_rate_limit, which needs the
    # caller's org tier but slowapi's dynamic-limit callables don't receive
    # the Request/dependency values directly.
    current_user_org_tier.set(user.org.tier if user.org is not None else None)
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user


def require_tos_accepted(current_user: User = Depends(get_current_user)) -> User:
    if current_user.tos_accepted_at is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must accept the Terms of Service and disclaimer before running a backtest. "
                   "Call POST /api/auth/accept-tos first.",
        )
    return current_user
