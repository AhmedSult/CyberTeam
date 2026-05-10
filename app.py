from __future__ import annotations

import io
import os
from datetime import date, datetime
from typing import Iterator

import pandas as pd
import plotly.express as px
import streamlit as st

from cyber_observatory.ai_prompts import (
    ECC_PDF_URL,
    NCA_OFFICIAL_URL,
    chat_system_prompt,
)
from cyber_observatory.demo_data import (
    MATURITY_LABELS,
    PRIORITIES,
    RISK_LEVELS,
    STATUSES,
    calc_stats,
    domains_order,
    maturity_by_domain,
    seed_audit_log,
    seed_controls,
    seed_departments,
    seed_frameworks,
    seed_records,
)
from cyber_observatory.i18n import Lang, t
from cyber_observatory.theme import hero_html, inject_theme
from cyber_observatory.widgets import (
    RISK_LABEL_AR,
    STATUS_LABEL_AR,
    maturity_meter,
    risk_badge,
    status_badge,
)

ECC_IMPLEMENTATION_GUIDE_URL = (
    "https://cdn.nca.gov.sa/api/files/public/upload/"
    "1d3a5d95-3c0e-495f-8aa1-d7f288c5a856_Guide-to-Essential-Cybersecurity-Controls-Implementation-ar.pdf"
)

DEMO_USERS = {
    "admin": "admin",
    "admin@example.com": "admin",
    "auditor": "auditor",
}

PAGE_LABELS = {
    "overview":      "page_overview",
    "kpis":          "page_kpis",
    "reports":       "page_reports",
    "records":       "page_records",
    "gaps":          "page_gaps",
    "action_plan":   "page_action_plan",
    "risk_register": "page_risk_register",
    "maturity":      "page_maturity",
    "audit_log":     "page_audit_log",
    "import":        "page_import",
    "frameworks":    "page_frameworks",
    "controls":      "page_controls",
    "ecc":           "page_ecc",
    "departments":   "page_departments",
    "control_codes": "page_control_codes",
    "preferences":   "page_preferences",
    "assistant":     "menu_assistant",
    "scanner":       "page_scanner",
    "compliance_browser": "page_compliance_browser",
}


# =========================================================================
#  State
# =========================================================================
def _init_state() -> None:
    st.session_state.setdefault("authenticated", False)
    st.session_state.setdefault("user", "")
    st.session_state.setdefault("lang", "ar")
    st.session_state.setdefault("theme", "light")
    st.session_state.setdefault("nav", "overview")
    st.session_state.setdefault("chat", [])
    st.session_state.setdefault("framework_id", "")
    st.session_state.setdefault("department_id", "")
    st.session_state.setdefault("status_filter", "")
    st.session_state.setdefault("risk_filter", "")
    st.session_state.setdefault("table_search", "")
    st.session_state.setdefault("gap_summary", "")
    st.session_state.setdefault("active_record_id", None)
    st.session_state.setdefault("scanner_url", "")
    st.session_state.setdefault("scanner_result", None)
    st.session_state.setdefault("scanner_error", "")
    st.session_state.setdefault("cb_dept_id", "")
    st.session_state.setdefault("cb_active_record", None)
    if "frameworks_df" not in st.session_state:
        st.session_state.frameworks_df = seed_frameworks()
    if "departments_df" not in st.session_state:
        st.session_state.departments_df = seed_departments()
    if "controls_df" not in st.session_state:
        st.session_state.controls_df = seed_controls()
    if "records_df" not in st.session_state:
        st.session_state.records_df = seed_records()
    if "audit_df" not in st.session_state:
        st.session_state.audit_df = seed_audit_log()


def _restore_session_from_url() -> None:
    """يحفظ تسجيل الدخول والصفحة في query params حتى لا يضيع عند تحديث الصفحة."""
    qp = st.query_params
    if not st.session_state.authenticated:
        u = (qp.get("u") or "").strip().lower()
        if u and u in DEMO_USERS:
            st.session_state.authenticated = True
            st.session_state.user = u
    page = qp.get("p")
    if page and page in PAGES:
        st.session_state.nav = page
    lang = qp.get("l")
    if lang in ("ar", "en"):
        st.session_state.lang = lang


def _persist_session_to_url() -> None:
    """يكتب الحالة الحالية إلى query params (تظل عبر تحديث الصفحة)."""
    if st.session_state.authenticated and st.session_state.user:
        st.query_params["u"] = st.session_state.user
        st.query_params["p"] = st.session_state.nav
        st.query_params["l"] = st.session_state.lang
    else:
        for k in ("u", "p", "l"):
            if k in st.query_params:
                del st.query_params[k]


def _go(page: str) -> None:
    st.session_state.nav = page
    st.query_params["p"] = page
    st.rerun()


def _audit(action: str, entity: str, entity_id: int | str, details: str) -> None:
    df = st.session_state.audit_df.copy()
    df.loc[len(df)] = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user": st.session_state.user or "—",
        "action": action,
        "entity": entity,
        "entity_id": str(entity_id),
        "details": details,
    }
    st.session_state.audit_df = df


# =========================================================================
#  Login
# =========================================================================
def _login_page(lang: Lang) -> None:
    st.markdown('<div class="login-wrap">', unsafe_allow_html=True)
    st.markdown(
        f"""
<div class="login-logo">
  <div class="icon">🛡️</div>
  <h2>{t(lang, "title")}</h2>
  <p>{t(lang, "login_caption")}</p>
</div>
""",
        unsafe_allow_html=True,
    )
    with st.form("login_form", clear_on_submit=False):
        email = st.text_input(t(lang, "login_email"), key="login_email")
        password = st.text_input(t(lang, "login_password"), type="password", key="login_password")
        c1, c2 = st.columns([1, 1])
        with c1:
            st.checkbox(t(lang, "login_remember"), value=True, key="login_remember")
        with c2:
            st.selectbox(
                t(lang, "language"),
                options=["ar", "en"],
                key="lang",
                format_func=lambda v: "العربية" if v == "ar" else "English",
            )
        submitted = st.form_submit_button(t(lang, "login_submit"), type="primary", use_container_width=True)
        if submitted:
            uid = (email or "").strip().lower()
            ok = uid in DEMO_USERS and DEMO_USERS[uid] == (password or "")
            if ok:
                st.session_state.authenticated = True
                st.session_state.user = uid
                st.session_state.nav = "overview"
                st.query_params["u"] = uid
                st.query_params["p"] = "overview"
                st.query_params["l"] = st.session_state.lang
                _audit("login", "user", uid, "تسجيل دخول ناجح")
                st.rerun()
            else:
                st.error(t(lang, "login_invalid"))
    st.markdown(
        f'<div class="login-demo"><b>{t(lang, "login_demo")}:</b> {t(lang, "login_demo_value")}</div>',
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)


# =========================================================================
#  Top navigation
# =========================================================================
def _menu_button(lang: Lang, page: str, label_key: str) -> None:
    label = t(lang, label_key)
    is_active = st.session_state.nav == page
    if st.button(
        label,
        key=f"menu_{page}_{label_key}",
        use_container_width=True,
        type="primary" if is_active else "secondary",
    ):
        _go(page)


def _top_nav(lang: Lang) -> None:
    st.markdown('<div class="topnav-wrap">', unsafe_allow_html=True)
    cols = st.columns([2.0, 1.2, 1.1, 1.05, 1.1, 1.3, 1.3, 1.0, 1.4], gap="small")

    with cols[0]:
        if st.button(f"🛡️ {t(lang, 'title')}", key="brand_home", use_container_width=True):
            _go("overview")

    with cols[1]:
        with st.popover(t(lang, "menu_dashboard"), use_container_width=True):
            _menu_button(lang, "overview", "page_overview")
            _menu_button(lang, "kpis", "page_kpis")
            _menu_button(lang, "maturity", "page_maturity")
            _menu_button(lang, "reports", "page_reports")

    with cols[2]:
        with st.popover(t(lang, "menu_compliance"), use_container_width=True):
            _menu_button(lang, "compliance_browser", "menu_compliance_browser")
            _menu_button(lang, "records", "page_records")
            _menu_button(lang, "gaps", "page_gaps")
            _menu_button(lang, "action_plan", "page_action_plan")
            _menu_button(lang, "risk_register", "page_risk_register")
            _menu_button(lang, "import", "page_import")

    with cols[3]:
        with st.popover(t(lang, "menu_library"), use_container_width=True):
            _menu_button(lang, "frameworks", "page_frameworks")
            _menu_button(lang, "controls", "page_controls")
            _menu_button(lang, "ecc", "page_ecc")

    with cols[4]:
        with st.popover(t(lang, "menu_settings"), use_container_width=True):
            _menu_button(lang, "departments", "page_departments")
            _menu_button(lang, "control_codes", "page_control_codes")
            _menu_button(lang, "audit_log", "page_audit_log")
            _menu_button(lang, "preferences", "page_preferences")

    with cols[5]:
        if st.button(
            f"🛰️ {t(lang, 'menu_scanner')}",
            key="menu_scanner_btn",
            use_container_width=True,
            type="primary" if st.session_state.nav == "scanner" else "secondary",
        ):
            _go("scanner")

    with cols[6]:
        if st.button(
            t(lang, "menu_assistant"),
            key="menu_assistant_btn",
            use_container_width=True,
            type="primary" if st.session_state.nav == "assistant" else "secondary",
        ):
            _go("assistant")

    with cols[7]:
        with st.popover(t(lang, "menu_links"), use_container_width=True):
            st.markdown(
                f"""
<a href="{NCA_OFFICIAL_URL}" target="_blank">{t(lang, "link_nca")}</a>
<a href="{ECC_PDF_URL}" target="_blank">{t(lang, "link_ecc_pdf")}</a>
<a href="{ECC_IMPLEMENTATION_GUIDE_URL}" target="_blank">{t(lang, "link_implementation_guide")}</a>
<a href="https://haseen.sa" target="_blank">{t(lang, "link_haseen")}</a>
<a href="https://academy.nca.gov.sa" target="_blank">{t(lang, "link_academy")}</a>
<a href="https://nca.gov.sa/ar/awareness/" target="_blank">{t(lang, "link_awareness")}</a>
<a href="https://nca.gov.sa/ar/cyberalerts/" target="_blank">{t(lang, "link_alerts")}</a>
""",
                unsafe_allow_html=True,
            )

    with cols[8]:
        user_label = st.session_state.user or t(lang, "menu_account")
        with st.popover(f"👤 {user_label}", use_container_width=True):
            st.markdown(
                f"<div style='padding:.4rem .6rem; color:#888; font-size:.85rem;'>"
                f"{t(lang, 'menu_account')}: <b>{st.session_state.user or '—'}</b></div>",
                unsafe_allow_html=True,
            )
            st.markdown("---")
            st.markdown(f"<div style='padding:0 .6rem; color:#888; font-size:.8rem;'>{t(lang, 'language')}</div>", unsafe_allow_html=True)
            st.radio("Lang", options=["ar", "en"], key="lang", horizontal=True,
                     label_visibility="collapsed",
                     format_func=lambda v: "العربية" if v == "ar" else "English")
            st.markdown(f"<div style='padding:0 .6rem; color:#888; font-size:.8rem;'>{t(lang, 'theme_label')}</div>", unsafe_allow_html=True)
            st.radio("Theme", options=["light", "dark"], key="theme", horizontal=True,
                     label_visibility="collapsed",
                     format_func=lambda v: "☀️ Light" if v == "light" else "🌙 Dark")
            st.markdown("---")
            if st.button(t(lang, "menu_logout"), key="logout_btn", use_container_width=True):
                _audit("logout", "user", st.session_state.user, "تسجيل خروج")
                for k in ("authenticated", "user", "chat", "nav", "active_record_id"):
                    st.session_state.pop(k, None)
                for k in ("u", "p", "l"):
                    if k in st.query_params:
                        del st.query_params[k]
                st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


# =========================================================================
#  Data helpers
# =========================================================================
def _filter_controls_records() -> tuple[pd.DataFrame, pd.DataFrame, dict[str, float | int]]:
    controls = st.session_state.controls_df.copy()
    records = st.session_state.records_df.copy()
    departments = st.session_state.departments_df.copy()
    frameworks = st.session_state.frameworks_df.copy()

    controls = controls.rename(columns={"id": "control_pk"})
    records = records.rename(columns={"id": "record_id"})
    departments = departments.rename(
        columns={"id": "department_pk", "name_ar": "department_name_ar", "code": "department_code"}
    )
    frameworks = frameworks.rename(columns={"id": "framework_pk", "name_ar": "framework_name_ar"})

    if st.session_state.framework_id:
        controls = controls[controls["framework_id"] == int(st.session_state.framework_id)]
    if st.session_state.department_id:
        records = records[records["department_id"] == int(st.session_state.department_id)]
    if st.session_state.status_filter:
        records = records[records["status"] == st.session_state.status_filter]
    if st.session_state.risk_filter:
        records = records[records["risk_rating"] == st.session_state.risk_filter]

    merged = records.merge(controls, left_on="control_id", right_on="control_pk", how="left")
    merged = merged.merge(
        departments[["department_pk", "department_name_ar", "department_code"]],
        left_on="department_id", right_on="department_pk", how="left",
    )
    merged = merged.merge(
        frameworks[["framework_pk", "framework_name_ar"]],
        left_on="framework_id", right_on="framework_pk", how="left",
    )
    if st.session_state.table_search and not merged.empty:
        q = st.session_state.table_search.strip().lower()
        mask = merged.astype(str).apply(lambda s: s.str.lower().str.contains(q, na=False))
        merged = merged[mask.any(axis=1)]
    stats = calc_stats(records=records, controls=controls)
    return controls, merged, stats


def _page_header(title: str, caption: str | None = None) -> None:
    st.markdown(f'<h1 class="page-title">{title}</h1>', unsafe_allow_html=True)
    if caption:
        st.markdown(f'<p class="page-caption">{caption}</p>', unsafe_allow_html=True)


def _render_filters(lang: Lang, with_status_risk: bool = False) -> None:
    fr_records = st.session_state.frameworks_df.to_dict("records")
    dp_records = st.session_state.departments_df.to_dict("records")
    cols = st.columns([1, 1, 1, 1, 2] if with_status_risk else [1, 1, 2])
    fw_opts = {"": t(lang, "all")}
    fw_opts.update({str(x["id"]): f'{x["name_ar"]} ({x["code"]})' for x in fr_records})
    cols[0].selectbox(t(lang, "framework"), options=list(fw_opts.keys()),
                      format_func=lambda x: fw_opts[x], key="framework_id")
    dep_opts = {"": t(lang, "all")}
    dep_opts.update({str(x["id"]): f'{x.get("code") or "-"} {x["name_ar"]}' for x in dp_records})
    cols[1].selectbox(t(lang, "department"), options=list(dep_opts.keys()),
                      format_func=lambda x: dep_opts[x], key="department_id")
    if with_status_risk:
        st_opts = {"": t(lang, "all"), **{s: STATUS_LABEL_AR[s] for s in STATUSES}}
        cols[2].selectbox(t(lang, "filter_status"), options=list(st_opts.keys()),
                          format_func=lambda x: st_opts[x], key="status_filter")
        rk_opts = {"": t(lang, "all"), **{r: RISK_LABEL_AR[r] for r in RISK_LEVELS}}
        cols[3].selectbox(t(lang, "filter_risk"), options=list(rk_opts.keys()),
                          format_func=lambda x: rk_opts[x], key="risk_filter")
        cols[4].text_input(t(lang, "search_table"), key="table_search",
                           placeholder=t(lang, "search_placeholder"))
    else:
        cols[2].text_input(t(lang, "search_table"), key="table_search",
                           placeholder=t(lang, "search_placeholder"))


# =========================================================================
#  Control Detail Dialog
# =========================================================================
@st.dialog("تفاصيل الضابط", width="large")
def _control_detail_dialog(record_id: int) -> None:
    df = st.session_state.records_df
    rec_row = df[df["id"] == record_id]
    if rec_row.empty:
        st.error("لم يُعثر على السجل.")
        return
    rec = rec_row.iloc[0].to_dict()
    ctrl = st.session_state.controls_df[
        st.session_state.controls_df["id"] == rec["control_id"]
    ].iloc[0].to_dict()

    deps = st.session_state.departments_df.to_dict("records")
    dep_map = {int(d["id"]): f'{d.get("code") or "-"} · {d["name_ar"]}' for d in deps}

    st.markdown(
        f"### {ctrl['control_ref']} — {ctrl['title_ar']}"
    )
    st.caption(f"{ctrl.get('domain_ar', '')} · {ctrl.get('subdomain_ar', '')}")
    st.markdown("---")

    tabs = st.tabs(["📋 المعلومات", "✅ الحالة والإسناد", "📎 الأدلة والملاحظات", "📚 الإرشاد"])

    with tabs[0]:
        st.markdown(f"**الهدف:** {ctrl.get('objective_ar', '—')}")
        st.markdown(f"**الأولوية:** {ctrl.get('priority', '—')}")
        st.markdown(f"**رقم السجل:** {rec['id']}")

    with tabs[1]:
        c1, c2 = st.columns(2)
        with c1:
            new_status = st.selectbox(
                "الحالة",
                options=STATUSES,
                index=STATUSES.index(rec["status"]) if rec["status"] in STATUSES else 0,
                format_func=lambda s: STATUS_LABEL_AR.get(s, s),
                key=f"d_status_{record_id}",
            )
            new_dep = st.selectbox(
                "الإدارة المختصة",
                options=list(dep_map.keys()),
                index=list(dep_map.keys()).index(int(rec["department_id"])) if int(rec["department_id"]) in dep_map else 0,
                format_func=lambda x: dep_map[x],
                key=f"d_dep_{record_id}",
            )
            new_owner = st.text_input("المسؤول (Owner)", value=str(rec.get("owner") or ""), key=f"d_own_{record_id}")
        with c2:
            new_risk = st.selectbox(
                "تقييم المخاطر",
                options=RISK_LEVELS,
                index=RISK_LEVELS.index(rec["risk_rating"]) if rec["risk_rating"] in RISK_LEVELS else 0,
                format_func=lambda r: RISK_LABEL_AR.get(r, r),
                key=f"d_risk_{record_id}",
            )
            new_maturity = st.slider(
                "مستوى النضج (0-5)",
                min_value=0, max_value=5, value=int(rec.get("maturity_level") or 0),
                key=f"d_mat_{record_id}",
                help="0 غير موجود · 1 أوّلي · 2 معرَّف · 3 مطبَّق · 4 مقاس · 5 محسَّن",
            )
            try:
                td = pd.to_datetime(rec.get("target_date"), errors="coerce")
                td_default = td.date() if pd.notna(td) else date.today()
            except Exception:
                td_default = date.today()
            new_target = st.date_input("تاريخ الإنجاز المستهدف", value=td_default, key=f"d_td_{record_id}")

    with tabs[2]:
        new_evidence = st.text_area("ملخص الأدلة", value=str(rec.get("evidence_summary") or ""),
                                    key=f"d_ev_{record_id}", height=120)
        new_files = st.text_input("الأدلة المرفقة (مسارات/أسماء، مفصولة بفاصلة)",
                                  value=str(rec.get("evidence_files") or ""), key=f"d_files_{record_id}")
        uploaded = st.file_uploader("إرفاق دليل جديد", type=None, key=f"d_up_{record_id}")
        if uploaded is not None:
            existing = [x.strip() for x in (new_files or "").split(",") if x.strip()]
            existing.append(uploaded.name)
            new_files = ", ".join(existing)
            st.success(f"تمت إضافة: {uploaded.name}")
        new_notes = st.text_area("ملاحظات", value=str(rec.get("notes") or ""),
                                 key=f"d_notes_{record_id}", height=100)

    with tabs[3]:
        st.markdown(f"**إرشادات التطبيق:** {ctrl.get('guidance_ar', '—')}")
        st.markdown(f"**إرشادات الأدلة:** {ctrl.get('evidence_guidance_ar', '—')}")
        st.markdown(
            f"<a class='link-card' target='_blank' href='{ECC_IMPLEMENTATION_GUIDE_URL}'>"
            f"<span class='lc-title'>📘 الدليل الإرشادي لتطبيق ECC (NCA)</span>"
            f"<span class='lc-desc'>{ECC_IMPLEMENTATION_GUIDE_URL}</span></a>",
            unsafe_allow_html=True,
        )

    st.markdown("---")
    cc1, cc2 = st.columns([1, 1])
    with cc1:
        if st.button("حفظ التغييرات", type="primary", use_container_width=True, key=f"save_{record_id}"):
            df = st.session_state.records_df.copy()
            i = df.index[df["id"] == record_id][0]
            changes = []
            for field, new_val in (
                ("status", new_status),
                ("department_id", int(new_dep)),
                ("owner", new_owner),
                ("risk_rating", new_risk),
                ("maturity_level", int(new_maturity)),
                ("target_date", new_target.isoformat()),
                ("evidence_summary", new_evidence),
                ("evidence_files", new_files),
                ("notes", new_notes),
            ):
                old_val = df.at[i, field] if field in df.columns else None
                if str(old_val) != str(new_val):
                    changes.append(f"{field}: {old_val} → {new_val}")
                    df.at[i, field] = new_val
            df.at[i, "last_updated"] = date.today().isoformat()
            df.at[i, "last_updated_by"] = st.session_state.user or "—"
            st.session_state.records_df = df
            if changes:
                _audit("update", "record", record_id, " | ".join(changes))
            st.success("تم الحفظ.")
            st.rerun()
    with cc2:
        if st.button("إغلاق", use_container_width=True, key=f"close_{record_id}"):
            st.rerun()


# =========================================================================
#  Pages — Dashboard
# =========================================================================
def _page_overview(lang: Lang) -> None:
    _, merged, stats = _filter_controls_records()
    fr_count = int(len(st.session_state.frameworks_df))
    dp_count = int(len(st.session_state.departments_df))

    a1, a2, a3, a4 = st.columns(4)
    a1.metric(t(lang, "metric_controls"), f"{stats['total_controls']}")
    a2.metric(t(lang, "metric_rate"), f"{stats['compliance_rate']}%")
    a3.metric(t(lang, "metric_gaps"), f"{stats['gap_open_count']}")
    a4.metric(t(lang, "metric_records"), f"{stats['records_total']}")

    b1, b2, b3, b4 = st.columns(4)
    b1.metric(t(lang, "metric_frameworks"), f"{fr_count}")
    b2.metric(t(lang, "metric_departments"), f"{dp_count}")
    b3.metric(t(lang, "metric_avg_maturity"), f"{stats['avg_maturity']}/5")
    b4.metric(t(lang, "metric_high_risk"), f"{stats['high_risk_count']}")

    cmap = {"compliant": "#10b981", "partial": "#f59e0b",
            "not_started": "#ef4444", "not_applicable": "#94a3b8"}

    chart_df = pd.DataFrame([
        {"status": "compliant", "count": stats["compliant"]},
        {"status": "partial", "count": stats["partial"]},
        {"status": "not_started", "count": stats["not_started"]},
        {"status": "not_applicable", "count": stats["not_applicable"]},
    ])
    fig = px.bar(chart_df, x="status", y="count", color="status",
                 title=t(lang, "compliance_distribution"), color_discrete_map=cmap)
    fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                      showlegend=False, margin=dict(t=44, l=10, r=10, b=10))
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    if not merged.empty and "domain_ar" in merged.columns:
        g = merged.groupby(["domain_ar", "status"], dropna=False).size().reset_index(name="count")
        fig2 = px.bar(g, x="domain_ar", y="count", color="status", barmode="stack",
                      title=t(lang, "compliance_by_domain"), color_discrete_map=cmap)
        fig2.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                           margin=dict(t=44, l=10, r=10, b=10))
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})


def _page_kpis(lang: Lang) -> None:
    _page_header(t(lang, "page_kpis"))
    _, merged, stats = _filter_controls_records()
    cols = st.columns(4)
    cols[0].metric(t(lang, "metric_rate"), f"{stats['compliance_rate']}%")
    cols[1].metric(t(lang, "metric_avg_maturity"), f"{stats['avg_maturity']}/5")
    cols[2].metric(t(lang, "metric_gaps"), f"{stats['gap_open_count']}")
    cols[3].metric(t(lang, "metric_high_risk"), f"{stats['high_risk_count']}")

    if not merged.empty and "framework_name_ar" in merged.columns:
        g = (merged.groupby(["framework_name_ar", "status"], dropna=False)
             .size().reset_index(name="count"))
        fig = px.bar(g, x="framework_name_ar", y="count", color="status",
                     barmode="group", title="حالة الامتثال لكل إطار",
                     color_discrete_map={"compliant": "#10b981", "partial": "#f59e0b",
                                         "not_started": "#ef4444", "not_applicable": "#94a3b8"})
        fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                          margin=dict(t=44, l=10, r=10, b=10))
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    if not merged.empty and "department_name_ar" in merged.columns:
        g2 = (merged.groupby(["department_name_ar", "status"], dropna=False)
              .size().reset_index(name="count"))
        fig2 = px.bar(g2, x="department_name_ar", y="count", color="status",
                      barmode="group", title="الامتثال حسب الإدارة",
                      color_discrete_map={"compliant": "#10b981", "partial": "#f59e0b",
                                          "not_started": "#ef4444", "not_applicable": "#94a3b8"})
        fig2.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                           margin=dict(t=44, l=10, r=10, b=10))
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})


def _page_maturity(lang: Lang) -> None:
    _page_header(t(lang, "page_maturity"), t(lang, "maturity_caption"))
    _, merged, _ = _filter_controls_records()

    if merged.empty or "maturity_level" not in merged.columns:
        st.info(t(lang, "no_gaps"))
        return

    pivot = (merged.pivot_table(
        index="domain_ar", columns="department_name_ar",
        values="maturity_level", aggfunc="mean", fill_value=0
    ).round(2))
    if pivot.empty:
        st.info("لا بيانات كافية.")
        return
    fig = px.imshow(pivot.values, x=list(pivot.columns), y=list(pivot.index),
                    color_continuous_scale="Greens", aspect="auto",
                    labels=dict(x="الإدارة", y="المجال", color="النضج"),
                    title="خريطة النضج (متوسط 0-5)")
    fig.update_layout(margin=dict(t=44, l=10, r=10, b=10),
                      plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    st.markdown(f'<div class="section-title">متوسط النضج لكل مجال</div>', unsafe_allow_html=True)
    by_dom = maturity_by_domain(merged)
    st.dataframe(by_dom, use_container_width=True, hide_index=True)


def _page_reports(lang: Lang) -> None:
    _page_header(t(lang, "page_reports"), t(lang, "reports_caption"))
    _, merged, stats = _filter_controls_records()
    open_gaps = (merged[merged["status"].isin(["partial", "not_started"])]
                 if "status" in merged.columns else pd.DataFrame())

    csv_full = merged.to_csv(index=False).encode("utf-8-sig")
    csv_gaps = open_gaps.to_csv(index=False).encode("utf-8-sig")
    action_cols = ["control_ref", "title_ar", "domain_ar", "department_name_ar",
                   "status", "risk_rating", "maturity_level", "owner", "target_date"]
    action_cols = [c for c in action_cols if c in open_gaps.columns]
    csv_plan = open_gaps[action_cols].to_csv(index=False).encode("utf-8-sig")

    summary = (
        "ملخص تنفيذي — درع سيبراني\n"
        f"التاريخ: {date.today().isoformat()}\n\n"
        f"إجمالي الضوابط: {stats['total_controls']}\n"
        f"السجلات: {stats['records_total']}\n"
        f"نسبة الامتثال: {stats['compliance_rate']}%\n"
        f"متوسط النضج: {stats['avg_maturity']}/5\n"
        f"الفجوات المفتوحة: {stats['gap_open_count']}\n"
        f"ضوابط عالية الخطورة: {stats['high_risk_count']}\n"
    )
    c1, c2 = st.columns(2)
    with c1:
        st.download_button(t(lang, "report_csv_full"), data=csv_full,
                           file_name="compliance-full.csv", mime="text/csv",
                           use_container_width=True)
        st.download_button(t(lang, "report_action_plan"), data=csv_plan,
                           file_name="compliance-action-plan.csv", mime="text/csv",
                           use_container_width=True)
    with c2:
        st.download_button(t(lang, "report_gaps"), data=csv_gaps,
                           file_name="compliance-gaps.csv", mime="text/csv",
                           use_container_width=True)
        st.download_button(t(lang, "report_executive"), data=summary.encode("utf-8-sig"),
                           file_name="executive-summary.txt", mime="text/plain",
                           use_container_width=True)

    st.markdown(f'<div class="section-title">معاينة</div>', unsafe_allow_html=True)
    st.dataframe(merged, use_container_width=True, hide_index=True)


# =========================================================================
#  Pages — Compliance
# =========================================================================
def _page_records(lang: Lang) -> None:
    _page_header(t(lang, "page_records"))
    st.markdown(
        """
<div class="hint-box">
  <b>كيف تعدّل حالة الامتثال؟</b>
  <ol style="margin:.4rem 0 0; padding-inline-start:1.2rem;">
    <li>استخدم <b>تبويب «تعديل سريع»</b> لتغيير الحالة / المخاطر / النضج / المسؤول / التاريخ مباشرة في الجدول، ثم اضغط <b>حفظ التغييرات</b>.</li>
    <li>أو استخدم <b>تبويب «تفصيل ضابط»</b> لفتح نافذة بكل التفاصيل والأدلة لكل ضابط.</li>
  </ol>
</div>
""",
        unsafe_allow_html=True,
    )
    _render_filters(lang, with_status_risk=True)
    _, merged, _ = _filter_controls_records()

    if merged.empty:
        st.info("لا توجد سجلات مطابقة للفلاتر الحالية.")
        return

    deps = st.session_state.departments_df.to_dict("records")
    dep_id_to_label = {int(d["id"]): f'{d.get("code") or "-"} · {d["name_ar"]}' for d in deps}
    dep_label_to_id = {v: k for k, v in dep_id_to_label.items()}

    tab_quick, tab_detail = st.tabs(["⚡ تعديل سريع", "📂 تفصيل ضابط"])

    with tab_quick:
        edit_view = merged.copy()
        edit_view["dept"] = edit_view["department_id"].map(dep_id_to_label)
        try:
            edit_view["target_date"] = pd.to_datetime(edit_view["target_date"], errors="coerce").dt.date
        except Exception:
            pass
        cols = ["record_id", "control_ref", "title_ar", "domain_ar",
                "dept", "status", "risk_rating", "maturity_level",
                "owner", "target_date"]
        cols = [c for c in cols if c in edit_view.columns]
        edited = st.data_editor(
            edit_view[cols],
            use_container_width=True, hide_index=True, num_rows="fixed",
            key="records_quick_editor",
            column_config={
                "record_id":   st.column_config.NumberColumn("#", disabled=True, width="small"),
                "control_ref": st.column_config.TextColumn("الضابط", disabled=True, width="small"),
                "title_ar":    st.column_config.TextColumn("العنوان", disabled=True),
                "domain_ar":   st.column_config.TextColumn("المجال", disabled=True),
                "dept":        st.column_config.SelectboxColumn(
                    "الإدارة المختصة", options=list(dep_id_to_label.values()), required=True,
                ),
                "status": st.column_config.SelectboxColumn(
                    "الحالة", options=STATUSES, required=True,
                    help="ممتثل / جزئي / لم يبدأ / لا ينطبق",
                ),
                "risk_rating": st.column_config.SelectboxColumn(
                    "المخاطر", options=RISK_LEVELS, required=True,
                ),
                "maturity_level": st.column_config.NumberColumn(
                    "النضج", min_value=0, max_value=5, step=1,
                    help="0 غير موجود · 1 أوّلي · 2 معرَّف · 3 مطبَّق · 4 مقاس · 5 محسَّن",
                ),
                "owner":       st.column_config.TextColumn("المسؤول"),
                "target_date": st.column_config.DateColumn("تاريخ الإنجاز"),
            },
        )

        c1, c2 = st.columns([1, 5])
        with c1:
            do_save = st.button("💾 حفظ التغييرات", type="primary", use_container_width=True, key="records_save")
        with c2:
            st.caption("التغييرات تُحفظ مباشرة في السجلات وتُسجَّل في «سجل المراجعة».")

        if do_save:
            df_orig = st.session_state.records_df.copy()
            n_changes = 0
            for _, row in edited.iterrows():
                rid = int(row["record_id"])
                idx_arr = df_orig.index[df_orig["id"] == rid]
                if len(idx_arr) == 0:
                    continue
                i = idx_arr[0]
                changes = []
                new_dep = dep_label_to_id.get(row.get("dept"), int(df_orig.at[i, "department_id"]))
                td_val = row.get("target_date")
                td_str = td_val.isoformat() if hasattr(td_val, "isoformat") else (str(td_val) if td_val else "")
                updates = {
                    "status":         str(row.get("status") or df_orig.at[i, "status"]),
                    "risk_rating":    str(row.get("risk_rating") or df_orig.at[i, "risk_rating"]),
                    "maturity_level": int(row.get("maturity_level") or 0),
                    "owner":          str(row.get("owner") or ""),
                    "target_date":    td_str,
                    "department_id":  int(new_dep),
                }
                for k, v in updates.items():
                    old = df_orig.at[i, k] if k in df_orig.columns else None
                    if str(old) != str(v):
                        changes.append(f"{k}: {old} → {v}")
                        df_orig.at[i, k] = v
                if changes:
                    df_orig.at[i, "last_updated"] = date.today().isoformat()
                    df_orig.at[i, "last_updated_by"] = st.session_state.user or "—"
                    _audit("update", "record", rid, " | ".join(changes))
                    n_changes += 1
            st.session_state.records_df = df_orig
            if n_changes:
                st.success(f"تم حفظ التغييرات على {n_changes} سجلاً.")
            else:
                st.info("لا توجد تغييرات للحفظ.")

    with tab_detail:
        c1, c2 = st.columns([3, 1])
        with c1:
            sel = st.selectbox(
                "اختر سجلاً للعرض/التعديل التفصيلي",
                options=[int(x) for x in merged["record_id"].dropna().tolist()],
                format_func=lambda r: (
                    f"#{r} · "
                    + str(merged[merged["record_id"] == r].iloc[0].get("control_ref", ""))
                    + " · "
                    + str(merged[merged["record_id"] == r].iloc[0].get("title_ar", ""))[:60]
                ),
                key="record_detail_select",
            )
        with c2:
            st.write("")
            if st.button(t(lang, "view_detail"), type="primary", use_container_width=True, key="open_detail_btn"):
                st.session_state.active_record_id = int(sel)

        if st.session_state.get("active_record_id"):
            rid = int(st.session_state.active_record_id)
            st.session_state.active_record_id = None
            _control_detail_dialog(rid)


# =========================================================================
#  Pages — Compliance Browser (warm-beige UI inspired by NCA controls page)
# =========================================================================
_CB_STATUS_TO_BADGE_KEY = {
    "compliant":      ("applied",  "cb_b_completed"),
    "partial":        ("partial",  "cb_b_partial"),
    "not_started":    ("required", "cb_b_required"),
    "not_applicable": ("notapp",   "cb_b_notapp"),
}

_CB_STATUS_OPTIONS = ["compliant", "partial", "not_started", "not_applicable"]


def _cb_compute_dept_stats(records: pd.DataFrame, dept_id: int) -> dict[str, int | float]:
    sub = records[records["department_id"] == dept_id]
    total = int(len(sub))
    if total == 0:
        return {"total": 0, "filled": 0, "fill_pct": 0.0,
                "compliance_pct": 0.0, "compliant": 0, "partial": 0,
                "not_started": 0, "not_applicable": 0, "pending": 0}

    has_files = sub["evidence_files"].fillna("").astype(str).str.strip().ne("") | \
                sub["evidence_summary"].fillna("").astype(str).str.strip().ne("")
    is_notapp = sub["status"] == "not_applicable"
    is_filled = is_notapp | has_files
    filled = int(is_filled.sum())

    compliant_n      = int(((sub["status"] == "compliant") & has_files).sum())
    partial_n        = int(((sub["status"] == "partial") & has_files).sum())
    not_started_n    = int(((sub["status"] == "not_started")).sum())
    not_applicable_n = int(is_notapp.sum())
    pending_n        = int(((sub["status"].isin(["compliant", "partial"])) & ~has_files).sum())

    score_denom = compliant_n + partial_n + not_started_n
    score_sum = compliant_n * 1.0 + partial_n * 0.5
    compliance_pct = round(100 * score_sum / score_denom, 1) if score_denom else 0.0
    fill_pct = round(100 * filled / total, 1) if total else 0.0

    return {
        "total": total, "filled": filled, "fill_pct": fill_pct,
        "compliance_pct": compliance_pct,
        "compliant": compliant_n, "partial": partial_n,
        "not_started": not_started_n, "not_applicable": not_applicable_n,
        "pending": pending_n,
    }


def _cb_status_badge_html(status: str | None, has_evidence: bool, lang: Lang) -> str:
    if not status:
        return f'<span class="cb-badge cb-b-pending">{t(lang, "cb_b_pending")}</span>'
    cls, label_key = _CB_STATUS_TO_BADGE_KEY.get(status, ("pending", "cb_b_pending"))
    if status in ("compliant", "partial") and not has_evidence:
        return f'<span class="cb-badge cb-b-pending">{t(lang, "cb_b_needs_files")}</span>'
    if status == "not_applicable":
        return f'<span class="cb-badge cb-b-{cls}">{t(lang, label_key)}</span>'
    return f'<span class="cb-badge cb-b-{cls}">{t(lang, label_key)}</span>'


def _cb_color_for_pct(pct: float) -> str:
    if pct >= 80:
        return "var(--cb-success-strong)"
    if pct >= 50:
        return "var(--cb-warn-strong)"
    if pct >= 1:
        return "var(--cb-danger-strong)"
    return "rgba(0,0,0,0.2)"


def _cb_status_label(stats: dict, lang: Lang) -> tuple[str, str, str]:
    if stats["total"] == 0:
        return (t(lang, "cb_state_unassigned"), "var(--cb-text-3)", "var(--cb-neutral-bg)")
    if stats["fill_pct"] == 0:
        return (t(lang, "cb_state_not_started"), "var(--cb-danger-text)", "var(--cb-danger-bg)")
    if stats["fill_pct"] < 100:
        return (t(lang, "cb_state_in_progress"), "var(--cb-warn-text)", "var(--cb-warn-bg)")
    if stats["compliance_pct"] >= 80:
        return (t(lang, "cb_state_compliant"), "var(--cb-success-text)", "var(--cb-success-bg)")
    return (t(lang, "cb_state_needs_improvement"), "var(--cb-warn-text)", "var(--cb-warn-bg)")


def _cb_render_stat_grid(stats: dict, lang: Lang) -> None:
    color_comp = _cb_color_for_pct(stats["compliance_pct"])
    color_fill = "var(--cb-info-border)"
    html = f"""
<div class="cb-stat-grid">
  <div class="cb-stat-card">
    <div class="cb-stat-label">{t(lang, "cb_stat_compliance")}</div>
    <div class="cb-stat-val success">{stats["compliance_pct"]}%</div>
    <div class="cb-progress-bar"><div style="width:{stats["compliance_pct"]}%; background:{color_comp};"></div></div>
  </div>
  <div class="cb-stat-card">
    <div class="cb-stat-label">{t(lang, "cb_stat_fill")}</div>
    <div class="cb-stat-val info">{stats["fill_pct"]}%</div>
    <div class="cb-progress-bar"><div style="width:{stats["fill_pct"]}%; background:{color_fill};"></div></div>
  </div>
  <div class="cb-stat-card">
    <div class="cb-stat-label">{t(lang, "cb_stat_completed")}</div>
    <div class="cb-stat-val success">{stats["compliant"]}</div>
  </div>
  <div class="cb-stat-card">
    <div class="cb-stat-label">{t(lang, "cb_stat_pending")}</div>
    <div class="cb-stat-val warn">{stats["pending"] + stats["not_started"]}</div>
  </div>
</div>
"""
    st.markdown(html, unsafe_allow_html=True)


def _cb_render_detail_panel(record: dict, control: dict, lang: Lang) -> None:
    rid = int(record["id"])
    st.markdown('<div class="cb-detail-panel">', unsafe_allow_html=True)
    guidance = (control.get("guidance_ar") or "").strip()
    if guidance:
        st.markdown(
            f'<div class="cb-guide-box"><b>{t(lang, "cb_section_guide")}</b><br/>{guidance}</div>',
            unsafe_allow_html=True,
        )

    tab_status, tab_files = st.tabs([
        t(lang, "cb_section_status"),
        t(lang, "cb_section_files"),
    ])

    with tab_status:
        cur = record.get("status") if record.get("status") in _CB_STATUS_OPTIONS else "not_started"
        new_status = st.radio(
            t(lang, "cb_section_status"),
            options=_CB_STATUS_OPTIONS,
            index=_CB_STATUS_OPTIONS.index(cur),
            format_func=lambda s: {
                "compliant":      t(lang, "cb_status_applied"),
                "partial":        t(lang, "cb_status_partial"),
                "not_started":    t(lang, "cb_status_required"),
                "not_applicable": t(lang, "cb_status_notapp"),
            }[s],
            key=f"cb_status_{rid}",
            horizontal=True,
            label_visibility="collapsed",
        )
        new_notes = st.text_area(
            t(lang, "cb_notes"),
            value=str(record.get("notes") or ""),
            key=f"cb_notes_{rid}",
            height=80,
        )

    with tab_files:
        new_summary = st.text_area(
            t(lang, "cb_evidence_summary"),
            value=str(record.get("evidence_summary") or ""),
            key=f"cb_evsum_{rid}",
            height=70,
        )
        existing = [x.strip() for x in str(record.get("evidence_files") or "").split(",") if x.strip()]
        if existing:
            st.markdown(
                "".join(
                    f'<span class="chip" style="margin:2px 4px;">📄 {f}</span>'
                    for f in existing
                ),
                unsafe_allow_html=True,
            )
        upl = st.file_uploader(
            t(lang, "cb_attach_evidence"),
            type=None,
            key=f"cb_upl_{rid}",
        )
        if upl is not None and upl.name not in existing:
            existing.append(upl.name)
        new_files = ", ".join(existing)

    cols = st.columns([1, 1, 4])
    if cols[0].button(t(lang, "cb_save_status"), key=f"cb_save_{rid}",
                      type="primary", use_container_width=True):
        df = st.session_state.records_df.copy()
        idx_arr = df.index[df["id"] == rid]
        if len(idx_arr):
            i = idx_arr[0]
            changes: list[str] = []
            for field, val in (
                ("status",           new_status),
                ("notes",            new_notes),
                ("evidence_summary", new_summary),
                ("evidence_files",   new_files),
            ):
                old = df.at[i, field] if field in df.columns else None
                if str(old or "") != str(val or ""):
                    changes.append(f"{field}: {old} → {val}")
                    df.at[i, field] = val
            if changes:
                df.at[i, "last_updated"]    = date.today().isoformat()
                df.at[i, "last_updated_by"] = st.session_state.user or "—"
                st.session_state.records_df = df
                _audit("update", "record", rid, " | ".join(changes))
                st.success(t(lang, "saved_ok"))
            else:
                st.info("لا توجد تغييرات.")
    if cols[1].button(t(lang, "cb_close_detail"), key=f"cb_close_{rid}",
                      use_container_width=True):
        st.session_state.cb_active_record = None
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


def _cb_render_user_view(lang: Lang) -> None:
    deps = st.session_state.departments_df.to_dict("records")
    controls = st.session_state.controls_df.copy()
    records = st.session_state.records_df.copy()

    if not deps:
        st.markdown(f'<div class="cb-empty">{t(lang, "cb_no_assigned")}</div>',
                    unsafe_allow_html=True)
        return

    if not st.session_state.cb_dept_id or \
       not any(str(d["id"]) == str(st.session_state.cb_dept_id) for d in deps):
        st.session_state.cb_dept_id = str(deps[0]["id"])

    dep_options = {str(d["id"]): f'{d.get("code") or "-"} · {d["name_ar"]}' for d in deps}
    cur_dep_id = int(st.session_state.cb_dept_id)
    cur_dep_name = next((d["name_ar"] for d in deps if int(d["id"]) == cur_dep_id), "—")

    stats = _cb_compute_dept_stats(records, cur_dep_id)

    head_cols = st.columns([2.6, 1])
    with head_cols[0]:
        st.markdown(
            f"""
<div class="cb-header">
  <h2><span class="cb-logo">🛡️</span> {t(lang, "page_compliance_browser")}</h2>
  <div class="cb-version">القسم الحالي: <b>{cur_dep_name}</b> · {stats["total"]} {t(lang, "cb_assigned_count")}</div>
</div>
""",
            unsafe_allow_html=True,
        )
    with head_cols[1]:
        st.selectbox(
            t(lang, "cb_select_dept"),
            options=list(dep_options.keys()),
            format_func=lambda x: dep_options[x],
            key="cb_dept_id",
            label_visibility="collapsed",
        )

    _cb_render_stat_grid(stats, lang)

    dept_records = records[records["department_id"] == cur_dep_id]
    if dept_records.empty:
        st.markdown(f'<div class="cb-empty">{t(lang, "cb_no_assigned")}</div>',
                    unsafe_allow_html=True)
        return

    merged = dept_records.merge(
        controls.rename(columns={"id": "control_pk"}),
        left_on="control_id", right_on="control_pk", how="left",
    )

    by_domain: dict[str, list[dict]] = {}
    for row in merged.to_dict("records"):
        dom = row.get("domain_ar") or "—"
        by_domain.setdefault(dom, []).append(row)

    for dom_name, rows in by_domain.items():
        rows.sort(key=lambda r: str(r.get("control_ref") or ""))
        n_done = sum(1 for r in rows if r.get("status") == "compliant"
                     and (str(r.get("evidence_files") or "").strip() or
                          str(r.get("evidence_summary") or "").strip()))
        header = f"{dom_name}  ·  {len(rows)} ضابط فرعي  ·  {n_done} مكتمل"
        with st.expander(header, expanded=True):
            for row in rows:
                rid = int(row["id"])
                ctrl_ref = str(row.get("control_ref") or "")
                title    = str(row.get("title_ar") or "")
                status   = row.get("status")
                has_ev   = bool(str(row.get("evidence_files") or "").strip()) or \
                           bool(str(row.get("evidence_summary") or "").strip())
                badge    = _cb_status_badge_html(status, has_ev, lang)

                cols = st.columns([0.7, 5.5, 1.5, 0.9])
                cols[0].markdown(
                    f'<span class="cb-ctrl-code">{ctrl_ref}</span>',
                    unsafe_allow_html=True,
                )
                cols[1].markdown(
                    f'<span class="cb-ctrl-text">{title}</span>',
                    unsafe_allow_html=True,
                )
                cols[2].markdown(badge, unsafe_allow_html=True)
                is_active = st.session_state.cb_active_record == rid
                if cols[3].button(
                    t(lang, "cb_close_detail" if is_active else "cb_open_detail"),
                    key=f"cb_open_{rid}",
                    use_container_width=True,
                ):
                    st.session_state.cb_active_record = None if is_active else rid
                    st.rerun()

                if is_active:
                    ctrl_dict = controls[controls["id"] == row["control_id"]].iloc[0].to_dict()
                    _cb_render_detail_panel(row, ctrl_dict, lang)


def _cb_render_admin_view(lang: Lang) -> None:
    deps = st.session_state.departments_df.to_dict("records")
    records = st.session_state.records_df.copy()

    rows_html: list[str] = []
    for d in deps:
        s = _cb_compute_dept_stats(records, int(d["id"]))
        fill_color = _cb_color_for_pct(s["fill_pct"])
        comp_color = _cb_color_for_pct(s["compliance_pct"])
        lbl, lbl_col, lbl_bg = _cb_status_label(s, lang)
        rows_html.append(f"""
<tr>
  <td><b>{d.get("code", "-") or "-"}</b> · {d["name_ar"]}</td>
  <td>{s["total"]}</td>
  <td>
    <div class="cb-mini-prog">
      <span class="num">{s["fill_pct"]}%</span>
      <div class="bar"><div class="fill" style="width:{s["fill_pct"]}%;background:{fill_color};"></div></div>
      <span class="count">{s["filled"]}/{s["total"]}</span>
    </div>
  </td>
  <td>
    <div class="cb-mini-prog">
      <span class="num">{s["compliance_pct"]}%</span>
      <div class="bar"><div class="fill" style="width:{s["compliance_pct"]}%;background:{comp_color};"></div></div>
    </div>
  </td>
  <td><span class="cb-status-tag" style="color:{lbl_col};background:{lbl_bg};">{lbl}</span></td>
</tr>
""")

    table_html = f"""
<div class="cb-summary-wrap">
  <h2>{t(lang, "cb_admin_summary_title")}</h2>
  <table class="cb-summary-table">
    <thead>
      <tr>
        <th>{t(lang, "cb_col_dept")}</th>
        <th>{t(lang, "cb_col_assigned")}</th>
        <th>{t(lang, "cb_col_fill")}</th>
        <th>{t(lang, "cb_col_compliance")}</th>
        <th>{t(lang, "cb_col_status")}</th>
      </tr>
    </thead>
    <tbody>{"".join(rows_html)}</tbody>
  </table>
</div>
"""
    st.markdown(table_html, unsafe_allow_html=True)

    st.markdown(
        f'<h3 style="font-size:15px;font-weight:700;margin:16px 0 10px;">'
        f'{t(lang, "cb_dept_distribution")}</h3>',
        unsafe_allow_html=True,
    )

    dept_cards: list[str] = []
    for d in deps:
        s = _cb_compute_dept_stats(records, int(d["id"]))
        fill_color = _cb_color_for_pct(s["fill_pct"])
        comp_color = _cb_color_for_pct(s["compliance_pct"])
        dept_cards.append(f"""
<div class="cb-dept-row">
  <div class="cb-dept-row-top">
    <span class="cb-dept-name">{d.get("code","-") or "-"} · {d["name_ar"]}</span>
    <span class="cb-pill-info" style="margin:0;">{s["total"]} ضابط</span>
  </div>
  <div class="cb-dept-meta">{s["compliant"]} مكتمل · {s["partial"]} جزئي · {s["not_started"]} لم يبدأ</div>
  <div class="cb-mini-prog" style="margin-bottom:4px;">
    <span class="num">تعبئة {s["fill_pct"]}%</span>
    <div class="bar"><div class="fill" style="width:{s["fill_pct"]}%;background:{fill_color};"></div></div>
  </div>
  <div class="cb-mini-prog">
    <span class="num">التزام {s["compliance_pct"]}%</span>
    <div class="bar"><div class="fill" style="width:{s["compliance_pct"]}%;background:{comp_color};"></div></div>
  </div>
</div>
""")
    st.markdown("".join(dept_cards), unsafe_allow_html=True)


def _page_compliance_browser(lang: Lang) -> None:
    _page_header(t(lang, "page_compliance_browser"), t(lang, "cb_caption"))
    st.markdown('<div class="cb-page-wrap">', unsafe_allow_html=True)
    user_tab, admin_tab = st.tabs([t(lang, "cb_tab_user"), t(lang, "cb_tab_admin")])
    with user_tab:
        _cb_render_user_view(lang)
    with admin_tab:
        _cb_render_admin_view(lang)
    st.markdown('</div>', unsafe_allow_html=True)


# =========================================================================
def _page_gaps(lang: Lang) -> None:
    _page_header(t(lang, "page_gaps"))
    _render_filters(lang)
    _, merged, _ = _filter_controls_records()
    if st.button(t(lang, "gap_run"), type="primary"):
        open_gaps = (merged[merged["status"].isin(["partial", "not_started"])]
                     if "status" in merged.columns else pd.DataFrame())
        if open_gaps.empty:
            st.session_state.gap_summary = t(lang, "no_gaps")
        else:
            refs = ", ".join(open_gaps["control_ref"].dropna().astype(str).head(8).tolist())
            high = open_gaps[open_gaps["risk_rating"].isin(["high", "critical"])]
            st.session_state.gap_summary = (
                f"تم رصد {len(open_gaps)} سجلات بحاجة معالجة، منها {len(high)} عالية/حرجة المخاطر.\n"
                f"أعلى الأولويات: {refs}.\n"
                "التوصية: ابدأ بالضوابط ذات الخطورة الحرجة، ثم not_started ذات الأولوية العالية، "
                "ثم أغلق partial بإضافة الأدلة."
            )
        _audit("analysis", "gap", "—", st.session_state.gap_summary[:120])
        st.success(t(lang, "gap_done"))
    if st.session_state.gap_summary:
        st.info(st.session_state.gap_summary)

    if not merged.empty and "status" in merged.columns:
        opens = merged[merged["status"].isin(["partial", "not_started"])]
        st.markdown(f'<div class="section-title">السجلات المفتوحة ({len(opens)})</div>', unsafe_allow_html=True)
        cols = ["control_ref", "title_ar", "domain_ar", "department_name_ar",
                "status", "risk_rating", "maturity_level", "target_date"]
        avail = [c for c in cols if c in opens.columns]
        st.dataframe(opens[avail], use_container_width=True, hide_index=True)


def _page_action_plan(lang: Lang) -> None:
    _page_header(t(lang, "page_action_plan"), t(lang, "action_plan_caption"))
    _, merged, _ = _filter_controls_records()
    if merged.empty or "status" not in merged.columns:
        st.info("لا توجد بيانات.")
        return
    opens = merged[merged["status"].isin(["partial", "not_started"])].copy()
    risk_rank = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    status_rank = {"not_started": 0, "partial": 1}
    opens["__r"] = opens["risk_rating"].map(risk_rank).fillna(99)
    opens["__s"] = opens["status"].map(status_rank).fillna(99)
    opens = opens.sort_values(["__r", "__s", "control_ref"]).drop(columns=["__r", "__s"])

    cols = ["control_ref", "title_ar", "domain_ar", "department_name_ar",
            "status", "risk_rating", "maturity_level", "owner", "target_date"]
    avail = [c for c in cols if c in opens.columns]
    st.dataframe(opens[avail], use_container_width=True, hide_index=True)

    csv = opens[avail].to_csv(index=False).encode("utf-8-sig")
    st.download_button(t(lang, "report_action_plan"), data=csv,
                       file_name="action-plan.csv", mime="text/csv",
                       use_container_width=True)


def _page_risk_register(lang: Lang) -> None:
    _page_header(t(lang, "page_risk_register"), t(lang, "risk_register_caption"))
    _, merged, _ = _filter_controls_records()
    if merged.empty:
        st.info("لا توجد بيانات.")
        return
    risk_rank = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    df = merged.copy()
    df["__r"] = df["risk_rating"].map(risk_rank).fillna(99)
    df = df.sort_values(["__r", "maturity_level", "control_ref"]).drop(columns=["__r"])

    cols = ["control_ref", "title_ar", "domain_ar", "department_name_ar",
            "risk_rating", "status", "maturity_level", "owner"]
    avail = [c for c in cols if c in df.columns]
    st.dataframe(df[avail], use_container_width=True, hide_index=True)

    if "risk_rating" in df.columns:
        rc = df.groupby("risk_rating").size().reset_index(name="count")
        fig = px.bar(rc, x="risk_rating", y="count", color="risk_rating",
                     color_discrete_map={"low": "#10b981", "medium": "#f59e0b",
                                         "high": "#ef4444", "critical": "#7f1d1d"},
                     title="توزيع المخاطر")
        fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                          showlegend=False, margin=dict(t=44, l=10, r=10, b=10))
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def _page_audit_log(lang: Lang) -> None:
    _page_header(t(lang, "page_audit_log"), t(lang, "audit_caption"))
    df = st.session_state.audit_df.copy()
    if df.empty:
        st.info(t(lang, "audit_no_entries"))
        return
    df = df.sort_values("timestamp", ascending=False)
    st.dataframe(df, use_container_width=True, hide_index=True)
    csv = df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(t(lang, "download_csv"), data=csv,
                       file_name="audit-log.csv", mime="text/csv",
                       use_container_width=True)


def _page_import(lang: Lang) -> None:
    _page_header(t(lang, "page_import"), t(lang, "upload_hint"))
    up = st.file_uploader("CSV / XLSX", type=["csv", "xlsx", "xls"])
    if up is not None:
        raw = up.read()
        if up.name.lower().endswith(".csv"):
            udf = pd.read_csv(io.BytesIO(raw))
        else:
            udf = pd.read_excel(io.BytesIO(raw), sheet_name=0)
        st.success(f"تم تحميل {len(udf)} صفاً من {up.name}.")
        st.dataframe(udf.head(80), use_container_width=True, hide_index=True)
        st.caption("الاستيراد الفعلي إلى قاعدة البيانات يتطلب ربط الأعمدة (مرجع الضابط / الإدارة / الحالة).")


# =========================================================================
#  Pages — Library
# =========================================================================
def _page_frameworks(lang: Lang) -> None:
    _page_header(t(lang, "page_frameworks"), t(lang, "frameworks_caption"))
    df = st.session_state.frameworks_df.copy()
    for _, row in df.iterrows():
        st.markdown(
            f"""
<div class="section-card">
  <div class="section-title">{row['name_ar']} <small style='color:#888;'>({row['code']})</small></div>
  <div style='color:#666;'>{row.get('description', '—')}</div>
</div>
""",
            unsafe_allow_html=True,
        )


def _page_controls(lang: Lang) -> None:
    _page_header(t(lang, "page_controls"), t(lang, "controls_caption"))
    fw_df = st.session_state.frameworks_df.to_dict("records")
    fw_opts = {"": t(lang, "all")}
    fw_opts.update({str(x["id"]): f'{x["name_ar"]} ({x["code"]})' for x in fw_df})
    st.selectbox(t(lang, "framework"), options=list(fw_opts.keys()),
                 format_func=lambda x: fw_opts[x], key="framework_id")
    controls = st.session_state.controls_df.copy()
    if st.session_state.framework_id:
        controls = controls[controls["framework_id"] == int(st.session_state.framework_id)]
    show = ["control_ref", "title_ar", "domain_ar", "subdomain_ar", "priority"]
    avail = [c for c in show if c in controls.columns]
    st.dataframe(controls[avail], use_container_width=True, hide_index=True,
                 column_config={
                     "control_ref": "المرجع",
                     "title_ar": "العنوان",
                     "domain_ar": "المجال",
                     "subdomain_ar": "الحقل الفرعي",
                     "priority": "الأولوية",
                 })


def _page_ecc(lang: Lang) -> None:
    _page_header(t(lang, "page_ecc"), t(lang, "ecc_caption"))
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(
            f'<a class="link-card" href="{ECC_PDF_URL}" target="_blank">'
            f'<span class="lc-title">📘 {t(lang, "ecc_open")}</span>'
            f'<span class="lc-desc">{ECC_PDF_URL}</span></a>',
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f'<a class="link-card" href="{ECC_IMPLEMENTATION_GUIDE_URL}" target="_blank">'
            f'<span class="lc-title">🛠️ {t(lang, "ecc_implementation")}</span>'
            f'<span class="lc-desc">{ECC_IMPLEMENTATION_GUIDE_URL}</span></a>',
            unsafe_allow_html=True,
        )

    st.markdown(f'<div class="section-title">المجالات الرئيسية</div>', unsafe_allow_html=True)
    controls = st.session_state.controls_df
    for dom in domains_order():
        sub = controls[controls["domain_ar"] == dom]
        with st.expander(f"{dom} — {len(sub)} ضابط", expanded=False):
            cols = ["control_ref", "title_ar", "subdomain_ar", "priority"]
            avail = [c for c in cols if c in sub.columns]
            st.dataframe(sub[avail], use_container_width=True, hide_index=True)


# =========================================================================
#  Pages — Settings
# =========================================================================
def _page_departments(lang: Lang) -> None:
    _page_header(t(lang, "page_departments"))
    df = st.session_state.departments_df.copy()
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown(f'<div class="section-title">{t(lang, "departments_settings")}</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        dep_code = st.text_input(t(lang, "code"), key="new_dep_code")
    with c2:
        dep_ar = st.text_input(t(lang, "name_ar"), key="new_dep_ar")
    with c3:
        dep_en = st.text_input(t(lang, "name_en"), key="new_dep_en")
    if st.button(t(lang, "add_dept"), type="primary"):
        if not dep_ar.strip() or not dep_en.strip():
            st.error(t(lang, "validation_dept"))
        else:
            df = st.session_state.departments_df.copy()
            nxt = int(df["id"].max()) + 1 if not df.empty else 1
            df.loc[len(df)] = {
                "id": nxt,
                "code": dep_code.strip() or None,
                "name_ar": dep_ar.strip(),
                "name_en": dep_en.strip(),
            }
            st.session_state.departments_df = df
            _audit("create", "department", nxt, f"{dep_code} · {dep_ar}")
            st.success("تمت الإضافة.")
            st.rerun()


def _page_control_codes(lang: Lang) -> None:
    _page_header(t(lang, "page_control_codes"))
    df = st.session_state.controls_df.copy()
    fw_map = {int(x["id"]): x["name_ar"] for x in st.session_state.frameworks_df.to_dict("records")}
    df = df.assign(framework=df["framework_id"].map(fw_map))
    edited = st.data_editor(
        df, use_container_width=True, hide_index=True, num_rows="dynamic",
        column_config={
            "id": st.column_config.NumberColumn("ID", disabled=True),
            "framework_id": st.column_config.NumberColumn("Framework", disabled=True),
            "framework": st.column_config.TextColumn("الإطار", disabled=True),
            "control_ref": "المرجع",
            "title_ar": "العنوان",
            "domain_ar": "المجال",
            "subdomain_ar": "الحقل الفرعي",
            "priority": "الأولوية",
        },
        key="controls_editor",
    )
    if st.button(t(lang, "save"), type="primary"):
        cleaned = edited.drop(columns=[c for c in ["framework"] if c in edited.columns])
        st.session_state.controls_df = cleaned
        _audit("update", "controls_catalog", "—", "تعديل ترميز الضوابط")
        st.success(t(lang, "saved_ok"))


def _page_preferences(lang: Lang) -> None:
    _page_header(t(lang, "page_preferences"))
    c1, c2 = st.columns(2)
    with c1:
        st.selectbox(t(lang, "language"), options=["ar", "en"], key="lang",
                     format_func=lambda v: "العربية" if v == "ar" else "English")
    with c2:
        st.selectbox(t(lang, "theme_label"), options=["light", "dark"], key="theme",
                     format_func=lambda v: "☀️ Light" if v == "light" else "🌙 Dark")


# =========================================================================
#  Pages — Website Vulnerability Scanner
# =========================================================================
def _scanner_severity_pill(sev: str, lang: Lang) -> str:
    label_key = {
        "critical": "scanner_critical",
        "high":     "scanner_high",
        "medium":   "scanner_medium",
        "low":      "scanner_low",
        "info":     "scanner_info",
        "ok":       "scanner_ok",
    }.get(sev, "scanner_info")
    css_cls = {
        "critical": "crit",
        "high":     "high",
        "medium":   "med",
        "low":      "low",
        "info":     "info",
        "ok":       "ok",
    }.get(sev, "info")
    return f'<span class="scan-pill {css_cls}">{t(lang, label_key)}</span>'


def _scanner_html_for_result(result: dict, lang: Lang) -> str:
    from cyber_observatory.scanner import DOMAIN_CATALOG, DOMAIN_ORDER, group_by_domain

    counts = result["score"]["counts"]
    score = int(result["score"]["score"])
    grade = result["score"]["grade"]
    score_cls = "danger" if score < 60 else "warn" if score < 80 else ""

    findings_by_domain = group_by_domain(result["findings"])

    started = result.get("started_at", "")
    host = result.get("host", "")
    url = result.get("url", "")

    # Header card
    header = f"""
<div class="scan-header">
  <h2><span class="scan-logo">🛰️</span> {t(lang, "page_scanner")} — {host}</h2>
  <div class="scan-meta">{url}<br/>{started}</div>
</div>
"""

    # Stats grid
    stats = f"""
<div class="scan-stat-grid">
  <div class="scan-stat score {score_cls}">
    <div class="lbl">{t(lang, "scanner_score")}</div>
    <div class="val">{score}<span class="grade">{grade}</span></div>
    <div class="progress"><div style="width:{score}%; background: {'var(--s-success-strong)' if score >= 80 else 'var(--s-warn-strong)' if score >= 60 else 'var(--s-danger-strong)'};"></div></div>
  </div>
  <div class="scan-stat crit"><div class="lbl">{t(lang, "scanner_critical")}</div><div class="val">{counts.get("critical", 0)}</div></div>
  <div class="scan-stat high"><div class="lbl">{t(lang, "scanner_high")}</div><div class="val">{counts.get("high", 0)}</div></div>
  <div class="scan-stat med"><div class="lbl">{t(lang, "scanner_medium")}</div><div class="val">{counts.get("medium", 0)}</div></div>
  <div class="scan-stat low"><div class="lbl">{t(lang, "scanner_low")}</div><div class="val">{counts.get("low", 0)}</div></div>
  <div class="scan-stat ok"><div class="lbl">{t(lang, "scanner_ok")}</div><div class="val">{counts.get("ok", 0)}</div></div>
</div>
"""

    # Domains
    severity_rank = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4, "ok": 5}
    title_key = "title_ar" if lang == "ar" else "title_en"
    domain_blocks: list[str] = []
    for dom_id in DOMAIN_ORDER:
        items = findings_by_domain.get(dom_id, [])
        if not items:
            continue
        cat = DOMAIN_CATALOG.get(dom_id, {"title_ar": dom_id, "title_en": dom_id, "icon": "•", "ecc": ""})
        items_sorted = sorted(items, key=lambda x: severity_rank.get(x.get("severity", "info"), 9))

        sev_present = {x["severity"] for x in items}
        worst = min(sev_present, key=lambda s: severity_rank.get(s, 9)) if sev_present else "info"
        meta_pill = _scanner_severity_pill(worst, lang)
        count_pill = f'<span class="scan-pill">{len(items)}</span>'

        finding_html_parts: list[str] = []
        for f in items_sorted:
            title_safe = (f.get("title") or "").replace("<", "&lt;").replace(">", "&gt;")
            desc_safe = (f.get("description") or "").replace("<", "&lt;").replace(">", "&gt;")
            fix_safe = (f.get("fix") or "").replace("<", "&lt;").replace(">", "&gt;")
            ev_safe = (f.get("evidence") or "").replace("<", "&lt;").replace(">", "&gt;")
            ecc_ref = f.get("ecc_ref") or ""
            evidence_block = (
                f'<div class="evidence">{ev_safe}</div>' if ev_safe else ""
            )
            ecc_block = (
                f'<span class="ecc-tag">{t(lang, "scanner_ecc_label")} · {ecc_ref}</span>'
                if ecc_ref else ""
            )
            finding_html_parts.append(f"""
<div class="scan-finding">
  <div class="scan-finding-head">
    <div class="ttl">{title_safe}</div>
    {_scanner_severity_pill(f.get("severity", "info"), lang)}
  </div>
  <p class="desc">{desc_safe}</p>
  <div class="fix-block">
    <span class="fix-label">🛠️ {t(lang, "scanner_fix_label")}</span>
    {fix_safe}
  </div>
  {evidence_block}
  {ecc_block}
</div>
""")

        is_open = worst in ("critical", "high")
        domain_blocks.append(f"""
<details class="scan-domain" {"open" if is_open else ""}>
  <summary>
    <div class="dom-title">
      <span class="dom-num">{cat.get("icon", "")}</span>
      {cat.get(title_key, dom_id)}
    </div>
    <div class="dom-meta">{meta_pill}{count_pill}</div>
  </summary>
  {''.join(finding_html_parts)}
</details>
""")

    body = "\n".join(domain_blocks) if domain_blocks else f'<div class="scan-empty">{t(lang, "scanner_no_results")}</div>'

    return f"""
<div class="scan-app">
  {header}
  <div class="scan-disclaimer">⚠️ {t(lang, "scanner_disclaimer")}</div>
  {stats}
  {body}
</div>
"""


def _vm_run_scan(url: str) -> dict:
    """Wrapper used by the VM platform — calls the passive scanner."""
    from cyber_observatory.scanner import scan
    return scan(url)


def _vm_ai_pentest_plan(scan: dict, lang: Lang) -> dict:
    """Wrapper for AI pentester — uses existing OpenAI key + model.

    Mirrors PentestGPT's Reasoning → Generation → Parsing pipeline.
    """
    from cyber_observatory import ai_pentester

    api_key = _resolve_api_key()
    if not api_key:
        return {"reasoning": "", "commands": "", "summary": "OPENAI_API_KEY missing."}

    result = scan.get("result") or {}
    return ai_pentester.generate_pentest_plan(
        api_key=api_key,
        model=_resolve_model(),
        url=result.get("url", "") or "—",
        findings=result.get("findings", []),
        score=result.get("score", {}),
        lang=lang,
    )


def _vm_ai_code_review(code: str, language: str, filename: str, lang: Lang) -> dict:
    """Wrapper for AI SAST code review."""
    from cyber_observatory import ai_pentester

    api_key = _resolve_api_key()
    if not api_key:
        return {"findings": [], "summary": "OPENAI_API_KEY missing.", "truncated": False}

    return ai_pentester.analyze_code(
        api_key=api_key,
        model=_resolve_model(),
        code=code,
        language=language,
        filename=filename,
        lang=lang,
    )


def _render_quick_exploits(result: dict, lang: Lang) -> None:
    """Show 'why vuln + how exploited' for each finding in the quick scan view."""
    sev_rank = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4, "ok": 5}
    findings = sorted(
        [f for f in result.get("findings", [])
         if f.get("severity") not in ("ok", "info") and (f.get("impact") or f.get("attack_steps") or f.get("attack_code"))],
        key=lambda f: sev_rank.get(f.get("severity", "info"), 9),
    )
    if not findings:
        return

    st.markdown(f"#### {t(lang, 'vm_how_exploit')}")
    st.warning(t(lang, "vm_disclaimer_exploit"))

    for f in findings:
        title = f.get("title", "—")
        sev = f.get("severity", "info")
        sev_label = t(lang, f"vm_{sev}")
        with st.expander(f"[{sev_label}] {title}", expanded=False):
            impact = f.get("impact") or ""
            if impact:
                st.markdown(f"**{t(lang, 'vm_why_vuln')}**")
                st.info(impact)

            summary = f.get("attack_summary") or ""
            steps = f.get("attack_steps") or []
            codes = f.get("attack_code") or []

            if summary:
                st.markdown(f"**{t(lang, 'vm_attack_summary')}:** {summary}")
            if steps:
                st.markdown(f"**{t(lang, 'vm_attack_steps')}:**")
                for i, s in enumerate(steps, 1):
                    st.markdown(f"{i}. {s}")
            if codes:
                st.markdown(f"**{t(lang, 'vm_attack_code')}:**")
                for snippet in codes:
                    st.markdown(f"`{snippet.get('label', 'code')}`")
                    st.code(snippet.get("code", ""), language=snippet.get("lang", "bash"))

            refs = f.get("references") or []
            if refs:
                st.markdown(f"**{t(lang, 'vm_refs_label')}:**")
                for r in refs:
                    st.markdown(f"- [{r}]({r})")


def _vm_ai_explain_vuln(v: dict, lang: Lang) -> str:
    api_key = _resolve_api_key()
    if not api_key:
        return _vm_local_explain_vuln(v, lang)
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key, timeout=30.0)
        sys_prompt = (
            "أنت محلل أمن سيبراني سعودي خبير. اشرح الثغرات لأصحاب المواقع بلغة "
            "بسيطة ومباشرة، مع خطوات إصلاح عملية وأمثلة كود/إعدادات. اربط بضوابط "
            "NCA ECC إن أمكن. أجب بالعربية الفصحى."
        ) if lang == "ar" else (
            "You are an expert Saudi cybersecurity analyst. Explain vulnerabilities "
            "to site owners in simple, direct language, with practical fix steps and "
            "concrete examples. Reference NCA ECC where applicable."
        )
        user_msg = (
            f"العنوان: {v['title']}\n"
            f"الخطورة: {v['severity']} (CVSS {v['cvss']})\n"
            f"الوصف: {v['description']}\n"
            f"إرشاد الإصلاح الأوّلي: {v['fix']}\n"
            f"CWE: {v.get('cwe')}\n"
            f"OWASP: {v.get('owasp')}\n"
            "اكتب: ١) شرح بسيط للثغرة، ٢) خطوات إصلاح مرتّبة، ٣) ECC ذو الصلة، ٤) المخاطر المتبقية."
        )
        resp = client.chat.completions.create(
            model=_resolve_model(),
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.4, max_tokens=900,
        )
        return resp.choices[0].message.content or _vm_local_explain_vuln(v, lang)
    except Exception as exc:
        return f"تعذّر الاتصال بـ AI: {exc}\n\n{_vm_local_explain_vuln(v, lang)}"


def _vm_local_explain_vuln(v: dict, lang: Lang) -> str:
    return (
        f"**الثغرة:** {v['title']}\n\n"
        f"**ما الذي يحدث؟** {v['description']}\n\n"
        f"**كيف تُصلَح؟**\n{v['fix']}\n\n"
        f"**التصنيفات:** {v.get('cwe', '')} · {v.get('owasp', '')} · CVSS {v['cvss']}\n"
        "**المخاطر المتبقية:** بعد الإصلاح أعد الفحص لتأكيد إغلاق الثغرة."
    )


def _vm_ai_summary(company: dict, scans: list, vulns: list, lang: Lang) -> str:
    api_key = _resolve_api_key()
    if not api_key:
        return _vm_local_exec_summary(company, scans, vulns)
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key, timeout=45.0)
        open_vulns = [v for v in vulns if v["status"] == "open"]
        sev_count = {s: sum(1 for v in open_vulns if v["severity"] == s)
                     for s in ("critical", "high", "medium", "low")}
        avg_score = round(sum(s["score"] for s in scans) / len(scans)) if scans else 0
        sys_prompt = (
            "أنت كبير محللي الأمن السيبراني. اكتب ملخصاً تنفيذياً للقيادة "
            "العليا بالعربية الفصحى، مكوناً من ٤ فقرات: الوضع الحالي، أهم المخاطر، "
            "خطّة المعالجة المقترحة، التوصيات الفورية. ربط بـ NCA ECC."
        ) if lang == "ar" else (
            "You are a chief cybersecurity analyst. Write a 4-paragraph executive "
            "summary for senior leadership: current posture, top risks, remediation "
            "plan, immediate actions. Reference NCA ECC where helpful."
        )
        ctx = (
            f"الشركة: {company['name']}\n"
            f"عدد الفحوصات: {len(scans)} · متوسط الدرجة: {avg_score}\n"
            f"ثغرات مفتوحة: {len(open_vulns)} (حرج {sev_count['critical']} · "
            f"عالي {sev_count['high']} · متوسط {sev_count['medium']} · "
            f"منخفض {sev_count['low']})\n"
            f"أبرز ٥: " + " | ".join(v["title"] for v in open_vulns[:5])
        )
        resp = client.chat.completions.create(
            model=_resolve_model(),
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": ctx},
            ],
            temperature=0.45, max_tokens=1400,
        )
        return resp.choices[0].message.content or _vm_local_exec_summary(company, scans, vulns)
    except Exception as exc:
        return f"تعذّر الاتصال بـ AI: {exc}\n\n{_vm_local_exec_summary(company, scans, vulns)}"


def _vm_local_exec_summary(company: dict, scans: list, vulns: list) -> str:
    open_vulns = [v for v in vulns if v["status"] == "open"]
    crit = sum(1 for v in open_vulns if v["severity"] == "critical")
    high = sum(1 for v in open_vulns if v["severity"] == "high")
    avg = round(sum(s["score"] for s in scans) / len(scans)) if scans else 0
    return (
        f"الوضع الراهن لأمن {company['name']}: متوسط درجة الأمان {avg}/100 عبر "
        f"{len(scans)} فحصاً. تم رصد {len(open_vulns)} ثغرة مفتوحة منها "
        f"{crit} حرجة و{high} عالية الخطورة.\n\n"
        "التوصيات الفورية: ابدأ بالثغرات الحرجة (تعرّض ملفات حسّاسة، مشاكل TLS)، "
        "ثم أغلق ترويسات الحماية (HSTS, CSP) وفعّل سجلات SPF/DMARC."
    )


def _page_scanner(lang: Lang) -> None:
    """Vulnerability Management Platform — multi-section UI."""
    from cyber_observatory import vm_data, vm_ui

    vm_data.init_state()
    vm_data.bootstrap_super_admin(st.session_state.get("user") or "admin")

    _page_header(t(lang, "page_scanner"), t(lang, "scanner_caption"))
    st.markdown('<div class="vm-platform">', unsafe_allow_html=True)

    vm_ui.render_banner(lang)
    vm_ui.render_role_switcher(lang)

    user = vm_data.current_user()
    role = user["role"] if user else vm_data.ROLE_MEMBER
    is_super = (role == vm_data.ROLE_SUPER)
    has_companies = bool(vm_data.all_companies())
    user_has_company = bool(user and user.get("company_id"))

    # Onboarding when no company exists yet, or when super admin without a tenant
    needs_onboarding = (not has_companies) or (is_super and not user_has_company)
    if needs_onboarding:
        vm_ui.render_onboarding(lang)
        st.markdown("</div>", unsafe_allow_html=True)
        return

    section_keys: list[tuple[str, str]] = [
        ("dashboard", "vm_section_dashboard"),
        ("sites",     "vm_section_sites"),
        ("scans",     "vm_section_scans"),
        ("vulns",     "vm_section_vulns"),
        ("pentester", "vm_section_pentester"),
        ("codereview","vm_section_codereview"),
        ("reports",   "vm_section_reports"),
        ("team",      "vm_section_team"),
        ("subs",      "vm_section_subs"),
        ("audit",     "vm_section_audit"),
    ]
    if is_super:
        section_keys.append(("admin", "vm_section_admin"))

    tabs = st.tabs([t(lang, k) for (_, k) in section_keys])
    for (sect_id, _), tab in zip(section_keys, tabs):
        with tab:
            if sect_id == "dashboard":
                vm_ui.render_dashboard(lang)
            elif sect_id == "sites":
                vm_ui.render_sites(lang)
            elif sect_id == "scans":
                vm_ui.render_scans(lang, _vm_run_scan)
            elif sect_id == "vulns":
                vm_ui.render_vulns(lang, _vm_ai_explain_vuln)
            elif sect_id == "pentester":
                vm_ui.render_ai_pentester(
                    lang, _vm_ai_pentest_plan, has_api_key=bool(_resolve_api_key()),
                )
            elif sect_id == "codereview":
                vm_ui.render_code_review(
                    lang, _vm_ai_code_review, has_api_key=bool(_resolve_api_key()),
                )
            elif sect_id == "reports":
                vm_ui.render_reports(lang, _vm_ai_summary)
            elif sect_id == "team":
                vm_ui.render_team(lang)
            elif sect_id == "subs":
                vm_ui.render_subscription(lang)
            elif sect_id == "audit":
                vm_ui.render_audit(lang)
            elif sect_id == "admin":
                vm_ui.render_admin(lang)

    st.markdown("</div>", unsafe_allow_html=True)

    with st.expander(t(lang, "vm_quick_scan"), expanded=False):
        st.caption(t(lang, "scanner_caption"))
        with st.form("vm_quick_scan_form", clear_on_submit=False):
            cols = st.columns([5, 1])
            url_q = cols[0].text_input(
                "URL", value=st.session_state.get("scanner_url", ""),
                placeholder=t(lang, "scanner_input_placeholder"),
                key="vm_quick_url", label_visibility="collapsed",
            )
            run_q = cols[1].form_submit_button(t(lang, "scanner_run"),
                                               type="primary", use_container_width=True)
        if run_q:
            target = (url_q or "").strip()
            if not target:
                st.warning(t(lang, "scanner_url_required"))
            else:
                try:
                    with st.spinner(t(lang, "scanner_running")):
                        result = _vm_run_scan(target)
                    st.session_state.scanner_url = target
                    st.session_state.scanner_result = result
                    st.session_state.scanner_error = ""
                    _audit("scan", "website", result.get("host", "—"),
                           f"score={result['score']['score']} grade={result['score']['grade']}")
                except Exception as exc:
                    st.session_state.scanner_result = None
                    st.session_state.scanner_error = str(exc)
        if st.session_state.get("scanner_error"):
            st.error(st.session_state.scanner_error)
        result = st.session_state.get("scanner_result")
        if result:
            st.markdown(_scanner_html_for_result(result, lang), unsafe_allow_html=True)
            _render_quick_exploits(result, lang)
            rows = [
                {
                    "severity": f.get("severity", ""), "domain": f.get("domain", ""),
                    "title": f.get("title", ""), "description": f.get("description", ""),
                    "fix": f.get("fix", ""), "evidence": f.get("evidence", ""),
                    "ecc_ref": f.get("ecc_ref", ""),
                } for f in result["findings"]
            ]
            if rows:
                csv = pd.DataFrame(rows).to_csv(index=False).encode("utf-8-sig")
                st.download_button(
                    t(lang, "scanner_export"), data=csv,
                    file_name=f"scan-{result.get('host', 'site')}.csv",
                    mime="text/csv",
                )


# =========================================================================
#  AI Assistant
# =========================================================================
def _read_secret(name: str) -> str | None:
    val: str | None = None
    try:
        val = st.secrets.get(name)  # type: ignore[attr-defined]
    except Exception:
        val = None
    if not val:
        val = os.environ.get(name)
    if val is None:
        return None
    s = str(val).strip()
    if len(s) >= 2 and ((s[0] == s[-1] == '"') or (s[0] == s[-1] == "'")):
        s = s[1:-1].strip()
    return s or None


def _resolve_api_key() -> str | None:
    return _read_secret("OPENAI_API_KEY")


def _resolve_model() -> str:
    return _read_secret("OPENAI_MODEL") or "gpt-4o-mini"


def _resolve_extra_context() -> str | None:
    return _read_secret("AI_SA_CYBER_CONTEXT_EXTRA")


def _check_openai_connection(api_key: str) -> tuple[bool, str]:
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key, timeout=15.0)
        client.chat.completions.create(
            model=_resolve_model(),
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=1, temperature=0.0,
        )
        return True, "OK"
    except Exception as exc:
        return False, str(exc)


def _build_context_payload(lang: Lang) -> tuple[str, dict[str, float | int], pd.DataFrame]:
    _, merged, stats = _filter_controls_records()
    open_gaps = (merged[merged["status"].isin(["partial", "not_started"])]
                 if "status" in merged.columns else merged)
    open_refs = (open_gaps["control_ref"].dropna().astype(str).unique().tolist()[:10]
                 if "control_ref" in open_gaps.columns else [])
    domain_breakdown = ""
    if not merged.empty and "domain_ar" in merged.columns and "status" in merged.columns:
        g = (merged.groupby(["domain_ar", "status"], dropna=False)
             .size().reset_index(name="count").head(20))
        domain_breakdown = "\n".join(
            f"- {row['domain_ar']} → {row['status']}: {int(row['count'])}" for _, row in g.iterrows()
        )
    summary_lang = "العربية" if lang == "ar" else "English"
    payload = (
        f"اللغة المطلوبة للجواب: {summary_lang}.\n"
        f"إجمالي الضوابط: {int(stats['total_controls'])}.\n"
        f"إجمالي السجلات: {int(stats['records_total'])}.\n"
        f"نسبة الامتثال: {stats['compliance_rate']}%.\n"
        f"متوسط النضج: {stats['avg_maturity']}/5.\n"
        f"compliant={int(stats['compliant'])}, partial={int(stats['partial'])}, "
        f"not_started={int(stats['not_started'])}, not_applicable={int(stats['not_applicable'])}.\n"
        f"الفجوات المفتوحة (partial + not_started): {int(len(open_gaps))}.\n"
        f"ضوابط عالية الخطورة: {int(stats['high_risk_count'])}.\n"
        f"أبرز مراجع الضوابط ذات الفجوات: {', '.join(open_refs) if open_refs else '—'}.\n"
        f"ملخص الفجوات الحالي (إن وُجد): {st.session_state.gap_summary or '—'}.\n"
        f"توزيع الحالات حسب المجال:\n{domain_breakdown or '—'}"
    )
    return payload, stats, open_gaps


def _stream_openai(prompt: str, lang: Lang, api_key: str) -> Iterator[str]:
    from openai import OpenAI
    payload, _, _ = _build_context_payload(lang)
    system = chat_system_prompt(structured_insights=True, extra_context=_resolve_extra_context())
    if lang == "en":
        system += ("\n\n— Note: reply in clear English while preserving NCA/ECC focus.")
    history: list[dict[str, str]] = [{"role": "system", "content": system}]
    for m in st.session_state.chat[-8:]:
        if m.get("role") in ("user", "assistant") and m.get("content"):
            history.append({"role": m["role"], "content": str(m["content"])})
    user_block = (
        "### لقطة امتثال (منطق المنصة)\n"
        f"{payload}\n\n"
        f"### تحليل الفجوات الأخير\n{st.session_state.gap_summary or '—'}\n\n"
        "### توجيه للإجابة\n"
        "- اربط الإجابة بمتطلبات NCA/ECC ووضع المستخدم.\n"
        "- إن طُلبت حلول قدّم خطوات عملية + أدلة + أولوية.\n"
        f"### السؤال\n{prompt}"
    )
    history.append({"role": "user", "content": user_block})
    client = OpenAI(api_key=api_key, timeout=60.0)
    stream = client.chat.completions.create(
        model=_resolve_model(), messages=history,
        temperature=0.38, max_tokens=2800, stream=True,
    )
    for chunk in stream:
        try:
            delta = chunk.choices[0].delta.content or ""
        except Exception:
            delta = ""
        if delta:
            yield delta


def _local_fallback_answer(prompt: str, lang: Lang) -> str:
    payload, stats, open_gaps = _build_context_payload(lang)
    refs = (open_gaps["control_ref"].dropna().astype(str).unique().tolist()[:5]
            if "control_ref" in open_gaps.columns else [])
    refs_line = "، ".join(refs) if refs else "—"
    return (
        f"**سؤالك:** {prompt}\n\n"
        f"**قراءة من المنصة**\n"
        f"- نسبة الامتثال: **{stats['compliance_rate']}%**\n"
        f"- متوسط النضج: **{stats['avg_maturity']}/5**\n"
        f"- الفجوات المفتوحة: **{int(len(open_gaps))}**\n"
        f"- ضوابط عالية الخطورة: **{int(stats['high_risk_count'])}**\n"
        f"- أولويات: {refs_line}\n\n"
        f"**خطة عملية مقترحة**\n"
        "1. ابدأ بالضوابط ذات الخطورة الحرجة (critical).\n"
        "2. ركّز على not_started ثم partial.\n"
        "3. وثّق الأدلة وحدّث المسؤول والمهلة.\n"
        "4. كرّر تحليل الفجوات أسبوعياً وراقب الاتجاه.\n"
    )


def _page_assistant(lang: Lang) -> None:
    _page_header(t(lang, "menu_assistant"))
    api_key = _resolve_api_key()
    model = _resolve_model() if api_key else "—"
    status_label = (f"{t(lang, 'ai_using_gpt')} · {model}" if api_key
                    else t(lang, "ai_local_mode"))
    status_chip = "success" if api_key else "warn"

    cols = st.columns([3, 1, 1])
    with cols[0]:
        st.markdown(
            f'<div class="status-bar"><span>{status_label}</span>'
            f'<span class="chip {status_chip}">{ "OpenAI" if api_key else "Local" }</span></div>',
            unsafe_allow_html=True,
        )
    with cols[1]:
        if st.button("اختبار الاتصال" if lang == "ar" else "Test connection", use_container_width=True):
            if not api_key:
                st.warning("لم يتم العثور على OPENAI_API_KEY.")
            else:
                with st.spinner("جارٍ الاختبار…"):
                    ok, msg = _check_openai_connection(api_key)
                if ok:
                    st.success(f"الاتصال يعمل · النموذج: {model}")
                else:
                    st.error("تعذر الاتصال. التفاصيل: " + msg)
    with cols[2]:
        if st.button(t(lang, "clear_chat"), use_container_width=True):
            st.session_state.chat = []
            st.rerun()

    for msg in st.session_state.chat:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input(t(lang, "assistant_hint")):
        st.session_state.chat.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            placeholder = st.empty()
            if api_key:
                buf = ""
                try:
                    with st.spinner(t(lang, "thinking")):
                        for chunk in _stream_openai(prompt, lang, api_key):
                            buf += chunk
                            placeholder.markdown(buf + "▌")
                    placeholder.markdown(buf if buf else _local_fallback_answer(prompt, lang))
                    answer = buf or _local_fallback_answer(prompt, lang)
                except Exception as exc:
                    answer = f"{t(lang, 'ai_error')}: {exc}\n\n{_local_fallback_answer(prompt, lang)}"
                    placeholder.markdown(answer)
            else:
                answer = _local_fallback_answer(prompt, lang)
                placeholder.markdown(answer)
        st.session_state.chat.append({"role": "assistant", "content": answer})


# =========================================================================
#  Footer
# =========================================================================
def _footer(lang: Lang) -> None:
    label = "© درع سيبراني · مرجع رسمي:"
    st.markdown(
        f'<div class="app-footer">{label} '
        f'<a href="{NCA_OFFICIAL_URL}" target="_blank">nca.gov.sa</a> · '
        f'<a href="{ECC_PDF_URL}" target="_blank">ECC-2-2024 PDF</a> · '
        f'<a href="{ECC_IMPLEMENTATION_GUIDE_URL}" target="_blank">دليل التطبيق</a></div>',
        unsafe_allow_html=True,
    )


# =========================================================================
#  Router
# =========================================================================
PAGES = {
    "overview":           _page_overview,
    "kpis":               _page_kpis,
    "maturity":           _page_maturity,
    "reports":            _page_reports,
    "compliance_browser": _page_compliance_browser,
    "records":            _page_records,
    "gaps":               _page_gaps,
    "action_plan":        _page_action_plan,
    "risk_register":      _page_risk_register,
    "audit_log":          _page_audit_log,
    "import":             _page_import,
    "frameworks":         _page_frameworks,
    "controls":           _page_controls,
    "ecc":                _page_ecc,
    "departments":        _page_departments,
    "control_codes":      _page_control_codes,
    "preferences":        _page_preferences,
    "scanner":            _page_scanner,
    "assistant":          _page_assistant,
}


def main() -> None:
    _init_state()
    _restore_session_from_url()
    lang: Lang = st.session_state.lang
    inject_theme(lang, st.session_state.theme)

    if not st.session_state.authenticated:
        _login_page(lang)
        return

    _persist_session_to_url()
    st.markdown(hero_html(lang), unsafe_allow_html=True)
    _top_nav(lang)

    page_fn = PAGES.get(st.session_state.nav, _page_overview)
    page_fn(lang)
    _footer(lang)
