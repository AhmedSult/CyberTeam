"""AI layer: uses OpenAI when configured, else deterministic rules (متوافق مع المقترح)."""

import asyncio
import io

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import settings
from app.models import ComplianceRecord, ComplianceStatusEnum, Control, Department, Framework
from app.services import ecc_kb

# سياق ثابت للنموذج: المستخدم يتحدث عن امتثال وضوابط سيبرانية بتركيز على إطار الهيئة الوطنية للأمن السيبراني (NCA) في المملكة.
# لا يُعتبر هذا توجيهاً رسمياً من الهيئة؛ المنصة للعرض/الداخلية — المرجع الرسمي nca.gov.sa

# كيف يعمل المساعد: GPT (تفسير وإرشاد) + منطق المنصة (أرقام ومدخلات من قاعدة البيانات) + مقتطفات ECC المفهرسة
PLATFORM_GPT_LOGIC_AR = (
    "【أسلوب العمل: GPT + منطق المنصة】 أنت تجمع بين نموذج لغوي (GPT) لشرح المعايير وتوجيه المستخدم، "
    "وبين **بيانات منطقية مُدخَلة في النظام**: سجلات الامتثال، الفلترة حسب الإدارة والإطار (NCA/NIST/ISO…)، وتحليل الفجوات من اللوحة — "
    "تظهر لك في نفس الرسالة كأقسام منفصلة. **اعتمد الأرقام والحالات الواردة فيها كحقيقة حالة المستخدم في المنصة** ولا تخترع أرقاماً أو نسباً لم تُذكر. "
    "المنصة تدعم **استيراد الضوابط من ملفات جدولية** (مثل Excel) و**رفع أدلة** مرتبطة بالسجلات؛ عند السؤال عن «الملفات» أو «الوضع حسب المدخلات» "
    "فاشرح أن الإجابة عن **حالة الامتثال** تعتمد على ما تم تسجيله واستيراده في النظام، وأنك تساعد في **تطبيق المعايير** وشرح المتطلبات. "
    "للمعيار الوطني للضوابط الأساسية يُرفق مع السؤال — عند التوفر — **مقتطفات مفهرسة من وثيقة ECC-2-2024** (PDF الرسمي على cdn.nca.gov.sa)؛ "
    "استخدمها لشرح متطلبات ECC والربط مع وضع المستخدم عندما ينطبق ذلك."
)

# رفض مواضيع خارج نطاق المنصة (لا يستبدل مراجعة أمنية أو قراراً رسمياً)
AI_SCOPE_GUARDRAILS_AR = (
    "【حدود المجال والرفض】 ناقش فقط: الامتثال، الضوابط والأمن السيبراني، الأدلة، بيانات المنصة، "
    "وسياسات وإجراءات أمن المعلومات **ضمن سياق الامتثال**، وإرشادات تطبيقية مرتبطة بذلك. "
    "لا تخض في: **الحديث أو الآراء السياسية**، أو **الأمور الشخصية** (صحة، علاقات، حياة خاصة)، "
    "أو مواضيع ترفيهية أو أي طلب لا صلة له بهذه المنصة. "
    "عند سؤال أو طلب من هذا النوع: **اعتذر بجملة قصيرة مهنية**، و**لا تُقدّم** محتوى ذلك الموضوع، "
    "و**وجّه المستخدم بلطف** لطرح سؤال يتعلق بالضوابط أو الامتثال أو استخدام المشروع."
)

NCA_FOCUS_SYSTEM_AR = (
    "أنت مساعد امتثال وضوابط سيبرانية داخل تطبيق لإدارة الامتثال. "
    "افترض دائماً أن أسئلة المستخدم تخص **الضوابط والممارسات والجاهزية السيبرانية في المملكة العربية السعودية** "
    "وبما يتماشى مع **إطار وإرشادات الهيئة الوطنية للأمن السيبراني (NCA)** كمرجع وطني أساسي، "
    "إلى جانب أطر أخرى قد تظهر في بيانات المنظمة (مثل NIST أو ISO 27001) كدعم أو مقارنة عند الحاجة. "
    f"{PLATFORM_GPT_LOGIC_AR} "
    "أجب بالعربية الفصحى المبسطة، بإيجاز وعملياً. "
    "إن وُجد سياق ضابط محدد في الرسالة فاستخدمه. "
    "لا تدّعِ أنك تمثّل الهيئة أو تصدر لها قرارات؛ إن طُلبت وثيقة رسمية فأحِل المستخدم إلى الموقع الرسمي nca.gov.sa. "
    "لا تخترع أرقام ضوابط أو نصوص رسمية؛ إن لم تكن متأكداً فذكّر بمراجعة الوثائق المعتمدة."
) + AI_SCOPE_GUARDRAILS_AR

NCA_GAP_SYSTEM_AR = (
    "أنت مستشار امتثال سيبراني لمدير في منظمة سعودية. "
    "ركّز على **الجاهزية والضوابط بما يتوافق مع توجهات الهيئة الوطنية للأمن السيبراني (NCA)** والممارسات الوطنية، "
    "مع إمكانية الإشارة لأطر دولية عند الفائدة. "
    f"{PLATFORM_GPT_LOGIC_AR} "
    "عند تلخيص الفجوات اعتمد على **مراجع الضوابط والبيانات المرفقة** من المنصة ومقتطفات ECC إن وُجدت. "
    "أجب بالعربية الفصحى المبسطة. لا تدّعِ صفة رسمية عن الهيئة."
) + AI_SCOPE_GUARDRAILS_AR

# يحسّن «الرؤية» دون الحاجة لتغيير النموذج — يُفعّل بـ AI_STRUCTURED_INSIGHTS=true
CHAT_INSIGHT_FORMAT_AR = """

【تنسيق الرؤية (عندما يناسب السؤال)】
للأسئلة التحليلية أو طلب التوصية، نسّق الإجابة بعناوين واضحة:
**1) ملخص تنفيذي** — 2–4 جمل للقارئ المشغول.
**2) قراءة الوضع** — ما يستنتج حصرياً من البيانات المرفقة (لقطة/فجوات) دون اختلاق أرقام.
**3) رؤية وتحليل** — أسباب، مخاطر، اعتماديات بين الضوابط عند الانطباق.
**4) توصيات عملية** — قائمة مرقمة مع **أولوية** (عاجل / متوسط / لاحق) و**الخطوة التالية** لكل بند.
**5) أدلة أو مؤشرات نجاح** — ما يثبت التحسّن.
إن كان السؤال بسيطاً (تعريف، نعم/لا) فاختصر دون إجبار كل الأقسام.
"""

GAP_INSIGHT_FORMAT_AR = """

【هيكل مخرجات تحليل الفجوات】
استخدم عناوين فرعية: **ملخص تنفيذي** → **أولويات مرقّمة** (مع تبرير قصير) → **مخاطر رئيسية** → **خطة إغلاق مقترحة** (خطوات عملية 4–8) مع تقدير **الأثر** و**الجهد** تقريبياً (منخفض/متوسط/مرتفع) عند الإمكان.
"""


def _system_chat() -> str:
    base = NCA_FOCUS_SYSTEM_AR
    if settings.ai_structured_insights:
        base += CHAT_INSIGHT_FORMAT_AR
    extra = (settings.ai_sa_cyber_context_extra or "").strip()
    if not extra:
        return base
    return f"{base}\n\n— سياق إضافي من إعدادات المنصة (المعايير/السياسات الداخلية المعتمدة لديكم):\n{extra}"


def _system_gap() -> str:
    base = NCA_GAP_SYSTEM_AR
    if settings.ai_structured_insights:
        base += GAP_INSIGHT_FORMAT_AR
    extra = (settings.ai_sa_cyber_context_extra or "").strip()
    if not extra:
        return base
    return f"{base}\n\n— سياق إضافي من إعدادات المنصة:\n{extra}"


def _fetch_compliance_rows(
    db: Session,
    department_id: int | None,
    framework_id: int | None,
    control_ids: list[int] | None = None,
) -> list[ComplianceRecord]:
    q = db.query(ComplianceRecord)
    if department_id is not None:
        q = q.filter(ComplianceRecord.department_id == department_id)
    if framework_id is not None:
        q = q.join(Control, ComplianceRecord.control_id == Control.id).filter(Control.framework_id == framework_id)
    if control_ids is not None:
        if len(control_ids) == 0:
            return []
        q = q.filter(ComplianceRecord.control_id.in_(control_ids))
    return q.all()


def _compliance_snapshot(db: Session, department_id: int | None, framework_id: int | None) -> str:
    """لقطة أرقام وحالات من قاعدة البيانات ليرد المساعد على أسئلة النسب والفجوات."""
    rows = _fetch_compliance_rows(db, department_id, framework_id, control_ids=None)

    dept_line = "جميع الإدارات (مجمّع)"
    if department_id is not None:
        d = db.query(Department).filter(Department.id == department_id).first()
        dept_line = f"إدارة: {d.name_ar}" if d else f"إدارة (معرّف {department_id})"

    fw_line = "جميع الأطر (مجمّع)"
    if framework_id is not None:
        fw = db.query(Framework).filter(Framework.id == framework_id).first()
        fw_line = f"الإطار المختار: {fw.name_ar} ({fw.code})" if fw else f"إطار (معرّف {framework_id})"

    def _cnt(st: ComplianceStatusEnum) -> int:
        return sum(1 for r in rows if r.status == st)

    total = len(rows)
    compliant = _cnt(ComplianceStatusEnum.compliant)
    partial = _cnt(ComplianceStatusEnum.partial)
    not_started = _cnt(ComplianceStatusEnum.not_started)
    not_applicable = _cnt(ComplianceStatusEnum.not_applicable)
    rate = round(100.0 * compliant / total, 1) if total else 0.0
    lib_q = db.query(func.count(Control.id))
    if framework_id is not None:
        lib_q = lib_q.filter(Control.framework_id == framework_id)
    total_controls_lib = lib_q.scalar() or 0

    lines: list[str] = [
        "### لقطة امتثال (منطق المنصة — مدخلات مستخدم وقاعدة بيانات)",
        "هذه الأرقام مأخوذة من سجلات الامتثال المسجّلة في النظام (بعد الاستيراد/التحديث اليدوي) وليست تقديراً من النموذج اللغوي.",
        f"- {fw_line}",
        f"- {dept_line}",
        f"- عدد سجلات الامتثال في هذا النطاق (حسب الفلترة أعلاه): {total}",
        f"- ممتثل: {compliant} | جزئي: {partial} | لم يبدأ: {not_started} | لا ينطبق: {not_applicable}",
        f"- **نسبة الممتثل من سجلات هذا النطاق**: {rate}% (ممتثل ÷ إجمالي السجلات)",
        f"- عدد الضوابط في المكتبة ضمن نفس نطاق الإطار (إن وُجد فلتر): {total_controls_lib}",
        "",
    ]

    open_rows = [r for r in rows if r.status in (ComplianceStatusEnum.partial, ComplianceStatusEnum.not_started)]
    open_rows = open_rows[:18]
    if open_rows:
        c_ids = {r.control_id for r in open_rows}
        d_ids = {r.department_id for r in open_rows}
        controls = {c.id: c for c in db.query(Control).filter(Control.id.in_(c_ids)).all()}
        depts = {d.id: d for d in db.query(Department).filter(Department.id.in_(d_ids)).all()}
        lines.append("سجلات تحتاج متابعة (جزئي / لم يبدأ) — أمثلة:")
        for r in open_rows:
            c = controls.get(r.control_id)
            dep = depts.get(r.department_id)
            ref = c.control_ref if c else str(r.control_id)
            title = (c.title_ar or "")[:100] if c else ""
            dep_ar = dep.name_ar if dep else ""
            lines.append(f"  - [{ref}] {title} — الإدارة: {dep_ar or r.department_id}")
    else:
        lines.append("لا توجد في هذا النطاق سجلات بحالة «جزئي» أو «لم يبدأ».")

    lines.append("")
    lines.append(
        "استخدم هذه الأرقام عند الإجابة عن نسبة الامتثال والمشاكل والأولويات. "
        "إن سأل المستخدم عن «نسبتي» فاشرح أن النسبة أعلاه تقصد نسبة السجلات «ممتثل» ضمن النطاق المختار."
    )
    return "\n".join(lines)


def _rule_based_recommendations(
    db: Session,
    department_id: int | None,
    framework_id: int | None,
    filter_control_ids: list[int] | None = None,
) -> tuple[str, list[int], bool]:
    rows = _fetch_compliance_rows(db, department_id, framework_id, filter_control_ids)
    partial_or_open = [
        r.control_id
        for r in rows
        if r.status in (ComplianceStatusEnum.not_started, ComplianceStatusEnum.partial)
    ]
    partial_or_open = list(dict.fromkeys(partial_or_open))[:15]
    if filter_control_ids is not None:
        scope = "الضوابط الظاهرة في جدول الامتثال بعد التصفية/البحث في الواجهة."
    else:
        scope = "النطاق المفلتر في اللوحة (إدارة/إطار إن وُجد)."
    text = (
        "تحليل قاعدي (بدون نموذج لغوي): ركّز على الضوابط ذات الحالة «جزئي» أو «لم يبدأ» ضمن "
        f"{scope} "
        "أضف أدلة واضحة لكل ضابط، وحدّث المسؤول والتاريخ. "
        "عند تفعيل OPENAI_API_KEY يتم توليد توصيات مخصصة بالعربية بما يتماشى مع الإطار المختار."
    )
    return text, partial_or_open, False


async def ai_gap_analysis(
    db: Session,
    department_id: int | None,
    framework_id: int | None = None,
    *,
    control_ids: list[int] | None = None,
) -> tuple[str, list[int], bool]:
    summary, prioritized_ids, used = _rule_based_recommendations(
        db, department_id, framework_id, filter_control_ids=control_ids
    )
    if not settings.openai_api_key:
        return summary, prioritized_ids, False
    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=settings.openai_api_key)
        dept = ""
        if department_id:
            d = db.query(Department).filter(Department.id == department_id).first()
            if d:
                dept = f"الإدارة: {d.name_ar}. "
        fw = ""
        if framework_id:
            frow = db.query(Framework).filter(Framework.id == framework_id).first()
            if frow:
                fw = f"الإطار المعتمد للتحليل: {frow.name_ar} ({frow.code}) — ركّز التوصيات على ضوابط هذا الإطار فقط. "
        scope_note = ""
        if control_ids is not None:
            scope_note = (
                f"نطاق التحليل مقيّد بـ {len(control_ids)} ضابطاً تظهر سجلاتها في الجدول بعد تصفية المستخدم (وليس كامل الإطار). "
            )
        controls = (
            db.query(Control).filter(Control.id.in_(prioritized_ids)).all() if prioritized_ids else []
        )
        refs = ", ".join(f"{c.control_ref}" for c in controls[:20])
        prompt = (
            f"{dept}{fw}{scope_note}"
            f"لدينا ضوابط تحتاج متابعة (مراجع: {refs or 'لا يوجد'}). "
            "السياق: منظمة تعمل ضمن متطلبات الجاهزية والامتثال السيبراني في المملكة وبما يتوافق مع توجهات NCA. "
            "اكتب ملخصاً قصيراً بالعربية لمدير امتثال: أولويات، مخاطر، و**حلول/خطوات عملية مقترحة** (3-6 نقاط) متماشية مع الإطار المذكور."
        )
        if settings.ecc_kb_enabled:
            ecc_q = f"ECC الضوابط الأساسية للأمن السيبراني فجوات أولويات {refs} {dept}{fw}"
            ecc_block = await asyncio.to_thread(ecc_kb.retrieve_for_query, ecc_q)
            if ecc_block.strip():
                prompt = (
                    "### مقتطفات مرجعية من ECC-2-2024 (استخراج آلياً من PDF الرسمي)\n"
                    f"{ecc_block}\n\n---\n\n"
                    + prompt
                )
        r = await client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": _system_gap()},
                {"role": "user", "content": prompt},
            ],
            max_tokens=settings.openai_max_tokens_gap,
            temperature=settings.openai_temperature,
        )
        text = (r.choices[0].message.content or summary).strip()
        return text, prioritized_ids, True
    except Exception:
        return summary, prioritized_ids, False


def _build_chat_user_content(
    user_message: str,
    db: Session,
    control_id: int | None,
    department_id: int | None,
    framework_id: int | None,
    gap_summary: str | None,
    include_compliance_snapshot: bool,
    ecc_excerpts: str = "",
) -> str:
    parts: list[str] = []
    if control_id:
        c = db.query(Control).filter(Control.id == control_id).first()
        if c:
            extra = []
            if c.domain_ar:
                extra.append(f"المجال: {c.domain_ar}")
            if c.standard_title_ar:
                extra.append(f"المعيار: {c.standard_title_ar}")
            if c.objective_ar:
                extra.append(f"الهدف: {c.objective_ar}")
            if c.implementation_guidance_ar:
                extra.append(f"نص الضابط: {c.implementation_guidance_ar}")
            if c.evidence_guidance_ar:
                extra.append(f"إرشادات الأدلة: {c.evidence_guidance_ar}")
            body = "\n".join(extra) if extra else (c.description_ar or "")
            parts.append(f"### ضابط محدد في السياق\n{c.control_ref} — {c.title_ar}\n{body}")
    if include_compliance_snapshot:
        parts.append(_compliance_snapshot(db, department_id, framework_id))
    gs = (gap_summary or "").strip()
    if gs:
        parts.append("### تحليل الفجوات الأخير (من لوحة التحكم)\n" + gs[:8000])
    ex = (ecc_excerpts or "").strip()
    if ex:
        parts.append(
            "### مقتطفات من وثيقة ECC-2-2024 (الضوابط الأساسية للأمن السيبراني — NCA)\n"
            "المصدر: ملف PDF المنشور على cdn.nca.gov.sa — النص مستخرج آلياً وقد ينقصه التنسيق أو يحوي أخطاء.\n"
            "عند الإجابة عن متطلبات ECC استند إلى هذه المقتطفات قدر الإمكان واذكر إن كان النص غير واضح.\n\n"
            + ex
        )
    parts.append(
        "### توجيه للإجابة (GPT + منطق)\n"
        "- اربط إجابتك بين **مقتطفات ECC-2-2024** (عند الحاجة للمعيار الوطني) وبين **لقطة الامتثال** و**تحليل الفجوات** (وضع المستخدم).\n"
        "- إن وُجد **تحليل فجوات** ووُضح **إطار** في اللقطة: قدّم **حلولاً مقترحة عملية** (خطوات، أدلة مقترحة، أولوية تنفيذ) متماشية مع ذلك الإطار ومع نص التحليل؛ صِغها كتوصيات وليست قراراً رسمياً.\n"
        "- إن سُئلت عن «تحليل الملفات»: وضّح أن استيراد الجداول ورفع الأدلة يحدّث بيانات المنصة، والمساعد يفسّر ويرشد وفق المعيار والبيانات المرفقة — لا يستبدل مراجعة داخلية رسمية.\n"
        f"### سؤال المستخدم\n{user_message}"
    )
    return "\n\n".join(parts)


async def ai_chat(
    user_message: str,
    db: Session,
    control_id: int | None,
    *,
    department_id: int | None = None,
    framework_id: int | None = None,
    gap_summary: str | None = None,
    include_compliance_snapshot: bool = True,
) -> tuple[str, bool]:
    ecc_excerpts = ""
    if settings.ecc_kb_enabled:
        ecc_q = user_message
        if framework_id is not None:
            fw = db.query(Framework).filter(Framework.id == framework_id).first()
            if fw:
                ecc_q = f"{user_message} {fw.name_ar} {fw.code} {fw.name_en} إطار امتثال"
        ecc_excerpts = await asyncio.to_thread(ecc_kb.retrieve_for_query, ecc_q)
    user_content = _build_chat_user_content(
        user_message,
        db,
        control_id,
        department_id,
        framework_id,
        gap_summary,
        include_compliance_snapshot,
        ecc_excerpts=ecc_excerpts,
    )
    if not settings.openai_api_key:
        reply = (
            "وضع بدون مفتاح API: أدناه لقطة من بياناتك (وتحليل الفجوات إن وُجد). "
            "لتفعيل إجابات المساعد الذكي، عيّن OPENAI_API_KEY في ملف .env\n\n"
            + user_content
        )
        return reply, False
    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=settings.openai_api_key)
        sys = (
            _system_chat()
            + " إذا وُجدت لقطة امتثال أو تحليل فجوات فهي **منطق المنصة** — مصدر الأرقام والحالات؛ إن وُضح «إطار» في اللقطة فالتزم به في الحلول المقترحة."
            + " إذا وُجدت مقتطفات ECC فهي من **ECC-2-2024** (استخراج آلياً من PDF) — للمعيار الوطني؛ نبّه لاحتمال أخطاء الاستخراج والرجوع لملف nca.gov.sa عند الحسم."
        )
        r = await client.chat.completions.create(
            model=settings.openai_model,
            messages=[{"role": "system", "content": sys}, {"role": "user", "content": user_content}],
            max_tokens=settings.openai_max_tokens_chat,
            temperature=settings.openai_temperature,
        )
        return (r.choices[0].message.content or "").strip(), True
    except Exception as e:
        return f"تعذر الاتصال بنموذج الذكاء الاصطناعي: {e}", False


EXPLAIN_FRAMEWORK_SYSTEM_AR = (
    "أنت تشرح أطر الامتثال والضوابط السيبرانية بالعربية لمستخدمي منصة داخلية في المملكة العربية السعودية. "
    "كن واضحاً ومنطقياً. لا تدّعِ أنك تمثّل الهيئة الوطنية للأمن السيبراني. "
    "إذا وُجدت مقتطفات من وثيقة ECC فهي مستخرجة آلياً من PDF رسمي — نبّه لاحتمال نقص التنسيق أو الأخطاء."
) + AI_SCOPE_GUARDRAILS_AR


async def explain_framework(db: Session, framework_id: int) -> tuple[str, bool]:
    """شرح إطار مختار مع ربط ECC عند توفر الفهرس والنموذج."""
    fw = db.query(Framework).filter(Framework.id == framework_id).first()
    if not fw:
        return "لم يُعثر على هذا الإطار في المنصة.", False

    controls = (
        db.query(Control)
        .filter(Control.framework_id == framework_id)
        .order_by(Control.control_ref)
        .limit(45)
        .all()
    )
    refs = "\n".join(f"- {c.control_ref}: {c.title_ar}" for c in controls) or "(لا توجد ضوابط مسجّلة لهذا الإطار في المنصة حالياً.)"

    ecc_block = ""
    if settings.ecc_kb_enabled:
        ecc_block = await asyncio.to_thread(
            ecc_kb.retrieve_for_query,
            f"شرح ECC الضوابط الأساسية للأمن السيبراني {fw.name_ar} {fw.code} {fw.name_en}",
            10,
            12000,
        )

    pdf_url = settings.ecc_pdf_url

    if not settings.openai_api_key:
        parts = [
            f"## {fw.name_ar}\n**الرمز:** {fw.code}\n\n{fw.description or '—'}\n",
            "### أمثلة ضوابط مسجّلة في المنصة لهذا الإطار\n" + refs,
        ]
        if ecc_block.strip():
            parts.append("\n### مقتطفات مرجعية من ECC-2-2024 (استخراج آلياً — قد ينقص أو يشوبه خطأ)\n" + ecc_block)
        parts.append(
            f"\n\n---\n**المرجع الرسمي لوثيقة الضوابط الأساسية للأمن السيبراني (ECC-2-2024):** {pdf_url}\n"
            "**الموقع العام للهيئة الوطنية للأمن السيبراني:** https://nca.gov.sa\n\n"
            "لتفعيل شرح تلقائي أوضح بالذكاء الاصطناعي، عيّن OPENAI_API_KEY في ملف بيئة الخادم."
        )
        return "\n".join(parts), False

    user_content = "\n".join(
        [
            "### بيانات الإطار من المنصة",
            f"- الرمز: {fw.code}",
            f"- الاسم (عربي): {fw.name_ar}",
            f"- الاسم (إنجليزي): {fw.name_en}",
            f"- وصف مختصر في المنصة: {fw.description or '—'}",
            "",
            "### ضوابط مرتبطة بهذا الإطار في قاعدة بيانات المنصة",
            refs,
        ]
    )
    if ecc_block.strip():
        user_content += (
            "\n\n### مقتطفات من ECC-2-2024 (PDF الرسمي على cdn.nca.gov.sa — استخراج آلياً)\n" + ecc_block
        )
    user_content += (
        "\n\n### المطلوب منك\n"
        "1) اشرح **ما هذا الإطار** و**دوره** في الامتثال والأمن السيبراني للجهات في السعودية.\n"
        "2) إن انطبق، اربط الإطار بـ **الضوابط الأساسية للأمن السيبراني ECC** والهيئة الوطنية للأمن السيبراني، مع الاعتماد على المقتطفات عند الحاجة.\n"
        "3) اشرح بإيجاز معنى **الضوابط المذكورة أعلاه** كأمثلة في المنصة (دون افتراض أنها القائمة الكاملة الرسمية).\n"
        "4) أختم بفقرة تحتوي صراحةً الرابط الرسمي للوثيقة PDF: "
        + pdf_url
        + " ورابط الموقع العام https://nca.gov.sa عند الحديث عن ECC.\n"
        "تجنّب الإطالة الزائدة (حوالي 700–1000 كلمة كحد أعلى تقريبي)."
    )

    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=settings.openai_api_key)
        r = await client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": EXPLAIN_FRAMEWORK_SYSTEM_AR},
                {"role": "user", "content": user_content},
            ],
            max_tokens=settings.openai_max_tokens_explain,
            temperature=settings.openai_temperature,
        )
        return (r.choices[0].message.content or "").strip(), True
    except Exception as e:
        return f"تعذر توليد الشرح: {e}", False


FILE_ANALYZE_SYSTEM_AR = (
    "أنت محلل وثائق ضمن منصة امتثال وضوابط سيبرانية في المملكة. "
    "ستتلقى نصاً مستخرجاً من ملف قد يكون سياسة داخلية، سجل أدلة، جدول ضوابط، أو وثيقة تقنية.\n"
    "المطلوب: (1) لخص بإيجاز ما يتعلق بالامتثال والأمن السيبراني. (2) اذكر فجوات أو نواقص ظاهرة في النص إن وجدت. "
    "(3) اربط عند الإمكان بمتطلبات الضوابط الأساسية ECC والممارسات الوطنية (NCA) باستخدام **المقتطفات المرجعية المرفقة فقط** كدعم — لا تفتعل متطلبات غير مذكورة هناك.\n"
    "(4) إن كان الملف لا يخص الامتثال أو الأمن السيبراني، صرّح بذلك ووجّه المستخدم لاستخدام المنصة لتتبع الضوابط.\n"
    "أجب بالعربية الفصحى المبسطة. لا تدّعِ تمثيل الهيئة."
) + AI_SCOPE_GUARDRAILS_AR


def _spreadsheet_bytes_to_text(raw: bytes, name_lower: str) -> str:
    import pandas as pd

    if name_lower.endswith(".csv"):
        df = pd.read_csv(io.BytesIO(raw))
    else:
        df = pd.read_excel(io.BytesIO(raw), sheet_name=0)
    parts: list[str] = []
    for _, row in df.head(250).iterrows():
        vals = [str(x).strip() for x in row.tolist() if pd.notna(x) and str(x).strip()]
        if vals:
            parts.append(" | ".join(vals))
    return "\n".join(parts)


async def ai_analyze_uploaded_file(
    file_bytes: bytes,
    filename: str,
    focus: str | None = None,
) -> tuple[str, bool, int]:
    """تحليل ملف PDF/Excel/CSV: استخراج نص + RAG من ECC + OpenAI + Guardrails."""
    from app.services.ecc_kb import extract_plain_text_from_pdf_bytes

    name = (filename or "").lower()
    text = ""
    if name.endswith(".pdf"):
        text = await asyncio.to_thread(extract_plain_text_from_pdf_bytes, file_bytes, 48000)
        if not text.strip():
            return "تعذر استخراج نص واضح من ملف PDF (قد يكون ممسوحاً ضوئياً دون طبقة نص).", False, 0
    elif name.endswith((".xlsx", ".xls", ".csv")):
        try:
            text = await asyncio.to_thread(_spreadsheet_bytes_to_text, file_bytes, name)
        except Exception as e:
            return f"تعذر قراءة الجدول: {e}", False, 0
    else:
        return "يُدعم تحليل ملفات PDF و Excel (xlsx/xls) و CSV فقط.", False, 0

    if not text.strip():
        return "الملف فارغ أو لا يحتوي بيانات قابلة للقراءة.", False, 0

    n = len(text)
    ecc_excerpts = ""
    if settings.ecc_kb_enabled:
        fq = f"{(focus or '').strip()} {text[:2000]} ECC NCA امتثال ضوابط أساسية"
        ecc_excerpts = await asyncio.to_thread(ecc_kb.retrieve_for_query, fq)

    user_block = (
        f"### اسم الملف\n{filename}\n\n"
        f"### تركيز المستخدم (اختياري)\n{(focus or '—').strip()}\n\n"
        "### مقتطفات مرجعية من وثيقة ECC (استخراج آلياً — قد تنقص)\n"
        f"{ecc_excerpts[:12000]}\n\n"
        "### نص مستخرج من الملف\n"
        f"{text[:32000]}"
    )

    if not settings.openai_api_key:
        return (
            f"تم استخراج {n} حرفاً من الملف. لتلخيص ذكي وربطاً بمرجع ECC، عيّن OPENAI_API_KEY في بيئة الخادم.\n\n"
            f"معاينة أول 1500 حرف:\n\n{text[:1500]}",
            False,
            n,
        )

    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=settings.openai_api_key)
        r = await client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": FILE_ANALYZE_SYSTEM_AR},
                {"role": "user", "content": user_block},
            ],
            max_tokens=min(settings.openai_max_tokens_chat, 3200),
            temperature=settings.openai_temperature,
        )
        return (r.choices[0].message.content or "").strip(), True, n
    except Exception as e:
        return f"تعذر التحليل عبر النموذج: {e}", False, n


def ai_parse_import_preview(rows: list[dict]) -> str:
    """Heuristic summary for imported spreadsheet rows (ذكاء اصطناعي خفيف بدون API)."""
    if not rows:
        return "لا توجد صفوف للتحليل."
    keys = set()
    for r in rows[:50]:
        keys.update(r.keys())
    return (
        f"تمت قراءة {len(rows)} صفاً. الأعمدة المكتشفة: {', '.join(sorted(keys))}. "
        "تأكد من وجود أعمدة: مرجع_الضابط، العنوان، الإطار (اختياري)."
    )
