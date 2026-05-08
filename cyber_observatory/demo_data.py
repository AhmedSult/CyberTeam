from __future__ import annotations

import pandas as pd


def demo_stats() -> dict[str, float | int]:
    return {
        "total_controls": 133,
        "compliance_rate": 71.4,
        "gap_open_count": 29,
        "records_total": 108,
        "compliant": 77,
        "partial": 21,
        "not_started": 8,
        "not_applicable": 2,
    }


def demo_records() -> pd.DataFrame:
    data = [
        {"control_id": 1, "department_id": 1, "status": "compliant", "evidence_summary": "سياسة محدثة"},
        {"control_id": 2, "department_id": 1, "status": "partial", "evidence_summary": "إجراءات قيد التنفيذ"},
        {"control_id": 3, "department_id": 2, "status": "not_started", "evidence_summary": "لا يوجد"},
        {"control_id": 4, "department_id": 2, "status": "compliant", "evidence_summary": "تقرير تدقيق"},
        {"control_id": 5, "department_id": 3, "status": "partial", "evidence_summary": "خطة معالجة"},
    ]
    return pd.DataFrame(data)

