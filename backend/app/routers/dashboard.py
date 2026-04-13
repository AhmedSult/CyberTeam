from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import ComplianceRecord, ComplianceStatusEnum, Control, User
from app.schemas import DashboardStats

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStats)
def stats(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    total_controls = db.query(func.count(Control.id)).scalar() or 0
    total_records = db.query(func.count(ComplianceRecord.id)).scalar() or 0
    by_status = dict(
        db.query(ComplianceRecord.status, func.count(ComplianceRecord.id)).group_by(ComplianceRecord.status).all()
    )
    compliant = int(by_status.get(ComplianceStatusEnum.compliant, 0))
    partial = int(by_status.get(ComplianceStatusEnum.partial, 0))
    not_started = int(by_status.get(ComplianceStatusEnum.not_started, 0))
    not_applicable = int(by_status.get(ComplianceStatusEnum.not_applicable, 0))
    denom = total_records or 1
    rate = round(100.0 * compliant / denom, 1)
    return DashboardStats(
        total_controls=total_controls,
        compliant=compliant,
        partial=partial,
        not_started=not_started,
        not_applicable=not_applicable,
        compliance_rate=rate,
    )
