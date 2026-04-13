"""مزامنة مكتبة ضوابط NCA (ECC-2-2024) مع بيانات وصفية GECC من JSON."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from sqlalchemy.orm import Session

from app.models import ComplianceRecord, ComplianceStatusEnum, Control, Department, Framework

_log = logging.getLogger(__name__)

_CATALOG = Path(__file__).resolve().parent.parent / "data" / "ecc2_2024_catalog.json"


def _ensure_nca_framework_labels(db: Session) -> None:
    fw = db.query(Framework).filter(Framework.code == "NCA_ECC").first()
    if not fw:
        return
    fw.name_ar = "الضوابط الأساسية للأمن السيبراني — الهيئة الوطنية (NCA / GECC)"
    fw.name_en = "NCA Essential Cybersecurity Controls (GECC)"
    fw.description = (
        "إطار وطني سعودي: نصوص الضوابط من ECC-2-2024؛ التنفيذ والأدلة الإرشادية تُنسَّق مع "
        "«الدليل الإرشادي لتطبيق الضوابط الأساسية» (GECC-1:2023)."
    )


def sync_ecc_catalog(db: Session) -> dict[str, int]:
    """يستبدل ضوابط إطار NCA_ECC بمحتوى الكتالوج ويُنشئ سجلات امتثال للأقسام عند الحاجة."""
    if not _CATALOG.is_file():
        _log.warning("ملف كتالوج ECC غير موجود: %s", _CATALOG)
        return {"updated": 0, "skipped": 1}

    fw = db.query(Framework).filter(Framework.code == "NCA_ECC").first()
    if not fw:
        return {"updated": 0, "skipped": 1}
    _ensure_nca_framework_labels(db)

    payload = json.loads(_CATALOG.read_text(encoding="utf-8"))
    rows: list[dict] = payload.get("controls") or []
    refs_json = {r["ref"] for r in rows}

    existing = db.query(Control).filter(Control.framework_id == fw.id).all()
    for c in existing:
        if not c.control_ref.startswith("ECC-"):
            continue
        if c.control_ref in refs_json:
            continue
        db.query(ComplianceRecord).filter(ComplianceRecord.control_id == c.id).delete()
        db.delete(c)
    db.flush()

    by_ref = {c.control_ref: c for c in db.query(Control).filter(Control.framework_id == fw.id).all()}
    updated = 0
    for r in rows:
        ref = r["ref"]
        obj = Control(
            framework_id=fw.id,
            control_ref=ref,
            title_ar=r.get("title_ar") or ref,
            title_en=r.get("title_en") or ref,
            domain_ar=r.get("domain_ar"),
            standard_title_ar=r.get("standard_title_ar"),
            objective_ar=r.get("objective_ar"),
            description_ar=r.get("objective_ar"),
            description_en=r.get("standard_title_en"),
            implementation_guidance_ar=r.get("control_text_ar"),
            evidence_guidance_ar=r.get("evidence_guidance_ar"),
            category=r.get("category_ar"),
        )
        if ref in by_ref:
            cur = by_ref[ref]
            cur.title_ar = obj.title_ar
            cur.title_en = obj.title_en
            cur.domain_ar = obj.domain_ar
            cur.standard_title_ar = obj.standard_title_ar
            cur.objective_ar = obj.objective_ar
            cur.description_ar = obj.description_ar
            cur.description_en = obj.description_en
            cur.implementation_guidance_ar = obj.implementation_guidance_ar
            cur.evidence_guidance_ar = obj.evidence_guidance_ar
            cur.category = obj.category
            _ensure_compliance_for_control(db, cur.id)
        else:
            db.add(obj)
            db.flush()
            by_ref[ref] = obj
            _ensure_compliance_for_control(db, obj.id)
        updated += 1

    db.commit()
    return {"updated": updated, "skipped": 0}


def _ensure_compliance_for_control(db: Session, control_id: int) -> None:
    depts = db.query(Department).all()
    for d in depts:
        exists = (
            db.query(ComplianceRecord)
            .filter(
                ComplianceRecord.control_id == control_id,
                ComplianceRecord.department_id == d.id,
            )
            .first()
        )
        if exists:
            continue
        db.add(
            ComplianceRecord(
                control_id=control_id,
                department_id=d.id,
                status=ComplianceStatusEnum.not_started,
                evidence_summary=None,
            )
        )
