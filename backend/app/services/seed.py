from sqlalchemy.orm import Session

from app.models import (
    ComplianceRecord,
    ComplianceStatusEnum,
    Control,
    Department,
    Framework,
    User,
    UserRole,
)
from app.security import hash_password


def seed_if_empty(db: Session) -> None:
    if db.query(Framework).first():
        return

    fw_nca = Framework(
        code="NCA_ECC",
        name_ar="الضوابط الأساسية للأمن السيبراني — الهيئة الوطنية (NCA / GECC)",
        name_en="NCA Essential Cybersecurity Controls (GECC)",
        description=(
            "إطار وطني سعودي؛ نصوص الضوابط ECC-2-2024 والتنفيذ وفق الدليل الإرشادي GECC-1:2023."
        ),
    )
    fw_nist = Framework(
        code="NIST_CSF",
        name_ar="إطار NIST للأمن السيبراني",
        name_en="NIST Cybersecurity Framework",
        description="Identify, Protect, Detect, Respond, Recover",
    )
    fw_iso = Framework(
        code="ISO27001",
        name_ar="ISO/IEC 27001",
        name_en="ISO/IEC 27001",
        description="نظام إدارة أمن المعلومات",
    )
    db.add_all([fw_nca, fw_nist, fw_iso])
    db.flush()

    controls_data = [
        (fw_nist.id, "PR.AC-1", "إدارة الهويات والاعتمادات", "Identities and credentials", "إدارة الهويات للأصول المصرح بها.", "ربط مع دليل نشط ومراجعة الحسابات."),
        (fw_nist.id, "PR.DS-1", "حماية البيانات", "Data-at-rest protection", "حماية البيانات المخزنة.", "تشفير الأقراص والنسخ الاحتياطي."),
        (fw_iso.id, "A.5.1", "سياسات أمن المعلومات", "Information security policies", "توجيه ودعم لممارسات أمن المعلومات.", "وثائق معتمدة وتواصل للموظفين."),
        (fw_iso.id, "A.8.1", "إدارة الأصول", "Asset management", "تحديد الأصول المعلوماتية وحمايتها.", "جرد الأصول وتصنيفها."),
    ]
    objs = []
    for fid, ref, tar, ten, desc, guide in controls_data:
        objs.append(
            Control(
                framework_id=fid,
                control_ref=ref,
                title_ar=tar,
                title_en=ten,
                description_ar=desc,
                description_en=desc,
                implementation_guidance_ar=guide,
                category="أساسي",
            )
        )
    db.add_all(objs)
    db.flush()

    dept_it = Department(code="IT", name_ar="تقنية المعلومات", name_en="IT")
    dept_risk = Department(code="RISK", name_ar="إدارة المخاطر", name_en="Risk")
    db.add_all([dept_it, dept_risk])
    db.flush()

    admin = User(
        email="admin@example.com",
        hashed_password=hash_password("admin123"),
        full_name_ar="مدير النظام",
        role=UserRole.admin,
        department_id=dept_it.id,
    )
    db.add(admin)
    db.flush()

    all_c = db.query(Control).all()
    for c in all_c:
        for d in [dept_it, dept_risk]:
            status = ComplianceStatusEnum.partial
            if c.control_ref == "PR.DS-1":
                status = ComplianceStatusEnum.not_started
            if c.control_ref == "PR.AC-1" and d.id == dept_it.id:
                status = ComplianceStatusEnum.compliant
            db.add(
                ComplianceRecord(
                    control_id=c.id,
                    department_id=d.id,
                    status=status,
                    evidence_summary="عينة أدلة" if status == ComplianceStatusEnum.compliant else None,
                    owner_user_id=admin.id if d.id == dept_it.id and status == ComplianceStatusEnum.compliant else None,
                )
            )

    db.commit()
