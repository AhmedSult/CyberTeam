from __future__ import annotations

from cyber_observatory.i18n import Lang, t


def inject_theme(lang: Lang, mode: str) -> None:
    import streamlit as st

    rtl = "rtl" if lang == "ar" else "ltr"
    align = "right" if lang == "ar" else "left"
    dark = mode == "dark"
    bg = "#0f172a" if dark else "#f3f8f5"
    card = "#1e293b" if dark else "#ffffff"
    text = "#f8fafc" if dark else "#0f2f23"
    border = "#334155" if dark else "#d8e6de"

    st.markdown(
        f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;800&display=swap');
html, body, [class*="st"] {{ font-family: 'Tajawal', sans-serif !important; }}
.stApp {{ direction: {rtl}; text-align: {align}; background: {bg}; color: {text}; }}
[data-testid="stHeader"], div[data-testid="stToolbar"] {{ direction: ltr; }}
[data-testid="stSidebar"] {{ border-left: 1px solid {border} !important; }}
[data-testid="stMetric"] {{
  background: {card}; border: 1px solid {border}; border-radius: 12px; padding: .9rem;
}}
.hero {{
  border: 1px solid {border}; border-radius: 16px; padding: 1.2rem;
  background: linear-gradient(120deg, #002b49 0%, #007a4a 100%); color: #fff;
}}
</style>
""",
        unsafe_allow_html=True,
    )


def hero_html(lang: Lang) -> str:
    return f"""
<section class="hero">
  <h2 style="margin:0;">{t(lang, "title")}</h2>
  <p style="margin:.4rem 0 0 0;opacity:.95;">{t(lang, "subtitle")}</p>
</section>
"""

