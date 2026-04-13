import asyncio
import logging
from contextlib import asynccontextmanager

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.config import settings
from app.database import Base, SessionLocal, engine, ensure_sqlite_columns
from app.routers import ai_router, auth, compliance, controls, dashboard, departments, import_router, mappings
from app.services import ecc_kb
from app.services.ecc_catalog_sync import sync_ecc_catalog
from app.services.seed import seed_if_empty

Base.metadata.create_all(bind=engine)
ensure_sqlite_columns()
db = SessionLocal()
try:
    seed_if_empty(db)
    sync_ecc_catalog(db)
finally:
    db.close()

_log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.ecc_kb_enabled:
        try:
            await asyncio.to_thread(ecc_kb.warm_index)
        except Exception:
            _log.exception("تعذر تسخين فهرس ECC — سيُبنى عند أول طلب للمساعد")
    yield


app = FastAPI(
    title="نظام إدارة الضوابط السيبرانية",
    description="منصة امتثال مع طبقة ذكاء اصطناعي — وفق مقترح المشروع",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(controls.router, prefix="/api")
app.include_router(departments.router, prefix="/api")
app.include_router(compliance.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(ai_router.router, prefix="/api")
app.include_router(import_router.router, prefix="/api")
app.include_router(mappings.router, prefix="/api")


@app.get("/api/health")
def health():
    return {"status": "ok"}


_BACKEND_ROOT = Path(__file__).resolve().parent.parent
_GECC_GUIDE_PDF = _BACKEND_ROOT / "data" / "gecc_implementation_guide_ar.pdf"


@app.get("/api/reference/gecc-implementation-guide-ar.pdf")
def gecc_implementation_guide_pdf():
    """الدليل الإرشادي لتطبيق الضوابط (نسخة محلية مرفقة مع المشروع)."""
    if not _GECC_GUIDE_PDF.is_file():
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="ملف الدليل غير موجود")
    return FileResponse(
        _GECC_GUIDE_PDF,
        media_type="application/pdf",
        filename="Guide-to-Essential-Cybersecurity-Controls-Implementation-ar.pdf",
    )


# مجلد رفع الأدلة
_BACKEND_ROOT.joinpath("uploads").mkdir(parents=True, exist_ok=True)
