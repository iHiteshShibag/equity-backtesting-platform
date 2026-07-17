from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.deps import get_current_user, require_admin
from app.modules.auth.models import User
from app.modules.orgs.models import VALID_TIERS
from app.modules.orgs.schemas import OrganizationOut, OrganizationUpdate

router = APIRouter(prefix="/api/orgs", tags=["orgs"])


@router.get("/me", response_model=OrganizationOut)
def get_my_org(current_user: User = Depends(get_current_user)):
    if current_user.org is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No organization assigned")
    return current_user.org


@router.patch("/me", response_model=OrganizationOut)
def update_my_org(
    body: OrganizationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    org = current_user.org
    if org is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No organization assigned")

    if body.tier is not None:
        if body.tier not in VALID_TIERS:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid tier")
        org.tier = body.tier
    if body.name is not None:
        org.name = body.name

    db.commit()
    db.refresh(org)
    return org
