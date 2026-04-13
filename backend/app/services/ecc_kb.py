"""
فهرسة مستند ECC (الضوابط الأساسية للأمن السيبراني) من نسخة PDF الرسمية المنشورة على cdn.nca.gov.sa
لاسترجاع مقتطفات ذات صلة وإرفاقها بطلبات المساعد (RAG خفيف عبر BM25).

المرجع الرسمي للنص: الموقع/الملف الأصلي للهيئة — الاستخراج آلياً وقد يحوي أخطاء؛ يُفضّل التدقيق من PDF.
"""

from __future__ import annotations

import io
import json
import logging
import re
import threading
from pathlib import Path
from urllib.parse import urlparse

import httpx
from pypdf import PdfReader
from rank_bm25 import BM25Okapi

from app.config import settings

logger = logging.getLogger(__name__)

# عند تغيير منطق الاستخراج ارفع الرقم لإبطال الذاكرة المحلية للفهرس
EXTRACTOR_VERSION = 2

_lock = threading.Lock()
_chunks: list[str] = []
_tokenized: list[list[str]] = []
_bm25: BM25Okapi | None = None
_load_error: str | None = None


def _backend_dir() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def _index_dir() -> Path:
    return _backend_dir() / "data" / "ecc"


def _meta_path() -> Path:
    return _index_dir() / "meta.json"


def _chunks_path() -> Path:
    return _index_dir() / "chunks.json"


def _pdf_path() -> Path:
    return _index_dir() / "source.pdf"


def _allowed_pdf_url(url: str) -> bool:
    try:
        host = (urlparse(url).hostname or "").lower()
    except Exception:
        return False
    return host == "cdn.nca.gov.sa" or host.endswith(".nca.gov.sa")


def tokenize(text: str) -> list[str]:
    if not text:
        return []
    return re.findall(r"[\u0600-\u06FFa-zA-Z0-9]+", text.lower())


def _normalize_pdf_text(s: str) -> str:
    """تقليل تشويه الأسطر والفواصل الشائعة في PDF العربي."""
    s = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", s)
    s = re.sub(r"[\u200c\u200d\ufeff\u202a-\u202e]", "", s)
    s = re.sub(r"\u00ad", "", s)  # soft hyphen
    # دمج أسطر التفاف داخل الجملة (غالباً يقطع الحروف في PDF)
    for _ in range(4):
        s = re.sub(r"([^\s\n])\n([^\s\n])", r"\1\2", s)
    s = re.sub(r"[ـ]{3,}", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def _chunk_text(full: str, max_size: int = 1200, overlap: int = 200) -> list[str]:
    full = re.sub(r"[ \t\f\v]+", " ", full)
    full = re.sub(r"\n{3,}", "\n\n", full.strip())
    if len(full) < 60:
        return [full] if full else []
    chunks: list[str] = []
    i = 0
    while i < len(full):
        piece = full[i : i + max_size]
        if len(piece.strip()) >= 40:
            chunks.append(piece.strip())
        i += max_size - overlap
        if i >= len(full):
            break
    return chunks


def _extract_chunks_from_pdf(pdf_bytes: bytes) -> list[str]:
    page_texts: list[str] = []
    try:
        import fitz

        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        for page in doc:
            raw = page.get_text("text") or ""
            t = _normalize_pdf_text(raw)
            if len(t) > 50:
                page_texts.append(t)
    except Exception as e:
        logger.warning("PyMuPDF extract failed, fallback pypdf: %s", e)

    if not page_texts:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        for page in reader.pages:
            try:
                raw = page.extract_text() or ""
            except Exception:
                raw = ""
            t = _normalize_pdf_text(raw)
            if len(t) > 50:
                page_texts.append(t)

    full = "\n\n".join(page_texts)
    if not full.strip():
        return []
    # دمج فقرات صغيرة ثم تقطيع للفهرسة
    raw_chunks: list[str] = []
    for para in re.split(r"\n\s*\n", full):
        p = para.strip()
        if len(p) < 30:
            continue
        raw_chunks.extend(_chunk_text(p, max_size=1300, overlap=220))
    # إزالة التكرار التقريبي
    seen: set[str] = set()
    out: list[str] = []
    for c in raw_chunks:
        key = c[:120]
        if key in seen:
            continue
        seen.add(key)
        out.append(c)
    return out


def extract_plain_text_from_pdf_bytes(pdf_bytes: bytes, max_chars: int = 48000) -> str:
    """استخراج نص من PDF مرفوع (لتحليل المستخدم) — ليس لفهرسة ECC."""
    chunks = _extract_chunks_from_pdf(pdf_bytes)
    if not chunks:
        return ""
    full = "\n\n".join(chunks)
    return full[:max_chars].strip()


def _download_pdf(url: str) -> bytes:
    headers = {"User-Agent": "CyberCompliance-ECC-Index/1.0 (+local RAG)"}
    with httpx.Client(timeout=180.0, follow_redirects=True, headers=headers) as client:
        r = client.get(url)
        r.raise_for_status()
        return r.content


def _save_artifacts(url: str, pdf_bytes: bytes, chunks: list[str]) -> None:
    d = _index_dir()
    d.mkdir(parents=True, exist_ok=True)
    _pdf_path().write_bytes(pdf_bytes)
    _chunks_path().write_text(json.dumps(chunks, ensure_ascii=False), encoding="utf-8")
    _meta_path().write_text(
        json.dumps(
            {"source_url": url, "chunk_count": len(chunks), "extractor_version": EXTRACTOR_VERSION},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def _try_load_cached(url: str) -> bool:
    global _chunks, _tokenized, _bm25
    if not _chunks_path().is_file() or not _meta_path().is_file():
        return False
    try:
        meta = json.loads(_meta_path().read_text(encoding="utf-8"))
        if meta.get("source_url") != url:
            return False
        if meta.get("extractor_version") != EXTRACTOR_VERSION:
            return False
        chunks = json.loads(_chunks_path().read_text(encoding="utf-8"))
        if not isinstance(chunks, list) or not chunks:
            return False
        raw = [str(c) for c in chunks]
        pairs = [(c, tokenize(c)) for c in raw]
        pairs = [(c, t) for c, t in pairs if t]
        if not pairs:
            return False
        _chunks = [c for c, _t in pairs]
        _tokenized = [t for _c, t in pairs]
        _bm25 = BM25Okapi(_tokenized)
        logger.info("ECC KB: loaded %s chunks from cache", len(_chunks))
        return True
    except Exception as e:
        logger.warning("ECC KB cache load failed: %s", e)
        return False


def _build_index(url: str) -> None:
    global _chunks, _tokenized, _bm25, _load_error
    if not _allowed_pdf_url(url):
        _load_error = "عنوان PDF غير مسموح (يُقبل فقط nca.gov.sa)"
        logger.error(_load_error)
        return
    pdf_bytes = _download_pdf(url)
    chunks = _extract_chunks_from_pdf(pdf_bytes)
    if not chunks:
        _load_error = "تعذر استخراج نص من PDF (قد يكون ممسوحاً ضوئياً أو محمياً)"
        logger.error(_load_error)
        return
    pairs = [(c, tokenize(c)) for c in chunks]
    pairs = [(c, t) for c, t in pairs if t]
    if not pairs:
        _load_error = "لا توجد مقاطع نصية صالحة للفهرسة بعد الاستخراج"
        logger.error(_load_error)
        return
    indexed_chunks = [c for c, _t in pairs]
    indexed_tokens = [t for _c, t in pairs]
    _save_artifacts(url, pdf_bytes, indexed_chunks)
    _chunks = indexed_chunks
    _tokenized = indexed_tokens
    _bm25 = BM25Okapi(_tokenized)
    _load_error = None
    logger.info("ECC KB: built index with %s chunks from NCA PDF", len(_chunks))


def ensure_index_loaded() -> None:
    """تحميل أو بناء الفهرس (متزامن — يُفضّل استدعاؤه من asyncio.to_thread)."""
    global _load_error
    if not settings.ecc_kb_enabled:
        return
    url = (settings.ecc_pdf_url or "").strip()
    if not url:
        _load_error = "ECC_PDF_URL فارغ"
        return
    with _lock:
        if _bm25 is not None and _chunks:
            return
        if _load_error and not settings.ecc_force_rebuild:
            return
        _load_error = None
        try:
            if not settings.ecc_force_rebuild and _try_load_cached(url):
                return
            _build_index(url)
        except Exception as e:
            _load_error = str(e)
            logger.exception("ECC KB build failed")


def warm_index() -> None:
    """للاستدعاء عند بدء التشغيل لتسخين الذاكرة المؤقتة."""
    ensure_index_loaded()


def retrieve_for_query(query: str, top_n: int | None = None, max_chars: int | None = None) -> str:
    """
    يعيد نصاً يضم مقتطفات الأعلى درجة صلة باستعلام BM25.
    """
    if not settings.ecc_kb_enabled:
        return ""
    ensure_index_loaded()
    if _bm25 is None or not _chunks:
        if _load_error:
            return f"(تعذر تحميل فهرس ECC: {_load_error})"
        return ""
    top_n = top_n or settings.ecc_retrieval_top_n
    max_chars = max_chars or settings.ecc_retrieval_max_chars
    q_tokens = tokenize(query)
    if not q_tokens:
        q_tokens = tokenize("الضوابط الأساسية للأمن السيبراني ECC")
    scores = _bm25.get_scores(q_tokens)
    ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
    picked: list[str] = []
    used = 0
    for i in ranked[:top_n]:
        block = f"[مقتطف {i + 1}]\n{_chunks[i]}"
        if used + len(block) > max_chars:
            break
        picked.append(block)
        used += len(block) + 2
    if not picked:
        return ""
    header = (
        "الآتي مقتطفات مستخرجة آلياً من وثيقة «ECC-2-2024» (الضوابط الأساسية) على موقع الهيئة. "
        "للتنفيذ والأدلة الإرشادية راجع أيضاً «الدليل الإرشادي لتطبيق الضوابط» (GECC) المرفق في المشروع. "
        "قد يحتوي الاستخراج على أخطاء؛ راجع الملف الرسمي عند الحسم.\n\n"
    )
    return header + "\n\n---\n\n".join(picked)


def status_dict() -> dict:
    """للتشخيص (اختياري)."""
    ensure_index_loaded()
    return {
        "enabled": settings.ecc_kb_enabled,
        "chunks": len(_chunks),
        "error": _load_error,
        "source_url": settings.ecc_pdf_url,
    }
