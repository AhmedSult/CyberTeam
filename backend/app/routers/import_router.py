import io
import os
import uuid
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, require_roles
from app.models import ComplianceRecord, Control, Evidence, Framework, User, UserRole
from app.services.ai_service import ai_parse_import_preview

router = APIRouter(prefix="/import", tags=["import"])

UPLOADS = Path(__file__).resolve().parent.parent.parent / "uploads"
UPLOADS.mkdir(parents=True, exist_ok=True)


@router.post("/preview")
async def preview(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    name = (file.filename or "").lower()
    raw = await file.read()
    try:
        if name.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(raw))
        elif name.endswith(".xlsx") or name.endswith(".xls"):
            df = pd.read_excel(io.BytesIO(raw))
        else:
            raise HTTPException(400, detail="يدعم CSV و XLSX فقط في المعاينة")
    except Exception as e:
        raise HTTPException(400, detail=f"فشل القراءة: {e}") from e
    rows = df.head(100).fillna("").to_dict(orient="records")
    return {"rows": rows, "ai_summary": ai_parse_import_preview(rows)}


@router.post("/controls")
async def import_controls(
    file: UploadFile = File(...),
    framework_code: str = "CUSTOM",
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.auditor)),
):
    raw = await file.read()
    name = (file.filename or "").lower()
    try:
        if name.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(raw))
        elif name.endswith(".xlsx"):
            df = pd.read_excel(io.BytesIO(raw))
        else:
            raise HTTPException(400, detail="CSV أو XLSX")
    except Exception as e:
        raise HTTPException(400, detail=str(e)) from e

    # أعمدة مرنة: ref / مرجع / control_ref
    col_map = {c.lower().strip(): c for c in df.columns}
    def pick(*names):
        for n in names:
            for k, v in col_map.items():
                if n in k.replace(" ", ""):
                    return v
        return None

    cref = pick("ref", "مرجع", "control")
    title = pick("title", "عنوان", "name")
    if not cref or not title:
        raise HTTPException(400, detail="يلزم عمود مرجع الضابط والعنوان")

    fw = db.query(Framework).filter(Framework.code == framework_code).first()
    if not fw:
        fw = Framework(code=framework_code, name_ar=framework_code, name_en=framework_code, description="مستورد")
        db.add(fw)
        db.flush()

    added = 0
    for _, row in df.iterrows():
        ref = str(row.get(cref, "")).strip()
        tar = str(row.get(title, "")).strip()
        if not ref or not tar:
            continue
        exists = db.query(Control).filter(Control.framework_id == fw.id, Control.control_ref == ref).first()
        if exists:
            continue
        db.add(
            Control(
                framework_id=fw.id,
                control_ref=ref,
                title_ar=tar,
                title_en=tar,
                description_ar=None,
                implementation_guidance_ar="مستورد من ملف",
            )
        )
        added += 1
    db.commit()
    return {"imported": added, "framework": framework_code}


@router.post("/evidence/{compliance_record_id}")
async def upload_evidence(
    compliance_record_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    rec = db.query(ComplianceRecord).filter(ComplianceRecord.id == compliance_record_id).first()
    if not rec:
        raise HTTPException(404, detail="سجل غير موجود")
    ext = os.path.splitext(file.filename or "")[1][:10] or ".bin"
    fn = f"{uuid.uuid4().hex}{ext}"
    path = UPLOADS / fn
    content = await file.read()
    path.write_bytes(content)
    ev = Evidence(
        compliance_record_id=compliance_record_id,
        filename=file.filename or fn,
        stored_path=str(path),
        notes=None,
    )
    db.add(ev)
    db.commit()
    db.refresh(ev)
    return {"id": ev.id, "filename": ev.filename}
