from __future__ import annotations

import io

import pandas as pd
import plotly.express as px
import streamlit as st

from cyber_observatory.demo_data import (
    calc_stats,
    seed_controls,
    seed_departments,
    seed_frameworks,
    seed_records,
)
from cyber_observatory.i18n import Lang, t
from cyber_observatory.theme import hero_html, inject_theme


def _init_state() -> None:
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


def _sidebar() -> None:
    with st.sidebar:
        st.selectbox("Language", ["ar", "en"], key="lang")
        st.selectbox("Theme", ["light", "dark"], key="theme")
        st.success("جاهز للعمل مباشرة على Streamlit Cloud")
        st.caption("لا يحتاج API خارجي أو تسجيل دخول.")


def _filter_controls_records() -> tuple[pd.DataFrame, pd.DataFrame, dict[str, float | int]]:
    controls = st.session_state.controls_df.copy()
    records = st.session_state.records_df.copy()
    departments = st.session_state.departments_df.copy()
    frameworks = st.session_state.frameworks_df.copy()

    # Avoid merge collisions on generic columns like id/name_ar.
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
    st.info("تشغيل تلقائي مدمج — جاهز للمراجعة عبر الإنترنت.")
    return controls, merged, stats


def _overview(lang: Lang) -> None:
    _, merged, stats = _filter_controls_records()

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


def _compliance(lang: Lang) -> None:
    st.subheader(t(lang, "nav_compliance"))
    frameworks = st.session_state.frameworks_df.to_dict("records")
    departments = st.session_state.departments_df.to_dict("records")
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

    controls, merged, _ = _filter_controls_records()
    show_cols = [
        "record_id",
        "control_ref",
        "title_ar",
        "domain_ar",
        "framework_name_ar",
        "department_name_ar",
        "status",
        "evidence_summary",
    ]
    available_cols = [c for c in show_cols if c in merged.columns]
    st.dataframe(merged[available_cols], use_container_width=True, hide_index=True)

    if not merged.empty and "record_id" in merged.columns:
        st.markdown("### تحديث حالة سجل")
        r1, r2, r3 = st.columns(3)
        with r1:
            rec_id = st.selectbox("رقم السجل", options=[int(x) for x in merged["record_id"].dropna().tolist()])
        with r2:
            new_status = st.selectbox("الحالة الجديدة", options=["not_started", "partial", "compliant", "not_applicable"])
        with r3:
            if st.button("حفظ الحالة", type="primary", use_container_width=True):
                try:
                    df = st.session_state.records_df.copy()
                    df.loc[df["id"] == rec_id, "status"] = new_status
                    st.session_state.records_df = df
                    st.success("تم التحديث.")
                except Exception as exc:
                    st.error(str(exc))

    st.markdown("### تحليل فجوات")
    if st.button("تشغيل تحليل الفجوات", type="primary"):
        open_gaps = merged[merged["status"].isin(["partial", "not_started"])] if "status" in merged.columns else pd.DataFrame()
        if open_gaps.empty:
            st.session_state.gap_summary = "لا توجد فجوات مفتوحة في النطاق الحالي."
        else:
            refs = ", ".join(open_gaps["control_ref"].dropna().astype(str).head(8).tolist())
            st.session_state.gap_summary = (
                f"تم رصد {len(open_gaps)} سجلات بحاجة معالجة. "
                f"أعلى الأولويات: {refs}. "
                "التوصية: ابدأ بالضوابط ذات حالة not_started، ثم أغلق partial بالأدلة."
            )
        st.success("اكتمل التحليل.")
        st.write(st.session_state.gap_summary)

    st.markdown(f"### {t(lang, 'upload_title')}")
    up = st.file_uploader("CSV / XLSX", type=["csv", "xlsx", "xls"])
    if up is not None:
        raw = up.read()
        if up.name.lower().endswith(".csv"):
            udf = pd.read_csv(io.BytesIO(raw))
        else:
            udf = pd.read_excel(io.BytesIO(raw), sheet_name=0)
        st.dataframe(udf.head(25), use_container_width=True, hide_index=True)
        st.caption("يمكن استخدام المعاينة الآن لأخذ ملاحظات الفريق قبل ربط الاستيراد الرسمي.")

    st.markdown("### تنزيل تقرير")
    csv_data = merged.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "تحميل تقرير الامتثال (CSV)",
        data=csv_data,
        file_name="compliance-report.csv",
        mime="text/csv",
        use_container_width=True,
    )

    st.markdown("### إعدادات ترميز الإدارات")
    c1, c2, c3 = st.columns(3)
    with c1:
        dep_code = st.text_input("Code", key="new_dep_code")
    with c2:
        dep_ar = st.text_input("الاسم العربي", key="new_dep_ar")
    with c3:
        dep_en = st.text_input("English name", key="new_dep_en")
    if st.button("إضافة إدارة", type="primary"):
        if not dep_ar.strip() or not dep_en.strip():
            st.error("أدخل اسم الإدارة بالعربي والإنجليزي.")
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
            st.success("تمت الإضافة.")


def _assistant(lang: Lang) -> None:
    st.subheader(t(lang, "nav_assistant"))
    for msg in st.session_state.chat:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input(t(lang, "assistant_hint")):
        st.session_state.chat.append({"role": "user", "content": prompt})
        _, merged, stats = _filter_controls_records()
        open_count = int((merged["status"].isin(["partial", "not_started"])).sum()) if "status" in merged.columns else 0
        answer = (
            "تحليل مبدئي: "
            f"نسبة الامتثال الحالية {stats['compliance_rate']}%، "
            f"والفجوات المفتوحة {open_count}. "
            "ابدأ بالضوابط not_started ثم partial مع توثيق الأدلة لكل سجل."
        )
        if st.session_state.gap_summary:
            answer += f"\n\nملخص الفجوات الحالي: {st.session_state.gap_summary}"
        st.session_state.chat.append({"role": "assistant", "content": answer})
        st.rerun()


def _api_page() -> None:
    st.subheader("جاهزية المنصة")
    st.success("المنصة تعمل الآن بتشغيل ذاتي كامل على Streamlit Cloud.")
    st.markdown(
        """
- لا تحتاج API خارجي لتشغيل العرض والمراجعة.
- الفلاتر والجداول والتحديثات تعمل مباشرة.
- يمكنك مشاركة الرابط مع الفريق لتجربة الواجهة وتقديم الملاحظات.
"""
    )


def main() -> None:
    _init_state()
    lang: Lang = st.session_state.lang
    inject_theme(lang, st.session_state.theme)
    _sidebar()

    st.markdown(hero_html(lang), unsafe_allow_html=True)
    _top_nav(lang)
    st.caption("منصة امتثال سيبراني متكاملة وجاهزة للمراجعة على الإنترنت.")

    page = st.session_state.nav
    if page == "overview":
        _overview(lang)
    elif page == "compliance":
        _compliance(lang)
    elif page == "assistant":
        _assistant(lang)
    else:
        _api_page()


if __name__ == "__main__":
    st.set_page_config(page_title="درع سيبراني", page_icon="🛡️", layout="wide", initial_sidebar_state="expanded")
    main()

