"""منصّة إدارة الثغرات — واجهة الأقسام.

كل قسم في المنصّة (Dashboard, Sites, Scans, Vulnerabilities, Reports,
Team, Subscription, Audit, Admin) معرَّف هنا كدالة render_*.
"""
from __future__ import annotations

import html as _html
from datetime import datetime
from typing import Any

import pandas as pd
import plotly.express as px
import streamlit as st

from cyber_observatory import vm_data
from cyber_observatory.i18n import Lang, t


# =========================================================================
#  Helpers
# =========================================================================
ENVIRONMENTS = ["production", "staging", "development", "test"]
SEVERITIES = ["critical", "high", "medium", "low"]

SCAN_TYPES = [
    ("quick",   "vm_scan_quick",   True),
    ("full",    "vm_scan_full",    True),
    ("ssl",     "vm_scan_ssl",     True),
    ("headers", "vm_scan_headers", True),
    ("api",     "vm_scan_api",     False),  # placeholder
]

ENGINES = [
    ("passive", "vm_engine_passive", True),
    ("zap",     "vm_engine_zap",     False),
    ("nuclei",  "vm_engine_nuclei",  False),
    ("nmap",    "vm_engine_nmap",    False),
]


def _esc(s: Any) -> str:
    return _html.escape(str(s or ""), quote=True)


def _human_dt(iso: str) -> str:
    try:
        dt = datetime.fromisoformat(iso)
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return iso or "—"


def _color_for_score(score: int) -> str:
    if score >= 80:
        return "var(--cb-success-strong)"
    if score >= 60:
        return "var(--cb-warn-strong)"
    return "var(--cb-danger-strong)"


def _grade_class(score: int) -> str:
    if score >= 80:
        return ""
    if score >= 60:
        return "warn"
    return "danger"


def _filter_scan_types_by_plan(plan: str) -> set[str]:
    return set(vm_data.plan_limits(plan)["scan_types"])


def _domain_label(d: dict) -> str:
    return f'{d["domain"]} ({d["environment"]})'


def _domain_label_scan(d: dict, lang: Lang) -> str:
    """Label in scan target picker; flags unverified when trial mode allows them."""
    base = _domain_label(d)
    if not vm_data.require_domain_verification() and not d.get("verified"):
        return f"{base} · {t(lang, 'vm_unverified')}"
    return base


# =========================================================================
#  Top banner with role + notifications
# =========================================================================
def render_banner(lang: Lang) -> None:
    user = vm_data.current_user()
    if not user:
        return
    company = vm_data.current_company()
    role = user["role"]
    role_cls = {
        vm_data.ROLE_SUPER:   "super",
        vm_data.ROLE_COMPANY: "company",
        vm_data.ROLE_MEMBER:  "member",
    }[role]
    role_label = (
        vm_data.ROLE_LABELS_AR if lang == "ar" else vm_data.ROLE_LABELS_EN
    )[role]

    company_name = company["name"] if company else "—"
    plan = vm_data.plan_for_company(company["id"]) if company else vm_data.PLAN_FREE
    plan_label = (vm_data.PLAN_LABELS_AR if lang == "ar" else vm_data.PLAN_LABELS_EN)[plan]

    unread = len(vm_data.user_notifications(user["id"], unread_only=True))

    st.markdown(
        f"""
<div class="vm-banner">
  <div class="vm-banner-left">
    <div class="vm-banner-icon">🛰️</div>
    <div>
      <div class="vm-banner-name">{_esc(user['name'])} <span style="font-weight:500;opacity:.7;">· {_esc(user['email'])}</span></div>
      <div class="vm-banner-meta">{_esc(company_name)} · {_esc(plan_label)}</div>
    </div>
  </div>
  <div class="vm-banner-right">
    <span class="vm-role-tag {role_cls}">{_esc(role_label)}</span>
    <span class="vm-role-tag" title="إشعارات غير مقروءة">🔔 {unread}</span>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_role_switcher(lang: Lang) -> None:
    """Switch the active platform user (visible only when >1 user exists)."""
    users = vm_data.all_users()
    show_switcher = len(users) > 1

    cols = st.columns([3, 4, 2, 1]) if show_switcher else st.columns([7, 2, 1])

    if show_switcher:
        options = {u["id"]: f'{u["name"]} · {u["email"]} · {u["role"]}' for u in users}
        with cols[1]:
            cur_id = st.session_state.vm_current_user_id
            idx = list(options.keys()).index(cur_id) if cur_id in options else 0
            new_id = st.selectbox(
                t(lang, "vm_switch_role"),
                options=list(options.keys()),
                format_func=lambda x: options[x],
                index=idx,
                key="vm_user_switch",
                label_visibility="collapsed",
            )
            if new_id != cur_id:
                vm_data.set_active_user(new_id)
                st.rerun()
        notif_col = cols[2]
        clear_col = cols[3]
    else:
        notif_col = cols[1]
        clear_col = cols[2]

    with notif_col:
        if st.button(t(lang, "vm_notifications") + " 🔔",
                     key="vm_notifs_btn", use_container_width=True):
            st.session_state.vm_show_notifs = not st.session_state.get("vm_show_notifs", False)
    with clear_col:
        if st.session_state.get("vm_show_notifs"):
            if st.button(t(lang, "vm_mark_all_read"),
                         key="vm_notifs_clear", use_container_width=True):
                u = vm_data.current_user()
                if u:
                    vm_data.mark_all_read(u["id"])
                st.rerun()

    if st.session_state.get("vm_show_notifs"):
        u = vm_data.current_user()
        if u:
            notifs = vm_data.user_notifications(u["id"])
            if not notifs:
                st.markdown(f'<div class="vm-empty">{t(lang, "vm_no_notifications")}</div>',
                            unsafe_allow_html=True)
            else:
                blocks = []
                for n in notifs[:10]:
                    cls = (n.get("level") or "info") + (" unread" if not n["read"] else "")
                    blocks.append(f"""
<div class="vm-notif-item {cls}">
  <div class="vm-notif-title">{_esc(n['title'])}</div>
  <div class="vm-notif-body">{_esc(n['body'])}</div>
  <div class="vm-notif-time">{_human_dt(n['created_at'])}</div>
</div>
""")
                st.markdown("".join(blocks), unsafe_allow_html=True)


# =========================================================================
#  Onboarding (no company yet)
# =========================================================================
def render_onboarding(lang: Lang) -> None:
    """First-time setup: create company + Company Admin."""
    user = vm_data.current_user()
    super_view_msg = ""
    if user and user["role"] == vm_data.ROLE_SUPER and vm_data.all_companies():
        super_view_msg = t(lang, "vm_onb_super_pending")

    plan_labels = (vm_data.PLAN_LABELS_AR if lang == "ar"
                   else vm_data.PLAN_LABELS_EN)

    st.markdown(f"""
<div class="vm-empty" style="text-align:start;">
  <div style="font-size:18px;font-weight:800;color:var(--cb-text);margin-bottom:6px;">
    {t(lang, "vm_onb_title")}
  </div>
  <div style="font-size:13.5px;color:var(--cb-text-2);line-height:1.8;">
    {t(lang, "vm_onb_caption")}
  </div>
</div>
""", unsafe_allow_html=True)

    if super_view_msg:
        st.info(super_view_msg)

    with st.form("vm_onboarding_form", clear_on_submit=False):
        st.markdown(f'<div class="vm-section-title">🏢 {t(lang, "vm_onb_company_title")}</div>',
                    unsafe_allow_html=True)
        cols = st.columns([2, 1])
        c_name = cols[0].text_input(
            t(lang, "vm_onb_company_name"),
            placeholder=t(lang, "vm_onb_company_name_ph"),
            key="vm_onb_company_name",
        )
        c_plan = cols[1].selectbox(
            t(lang, "vm_onb_plan"),
            options=[vm_data.PLAN_FREE, vm_data.PLAN_STARTER,
                     vm_data.PLAN_BUSINESS, vm_data.PLAN_ENTERPRISE],
            format_func=lambda p: f"{plan_labels[p]} · {vm_data.PLAN_PRICES[p]}",
            index=1,
            key="vm_onb_plan",
        )

        st.markdown('<div class="vm-divider"></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="vm-section-title">👤 {t(lang, "vm_onb_admin_title")}</div>',
                    unsafe_allow_html=True)
        cols2 = st.columns(2)
        a_name = cols2[0].text_input(
            t(lang, "vm_onb_admin_name"),
            placeholder=t(lang, "vm_onb_admin_name_ph"),
            key="vm_onb_admin_name",
        )
        a_email = cols2[1].text_input(
            t(lang, "vm_onb_admin_email"),
            placeholder=t(lang, "vm_onb_admin_email_ph"),
            key="vm_onb_admin_email",
        )

        submitted = st.form_submit_button(
            t(lang, "vm_onb_submit"),
            type="primary",
            use_container_width=True,
        )

    if submitted:
        if not (c_name.strip() and a_name.strip() and a_email.strip()):
            st.error(t(lang, "vm_onb_validate"))
            return
        if "@" not in a_email or "." not in a_email.split("@")[-1]:
            st.error(t(lang, "vm_onb_invalid_email"))
            return
        company, admin = vm_data.create_company_and_admin(
            c_name, c_plan, a_name, a_email,
            by_user=user["id"] if user else "system",
        )
        vm_data.set_active_user(admin["id"])
        st.success(f"✓ تم إنشاء «{company['name']}». انتقلنا تلقائياً إلى حساب Company Admin.")
        st.rerun()


# =========================================================================
#  Section: Dashboard
# =========================================================================
def render_dashboard(lang: Lang) -> None:
    user = vm_data.current_user()
    if not user:
        return
    role = user["role"]

    if role == vm_data.ROLE_SUPER:
        st.markdown(f'<div class="vm-section-title">{t(lang, "vm_section_dashboard")} '
                    f'<small>· super admin view</small></div>', unsafe_allow_html=True)
        s = vm_data.system_stats()
        kpis = [
            ("info",    t(lang, "vm_admin_companies"), str(s["companies"])),
            ("info",    t(lang, "vm_admin_users"),     str(s["users"])),
            ("",        t(lang, "vm_total_domains"),   str(s["domains"])),
            ("",        t(lang, "vm_total_scans"),     str(s["scans"])),
            ("crit",    t(lang, "vm_open_vulns"),      str(s["vulns_open"])),
        ]
        _render_kpis(kpis)
        _render_recent_scans_table(vm_data.all_scans(), lang)
        return

    company = vm_data.current_company()
    if not company:
        st.warning("لا توجد شركة مرتبطة بالحساب.")
        return
    s = vm_data.dashboard_stats(company["id"])

    st.markdown(f'<div class="vm-section-title">{t(lang, "vm_section_dashboard")} '
                f'<small>· {_esc(company["name"])}</small></div>',
                unsafe_allow_html=True)

    score = s["avg_score"]
    score_cls = _grade_class(score)
    grade = "A" if score >= 90 else "B" if score >= 75 else "C" if score >= 60 else "D" if score >= 40 else "F"

    cols = st.columns([1.2, 2.8])
    with cols[0]:
        st.markdown(f"""
<div class="vm-score-gauge">
  <div class="vm-score-num {score_cls}">{score}</div>
  <span class="vm-score-grade {score_cls}">{grade}</span>
  <div class="vm-score-cap">{t(lang, "vm_avg_score")}</div>
</div>
""", unsafe_allow_html=True)
    with cols[1]:
        kpis = [
            ("info",    t(lang, "vm_total_domains"), f"{s['domains_total']}",
             f"{s['domains_verified']} {t(lang, 'vm_verified_domains')}"),
            ("",        t(lang, "vm_total_scans"),   f"{s['scans_total']}",
             f"{s['scans_completed']} {t(lang, 'vm_scan_status_completed')}"),
            ("crit",    t(lang, "vm_critical"),      f"{s['critical']}", ""),
            ("high",    t(lang, "vm_high"),          f"{s['high']}", ""),
            ("med",     t(lang, "vm_medium"),        f"{s['medium']}", ""),
            ("success", t(lang, "vm_low"),           f"{s['low']}", ""),
        ]
        _render_kpis(kpis)

    if any(s[k] > 0 for k in ("critical", "high", "medium", "low")):
        df = pd.DataFrame([
            {"sev": "critical", "count": s["critical"]},
            {"sev": "high",     "count": s["high"]},
            {"sev": "medium",   "count": s["medium"]},
            {"sev": "low",      "count": s["low"]},
        ])
        fig = px.bar(
            df, x="sev", y="count", color="sev",
            color_discrete_map={
                "critical": "#8E1A1A", "high": "#E24B4A",
                "medium":   "#BA7517", "low":  "#888780",
            },
            title=t(lang, "vm_risk_dist"),
        )
        fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                          showlegend=False, margin=dict(t=44, l=10, r=10, b=10),
                          height=280)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    scans = sorted(vm_data.company_scans(company["id"]),
                   key=lambda x: x["completed_at"], reverse=True)[:5]
    _render_recent_scans_table(scans, lang)


def _render_kpis(items: list[tuple]) -> None:
    blocks = []
    for itm in items:
        cls, lbl, val, *rest = itm
        sub = rest[0] if rest else ""
        sub_html = f'<div class="vm-kpi-sub">{_esc(sub)}</div>' if sub else ""
        blocks.append(f"""
<div class="vm-kpi {cls}">
  <div class="vm-kpi-label">{_esc(lbl)}</div>
  <div class="vm-kpi-val">{_esc(val)}</div>
  {sub_html}
</div>""")
    st.markdown(f'<div class="vm-kpi-grid">{"".join(blocks)}</div>',
                unsafe_allow_html=True)


def _render_recent_scans_table(scans: list[dict], lang: Lang) -> None:
    st.markdown(f'<div class="vm-section-title">{t(lang, "vm_recent_scans")}</div>',
                unsafe_allow_html=True)
    if not scans:
        st.markdown(f'<div class="vm-empty">{t(lang, "vm_no_scans")}</div>',
                    unsafe_allow_html=True)
        return
    rows = []
    for s in scans[:10]:
        d = vm_data.get_domain(s["domain_id"])
        rows.append({
            "النطاق": d["domain"] if d else "—",
            "النوع":   s["scan_type"],
            "التاريخ":  _human_dt(s["completed_at"]),
            "الدرجة":   f'{s["score"]} · {s["grade"]}',
            "Critical": s["critical"], "High": s["high"],
            "Medium":   s["medium"],   "Low":  s["low"],
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


# =========================================================================
#  Section: Sites
# =========================================================================
def render_sites(lang: Lang) -> None:
    user = vm_data.current_user()
    if not user:
        return
    company = vm_data.current_company()
    if not company:
        st.warning("لا توجد شركة.")
        return

    st.markdown(f'<div class="vm-section-title">{t(lang, "vm_section_sites")}</div>',
                unsafe_allow_html=True)

    used_d, lim_d = vm_data.domains_quota_used(company["id"])
    used_s, lim_s = vm_data.scans_quota_used(company["id"])
    cols = st.columns(2)
    with cols[0]:
        _render_quota(t(lang, "vm_quota_domains"), used_d, lim_d)
    with cols[1]:
        _render_quota(t(lang, "vm_quota_scans"), used_s, lim_s)

    if not vm_data.require_domain_verification():
        st.info(t(lang, "vm_trial_scan_without_verify"))
    else:
        st.warning(t(lang, "vm_verify_required_banner"))

    can_add = user["role"] in (vm_data.ROLE_SUPER, vm_data.ROLE_COMPANY)
    if can_add and used_d < lim_d:
        with st.expander(t(lang, "vm_add_domain"), expanded=False):
            with st.form("vm_add_domain_form", clear_on_submit=True):
                fcols = st.columns([2, 2, 1])
                domain = fcols[0].text_input(t(lang, "vm_domain_name"),
                                             placeholder="example.sa")
                desc = fcols[1].text_input(t(lang, "vm_domain_desc"))
                env = fcols[2].selectbox(t(lang, "vm_domain_env"), options=ENVIRONMENTS)
                tags_str = st.text_input(t(lang, "vm_domain_tags"),
                                         placeholder="public, saas")
                if st.form_submit_button(t(lang, "vm_save"), type="primary"):
                    if not domain.strip():
                        st.error("أدخل اسم النطاق.")
                    else:
                        tags = [s.strip() for s in tags_str.split(",") if s.strip()]
                        d = vm_data.add_domain(company["id"], domain, desc, env, tags, user["id"])
                        st.success(f"تمت إضافة {d['domain']}.")
                        st.rerun()

    domains = vm_data.company_domains(company["id"])
    if not domains:
        st.markdown(f'<div class="vm-empty">{t(lang, "vm_no_domains")}</div>',
                    unsafe_allow_html=True)
        return

    for d in domains:
        _render_domain_card(d, lang, user)


def _render_quota(label: str, used: int, limit: int) -> None:
    pct = min(100, int(100 * used / max(limit, 1)))
    color = "var(--cb-success-strong)" if pct < 70 else \
            "var(--cb-warn-strong)" if pct < 90 else "var(--cb-danger-strong)"
    st.markdown(f"""
<div class="vm-quota">
  <div class="vm-quota-top">
    <span>{_esc(label)}</span>
    <span><b>{used}</b> / {limit}</span>
  </div>
  <div class="vm-quota-bar"><div class="vm-quota-fill" style="width:{pct}%;background:{color};"></div></div>
</div>""", unsafe_allow_html=True)


def _render_domain_card(d: dict, lang: Lang, user: dict) -> None:
    verified = d["verified"]
    req_v = vm_data.require_domain_verification()
    tag_cls = "success" if verified else "warn"
    tag_label = t(lang, "vm_verified" if verified else "vm_unverified")
    tag_chips = "".join(f'<span class="vm-tag neutral">{_esc(x)}</span>' for x in d.get("tags", []))
    env_tag = f'<span class="vm-tag">{_esc(d["environment"])}</span>'

    st.markdown(f"""
<div class="vm-domain-card">
  <div class="vm-domain-top">
    <div>
      <span class="vm-domain-name">{_esc(d["domain"])}</span>
      <span class="vm-tag {tag_cls}" style="margin-inline-start:8px;">{tag_label}</span>
    </div>
    <div>{env_tag} {tag_chips}</div>
  </div>
  <div class="vm-domain-meta">{_esc(d.get("description") or "—")}</div>
</div>
""", unsafe_allow_html=True)

    can_manage = user["role"] in (vm_data.ROLE_SUPER, vm_data.ROLE_COMPANY)
    cols = st.columns([1, 1, 1, 2])
    # بدون إلزام التحقق: فحص مباشر من البطاقة. مع الإلزام: تحقق أولاً ثم يظهر الفحص.
    if req_v and not verified:
        if cols[0].button(t(lang, "vm_verify"), key=f"vrf_{d['id']}",
                          use_container_width=True):
            st.session_state[f"vm_show_verify_{d['id']}"] = True
    else:
        if cols[0].button(t(lang, "vm_run_scan"), key=f"scan_{d['id']}",
                          type="primary", use_container_width=True):
            st.session_state.vm_scan_target_id = d["id"]
            st.session_state.vm_pending_platform_tab = "scans"
            st.rerun()

    if can_manage and cols[1].button(t(lang, "vm_delete"), key=f"del_{d['id']}",
                                     use_container_width=True):
        vm_data.remove_domain(d["id"], user["id"])
        st.warning(f"تم حذف {d['domain']}")
        st.rerun()

    if req_v and st.session_state.get(f"vm_show_verify_{d['id']}"):
        _render_verification_panel(d, lang, user)


def _render_verification_panel(d: dict, lang: Lang, user: dict) -> None:
    st.markdown(f"""
<div class="vm-vuln-card">
  <div style="font-weight:700;font-size:14px;color:var(--cb-text);">{t(lang, "vm_verify_title")}</div>
  <div style="color:var(--cb-text-2);font-size:13px;margin-top:4px;">{t(lang, "vm_verify_caption")}</div>
</div>""", unsafe_allow_html=True)
    tab_dns, tab_file, tab_email = st.tabs([
        t(lang, "vm_verify_dns"),
        t(lang, "vm_verify_file"),
        t(lang, "vm_verify_email"),
    ])
    token = d["verification_token"]
    with tab_dns:
        st.write(t(lang, "vm_verify_dns_inst"))
        st.code(f"_cybershield-verification.{d['domain']}.   IN TXT   \"{token}\"",
                language="text")
        if st.button(t(lang, "vm_verify_now"), key=f"vrf_dns_{d['id']}",
                     type="primary"):
            vm_data.verify_domain(d["id"], "dns", user["id"])
            st.session_state[f"vm_show_verify_{d['id']}"] = False
            st.success(t(lang, "vm_verify_done"))
            st.rerun()
    with tab_file:
        st.write(t(lang, "vm_verify_file_inst"))
        st.code(f"https://{d['domain']}/.well-known/cybershield-{token}.txt", language="text")
        st.caption("محتوى الملف: " + token)
        if st.button(t(lang, "vm_verify_now"), key=f"vrf_file_{d['id']}",
                     type="primary"):
            vm_data.verify_domain(d["id"], "file", user["id"])
            st.session_state[f"vm_show_verify_{d['id']}"] = False
            st.success(t(lang, "vm_verify_done"))
            st.rerun()
    with tab_email:
        st.write(t(lang, "vm_verify_email_inst"))
        st.code(f"admin@{d['domain']}, webmaster@{d['domain']}, hostmaster@{d['domain']}",
                language="text")
        if st.button(t(lang, "vm_verify_now"), key=f"vrf_em_{d['id']}",
                     type="primary"):
            vm_data.verify_domain(d["id"], "email", user["id"])
            st.session_state[f"vm_show_verify_{d['id']}"] = False
            st.success(t(lang, "vm_verify_done"))
            st.rerun()


# =========================================================================
#  Section: Scans (run + history)
# =========================================================================
def render_scans(lang: Lang, run_scan_fn) -> None:
    user = vm_data.current_user()
    company = vm_data.current_company()
    if not user or not company:
        return
    plan = vm_data.plan_for_company(company["id"])
    allowed_types = _filter_scan_types_by_plan(plan)

    st.markdown(f'<div class="vm-section-title">{t(lang, "vm_section_scans")}</div>',
                unsafe_allow_html=True)

    ok_flash = st.session_state.pop("vm_scan_flash_ok", None)
    err_flash = st.session_state.pop("vm_scan_flash_err", None)
    if ok_flash:
        st.success(ok_flash)
    if err_flash:
        st.error(err_flash)

    if vm_data.require_domain_verification():
        domains = [d for d in vm_data.company_domains(company["id"]) if d["verified"]]
        empty_msg = t(lang, "vm_no_verified_targets")
    else:
        domains = list(vm_data.company_domains(company["id"]))
        empty_msg = t(lang, "vm_no_domains")

    if not domains:
        st.markdown(f'<div class="vm-empty">{empty_msg}</div>',
                    unsafe_allow_html=True)
    else:
        cols = st.columns([2, 1, 1, 1])
        target_id = cols[0].selectbox(
            t(lang, "vm_select_target"),
            options=[d["id"] for d in domains],
            format_func=lambda i: _domain_label_scan(
                next(d for d in domains if d["id"] == i), lang,
            ),
            key="vm_scan_target_id",
        )
        scan_type = cols[1].selectbox(
            t(lang, "vm_scan_type"),
            options=[k for (k, _, _) in SCAN_TYPES],
            format_func=lambda k: t(lang, dict((kk, v) for (kk, v, _) in SCAN_TYPES)[k]),
            key="vm_scan_type",
        )
        engine = cols[2].selectbox(
            t(lang, "vm_scan_engine"),
            options=[k for (k, _, _) in ENGINES],
            format_func=lambda k: t(lang, dict((kk, v) for (kk, v, _) in ENGINES)[k]),
            key="vm_scan_engine",
        )
        engine_avail = dict((k, av) for (k, _, av) in ENGINES)[engine]
        type_avail = scan_type in allowed_types and dict((k, av) for (k, _, av) in SCAN_TYPES)[scan_type]
        if not engine_avail:
            st.caption("⚠️ " + t(lang, "vm_engine_unavailable"))
        if scan_type not in allowed_types:
            st.caption(f"⚠️ هذا النوع غير متاح في باقة «{vm_data.PLAN_LABELS_AR[plan]}».")

        run_disabled = (not engine_avail) or (not type_avail)
        if cols[3].button(
            t(lang, "vm_run_scan"),
            type="primary",
            use_container_width=True,
            disabled=run_disabled,
            key="vm_run_scan_main",
        ):
            d = vm_data.get_domain(target_id)
            with st.spinner(t(lang, "scanner_running")):
                started = datetime.now().isoformat(timespec="seconds")
                try:
                    result = run_scan_fn(d["domain"])
                    vm_data.record_scan(d["id"], scan_type, result, started, user["id"])
                    st.session_state.vm_scan_flash_ok = t(lang, "vm_scan_done").format(
                        score=result["score"]["score"], grade=result["score"]["grade"]
                    )
                    st.session_state.vm_last_scan_url = result["url"]
                except Exception as exc:
                    st.session_state.vm_scan_flash_err = t(lang, "vm_scan_failed").format(
                        error=str(exc)
                    )
            st.rerun()

    st.markdown('<div class="vm-divider"></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="vm-section-title">{t(lang, "vm_scan_history")}</div>',
                unsafe_allow_html=True)
    scans = sorted(vm_data.company_scans(company["id"]),
                   key=lambda x: x["completed_at"], reverse=True)
    if not scans:
        st.markdown(f'<div class="vm-empty">{t(lang, "vm_no_scans")}</div>',
                    unsafe_allow_html=True)
        return
    rows = []
    for s in scans:
        d = vm_data.get_domain(s["domain_id"])
        rows.append({
            "id":     s["id"],
            "domain": d["domain"] if d else "—",
            "type":   s["scan_type"],
            "date":   _human_dt(s["completed_at"]),
            "score":  s["score"], "grade": s["grade"],
            "C": s["critical"], "H": s["high"], "M": s["medium"], "L": s["low"],
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


# =========================================================================
#  Section: Vulnerabilities
# =========================================================================
def render_vulns(lang: Lang, ai_explain_fn) -> None:
    user = vm_data.current_user()
    company = vm_data.current_company()
    if not user or not company:
        return

    st.markdown(f'<div class="vm-section-title">{t(lang, "vm_section_vulns")}</div>',
                unsafe_allow_html=True)
    vulns = vm_data.company_vulns(company["id"])
    if not vulns:
        st.markdown(f'<div class="vm-empty">{t(lang, "vm_no_vulns")}</div>',
                    unsafe_allow_html=True)
        return

    cols = st.columns([1, 1, 1, 1])
    sev_opts = ["all"] + SEVERITIES
    sev_pick = cols[0].selectbox(
        t(lang, "vm_vuln_filter_sev"),
        options=sev_opts,
        format_func=lambda s: "الكل" if s == "all" else t(lang, f"vm_{s}"),
        key="vm_vuln_filter_sev",
    )
    status_opts = ["all", "open", "fixed", "accepted_risk", "false_positive"]
    status_pick = cols[1].selectbox(
        t(lang, "vm_vuln_filter_status"),
        options=status_opts,
        format_func=lambda s: "الكل" if s == "all" else t(lang, f"vm_vuln_status_{s}"),
        key="vm_vuln_filter_status",
    )
    domains = vm_data.company_domains(company["id"])
    dom_opts = ["all"] + [d["id"] for d in domains]
    dom_pick = cols[2].selectbox(
        t(lang, "vm_vuln_filter_domain"),
        options=dom_opts,
        format_func=lambda i: "الكل" if i == "all" else next(d["domain"] for d in domains if d["id"] == i),
        key="vm_vuln_filter_dom",
    )

    sev_rank = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    filtered = vulns
    if sev_pick != "all":
        filtered = [v for v in filtered if v["severity"] == sev_pick]
    if status_pick != "all":
        filtered = [v for v in filtered if v["status"] == status_pick]
    if dom_pick != "all":
        filtered = [v for v in filtered if v["domain_id"] == dom_pick]
    filtered = sorted(filtered, key=lambda v: (sev_rank.get(v["severity"], 9), -v["cvss"]))

    if not filtered:
        st.markdown('<div class="vm-empty">لا نتائج بالفلاتر الحالية.</div>',
                    unsafe_allow_html=True)
        return

    for v in filtered:
        _render_vuln_card(v, lang, user, ai_explain_fn)


def _render_exploit_block(v: dict, lang: Lang) -> None:
    """يعرض «لماذا ثغرة؟» و«كيف تُستغل؟» مع أمثلة كود."""
    st.warning(t(lang, "vm_disclaimer_exploit"))

    impact = v.get("impact") or ""
    if impact:
        st.markdown(f'**{t(lang, "vm_why_vuln")}**')
        st.markdown(
            f'<div class="vm-vuln-fix" style="background:rgba(220,38,38,.06);'
            f'border-color:rgba(220,38,38,.25);">{_esc(impact)}</div>',
            unsafe_allow_html=True,
        )

    summary = v.get("attack_summary") or ""
    steps = v.get("attack_steps") or []
    codes = v.get("attack_code") or []

    if summary or steps or codes:
        st.markdown(f'**{t(lang, "vm_how_exploit")}**')

    if summary:
        st.markdown(
            f'<div style="font-size:13.5px;color:var(--cb-text);line-height:1.85;'
            f'margin:6px 0 10px 0;">'
            f'<b>{t(lang, "vm_attack_summary")}:</b> {_esc(summary)}</div>',
            unsafe_allow_html=True,
        )

    if steps:
        st.markdown(f'<div style="font-size:13px;color:var(--cb-text-2);font-weight:600;'
                    f'margin-top:6px;">{t(lang, "vm_attack_steps")}:</div>',
                    unsafe_allow_html=True)
        steps_html = "".join(
            f'<li style="margin:4px 0;font-size:13px;color:var(--cb-text);">{_esc(s)}</li>'
            for s in steps
        )
        st.markdown(
            f'<ol style="padding-inline-start:22px;line-height:1.85;">{steps_html}</ol>',
            unsafe_allow_html=True,
        )

    if codes:
        st.markdown(f'<div style="font-size:13px;color:var(--cb-text-2);font-weight:600;'
                    f'margin-top:6px;">{t(lang, "vm_attack_code")}:</div>',
                    unsafe_allow_html=True)
        for snippet in codes:
            label = snippet.get("label", "code")
            lang_tag = snippet.get("lang", "bash")
            code_text = snippet.get("code", "")
            if not code_text:
                continue
            st.markdown(f'<div class="vm-meta-chip" style="margin:8px 0 4px 0;">'
                        f'{_esc(label)}</div>', unsafe_allow_html=True)
            st.code(code_text, language=lang_tag)

    refs = v.get("references") or []
    if refs:
        items = "".join(
            f'<li><a href="{_esc(r)}" target="_blank" rel="noopener">{_esc(r)}</a></li>'
            for r in refs
        )
        st.markdown(
            f'<div style="margin-top:10px;font-size:12.5px;color:var(--cb-text-2);">'
            f'<b>{t(lang, "vm_refs_label")}:</b>'
            f'<ul style="padding-inline-start:18px;">{items}</ul></div>',
            unsafe_allow_html=True,
        )


def _render_vuln_card(v: dict, lang: Lang, user: dict, ai_explain_fn) -> None:
    d = vm_data.get_domain(v["domain_id"])
    sev = v["severity"]
    title_safe = _esc(v["title"])
    desc_safe = _esc(v["description"])
    fix_safe = _esc(v["fix"])
    ev_safe = _esc(v.get("evidence", ""))

    chips = []
    if v.get("cwe"):
        chips.append(f'<span class="vm-meta-chip">{_esc(v["cwe"])}</span>')
    if v.get("owasp"):
        chips.append(f'<span class="vm-meta-chip">{_esc(v["owasp"])}</span>')
    if v.get("ecc_ref"):
        chips.append(f'<span class="vm-meta-chip">ECC · {_esc(v["ecc_ref"])}</span>')
    chips.append(f'<span class="vm-meta-chip">CVSS {v["cvss"]}</span>')
    chips.append(f'<span class="vm-meta-chip">{_esc(d["domain"]) if d else "—"}</span>')
    chips.append(f'<span class="vm-meta-chip">{_esc(v["status"])}</span>')

    evidence_html = (
        f'<div class="vm-vuln-evidence">{ev_safe}</div>' if ev_safe else ""
    )

    st.markdown(f"""
<div class="vm-vuln-card">
  <div class="vm-vuln-header">
    <div class="vm-vuln-title">{title_safe}</div>
    <span class="vm-sev {sev}">{t(lang, f"vm_{sev}")}</span>
  </div>
  <div class="vm-vuln-meta-row">{"".join(chips)}</div>
  <div class="vm-vuln-desc">{desc_safe}</div>
  <div class="vm-vuln-fix"><b>🛠️ {t(lang, "scanner_fix_label")}</b><br/>{fix_safe}</div>
  {evidence_html}
</div>""", unsafe_allow_html=True)

    cols = st.columns(5)
    if v["status"] == "open":
        if cols[0].button(t(lang, "vm_vuln_mark_fixed"), key=f"fix_{v['id']}",
                          use_container_width=True):
            vm_data.update_vuln_status(v["id"], "fixed", user["id"])
            st.rerun()
        if cols[1].button(t(lang, "vm_vuln_mark_accepted"), key=f"acc_{v['id']}",
                          use_container_width=True):
            vm_data.update_vuln_status(v["id"], "accepted_risk", user["id"])
            st.rerun()
        if cols[2].button(t(lang, "vm_vuln_mark_fp"), key=f"fp_{v['id']}",
                          use_container_width=True):
            vm_data.update_vuln_status(v["id"], "false_positive", user["id"])
            st.rerun()
    else:
        if cols[0].button(t(lang, "vm_vuln_mark_open"), key=f"reop_{v['id']}",
                          use_container_width=True):
            vm_data.update_vuln_status(v["id"], "open", user["id"])
            st.rerun()

    if cols[3].button(t(lang, "vm_vuln_explain"), key=f"ai_{v['id']}",
                      use_container_width=True):
        st.session_state[f"vm_ai_show_{v['id']}"] = True

    # ----- Exploitation details (educational) -----
    has_exploit = bool(v.get("impact") or v.get("attack_steps") or v.get("attack_code"))
    if has_exploit:
        with st.expander(t(lang, "vm_show_exploit"), expanded=False):
            _render_exploit_block(v, lang)

    if st.session_state.get(f"vm_ai_show_{v['id']}"):
        company = vm_data.current_company()
        plan = vm_data.plan_for_company(company["id"]) if company else vm_data.PLAN_FREE
        if not vm_data.plan_limits(plan)["ai_analysis"]:
            st.warning(t(lang, "vm_ai_disabled"))
        else:
            with st.spinner(t(lang, "vm_ai_thinking")):
                answer = ai_explain_fn(v, lang)
            st.markdown(f"""
<div class="vm-ai-card">
  <span class="ai-label">AI Analyst</span>
  <div class="ai-body">{_esc(answer)}</div>
</div>""", unsafe_allow_html=True)


# =========================================================================
#  Section: Reports
# =========================================================================
def render_reports(lang: Lang, ai_summary_fn) -> None:
    user = vm_data.current_user()
    company = vm_data.current_company()
    if not user or not company:
        return
    st.markdown(f'<div class="vm-section-title">{t(lang, "vm_section_reports")}</div>',
                unsafe_allow_html=True)

    plan = vm_data.plan_for_company(company["id"])
    formats = vm_data.plan_limits(plan)["report_formats"]
    cols = st.columns([2, 2, 2])
    rtype = cols[0].selectbox(
        t(lang, "vm_report_type"),
        options=["executive", "technical", "compliance"],
        format_func=lambda s: {
            "executive":  t(lang, "vm_report_exec"),
            "technical":  t(lang, "vm_report_tech"),
            "compliance": t(lang, "vm_report_compliance"),
        }[s],
        key="vm_report_type",
    )
    fmt = cols[1].selectbox(
        t(lang, "vm_report_format"),
        options=formats,
        format_func=lambda s: t(lang, f"vm_report_format_{s}") if s != "pdf" else "PDF (HTML قابل للطباعة)",
        key="vm_report_format",
    )
    if cols[2].button(t(lang, "vm_report_generate"), type="primary",
                      use_container_width=True):
        scans = vm_data.company_scans(company["id"])
        vulns = vm_data.company_vulns(company["id"])
        ai_text = ""
        if rtype == "executive" and vm_data.plan_limits(plan)["ai_analysis"]:
            with st.spinner(t(lang, "vm_ai_thinking")):
                ai_text = ai_summary_fn(company, scans, vulns, lang)
        if fmt == "csv":
            data = _build_csv_report(scans, vulns)
            st.download_button(
                t(lang, "vm_report_download"),
                data=data,
                file_name=f"report-{company['id']}-{rtype}.csv",
                mime="text/csv",
                use_container_width=True,
            )
        else:
            html_doc = _build_html_report(company, scans, vulns, rtype, ai_text, lang)
            st.download_button(
                t(lang, "vm_report_download"),
                data=html_doc.encode("utf-8"),
                file_name=f"report-{company['id']}-{rtype}.html",
                mime="text/html",
                use_container_width=True,
            )
            st.caption(t(lang, "vm_report_print_hint"))
            with st.expander("معاينة"):
                st.components.v1.html(html_doc, height=500, scrolling=True)


def _build_csv_report(scans: list[dict], vulns: list[dict]) -> bytes:
    rows = []
    for v in vulns:
        d = vm_data.get_domain(v["domain_id"])
        rows.append({
            "domain":     d["domain"] if d else "",
            "title":      v["title"],
            "severity":   v["severity"],
            "cvss":       v["cvss"],
            "cwe":        v["cwe"],
            "owasp":      v["owasp"],
            "ecc_ref":    v.get("ecc_ref", ""),
            "status":     v["status"],
            "found_at":   v["found_at"],
            "fix":        v["fix"],
            "evidence":   v.get("evidence", ""),
        })
    return pd.DataFrame(rows).to_csv(index=False).encode("utf-8-sig")


def _build_html_report(company: dict, scans: list[dict], vulns: list[dict],
                        rtype: str, ai_text: str, lang: Lang) -> str:
    open_v = [v for v in vulns if v["status"] == "open"]
    sev_count = {s: sum(1 for v in open_v if v["severity"] == s) for s in SEVERITIES}
    score = (round(sum(s["score"] for s in scans) / len(scans))
             if scans else 0)

    sev_rows = "".join(
        f'<tr><td>{s}</td><td>{sev_count.get(s, 0)}</td></tr>' for s in SEVERITIES
    )
    vulns_sorted = sorted(open_v,
                          key=lambda v: ({"critical": 0, "high": 1, "medium": 2, "low": 3}.get(v["severity"], 9), -v["cvss"]))
    detail_rows = "".join(f"""
<tr>
  <td>{_esc(v['title'])}</td>
  <td><span class="sev sev-{v['severity']}">{v['severity']}</span></td>
  <td>{v['cvss']}</td>
  <td style="font-family:monospace;">{_esc(v['cwe'])}</td>
  <td>{_esc(v['owasp'])}</td>
  <td>{_esc(vm_data.get_domain(v['domain_id'])['domain'] if vm_data.get_domain(v['domain_id']) else '')}</td>
</tr>""" for v in vulns_sorted)

    fix_rows = "".join(f"""
<div class="finding">
  <h3>{_esc(v['title'])} <span class="sev sev-{v['severity']}">{v['severity']}</span></h3>
  <p>{_esc(v['description'])}</p>
  <div class="fix"><b>الإصلاح:</b><br/><pre>{_esc(v['fix'])}</pre></div>
  <div class="meta">CWE: {_esc(v['cwe'])} · OWASP: {_esc(v['owasp'])} · CVSS: {v['cvss']}</div>
</div>""" for v in vulns_sorted) if rtype == "technical" else ""

    ai_block = f'<div class="ai"><h2>🤖 ملخص الذكاء الاصطناعي</h2><pre>{_esc(ai_text)}</pre></div>' if ai_text else ""

    title = {"executive": "تقرير تنفيذي", "technical": "تقرير تقني",
             "compliance": "تقرير امتثال (ECC)"}[rtype]

    return f"""<!DOCTYPE html>
<html lang="ar" dir="rtl"><head>
<meta charset="utf-8"><title>{_esc(title)} — {_esc(company['name'])}</title>
<style>
body {{ font-family: 'Tajawal', system-ui, sans-serif; background: #F7F6F2; color: #2C2C2A; margin: 0; padding: 24px; }}
.container {{ max-width: 900px; margin: 0 auto; background: #fff; border-radius: 14px; padding: 28px; border: 1px solid rgba(0,0,0,0.10); }}
h1 {{ color: #0C447C; margin-top: 0; }}
h2 {{ color: #2C2C2A; margin-top: 28px; padding-bottom: 6px; border-bottom: 2px solid #E6F1FB; }}
.score {{ font-size: 64px; font-weight: 800; color: {_color_for_score(score)}; line-height: 1; }}
.kpi-row {{ display: flex; gap: 14px; flex-wrap: wrap; margin: 14px 0; }}
.kpi {{ flex: 1; background: #F1EFE8; padding: 12px 16px; border-radius: 10px; min-width: 130px; }}
.kpi b {{ font-size: 22px; display: block; }}
table {{ width: 100%; border-collapse: collapse; margin: 14px 0; }}
th, td {{ padding: 9px 12px; text-align: right; border-bottom: 1px solid rgba(0,0,0,0.10); font-size: 13px; }}
th {{ background: #F1EFE8; font-weight: 700; }}
.sev {{ display: inline-block; padding: 2px 9px; border-radius: 8px; font-size: 11px; font-weight: 700; }}
.sev-critical {{ background: #F4DCDC; color: #5B1313; }}
.sev-high {{ background: #FCEBEB; color: #791F1F; }}
.sev-medium {{ background: #FAEEDA; color: #854F0B; }}
.sev-low {{ background: #F1EFE8; color: #444441; }}
.finding {{ background: #F7F6F2; padding: 14px 16px; border-radius: 10px; margin: 10px 0; border-inline-start: 3px solid #639922; }}
.finding pre {{ background: #2C2C2A; color: #F7F6F2; padding: 10px; border-radius: 8px; direction: ltr; white-space: pre-wrap; font-size: 12px; }}
.fix {{ font-size: 13px; line-height: 1.7; }}
.meta {{ color: #5F5E5A; font-size: 11.5px; margin-top: 6px; direction: ltr; }}
.ai {{ background: linear-gradient(135deg, #F7F6F2, #E6F1FB); padding: 14px 16px; border-radius: 10px; margin: 14px 0; border: 1px solid #378ADD; }}
.ai pre {{ white-space: pre-wrap; font-family: inherit; font-size: 13.5px; line-height: 1.8; }}
.footer {{ text-align: center; color: #888780; font-size: 11px; margin-top: 24px; }}
@media print {{ body {{ background: #fff; padding: 0; }} .container {{ border: 0; }} }}
</style>
</head><body>
<div class="container">
<h1>🛰️ {_esc(title)}</h1>
<div style="color:#5F5E5A;font-size:13px;">{_esc(company['name'])} · {_human_dt(_now_iso())}</div>
<h2>📊 المؤشرات الرئيسية</h2>
<div class="kpi-row">
  <div class="kpi"><span>متوسط درجة الأمان</span><b>{score}</b></div>
  <div class="kpi"><span>إجمالي الفحوصات</span><b>{len(scans)}</b></div>
  <div class="kpi"><span>ثغرات مفتوحة</span><b>{len(open_v)}</b></div>
  <div class="kpi"><span>حرجة</span><b style="color:#8E1A1A;">{sev_count['critical']}</b></div>
</div>
{ai_block}
<h2>📈 توزيع الخطورة</h2>
<table><thead><tr><th>الخطورة</th><th>العدد</th></tr></thead>
<tbody>{sev_rows}</tbody></table>
<h2>🐞 قائمة الثغرات</h2>
<table><thead><tr><th>العنوان</th><th>الخطورة</th><th>CVSS</th><th>CWE</th><th>OWASP</th><th>الموقع</th></tr></thead>
<tbody>{detail_rows or '<tr><td colspan="6">لا ثغرات.</td></tr>'}</tbody></table>
{('<h2>🛠️ تفاصيل الإصلاح</h2>' + fix_rows) if rtype == 'technical' else ''}
<div class="footer">© Cyber Shield Vulnerability Platform — تقرير تلقائي</div>
</div>
</body></html>"""


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


# =========================================================================
#  Section: Team
# =========================================================================
def render_team(lang: Lang) -> None:
    user = vm_data.current_user()
    company = vm_data.current_company()
    if not user or not company:
        return
    st.markdown(f'<div class="vm-section-title">{t(lang, "vm_section_team")}</div>',
                unsafe_allow_html=True)

    can_manage = user["role"] in (vm_data.ROLE_SUPER, vm_data.ROLE_COMPANY)
    if can_manage:
        with st.expander(t(lang, "vm_invite_member")):
            with st.form("vm_invite_form", clear_on_submit=True):
                cols = st.columns([3, 2, 2, 1])
                name = cols[0].text_input("الاسم", placeholder="Aisha Salem")
                email = cols[1].text_input(t(lang, "vm_invite_email"))
                role = cols[2].selectbox(
                    t(lang, "vm_invite_role"),
                    options=[vm_data.ROLE_COMPANY, vm_data.ROLE_MEMBER],
                    format_func=lambda r: t(lang, f"vm_role_{ 'company' if r == vm_data.ROLE_COMPANY else 'member' }"),
                )
                if cols[3].form_submit_button(t(lang, "vm_send_invite"), type="primary"):
                    if not (name.strip() and email.strip()):
                        st.error("أدخل الاسم والبريد.")
                    else:
                        u = vm_data.add_user_to_company(name, email, role, company["id"])
                        vm_data.invite_member(company["id"], email, role, user["id"])
                        vm_data.notify(u["id"], "🎉 مرحباً بك",
                                       "تمت إضافتك إلى فريق " + company["name"])
                        st.success(f"تمت الدعوة: {email}")
                        st.rerun()

    members = vm_data.company_users(company["id"])
    if not members:
        st.markdown(f'<div class="vm-empty">{t(lang, "vm_no_members")}</div>',
                    unsafe_allow_html=True)
        return

    rows = []
    for m in members:
        rows.append({
            "id":    m["id"],
            "name":  m["name"],
            "email": m["email"],
            "role":  m["role"],
            "verified": "✓" if m["verified"] else "—",
            "MFA":   "🔐" if m["mfa_enabled"] else "—",
            "since": _human_dt(m["created_at"]),
        })
    st.dataframe(pd.DataFrame(rows).drop(columns=["id"]),
                 use_container_width=True, hide_index=True)

    if can_manage:
        st.markdown('<div class="vm-divider"></div>', unsafe_allow_html=True)
        target = st.selectbox(
            t(lang, "vm_member_remove"),
            options=[m["id"] for m in members if m["id"] != user["id"]],
            format_func=lambda i: next(m["name"] + " · " + m["email"] for m in members if m["id"] == i),
            key="vm_remove_target",
        )
        if st.button(t(lang, "vm_member_remove"), key="vm_remove_btn", type="secondary"):
            vm_data.remove_member(target, user["id"])
            st.success("تم الحذف.")
            st.rerun()


# =========================================================================
#  Section: Subscription
# =========================================================================
def render_subscription(lang: Lang) -> None:
    company = vm_data.current_company()
    if not company:
        return
    st.markdown(f'<div class="vm-section-title">{t(lang, "vm_section_subs")}</div>',
                unsafe_allow_html=True)
    cur_plan = vm_data.plan_for_company(company["id"])
    plan_labels = vm_data.PLAN_LABELS_AR if lang == "ar" else vm_data.PLAN_LABELS_EN

    cards = []
    for plan_key in [vm_data.PLAN_FREE, vm_data.PLAN_STARTER,
                     vm_data.PLAN_BUSINESS, vm_data.PLAN_ENTERPRISE]:
        limits = vm_data.PLAN_LIMITS[plan_key]
        is_cur = plan_key == cur_plan
        cur_tag = f'<div class="vm-plan-current-tag">الحالية</div>' if is_cur else ""
        ai_yes = "✓" if limits["ai_analysis"] else "✕"
        feats = [
            f'{t(lang, "vm_plan_max_domains")}: <b>{limits["max_domains"]}</b>',
            f'{t(lang, "vm_plan_max_scans")}: <b>{limits["max_scans_month"]}</b>',
            f'{t(lang, "vm_plan_ai")}: <b>{ai_yes}</b>',
            f'{t(lang, "vm_plan_scan_types")}: <b>{", ".join(limits["scan_types"])}</b>',
            f'{t(lang, "vm_plan_reports")}: <b>{", ".join(limits["report_formats"])}</b>',
        ]
        feat_html = "".join(f'<div class="vm-plan-feat">{f}</div>' for f in feats)
        cards.append(f"""
<div class="vm-plan {'current' if is_cur else ''}">
  {cur_tag}
  <div class="vm-plan-name">{_esc(plan_labels[plan_key])}</div>
  <div class="vm-plan-price">{_esc(vm_data.PLAN_PRICES[plan_key])}</div>
  {feat_html}
</div>""")
    st.markdown(f'<div class="vm-plan-grid">{"".join(cards)}</div>',
                unsafe_allow_html=True)


# =========================================================================
#  Section: AI Pentester (PentestGPT-style)
# =========================================================================
def render_ai_pentester(lang: Lang, ai_pentest_fn, has_api_key: bool) -> None:
    """ai_pentest_fn(scan_dict, lang) -> {reasoning, commands, summary}"""
    user = vm_data.current_user()
    company = vm_data.current_company()
    if not user or not company:
        return

    st.markdown(
        f'<div class="vm-section-title">{t(lang, "vm_pen_title")}</div>',
        unsafe_allow_html=True,
    )
    st.caption(t(lang, "vm_pen_caption"))

    if not has_api_key:
        st.error(t(lang, "vm_pen_no_key"))
        return

    st.warning(t(lang, "vm_pen_disclaimer"))

    scans = sorted(
        vm_data.company_scans(company["id"]),
        key=lambda s: s.get("completed_at", s.get("started_at", "")),
        reverse=True,
    )
    if not scans:
        st.info(t(lang, "vm_pen_no_scans"))
        return

    options = {}
    for s in scans:
        d = vm_data.get_domain(s["domain_id"])
        domain_name = d["domain"] if d else "—"
        options[s["id"]] = (
            f'{domain_name} · {s["scan_type"]} · '
            f'score={s["score"]} · {_human_dt(s.get("completed_at",""))}'
        )

    cols = st.columns([4, 1])
    pick = cols[0].selectbox(
        t(lang, "vm_pen_select_scan"),
        options=list(options.keys()),
        format_func=lambda k: options[k],
        key="vm_pen_pick",
    )
    run = cols[1].button(t(lang, "vm_pen_run"), type="primary",
                         use_container_width=True, key="vm_pen_run_btn")

    cache_key = f"vm_pen_result_{pick}"

    if run:
        scan = next((s for s in scans if s["id"] == pick), None)
        if scan:
            with st.spinner(t(lang, "vm_pen_running")):
                try:
                    out = ai_pentest_fn(scan, lang)
                    st.session_state[cache_key] = out
                    vm_data.audit(user["id"], "ai_pentester.generate",
                                  "scan", scan["id"],
                                  f"AI pentest plan generated · {scan['scan_type']}")
                except Exception as exc:
                    st.error(f"AI error: {exc}")

    out = st.session_state.get(cache_key)
    if not out:
        return

    summary = (out.get("summary") or "").strip()
    reasoning = (out.get("reasoning") or "").strip()
    commands = (out.get("commands") or "").strip()

    if summary:
        st.markdown(f"#### {t(lang, 'vm_pen_summary')}")
        st.info(summary)

    if reasoning:
        with st.expander(t(lang, "vm_pen_attack_tree"), expanded=True):
            st.markdown(reasoning)

    if commands:
        with st.expander(t(lang, "vm_pen_pocs"), expanded=True):
            st.markdown(commands)

    md_report = (
        f"# AI Pentest Report\n\n"
        f"## Executive Summary\n\n{summary}\n\n"
        f"## Attack Tree\n\n{reasoning}\n\n"
        f"## PoCs\n\n{commands}\n"
    )
    st.download_button(
        t(lang, "vm_pen_export_md"),
        data=md_report.encode("utf-8"),
        file_name=f"pentest-report-{pick}.md",
        mime="text/markdown",
        key=f"vm_pen_dl_{pick}",
    )


# =========================================================================
#  Section: AI Code Review (SAST)
# =========================================================================
_SUPPORTED_CODE_LANGS = [
    "auto", "python", "javascript", "typescript", "php", "java", "go",
    "ruby", "csharp", "sql", "html", "bash",
]


def render_code_review(lang: Lang, code_review_fn, has_api_key: bool) -> None:
    """code_review_fn(code, language, filename, lang) -> {findings, summary, truncated}"""
    user = vm_data.current_user()
    company = vm_data.current_company()
    if not user or not company:
        return

    st.markdown(
        f'<div class="vm-section-title">{t(lang, "vm_cr_title")}</div>',
        unsafe_allow_html=True,
    )
    st.caption(t(lang, "vm_cr_caption"))

    if not has_api_key:
        st.error(t(lang, "vm_pen_no_key"))
        return

    cols = st.columns([3, 1])
    code_text = cols[0].text_area(
        t(lang, "vm_cr_paste"),
        height=260,
        key="vm_cr_code",
        placeholder="def login(u, p):\n    sql = \"SELECT * FROM users WHERE u='\" + u + \"' AND p='\" + p + \"'\"\n    db.execute(sql)\n",
    )
    with cols[1]:
        uploaded = st.file_uploader(
            t(lang, "vm_cr_upload"),
            type=["py", "js", "ts", "tsx", "jsx", "php", "java", "go", "rb",
                  "cs", "sql", "html", "sh"],
            key="vm_cr_upload_file",
        )
        language = st.selectbox(
            t(lang, "vm_cr_lang"),
            options=_SUPPORTED_CODE_LANGS,
            key="vm_cr_lang_pick",
        )
        run = st.button(t(lang, "vm_cr_run"), type="primary",
                        use_container_width=True, key="vm_cr_run_btn")

    filename = ""
    if uploaded is not None:
        try:
            code_text = uploaded.read().decode("utf-8", errors="replace")
            filename = uploaded.name
        except Exception as exc:
            st.error(f"File read error: {exc}")
            return

    if run:
        if not code_text or not code_text.strip():
            st.warning(t(lang, "vm_cr_empty"))
            return
        with st.spinner(t(lang, "vm_cr_running")):
            try:
                out = code_review_fn(code_text, language, filename, lang)
                st.session_state["vm_cr_result"] = out
                vm_data.audit(user["id"], "ai_codereview.run", "code",
                              filename or "snippet",
                              f"language={language}")
            except Exception as exc:
                st.error(f"AI error: {exc}")
                return

    out = st.session_state.get("vm_cr_result")
    if not out:
        return

    if out.get("truncated"):
        st.warning(t(lang, "vm_cr_truncated"))

    summary = (out.get("summary") or "").strip()
    if summary:
        st.info(summary)

    findings = out.get("findings") or []
    if not findings:
        st.success(t(lang, "vm_cr_no_findings"))
        return

    sev_rank = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    findings = sorted(findings, key=lambda f: sev_rank.get(f.get("severity", "info"), 9))

    for i, f in enumerate(findings, 1):
        sev = f.get("severity", "info")
        title = f.get("title", "—")
        cwe = f.get("cwe", "") or ""
        ls = f.get("line_start", 0)
        le = f.get("line_end", 0)
        line_label = (
            f'{t(lang, "vm_cr_line")} {ls}' if ls and (not le or ls == le)
            else (f'{t(lang, "vm_cr_line")} {ls}–{le}' if ls and le else "")
        )

        chips = [f'<span class="vm-meta-chip">{_esc(cwe)}</span>'] if cwe else []
        if line_label:
            chips.append(f'<span class="vm-meta-chip">{_esc(line_label)}</span>')

        st.markdown(f"""
<div class="vm-vuln-card">
  <div class="vm-vuln-header">
    <div class="vm-vuln-title">{i}. {_esc(title)}</div>
    <span class="vm-sev {sev}">{t(lang, f"vm_{sev}")}</span>
  </div>
  <div class="vm-vuln-meta-row">{"".join(chips)}</div>
  <div class="vm-vuln-desc">{_esc(f.get('description',''))}</div>
</div>""", unsafe_allow_html=True)

        snippet = f.get("vulnerable_snippet") or ""
        if snippet:
            st.markdown(f"**{t(lang, 'vm_cr_vuln_code')}:**")
            st.code(snippet, language=language if language != "auto" else None)

        exploit = f.get("exploit_example") or ""
        if exploit:
            st.markdown(f"**{t(lang, 'vm_cr_exploit_ex')}:**")
            st.code(exploit, language=language if language != "auto" else None)

        fix = f.get("fix_snippet") or ""
        if fix:
            st.markdown(f"**{t(lang, 'vm_cr_fix_code')}:**")
            st.code(fix, language=language if language != "auto" else None)

        refs = f.get("references") or []
        if refs:
            items = "".join(f'- [{_esc(r)}]({_esc(r)})\n' for r in refs)
            st.markdown(f"**{t(lang, 'vm_refs_label')}:**\n{items}")

        st.markdown('<div class="vm-divider"></div>', unsafe_allow_html=True)


# =========================================================================
#  Section: Audit
# =========================================================================
def render_audit(lang: Lang) -> None:
    user = vm_data.current_user()
    company = vm_data.current_company()
    if not user:
        return
    st.markdown(f'<div class="vm-section-title">{t(lang, "vm_section_audit")}</div>',
                unsafe_allow_html=True)
    entries = (vm_data.audit_for_company(company["id"]) if company
               else list(st.session_state.vm_audit))
    if user["role"] == vm_data.ROLE_SUPER:
        entries = sorted(st.session_state.vm_audit,
                         key=lambda x: x["timestamp"], reverse=True)
    if not entries:
        st.markdown(f'<div class="vm-empty">{t(lang, "vm_audit_no_entries")}</div>',
                    unsafe_allow_html=True)
        return
    rows = []
    for a in entries[:200]:
        u = vm_data.get_user(a["user_id"])
        rows.append({
            "timestamp": _human_dt(a["timestamp"]),
            "user":      u["email"] if u else a["user_id"],
            "action":    a["action"],
            "entity":    a["entity"],
            "entity_id": a["entity_id"],
            "details":   a["details"],
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


# =========================================================================
#  Section: Admin (super only)
# =========================================================================
def render_admin(lang: Lang) -> None:
    user = vm_data.current_user()
    if not user or user["role"] != vm_data.ROLE_SUPER:
        st.warning("هذا القسم متاح فقط لـ Super Admin.")
        return

    st.markdown(f'<div class="vm-section-title">{t(lang, "vm_section_admin")}</div>',
                unsafe_allow_html=True)
    s = vm_data.system_stats()
    _render_kpis([
        ("info",    t(lang, "vm_admin_companies"), str(s["companies"])),
        ("info",    t(lang, "vm_admin_users"),     str(s["users"])),
        ("",        t(lang, "vm_total_domains"),   str(s["domains"])),
        ("",        t(lang, "vm_total_scans"),     str(s["scans"])),
        ("crit",    t(lang, "vm_open_vulns"),      str(s["vulns_open"])),
    ])

    st.markdown(f'<div class="vm-section-title">{t(lang, "vm_admin_companies")}</div>',
                unsafe_allow_html=True)
    crows = []
    for c in vm_data.all_companies():
        ds = vm_data.company_domains(c["id"])
        ss = vm_data.company_scans(c["id"])
        vs = vm_data.company_vulns(c["id"])
        crows.append({
            "id":    c["id"],
            "name":  c["name"],
            "plan":  c["subscription"],
            "since": _human_dt(c["created_at"]),
            "domains": len(ds), "scans": len(ss), "open_vulns": sum(1 for v in vs if v["status"] == "open"),
        })
    st.dataframe(pd.DataFrame(crows).drop(columns=["id"]),
                 use_container_width=True, hide_index=True)

    st.markdown(f'<div class="vm-section-title">{t(lang, "vm_admin_workers")}</div>',
                unsafe_allow_html=True)
    workers = [
        ("Passive scanner (built-in)", "online", "var(--cb-success-strong)"),
        ("OWASP ZAP",                  "offline", "var(--cb-text-3)"),
        ("Nuclei",                     "offline", "var(--cb-text-3)"),
        ("Nmap",                       "offline", "var(--cb-text-3)"),
        ("Report renderer",            "online", "var(--cb-success-strong)"),
        ("AI analyst (OpenAI)",        "conditional", "var(--cb-warn-strong)"),
    ]
    rows = []
    for name, status, _ in workers:
        rows.append({"worker": name, "status": status})
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    st.caption("لتفعيل ZAP/Nuclei/Nmap ضع worker container منفصل — البنية جاهزة (انظر README).")
