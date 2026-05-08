from __future__ import annotations

import pandas as pd


def seed_frameworks() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"id": 1, "code": "NCA_ECC", "name_ar": "ضوابط NCA ECC"},
            {"id": 2, "code": "NIST_CSF", "name_ar": "إطار NIST CSF"},
            {"id": 3, "code": "ISO27001", "name_ar": "إطار ISO 27001"},
        ]
    )


def seed_departments() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"id": 1, "code": "IT", "name_ar": "تقنية المعلومات"},
            {"id": 2, "code": "RISK", "name_ar": "إدارة المخاطر"},
            {"id": 3, "code": "GRC", "name_ar": "الحوكمة والامتثال"},
        ]
    )


def seed_controls() -> pd.DataFrame:
    data = [
        {"id": 1, "framework_id": 1, "control_ref": "ECC-1-1", "title_ar": "الحوكمة", "domain_ar": "الحوكمة"},
        {"id": 2, "framework_id": 1, "control_ref": "ECC-1-2", "title_ar": "إدارة الأصول", "domain_ar": "الحماية"},
        {"id": 3, "framework_id": 1, "control_ref": "ECC-1-3", "title_ar": "الهوية والوصول", "domain_ar": "الحماية"},
        {"id": 4, "framework_id": 2, "control_ref": "PR.AC-1", "title_ar": "التحكم بالوصول", "domain_ar": "Protect"},
        {"id": 5, "framework_id": 2, "control_ref": "DE.CM-1", "title_ar": "المراقبة المستمرة", "domain_ar": "Detect"},
        {"id": 6, "framework_id": 3, "control_ref": "A.5.1", "title_ar": "سياسات أمن المعلومات", "domain_ar": "ISMS"},
    ]
    return pd.DataFrame(data)


def seed_records() -> pd.DataFrame:
    data = [
        {"id": 1, "control_id": 1, "department_id": 1, "status": "compliant", "evidence_summary": "سياسة معتمدة"},
        {"id": 2, "control_id": 2, "department_id": 1, "status": "partial", "evidence_summary": "جرد جزئي"},
        {"id": 3, "control_id": 3, "department_id": 1, "status": "not_started", "evidence_summary": ""},
        {"id": 4, "control_id": 1, "department_id": 2, "status": "partial", "evidence_summary": "ضوابط قيد التنفيذ"},
        {"id": 5, "control_id": 4, "department_id": 2, "status": "compliant", "evidence_summary": "تقرير تدقيق"},
        {"id": 6, "control_id": 5, "department_id": 2, "status": "partial", "evidence_summary": ""},
        {"id": 7, "control_id": 6, "department_id": 3, "status": "not_started", "evidence_summary": ""},
    ]
    return pd.DataFrame(data)


def calc_stats(records: pd.DataFrame, controls: pd.DataFrame) -> dict[str, float | int]:
    total_controls = int(len(controls))
    compliant = int((records["status"] == "compliant").sum())
    partial = int((records["status"] == "partial").sum())
    not_started = int((records["status"] == "not_started").sum())
    not_applicable = int((records["status"] == "not_applicable").sum())
    total = max(len(records), 1)
    rate = round(100.0 * compliant / total, 1)
    return {
        "total_controls": total_controls,
        "compliance_rate": rate,
        "gap_open_count": partial + not_started,
        "records_total": int(len(records)),
        "compliant": compliant,
        "partial": partial,
        "not_started": not_started,
        "not_applicable": not_applicable,
    }

