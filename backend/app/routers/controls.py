from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import Control, Framework, User
from app.schemas import ControlOut, FrameworkOut

router = APIRouter(prefix="/controls", tags=["controls"])


@router.get("/frameworks", response_model=list[FrameworkOut])
def list_frameworks(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(Framework).order_by(Framework.code).all()


@router.get("", response_model=list[ControlOut])
def list_controls(
    framework_id: int | None = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = db.query(Control)
    if framework_id is not None:
        q = q.filter(Control.framework_id == framework_id)
    return q.order_by(Control.framework_id, Control.control_ref).all()
