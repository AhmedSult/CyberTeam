"""تقرير امتثال PDF (عربي RTL) — ReportLab + خط Noto."""

from __future__ import annotations

import io
from datetime import datetime
from pathlib import Path

import arabic_reshaper
from bidi.algorithm import get_display
from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy.orm import Session

from app.brand import PLATFORM_NAME_AR
from app.models import ComplianceRecord, ComplianceStatusEnum, Control, Department, Framework

_BACKEND = Path(__file__).resolve().parent.parent.parent
_FONT_PATH = _BACKEND / "data" / "fonts" / "NotoSansArabic-Regular.ttf"
_FONT_NAME = "NotoSansArabic"


def _rtl(text: str) -> str:
    if not text.strip():
        return text
    reshaped = arabic_reshaper.reshape(text)
    return get_display(reshaped)


def _ensure_font() -> str:
    if _FONT_PATH.is_file():
        try:
            pdfmetrics.registerFont(TTFont(_FONT_NAME, str(_FONT_PATH)))
        except Exception:
            return "Helvetica"
        return _FONT_NAME
    return "Helvetica"


def _p_style(font_name: str, size: float, leading: float | None = None) -> ParagraphStyle:
    return ParagraphStyle(
        name=f"ar_{size}",
        fontName=font_name,
        fontSize=size,
        leading=leading or size * 1.35,
        alignment=TA_RIGHT,
        textColor=colors.HexColor("#1a1a1a"),
    )


def _scoped_records(
    db: Session,
    department_id: int | None,
    framework_id: int | None,
) -> list[ComplianceRecord]:
    q = db.query(ComplianceRecord)
    if department_id is not None:
        q = q.filter(ComplianceRecord.department_id == department_id)
    if framework_id is not None:
        q = q.join(Control, ComplianceRecord.control_id == Control.id).filter(Control.framework_id == framework_id)
    return q.all()


def build_compliance_report_pdf(
    db: Session,
    *,
    department_id: int | None = None,
    framework_id: int | None = None,
) -> bytes:
    rows = _scoped_records(db, department_id, framework_id)

    def _cnt(st: ComplianceStatusEnum) -> int:
        return sum(1 for r in rows if r.status == st)

    total = len(rows)
    compliant = _cnt(ComplianceStatusEnum.compliant)
    partial = _cnt(ComplianceStatusEnum.partial)
    not_started = _cnt(ComplianceStatusEnum.not_started)
    not_applicable = _cnt(ComplianceStatusEnum.not_applicable)
    gap_open = partial + not_started
    rate = round(100.0 * compliant / total, 1) if total else 0.0

    dept_line = "جميع الإدارات"
    if department_id is not None:
        d = db.query(Department).filter(Department.id == department_id).first()
        dept_line = d.name_ar if d else f"إدارة #{department_id}"

    fw_line = "جميع الأطر"
    if framework_id is not None:
        fw = db.query(Framework).filter(Framework.id == framework_id).first()
        fw_line = f"{fw.name_ar} ({fw.code})" if fw else f"إطار #{framework_id}"

    font = _ensure_font()
    title_style = _p_style(font, 16)
    body_style = _p_style(font, 11)
    small_style = _p_style(font, 9)

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        rightMargin=1.8 * cm,
        leftMargin=1.8 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
        title="ComplianceReport",
    )
    story: list = []

    story.append(Paragraph(_rtl(f"تقرير امتثال — {PLATFORM_NAME_AR}"), title_style))
    story.append(Spacer(1, 0.4 * cm))
    story.append(
        Paragraph(
            _rtl(f"تاريخ الإنشاء: {datetime.now().strftime('%Y-%m-%d %H:%M')} — النطاق: {dept_line} — {fw_line}"),
            small_style,
        )
    )
    story.append(Spacer(1, 0.5 * cm))

    stats_data = [
        [_rtl("إجمالي السجلات في النطاق"), str(total)],
        [_rtl("ممتثل"), str(compliant)],
        [_rtl("جزئي"), str(partial)],
        [_rtl("لم يبدأ"), str(not_started)],
        [_rtl("لا ينطبق"), str(not_applicable)],
        [_rtl("فجوات مفتوحة (جزئي + لم يبدأ)"), str(gap_open)],
        [_rtl("نسبة الممتثل"), f"{rate}%"],
    ]
    t = Table([[Paragraph(_rtl(a), body_style), b] for a, b in stats_data], colWidths=[9 * cm, 4 * cm])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f4f7f5")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#c8d4cc")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (1, 0), (1, -1), "CENTER"),
            ]
        )
    )
    story.append(t)
    story.append(Spacer(1, 0.6 * cm))

    open_rows = [r for r in rows if r.status in (ComplianceStatusEnum.partial, ComplianceStatusEnum.not_started)]
    open_rows = open_rows[:35]
    if open_rows:
        story.append(Paragraph(_rtl("أمثلة ضوابط تحتاج متابعة (جزئي / لم يبدأ):"), body_style))
        story.append(Spacer(1, 0.25 * cm))
        c_ids = {r.control_id for r in open_rows}
        controls = {c.id: c for c in db.query(Control).filter(Control.id.in_(c_ids)).all()}
        for r in open_rows:
            c = controls.get(r.control_id)
            ref = c.control_ref if c else str(r.control_id)
            title = (c.title_ar or "")[:120] if c else ""
            st_l = "جزئي" if r.status == ComplianceStatusEnum.partial else "لم يبدأ"
            line = f"[{ref}] {title} — {st_l}"
            story.append(Paragraph(_rtl(line), small_style))
            story.append(Spacer(1, 0.12 * cm))
    else:
        story.append(Paragraph(_rtl("لا توجد في هذا النطاق سجلات بحالة «جزئي» أو «لم يبدأ»."), body_style))

    story.append(Spacer(1, 0.5 * cm))
    story.append(
        Paragraph(
            _rtl(
                f"تنويه: هذا التقرير مبني على بيانات مسجّلة في {PLATFORM_NAME_AR} ولا يمثّل اعتماداً رسمياً من الجهات الخارجية. "
                "المرجع الرسمي للضوابط: الهيئة الوطنية للأمن السيبراني nca.gov.sa"
            ),
            small_style,
        )
    )

    doc.build(story)
    return buf.getvalue()
