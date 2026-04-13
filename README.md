# درع سيبراني — إدارة الضوابط والامتثال السيبراني (مشروع ذكاء اصطناعي)

تنفيذ عملي لمنصة **درع سيبراني** لإدارة **الضوابط والامتثال** مع **مرحلة ذكاء اصطناعي**: مساعد محادثة، تحليل فجوات (قاعدي أو عبر LLM عند توفر مفتاح)، واستيراد من Excel/CSV.

## المتطلبات

- Python 3.12+
- Node.js 20+

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

## تشغيل الواجهة (عربي RTL)

```bash
cd frontend
npm install
npm run dev
```

افتح [http://127.0.0.1:5173](http://127.0.0.1:5173) — الطلبات إلى `/api` تُوجَّه تلقائياً إلى المنفذ 8000.

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
- `frontend/src` — React + Vite، واجهة عربية

## النشر على Streamlit Cloud

Streamlit يشغّل **ملف Python واحد** من الجذر، وليس FastAPI + React معاً.

- **ملف الدخول:** `streamlit_app.py` (في جذر المستودع)
- **التبعيات:** `requirements.txt` في الجذر (خاص بـ Streamlit)
- في لوحة Streamlit: **Main file path** = `streamlit_app.py`
- (اختياري) بعد نشر الـ API على Render وغيره: في **Secrets** أضف `API_URL = "https://...."` ثم استخدم «فحص /api/health» من الشريط الجانبي

للنسخة الكاملة (واجهة + API + قاعدة بيانات) استخدم Render / Railway / VPS أو Docker — انظر أقسام التشغيل أعلاه.
