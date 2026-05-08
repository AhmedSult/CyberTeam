"""عناصر واجهة مشتركة: شارات الحالة والمخاطر والنضج."""

from __future__ import annotations

STATUS_LABEL_AR = {
    "compliant": "ممتثل",
    "partial": "جزئي",
    "not_started": "لم يبدأ",
    "not_applicable": "لا ينطبق",
}
STATUS_LABEL_EN = {
    "compliant": "Compliant",
    "partial": "Partial",
    "not_started": "Not started",
    "not_applicable": "Not applicable",
}
STATUS_COLOR = {
    "compliant": "#10b981",
    "partial": "#f59e0b",
    "not_started": "#ef4444",
    "not_applicable": "#94a3b8",
}
RISK_LABEL_AR = {"low": "منخفض", "medium": "متوسط", "high": "مرتفع", "critical": "حرج"}
RISK_LABEL_EN = {"low": "Low", "medium": "Medium", "high": "High", "critical": "Critical"}
RISK_COLOR = {"low": "#10b981", "medium": "#f59e0b", "high": "#ef4444", "critical": "#7f1d1d"}


def status_badge(status: str, lang: str = "ar") -> str:
    label = (STATUS_LABEL_AR if lang == "ar" else STATUS_LABEL_EN).get(status, status)
    color = STATUS_COLOR.get(status, "#94a3b8")
    return (
        f'<span style="background:{color}22;color:{color};border:1px solid {color}55;'
        f'padding:.18rem .55rem;border-radius:999px;font-size:.78rem;font-weight:600;">{label}</span>'
    )


def risk_badge(risk: str, lang: str = "ar") -> str:
    label = (RISK_LABEL_AR if lang == "ar" else RISK_LABEL_EN).get(risk, risk)
    color = RISK_COLOR.get(risk, "#94a3b8")
    return (
        f'<span style="background:{color}22;color:{color};border:1px solid {color}55;'
        f'padding:.18rem .55rem;border-radius:999px;font-size:.78rem;font-weight:600;">{label}</span>'
    )


def maturity_meter(level: int) -> str:
    level = max(0, min(5, int(level)))
    filled = "▰" * level
    empty = "▱" * (5 - level)
    return f'<span style="letter-spacing:1px;">{filled}{empty}</span> <small style="color:#888;">({level}/5)</small>'
