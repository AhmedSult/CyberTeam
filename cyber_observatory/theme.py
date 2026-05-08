from __future__ import annotations

from cyber_observatory.i18n import Lang, t


def inject_theme(lang: Lang, mode: str) -> None:
    import streamlit as st

    rtl = "rtl" if lang == "ar" else "ltr"
    align = "right" if lang == "ar" else "left"
    dark = mode == "dark"

    if dark:
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
        nav_bg = "#0f1a2e"
        menu_hover = "rgba(16, 185, 129, 0.08)"
    else:
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
        nav_bg = "#ffffff"
        menu_hover = "rgba(10, 124, 90, 0.08)"

    st.markdown(
        f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700&display=swap');

/* ===== Unified font for the entire app (incl. popovers, dialogs, editors) ===== */
:root {{
    --app-font: 'Tajawal', 'Inter', system-ui, -apple-system, 'Segoe UI', sans-serif;
}}

html, body, .stApp,
.stApp *:not([data-testid="stIconMaterial"]):not(.material-icons):not(.material-symbols-rounded):not(.material-symbols-outlined):not([class*="material-symbols"]):not(i) {{
    font-family: var(--app-font) !important;
}}

/* Streamlit popover content lives in a portal outside .stApp — target globally */
[data-testid="stPopover"], [data-testid="stPopoverBody"],
[data-testid="stPopover"] *, [data-testid="stPopoverBody"] *,
[data-baseweb="popover"], [data-baseweb="popover"] *,
[data-baseweb="menu"], [data-baseweb="menu"] *,
[data-baseweb="select"], [data-baseweb="select"] *,
[data-baseweb="select-dropdown"], [data-baseweb="select-dropdown"] *,
[role="listbox"], [role="listbox"] *,
[role="option"], [role="option"] *,
[role="menuitem"], [role="menuitem"] *,
[data-testid="stDialog"], [data-testid="stDialog"] *,
[data-testid="stModal"], [data-testid="stModal"] *,
[data-testid="stTooltipContent"], [data-testid="stTooltipContent"] *,
[data-testid="stDataFrame"], [data-testid="stDataFrame"] *,
[data-testid="stDataEditor"], [data-testid="stDataEditor"] *,
.stChatFloatingInputContainer, .stChatFloatingInputContainer *,
.stChatMessage, .stChatMessage *,
.stTabs, .stTabs *,
.stMarkdown, .stMarkdown *,
input, textarea, select, button, optgroup, option {{
    font-family: var(--app-font) !important;
}}

/* Glide data grid (st.dataframe / st.data_editor) overrides */
.glideDataEditor, .glideDataEditor * {{
    font-family: var(--app-font) !important;
}}

/* Material icons must keep their own font */
[data-testid="stIconMaterial"],
.material-icons, .material-symbols-rounded, .material-symbols-outlined,
[class*="material-symbols"] {{
    font-family: 'Material Symbols Rounded', 'Material Icons', 'Material Symbols Outlined' !important;
    font-feature-settings: 'liga' !important;
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
    padding-top: 1rem !important;
    padding-bottom: 3rem !important;
    padding-left: 1.6rem !important;
    padding-right: 1.6rem !important;
    max-width: 100% !important;
}}

/* ===== Top Navigation Bar — full width ===== */
.topnav-wrap {{
    background: {nav_bg};
    border: 1px solid {border};
    border-radius: 14px;
    padding: 0.55rem 0.9rem;
    margin: 0.4rem 0 1rem 0;
    box-shadow: 0 2px 6px rgba(0,0,0,0.04);
    position: sticky;
    top: 0.5rem;
    z-index: 99;
    width: 100%;
}}
.topnav-wrap [data-testid="stHorizontalBlock"] {{ gap: 0.45rem !important; }}
.topnav-wrap [data-testid="stHorizontalBlock"] {{ align-items: center; }}

/* Buttons inside top nav (menu items) */
.topnav-wrap .stButton>button {{
    border-radius: 10px !important;
    font-weight: 600 !important;
    padding: 0.42rem 0.85rem !important;
    border: 1px solid transparent !important;
    background: transparent !important;
    color: {text} !important;
    transition: all .18s ease;
    white-space: nowrap !important;
}}
.topnav-wrap .stButton>button:hover {{
    background: {menu_hover} !important;
    border-color: {border} !important;
    color: {primary_dark} !important;
}}
.topnav-wrap .stButton>button[kind="primary"] {{
    background: {primary} !important;
    border-color: {primary} !important;
    color: #ffffff !important;
}}

/* Popover (dropdown menu) trigger */
.topnav-wrap [data-testid="stPopover"] button {{
    border-radius: 10px !important;
    font-weight: 600 !important;
    padding: 0.42rem 0.85rem !important;
    border: 1px solid transparent !important;
    background: transparent !important;
    color: {text} !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
}}
.topnav-wrap [data-testid="stPopover"] button:hover {{
    background: {menu_hover} !important;
    border-color: {border} !important;
}}
/* small chevron icon in popover trigger */
.topnav-wrap [data-testid="stPopover"] [data-testid="stIconMaterial"] {{
    font-size: 1.05rem !important;
    margin: 0 0.15rem !important;
    color: {muted} !important;
}}

/* Popover panel content (dropdown items) */
[data-testid="stPopoverBody"] {{
    padding: 0.4rem !important;
    min-width: 240px;
    background: {card} !important;
    border: 1px solid {border} !important;
    border-radius: 12px !important;
    box-shadow: 0 14px 30px rgba(0,0,0,0.10) !important;
}}
[data-testid="stPopoverBody"] .stButton>button {{
    width: 100% !important;
    text-align: {align} !important;
    border: 0 !important;
    background: transparent !important;
    padding: 0.55rem 0.7rem !important;
    color: {text} !important;
    font-weight: 500 !important;
    border-radius: 8px !important;
}}
[data-testid="stPopoverBody"] .stButton>button:hover {{
    background: {menu_hover} !important;
    color: {primary_dark} !important;
}}
[data-testid="stPopoverBody"] .stButton>button[kind="primary"] {{
    background: {menu_hover} !important;
    color: {primary_dark} !important;
    font-weight: 700 !important;
}}
[data-testid="stPopoverBody"] a {{
    display: block;
    padding: 0.55rem 0.7rem;
    border-radius: 8px;
    color: {text};
    text-decoration: none;
    font-weight: 500;
}}
[data-testid="stPopoverBody"] a:hover {{
    background: {menu_hover};
    color: {primary_dark};
}}
[data-testid="stPopoverBody"] hr {{ margin: 0.3rem 0; border-color: {border}; }}

/* ===== Hero ===== */
.hero {{
    border-radius: 18px;
    padding: 1.5rem 2rem;
    background: {hero_grad};
    color: #ffffff;
    box-shadow: 0 12px 30px rgba(0, 80, 60, 0.18);
    margin-bottom: 0.9rem;
    width: 100%;
}}
.hero h1 {{ margin: 0 0 0.3rem 0; font-size: 1.55rem; font-weight: 800; }}
.hero p {{ margin: 0; opacity: 0.92; font-size: 1rem; }}
.hero .badge {{
    display: inline-block;
    margin-top: 0.6rem;
    background: rgba(255,255,255,0.16);
    padding: 0.28rem 0.6rem;
    border-radius: 8px;
    font-size: 0.78rem;
    border: 1px solid rgba(255,255,255,0.22);
}}

/* ===== Login screen ===== */
.login-wrap {{
    max-width: 480px;
    margin: 2.5rem auto 0 auto;
    background: {card};
    border: 1px solid {border};
    border-radius: 18px;
    padding: 2rem 1.8rem;
    box-shadow: 0 18px 40px rgba(0,0,0,0.08);
}}
.login-logo {{
    text-align: center;
    margin-bottom: 1rem;
}}
.login-logo .icon {{
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 64px; height: 64px;
    border-radius: 16px;
    background: {hero_grad};
    color: #fff;
    font-size: 1.8rem;
    margin-bottom: 0.6rem;
    box-shadow: 0 8px 20px rgba(0,80,60,0.18);
}}
.login-logo h2 {{ margin: 0; font-size: 1.4rem; font-weight: 800; color: {text}; }}
.login-logo p  {{ margin: 0.25rem 0 0; color: {muted}; font-size: 0.92rem; }}
.login-demo {{
    margin-top: 0.8rem;
    padding: 0.7rem 0.9rem;
    background: {card_alt};
    border: 1px dashed {border};
    border-radius: 10px;
    color: {muted};
    font-size: 0.86rem;
}}
.login-demo b {{ color: {text}; }}

/* ===== Metrics ===== */
[data-testid="stMetric"] {{
    background: {card};
    border: 1px solid {border};
    border-radius: 14px;
    padding: 1rem 1.1rem;
    box-shadow: 0 1px 2px rgba(0,0,0,0.03);
}}
[data-testid="stMetricValue"] {{ color: {primary_dark} !important; font-weight: 800 !important; }}
[data-testid="stMetricLabel"] {{ color: {muted} !important; }}

/* ===== Sections ===== */
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
    margin: 0.4rem 0 0.6rem 0;
    color: {text};
}}
.page-title {{
    font-size: 1.35rem;
    font-weight: 800;
    margin: 0 0 0.2rem 0;
    color: {text};
}}
.page-caption {{
    color: {muted};
    margin: 0 0 1rem 0;
    font-size: 0.95rem;
}}
.hint-box {{
    background: {card_alt};
    border: 1px solid {border};
    border-inline-start: 4px solid {primary};
    border-radius: 12px;
    padding: 0.85rem 1rem;
    margin: 0 0 1rem 0;
    color: {text};
    font-size: 0.92rem;
    line-height: 1.7;
}}
.hint-box b {{ color: {primary}; }}
.hint-box ol {{ color: {text}; }}

/* ===== Inputs ===== */
[data-baseweb="input"] input,
[data-baseweb="select"]>div,
.stTextInput input, .stSelectbox div[data-baseweb="select"]>div {{
    border-radius: 10px !important;
    background: {card_alt} !important;
}}

/* ===== Chat ===== */
[data-testid="stChatMessage"] {{
    background: {card};
    border: 1px solid {border};
    border-radius: 12px;
    padding: 0.85rem 1rem;
    margin: 0.4rem 0;
}}
.stChatInput textarea {{ border-radius: 12px !important; background: {card_alt} !important; }}

/* ===== Dataframe ===== */
[data-testid="stDataFrame"] {{
    border: 1px solid {border} !important;
    border-radius: 12px;
    overflow: hidden;
}}

/* ===== Chips / badges ===== */
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
.chip.warn    {{ color: #92400e; border-color: #fde68a; background: #fffbeb; }}
.chip.danger  {{ color: #991b1b; border-color: #fecaca; background: #fef2f2; }}

/* ===== Plotly ===== */
[data-testid="stPlotlyChart"] {{
    background: {card};
    border: 1px solid {border};
    border-radius: 14px;
    padding: 0.4rem 0.5rem;
}}

/* ===== Buttons / Downloads ===== */
.stButton>button {{ border-radius: 10px !important; font-weight: 600 !important; }}
.stDownloadButton>button {{ border-radius: 10px !important; font-weight: 600 !important; }}

/* ===== Status bar ===== */
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

/* ===== Link cards (for the Links menu page) ===== */
.link-card {{
    display: flex;
    flex-direction: column;
    gap: 0.2rem;
    background: {card};
    border: 1px solid {border};
    border-radius: 14px;
    padding: 1rem 1.1rem;
    margin: 0.4rem 0;
    transition: all .15s ease;
    text-decoration: none !important;
    color: {text} !important;
}}
.link-card:hover {{
    transform: translateY(-1px);
    border-color: {primary};
    box-shadow: 0 8px 18px rgba(10, 124, 90, 0.12);
}}
.link-card .lc-title {{ font-weight: 700; color: {text}; }}
.link-card .lc-desc  {{ font-size: 0.86rem; color: {muted}; }}

/* ===== Footer ===== */
.app-footer {{
    margin-top: 2rem;
    padding: 0.9rem 1rem;
    border-top: 1px solid {border};
    color: {muted};
    font-size: 0.82rem;
    text-align: center;
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
