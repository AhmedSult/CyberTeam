import enum
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class UserRole(str, enum.Enum):
    admin = "admin"
    auditor = "auditor"
    owner = "owner"
    viewer = "viewer"


class ComplianceStatusEnum(str, enum.Enum):
    not_started = "not_started"
    partial = "partial"
    compliant = "compliant"
    not_applicable = "not_applicable"


class Framework(Base):
    __tablename__ = "frameworks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    name_ar: Mapped[str] = mapped_column(String(256))
    name_en: Mapped[str] = mapped_column(String(256))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    controls: Mapped[list["Control"]] = relationship(back_populates="framework")


class Control(Base):
    __tablename__ = "controls"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    framework_id: Mapped[int] = mapped_column(ForeignKey("frameworks.id"), index=True)
    control_ref: Mapped[str] = mapped_column(String(64), index=True)
    title_ar: Mapped[str] = mapped_column(String(512))
    title_en: Mapped[str] = mapped_column(String(512))
    # المجال (حوكمة، تعزيز، صمود، …) — مُنسَّق مع هيكل ECC / GECC
    domain_ar: Mapped[str | None] = mapped_column(String(128), nullable=True)
    standard_title_ar: Mapped[str | None] = mapped_column(Text, nullable=True)
    objective_ar: Mapped[str | None] = mapped_column(Text, nullable=True)
    description_ar: Mapped[str | None] = mapped_column(Text, nullable=True)
    description_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    implementation_guidance_ar: Mapped[str | None] = mapped_column(Text, nullable=True)
    # إرشادات أدلة/إثبات (مرجع الدليل الإرشادي GECC)
    evidence_guidance_ar: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str | None] = mapped_column(String(128), nullable=True)

    framework: Mapped["Framework"] = relationship(back_populates="controls")
    compliance_records: Mapped[list["ComplianceRecord"]] = relationship(back_populates="control")

    __table_args__ = (UniqueConstraint("framework_id", "control_ref", name="uq_framework_control_ref"),)


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str | None] = mapped_column(String(32), unique=True, index=True, nullable=True)
    name_ar: Mapped[str] = mapped_column(String(256))
    name_en: Mapped[str] = mapped_column(String(256))


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(256))
    full_name_ar: Mapped[str] = mapped_column(String(256))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.viewer)
    department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class ComplianceRecord(Base):
    __tablename__ = "compliance_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    control_id: Mapped[int] = mapped_column(ForeignKey("controls.id"), index=True)
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"), index=True)
    status: Mapped[ComplianceStatusEnum] = mapped_column(
        Enum(ComplianceStatusEnum), default=ComplianceStatusEnum.not_started
    )
    evidence_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    owner_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    control: Mapped["Control"] = relationship(back_populates="compliance_records")
    evidences: Mapped[list["Evidence"]] = relationship(back_populates="compliance_record")


class Evidence(Base):
    __tablename__ = "evidences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    compliance_record_id: Mapped[int] = mapped_column(ForeignKey("compliance_records.id"), index=True)
    filename: Mapped[str] = mapped_column(String(512))
    stored_path: Mapped[str] = mapped_column(String(1024))
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    compliance_record: Mapped["ComplianceRecord"] = relationship(back_populates="evidences")


class ControlMapping(Base):
    __tablename__ = "control_mappings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_control_id: Mapped[int] = mapped_column(ForeignKey("controls.id"), index=True)
    target_control_id: Mapped[int] = mapped_column(ForeignKey("controls.id"), index=True)
    mapping_note: Mapped[str | None] = mapped_column(String(512), nullable=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(128))
    entity_type: Mapped[str] = mapped_column(String(64))
    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title_ar: Mapped[str] = mapped_column(String(512))
    control_id: Mapped[int | None] = mapped_column(ForeignKey("controls.id"), nullable=True)
    department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id"), nullable=True)
    assignee_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    due_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="open")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
