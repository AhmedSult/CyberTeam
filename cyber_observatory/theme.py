from __future__ import annotations

from cyber_observatory.i18n import Lang, t


def inject_theme(lang: Lang, mode: str) -> None:
    import streamlit as st

    rtl = "rtl" if lang == "ar" else "ltr"
    align = "right" if lang == "ar" else "left"
    dark = mode == "dark"

    if dark:
        bg = "#0b1220"
        bg_grad = "linear-gradient(180deg, #0b1220 0%, #0f172a 100%)"
        card = "#111c2f"
        card_alt = "#152135"
        text = "#e7eef9"
        muted = "#9aa6bd"
        border = "#26334d"
        primary = "#10b981"
        primary_dark = "#059669"
        hero_grad = "linear-gradient(125deg, #042f2e 0%, #064e3b 35%, #047857 100%)"
        chip = "#1e293b"
    else:
        bg = "#f5f8f6"
        bg_grad = "linear-gradient(180deg, #f5f8f6 0%, #ffffff 100%)"
        card = "#ffffff"
        card_alt = "#f7faf8"
        text = "#0f2f23"
        muted = "#5b6b65"
        border = "#dde7e0"
        primary = "#0a7c5a"
        primary_dark = "#066047"
        hero_grad = "linear-gradient(125deg, #03342a 0%, #0a7c5a 60%, #16a34a 100%)"
        chip = "#eef4f0"

    st.markdown(
        f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="st"] {{
    font-family: 'Tajawal', 'Inter', system-ui, -apple-system, sans-serif !important;
}}

.stApp {{
    direction: {rtl};
    text-align: {align};
    background: {bg_grad};
    color: {text};
}}

[data-testid="stHeader"], div[data-testid="stToolbar"] {{ direction: ltr; }}

section[data-testid="stSidebar"] {{ display: none !important; }}
[data-testid="collapsedControl"] {{ display: none !important; }}

.block-container {{
    padding-top: 1.2rem !important;
    padding-bottom: 3rem !important;
    max-width: 1200px;
}}

/* Top navigation bar */
.topnav-wrap {{
    background: {card};
    border: 1px solid {border};
    border-radius: 14px;
    padding: 0.45rem 0.7rem;
    margin: 0.6rem 0 1rem 0;
    box-shadow: 0 1px 2px rgba(0,0,0,0.03);
}}
.topnav-wrap .stButton>button {{
    border-radius: 10px !important;
    font-weight: 600 !important;
    padding: 0.45rem 0.9rem !important;
    border: 1px solid {border} !important;
    background: {card_alt} !important;
    color: {text} !important;
    transition: all .18s ease;
}}
.topnav-wrap .stButton>button:hover {{
    border-color: {primary} !important;
    color: {primary_dark} !important;
}}
.topnav-wrap .stButton>button[kind="primary"] {{
    background: {primary} !important;
    border-color: {primary} !important;
    color: #ffffff !important;
}}

/* Hero */
.hero {{
    border-radius: 18px;
    padding: 1.4rem 1.6rem;
    background: {hero_grad};
    color: #ffffff;
    box-shadow: 0 12px 30px rgba(0, 80, 60, 0.18);
    margin-bottom: 1.1rem;
}}
.hero h1 {{
    margin: 0 0 0.3rem 0;
    font-size: 1.55rem;
    font-weight: 800;
}}
.hero p {{
    margin: 0;
    opacity: 0.92;
    font-size: 1rem;
}}
.hero .badge {{
    display: inline-block;
    margin-top: 0.6rem;
    background: rgba(255,255,255,0.16);
    padding: 0.28rem 0.6rem;
    border-radius: 8px;
    font-size: 0.78rem;
    letter-spacing: 0.02em;
    border: 1px solid rgba(255,255,255,0.22);
}}

/* Metrics */
[data-testid="stMetric"] {{
    background: {card};
    border: 1px solid {border};
    border-radius: 14px;
    padding: 1rem 1.1rem;
    box-shadow: 0 1px 2px rgba(0,0,0,0.03);
}}
[data-testid="stMetricValue"] {{
    color: {primary_dark} !important;
    font-weight: 800 !important;
}}
[data-testid="stMetricLabel"] {{ color: {muted} !important; }}

/* Cards/sections */
.section-card {{
    background: {card};
    border: 1px solid {border};
    border-radius: 14px;
    padding: 1rem 1.1rem;
    margin: 0.7rem 0;
}}
.section-title {{
    font-size: 1.05rem;
    font-weight: 700;
    margin: 0 0 0.6rem 0;
    color: {text};
}}

/* Inputs */
[data-baseweb="input"] input,
[data-baseweb="select"]>div,
.stTextInput input, .stSelectbox div[data-baseweb="select"]>div {{
    border-radius: 10px !important;
    background: {card_alt} !important;
}}

/* Chat */
[data-testid="stChatMessage"] {{
    background: {card};
    border: 1px solid {border};
    border-radius: 12px;
    padding: 0.85rem 1rem;
    margin: 0.4rem 0;
}}
.stChatInput textarea {{
    border-radius: 12px !important;
    background: {card_alt} !important;
}}

/* Dataframe */
[data-testid="stDataFrame"] {{
    border: 1px solid {border} !important;
    border-radius: 12px;
    overflow: hidden;
}}

/* Badges */
.chip {{
    display: inline-block;
    padding: 0.18rem 0.5rem;
    border-radius: 999px;
    font-size: 0.78rem;
    background: {chip};
    color: {text};
    border: 1px solid {border};
}}
.chip.success {{ color: #047857; border-color: #a7f3d0; background: #ecfdf5; }}
.chip.warn {{ color: #92400e; border-color: #fde68a; background: #fffbeb; }}
.chip.danger {{ color: #991b1b; border-color: #fecaca; background: #fef2f2; }}

/* Plotly container */
[data-testid="stPlotlyChart"] {{
    background: {card};
    border: 1px solid {border};
    border-radius: 14px;
    padding: 0.4rem 0.5rem;
}}

/* Buttons (default outside topnav) */
.stButton>button {{ border-radius: 10px !important; font-weight: 600 !important; }}
.stDownloadButton>button {{ border-radius: 10px !important; }}

/* Status bar */
.status-bar {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: {card_alt};
    border: 1px dashed {border};
    border-radius: 10px;
    padding: 0.5rem 0.8rem;
    color: {muted};
    font-size: 0.85rem;
    margin-bottom: 0.8rem;
}}
</style>
""",
        unsafe_allow_html=True,
    )


def hero_html(lang: Lang) -> str:
    badge = "Cybersecurity Compliance · NCA · ECC" if lang == "en" else "امتثال سيبراني · NCA · ECC"
    return f"""
<section class="hero">
  <h1>{t(lang, "title")}</h1>
  <p>{t(lang, "subtitle")}</p>
  <span class="badge">{badge}</span>
</section>
"""
