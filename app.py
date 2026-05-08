from __future__ import annotations

import io
from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st

from cyber_observatory.client import ApiClient
from cyber_observatory.demo_data import demo_records, demo_stats
from cyber_observatory.i18n import Lang, t
from cyber_observatory.theme import hero_html, inject_theme


def _init_state() -> None:
    st.session_state.setdefault("lang", "ar")
    st.session_state.setdefault("theme", "light")
    st.session_state.setdefault("nav", "overview")
    st.session_state.setdefault("api_url", st.secrets.get("API_URL", "http://127.0.0.1:8000"))
    st.session_state.setdefault("token", "")
    st.session_state.setdefault("chat", [])
    st.session_state.setdefault("framework_id", "")
    st.session_state.setdefault("department_id", "")
    st.session_state.setdefault("table_search", "")


def _top_nav(lang: Lang) -> None:
    tabs = {
        "overview": t(lang, "nav_overview"),
        "compliance": t(lang, "nav_compliance"),
        "assistant": t(lang, "nav_assistant"),
        "api": t(lang, "nav_api"),
    }
    cols = st.columns(4, gap="small")
    for idx, (key, label) in enumerate(tabs.items()):
        with cols[idx]:
            if st.button(
                label,
                use_container_width=True,
                type="primary" if st.session_state.nav == key else "secondary",
                key=f"nav_{key}",
            ):
                st.session_state.nav = key


def _sidebar(lang: Lang) -> ApiClient:
    with st.sidebar:
        st.selectbox("Language", ["ar", "en"], key="lang")
        st.selectbox("Theme", ["light", "dark"], key="theme")
        st.text_input(t(lang, "api_url"), key="api_url")

        client = ApiClient(base_url=st.session_state.api_url.rstrip("/"), token=st.session_state.token or None)
        st.markdown(f"#### {t(lang, 'login_title')}")
        email = st.text_input(t(lang, "email"), value="admin@example.com", key="login_email")
        pwd = st.text_input(t(lang, "password"), value="admin123", type="password", key="login_password")
        c1, c2 = st.columns(2)
        with c1:
            if st.button(t(lang, "login_btn"), use_container_width=True):
                try:
                    token = client.login(email, pwd)
                    st.session_state.token = token
                    st.success("OK")
                except Exception as exc:
                    st.error(str(exc))
        with c2:
            if st.button(t(lang, "logout_btn"), use_container_width=True):
                st.session_state.token = ""
                st.rerun()
    return ApiClient(base_url=st.session_state.api_url.rstrip("/"), token=st.session_state.token or None)


def _load_refs(client: ApiClient) -> tuple[list[dict], list[dict]]:
    frameworks: list[dict] = []
    departments: list[dict] = []
    try:
        if client.token:
            frameworks = client.frameworks()
            departments = client.departments()
    except Exception:
        pass
    return frameworks, departments


def _filter_controls_records(client: ApiClient) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, float | int]]:
    connected = False
    try:
        if not client.token:
            raise RuntimeError("demo")
        fw = int(st.session_state.framework_id) if st.session_state.framework_id else None
        dept = int(st.session_state.department_id) if st.session_state.department_id else None
        controls = pd.DataFrame(client.controls(framework_id=fw))
        records = pd.DataFrame(client.records(department_id=dept))
        raw = client.stats()
        stats = {
            "total_controls": raw["total_controls"],
            "compliance_rate": raw["compliance_rate"],
            "gap_open_count": raw["gap_open_count"],
            "records_total": raw["compliant"] + raw["partial"] + raw["not_started"] + raw["not_applicable"],
            "compliant": raw["compliant"],
            "partial": raw["partial"],
            "not_started": raw["not_started"],
            "not_applicable": raw["not_applicable"],
        }
        connected = True
    except Exception:
        controls = pd.DataFrame(
            [
                {"id": 1, "control_ref": "ECC-1-1", "title_ar": "الحوكمة", "domain_ar": "الحوكمة", "framework_id": 1},
                {"id": 2, "control_ref": "ECC-1-2", "title_ar": "إدارة الأصول", "domain_ar": "التعزيز", "framework_id": 1},
            ]
        )
        records = demo_records().rename(columns={"control_id": "control_id"})
        stats = demo_stats()
    if not records.empty and not controls.empty and "id" in controls.columns:
        merged = records.merge(controls, left_on="control_id", right_on="id", how="left")
    else:
        merged = records
    if st.session_state.table_search and not merged.empty:
        q = st.session_state.table_search.strip().lower()
        mask = merged.astype(str).apply(lambda s: s.str.lower().str.contains(q, na=False))
        merged = merged[mask.any(axis=1)]
    st.info(t(st.session_state.lang, "connected") if connected else t(st.session_state.lang, "not_connected"))
    return controls, merged, stats


def _overview(lang: Lang, client: ApiClient) -> None:
    _, merged, stats = _filter_controls_records(client)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric(t(lang, "metric_controls"), f"{stats['total_controls']}")
    m2.metric(t(lang, "metric_rate"), f"{stats['compliance_rate']}%")
    m3.metric(t(lang, "metric_gaps"), f"{stats['gap_open_count']}")
    m4.metric(t(lang, "metric_records"), f"{stats['records_total']}")

    chart_df = pd.DataFrame(
        [
            {"status": "compliant", "count": stats["compliant"]},
            {"status": "partial", "count": stats["partial"]},
            {"status": "not_started", "count": stats["not_started"]},
            {"status": "not_applicable", "count": stats["not_applicable"]},
        ]
    )
    fig = px.bar(chart_df, x="status", y="count", color="count", title="Compliance Distribution")
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    if not merged.empty and "domain_ar" in merged.columns and "status" in merged.columns:
        g = merged.groupby(["domain_ar", "status"], dropna=False).size().reset_index(name="count")
        fig2 = px.bar(g, x="domain_ar", y="count", color="status", title="الامتثال حسب المجال")
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})


def _compliance(lang: Lang, client: ApiClient) -> None:
    st.subheader(t(lang, "nav_compliance"))
    frameworks, departments = _load_refs(client)
    f1, f2, f3 = st.columns([1, 1, 2])
    with f1:
        fw_opts = {"": "الكل"}
        fw_opts.update({str(x["id"]): f'{x["name_ar"]} ({x["code"]})' for x in frameworks})
        st.selectbox("الإطار", options=list(fw_opts.keys()), format_func=lambda x: fw_opts[x], key="framework_id")
    with f2:
        dep_opts = {"": "الكل"}
        dep_opts.update({str(x["id"]): f'{x.get("code") or "-"} {x["name_ar"]}' for x in departments})
        st.selectbox("الإدارة", options=list(dep_opts.keys()), format_func=lambda x: dep_opts[x], key="department_id")
    with f3:
        st.text_input("بحث في الجدول", key="table_search", placeholder="رقم الضابط، الاسم، المجال، الوصف...")

    controls, merged, _ = _filter_controls_records(client)
    st.dataframe(merged, use_container_width=True, hide_index=True)

    if client.token and not merged.empty and "id_x" in merged.columns:
        st.markdown("### تحديث حالة سجل")
        r1, r2, r3 = st.columns(3)
        with r1:
            rec_id = st.selectbox("رقم السجل", options=[int(x) for x in merged["id_x"].dropna().tolist()])
        with r2:
            new_status = st.selectbox("الحالة الجديدة", options=["not_started", "partial", "compliant", "not_applicable"])
        with r3:
            if st.button("حفظ الحالة", type="primary", use_container_width=True):
                try:
                    client.patch_record(rec_id, new_status)
                    st.success("تم التحديث.")
                except Exception as exc:
                    st.error(str(exc))

    st.markdown("### تحليل فجوات")
    if st.button("تشغيل تحليل الفجوات", type="primary"):
        try:
            if client.token:
                st.write(client.gap_analysis().get("gaps_summary", ""))
            else:
                st.info("يلزم تسجيل الدخول للـ API.")
        except Exception as exc:
            st.error(str(exc))

    if client.token and frameworks:
        st.markdown("### شرح الإطار")
        selected = int(st.session_state.framework_id) if st.session_state.framework_id else frameworks[0]["id"]
        if st.button("شرح الإطار والمعيار"):
            try:
                ex = client.explain_framework(selected)
                st.write(ex.get("explanation", ""))
                if ex.get("official_ecc_pdf_url"):
                    st.markdown(f"[وثيقة ECC الرسمية]({ex['official_ecc_pdf_url']})")
            except Exception as exc:
                st.error(str(exc))

    st.markdown(f"### {t(lang, 'upload_title')}")
    up = st.file_uploader("CSV / XLSX / PDF", type=["csv", "xlsx", "xls", "pdf"])
    if up is not None:
        raw = up.read()
        if up.name.lower().endswith(".pdf"):
            focus = st.text_input("تركيز التحليل (اختياري)", placeholder="مثال: المخاطر عالية الأولوية")
            if st.button("تحليل الملف بالذكاء الاصطناعي"):
                try:
                    if not client.token:
                        st.error("يلزم تسجيل الدخول.")
                    else:
                        ans = client.analyze_file(up.name, raw, focus=focus or None)
                        st.write(ans.get("analysis", ""))
                except Exception as exc:
                    st.error(str(exc))
        else:
            if up.name.lower().endswith(".csv"):
                udf = pd.read_csv(io.BytesIO(raw))
            else:
                udf = pd.read_excel(io.BytesIO(raw), sheet_name=0)
            st.dataframe(udf.head(25), use_container_width=True, hide_index=True)

    st.markdown("### تقرير امتثال PDF")
    if st.button("تنزيل التقرير", use_container_width=True):
        try:
            if not client.token:
                st.error("يلزم تسجيل الدخول.")
            else:
                dep = int(st.session_state.department_id) if st.session_state.department_id else None
                fw = int(st.session_state.framework_id) if st.session_state.framework_id else None
                pdf_bytes = client.download_compliance_pdf(department_id=dep, framework_id=fw)
                date = datetime.now().strftime("%Y-%m-%d")
                st.download_button(
                    "تحميل الآن",
                    data=pdf_bytes,
                    file_name=f"compliance-report-{date}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
        except Exception as exc:
            st.error(str(exc))

    st.markdown("### إعدادات ترميز الإدارات")
    if client.token:
        c1, c2, c3 = st.columns(3)
        with c1:
            dep_code = st.text_input("Code", key="new_dep_code")
        with c2:
            dep_ar = st.text_input("الاسم العربي", key="new_dep_ar")
        with c3:
            dep_en = st.text_input("English name", key="new_dep_en")
        if st.button("إضافة إدارة", type="primary"):
            try:
                client.create_department(dep_ar.strip(), dep_en.strip(), dep_code.strip() or None)
                st.success("تمت الإضافة.")
            except Exception as exc:
                st.error(str(exc))


def _assistant(lang: Lang, client: ApiClient) -> None:
    st.subheader(t(lang, "nav_assistant"))
    for msg in st.session_state.chat:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input(t(lang, "assistant_hint")):
        st.session_state.chat.append({"role": "user", "content": prompt})
        answer = "نموذج تجريبي: اربط API وسجّل الدخول لتفعيل الرد الذكي."
        try:
            if client.token:
                result = client.chat(prompt)
                answer = result.get("reply", answer)
        except Exception:
            pass
        st.session_state.chat.append({"role": "assistant", "content": answer})
        st.rerun()


def _api_page(client: ApiClient) -> None:
    st.subheader("API Health")
    if st.button("Check /api/health", type="primary"):
        try:
            st.json(client.health())
        except Exception as exc:
            st.error(str(exc))

    if client.token and st.button("Run Gap Analysis"):
        try:
            st.json(client.gap_analysis())
        except Exception as exc:
            st.error(str(exc))


def main() -> None:
    _init_state()
    lang: Lang = st.session_state.lang
    inject_theme(lang, st.session_state.theme)
    client = _sidebar(lang)

    st.markdown(hero_html(lang), unsafe_allow_html=True)
    _top_nav(lang)
    st.caption(t(lang, "about"))

    page = st.session_state.nav
    if page == "overview":
        _overview(lang, client)
    elif page == "compliance":
        _compliance(lang, client)
    elif page == "assistant":
        _assistant(lang, client)
    else:
        _api_page(client)


if __name__ == "__main__":
    st.set_page_config(page_title="درع سيبراني", page_icon="🛡️", layout="wide", initial_sidebar_state="expanded")
    main()

