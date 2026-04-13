from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import AuditLog, ComplianceRecord, ComplianceStatusEnum, User, UserRole
from app.schemas import ComplianceRecordOut, ComplianceRecordUpdate

router = APIRouter(prefix="/compliance", tags=["compliance"])


def _log(db: Session, user: User, action: str, entity: str, eid: int | None, detail: str | None):
    db.add(AuditLog(user_id=user.id, action=action, entity_type=entity, entity_id=eid, detail=detail))


@router.get("/records", response_model=list[ComplianceRecordOut])
def list_records(
    department_id: int | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = db.query(ComplianceRecord)
    if department_id is not None:
        q = q.filter(ComplianceRecord.department_id == department_id)
    if user.role == UserRole.owner and user.department_id:
        q = q.filter(ComplianceRecord.department_id == user.department_id)
    return q.all()


@router.patch("/records/{record_id}", response_model=ComplianceRecordOut)
def update_record(
    record_id: int,
    body: ComplianceRecordUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if user.role == UserRole.viewer:
        raise HTTPException(403, detail="قراءة فقط")
    rec = db.query(ComplianceRecord).filter(ComplianceRecord.id == record_id).first()
    if not rec:
        raise HTTPException(404, detail="غير موجود")
    if user.role == UserRole.owner and user.department_id and rec.department_id != user.department_id:
        raise HTTPException(403, detail="لا يمكن تعديل إدارة أخرى")

    if body.status is not None:
        rec.status = ComplianceStatusEnum(body.status.value)
    if body.evidence_summary is not None:
        rec.evidence_summary = body.evidence_summary
    if body.owner_user_id is not None:
        rec.owner_user_id = body.owner_user_id
    rec.last_reviewed_at = datetime.now(timezone.utc)
    _log(db, user, "update", "compliance_record", rec.id, str(body.model_dump(exclude_unset=True)))
    db.commit()
    db.refresh(rec)
    return rec
