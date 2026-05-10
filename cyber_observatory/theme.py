from __future__ import annotations

import html as html_module

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
.hero-row {{
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 1rem;
    flex-wrap: wrap;
}}
.hero-text {{ flex: 1 1 280px; min-width: 0; }}
.hero-user-wrap {{ flex-shrink: 0; }}
.hero-user-chip {{
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    background: rgba(255,255,255,0.18);
    border: 1px solid rgba(255,255,255,0.28);
    padding: 0.38rem 0.75rem;
    border-radius: 999px;
    font-size: 0.82rem;
    font-weight: 600;
    max-width: 220px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
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

/* ----- Login page (hero + form column card) ----- */
.login-top-bar {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 0.55rem;
    margin: 0 0 0.35rem 0;
    padding: 0.2rem 0 0.55rem 0;
    border-bottom: 1px solid {border};
}}
.login-brand-mini {{
    font-weight: 800;
    font-size: 1.06rem;
    color: {text};
    letter-spacing: -0.02em;
}}
.login-hero-banner {{
    border-radius: 20px;
    padding: 2rem 1.75rem 2.4rem;
    background: {hero_grad};
    color: #fff;
    margin: 0.45rem 0 0 0;
    box-shadow: 0 14px 38px rgba(0, 80, 60, 0.2);
    position: relative;
    overflow: hidden;
}}
.login-hero-banner::before {{
    content: "";
    position: absolute;
    inset: 0;
    background:
        radial-gradient(ellipse 70% 55% at 15% 85%, rgba(255,255,255,0.14) 0%, transparent 55%),
        radial-gradient(ellipse 50% 45% at 90% 15%, rgba(255,255,255,0.1) 0%, transparent 50%);
    pointer-events: none;
}}
.login-hero-inner {{ position: relative; z-index: 1; max-width: 640px; }}
.login-hero-banner h1 {{
    margin: 0 0 0.3rem 0;
    font-size: clamp(1.35rem, 3.5vw, 1.75rem);
    font-weight: 800;
    line-height: 1.25;
    letter-spacing: -0.02em;
}}
.login-hero-banner p.login-tagline {{
    margin: 0 0 1rem 0;
    opacity: 0.95;
    font-size: 0.96rem;
    line-height: 1.65;
}}
.login-hero-features {{
    list-style: none;
    margin: 0;
    padding: 0;
    display: flex;
    flex-direction: column;
    gap: 0.42rem;
}}
.login-hero-features li {{
    display: flex;
    align-items: flex-start;
    gap: 0.5rem;
    font-size: 0.88rem;
    opacity: 0.96;
    line-height: 1.45;
}}
.login-hero-features .feat-ico {{ flex-shrink: 0; opacity: 0.95; font-size: 1rem; }}

.block-container:has(.login-hero-banner) {{
    padding-top: 0.65rem !important;
}}

.block-container:has(.login-hero-banner) [data-testid="stHorizontalBlock"] [data-testid="column"]:has([data-testid="stForm"]) {{
    background: {card};
    border: 1px solid {border};
    border-radius: 18px;
    padding: 1.5rem 1.35rem 1.2rem;
    box-shadow: 0 18px 44px rgba(0,0,0,0.09);
    margin-top: 0.85rem;
}}
.block-container:has(.login-hero-banner) [data-testid="stForm"] {{
    border: none !important;
    padding: 0 !important;
    background: transparent !important;
}}
.block-container:has(.login-hero-banner) [data-testid="stForm"] [data-testid="stFormSubmitButton"]>button {{
    border-radius: 12px !important;
    font-weight: 700 !important;
    padding: 0.55rem 1rem !important;
    min-height: 2.65rem;
}}

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

/* =============================================================
   Website Scanner — warm/beige palette inspired by NCA controls UI
   ============================================================= */
.scan-app {{
    --s-bg: #F7F6F2;
    --s-surface: #FFFFFF;
    --s-surface-2: #F1EFE8;
    --s-text: #2C2C2A;
    --s-text-2: #5F5E5A;
    --s-text-3: #888780;
    --s-border: rgba(0,0,0,0.10);
    --s-border-2: rgba(0,0,0,0.18);
    --s-info-bg: #E6F1FB;     --s-info-text: #0C447C;     --s-info-border: #378ADD;
    --s-success-bg: #EAF3DE;  --s-success-text: #3B6D11;  --s-success-strong: #639922;
    --s-warn-bg: #FAEEDA;     --s-warn-text: #854F0B;     --s-warn-strong: #BA7517;
    --s-danger-bg: #FCEBEB;   --s-danger-text: #791F1F;   --s-danger-strong: #E24B4A;
    --s-critical-bg: #F4DCDC; --s-critical-text: #5B1313; --s-critical-strong: #8E1A1A;
    --s-neutral-bg: #F1EFE8;  --s-neutral-text: #444441;
    background: var(--s-bg);
    color: var(--s-text);
    border-radius: 16px;
    padding: 18px;
    margin-top: 8px;
    border: 1px solid var(--s-border);
    direction: rtl;
}}
.scan-app * {{ box-sizing: border-box; }}

.scan-header {{
    background: var(--s-surface);
    border-radius: 12px;
    padding: 16px 18px;
    border: 1px solid var(--s-border);
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 12px;
    margin-bottom: 14px;
}}
.scan-header h2 {{
    font-size: 17px;
    font-weight: 700;
    color: var(--s-text);
    margin: 0;
    display: flex;
    align-items: center;
    gap: 10px;
}}
.scan-header .scan-logo {{
    width: 38px; height: 38px;
    background: var(--s-info-bg);
    color: var(--s-info-text);
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
}}
.scan-header .scan-meta {{
    color: var(--s-text-2);
    font-size: 12px;
    direction: ltr;
}}

.scan-stat-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 10px;
    margin-bottom: 14px;
}}
.scan-stat {{
    background: var(--s-surface);
    border: 1px solid var(--s-border);
    border-radius: 12px;
    padding: 12px 14px;
}}
.scan-stat .lbl {{ font-size: 12px; color: var(--s-text-2); margin-bottom: 4px; }}
.scan-stat .val {{ font-size: 24px; font-weight: 700; color: var(--s-text); }}
.scan-stat.score .val {{ color: var(--s-success-strong); }}
.scan-stat.score .grade {{
    display: inline-block;
    padding: 2px 10px;
    border-radius: 8px;
    background: var(--s-success-bg);
    color: var(--s-success-text);
    font-size: 13px;
    font-weight: 700;
    margin-inline-start: 6px;
}}
.scan-stat.score.warn .val {{ color: var(--s-warn-strong); }}
.scan-stat.score.warn .grade {{ background: var(--s-warn-bg); color: var(--s-warn-text); }}
.scan-stat.score.danger .val {{ color: var(--s-danger-strong); }}
.scan-stat.score.danger .grade {{ background: var(--s-danger-bg); color: var(--s-danger-text); }}
.scan-stat .progress {{
    height: 6px; background: rgba(0,0,0,0.06); border-radius: 4px;
    overflow: hidden; margin-top: 8px;
}}
.scan-stat .progress > div {{ height: 100%; border-radius: 4px; }}
.scan-stat.crit  .val {{ color: var(--s-critical-strong); }}
.scan-stat.high  .val {{ color: var(--s-danger-strong); }}
.scan-stat.med   .val {{ color: var(--s-warn-strong); }}
.scan-stat.low   .val {{ color: var(--s-text-2); }}
.scan-stat.ok    .val {{ color: var(--s-success-strong); }}

.scan-disclaimer {{
    background: var(--s-info-bg);
    color: var(--s-info-text);
    border-inline-start: 3px solid var(--s-info-border);
    padding: 10px 14px;
    border-radius: 10px;
    font-size: 13px;
    margin-bottom: 14px;
    line-height: 1.7;
}}

details.scan-domain {{
    background: var(--s-surface);
    border: 1px solid var(--s-border);
    border-radius: 12px;
    margin-bottom: 12px;
    overflow: hidden;
}}
details.scan-domain[open] {{
    box-shadow: 0 6px 18px rgba(0,0,0,0.05);
}}
details.scan-domain > summary {{
    list-style: none;
    cursor: pointer;
    padding: 14px 18px;
    background: var(--s-surface-2);
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
    user-select: none;
}}
details.scan-domain > summary::-webkit-details-marker {{ display: none; }}
details.scan-domain > summary:hover {{ background: #E8E5DC; }}
details.scan-domain .dom-title {{
    display: flex; align-items: center; gap: 10px;
    font-weight: 700; font-size: 15px; color: var(--s-text);
}}
details.scan-domain .dom-num {{
    background: var(--s-info-bg); color: var(--s-info-text);
    padding: 3px 10px; border-radius: 8px;
    font-size: 12px; font-weight: 700;
    min-width: 36px; text-align: center;
}}
details.scan-domain .dom-meta {{
    display: flex; gap: 6px; align-items: center; flex-wrap: wrap;
}}
.scan-pill {{
    display: inline-block; padding: 3px 9px; border-radius: 10px;
    font-size: 11px; font-weight: 600;
    background: var(--s-info-bg); color: var(--s-info-text);
}}
.scan-pill.crit {{ background: var(--s-critical-bg); color: var(--s-critical-text); }}
.scan-pill.high {{ background: var(--s-danger-bg);   color: var(--s-danger-text); }}
.scan-pill.med  {{ background: var(--s-warn-bg);     color: var(--s-warn-text); }}
.scan-pill.low  {{ background: var(--s-neutral-bg);  color: var(--s-neutral-text); }}
.scan-pill.ok   {{ background: var(--s-success-bg);  color: var(--s-success-text); }}
.scan-pill.info {{ background: var(--s-info-bg);     color: var(--s-info-text); }}

.scan-finding {{
    padding: 14px 18px;
    border-top: 1px solid var(--s-border);
    background: var(--s-surface);
}}
.scan-finding-head {{
    display: flex; justify-content: space-between; gap: 12px;
    align-items: flex-start; flex-wrap: wrap; margin-bottom: 8px;
}}
.scan-finding-head .ttl {{
    font-weight: 700; color: var(--s-text); font-size: 14px;
    line-height: 1.6;
}}
.scan-finding .desc {{
    color: var(--s-text-2); font-size: 13.5px; line-height: 1.75;
    margin: 0 0 10px 0;
}}
.scan-finding .fix-block {{
    background: var(--s-surface-2);
    border-inline-start: 3px solid var(--s-success-strong);
    padding: 10px 14px;
    border-radius: 10px;
    color: var(--s-text);
    font-size: 13px; line-height: 1.8;
    white-space: pre-wrap;
}}
.scan-finding .fix-label {{
    font-weight: 700; color: var(--s-success-text);
    margin-bottom: 4px; display: block;
}}
.scan-finding .evidence {{
    margin-top: 8px;
    background: #2C2C2A; color: #F7F6F2;
    border-radius: 8px;
    padding: 8px 12px;
    font-family: ui-monospace, "SF Mono", Menlo, monospace;
    font-size: 12px;
    direction: ltr;
    white-space: pre-wrap;
    word-break: break-all;
    max-height: 160px;
    overflow: auto;
}}
.scan-finding .ecc-tag {{
    display: inline-block;
    margin-top: 8px;
    background: var(--s-info-bg);
    color: var(--s-info-text);
    padding: 2px 9px;
    border-radius: 8px;
    font-size: 11px;
    font-weight: 600;
    direction: ltr;
}}

/* قابل للطي دون st.expander (يعمل داخل expander الفحص السريع) */
details.scan-quick-exploit {{
    margin: 10px 0;
    border: 1px solid var(--s-border-2);
    border-radius: 12px;
    background: var(--s-surface);
    padding: 6px 12px 10px;
}}
details.scan-quick-exploit summary {{
    cursor: pointer;
    font-weight: 700;
    color: var(--s-text-1);
    padding: 6px 2px;
    list-style-position: outside;
}}
details.scan-quick-exploit .scan-quick-body {{
    margin-top: 8px;
    padding-top: 10px;
    border-top: 1px solid var(--s-border-2);
    font-size: 13px;
    color: var(--s-text-2);
    line-height: 1.7;
}}
details.scan-quick-exploit .scan-quick-body strong {{
    color: var(--s-text-1);
}}
details.scan-quick-exploit pre {{
    margin: 8px 0 0 0;
    background: #2C2C2A;
    color: #F7F6F2;
    border-radius: 8px;
    padding: 10px 12px;
    font-family: ui-monospace, "SF Mono", Menlo, monospace;
    font-size: 12px;
    direction: ltr;
    white-space: pre-wrap;
    word-break: break-word;
    max-height: 280px;
    overflow: auto;
}}
details.scan-quick-exploit .impact-note {{
    background: var(--s-info-bg);
    color: var(--s-info-text);
    border-radius: 8px;
    padding: 10px 12px;
    margin: 8px 0;
    font-size: 13px;
}}

.scan-empty {{
    text-align: center;
    padding: 50px 20px;
    color: var(--s-text-3);
    font-size: 14px;
    background: var(--s-surface);
    border-radius: 12px;
    border: 1px dashed var(--s-border-2);
}}

/* =============================================================
   Compliance Browser (.cb-*) — same beige palette,
   replicates the HTML reference: stat grid, domain cards,
   control items with status badges and inline detail panel.
   ============================================================= */
:root {{
    --cb-bg: #F7F6F2;
    --cb-surface: #FFFFFF;
    --cb-surface-2: #F1EFE8;
    --cb-text: #2C2C2A;
    --cb-text-2: #5F5E5A;
    --cb-text-3: #888780;
    --cb-border: rgba(0,0,0,0.10);
    --cb-border-2: rgba(0,0,0,0.18);
    --cb-info-bg: #E6F1FB;
    --cb-info-text: #0C447C;
    --cb-info-border: #378ADD;
    --cb-success-bg: #EAF3DE;
    --cb-success-text: #3B6D11;
    --cb-success-strong: #639922;
    --cb-warn-bg: #FAEEDA;
    --cb-warn-text: #854F0B;
    --cb-warn-strong: #BA7517;
    --cb-danger-bg: #FCEBEB;
    --cb-danger-text: #791F1F;
    --cb-danger-strong: #E24B4A;
    --cb-neutral-bg: #F1EFE8;
    --cb-neutral-text: #444441;
}}

/* Outer wrapper that turns the whole page beige */
.cb-page-wrap {{
    background: var(--cb-bg);
    border-radius: 16px;
    border: 1px solid var(--cb-border);
    padding: 18px;
    margin-top: 8px;
}}

/* Header card mirroring the HTML's .header */
.cb-header {{
    background: var(--cb-surface);
    border-radius: 12px;
    padding: 16px 22px;
    margin-bottom: 14px;
    border: 1px solid var(--cb-border);
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 12px;
}}
.cb-header h2 {{
    font-size: 17px;
    font-weight: 700;
    color: var(--cb-text);
    margin: 0;
    display: flex;
    align-items: center;
    gap: 10px;
}}
.cb-logo {{
    width: 38px; height: 38px;
    background: var(--cb-info-bg);
    color: var(--cb-info-text);
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
}}
.cb-version {{
    font-size: 12px; color: var(--cb-text-2); direction: ltr;
}}

/* ---- Stat grid (4 cards) ---- */
.cb-stat-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
    gap: 10px;
    margin-bottom: 14px;
}}
.cb-stat-card {{
    background: var(--cb-surface);
    border: 1px solid var(--cb-border);
    border-radius: 12px;
    padding: 12px 16px;
}}
.cb-stat-label {{ font-size: 12px; color: var(--cb-text-2); margin-bottom: 4px; }}
.cb-stat-val {{ font-size: 24px; font-weight: 700; color: var(--cb-text); }}
.cb-stat-val.success {{ color: var(--cb-success-strong); }}
.cb-stat-val.info    {{ color: var(--cb-info-text); }}
.cb-stat-val.warn    {{ color: var(--cb-warn-strong); }}
.cb-stat-val.danger  {{ color: var(--cb-danger-strong); }}
.cb-progress-bar {{
    height: 6px;
    background: rgba(0,0,0,0.06);
    border-radius: 4px;
    overflow: hidden;
    margin-top: 8px;
}}
.cb-progress-bar > div {{ height: 100%; border-radius: 4px; }}
.cb-pf-success {{ background: var(--cb-success-strong); }}
.cb-pf-info    {{ background: var(--cb-info-border); }}

/* ---- Domain cards via st.expander ---- */
.cb-page-wrap [data-testid="stExpander"] {{
    background: var(--cb-surface) !important;
    border: 1px solid var(--cb-border) !important;
    border-radius: 12px !important;
    margin-bottom: 12px !important;
    overflow: hidden !important;
    box-shadow: none !important;
}}
.cb-page-wrap [data-testid="stExpander"] details {{
    background: var(--cb-surface) !important;
}}
.cb-page-wrap [data-testid="stExpander"] summary {{
    background: var(--cb-surface-2) !important;
    padding: 14px 18px !important;
    cursor: pointer !important;
    color: var(--cb-text) !important;
    font-weight: 700 !important;
    font-size: 15px !important;
    border-bottom: 1px solid var(--cb-border) !important;
}}
.cb-page-wrap [data-testid="stExpander"] summary:hover {{
    background: #E8E5DC !important;
}}
.cb-page-wrap [data-testid="stExpander"] summary p {{
    color: var(--cb-text) !important;
    font-weight: 700 !important;
}}
.cb-page-wrap [data-testid="stExpander"] [data-testid="stExpanderDetails"] {{
    background: var(--cb-surface) !important;
    padding: 6px 14px 12px !important;
}}

/* Domain header pill (rendered inside summary via markdown) */
.cb-dom-num {{
    display: inline-block;
    background: var(--cb-info-bg);
    color: var(--cb-info-text);
    padding: 3px 10px;
    border-radius: 8px;
    font-size: 12px;
    font-weight: 700;
    min-width: 40px;
    text-align: center;
    margin-inline-end: 8px;
}}
.cb-pill-info {{
    display: inline-block;
    padding: 2px 9px;
    background: var(--cb-info-bg);
    color: var(--cb-info-text);
    border-radius: 10px;
    font-size: 11px;
    font-weight: 600;
    margin-inline-start: 8px;
}}

/* ---- Control row inside an expander ---- */
.cb-ctrl-row {{
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 12px;
    border-bottom: 1px solid var(--cb-border);
    border-radius: 8px;
}}
.cb-ctrl-row.selected {{
    background: var(--cb-info-bg);
}}
.cb-ctrl-row:hover {{ background: var(--cb-surface-2); }}
.cb-ctrl-code {{
    color: var(--cb-text-2);
    font-size: 12.5px;
    font-weight: 600;
    min-width: 60px;
    direction: ltr;
}}
.cb-ctrl-text {{
    flex: 1;
    color: var(--cb-text);
    font-size: 13.5px;
    line-height: 1.6;
}}

/* Streamlit columns inside expander — make them feel like a row */
.cb-page-wrap [data-testid="stExpander"] [data-testid="stHorizontalBlock"] {{
    align-items: center !important;
    border-bottom: 1px solid var(--cb-border) !important;
    padding: 8px 4px !important;
    margin: 0 !important;
}}
.cb-page-wrap [data-testid="stExpander"] [data-testid="stHorizontalBlock"]:hover {{
    background: var(--cb-surface-2) !important;
}}

/* Status badges (matches HTML reference) */
.cb-badge {{
    display: inline-block;
    font-size: 11px;
    padding: 3px 9px;
    border-radius: 8px;
    font-weight: 600;
    white-space: nowrap;
}}
.cb-b-applied  {{ background: var(--cb-success-bg);  color: var(--cb-success-text); }}
.cb-b-partial  {{ background: var(--cb-warn-bg);     color: var(--cb-warn-text); }}
.cb-b-required {{ background: var(--cb-danger-bg);   color: var(--cb-danger-text); }}
.cb-b-notapp   {{ background: var(--cb-neutral-bg);  color: var(--cb-neutral-text); }}
.cb-b-pending  {{ background: var(--cb-surface-2);   color: var(--cb-text-3); }}

/* Open detail button styled subtly */
.cb-page-wrap [data-testid="stExpander"] [data-testid="stHorizontalBlock"] .stButton > button {{
    border: 1px solid var(--cb-border-2) !important;
    background: var(--cb-surface) !important;
    color: var(--cb-text) !important;
    padding: 6px 10px !important;
    border-radius: 8px !important;
    font-size: 12px !important;
    font-weight: 600 !important;
    box-shadow: none !important;
}}
.cb-page-wrap [data-testid="stExpander"] [data-testid="stHorizontalBlock"] .stButton > button:hover {{
    background: var(--cb-info-bg) !important;
    border-color: var(--cb-info-border) !important;
    color: var(--cb-info-text) !important;
}}

/* Detail panel rendered inline below selected control */
.cb-detail-panel {{
    background: var(--cb-surface);
    border: 1px solid var(--cb-border-2);
    border-radius: 10px;
    padding: 14px 16px;
    margin: 8px 0 12px 0;
}}
.cb-guide-box {{
    background: var(--cb-surface-2);
    border-inline-start: 3px solid var(--cb-info-border);
    padding: 12px 14px;
    border-radius: 8px;
    font-size: 13px;
    line-height: 1.8;
    color: var(--cb-text);
    margin-bottom: 10px;
}}
.cb-guide-box b {{ color: var(--cb-info-text); }}

/* Status options (matches the four pills in HTML) */
.cb-page-wrap .cb-detail-panel [data-baseweb="radio"] label {{
    background: var(--cb-surface);
    border: 1px solid var(--cb-border);
    border-radius: 8px;
    padding: 8px 14px !important;
    margin: 4px !important;
}}

/* Admin summary table */
.cb-summary-wrap {{
    background: var(--cb-surface-2);
    border-radius: 10px;
    padding: 14px 16px;
    margin-bottom: 14px;
}}
.cb-summary-wrap h2 {{
    font-size: 15px;
    font-weight: 700;
    color: var(--cb-text);
    margin: 0 0 10px 0;
}}
.cb-summary-table {{
    width: 100%;
    border-collapse: collapse;
}}
.cb-summary-table th,
.cb-summary-table td {{
    padding: 10px 12px;
    text-align: right;
    font-size: 13px;
    border-bottom: 1px solid var(--cb-border);
    color: var(--cb-text);
}}
.cb-summary-table th {{
    background: var(--cb-surface);
    font-weight: 600;
    color: var(--cb-text-2);
    font-size: 12px;
}}
.cb-summary-table tr:hover td {{ background: var(--cb-surface); }}
.cb-mini-prog {{
    display: flex;
    align-items: center;
    gap: 8px;
    min-width: 130px;
}}
.cb-mini-prog .num {{ font-size: 12px; font-weight: 600; min-width: 36px; }}
.cb-mini-prog .bar {{
    flex: 1; height: 6px;
    background: rgba(0,0,0,0.08);
    border-radius: 3px; overflow: hidden;
}}
.cb-mini-prog .fill {{ height: 100%; border-radius: 3px; }}
.cb-mini-prog .count {{ font-size: 11px; color: var(--cb-text-2); }}
.cb-status-tag {{
    display: inline-block; padding: 3px 10px;
    border-radius: 8px; font-size: 11.5px; font-weight: 600;
}}

/* Department list cards in admin view */
.cb-dept-row {{
    background: var(--cb-surface-2);
    border-radius: 10px;
    padding: 12px 14px;
    margin-bottom: 8px;
    border: 1px solid var(--cb-border);
}}
.cb-dept-row-top {{
    display: flex; justify-content: space-between;
    align-items: center; margin-bottom: 6px;
}}
.cb-dept-name {{ font-weight: 700; font-size: 14px; color: var(--cb-text); }}
.cb-dept-meta {{ font-size: 11.5px; color: var(--cb-text-2); margin-bottom: 6px; }}

.cb-empty {{
    text-align: center;
    padding: 40px 20px;
    color: var(--cb-text-3);
    font-size: 13px;
    background: var(--cb-surface);
    border-radius: 12px;
    border: 1px dashed var(--cb-border-2);
}}

/* =============================================================
   Vulnerability Management Platform (.vm-*)
   ============================================================= */
.vm-platform {{
    background: var(--cb-bg);
    border-radius: 16px;
    border: 1px solid var(--cb-border);
    padding: 18px;
    margin-top: 8px;
}}

/* Top role banner */
.vm-banner {{
    background: linear-gradient(135deg, #2C2C2A 0%, #1a1a18 100%);
    color: #F7F6F2;
    border-radius: 14px;
    padding: 14px 20px;
    margin-bottom: 14px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 12px;
}}
.vm-banner-left {{
    display: flex; align-items: center; gap: 14px;
}}
.vm-banner-icon {{
    width: 44px; height: 44px; border-radius: 12px;
    background: rgba(255,255,255,0.10);
    display: flex; align-items: center; justify-content: center;
    font-size: 20px;
}}
.vm-banner-name {{ font-weight: 700; font-size: 16px; line-height: 1.2; }}
.vm-banner-meta {{ font-size: 12px; opacity: 0.78; margin-top: 2px; }}
.vm-banner-right {{
    display: flex; align-items: center; gap: 12px;
}}
.vm-role-tag {{
    background: rgba(255,255,255,0.12);
    color: #F7F6F2;
    padding: 5px 12px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 600;
}}
.vm-role-tag.super    {{ background: rgba(226,75,74,0.25); }}
.vm-role-tag.company  {{ background: rgba(99,153,34,0.25); }}
.vm-role-tag.member   {{ background: rgba(55,138,221,0.25); }}

/* KPI cards */
.vm-kpi-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
    gap: 10px;
    margin-bottom: 14px;
}}
.vm-kpi {{
    background: var(--cb-surface);
    border: 1px solid var(--cb-border);
    border-radius: 12px;
    padding: 14px 16px;
    position: relative;
    overflow: hidden;
}}
.vm-kpi-label {{ font-size: 12px; color: var(--cb-text-2); margin-bottom: 4px; }}
.vm-kpi-val {{ font-size: 26px; font-weight: 800; color: var(--cb-text); line-height: 1.1; }}
.vm-kpi-sub {{ font-size: 11.5px; color: var(--cb-text-3); margin-top: 4px; }}
.vm-kpi.crit .vm-kpi-val {{ color: var(--cb-critical-strong); }}
.vm-kpi.high .vm-kpi-val {{ color: var(--cb-danger-strong); }}
.vm-kpi.med  .vm-kpi-val {{ color: var(--cb-warn-strong); }}
.vm-kpi.success .vm-kpi-val {{ color: var(--cb-success-strong); }}
.vm-kpi.info .vm-kpi-val {{ color: var(--cb-info-text); }}

/* Score gauge */
.vm-score-gauge {{
    background: linear-gradient(135deg, #F7F6F2, #FFFFFF);
    border: 1px solid var(--cb-border);
    border-radius: 14px;
    padding: 20px 18px;
    text-align: center;
}}
.vm-score-num {{ font-size: 56px; font-weight: 800; line-height: 1; color: var(--cb-success-strong); }}
.vm-score-num.warn {{ color: var(--cb-warn-strong); }}
.vm-score-num.danger {{ color: var(--cb-danger-strong); }}
.vm-score-grade {{
    display: inline-block;
    margin-top: 6px;
    padding: 4px 14px;
    background: var(--cb-success-bg);
    color: var(--cb-success-text);
    border-radius: 10px;
    font-weight: 700;
    font-size: 14px;
}}
.vm-score-grade.warn {{ background: var(--cb-warn-bg); color: var(--cb-warn-text); }}
.vm-score-grade.danger {{ background: var(--cb-danger-bg); color: var(--cb-danger-text); }}
.vm-score-cap {{ font-size: 12px; color: var(--cb-text-2); margin-top: 8px; }}

/* Domain card */
.vm-domain-card {{
    background: var(--cb-surface);
    border: 1px solid var(--cb-border);
    border-radius: 12px;
    padding: 14px 16px;
    margin-bottom: 10px;
}}
.vm-domain-top {{
    display: flex; justify-content: space-between; align-items: center;
    flex-wrap: wrap; gap: 10px; margin-bottom: 6px;
}}
.vm-domain-name {{ font-weight: 700; font-size: 15px; color: var(--cb-text); }}
.vm-domain-meta {{ font-size: 12px; color: var(--cb-text-2); }}
.vm-tag {{
    display: inline-block;
    padding: 2px 9px;
    background: var(--cb-info-bg);
    color: var(--cb-info-text);
    border-radius: 999px;
    font-size: 11px;
    font-weight: 600;
    margin-inline-end: 4px;
}}
.vm-tag.warn   {{ background: var(--cb-warn-bg);    color: var(--cb-warn-text); }}
.vm-tag.danger {{ background: var(--cb-danger-bg);  color: var(--cb-danger-text); }}
.vm-tag.success {{ background: var(--cb-success-bg); color: var(--cb-success-text); }}
.vm-tag.neutral {{ background: var(--cb-neutral-bg); color: var(--cb-neutral-text); }}

/* Severity pill (vulnerability list) */
.vm-sev {{
    display: inline-block; padding: 3px 10px; border-radius: 8px;
    font-size: 11.5px; font-weight: 700; min-width: 60px; text-align: center;
}}
.vm-sev.critical {{ background: var(--cb-critical-bg); color: var(--cb-critical-text); }}
.vm-sev.high     {{ background: var(--cb-danger-bg);   color: var(--cb-danger-text); }}
.vm-sev.medium   {{ background: var(--cb-warn-bg);     color: var(--cb-warn-text); }}
.vm-sev.low      {{ background: var(--cb-neutral-bg);  color: var(--cb-neutral-text); }}
.vm-sev.info     {{ background: var(--cb-info-bg);     color: var(--cb-info-text); }}
.vm-sev.ok       {{ background: var(--cb-success-bg);  color: var(--cb-success-text); }}

/* Vulnerability detail */
.vm-vuln-card {{
    background: var(--cb-surface);
    border: 1px solid var(--cb-border);
    border-radius: 12px;
    padding: 14px 16px;
    margin-bottom: 10px;
}}
.vm-vuln-header {{
    display: flex; justify-content: space-between;
    align-items: flex-start; gap: 10px; margin-bottom: 10px;
    flex-wrap: wrap;
}}
.vm-vuln-title {{ font-weight: 700; font-size: 15px; color: var(--cb-text); }}
.vm-vuln-meta-row {{
    display: flex; gap: 6px; flex-wrap: wrap; margin: 6px 0 8px;
    font-size: 11.5px;
}}
.vm-meta-chip {{
    background: var(--cb-surface-2);
    color: var(--cb-text-2);
    padding: 2px 9px;
    border-radius: 8px;
    border: 1px solid var(--cb-border);
    direction: ltr;
}}
.vm-vuln-desc {{ color: var(--cb-text-2); font-size: 13.5px; line-height: 1.75; }}
.vm-vuln-fix {{
    margin-top: 10px;
    background: var(--cb-surface-2);
    border-inline-start: 3px solid var(--cb-success-strong);
    padding: 10px 14px; border-radius: 10px;
    color: var(--cb-text); font-size: 13px; line-height: 1.8;
    white-space: pre-wrap;
}}
.vm-vuln-fix b {{ color: var(--cb-success-text); }}
.vm-vuln-evidence {{
    margin-top: 8px;
    background: #2C2C2A; color: #F7F6F2;
    border-radius: 8px;
    padding: 8px 12px;
    font-family: ui-monospace, "SF Mono", Menlo, monospace;
    font-size: 12px;
    direction: ltr;
    white-space: pre-wrap;
    word-break: break-all;
    max-height: 160px;
    overflow: auto;
}}

/* Notification dropdown */
.vm-notif-item {{
    background: var(--cb-surface);
    border: 1px solid var(--cb-border);
    border-radius: 10px;
    padding: 10px 12px;
    margin-bottom: 6px;
    border-inline-start: 3px solid var(--cb-info-border);
}}
.vm-notif-item.unread {{ background: var(--cb-info-bg); }}
.vm-notif-item.critical {{ border-inline-start-color: var(--cb-critical-strong); }}
.vm-notif-item.warn {{ border-inline-start-color: var(--cb-warn-strong); }}
.vm-notif-item.success {{ border-inline-start-color: var(--cb-success-strong); }}
.vm-notif-title {{ font-weight: 700; font-size: 13.5px; color: var(--cb-text); }}
.vm-notif-body  {{ font-size: 12.5px; color: var(--cb-text-2); margin-top: 3px; line-height: 1.6; }}
.vm-notif-time  {{ font-size: 11px; color: var(--cb-text-3); margin-top: 4px; direction: ltr; }}

/* Subscription card */
.vm-plan-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 12px;
}}
.vm-plan {{
    background: var(--cb-surface);
    border: 1px solid var(--cb-border);
    border-radius: 14px;
    padding: 18px;
    position: relative;
}}
.vm-plan.current {{
    border-color: var(--cb-info-border);
    box-shadow: 0 0 0 3px rgba(55,138,221,0.10);
}}
.vm-plan-name {{ font-size: 18px; font-weight: 800; color: var(--cb-text); }}
.vm-plan-price {{ font-size: 22px; font-weight: 800; color: var(--cb-info-text); margin: 6px 0 10px; }}
.vm-plan-feat {{
    font-size: 13px; color: var(--cb-text-2);
    padding: 4px 0; line-height: 1.7;
    border-top: 1px dashed var(--cb-border);
}}
.vm-plan-feat:first-of-type {{ border-top: none; }}
.vm-plan-current-tag {{
    position: absolute; top: 12px;
    inset-inline-end: 12px;
    background: var(--cb-info-bg); color: var(--cb-info-text);
    padding: 3px 10px; border-radius: 999px;
    font-size: 11px; font-weight: 700;
}}

/* Quota progress */
.vm-quota {{
    background: var(--cb-surface-2);
    border: 1px solid var(--cb-border);
    border-radius: 10px;
    padding: 10px 14px;
    margin-bottom: 8px;
}}
.vm-quota-top {{
    display: flex; justify-content: space-between;
    font-size: 12.5px; color: var(--cb-text-2); margin-bottom: 4px;
}}
.vm-quota-bar {{
    height: 6px; background: rgba(0,0,0,0.06);
    border-radius: 4px; overflow: hidden;
}}
.vm-quota-fill {{ height: 100%; border-radius: 4px; }}

/* Section title for platform sub-views */
.vm-section-title {{
    display: flex; align-items: center; gap: 10px;
    font-size: 16px; font-weight: 700;
    color: var(--cb-text); margin: 4px 0 10px;
}}
.vm-section-title small {{ font-weight: 500; color: var(--cb-text-3); font-size: 12.5px; }}
.vm-divider {{ height: 1px; background: var(--cb-border); margin: 14px 0; }}

/* Empty state */
.vm-empty {{
    text-align: center; padding: 38px 20px;
    color: var(--cb-text-3); font-size: 13px;
    background: var(--cb-surface); border-radius: 12px;
    border: 1px dashed var(--cb-border-2);
}}

/* Make Streamlit tabs inside .vm-platform look beige + cybersecurity */
.vm-platform [data-baseweb="tab-list"] {{
    background: var(--cb-surface);
    border-radius: 10px !important;
    padding: 4px !important;
    border: 1px solid var(--cb-border) !important;
    gap: 4px !important;
}}
.vm-platform [data-baseweb="tab"] {{
    border-radius: 8px !important;
    padding: 8px 14px !important;
    color: var(--cb-text-2) !important;
    font-weight: 600 !important;
}}
.vm-platform [data-baseweb="tab"][aria-selected="true"] {{
    background: var(--cb-info-bg) !important;
    color: var(--cb-info-text) !important;
}}

/* Horizontal section nav (st.radio) — match tab pill style */
.vm-platform [data-testid="stRadio"] [role="radiogroup"] {{
    background: var(--cb-surface) !important;
    border-radius: 10px !important;
    padding: 4px !important;
    border: 1px solid var(--cb-border) !important;
    gap: 4px !important;
    flex-wrap: wrap !important;
}}
.vm-platform [data-testid="stRadio"] [role="radiogroup"] label {{
    border-radius: 8px !important;
    padding: 8px 14px !important;
    margin: 0 !important;
    font-weight: 600 !important;
    color: var(--cb-text-2) !important;
    border: 1px solid transparent !important;
    background: transparent !important;
}}
.vm-platform [data-testid="stRadio"] [role="radiogroup"] label:has(input:checked) {{
    background: var(--cb-info-bg) !important;
    color: var(--cb-info-text) !important;
    border-color: var(--cb-info-border) !important;
}}

/* AI insight box */
.vm-ai-card {{
    background: linear-gradient(135deg, #F7F6F2 0%, #E6F1FB 100%);
    border: 1px solid var(--cb-info-border);
    border-radius: 12px;
    padding: 14px 16px;
    margin: 8px 0;
}}
.vm-ai-card .ai-label {{
    font-size: 11.5px; font-weight: 700;
    color: var(--cb-info-text);
    letter-spacing: 0.5px;
    text-transform: uppercase;
    margin-bottom: 6px;
    display: inline-block;
}}
.vm-ai-card .ai-body {{
    font-size: 13.5px;
    color: var(--cb-text);
    line-height: 1.8;
    white-space: pre-wrap;
}}
</style>
""",
        unsafe_allow_html=True,
    )


def hero_html(lang: Lang, username: str = "") -> str:
    badge = "Cybersecurity Compliance · NCA · ECC" if lang == "en" else "امتثال سيبراني · NCA · ECC"
    user_block = ""
    if username:
        safe = html_module.escape(str(username))
        user_block = (
            f'<div class="hero-user-wrap"><span class="hero-user-chip" '
            f'title="{safe}">👤 {safe}</span></div>'
        )
    return f"""
<section class="hero">
  <div class="hero-row">
    <div class="hero-text">
      <h1>{t(lang, "title")}</h1>
      <p>{t(lang, "subtitle")}</p>
      <span class="badge">{badge}</span>
    </div>
    {user_block}
  </div>
</section>
"""
