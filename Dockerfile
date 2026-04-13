# درع سيبراني — صورة واحدة: واجهة React + FastAPI
# البناء: docker build -t draya-cyber .
# التشغيل: docker run -p 8000:8000 -e SECRET_KEY=... draya-cyber

FROM node:20-bookworm-slim AS frontend
WORKDIR /src
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim-bookworm
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY backend/ /app/
RUN mkdir -p /app/data /app/uploads /app/static/web
COPY --from=frontend /src/dist/ /app/static/web/

# قاعدة SQLite افتراضية داخل الحاوية (للإنتاج الجاد فكّر في PostgreSQL عبر DATABASE_URL)
ENV DATABASE_URL=sqlite:////app/data/cyber_compliance.db

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
