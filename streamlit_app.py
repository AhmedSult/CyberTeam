"""
درع سيبراني — نسخة Streamlit Cloud

المنصة الكاملة: FastAPI (backend/) + React (frontend/). هذا الملف يُمكّن النشر على share.streamlit.io فقط.

إعدادات Streamlit Cloud:
- Main file path: streamlit_app.py
- Python version: 3.12 (موصى به)

أسرار اختيارية (Settings → Secrets):
API_URL = "https://عنوان-خادمك-لاحقاً.onrender.com"
"""

from __future__ import annotations

import io
from typing import Any

import httpx
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="درع سيبراني",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;600;700;800&display=swap');
    html, body, [class*="st"] { font-family: 'Tajawal', 'IBM Plex Sans Arabic', sans-serif !important; }
    .stApp { direction: rtl; text-align: right; }
    [data-testid="stHeader"] { direction: ltr; }
    div[data-testid="stToolbar"] { direction: ltr; }
    h1, h2, h3 { font-weight: 800 !important; color: #003d28 !important; }
</style>
""",
    unsafe_allow_html=True,
)


def _secrets_get(key: str, default: str | None = None) -> str | None:
    try:
        v = st.secrets.get(key)
        return str(v).strip() if v else default
    except Exception:
        return default


def main() -> None:
    st.title("🛡️ درع سيبراني")
    st.caption("إدارة الضوابط والامتثال السيبراني — عرض على Streamlit Cloud")

    st.info(
        "**ملاحظة:** النسخة الكاملة للمنصة تتضمن واجهة React وخادم FastAPI وقاعدة بيانات. "
        "هنا تعرض **واجهة خفيفة** للمعاينة؛ لربطها بخادمك انشر الـ API (مثل Render) ثم أضف `API_URL` في أسرار التطبيق."
    )

    api_url = _secrets_get("API_URL", "").rstrip("/")
    with st.sidebar:
        st.subheader("الاتصال بالـ API")
        manual = st.text_input(
            "عنوان API (اختياري)",
            value=api_url or "",
            placeholder="https://....onrender.com",
            help="يُقرأ أيضاً من Secrets كـ API_URL",
        )
        base = (manual or api_url or "").rstrip("/")
        if st.button("فحص /api/health"):
            if not base:
                st.warning("أدخل عنوان API أو عيّن API_URL في Secrets.")
            else:
                try:
                    r = httpx.get(f"{base}/api/health", timeout=15.0)
                    if r.status_code == 200:
                        st.success(f"متصل: {r.json()}")
                    else:
                        st.error(f"خطأ HTTP {r.status_code}")
                except Exception as e:
                    st.error(f"تعذر الاتصال: {e}")

    tab1, tab2 = st.tabs(["معاينة جدول (Excel / CSV)", "عن المنصة"])
    with tab1:
        st.markdown("ارفع ملفاً لعرض أول الصفوف وعدد الأعمدة — **بدون** تخزين على خادم Streamlit بعد إغلاق الجلسة.")
        up = st.file_uploader("ملف", type=["csv", "xlsx", "xls"])
        if up is not None:
            name = (up.name or "").lower()
            raw = up.read()
            try:
                if name.endswith(".csv"):
                    df = pd.read_csv(io.BytesIO(raw))
                else:
                    df = pd.read_excel(io.BytesIO(raw), sheet_name=0)
                st.success(f"تمت القراءة: {len(df)} صفاً، {len(df.columns)} عموداً.")
                st.dataframe(df.head(25), use_container_width=True)
            except Exception as e:
                st.error(f"فشل القراءة: {e}")

    with tab2:
        st.markdown(
            """
### المشروع على GitHub
- **الواجهة الكاملة:** مجلد `frontend/` — يُبنى بـ `npm run build`.
- **الخلفية:** مجلد `backend/` — تشغيل: `uvicorn app.main:app --host 0.0.0.0 --port 8000`.

### النشر الموصى به للنسخة الكاملة
1. ارفع **الخلفية** على [Render](https://render.com) أو Railway أو VPS وتشغيل `uvicorn`.
2. ارفع **الواجهة** كملفات ثابتة (Netlify / Cloudflare Pages) مع توجيه `/api` إلى الخادم.
3. أو استخدم حاوية Docker واحدة تجمع الاثنين.

### Streamlit Cloud وحده
ينفّذ **هذا الملف فقط** — لا يشغّل React ولا FastAPI تلقائياً. استخدمه للمعاينة السريعة أو كبوابة مع اختبار `API_URL` بعد نشر الـ API.
"""
        )


if __name__ == "__main__":
    main()
