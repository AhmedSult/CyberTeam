"""فاحص أمان مواقع — passive web security scanner.

يجري فحوصاً غير تدخلية فقط (HTTP HEAD/GET، TLS handshake، DNS).
لا يستخدم أي تقنيات هجومية. آمن للاستخدام على أي موقع تملك صلاحية فحصه.
"""

from __future__ import annotations

import re
import socket
import ssl
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterable
from urllib.parse import urlparse

import requests

from cyber_observatory import exploits

USER_AGENT = "CyberShield-Scanner/1.0 (+passive security audit)"
TIMEOUT = 8
PROBE_TIMEOUT = 5

SEVERITIES: tuple[str, ...] = ("critical", "high", "medium", "low", "info", "ok")

# الفئات (بطاقات «المجال» في الواجهة).
DOMAIN_CATALOG: dict[str, dict[str, str]] = {
    "transport": {"title_ar": "النقل الآمن (HTTPS/TLS)",      "title_en": "Transport security (HTTPS/TLS)", "icon": "🔒", "ecc": "2-8"},
    "headers":   {"title_ar": "ترويسات الحماية",                "title_en": "Security headers",               "icon": "🛡️", "ecc": "2-3"},
    "cookies":   {"title_ar": "أمان الكوكيز",                   "title_en": "Cookie security",                "icon": "🍪", "ecc": "2-3"},
    "exposure":  {"title_ar": "كشف ملفات حسّاسة",                "title_en": "Sensitive file exposure",        "icon": "📂", "ecc": "2-7"},
    "info":      {"title_ar": "كشف معلومات الخادم",              "title_en": "Information disclosure",         "icon": "🕵️", "ecc": "2-3"},
    "dns":       {"title_ar": "سجلات البريد و DNS",              "title_en": "Email & DNS records",            "icon": "🌐", "ecc": "2-15"},
    "content":   {"title_ar": "محتوى الصفحة",                    "title_en": "Page content",                   "icon": "📄", "ecc": "2-7"},
}

DOMAIN_ORDER: tuple[str, ...] = (
    "transport", "headers", "cookies", "exposure", "info", "dns", "content",
)


# =========================================================================
#  Data
# =========================================================================
@dataclass
class Finding:
    severity: str
    domain: str
    title: str
    description: str
    fix: str
    evidence: str = ""
    references: list[str] = field(default_factory=list)
    ecc_ref: str = ""
    kind: str = ""           # stable id for exploit lookup
    impact: str = ""         # populated from exploits registry
    attack_summary: str = ""
    attack_steps: list[str] = field(default_factory=list)
    attack_code: list[dict] = field(default_factory=list)


# =========================================================================
#  Helpers
# =========================================================================
def _normalize_url(url: str) -> tuple[str, str]:
    raw = (url or "").strip()
    if not raw:
        raise ValueError("URL is required")
    if not re.match(r"^https?://", raw, re.I):
        raw = "https://" + raw
    parsed = urlparse(raw)
    if not parsed.hostname:
        raise ValueError("Invalid URL")
    return raw, parsed.hostname


def _fetch(url: str) -> requests.Response:
    return requests.get(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "text/html,*/*"},
        timeout=TIMEOUT,
        allow_redirects=True,
        verify=True,
    )


def _set_cookie_lines(resp: requests.Response) -> list[str]:
    """يرجع سطور Set-Cookie منفصلة (يدعم تكرار الترويسة)."""
    raw = getattr(resp, "raw", None)
    if raw is not None:
        headers = getattr(raw, "headers", None)
        if headers is not None and hasattr(headers, "getlist"):
            try:
                items = headers.getlist("Set-Cookie")
                if items:
                    return [s for s in items if s]
            except Exception:
                pass
    joined = resp.headers.get("Set-Cookie", "")
    if not joined:
        return []
    # تقسيم تقريبي: تكرار "name=value; …, name2=value2; …"
    return [c.strip() for c in re.split(r",(?=\s*[A-Za-z0-9_\-]+=)", joined) if c.strip()]


# =========================================================================
#  Checks
# =========================================================================
def _check_http_to_https(url: str, findings: list[Finding]) -> None:
    parsed = urlparse(url)
    if parsed.scheme.lower() == "http":
        findings.append(Finding(
            severity="critical", domain="transport",
            title="الموقع لا يعمل عبر HTTPS",
            description="بروتوكول HTTP غير مشفّر؛ كل البيانات (كلمات المرور، الجلسات، الكوكيز) قابلة للاعتراض على الشبكة.",
            fix="فعّل HTTPS عبر شهادة مجانية (Let's Encrypt) أو شهادة من مزوّد معتمد، ثم وجّه HTTP→HTTPS بكود 301 وفعّل HSTS.",
            ecc_ref="2-8-1",
            kind="no_https",
        ))
        return
    http_url = "http://" + parsed.netloc + (parsed.path or "/")
    try:
        r = requests.get(http_url, timeout=PROBE_TIMEOUT, allow_redirects=False,
                         headers={"User-Agent": USER_AGENT})
        loc = r.headers.get("Location", "")
        if r.status_code in (301, 302, 307, 308) and loc.lower().startswith("https://"):
            findings.append(Finding(
                severity="ok", domain="transport",
                title="إعادة توجيه HTTP→HTTPS مفعّلة",
                description=f"الخادم يعيد التوجيه إلى HTTPS (رمز {r.status_code}).",
                fix="حافظ على هذه الإعدادات وفعّل HSTS لمنع تجاوزها.",
                ecc_ref="2-8-1",
            ))
        elif r.status_code == 200:
            findings.append(Finding(
                severity="high", domain="transport",
                title="الموقع متاح عبر HTTP بدون إعادة توجيه",
                description="يمكن للزائر الوصول إلى الموقع عبر HTTP العادي مما يعرّض الجلسة للاختطاف.",
                fix="أعد توجيه كل طلبات HTTP إلى HTTPS بكود 301 على مستوى nginx/Apache/Cloudflare، وفعّل HSTS.",
                evidence=f"HTTP status: {r.status_code}",
                ecc_ref="2-8-1",
                kind="http_no_redirect",
            ))
    except requests.exceptions.RequestException:
        pass


def _check_tls(host: str, findings: list[Finding]) -> dict[str, Any]:
    info: dict[str, Any] = {"reachable": False}
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((host, 443), timeout=TIMEOUT) as sock:
            with ctx.wrap_socket(sock, server_hostname=host) as ssock:
                cert = ssock.getpeercert() or {}
                version = ssock.version() or ""
                cipher = ssock.cipher()
                info.update({
                    "reachable": True,
                    "tls_version": version,
                    "cipher": cipher[0] if cipher else None,
                    "cert": cert,
                })
                not_after = cert.get("notAfter")
                if not_after:
                    try:
                        exp = datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
                        days_left = (exp - datetime.now(timezone.utc)).days
                        info["days_left"] = days_left
                        if days_left < 0:
                            findings.append(Finding(
                                severity="critical", domain="transport",
                                title="شهادة TLS منتهية الصلاحية",
                                description=f"شهادة الموقع منتهية منذ {-days_left} يوم.",
                                fix="جدّد الشهادة فوراً (Let's Encrypt مجاناً، أو مزوّد معتمد) وفعّل التجديد التلقائي.",
                                evidence=f"notAfter: {not_after}",
                                ecc_ref="2-8-1",
                                kind="tls_expired",
                            ))
                        elif days_left < 30:
                            findings.append(Finding(
                                severity="medium", domain="transport",
                                title="شهادة TLS قاربت على الانتهاء",
                                description=f"تنتهي الشهادة خلال {days_left} يوم.",
                                fix="جدّد الشهادة قبل انتهائها وفعّل التجديد التلقائي عبر certbot أو ACME.",
                                ecc_ref="2-8-1",
                            ))
                        else:
                            findings.append(Finding(
                                severity="ok", domain="transport",
                                title="شهادة TLS صالحة",
                                description=f"الشهادة صالحة لمدة {days_left} يوم.",
                                fix="استمر في مراقبة تواريخ انتهاء الشهادة وفعّل التجديد التلقائي.",
                                ecc_ref="2-8-1",
                            ))
                    except ValueError:
                        pass

                if version in ("TLSv1", "TLSv1.1", "SSLv3", "SSLv2"):
                    findings.append(Finding(
                        severity="high", domain="transport",
                        title=f"إصدار TLS قديم ({version})",
                        description="الإصدار المُستخدم ضعيف وقابل لهجمات معروفة (POODLE / BEAST).",
                        fix="فعّل TLS 1.2/1.3 فقط على الخادم/الـ CDN وعطّل الإصدارات الأقدم.",
                        ecc_ref="2-8-1",
                        kind="tls_old_version",
                    ))
                elif version == "TLSv1.2":
                    findings.append(Finding(
                        severity="info", domain="transport",
                        title="TLS 1.2",
                        description="إصدار مقبول؛ TLS 1.3 مُفضّل لأداء وأمان أفضل.",
                        fix="فعّل TLS 1.3 إن دعمها الخادم/الـ CDN.",
                        ecc_ref="2-8-1",
                    ))
                else:
                    findings.append(Finding(
                        severity="ok", domain="transport",
                        title=f"إصدار TLS حديث ({version})",
                        description="الموقع يستخدم بروتوكولاً حديثاً.",
                        fix="استمر بمتابعة أفضل الممارسات وتعطيل الأنماط الضعيفة.",
                        ecc_ref="2-8-1",
                    ))
    except ssl.SSLError as exc:
        findings.append(Finding(
            severity="high", domain="transport",
            title="مشكلة في شهادة SSL/TLS",
            description=str(exc),
            fix="تأكّد من سلسلة الشهادات (intermediate)، تطابق اسم النطاق، وعدم انتهاء الشهادة.",
            ecc_ref="2-8-1",
        ))
    except (socket.timeout, socket.gaierror, ConnectionError, OSError) as exc:
        findings.append(Finding(
            severity="high", domain="transport",
            title="تعذّر الاتصال على المنفذ 443",
            description=str(exc),
            fix="تأكّد من تشغيل HTTPS على الخادم وفتح المنفذ 443.",
            ecc_ref="2-8-1",
        ))
    return info


def _check_security_headers(resp: requests.Response, findings: list[Finding]) -> None:
    h = {k.lower(): v for k, v in resp.headers.items()}

    # ----- HSTS -----
    hsts = h.get("strict-transport-security")
    if not hsts:
        findings.append(Finding(
            severity="high", domain="headers",
            title="HSTS غير مفعّلة",
            description="غياب Strict-Transport-Security يفتح الباب لهجمات إزالة TLS (SSL Stripping).",
            fix="أضِف الترويسة: Strict-Transport-Security: max-age=31536000; includeSubDomains; preload",
            ecc_ref="2-8-1",
            kind="no_hsts",
        ))
    else:
        m = re.search(r"max-age\s*=\s*(\d+)", hsts, re.I)
        max_age = int(m.group(1)) if m else 0
        if max_age < 15768000:  # < 6 أشهر
            findings.append(Finding(
                severity="medium", domain="headers",
                title="HSTS بقيمة max-age قصيرة",
                description=f"max-age الحالية {max_age} ثانية، أقل من 6 أشهر.",
                fix="ارفع القيمة إلى 31536000 (سنة) وأضِف includeSubDomains.",
                evidence=hsts,
                ecc_ref="2-8-1",
            ))
        else:
            findings.append(Finding(
                severity="ok", domain="headers",
                title="HSTS مفعّلة",
                description="ترويسة HSTS موجودة بقيمة مناسبة.",
                fix="فكّر بإضافة preload وسجّل النطاق في hstspreload.org.",
                evidence=hsts,
                ecc_ref="2-8-1",
            ))

    # ----- CSP -----
    csp = h.get("content-security-policy")
    if not csp:
        findings.append(Finding(
            severity="high", domain="headers",
            title="Content-Security-Policy غير مُعرَّفة",
            description="غياب CSP يسهّل هجمات XSS وحقن السكربتات الخارجية.",
            fix=("ابدأ بسياسة صارمة:\n"
                 "default-src 'self'; script-src 'self'; object-src 'none'; "
                 "frame-ancestors 'none'; base-uri 'self'\n"
                 "ثم وسّعها وفق احتياج الموقع."),
            ecc_ref="2-3-1",
            kind="no_csp",
        ))
    else:
        if "unsafe-inline" in csp.lower() or "unsafe-eval" in csp.lower():
            findings.append(Finding(
                severity="medium", domain="headers",
                title="CSP فضفاضة (تسمح unsafe-inline/eval)",
                description="السماح بـ inline JS/CSS أو eval يضعف الحماية من XSS.",
                fix="استبدل unsafe-inline بـ nonces أو hashes، وأزل unsafe-eval.",
                evidence=csp[:200],
                ecc_ref="2-3-1",
                kind="weak_csp",
            ))
        else:
            findings.append(Finding(
                severity="ok", domain="headers",
                title="CSP مُعرَّفة",
                description="سياسة محتوى مفعّلة.",
                fix="راجعها دورياً وفعّل report-to لمتابعة الانتهاكات.",
                ecc_ref="2-3-1",
            ))

    # ----- Clickjacking -----
    xfo = h.get("x-frame-options", "")
    has_frame_ancestors = "frame-ancestors" in (csp or "").lower()
    if not xfo and not has_frame_ancestors:
        findings.append(Finding(
            severity="medium", domain="headers",
            title="حماية Clickjacking غير مفعّلة",
            description="غياب X-Frame-Options و frame-ancestors يسمح بإطار الموقع داخل صفحات أخرى (Clickjacking).",
            fix="أضِف: X-Frame-Options: DENY أو CSP: frame-ancestors 'none'",
            ecc_ref="2-3-1",
            kind="no_clickjacking",
        ))
    else:
        findings.append(Finding(
            severity="ok", domain="headers",
            title="حماية Clickjacking مفعّلة",
            description=f"موجود: {xfo or 'CSP frame-ancestors'}",
            fix="استخدم DENY ما لم يكن لديك سبب لاستعمال SAMEORIGIN.",
            ecc_ref="2-3-1",
        ))

    # ----- X-Content-Type-Options -----
    xcto = (h.get("x-content-type-options") or "").lower()
    if xcto != "nosniff":
        findings.append(Finding(
            severity="low", domain="headers",
            title="X-Content-Type-Options غير مضبوطة",
            description="غياب nosniff قد يسمح للمتصفحات بتخمين نوع المحتوى وتنفيذه.",
            fix="أضِف: X-Content-Type-Options: nosniff",
            ecc_ref="2-3-1",
            kind="no_xcto",
        ))
    else:
        findings.append(Finding(
            severity="ok", domain="headers",
            title="X-Content-Type-Options: nosniff",
            description="ترويسة صحيحة.",
            fix="استمر في تفعيلها على جميع الاستجابات.",
            ecc_ref="2-3-1",
        ))

    # ----- Referrer-Policy -----
    rp = h.get("referrer-policy", "")
    if not rp:
        findings.append(Finding(
            severity="low", domain="headers",
            title="Referrer-Policy غير مُعرَّفة",
            description="قد يُكشف URL كامل (مع معاملات حسّاسة) عند الانتقال لمواقع خارجية.",
            fix="أضِف: Referrer-Policy: strict-origin-when-cross-origin",
            ecc_ref="2-3-1",
            kind="no_referrer_policy",
        ))
    else:
        findings.append(Finding(
            severity="ok", domain="headers",
            title="Referrer-Policy مضبوطة",
            description=f"القيمة الحالية: {rp}",
            fix="القيمة المفضّلة: strict-origin-when-cross-origin أو no-referrer.",
            ecc_ref="2-3-1",
        ))

    # ----- Permissions-Policy -----
    pp = h.get("permissions-policy") or h.get("feature-policy")
    if not pp:
        findings.append(Finding(
            severity="low", domain="headers",
            title="Permissions-Policy غير مُعرَّفة",
            description="غياب الترويسة يترك صلاحيات الجهاز (camera/microphone/geolocation) دون تقييد صريح.",
            fix="أضِف: Permissions-Policy: camera=(), microphone=(), geolocation=()",
            ecc_ref="2-3-1",
        ))


def _check_cookies(resp: requests.Response, findings: list[Finding]) -> None:
    cookies = _set_cookie_lines(resp)
    if not cookies:
        findings.append(Finding(
            severity="info", domain="cookies",
            title="لا توجد كوكيز في الاستجابة",
            description="لم تُلاحَظ ترويسات Set-Cookie في الاستجابة الرئيسية.",
            fix="إن استخدمت كوكيز جلسة لاحقاً، تأكّد من Secure و HttpOnly و SameSite.",
            ecc_ref="2-3-1",
        ))
        return

    issues_found = False
    for c in cookies:
        name = c.split("=", 1)[0].strip()
        lc = c.lower()
        miss: list[str] = []
        if "secure" not in lc:
            miss.append("Secure")
        if "httponly" not in lc:
            miss.append("HttpOnly")
        if "samesite" not in lc:
            miss.append("SameSite")
        if miss:
            issues_found = True
            findings.append(Finding(
                severity="medium", domain="cookies",
                title=f"كوكي «{name}» مفقود فيه: {' / '.join(miss)}",
                description="غياب هذه الأعلام يعرّض الكوكي للسرقة عبر XSS أو التسرّب على الشبكة.",
                fix=("أضِف الأعلام المفقودة. مثال:\n"
                     f"Set-Cookie: {name}=...; Secure; HttpOnly; SameSite=Lax"),
                evidence=c[:160],
                ecc_ref="2-3-1",
                kind="cookie_missing_flags",
            ))
    if not issues_found:
        findings.append(Finding(
            severity="ok", domain="cookies",
            title="جميع الكوكيز محميّة",
            description="جميع الكوكيز تحمل Secure و HttpOnly و SameSite.",
            fix="فكّر باستخدام __Host- prefix للكوكيز الحرجة لمزيد من التشدّد.",
            ecc_ref="2-3-1",
        ))


def _check_info_disclosure(resp: requests.Response, findings: list[Finding]) -> None:
    server = resp.headers.get("Server", "")
    powered = resp.headers.get("X-Powered-By", "")
    asp_net = resp.headers.get("X-AspNet-Version", "") or resp.headers.get("X-AspNetMvc-Version", "")

    if server and re.search(r"\d", server):
        findings.append(Finding(
            severity="low", domain="info",
            title="ترويسة Server تكشف الإصدار",
            description=f"تم الكشف: {server}",
            fix=("عطّل عرض الإصدار:\n"
                 "- nginx: server_tokens off;\n"
                 "- Apache: ServerTokens Prod / ServerSignature Off"),
            evidence=server,
            ecc_ref="2-3-1",
            kind="server_version_disclosure",
        ))
    if powered:
        findings.append(Finding(
            severity="low", domain="info",
            title="ترويسة X-Powered-By تكشف التقنية",
            description=f"تم الكشف: {powered}",
            fix=("احذف الترويسة على مستوى التطبيق/الـ proxy.\n"
                 "في Express: app.disable('x-powered-by')\n"
                 "في PHP: expose_php = Off"),
            evidence=powered,
            ecc_ref="2-3-1",
            kind="powered_by_disclosure",
        ))
    if asp_net:
        findings.append(Finding(
            severity="low", domain="info",
            title="X-AspNet-Version تكشف إصدار الإطار",
            description=f"تم الكشف: {asp_net}",
            fix="عطّل في web.config: <httpRuntime enableVersionHeader='false' />",
            evidence=asp_net,
            ecc_ref="2-3-1",
        ))


# قائمة مسارات حسّاسة شائعة (passive — GET فقط، لا brute force).
SENSITIVE_PATHS: list[tuple[str, str, str]] = [
    ("/.env",            "ملف متغيرات بيئة قد يحتوي مفاتيح API وكلمات مرور.", "critical"),
    ("/.git/config",     "مستودع Git مكشوف؛ يُمكن استنساخ كامل كود التطبيق.",   "critical"),
    ("/.git/HEAD",       "مؤشّر Git مكشوف.",                                    "high"),
    ("/backup.zip",      "ملف نسخة احتياطية مكشوف.",                            "critical"),
    ("/backup.tar.gz",   "ملف نسخة احتياطية مكشوف.",                            "critical"),
    ("/db.sql",          "مفرّغة قاعدة بيانات.",                                "critical"),
    ("/database.sql",    "مفرّغة قاعدة بيانات.",                                "critical"),
    ("/wp-config.php.bak", "نسخة احتياطية لإعدادات WordPress.",                "critical"),
    ("/.htaccess",       "ملف إعدادات Apache مكشوف.",                          "high"),
    ("/.DS_Store",       "ملف macOS قد يكشف هيكل المجلدات.",                   "low"),
    ("/server-status",   "صفحة Apache server-status.",                         "medium"),
    ("/server-info",     "صفحة Apache server-info.",                           "medium"),
    ("/phpinfo.php",     "صفحة phpinfo قد تكشف بيانات حسّاسة.",                "high"),
    ("/.svn/entries",    "مستودع SVN مكشوف.",                                  "high"),
]


def _looks_like_real_file(path: str, resp: requests.Response) -> bool:
    """تجنّب الإيجابيات الكاذبة من صفحات soft-404 التي ترجع 200 + HTML."""
    body = (resp.text or "")[:4000].lower()
    ct = (resp.headers.get("Content-Type") or "").lower()
    ext = path.rsplit(".", 1)[-1].lower() if "." in path else ""

    if ext in ("env", "sql", "bak", "zip", "tar", "gz"):
        return "text/html" not in ct
    if path.endswith(".git/config"):
        return "[core]" in body or "repositoryformatversion" in body
    if path.endswith(".git/HEAD"):
        return "ref:" in body or len(body.strip()) < 200
    if path.endswith(".htaccess"):
        return "<html" not in body and "doctype" not in body
    if path.endswith(".DS_Store"):
        return "text/html" not in ct
    if path == "/server-status":
        return "apache server status" in body or "server uptime" in body
    if path == "/server-info":
        return "apache server information" in body
    if path == "/phpinfo.php":
        return "phpinfo()" in body or "php version" in body
    if path == "/.svn/entries":
        return "<html" not in body
    return True


def _exposure_kind(path: str) -> str:
    p = path.lower()
    if ".env" in p:                return "exposed_env"
    if ".git" in p:                return "exposed_git"
    if any(p.endswith(s) for s in (".sql",)): return "exposed_backup"
    if any(p.endswith(s) for s in (".zip", ".tar.gz", ".bak")): return "exposed_backup"
    if "phpinfo" in p:             return "exposed_phpinfo"
    return "exposed_env"  # generic fallback


def _check_exposed_paths(base_url: str, findings: list[Finding]) -> None:
    parsed = urlparse(base_url)
    origin = f"{parsed.scheme}://{parsed.netloc}"
    exposed = 0
    for path, desc, severity in SENSITIVE_PATHS:
        try:
            r = requests.get(
                origin + path,
                timeout=PROBE_TIMEOUT,
                allow_redirects=False,
                headers={"User-Agent": USER_AGENT},
            )
            if r.status_code == 200 and r.content and _looks_like_real_file(path, r):
                exposed += 1
                findings.append(Finding(
                    severity=severity, domain="exposure",
                    title=f"ملف حسّاس مكشوف: {path}",
                    description=desc,
                    fix=("احذف الملف من بيئة الإنتاج، أو امنع الوصول إليه:\n"
                         "- nginx: location ~ /\\.(env|git|svn|htaccess) { deny all; return 404; }\n"
                         "- Apache: <FilesMatch \"^\\.(env|git|svn|htaccess)\"> Require all denied </FilesMatch>"),
                    evidence=f"GET {path} → {r.status_code} ({len(r.content)} bytes)",
                    ecc_ref="2-7-1",
                    kind=_exposure_kind(path),
                ))
        except requests.exceptions.RequestException:
            continue

    if exposed == 0:
        findings.append(Finding(
            severity="ok", domain="exposure",
            title="لا ملفات حسّاسة مكشوفة",
            description="لم يُعثر على أيٍّ من المسارات الشائعة الحسّاسة (.env, .git, backups, …).",
            fix="حافظ على هذه الإعدادات واحجب أي ملفات تنتهي بـ .env / .git / .bak / .sql.",
            ecc_ref="2-7-1",
        ))


def _check_dns(host: str, findings: list[Finding]) -> None:
    try:
        import dns.resolver  # type: ignore
    except ImportError:
        findings.append(Finding(
            severity="info", domain="dns",
            title="فحص DNS غير متاح",
            description="مكتبة dnspython غير مثبتة فلم نتمكن من فحص SPF/DMARC.",
            fix="ثبّت الحزمة: pip install dnspython ثم أعد تشغيل التطبيق.",
        ))
        return

    parts = host.split(".")
    root = ".".join(parts[-2:]) if len(parts) >= 2 else host

    # SPF
    try:
        ans = dns.resolver.resolve(root, "TXT", lifetime=6)
        spf = next(
            (r.to_text().strip('"') for r in ans if "v=spf1" in r.to_text().lower()),
            None,
        )
        if spf:
            ends_with_strict = re.search(r"[\-~]all\s*$", spf.strip())
            if ends_with_strict:
                findings.append(Finding(
                    severity="ok", domain="dns",
                    title="سجل SPF موجود",
                    description=spf[:180],
                    fix="استمر في تحديثه عند تغيير مزوّدي البريد.",
                    evidence=spf,
                    ecc_ref="2-15-1",
                ))
            else:
                findings.append(Finding(
                    severity="medium", domain="dns",
                    title="SPF بقاعدة افتراضية متساهلة",
                    description="السجل لا ينتهي بـ -all أو ~all مما يسمح للسيرفرات غير المرخّصة بإرسال البريد باسم النطاق.",
                    fix="أنه السجل بـ -all (رفض) أو ~all (وضع تجريبي).",
                    evidence=spf,
                    ecc_ref="2-15-1",
                    kind="no_spf",
                ))
        else:
            findings.append(Finding(
                severity="medium", domain="dns",
                title="لا يوجد سجل SPF",
                description="غياب SPF يسهّل انتحال البريد من نطاقك (Email Spoofing).",
                fix="أضِف TXT للنطاق: v=spf1 include:_spf.google.com -all (أو وفقاً لمزوّد البريد).",
                ecc_ref="2-15-1",
                kind="no_spf",
            ))
    except Exception as e:
        findings.append(Finding(
            severity="info", domain="dns",
            title="تعذّر استعلام TXT",
            description=str(e),
            fix="تأكّد من إعدادات DNS لنطاقك.",
        ))

    # DMARC
    try:
        ans = dns.resolver.resolve("_dmarc." + root, "TXT", lifetime=6)
        dmarc = next(
            (r.to_text().strip('"') for r in ans if "v=dmarc1" in r.to_text().lower()),
            None,
        )
        if dmarc:
            policy = re.search(r"p\s*=\s*(\w+)", dmarc.lower())
            p_val = policy.group(1) if policy else "none"
            sev = "ok" if p_val in ("reject", "quarantine") else "medium"
            findings.append(Finding(
                severity=sev, domain="dns",
                title=f"DMARC: p={p_val}",
                description=dmarc[:180],
                fix=("ارفع السياسة إلى quarantine ثم reject بعد المراقبة."
                     if p_val == "none" else "حافظ على السياسة وراقب التقارير."),
                evidence=dmarc,
                ecc_ref="2-15-1",
            ))
        else:
            findings.append(Finding(
                severity="medium", domain="dns",
                title="لا يوجد سجل DMARC",
                description="غياب DMARC يسمح بهجمات phishing من نطاقك دون رصد.",
                fix=("أضِف TXT للسجل _dmarc.<domain>:\n"
                     "v=DMARC1; p=quarantine; rua=mailto:dmarc@yourdomain.sa"),
                ecc_ref="2-15-1",
                kind="no_dmarc",
            ))
    except Exception:
        findings.append(Finding(
            severity="medium", domain="dns",
            title="لا يوجد سجل DMARC",
            description="لم يُعثر على _dmarc.<domain>.",
            fix=("أضِف TXT للسجل _dmarc.<domain>:\n"
                 "v=DMARC1; p=quarantine; rua=mailto:dmarc@yourdomain.sa"),
            ecc_ref="2-15-1",
            kind="no_dmarc",
        ))


def _check_mixed_content(resp: requests.Response, findings: list[Finding]) -> None:
    if not resp.url.lower().startswith("https://"):
        return
    body = resp.text or ""
    matches = re.findall(r'(?:src|href)\s*=\s*["\'](http://[^"\']+)', body, re.I)
    if matches:
        unique = list(dict.fromkeys(matches))[:5]
        findings.append(Finding(
            severity="medium", domain="content",
            title=f"محتوى مختلط (Mixed Content) — {len(matches)} رابط HTTP",
            description="صفحة HTTPS تحمّل موارد عبر HTTP مما يكسر ضمانات التشفير.",
            fix=("حوّل الروابط إلى HTTPS، وفعّل CSP: upgrade-insecure-requests.\n"
                 "للمراجعة افتح المتصفح > Developer Tools > Console > Mixed Content warnings."),
            evidence="\n".join(unique),
            ecc_ref="2-8-1",
            kind="mixed_content",
        ))
    else:
        findings.append(Finding(
            severity="ok", domain="content",
            title="لا يوجد محتوى مختلط",
            description="جميع الموارد تحمّل عبر HTTPS.",
            fix="حافظ على هذه السياسة وفعّل upgrade-insecure-requests احتياطياً.",
            ecc_ref="2-8-1",
        ))


# =========================================================================
#  Score
# =========================================================================
SEV_WEIGHT: dict[str, int] = {
    "critical": 25, "high": 12, "medium": 5, "low": 2, "info": 0, "ok": 0,
}


def _calc_score(findings: Iterable[Finding]) -> dict[str, Any]:
    counts = {s: 0 for s in SEVERITIES}
    penalty = 0
    for f in findings:
        counts[f.severity] = counts.get(f.severity, 0) + 1
        penalty += SEV_WEIGHT.get(f.severity, 0)
    score = max(0, 100 - penalty)
    grade = (
        "A" if score >= 90 else
        "B" if score >= 75 else
        "C" if score >= 60 else
        "D" if score >= 40 else
        "F"
    )
    return {"score": score, "grade": grade, "counts": counts, "total": sum(counts.values())}


# =========================================================================
#  Public entry point
# =========================================================================
def scan(url: str) -> dict[str, Any]:
    """يفحص URL ويرجع dict جاهزاً للعرض في الواجهة."""
    canonical, host = _normalize_url(url)
    findings: list[Finding] = []
    started = datetime.now().isoformat(timespec="seconds")

    _check_http_to_https(canonical, findings)
    tls_info = _check_tls(host, findings)

    try:
        resp = _fetch(canonical)
        _check_security_headers(resp, findings)
        _check_cookies(resp, findings)
        _check_info_disclosure(resp, findings)
        _check_mixed_content(resp, findings)
    except requests.exceptions.SSLError as exc:
        findings.append(Finding(
            severity="critical", domain="transport",
            title="فشل التحقق من شهادة SSL",
            description=str(exc),
            fix="تأكّد من سلسلة الشهادات وتطابق اسم النطاق وعدم انتهاء الشهادة.",
            ecc_ref="2-8-1",
        ))
    except requests.exceptions.RequestException as exc:
        findings.append(Finding(
            severity="high", domain="transport",
            title="تعذّر الاتصال بالموقع",
            description=str(exc),
            fix="تحقّق من URL، الاتصال بالشبكة، وإعدادات الجدار الناري/CDN.",
        ))

    _check_exposed_paths(canonical, findings)
    _check_dns(host, findings)

    score = _calc_score(findings)

    # دمج معلومات الاستغلال (impact / attack steps / code) من القاموس.
    enriched: list[dict[str, Any]] = []
    for f in findings:
        d = asdict(f)
        if f.severity not in ("ok", "info"):
            info = exploits.get(f.kind)
            if info:
                d["impact"] = info.get("impact", "")
                d["attack_summary"] = info.get("attack_summary", "")
                d["attack_steps"] = list(info.get("attack_steps", []))
                d["attack_code"] = list(info.get("attack_code", []))
                d.setdefault("references", [])
                for ref in info.get("references", []):
                    if ref not in d["references"]:
                        d["references"].append(ref)
        enriched.append(d)

    return {
        "url": canonical,
        "host": host,
        "started_at": started,
        "tls": {k: v for k, v in tls_info.items() if k != "cert"},
        "findings": enriched,
        "score": score,
    }


def group_by_domain(findings: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """يرتّب نتائج الفحص حسب الفئة (للعرض في بطاقات domain-card)."""
    out: dict[str, list[dict[str, Any]]] = {k: [] for k in DOMAIN_ORDER}
    for f in findings:
        out.setdefault(f.get("domain", "info"), []).append(f)
    return out
