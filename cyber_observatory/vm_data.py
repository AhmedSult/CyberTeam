"""منصّة إدارة الثغرات — طبقة البيانات.

نموذج بيانات Multi-tenant. session_state = working cache، SQLite = التخزين الدائم.
كل mutator يكتب write-through إلى القاعدة، وعند بدء الجلسة يحمّل البيانات منها.
"""
from __future__ import annotations

import secrets
from datetime import datetime, timedelta
from typing import Any

import streamlit as st

from cyber_observatory import storage


# =========================================================================
#  Constants
# =========================================================================
ROLE_SUPER = "super_admin"
ROLE_COMPANY = "company_admin"
ROLE_MEMBER = "team_member"

ROLE_LABELS_AR: dict[str, str] = {
    ROLE_SUPER:   "Super Admin · صلاحيات النظام",
    ROLE_COMPANY: "Company Admin · مسؤول الشركة",
    ROLE_MEMBER:  "Team Member · عضو الفريق",
}
ROLE_LABELS_EN: dict[str, str] = {
    ROLE_SUPER:   "Super Admin · Platform owner",
    ROLE_COMPANY: "Company Admin · Tenant owner",
    ROLE_MEMBER:  "Team Member · Read & remediate",
}

PLAN_FREE = "free"
PLAN_STARTER = "starter"
PLAN_BUSINESS = "business"
PLAN_ENTERPRISE = "enterprise"

PLAN_LIMITS: dict[str, dict[str, Any]] = {
    PLAN_FREE: {
        "max_domains": 1,    "max_scans_month": 5,    "ai_analysis": False,
        "scan_types": ["quick", "headers", "ssl"],
        "report_formats": ["html"],
    },
    PLAN_STARTER: {
        "max_domains": 5,    "max_scans_month": 50,   "ai_analysis": True,
        "scan_types": ["quick", "headers", "ssl", "full"],
        "report_formats": ["html", "csv"],
    },
    PLAN_BUSINESS: {
        "max_domains": 25,   "max_scans_month": 500,  "ai_analysis": True,
        "scan_types": ["quick", "headers", "ssl", "full", "api"],
        "report_formats": ["html", "csv", "pdf"],
    },
    PLAN_ENTERPRISE: {
        "max_domains": 9999, "max_scans_month": 9999, "ai_analysis": True,
        "scan_types": ["quick", "headers", "ssl", "full", "api"],
        "report_formats": ["html", "csv", "pdf"],
    },
}

PLAN_LABELS_AR: dict[str, str] = {
    PLAN_FREE: "مجانية", PLAN_STARTER: "Starter",
    PLAN_BUSINESS: "Business", PLAN_ENTERPRISE: "Enterprise",
}
PLAN_LABELS_EN: dict[str, str] = {
    PLAN_FREE: "Free", PLAN_STARTER: "Starter",
    PLAN_BUSINESS: "Business", PLAN_ENTERPRISE: "Enterprise",
}

PLAN_PRICES: dict[str, str] = {
    PLAN_FREE: "0 ريال/شهر",
    PLAN_STARTER: "199 ريال/شهر",
    PLAN_BUSINESS: "799 ريال/شهر",
    PLAN_ENTERPRISE: "حسب الاتفاقية",
}

# Severity to CVSS estimate (passive scanner — heuristic).
SEVERITY_TO_CVSS: dict[str, float] = {
    "critical": 9.5, "high": 7.5, "medium": 5.0, "low": 3.0, "info": 1.0, "ok": 0.0,
}

OWASP_2021 = {
    "transport": "A02:2021 Cryptographic Failures",
    "headers":   "A05:2021 Security Misconfiguration",
    "cookies":   "A07:2021 Identification & Authentication Failures",
    "exposure":  "A01:2021 Broken Access Control",
    "info":      "A05:2021 Security Misconfiguration",
    "dns":       "A07:2021 Identification & Authentication Failures",
    "content":   "A02:2021 Cryptographic Failures",
}


def map_cwe(domain: str, title: str) -> str:
    t = (title or "").lower()
    if domain == "transport":
        if "تلق" in title or "ssl" in t or "tls" in t or "شهادة" in title:
            return "CWE-326: Inadequate Encryption Strength"
        if "https" in t or "إعادة توجيه" in title or "http" in t:
            return "CWE-319: Cleartext Transmission of Sensitive Information"
        return "CWE-326: Inadequate Encryption Strength"
    if domain == "headers":
        if "csp" in t or "content-security" in t or "xss" in t or "clickjacking" in title.lower():
            return "CWE-1021: Improper Restriction of Rendered UI Layers"
        return "CWE-693: Protection Mechanism Failure"
    if domain == "cookies":
        return "CWE-614: Sensitive Cookie Without 'Secure' Flag"
    if domain == "exposure":
        return "CWE-538: File and Directory Information Exposure"
    if domain == "info":
        return "CWE-200: Information Exposure"
    if domain == "dns":
        return "CWE-290: Authentication Bypass by Spoofing"
    if domain == "content":
        return "CWE-311: Missing Encryption of Sensitive Data"
    return "CWE-200: Information Exposure"


# =========================================================================
#  Helpers
# =========================================================================
def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _ago(minutes: int) -> str:
    return (datetime.now() - timedelta(minutes=minutes)).isoformat(timespec="seconds")


def _gen_id(prefix: str = "") -> str:
    return f"{prefix}{secrets.token_hex(4)}"


def _gen_token() -> str:
    return "cybershield-verify-" + secrets.token_hex(8)


# =========================================================================
#  State init (clean slate — no demo data)
# =========================================================================
def init_state() -> None:
    """Load persisted data from SQLite into session_state (once per session)."""
    if st.session_state.get("vm_initialized"):
        return

    storage.init_db()
    data = storage.load_all()

    st.session_state.vm_companies       = data["companies"]
    st.session_state.vm_users           = data["users"]
    st.session_state.vm_domains         = data["domains"]
    st.session_state.vm_scans           = data["scans"]
    st.session_state.vm_vulnerabilities = data["vulnerabilities"]
    st.session_state.vm_notifications   = data["notifications"]
    st.session_state.vm_reports         = data["reports"]
    st.session_state.vm_invitations     = data["invitations"]
    st.session_state.vm_audit           = data["audit"]

    persisted_uid = storage.get_meta("current_user_id")
    if persisted_uid and any(u["id"] == persisted_uid for u in st.session_state.vm_users):
        st.session_state.vm_current_user_id = persisted_uid
    else:
        st.session_state.vm_current_user_id = None

    st.session_state.vm_initialized = True


def bootstrap_super_admin(streamlit_user: str) -> dict:
    """Create the platform's first Super Admin from the Streamlit login.

    Idempotent: if a user already exists, just ensure the active user is set.
    """
    init_state()
    if st.session_state.vm_users:
        if not get_user(st.session_state.get("vm_current_user_id")):
            st.session_state.vm_current_user_id = st.session_state.vm_users[0]["id"]
        return get_user(st.session_state.vm_current_user_id)  # type: ignore[return-value]

    raw = (streamlit_user or "admin").strip()
    email = raw if "@" in raw else f"{raw}@local"
    name = raw.split("@")[0] if "@" in raw else raw
    user = {
        "id": _gen_id("u-"),
        "email": email,
        "name": name,
        "role": ROLE_SUPER,
        "company_id": None,
        "verified": True,
        "mfa_enabled": False,
        "created_at": _now(),
    }
    st.session_state.vm_users.append(user)
    storage.save_user(user)
    set_active_user(user["id"])
    audit(user["id"], "user.bootstrap", "user", user["id"],
          "إنشاء أول حساب Super Admin من تسجيل الدخول")
    return user


def create_company_and_admin(
    company_name: str, plan: str,
    admin_name: str, admin_email: str,
    by_user: str,
) -> tuple[dict, dict]:
    """Create a new company and its first Company Admin user."""
    company = {
        "id": _gen_id("c-"),
        "name": company_name.strip(),
        "subscription": plan,
        "country": "SA",
        "created_at": _now(),
    }
    st.session_state.vm_companies.append(company)
    storage.save_company(company)

    admin = {
        "id": _gen_id("u-"),
        "email": admin_email.strip().lower(),
        "name": admin_name.strip(),
        "role": ROLE_COMPANY,
        "company_id": company["id"],
        "verified": True,
        "mfa_enabled": False,
        "created_at": _now(),
    }
    st.session_state.vm_users.append(admin)
    storage.save_user(admin)

    audit(by_user, "company.create", "company", company["id"],
          f"إنشاء شركة: {company['name']} · باقة {plan}")
    audit(by_user, "user.create", "user", admin["id"],
          f"إضافة Company Admin: {admin['email']}")
    notify(admin["id"], "🎉 مرحباً بك",
           f"تم إنشاء شركة «{company['name']}» بنجاح. يمكنك الآن إضافة موقعك الأول.",
           level="success")
    return company, admin


# =========================================================================
#  Read accessors
# =========================================================================
def current_user() -> dict[str, Any] | None:
    init_state()
    uid = st.session_state.get("vm_current_user_id")
    return next((u for u in st.session_state.vm_users if u["id"] == uid), None)


def current_company() -> dict[str, Any] | None:
    u = current_user()
    if not u or not u.get("company_id"):
        return None
    return next(
        (c for c in st.session_state.vm_companies if c["id"] == u["company_id"]),
        None,
    )


def current_role() -> str:
    u = current_user()
    return u["role"] if u else ROLE_MEMBER


def get_user(user_id: str) -> dict | None:
    return next((u for u in st.session_state.vm_users if u["id"] == user_id), None)


def get_company(company_id: str) -> dict | None:
    return next((c for c in st.session_state.vm_companies if c["id"] == company_id), None)


def get_domain(domain_id: str) -> dict | None:
    return next((d for d in st.session_state.vm_domains if d["id"] == domain_id), None)


def get_scan(scan_id: str) -> dict | None:
    return next((s for s in st.session_state.vm_scans if s["id"] == scan_id), None)


def company_users(company_id: str) -> list[dict]:
    return [u for u in st.session_state.vm_users if u.get("company_id") == company_id]


def company_domains(company_id: str) -> list[dict]:
    return [d for d in st.session_state.vm_domains if d["company_id"] == company_id]


def company_scans(company_id: str) -> list[dict]:
    domain_ids = {d["id"] for d in company_domains(company_id)}
    return [s for s in st.session_state.vm_scans if s["domain_id"] in domain_ids]


def company_vulns(company_id: str) -> list[dict]:
    domain_ids = {d["id"] for d in company_domains(company_id)}
    return [v for v in st.session_state.vm_vulnerabilities if v["domain_id"] in domain_ids]


def all_companies() -> list[dict]:
    return list(st.session_state.vm_companies)


def all_users() -> list[dict]:
    return list(st.session_state.vm_users)


def all_scans() -> list[dict]:
    return list(st.session_state.vm_scans)


# =========================================================================
#  Mutators
# =========================================================================
def set_active_user(user_id: str) -> None:
    if get_user(user_id):
        st.session_state.vm_current_user_id = user_id
        try:
            storage.set_meta("current_user_id", user_id)
        except Exception:
            pass


def add_domain(company_id: str, domain: str, description: str,
               environment: str, tags: list[str], by_user: str) -> dict:
    rec = {
        "id": _gen_id("d-"),
        "company_id": company_id,
        "domain": domain.strip().lower(),
        "description": description,
        "environment": environment,
        "tags": tags,
        "verified": False,
        "verification_method": None,
        "verification_token": _gen_token(),
        "added_at": _now(),
        "added_by": by_user,
    }
    st.session_state.vm_domains.append(rec)
    storage.save_domain(rec)
    audit(by_user, "domain.create", "domain", rec["id"], f"تمت إضافة {rec['domain']}")
    notify(by_user, "تمت إضافة الموقع",
           f"تمت إضافة {rec['domain']} وهو بحاجة للتحقق من الملكية قبل الفحص.",
           level="info")
    return rec


def remove_domain(domain_id: str, by_user: str) -> None:
    d = get_domain(domain_id)
    if not d:
        return
    st.session_state.vm_domains = [x for x in st.session_state.vm_domains if x["id"] != domain_id]
    st.session_state.vm_scans = [s for s in st.session_state.vm_scans if s["domain_id"] != domain_id]
    st.session_state.vm_vulnerabilities = [
        v for v in st.session_state.vm_vulnerabilities if v["domain_id"] != domain_id
    ]
    storage.delete_domain(domain_id)  # cascades to scans + vulns
    audit(by_user, "domain.delete", "domain", domain_id, f"حذف {d['domain']}")


def update_domain(domain_id: str, **fields) -> None:
    for d in st.session_state.vm_domains:
        if d["id"] == domain_id:
            d.update(fields)
            storage.save_domain(d)
            return


def verify_domain(domain_id: str, method: str, by_user: str) -> bool:
    d = get_domain(domain_id)
    if not d:
        return False
    d["verified"] = True
    d["verification_method"] = method
    storage.save_domain(d)
    audit(by_user, "domain.verify", "domain", domain_id,
          f"verified via {method}: {d['domain']}")
    notify(by_user, "تم التحقّق من الموقع",
           f"تم التحقّق من ملكية {d['domain']} عبر {method}.", level="success")
    return True


def record_scan(domain_id: str, scan_type: str, result: dict,
                started_at: str, by_user: str) -> dict:
    counts = result["score"]["counts"]
    scan = {
        "id": _gen_id("s-"),
        "domain_id": domain_id,
        "scan_type": scan_type,
        "status": "completed",
        "started_at": started_at,
        "completed_at": _now(),
        "score": int(result["score"]["score"]),
        "grade": result["score"]["grade"],
        "findings_count": result["score"]["total"],
        "critical": counts.get("critical", 0),
        "high":     counts.get("high", 0),
        "medium":   counts.get("medium", 0),
        "low":      counts.get("low", 0),
        "ok":       counts.get("ok", 0),
        "result": result,
        "by_user": by_user,
    }
    st.session_state.vm_scans.append(scan)
    storage.save_scan(scan)

    for f in result["findings"]:
        if f["severity"] in ("ok", "info"):
            continue
        v = {
            "id": _gen_id("v-"),
            "scan_id": scan["id"],
            "domain_id": domain_id,
            "title": f["title"],
            "severity": f["severity"],
            "cvss": SEVERITY_TO_CVSS.get(f["severity"], 0.0),
            "description": f["description"],
            "fix": f["fix"],
            "evidence": f.get("evidence", ""),
            "url": result.get("url", ""),
            "category": f["domain"],
            "cwe": map_cwe(f["domain"], f["title"]),
            "owasp": OWASP_2021.get(f["domain"], "—"),
            "ecc_ref": f.get("ecc_ref", ""),
            "status": "open",
            "found_at": _now(),
            "fixed_at": None,
            # exploitation context
            "kind": f.get("kind", ""),
            "impact": f.get("impact", ""),
            "attack_summary": f.get("attack_summary", ""),
            "attack_steps": list(f.get("attack_steps", []) or []),
            "attack_code": list(f.get("attack_code", []) or []),
            "references": list(f.get("references", []) or []),
        }
        st.session_state.vm_vulnerabilities.append(v)
        storage.save_vuln(v)

    domain = get_domain(domain_id)
    domain_name = domain["domain"] if domain else "—"
    audit(by_user, "scan.complete", "scan", scan["id"],
          f"{scan_type} on {domain_name} → score={scan['score']}")

    if counts.get("critical", 0) > 0:
        notify(by_user, "🚨 ثغرة حرجة مكتشفة",
               f"اكتُشِفت {counts['critical']} ثغرة حرجة في {domain_name}",
               level="critical")
    elif counts.get("high", 0) > 0:
        notify(by_user, "⚠️ ثغرات عالية الخطورة",
               f"اكتُشِفت {counts['high']} ثغرة عالية في {domain_name}",
               level="warn")
    else:
        notify(by_user, "✅ اكتمل الفحص",
               f"اكتمل فحص {domain_name} · الدرجة {scan['score']}/{scan['grade']}",
               level="info")
    return scan


def update_vuln_status(vuln_id: str, new_status: str, by_user: str) -> None:
    for v in st.session_state.vm_vulnerabilities:
        if v["id"] == vuln_id:
            old = v["status"]
            v["status"] = new_status
            v["fixed_at"] = _now() if new_status == "fixed" else None
            storage.save_vuln(v)
            audit(by_user, "vuln.update", "vuln", vuln_id, f"{old} → {new_status}")
            return


# Notifications
def notify(user_id: str, title: str, body: str, level: str = "info") -> None:
    rec = {
        "id": _gen_id("n-"),
        "user_id": user_id,
        "title": title,
        "body": body,
        "level": level,
        "read": False,
        "created_at": _now(),
    }
    st.session_state.vm_notifications.append(rec)
    storage.save_notification(rec)


def user_notifications(user_id: str, unread_only: bool = False) -> list[dict]:
    notifs = [n for n in st.session_state.vm_notifications if n["user_id"] == user_id]
    if unread_only:
        notifs = [n for n in notifs if not n["read"]]
    return sorted(notifs, key=lambda x: x["created_at"], reverse=True)


def mark_all_read(user_id: str) -> None:
    for n in st.session_state.vm_notifications:
        if n["user_id"] == user_id:
            n["read"] = True
    storage.mark_user_notifications_read(user_id)


# Audit
def audit(user_id: str, action: str, entity: str, entity_id: str, details: str) -> None:
    rec = {
        "id": _gen_id("a-"),
        "timestamp": _now(),
        "user_id": user_id,
        "action": action,
        "entity": entity,
        "entity_id": str(entity_id),
        "details": details,
    }
    st.session_state.vm_audit.append(rec)
    storage.save_audit(rec)


def audit_for_company(company_id: str) -> list[dict]:
    domain_ids = {d["id"] for d in company_domains(company_id)}
    scan_ids = {s["id"] for s in company_scans(company_id)}
    vuln_ids = {v["id"] for v in company_vulns(company_id)}
    user_ids = {u["id"] for u in company_users(company_id)}
    relevant = []
    for a in st.session_state.vm_audit:
        if a["entity"] == "domain" and a["entity_id"] in domain_ids:
            relevant.append(a)
        elif a["entity"] == "scan" and a["entity_id"] in scan_ids:
            relevant.append(a)
        elif a["entity"] == "vuln" and a["entity_id"] in vuln_ids:
            relevant.append(a)
        elif a["entity"] == "user" and a["entity_id"] in user_ids:
            relevant.append(a)
    return sorted(relevant, key=lambda x: x["timestamp"], reverse=True)


# Team management
def invite_member(company_id: str, email: str, role: str, by_user: str) -> dict:
    rec = {
        "id": _gen_id("i-"),
        "company_id": company_id,
        "email": email.strip().lower(),
        "role": role,
        "invited_by": by_user,
        "invited_at": _now(),
        "status": "pending",
    }
    st.session_state.vm_invitations.append(rec)
    storage.save_invitation(rec)
    audit(by_user, "invitation.send", "user", rec["id"], f"دعوة {email} كـ {role}")
    return rec


def remove_member(user_id: str, by_user: str) -> None:
    target = get_user(user_id)
    if not target:
        return
    st.session_state.vm_users = [u for u in st.session_state.vm_users if u["id"] != user_id]
    storage.delete_user(user_id)
    audit(by_user, "user.delete", "user", user_id, f"إزالة {target['email']}")


def add_user_to_company(name: str, email: str, role: str, company_id: str) -> dict:
    rec = {
        "id": _gen_id("u-"),
        "email": email.strip().lower(),
        "name": name.strip(),
        "role": role,
        "company_id": company_id,
        "verified": False,
        "mfa_enabled": False,
        "created_at": _now(),
    }
    st.session_state.vm_users.append(rec)
    storage.save_user(rec)
    return rec


# =========================================================================
#  Stats
# =========================================================================
def dashboard_stats(company_id: str) -> dict[str, int]:
    domains = company_domains(company_id)
    scans = company_scans(company_id)
    vulns = company_vulns(company_id)
    open_vulns = [v for v in vulns if v["status"] == "open"]

    last_by_domain: dict[str, dict] = {}
    for s in scans:
        cur = last_by_domain.get(s["domain_id"])
        if cur is None or s["completed_at"] > cur["completed_at"]:
            last_by_domain[s["domain_id"]] = s
    avg_score = (
        round(sum(s["score"] for s in last_by_domain.values()) / len(last_by_domain))
        if last_by_domain else 0
    )

    sev_counter = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for v in open_vulns:
        sev_counter[v["severity"]] = sev_counter.get(v["severity"], 0) + 1

    return {
        "domains_total":    len(domains),
        "domains_verified": sum(1 for d in domains if d["verified"]),
        "scans_total":      len(scans),
        "scans_completed":  sum(1 for s in scans if s["status"] == "completed"),
        "vulns_open":       len(open_vulns),
        "vulns_fixed":      sum(1 for v in vulns if v["status"] == "fixed"),
        "critical":         sev_counter["critical"],
        "high":             sev_counter["high"],
        "medium":           sev_counter["medium"],
        "low":              sev_counter["low"],
        "avg_score":        avg_score,
    }


def system_stats() -> dict[str, int]:
    return {
        "companies":  len(st.session_state.vm_companies),
        "users":      len(st.session_state.vm_users),
        "domains":    len(st.session_state.vm_domains),
        "scans":      len(st.session_state.vm_scans),
        "vulns_open": sum(1 for v in st.session_state.vm_vulnerabilities if v["status"] == "open"),
    }


# =========================================================================
#  Subscription helpers
# =========================================================================
def plan_for_company(company_id: str) -> str:
    c = get_company(company_id)
    return (c.get("subscription") if c else PLAN_FREE) or PLAN_FREE


def plan_limits(plan: str) -> dict[str, Any]:
    return PLAN_LIMITS.get(plan, PLAN_LIMITS[PLAN_FREE])


def domains_quota_used(company_id: str) -> tuple[int, int]:
    used = len(company_domains(company_id))
    limit = plan_limits(plan_for_company(company_id))["max_domains"]
    return used, limit


def scans_quota_used(company_id: str) -> tuple[int, int]:
    """Counts scans done in the last 30 days."""
    threshold = (datetime.now() - timedelta(days=30)).isoformat()
    used = sum(1 for s in company_scans(company_id) if s["started_at"] >= threshold)
    limit = plan_limits(plan_for_company(company_id))["max_scans_month"]
    return used, limit
