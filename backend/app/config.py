from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# مجلد backend/ (حيث يجب أن يوجد ملف .env) — لا يعتمد على مجلد تشغيل uvicorn
_BACKEND_DIR = Path(__file__).resolve().parent.parent
_ENV_FILE = _BACKEND_DIR / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "sqlite:///./cyber_compliance.db"
    # للإنتاج: أضف نطاق موقعك مفصولاً بفاصلة، مثل: https://app.onrender.com,https://www.example.com
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    secret_key: str = "change-me-in-production-use-openssl-rand-hex-32"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    # ثبات أعلى للأرقام والامتثال؛ ارفع قليلاً (مثلاً 0.55) لصياغة أكثر تنوعاً
    openai_temperature: float = Field(default=0.38, ge=0.0, le=2.0)
    # طلب هيكل «رؤية» (ملخص، تحليل، توصيات) في إجابات المساعد وتحليل الفجوات
    ai_structured_insights: bool = True
    openai_max_tokens_chat: int = Field(default=2800, ge=500, le=16000)
    openai_max_tokens_gap: int = Field(default=1200, ge=200, le=8000)
    openai_max_tokens_explain: int = Field(default=1600, ge=300, le=8000)
    # نص اختياري يُلحق برسائل النظام للمساعد وتحليل الفجوات (توجيه إضافي، وليس تدريباً للنموذج)
    ai_sa_cyber_context_extra: str | None = None
    # فهرسة PDF الرسمي ECC-2-2024 من CDN الهيئة (استرجاع مقتطفات للمساعد)
    ecc_kb_enabled: bool = True
    ecc_pdf_url: str = (
        "https://cdn.nca.gov.sa/api/files/public/upload/"
        "29a9e86a-595f-4af9-8db5-88715a458a14_ECC-2-2024---NCA.pdf"
    )
    ecc_retrieval_top_n: int = 12
    ecc_retrieval_max_chars: int = 16000
    # إعادة تنزيل وبناء الفهرس (ECC_FORCE_REBUILD=true للصيانة لمرة واحدة)
    ecc_force_rebuild: bool = False

    @field_validator("openai_api_key", mode="before")
    @classmethod
    def strip_api_key(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = str(v).strip()
        return s if s else None

    @field_validator("ai_sa_cyber_context_extra", mode="before")
    @classmethod
    def strip_context_extra(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = str(v).strip()
        return s if s else None


settings = Settings()
