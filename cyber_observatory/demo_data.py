from __future__ import annotations

from datetime import date, timedelta

import pandas as pd

from cyber_observatory.ecc_catalog import ECC_CONTROLS, DOMAINS_ORDER

STATUSES = ["not_started", "partial", "compliant", "not_applicable"]
RISK_LEVELS = ["low", "medium", "high", "critical"]
PRIORITIES = ["low", "medium", "high", "critical"]
MATURITY_LABELS = {
    0: "غير موجود",
    1: "أوّلي",
    2: "مُعرَّف",
    3: "مُطبَّق",
    4: "مُقاس",
    5: "محسّن",
}


def seed_frameworks() -> pd.DataFrame:
    return pd.DataFrame([
        {"id": 1, "code": "NCA_ECC", "name_ar": "ضوابط NCA ECC-2-2024",
         "description": "الضوابط الأساسية للأمن السيبراني — الهيئة الوطنية للأمن السيبراني (المملكة العربية السعودية)."},
        {"id": 2, "code": "NIST_CSF", "name_ar": "NIST Cybersecurity Framework",
         "description": "إطار NIST للأمن السيبراني — مرجع دولي للحوكمة والحماية والاكتشاف والاستجابة."},
        {"id": 3, "code": "ISO27001", "name_ar": "ISO/IEC 27001:2022",
         "description": "المعيار الدولي لإدارة أمن المعلومات (ISMS)."},
    ])


def seed_departments() -> pd.DataFrame:
    return pd.DataFrame([
        {"id": 1, "code": "IT", "name_ar": "تقنية المعلومات", "name_en": "Information Technology"},
        {"id": 2, "code": "RISK", "name_ar": "إدارة المخاطر", "name_en": "Risk Management"},
        {"id": 3, "code": "GRC", "name_ar": "الحوكمة والامتثال", "name_en": "Governance & Compliance"},
        {"id": 4, "code": "SOC", "name_ar": "مركز عمليات الأمن", "name_en": "Security Operations Center"},
        {"id": 5, "code": "HR", "name_ar": "الموارد البشرية", "name_en": "Human Resources"},
        {"id": 6, "code": "LEGAL", "name_ar": "الشؤون القانونية", "name_en": "Legal Affairs"},
    ])


def seed_controls() -> pd.DataFrame:
    rows = []
    for i, c in enumerate(ECC_CONTROLS, start=1):
        rows.append({
            "id": i,
            "framework_id": 1,
            "control_ref": c["ref"],
            "title_ar": c["title"],
            "domain_ar": c["domain"],
            "subdomain_ar": c["subdomain"],
            "objective_ar": c["objective"],
            "guidance_ar": c["guidance"],
            "evidence_guidance_ar": c["evidence"],
            "priority": c["priority"],
        })
    return pd.DataFrame(rows)


def _seed_records_template() -> list[dict]:
    """قراءة افتراضية معقولة: GRC تتعامل مع الحوكمة، IT/SOC مع التعزيز، إلخ."""
    today = date.today()
    out: list[dict] = []
    rec_id = 1
    for control in seed_controls().to_dict("records"):
        domain = control["domain_ar"]
        # توزيع الإدارة المختصة بحسب المجال
        if domain == "حوكمة الأمن السيبراني":
            dept = 3  # GRC
        elif domain == "تعزيز الأمن السيبراني":
            dept = 4 if control["control_ref"].startswith(("2-12", "2-13")) else 1
        elif domain == "صمود الأمن السيبراني":
            dept = 2  # Risk
        else:
            dept = 6  # Legal
        # حالة افتراضية متفاوتة لإعطاء واقعية
        ref = control["control_ref"]
        idx = (rec_id - 1) % 7
        status = ("compliant", "partial", "not_started", "compliant",
                  "partial", "not_started", "not_applicable")[idx]
        maturity = (3, 2, 1, 4, 2, 0, 0)[idx]
        risk = ("low", "medium", "high", "low", "medium", "high", "low")[idx]
        target = today + timedelta(days=(60 - idx * 5))
        out.append({
            "id": rec_id,
            "control_id": control["id"],
            "department_id": dept,
            "status": status,
            "maturity_level": maturity,
            "risk_rating": risk,
            "owner": "—",
            "target_date": target.isoformat(),
            "evidence_summary": "" if status == "not_started" else f"دليل أوّلي للضابط {ref}",
            "evidence_files": "",
            "notes": "",
            "last_updated": today.isoformat(),
            "last_updated_by": "system",
        })
        rec_id += 1
    return out


def seed_records() -> pd.DataFrame:
    return pd.DataFrame(_seed_records_template())


def seed_audit_log() -> pd.DataFrame:
    return pd.DataFrame(columns=["timestamp", "user", "action", "entity", "entity_id", "details"])


def calc_stats(records: pd.DataFrame, controls: pd.DataFrame) -> dict[str, float | int]:
    total_controls = int(len(controls))
    compliant = int((records["status"] == "compliant").sum())
    partial = int((records["status"] == "partial").sum())
    not_started = int((records["status"] == "not_started").sum())
    not_applicable = int((records["status"] == "not_applicable").sum())
    total = max(len(records), 1)
    rate = round(100.0 * compliant / total, 1)
    avg_maturity = round(float(records["maturity_level"].mean()), 2) if "maturity_level" in records.columns and len(records) else 0.0
    high_risk = int((records["risk_rating"].isin(["high", "critical"])).sum()) if "risk_rating" in records.columns else 0
    return {
        "total_controls": total_controls,
        "compliance_rate": rate,
        "gap_open_count": partial + not_started,
        "records_total": int(len(records)),
        "compliant": compliant,
        "partial": partial,
        "not_started": not_started,
        "not_applicable": not_applicable,
        "avg_maturity": avg_maturity,
        "high_risk_count": high_risk,
    }


def maturity_by_domain(records_merged: pd.DataFrame) -> pd.DataFrame:
    if records_merged.empty or "domain_ar" not in records_merged.columns:
        return pd.DataFrame(columns=["domain_ar", "avg_maturity", "count"])
    g = (
        records_merged.groupby("domain_ar")
        .agg(avg_maturity=("maturity_level", "mean"), count=("maturity_level", "count"))
        .reset_index()
    )
    g["avg_maturity"] = g["avg_maturity"].round(2)
    return g


def domains_order() -> list[str]:
    return list(DOMAINS_ORDER)
