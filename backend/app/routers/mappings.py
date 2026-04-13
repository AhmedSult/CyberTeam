from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import ControlMapping, User
from app.schemas import ControlMappingOut

router = APIRouter(prefix="/mappings", tags=["mappings"])


@router.get("", response_model=list[ControlMappingOut])
def list_mappings(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(ControlMapping).all()
