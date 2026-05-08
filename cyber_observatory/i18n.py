from __future__ import annotations

from typing import Literal

Lang = Literal["ar", "en"]

STRINGS: dict[Lang, dict[str, str]] = {
    "ar": {
        "title": "درع سيبراني",
        "subtitle": "منصة امتثال سيبراني بنمط DHWO للعرض والنشر عبر Streamlit Cloud",
        "nav_overview": "نظرة عامة",
        "nav_compliance": "الامتثال",
        "nav_assistant": "المساعد",
        "nav_api": "تكامل API",
        "metric_controls": "عدد الضوابط",
        "metric_rate": "نسبة الامتثال",
        "metric_gaps": "الفجوات المفتوحة",
        "metric_records": "سجلات الامتثال",
        "login_title": "تسجيل دخول API",
        "email": "البريد الإلكتروني",
        "password": "كلمة المرور",
        "api_url": "عنوان API",
        "login_btn": "تسجيل الدخول",
        "logout_btn": "تسجيل الخروج",
        "connected": "متصل بالخادم",
        "not_connected": "غير متصل. تعمل على بيانات تجريبية.",
        "assistant_hint": "اكتب سؤالك حول الفجوات والضوابط.",
        "assistant_send": "إرسال",
        "upload_title": "معاينة ملف امتثال",
        "about": "هذه نسخة Streamlit موحدة بنفس أسلوب DHWO مع واجهات مطورة وتنقل علوي.",
    },
    "en": {
        "title": "Cyber Shield",
        "subtitle": "DHWO-style cyber compliance experience on Streamlit Cloud",
        "nav_overview": "Overview",
        "nav_compliance": "Compliance",
        "nav_assistant": "Assistant",
        "nav_api": "API Integration",
        "metric_controls": "Total controls",
        "metric_rate": "Compliance rate",
        "metric_gaps": "Open gaps",
        "metric_records": "Compliance records",
        "login_title": "API Login",
        "email": "Email",
        "password": "Password",
        "api_url": "API URL",
        "login_btn": "Sign in",
        "logout_btn": "Sign out",
        "connected": "Connected to backend",
        "not_connected": "Not connected. Running in demo mode.",
        "assistant_hint": "Ask about controls, gaps, and action priorities.",
        "assistant_send": "Send",
        "upload_title": "Compliance file preview",
        "about": "Unified Streamlit app using the DHWO techniques with enhanced UX.",
    },
}


def t(lang: Lang, key: str) -> str:
    return STRINGS[lang].get(key, key)

