#!/usr/bin/env python3
"""Extract ECC-2-2024 control clauses from the official PDF into JSON (Arabic text as extracted)."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import fitz

AR_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")

# Sub-domain numbering in the PDF uses two-digit forms for items 10–15 (e.g. ٠١ → 10).
SUB_REF_FIX_DOMAIN1 = {"01": "10"}
SUB_REF_FIX_DOMAIN2 = {
    "01": "10",
    "11": "11",
    "21": "12",
    "31": "13",
    "41": "14",
    "51": "15",
}

DOMAIN_CATEGORY_AR = {
    "1": "حوكمة الأمن السيبراني",
    "2": "تعزيز الأمن السيبراني",
    "3": "صمود الأمن السيبراني",
    "4": "الأطراف الخارجية والحوسبة السحابية",
}

STANDARD_TITLES: dict[str, dict[str, str]] = {
    "1-1": {"ar": "استراتيجية الأمن السيبراني", "en": "Cybersecurity Strategy"},
    "1-2": {"ar": "إدارة الأمن السيبراني", "en": "Cybersecurity Management"},
    "1-3": {"ar": "سياسات وإجراءات الأمن السيبراني", "en": "Cybersecurity Policies and Procedures"},
    "1-4": {"ar": "أدوار ومسؤوليات الأمن السيبراني", "en": "Cybersecurity Roles and Responsibilities"},
    "1-5": {"ar": "إدارة مخاطر الأمن السيبراني", "en": "Cybersecurity Risk Management"},
    "1-6": {"ar": "الأمن السيبراني ضمن إدارة المشاريع المعلوماتية والتقنية", "en": "Cybersecurity in IT Projects"},
    "1-7": {"ar": "الالتزام بالتشريعات والمعايير", "en": "Cybersecurity Regulatory Compliance"},
    "1-8": {"ar": "المراجعة والتدقيق الدوري للأمن السيبراني", "en": "Periodical Assessment and Audit"},
    "1-9": {"ar": "الأمن السيبراني المتعلق بالموارد البشرية", "en": "Cybersecurity in Human Resources"},
    "1-10": {"ar": "برنامج التوعية والتدريب بالأمن السيبراني", "en": "Awareness and Training Program"},
    "2-1": {"ar": "إدارة الأصول", "en": "Asset Management"},
    "2-2": {"ar": "إدارة هويات الدخول والصلاحيات", "en": "Identity and Access Management"},
    "2-3": {"ar": "حماية الأنظمة وأجهزة معالجة المعلومات", "en": "System and Processing Facilities Protection"},
    "2-4": {"ar": "حماية البريد الإلكتروني", "en": "Email Protection"},
    "2-5": {"ar": "إدارة أمن الشبكات", "en": "Networks Security Management"},
    "2-6": {"ar": "أمن الأجهزة المحمولة", "en": "Mobile Devices Security"},
    "2-7": {"ar": "حماية البيانات والمعلومات", "en": "Data and Information Protection"},
    "2-8": {"ar": "التشفير", "en": "Cryptography"},
    "2-9": {"ar": "إدارة النسخ الاحتياطية", "en": "Backup and Recovery Management"},
    "2-10": {"ar": "إدارة الثغرات", "en": "Vulnerabilities Management"},
    "2-11": {"ar": "اختبار الاختراق", "en": "Penetration Testing"},
    "2-12": {"ar": "إدارة سجلات الأحداث ومراقبة الأمن السيبراني", "en": "Event Logs and Monitoring"},
    "2-13": {"ar": "إدارة حوادث وتهديدات الأمن السيبراني", "en": "Incident and Threat Management"},
    "2-14": {"ar": "الأمن المادي", "en": "Physical Security"},
    "2-15": {"ar": "حماية تطبيقات الويب", "en": "Web Application Security"},
    "3-1": {
        "ar": "جوانب صمود الأمن السيبراني في إدارة استمرارية الأعمال",
        "en": "Resilience aspects of BCM",
    },
    "4-1": {"ar": "الأمن السيبراني المتعلق بالأطراف الخارجية", "en": "Third-Party Cybersecurity"},
    "4-2": {"ar": "الأمن السيبراني للحوسبة السحابية والاستضافة", "en": "Cloud and Hosting Cybersecurity"},
}


def normalize_ref_parts(raw_ref: str) -> list[str]:
    parts = raw_ref.split("-")
    if len(parts) < 2:
        return parts
    dom, sub = parts[0], parts[1]
    if dom == "1" and sub in SUB_REF_FIX_DOMAIN1:
        parts[1] = SUB_REF_FIX_DOMAIN1[sub]
    elif dom == "2" and sub in SUB_REF_FIX_DOMAIN2:
        parts[1] = SUB_REF_FIX_DOMAIN2[sub]
    return parts


def to_standard_key(parts: list[str]) -> str | None:
    if len(parts) < 2:
        return None
    return f"{parts[0]}-{parts[1]}"


def to_ecc_ref(parts: list[str]) -> str:
    return "ECC-" + "-".join(parts)


# نصوص مستخرجة من PDF (أشكال عرضية) — لا تطابق «الهدف» المعيارية دائماً
_PDF_GOAL = "اﻟﻬﺪف"
_PDF_CONTROLS = "اﻟﻀﻮاﺑﻂ"


def extract_objective(chunk: str) -> str | None:
    """الهدف في PDF: فقرة بعد سطر المرجع ثنائي المستوى (مثل 1-1) وقبل ترويسة «الهدف»."""
    if _PDF_GOAL not in chunk:
        return None
    before = chunk.split(_PDF_GOAL, 1)[0]
    matches = list(re.finditer(r"(?<![0-9])(\d+-\d+)(?![0-9-])\s+", before))
    if not matches:
        return None
    start = matches[-1].end()
    obj = before[start:].strip()
    obj = re.sub(r"\s+", " ", obj).strip()
    if len(obj) < 25:
        return None
    return obj


def extract_control_clause(chunk: str, raw_ref: str) -> str:
    if _PDF_GOAL in chunk:
        tail = chunk.split(_PDF_GOAL, 1)[-1]
        if _PDF_CONTROLS in tail:
            body = tail.split(_PDF_CONTROLS, 1)[-1]
        else:
            body = tail
    else:
        lp = chunk.rfind(_PDF_CONTROLS)
        body = chunk[lp + len(_PDF_CONTROLS) :] if lp != -1 else chunk
    if raw_ref in body:
        body = body.rsplit(raw_ref, 1)[0]
    body = body.strip()
    body = re.sub(r"[.\u2026…]+\s*$", "", body)
    body = re.sub(r"\s+", " ", body)
    return body.strip()


def pdf_to_blob(path: Path) -> str:
    doc = fitz.open(path)
    try:
        parts = [doc[i].get_text("text") for i in range(doc.page_count)]
    finally:
        doc.close()
    return "".join(parts).translate(AR_DIGITS)


def parse_controls(blob: str) -> list[dict]:
    pat = re.compile(r"(?<![0-9])(\d{1,2}(?:-\d{1,2}){2,4})(?![0-9])")
    matches: list[tuple[int, int, str]] = []
    for m in pat.finditer(blob):
        raw = m.group(1)
        parts = raw.split("-")
        if len(parts[0]) > 1:
            continue
        dom = int(parts[0])
        if dom < 1 or dom > 4:
            continue
        if any(int(p) > 60 for p in parts):
            continue
        matches.append((m.start(), m.end(), raw))

    seen: set[str] = set()
    ordered: list[tuple[int, int, str]] = []
    for s, e, raw in matches:
        if raw in seen:
            continue
        seen.add(raw)
        ordered.append((s, e, raw))

    std_objective: dict[str, str] = {}
    out: list[dict] = []
    prev_end = 0

    detail_marker = "ﺗﻔﺎﺻﻴﻞ اﻟﻀﻮاﺑﻂ اﻷﺳﺎﺳﻴﺔ ﻟﻸﻣﻦ اﻟﺴﻴﺒﺮاﻧﻲ"
    for i, (s, e, raw_ref) in enumerate(ordered):
        start = prev_end
        if i == 0:
            ds = blob.rfind(detail_marker, 0, s)
            start = ds if ds != -1 else max(0, s - 2200)
        chunk = blob[start:s]
        prev_end = e
        norm_parts = normalize_ref_parts(raw_ref)
        sk = to_standard_key(norm_parts)
        if not sk:
            continue
        if sk not in STANDARD_TITLES:
            continue

        obj = extract_objective(chunk)
        if obj:
            std_objective[sk] = obj
        objective = std_objective.get(sk)

        clause = extract_control_clause(chunk, raw_ref)
        if len(clause) < 15:
            continue

        st = STANDARD_TITLES[sk]
        ecc_ref = to_ecc_ref(norm_parts)
        dom = norm_parts[0]
        category = DOMAIN_CATEGORY_AR.get(dom, "")

        out.append(
            {
                "ref": ecc_ref,
                "standard_ref": sk,
                "standard_title_ar": st["ar"],
                "standard_title_en": st["en"],
                "objective_ar": objective,
                "category_ar": category,
                "title_ar": f"{st['ar']} — {ecc_ref}",
                "title_en": f"{st['en']} — {ecc_ref}",
                "control_text_ar": clause,
            }
        )

    return out


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    default_pdf = root / "data" / "ecc_source.pdf"
    pdf = Path(sys.argv[1]) if len(sys.argv) > 1 else default_pdf
    if not pdf.is_file():
        print(f"Missing PDF: {pdf}", file=sys.stderr)
        sys.exit(1)

    blob = pdf_to_blob(pdf)
    rows = parse_controls(blob)
    out_path = root / "app" / "data" / "ecc2_2024_catalog.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"version": "ECC-2-2024", "source_pdf": pdf.name, "control_count": len(rows), "controls": rows}
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(rows)} controls to {out_path}")


if __name__ == "__main__":
    main()
