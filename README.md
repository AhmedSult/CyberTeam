# درع سيبراني — Cyber Shield

منصّة Streamlit متكاملة لإدارة **الضوابط والامتثال السيبراني**، مخصّصة وفق توجيهات
الهيئة الوطنية للأمن السيبراني (NCA) ووثيقة الضوابط الأساسية ECC-2-2024.

## التشغيل المحلي

```bash
python3 -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

افتح [http://localhost:8501](http://localhost:8501).

## النشر على Streamlit Cloud

- **Main file path:** `streamlit_app.py`
- **Python version:** 3.12
- **Requirements:** `requirements.txt` (في الجذر)

في إعدادات التطبيق ← **Secrets**، أضف:

```toml
OPENAI_API_KEY = "sk-..."
OPENAI_MODEL  = "gpt-4o-mini"
# اختياري: سياسات/معايير داخلية تُلحَق برسالة النظام للمساعد
AI_SA_CYBER_CONTEXT_EXTRA = """
معايير المنظمة الداخلية: ...
"""
```

## بنية المشروع

```
streamlit_app.py        نقطة الدخول لـ Streamlit Cloud
app.py                  واجهة المستخدم وصفحات التطبيق
cyber_observatory/
  ai_prompts.py         رسائل النظام للمساعد (NCA / ECC)
  demo_data.py          بيانات أوّلية للضوابط والسجلات
  i18n.py               نصوص العربية/الإنجليزية
  theme.py              ثيم RTL مع وضع فاتح/داكن
.streamlit/config.toml  إعدادات Streamlit
requirements.txt        التبعيات
```

## المميزات

- لوحة نظرة عامة مع مؤشرات وتوزيع الامتثال حسب المجال.
- إدارة سجلات الامتثال (تحديث الحالة، الفلاتر، البحث، إضافة إدارات، تنزيل CSV).
- استيراد ملفات CSV/XLSX للمعاينة.
- تحليل فجوات قاعدي مدمج.
- مساعد ذكي مدعوم بـ OpenAI (تدفّق فوري) ومخصّص لضوابط NCA/ECC، مع وضع تحليل
  محلي عند غياب المفتاح، وزر اختبار اتصال داخل الواجهة.

## مراجع

- الهيئة الوطنية للأمن السيبراني: <https://nca.gov.sa>
- الضوابط الأساسية ECC-2-2024 (PDF):
  <https://cdn.nca.gov.sa/api/files/public/upload/29a9e86a-595f-4af9-8db5-88715a458a14_ECC-2-2024---NCA.pdf>
