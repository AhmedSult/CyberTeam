from __future__ import annotations

import io
import os
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
    calc_stats,
    seed_controls,
    seed_departments,
    seed_frameworks,
    seed_records,
)
from cyber_observatory.i18n import Lang, t
from cyber_observatory.theme import hero_html, inject_theme

DEMO_USERS = {
    "admin": "admin",
    "admin@example.com": "admin",
    "auditor": "auditor",
}


# =========================================================================
#  Session state
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
    st.session_state.setdefault("table_search", "")
    st.session_state.setdefault("gap_summary", "")
    if "frameworks_df" not in st.session_state:
        st.session_state.frameworks_df = seed_frameworks()
    if "departments_df" not in st.session_state:
        st.session_state.departments_df = seed_departments()
    if "controls_df" not in st.session_state:
        st.session_state.controls_df = seed_controls()
    if "records_df" not in st.session_state:
        st.session_state.records_df = seed_records()


def _go(page: str) -> None:
    st.session_state.nav = page
    st.rerun()


# =========================================================================
#  Login page
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
                st.rerun()
            else:
                st.error(t(lang, "login_invalid"))

    st.markdown(
        f'<div class="login-demo"><b>{t(lang, "login_demo")}:</b> {t(lang, "login_demo_value")}</div>',
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)


# =========================================================================
#  Top navigation (with dropdown popovers)
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
    cols = st.columns([2.0, 1.2, 1.1, 1.05, 1.1, 1.3, 1.0, 1.4], gap="small")

    with cols[0]:
        if st.button(f"🛡️ {t(lang, 'title')}", key="brand_home", use_container_width=True):
            _go("overview")

    with cols[1]:
        with st.popover(t(lang, "menu_dashboard"), use_container_width=True):
            _menu_button(lang, "overview", "page_overview")
            _menu_button(lang, "kpis", "page_kpis")
            _menu_button(lang, "reports", "page_reports")

    with cols[2]:
        with st.popover(t(lang, "menu_compliance"), use_container_width=True):
            _menu_button(lang, "records", "page_records")
            _menu_button(lang, "gaps", "page_gaps")
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
            _menu_button(lang, "preferences", "page_preferences")

    with cols[5]:
        if st.button(
            t(lang, "menu_assistant"),
            key="menu_assistant_btn",
            use_container_width=True,
            type="primary" if st.session_state.nav == "assistant" else "secondary",
        ):
            _go("assistant")

    with cols[6]:
        with st.popover(t(lang, "menu_links"), use_container_width=True):
            st.markdown(
                f"""
<a href="{NCA_OFFICIAL_URL}" target="_blank">{t(lang, "link_nca")}</a>
<a href="https://haseen.sa" target="_blank">{t(lang, "link_haseen")}</a>
<a href="https://academy.nca.gov.sa" target="_blank">{t(lang, "link_academy")}</a>
<a href="{ECC_PDF_URL}" target="_blank">{t(lang, "link_ecc_pdf")}</a>
<a href="https://nca.gov.sa/ar/awareness/" target="_blank">{t(lang, "link_awareness")}</a>
<a href="https://nca.gov.sa/ar/cyberalerts/" target="_blank">{t(lang, "link_alerts")}</a>
""",
                unsafe_allow_html=True,
            )

    with cols[7]:
        user_label = st.session_state.user or t(lang, "menu_account")
        with st.popover(f"👤 {user_label}", use_container_width=True):
            st.markdown(
                f"<div style='padding:.4rem .6rem; color:#888; font-size:.85rem;'>"
                f"{t(lang, 'menu_account')}: <b>{st.session_state.user or '—'}</b></div>",
                unsafe_allow_html=True,
            )
            st.markdown("---")
            st.markdown(
                f"<div style='padding:0 .6rem; color:#888; font-size:.8rem;'>{t(lang, 'language')}</div>",
                unsafe_allow_html=True,
            )
            st.radio(
                "Lang",
                options=["ar", "en"],
                key="lang",
                horizontal=True,
                label_visibility="collapsed",
                format_func=lambda v: "العربية" if v == "ar" else "English",
            )
            st.markdown(
                f"<div style='padding:0 .6rem; color:#888; font-size:.8rem;'>{t(lang, 'theme_label')}</div>",
                unsafe_allow_html=True,
            )
            st.radio(
                "Theme",
                options=["light", "dark"],
                key="theme",
                horizontal=True,
                label_visibility="collapsed",
                format_func=lambda v: "☀️ Light" if v == "light" else "🌙 Dark",
            )
            st.markdown("---")
            if st.button(t(lang, "menu_logout"), key="logout_btn", use_container_width=True):
                for k in ("authenticated", "user", "chat", "nav"):
                    st.session_state.pop(k, None)
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
        fw = int(st.session_state.framework_id)
        controls = controls[controls["framework_id"] == fw]
    if st.session_state.department_id:
        dept = int(st.session_state.department_id)
        records = records[records["department_id"] == dept]

    merged = records.merge(controls, left_on="control_id", right_on="control_pk", how="left")
    merged = merged.merge(
        departments[["department_pk", "department_name_ar", "department_code"]],
        left_on="department_id",
        right_on="department_pk",
        how="left",
    )
    merged = merged.merge(
        frameworks[["framework_pk", "framework_name_ar"]],
        left_on="framework_id",
        right_on="framework_pk",
        how="left",
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


def _render_filters(lang: Lang) -> None:
    frameworks = st.session_state.frameworks_df.to_dict("records")
    departments = st.session_state.departments_df.to_dict("records")
    f1, f2, f3 = st.columns([1, 1, 2])
    with f1:
        fw_opts = {"": t(lang, "all")}
        fw_opts.update({str(x["id"]): f'{x["name_ar"]} ({x["code"]})' for x in frameworks})
        st.selectbox(t(lang, "framework"), options=list(fw_opts.keys()),
                     format_func=lambda x: fw_opts[x], key="framework_id")
    with f2:
        dep_opts = {"": t(lang, "all")}
        dep_opts.update({str(x["id"]): f'{x.get("code") or "-"} {x["name_ar"]}' for x in departments})
        st.selectbox(t(lang, "department"), options=list(dep_opts.keys()),
                     format_func=lambda x: dep_opts[x], key="department_id")
    with f3:
        st.text_input(t(lang, "search_table"), key="table_search",
                      placeholder=t(lang, "search_placeholder"))


# =========================================================================
#  Pages
# =========================================================================
def _page_overview(lang: Lang) -> None:
    _, merged, stats = _filter_controls_records()

    fr_count = int(len(st.session_state.frameworks_df))
    dp_count = int(len(st.session_state.departments_df))
    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric(t(lang, "metric_controls"), f"{stats['total_controls']}")
    m2.metric(t(lang, "metric_rate"), f"{stats['compliance_rate']}%")
    m3.metric(t(lang, "metric_gaps"), f"{stats['gap_open_count']}")
    m4.metric(t(lang, "metric_records"), f"{stats['records_total']}")
    m5.metric(t(lang, "metric_frameworks"), f"{fr_count}")
    m6.metric(t(lang, "metric_departments"), f"{dp_count}")

    chart_df = pd.DataFrame([
        {"status": "compliant", "count": stats["compliant"]},
        {"status": "partial", "count": stats["partial"]},
        {"status": "not_started", "count": stats["not_started"]},
        {"status": "not_applicable", "count": stats["not_applicable"]},
    ])
    cmap = {
        "compliant": "#10b981",
        "partial": "#f59e0b",
        "not_started": "#ef4444",
        "not_applicable": "#94a3b8",
    }
    fig = px.bar(chart_df, x="status", y="count", color="status",
                 title=t(lang, "compliance_distribution"), color_discrete_map=cmap)
    fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                      showlegend=False, margin=dict(t=44, l=10, r=10, b=10))
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    if not merged.empty and "domain_ar" in merged.columns and "status" in merged.columns:
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
    cols[1].metric("Compliant", int(stats["compliant"]))
    cols[2].metric("Partial",   int(stats["partial"]))
    cols[3].metric("Not started", int(stats["not_started"]))

    if not merged.empty and "framework_name_ar" in merged.columns:
        by_fw = (
            merged.groupby(["framework_name_ar", "status"], dropna=False)
            .size().reset_index(name="count")
        )
        fig = px.bar(by_fw, x="framework_name_ar", y="count", color="status",
                     barmode="group", title="Compliance status per framework",
                     color_discrete_map={
                         "compliant": "#10b981", "partial": "#f59e0b",
                         "not_started": "#ef4444", "not_applicable": "#94a3b8",
                     })
        fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                          margin=dict(t=44, l=10, r=10, b=10))
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def _page_reports(lang: Lang) -> None:
    _page_header(t(lang, "page_reports"), t(lang, "reports_caption"))
    _, merged, _ = _filter_controls_records()
    csv_full = merged.to_csv(index=False).encode("utf-8-sig")
    open_gaps = (
        merged[merged["status"].isin(["partial", "not_started"])]
        if "status" in merged.columns else pd.DataFrame()
    )
    csv_gaps = open_gaps.to_csv(index=False).encode("utf-8-sig")

    c1, c2 = st.columns(2)
    with c1:
        st.download_button(t(lang, "report_csv_full"), data=csv_full,
                           file_name="compliance-full.csv", mime="text/csv",
                           use_container_width=True)
    with c2:
        st.download_button(t(lang, "report_gaps"), data=csv_gaps,
                           file_name="compliance-gaps.csv", mime="text/csv",
                           use_container_width=True)

    st.dataframe(merged, use_container_width=True, hide_index=True)


def _page_records(lang: Lang) -> None:
    _page_header(t(lang, "page_records"))
    _render_filters(lang)
    _, merged, _ = _filter_controls_records()
    show_cols = ["record_id", "control_ref", "title_ar", "domain_ar",
                 "framework_name_ar", "department_name_ar", "status", "evidence_summary"]
    available = [c for c in show_cols if c in merged.columns]
    st.dataframe(merged[available], use_container_width=True, hide_index=True)

    if not merged.empty and "record_id" in merged.columns:
        st.markdown(f'<div class="section-title">{t(lang, "update_status")}</div>', unsafe_allow_html=True)
        r1, r2, r3 = st.columns([1, 1, 1])
        with r1:
            rec_id = st.selectbox(t(lang, "record_id"),
                                  options=[int(x) for x in merged["record_id"].dropna().tolist()])
        with r2:
            new_status = st.selectbox(t(lang, "new_status"),
                                      options=["not_started", "partial", "compliant", "not_applicable"])
        with r3:
            st.write("")
            if st.button(t(lang, "save_status"), type="primary", use_container_width=True):
                df = st.session_state.records_df.copy()
                df.loc[df["id"] == rec_id, "status"] = new_status
                st.session_state.records_df = df
                st.success(t(lang, "saved_ok"))
                st.rerun()


def _page_gaps(lang: Lang) -> None:
    _page_header(t(lang, "page_gaps"))
    _render_filters(lang)
    _, merged, _ = _filter_controls_records()
    if st.button(t(lang, "gap_run"), type="primary"):
        open_gaps = (
            merged[merged["status"].isin(["partial", "not_started"])]
            if "status" in merged.columns else pd.DataFrame()
        )
        if open_gaps.empty:
            st.session_state.gap_summary = t(lang, "no_gaps")
        else:
            refs = ", ".join(open_gaps["control_ref"].dropna().astype(str).head(8).tolist())
            st.session_state.gap_summary = (
                f"تم رصد {len(open_gaps)} سجلات بحاجة معالجة. "
                f"أعلى الأولويات: {refs}. "
                "التوصية: ابدأ بالضوابط ذات حالة not_started، ثم أغلق partial بالأدلة."
            )
        st.success(t(lang, "gap_done"))
    if st.session_state.gap_summary:
        st.info(st.session_state.gap_summary)


def _page_import(lang: Lang) -> None:
    _page_header(t(lang, "page_import"), t(lang, "upload_hint"))
    up = st.file_uploader("CSV / XLSX", type=["csv", "xlsx", "xls"])
    if up is not None:
        raw = up.read()
        if up.name.lower().endswith(".csv"):
            udf = pd.read_csv(io.BytesIO(raw))
        else:
            udf = pd.read_excel(io.BytesIO(raw), sheet_name=0)
        st.dataframe(udf.head(50), use_container_width=True, hide_index=True)


def _page_frameworks(lang: Lang) -> None:
    _page_header(t(lang, "page_frameworks"), t(lang, "frameworks_caption"))
    df = st.session_state.frameworks_df.copy()
    df = df.rename(columns={"id": "ID", "code": "Code", "name_ar": "الاسم"})
    st.dataframe(df, use_container_width=True, hide_index=True)


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
    fw_map = {int(x["id"]): x["name_ar"] for x in fw_df}
    controls = controls.assign(framework=controls["framework_id"].map(fw_map))
    show = ["id", "control_ref", "title_ar", "domain_ar", "framework"]
    available = [c for c in show if c in controls.columns]
    st.dataframe(controls[available], use_container_width=True, hide_index=True)


def _page_ecc(lang: Lang) -> None:
    _page_header(t(lang, "page_ecc"), t(lang, "ecc_caption"))
    st.markdown(
        f'<a class="link-card" href="{ECC_PDF_URL}" target="_blank">'
        f'<span class="lc-title">📘 {t(lang, "ecc_open")}</span>'
        f'<span class="lc-desc">{ECC_PDF_URL}</span></a>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<a class="link-card" href="{NCA_OFFICIAL_URL}" target="_blank">'
        f'<span class="lc-title">🔗 {t(lang, "link_nca")}</span>'
        f'<span class="lc-desc">{NCA_OFFICIAL_URL}</span></a>',
        unsafe_allow_html=True,
    )


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
            st.success(t(lang, "added_ok"))
            st.rerun()


def _page_control_codes(lang: Lang) -> None:
    _page_header(t(lang, "page_control_codes"))
    df = st.session_state.controls_df.copy()
    fw_map = {int(x["id"]): x["name_ar"] for x in st.session_state.frameworks_df.to_dict("records")}
    df = df.assign(framework=df["framework_id"].map(fw_map))
    edited = st.data_editor(
        df,
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",
        column_config={
            "id": st.column_config.NumberColumn("ID", disabled=True),
            "framework_id": st.column_config.NumberColumn(t(lang, "framework"), disabled=True),
            "framework": st.column_config.TextColumn(t(lang, "framework"), disabled=True),
            "control_ref": st.column_config.TextColumn(t(lang, "code")),
            "title_ar": st.column_config.TextColumn(t(lang, "name_ar")),
            "domain_ar": st.column_config.TextColumn("Domain"),
        },
        key="controls_editor",
    )
    if st.button(t(lang, "save_status"), type="primary"):
        cleaned = edited.drop(columns=[c for c in ["framework"] if c in edited.columns])
        st.session_state.controls_df = cleaned
        st.success(t(lang, "saved_ok"))


def _page_preferences(lang: Lang) -> None:
    _page_header(t(lang, "page_preferences"))
    c1, c2 = st.columns(2)
    with c1:
        st.selectbox(t(lang, "language"), options=["ar", "en"], key="lang",
                     format_func=lambda v: "العربية" if v == "ar" else "English")
    with c2:
        st.selectbox(t(lang, "theme_label"), options=["light", "dark"], key="theme",
                     format_func=lambda v: ("☀️ Light" if v == "light" else "🌙 Dark"))


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
    open_gaps = (
        merged[merged["status"].isin(["partial", "not_started"])]
        if "status" in merged.columns else merged
    )
    open_refs = (
        open_gaps["control_ref"].dropna().astype(str).unique().tolist()[:10]
        if "control_ref" in open_gaps.columns else []
    )
    domain_breakdown = ""
    if not merged.empty and "domain_ar" in merged.columns and "status" in merged.columns:
        g = (
            merged.groupby(["domain_ar", "status"], dropna=False)
            .size().reset_index(name="count").head(20)
        )
        domain_breakdown = "\n".join(
            f"- {row['domain_ar']} → {row['status']}: {int(row['count'])}" for _, row in g.iterrows()
        )
    summary_lang = "العربية" if lang == "ar" else "English"
    payload = (
        f"اللغة المطلوبة للجواب: {summary_lang}.\n"
        f"إجمالي الضوابط: {int(stats['total_controls'])}.\n"
        f"إجمالي السجلات: {int(stats['records_total'])}.\n"
        f"نسبة الامتثال: {stats['compliance_rate']}%.\n"
        f"compliant={int(stats['compliant'])}, partial={int(stats['partial'])}, "
        f"not_started={int(stats['not_started'])}, not_applicable={int(stats['not_applicable'])}.\n"
        f"الفجوات المفتوحة (partial + not_started): {int(len(open_gaps))}.\n"
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
        system += (
            "\n\n— Note: the user is asking in English; reply in clear, concise English "
            "while preserving the same NCA/ECC focus and platform-data discipline."
        )
    history: list[dict[str, str]] = [{"role": "system", "content": system}]
    for m in st.session_state.chat[-8:]:
        if m.get("role") in ("user", "assistant") and m.get("content"):
            history.append({"role": m["role"], "content": str(m["content"])})
    user_block = (
        "### لقطة امتثال (منطق المنصة — مدخلات المستخدم وقاعدة البيانات)\n"
        f"{payload}\n\n"
        f"### تحليل الفجوات الأخير (من لوحة التحكم)\n{st.session_state.gap_summary or '—'}\n\n"
        "### توجيه للإجابة (GPT + منطق)\n"
        "- اربط الإجابة بين متطلبات NCA/ECC ووضع المستخدم (اللقطة أعلاه).\n"
        "- إن طُلب «حلولاً» قدّم خطوات عملية وأدلة مقترحة وأولوية تنفيذ، وصِغها كتوصيات لا قراراً رسمياً.\n"
        f"### سؤال المستخدم\n{prompt}"
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
    refs = (
        open_gaps["control_ref"].dropna().astype(str).unique().tolist()[:5]
        if "control_ref" in open_gaps.columns else []
    )
    refs_line = "، ".join(refs) if refs else "—"
    if lang == "ar":
        return (
            f"**سؤالك:** {prompt}\n\n"
            f"**قراءة سريعة من المنصة**\n"
            f"- نسبة الامتثال: **{stats['compliance_rate']}%**\n"
            f"- الفجوات المفتوحة: **{int(len(open_gaps))}**\n"
            f"- أولويات مقترحة: {refs_line}\n\n"
            f"**خطة عملية مقترحة**\n"
            f"1. ابدأ بالضوابط ذات الحالة `not_started` ووثّق المسؤول والمهلة.\n"
            f"2. حوّل `partial` إلى `compliant` بإضافة الأدلة وروابط السياسات.\n"
            f"3. حدّث `evidence_summary` لكل سجل بدليل يمكن مراجعته.\n"
            f"4. كرر التحليل أسبوعياً وراقب الاتجاه في صفحة النظرة العامة.\n"
        )
    return (
        f"**Your question:** {prompt}\n\n"
        f"**Quick platform read**\n"
        f"- Compliance rate: **{stats['compliance_rate']}%**\n"
        f"- Open gaps: **{int(len(open_gaps))}**\n"
        f"- Suggested priorities: {refs_line}\n\n"
        f"**Suggested action plan**\n"
        f"1. Start with `not_started` controls; assign owners and deadlines.\n"
        f"2. Move `partial` to `compliant` by attaching evidence.\n"
        f"3. Update `evidence_summary` with auditable proof on every record.\n"
        f"4. Re-run gap analysis weekly and watch the overview trend.\n"
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
                st.warning("لم يتم العثور على OPENAI_API_KEY في Secrets/البيئة." if lang == "ar"
                           else "OPENAI_API_KEY not found.")
            else:
                with st.spinner("جارٍ الاختبار…" if lang == "ar" else "Testing…"):
                    ok, msg = _check_openai_connection(api_key)
                if ok:
                    st.success(f"الاتصال يعمل · النموذج: {model}" if lang == "ar"
                               else f"Connection OK · Model: {model}")
                else:
                    st.error((("تعذر الاتصال. التفاصيل: ") if lang == "ar" else "Failed: ") + msg)
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
    label = "© درع سيبراني · مرجع رسمي:" if lang == "ar" else "© Cyber Shield · Official reference:"
    st.markdown(
        f'<div class="app-footer">{label} '
        f'<a href="{NCA_OFFICIAL_URL}" target="_blank">nca.gov.sa</a></div>',
        unsafe_allow_html=True,
    )


# =========================================================================
#  Router
# =========================================================================
PAGES = {
    "overview":      _page_overview,
    "kpis":          _page_kpis,
    "reports":       _page_reports,
    "records":       _page_records,
    "gaps":          _page_gaps,
    "import":        _page_import,
    "frameworks":    _page_frameworks,
    "controls":      _page_controls,
    "ecc":           _page_ecc,
    "departments":   _page_departments,
    "control_codes": _page_control_codes,
    "preferences":   _page_preferences,
    "assistant":     _page_assistant,
}


def main() -> None:
    _init_state()
    lang: Lang = st.session_state.lang
    inject_theme(lang, st.session_state.theme)

    if not st.session_state.authenticated:
        _login_page(lang)
        return

    st.markdown(hero_html(lang), unsafe_allow_html=True)
    _top_nav(lang)

    page_fn = PAGES.get(st.session_state.nav, _page_overview)
    page_fn(lang)
    _footer(lang)
