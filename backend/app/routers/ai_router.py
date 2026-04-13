from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.config import settings
from app.schemas import (
    AIChatRequest,
    AIChatResponse,
    ExplainFrameworkRequest,
    ExplainFrameworkResponse,
    FileAnalysisResponse,
    GapAnalysisRequest,
    GapAnalysisResponse,
)
from app.services import ai_service as ai

router = APIRouter(prefix="/ai", tags=["ai"])

_MAX_ANALYZE_BYTES = 8 * 1024 * 1024


@router.post("/chat", response_model=AIChatResponse)
async def chat(
    body: AIChatRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    reply, used = await ai.ai_chat(
        body.message,
        db,
        body.context_control_id,
        department_id=body.department_id,
        framework_id=body.framework_id,
        gap_summary=body.gap_summary,
        include_compliance_snapshot=body.include_compliance_snapshot,
    )
    return AIChatResponse(reply=reply, used_llm=used)


@router.post("/explain-framework", response_model=ExplainFrameworkResponse)
async def explain_framework(
    body: ExplainFrameworkRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    text, used = await ai.explain_framework(db, body.framework_id)
    return ExplainFrameworkResponse(
        explanation=text,
        used_llm=used,
        official_ecc_pdf_url=settings.ecc_pdf_url,
    )


@router.post("/gap-analysis", response_model=GapAnalysisResponse)
async def gap(
    body: GapAnalysisRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    summary, ids, used = await ai.ai_gap_analysis(
        db, body.department_id, body.framework_id, control_ids=body.control_ids
    )
    return GapAnalysisResponse(gaps_summary=summary, prioritized_controls=ids, used_llm=used)


@router.post("/analyze-file", response_model=FileAnalysisResponse)
async def analyze_file(
    file: UploadFile = File(...),
    focus: str = Form(""),
    _: User = Depends(get_current_user),
):
    """تحليل ملف PDF/Excel/CSV: استخراج نص + مقتطفات ECC (RAG) + OpenAI مع حدود المجال."""
    raw = await file.read()
    if len(raw) > _MAX_ANALYZE_BYTES:
        raise HTTPException(status_code=413, detail="حجم الملف يتجاوز 8 ميجابايت")
    name = file.filename or "upload"
    analysis, used, n = await ai.ai_analyze_uploaded_file(raw, name, focus.strip() or None)
    return FileAnalysisResponse(analysis=analysis, used_llm=used, extracted_chars=n)
