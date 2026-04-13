from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, require_roles
from app.models import Department, User, UserRole
from app.schemas import DepartmentCreate, DepartmentOut

router = APIRouter(prefix="/departments", tags=["departments"])


@router.get("", response_model=list[DepartmentOut])
def list_departments(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(Department).order_by(Department.id).all()


@router.post("", response_model=DepartmentOut)
def create_department(
    body: DepartmentCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.admin)),
):
    code = (body.code or "").strip() or None
    if code:
        taken = db.query(Department).filter(Department.code == code).first()
        if taken:
            raise HTTPException(status_code=400, detail="ترميز الإدارة مستخدم مسبقاً")
    row = Department(
        name_ar=body.name_ar.strip(),
        name_en=body.name_en.strip(),
        code=code,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
