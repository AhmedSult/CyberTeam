from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.services.report_pdf import build_compliance_report_pdf

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/compliance.pdf")
def compliance_pdf(
    department_id: int | None = Query(default=None, description="تضييق التقرير على إدارة."),
    framework_id: int | None = Query(default=None, description="تضييق التقرير على إطار."),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """تقرير PDF لحالة الامتثال ضمن النطاق المختار (بيانات المنصة)."""
    pdf = build_compliance_report_pdf(db, department_id=department_id, framework_id=framework_id)
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": 'attachment; filename="compliance-report.pdf"',
        },
    )
