from datetime import datetime
from enum import Enum

from pydantic import BaseModel, EmailStr, Field


class UserRoleOut(str, Enum):
    admin = "admin"
    auditor = "auditor"
    owner = "owner"
    viewer = "viewer"


class ComplianceStatusOut(str, Enum):
    not_started = "not_started"
    partial = "partial"
    compliant = "compliant"
    not_applicable = "not_applicable"


class FrameworkOut(BaseModel):
    id: int
    code: str
    name_ar: str
    name_en: str
    description: str | None

    model_config = {"from_attributes": True}


class ControlOut(BaseModel):
    id: int
    framework_id: int
    control_ref: str
    title_ar: str
    title_en: str
    domain_ar: str | None = None
    standard_title_ar: str | None = None
    objective_ar: str | None = None
    description_ar: str | None
    description_en: str | None
    implementation_guidance_ar: str | None
    evidence_guidance_ar: str | None = None
    category: str | None

    model_config = {"from_attributes": True}


class DepartmentOut(BaseModel):
    id: int
    code: str | None = None
    name_ar: str
    name_en: str

    model_config = {"from_attributes": True}


class DepartmentCreate(BaseModel):
    name_ar: str = Field(..., min_length=1, max_length=256)
    name_en: str = Field(..., min_length=1, max_length=256)
    code: str | None = Field(
        default=None,
        max_length=32,
        description="ترميز قصير فريد (مثل IT، RISK) لربط الأنظمة والتقارير.",
    )


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    full_name_ar: str
    role: UserRoleOut = UserRoleOut.viewer
    department_id: int | None = None


class UserOut(BaseModel):
    id: int
    email: str
    full_name_ar: str
    role: UserRoleOut
    department_id: int | None

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ComplianceRecordOut(BaseModel):
    id: int
    control_id: int
    department_id: int
    status: ComplianceStatusOut
    evidence_summary: str | None
    last_reviewed_at: datetime | None
    owner_user_id: int | None

    model_config = {"from_attributes": True}


class ComplianceRecordUpdate(BaseModel):
    status: ComplianceStatusOut | None = None
    evidence_summary: str | None = None
    owner_user_id: int | None = None


class EvidenceOut(BaseModel):
    id: int
    compliance_record_id: int
    filename: str
    notes: str | None
    uploaded_at: datetime

    model_config = {"from_attributes": True}


class DashboardStats(BaseModel):
    total_controls: int
    compliant: int
    partial: int
    not_started: int
    not_applicable: int
    compliance_rate: float


class AIChatRequest(BaseModel):
    message: str
    context_control_id: int | None = None
    department_id: int | None = Field(
        default=None,
        description="نفس فلتر الإدارة في اللوحة — تُحسب لقطة الامتثال ضمن هذا النطاق.",
    )
    gap_summary: str | None = Field(
        default=None,
        max_length=16000,
        description="آخر نص تحليل الفجوات من الواجهة لربط إجابات المساعد به.",
    )
    include_compliance_snapshot: bool = Field(
        default=True,
        description="إن كان True تُلحق لقطة أرقام من قاعدة البيانات (نسب، حالات، ضوابط متأخرة).",
    )
    framework_id: int | None = Field(
        default=None,
        description="نفس فلتر «الإطار» في اللوحة — تُحسب اللقطة والسياق ضمن ضوابط هذا الإطار فقط.",
    )


class AIChatResponse(BaseModel):
    reply: str
    used_llm: bool


class GapAnalysisRequest(BaseModel):
    department_id: int | None = None
    framework_id: int | None = Field(
        default=None,
        description="تضييق تحليل الفجوات على سجلات الامتثال المرتبطة بضوابط هذا الإطار.",
    )
    control_ids: list[int] | None = Field(
        default=None,
        description="عند الإرسال: يقتصر التحليل على سجلات الامتثال لهذه الضوابط فقط (تصفية الجدول في الواجهة).",
    )


class GapAnalysisResponse(BaseModel):
    gaps_summary: str
    prioritized_controls: list[int]
    used_llm: bool


class ExplainFrameworkRequest(BaseModel):
    framework_id: int = Field(..., ge=1)


class ExplainFrameworkResponse(BaseModel):
    explanation: str
    used_llm: bool
    official_ecc_pdf_url: str


class ControlMappingOut(BaseModel):
    id: int
    source_control_id: int
    target_control_id: int
    mapping_note: str | None

    model_config = {"from_attributes": True}
