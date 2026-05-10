"""طبقة تخزين SQLite للمنصّة.

write-through: كل mutator في vm_data يكتب إلى session_state وإلى SQLite معاً.
عند بدء جلسة جديدة، init_state يحمّل البيانات الموجودة من القاعدة فيستعيد المستخدم
شركاته/مواقعه/فحوصاته/ثغراته. لا توجد بيانات تجريبية مسبقة.
"""
from __future__ import annotations

import json
import os
import sqlite3
import threading
from pathlib import Path
from typing import Any, Iterable

# ---------------------------------------------------------------------------
DB_PATH_ENV = "CYBERSHIELD_DB_PATH"
DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "vm.sqlite3"

_lock = threading.Lock()
_initialized = False


def db_path() -> Path:
    raw = os.environ.get(DB_PATH_ENV)
    return Path(raw) if raw else DEFAULT_DB_PATH


def get_conn() -> sqlite3.Connection:
    """Return a fresh connection. Streamlit reruns are short-lived; we open/close per call."""
    p = db_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(p), check_same_thread=False, timeout=15.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


# ---------------------------------------------------------------------------
#  Schema
# ---------------------------------------------------------------------------
SCHEMA = [
    """CREATE TABLE IF NOT EXISTS companies (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        subscription TEXT,
        country TEXT,
        created_at TEXT
    )""",
    """CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        email TEXT,
        name TEXT,
        role TEXT,
        company_id TEXT,
        verified INTEGER,
        mfa_enabled INTEGER,
        created_at TEXT
    )""",
    """CREATE TABLE IF NOT EXISTS domains (
        id TEXT PRIMARY KEY,
        company_id TEXT,
        domain TEXT,
        description TEXT,
        environment TEXT,
        tags_json TEXT,
        verified INTEGER,
        verification_method TEXT,
        verification_token TEXT,
        added_at TEXT,
        added_by TEXT
    )""",
    """CREATE TABLE IF NOT EXISTS scans (
        id TEXT PRIMARY KEY,
        domain_id TEXT,
        scan_type TEXT,
        status TEXT,
        started_at TEXT,
        completed_at TEXT,
        score INTEGER,
        grade TEXT,
        findings_count INTEGER,
        critical INTEGER,
        high INTEGER,
        medium INTEGER,
        low INTEGER,
        ok INTEGER,
        result_json TEXT,
        by_user TEXT
    )""",
    """CREATE TABLE IF NOT EXISTS vulnerabilities (
        id TEXT PRIMARY KEY,
        scan_id TEXT,
        domain_id TEXT,
        title TEXT,
        severity TEXT,
        cvss REAL,
        description TEXT,
        fix TEXT,
        evidence TEXT,
        url TEXT,
        category TEXT,
        cwe TEXT,
        owasp TEXT,
        ecc_ref TEXT,
        status TEXT,
        found_at TEXT,
        fixed_at TEXT,
        kind TEXT,
        impact TEXT,
        attack_summary TEXT,
        attack_steps_json TEXT,
        attack_code_json TEXT,
        references_json TEXT
    )""",
    """CREATE TABLE IF NOT EXISTS notifications (
        id TEXT PRIMARY KEY,
        user_id TEXT,
        title TEXT,
        body TEXT,
        level TEXT,
        is_read INTEGER,
        created_at TEXT
    )""",
    """CREATE TABLE IF NOT EXISTS reports (
        id TEXT PRIMARY KEY,
        company_id TEXT,
        type TEXT,
        title TEXT,
        body TEXT,
        created_at TEXT,
        by_user TEXT
    )""",
    """CREATE TABLE IF NOT EXISTS invitations (
        id TEXT PRIMARY KEY,
        company_id TEXT,
        email TEXT,
        role TEXT,
        invited_at TEXT,
        invited_by TEXT,
        status TEXT
    )""",
    """CREATE TABLE IF NOT EXISTS audit (
        id TEXT PRIMARY KEY,
        timestamp TEXT,
        user_id TEXT,
        action TEXT,
        entity TEXT,
        entity_id TEXT,
        details TEXT
    )""",
    """CREATE TABLE IF NOT EXISTS meta (
        key TEXT PRIMARY KEY,
        value TEXT
    )""",
]

# Indexes for common queries
INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_users_company ON users(company_id)",
    "CREATE INDEX IF NOT EXISTS idx_domains_company ON domains(company_id)",
    "CREATE INDEX IF NOT EXISTS idx_scans_domain ON scans(domain_id)",
    "CREATE INDEX IF NOT EXISTS idx_vulns_domain ON vulnerabilities(domain_id)",
    "CREATE INDEX IF NOT EXISTS idx_vulns_scan ON vulnerabilities(scan_id)",
    "CREATE INDEX IF NOT EXISTS idx_notifs_user ON notifications(user_id)",
    "CREATE INDEX IF NOT EXISTS idx_audit_ts ON audit(timestamp)",
]


def init_db() -> None:
    global _initialized
    if _initialized:
        return
    with _lock:
        if _initialized:
            return
        with get_conn() as conn:
            for stmt in SCHEMA:
                conn.execute(stmt)
            for idx in INDEXES:
                conn.execute(idx)
            conn.commit()
        _initialized = True


# ---------------------------------------------------------------------------
#  Serialization helpers
# ---------------------------------------------------------------------------
def _json_or_empty(val) -> str:
    try:
        return json.dumps(val or [], ensure_ascii=False)
    except Exception:
        return "[]"


def _json_loads(val) -> Any:
    if not val:
        return []
    try:
        return json.loads(val)
    except Exception:
        return []


# ---------------------------------------------------------------------------
#  COMPANIES
# ---------------------------------------------------------------------------
def save_company(c: dict) -> None:
    with get_conn() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO companies
               (id, name, subscription, country, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            (c["id"], c.get("name", ""), c.get("subscription", ""),
             c.get("country", ""), c.get("created_at", "")),
        )
        conn.commit()


def delete_company(company_id: str) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM companies WHERE id=?", (company_id,))
        conn.commit()


# ---------------------------------------------------------------------------
#  USERS
# ---------------------------------------------------------------------------
def save_user(u: dict) -> None:
    with get_conn() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO users
               (id, email, name, role, company_id, verified, mfa_enabled, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (u["id"], u.get("email", ""), u.get("name", ""),
             u.get("role", ""), u.get("company_id"),
             int(bool(u.get("verified"))), int(bool(u.get("mfa_enabled"))),
             u.get("created_at", "")),
        )
        conn.commit()


def delete_user(user_id: str) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM users WHERE id=?", (user_id,))
        conn.commit()


# ---------------------------------------------------------------------------
#  DOMAINS
# ---------------------------------------------------------------------------
def save_domain(d: dict) -> None:
    with get_conn() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO domains
               (id, company_id, domain, description, environment, tags_json,
                verified, verification_method, verification_token, added_at, added_by)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (d["id"], d.get("company_id"), d.get("domain", ""),
             d.get("description", ""), d.get("environment", ""),
             _json_or_empty(d.get("tags", [])),
             int(bool(d.get("verified"))),
             d.get("verification_method"),
             d.get("verification_token", ""),
             d.get("added_at", ""), d.get("added_by", "")),
        )
        conn.commit()


def delete_domain(domain_id: str) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM vulnerabilities WHERE domain_id=?", (domain_id,))
        conn.execute("DELETE FROM scans WHERE domain_id=?", (domain_id,))
        conn.execute("DELETE FROM domains WHERE id=?", (domain_id,))
        conn.commit()


# ---------------------------------------------------------------------------
#  SCANS
# ---------------------------------------------------------------------------
def save_scan(s: dict) -> None:
    with get_conn() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO scans
               (id, domain_id, scan_type, status, started_at, completed_at,
                score, grade, findings_count, critical, high, medium, low, ok,
                result_json, by_user)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (s["id"], s.get("domain_id"), s.get("scan_type", ""),
             s.get("status", ""), s.get("started_at", ""), s.get("completed_at", ""),
             int(s.get("score", 0)), s.get("grade", ""),
             int(s.get("findings_count", 0)),
             int(s.get("critical", 0)), int(s.get("high", 0)),
             int(s.get("medium", 0)), int(s.get("low", 0)), int(s.get("ok", 0)),
             json.dumps(s.get("result", {}), ensure_ascii=False),
             s.get("by_user", "")),
        )
        conn.commit()


def delete_scan(scan_id: str) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM vulnerabilities WHERE scan_id=?", (scan_id,))
        conn.execute("DELETE FROM scans WHERE id=?", (scan_id,))
        conn.commit()


# ---------------------------------------------------------------------------
#  VULNERABILITIES
# ---------------------------------------------------------------------------
def save_vuln(v: dict) -> None:
    with get_conn() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO vulnerabilities
               (id, scan_id, domain_id, title, severity, cvss, description, fix,
                evidence, url, category, cwe, owasp, ecc_ref, status,
                found_at, fixed_at, kind, impact, attack_summary,
                attack_steps_json, attack_code_json, references_json)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                       ?, ?, ?, ?, ?, ?)""",
            (v["id"], v.get("scan_id"), v.get("domain_id"),
             v.get("title", ""), v.get("severity", ""), float(v.get("cvss", 0.0)),
             v.get("description", ""), v.get("fix", ""), v.get("evidence", ""),
             v.get("url", ""), v.get("category", ""), v.get("cwe", ""),
             v.get("owasp", ""), v.get("ecc_ref", ""), v.get("status", "open"),
             v.get("found_at", ""), v.get("fixed_at"),
             v.get("kind", ""), v.get("impact", ""), v.get("attack_summary", ""),
             _json_or_empty(v.get("attack_steps", [])),
             _json_or_empty(v.get("attack_code", [])),
             _json_or_empty(v.get("references", []))),
        )
        conn.commit()


def delete_vuln(vuln_id: str) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM vulnerabilities WHERE id=?", (vuln_id,))
        conn.commit()


# ---------------------------------------------------------------------------
#  NOTIFICATIONS
# ---------------------------------------------------------------------------
def save_notification(n: dict) -> None:
    with get_conn() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO notifications
               (id, user_id, title, body, level, is_read, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (n["id"], n.get("user_id"), n.get("title", ""),
             n.get("body", ""), n.get("level", "info"),
             int(bool(n.get("read"))), n.get("created_at", "")),
        )
        conn.commit()


def mark_user_notifications_read(user_id: str) -> None:
    with get_conn() as conn:
        conn.execute("UPDATE notifications SET is_read=1 WHERE user_id=?", (user_id,))
        conn.commit()


# ---------------------------------------------------------------------------
#  REPORTS / INVITATIONS / AUDIT
# ---------------------------------------------------------------------------
def save_report(r: dict) -> None:
    with get_conn() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO reports
               (id, company_id, type, title, body, created_at, by_user)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (r["id"], r.get("company_id"), r.get("type", ""),
             r.get("title", ""), r.get("body", ""),
             r.get("created_at", ""), r.get("by_user", "")),
        )
        conn.commit()


def save_invitation(i: dict) -> None:
    with get_conn() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO invitations
               (id, company_id, email, role, invited_at, invited_by, status)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (i["id"], i.get("company_id"), i.get("email", ""),
             i.get("role", ""), i.get("invited_at", ""),
             i.get("invited_by", ""), i.get("status", "pending")),
        )
        conn.commit()


def save_audit(a: dict) -> None:
    with get_conn() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO audit
               (id, timestamp, user_id, action, entity, entity_id, details)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (a["id"], a.get("timestamp", ""), a.get("user_id", ""),
             a.get("action", ""), a.get("entity", ""),
             a.get("entity_id", ""), a.get("details", "")),
        )
        conn.commit()


# ---------------------------------------------------------------------------
#  META
# ---------------------------------------------------------------------------
def set_meta(key: str, value: str) -> None:
    with get_conn() as conn:
        conn.execute("INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)",
                     (key, value))
        conn.commit()


def get_meta(key: str) -> str | None:
    with get_conn() as conn:
        row = conn.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
        return row["value"] if row else None


# ---------------------------------------------------------------------------
#  Bulk load
# ---------------------------------------------------------------------------
def _rows_to_dicts(rows: Iterable[sqlite3.Row]) -> list[dict]:
    return [dict(r) for r in rows]


def load_all() -> dict[str, list[dict]]:
    """Read everything into Python dicts (matching session_state shape)."""
    init_db()
    with get_conn() as conn:
        companies = _rows_to_dicts(conn.execute("SELECT * FROM companies"))

        users_raw = _rows_to_dicts(conn.execute("SELECT * FROM users"))
        users = []
        for u in users_raw:
            u["verified"] = bool(u.get("verified"))
            u["mfa_enabled"] = bool(u.get("mfa_enabled"))
            users.append(u)

        domains_raw = _rows_to_dicts(conn.execute("SELECT * FROM domains"))
        domains = []
        for d in domains_raw:
            d["verified"] = bool(d.get("verified"))
            d["tags"] = _json_loads(d.pop("tags_json", "[]"))
            domains.append(d)

        scans_raw = _rows_to_dicts(conn.execute("SELECT * FROM scans"))
        scans = []
        for s in scans_raw:
            try:
                s["result"] = json.loads(s.pop("result_json", "{}") or "{}")
            except Exception:
                s["result"] = {}
                s.pop("result_json", None)
            scans.append(s)

        vulns_raw = _rows_to_dicts(conn.execute("SELECT * FROM vulnerabilities"))
        vulns = []
        for v in vulns_raw:
            v["attack_steps"] = _json_loads(v.pop("attack_steps_json", "[]"))
            v["attack_code"]  = _json_loads(v.pop("attack_code_json", "[]"))
            v["references"]   = _json_loads(v.pop("references_json", "[]"))
            vulns.append(v)

        notifs_raw = _rows_to_dicts(conn.execute("SELECT * FROM notifications"))
        notifs = []
        for n in notifs_raw:
            n["read"] = bool(n.pop("is_read", 0))
            notifs.append(n)

        reports     = _rows_to_dicts(conn.execute("SELECT * FROM reports"))
        invitations = _rows_to_dicts(conn.execute("SELECT * FROM invitations"))
        audit       = _rows_to_dicts(conn.execute("SELECT * FROM audit"))

    return {
        "companies":       companies,
        "users":           users,
        "domains":         domains,
        "scans":           scans,
        "vulnerabilities": vulns,
        "notifications":   notifs,
        "reports":         reports,
        "invitations":     invitations,
        "audit":           audit,
    }
