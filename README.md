# درع سيبراني — إدارة الضوابط والامتثال السيبراني (مشروع ذكاء اصطناعي)

تنفيذ عملي لمنصة **درع سيبراني** لإدارة **الضوابط والامتثال** مع **مرحلة ذكاء اصطناعي**: مساعد محادثة، تحليل فجوات (قاعدي أو عبر LLM عند توفر مفتاح)، واستيراد من Excel/CSV.

## المتطلبات

- Python 3.12+
- (اختياري) Node.js فقط إذا أردت تشغيل الواجهة القديمة في `frontend/`

## تشغيل الخادم (API)

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # ثم عيّن OPENAI_API_KEY إن رغبت
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- وثائق تفاعلية: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- مستخدم تجريبي: `admin@example.com` / `admin123`

## تشغيل الواجهة الرئيسية (Streamlit — بنمط DHWO)

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

افتح [http://127.0.0.1:8501](http://127.0.0.1:8501)

> واجهة Streamlit أصبحت المسار الأساسي للتشغيل المحلي والنشر.

## ما يتضمنه المشروع

| المكوّن | الوصف |
|--------|--------|
| مكتبة ضوابط | إطارات عيّنة: NCA ECC، NIST CSF، ISO 27001 مع ربط متقاطع نموذجي |
| تتبع امتثال | سجلات لكل إدارة وحالات: لم يبدأ / جزئي / ممتثل / لا ينطبق |
| أدلة | رفع ملفات مرتبطة بسجل امتثال |
| استيراد | معاينة واستيراد ضوابط من CSV/XLSX |
| ذكاء اصطناعي | `/api/ai/chat` و `/api/ai/gap-analysis` — بدون مفتاح: قواعد؛ مع `OPENAI_API_KEY`: نموذج لغوي |
| حوكمة | JWT، أدوار (admin, auditor, owner, viewer)، سجل تدقيق عند تحديث الامتثال |

## هيكل المجلدات

- `backend/app` — FastAPI، SQLAlchemy، خدمة AI
- `app.py` — تطبيق Streamlit الرئيسي
- `streamlit_app.py` — نقطة دخول Streamlit Cloud
- `cyber_observatory/` — طبقة الواجهة (theme / i18n / client / demo)
- `frontend/src` — واجهة قديمة (Legacy)

## النشر على Streamlit Cloud (بنمط DHWO)

تمت إضافة نسخة Streamlit موحدة بهيكل modular مشابه لتقنيات مشروع DHWO:

- **نقطة التشغيل الأساسية:** `app.py`
- **نقطة دخول السحابة:** `streamlit_app.py` (تستدعي `app.main()`)
- **الوحدات المساعدة:** `cyber_observatory/` (تقسيم `theme` + `i18n` + `client` + `demo_data`)

إعداد Streamlit Cloud:

- **Main file path:** `streamlit_app.py`
- **requirements:** `requirements.txt` في الجذر
- (اختياري) لإحضار البيانات الحية من الـ backend أضف في Secrets:
  - `API_URL = "https://...."`

محتوى النسخة الجديدة:

- تنقل علوي متعدد الصفحات (Overview / Compliance / Assistant / API)
- واجهة RTL محسّنة وثيم light/dark
- ربط مباشر مع API (تسجيل دخول JWT + Dashboard stats + Gap analysis + AI chat)
- وضع تجريبي fallback عند غياب الاتصال بالخادم

للنسخة الكاملة (واجهة + API + قاعدة بيانات) استخدم Render / Railway / VPS أو Docker — انظر أقسام التشغيل أعلاه.

## نشر الموقع الكامل (واجهة Streamlit + API)

المشروع يعتمد الآن على **Streamlit + FastAPI** كمسار رئيسي.

### خيار Docker (موصى به للبداية)

من **جذر المستودع**:

```bash
docker build -t draya-cyber .
docker run -p 8000:8000 \
  -e SECRET_KEY=ضع_مفتاحاً_عشوائياً_طويلاً \
  -e OPENAI_API_KEY=اختياري \
  draya-cyber
```

ثم:
- افتح الـ API على `http://localhost:8000`
- وشغّل Streamlit منفصلًا من الجذر: `streamlit run streamlit_app.py`

### Render.com (مجاني محدود)

1. أنشئ **Web Service** من نفس المستودع، **Docker** كبيئة تشغيل.
2. أضف متغيرات البيئة: `SECRET_KEY`، واختياري `OPENAI_API_KEY`، `DATABASE_URL` (أو اترك SQLite الافتراضي مع العلم أن القرص قد يُعاد عند إعادة التشغيل على الطبقة المجانية).
3. المنفذ: **8000**.

### Railway / Fly.io / VPS

نفس فكرة Docker: ابنِ الصورة وشغّلها مع المنفذ 8000 ومتغيرات البيئة.

### ملاحظات

- **Streamlit (`streamlit_app.py`) هو الواجهة الرئيسية الحالية**.
- مجلد `frontend/` موجود كنسخة Legacy للرجوع إليه فقط، وليس مسار التشغيل الافتراضي.
- إذا فصلت Streamlit عن الـ API على نطاقين مختلفين، عيّن `CORS_ORIGINS` في إعدادات الخادم (انظر `backend/.env.example`).
