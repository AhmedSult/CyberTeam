#!/usr/bin/env python3
"""يضيف domain_ar و evidence_guidance_ar لكل ضابط في كتالوج NCA (JSON)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "app" / "data" / "ecc2_2024_catalog.json"

# أسماء مجالات قصيرة للواجهة (من أعمدة category_ar في الكتالوج)
SHORT_DOMAIN = {
    "حوكمة الأمن السيبراني": "حوكمة",
    "تعزيز الأمن السيبراني": "تعزيز",
    "صمود الأمن السيبراني": "صمود",
    "الأطراف الخارجية والحوسبة السحابية": "خارجية / سحابة",
}

EVIDENCE_BLOCK = (
    "إرشادات الأدلة والإثبات: راجع «الدليل الإرشادي لتطبيق الضوابط الأساسية للأمن السيبراني» "
    "(GECC-1:2023) في الفصل الخاص بالمعيار الفرعي؛ تتضمن الوثيقة أمثلة وتوجيهات لأنواع الأدلة المناسبة "
    "(سياسات، إجراءات، سجلات، لقطات إعدادات، تقارير فحص أو مراجعة، إلخ) بحسب طبيعة الضابط. "
    "يُكمّل ذلك وثيقة الضوابط ECC-2-2024 للنصوص المعيارية."
)


def main() -> None:
    payload = json.loads(CATALOG.read_text(encoding="utf-8"))
    payload["version"] = "ECC-2-2024+GECC-1-2023-meta"
    payload["implementation_guide_pdf"] = "backend/data/gecc_implementation_guide_ar.pdf"
    payload["notes_ar"] = (
        "البنود المفصّلة مستخرجة من وثيقة الضوابط ECC-2-2024؛ المجال وإرشاد الأدلة مُنسّقة مع "
        "«الدليل الإرشادي لتطبيق الضوابط» (GECC) كمرجع تنفيذي."
    )
    rows: list[dict] = payload.get("controls") or []
    for r in rows:
        cat = (r.get("category_ar") or "").strip()
        r["domain_ar"] = SHORT_DOMAIN.get(cat, cat or None)
        r["evidence_guidance_ar"] = EVIDENCE_BLOCK
    CATALOG.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Updated {len(rows)} controls in {CATALOG}")


if __name__ == "__main__":
    main()
