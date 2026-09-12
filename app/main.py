"""CyberSift -- FastAPI entrypoint.

Endpoints: health check, file ingestion (file -> text), and extraction
(file or pasted text -> verified findings via the LLM pipeline).
"""

import os
import tempfile

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.core.pipeline import build_summary, run_extraction
from app.core.registry import get_extractors, get_loader, supported_categories, supported_formats
from app.schemas.models import ExtractionResponse

MAX_UPLOAD_BYTES = 15 * 1024 * 1024

app = FastAPI(title="CyberSift")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://cybersift.vercel.app",
        "https://cybersift-karansoni.vercel.app",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "formats": supported_formats(),
        "categories": supported_categories(),
        "llm_configured": bool(os.environ.get("ANTHROPIC_API_KEY")),
    }


async def _load_upload(file: UploadFile, format: str) -> tuple[str, str]:
    """Save the upload to a temp file and load it to text. Returns (text, format_used)."""
    data = await file.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File too large (limit 15 MB).")
    suffix = os.path.splitext(file.filename or "")[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(data)
        tmp_path = tmp.name
    try:
        loader = get_loader(file.filename or tmp_path, format_override=format)
        text = loader.load(tmp_path)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception:
        raise HTTPException(
            status_code=400,
            detail=f"Could not read this file as {format if format != 'auto' else 'its detected format'}. "
            "Try the format override dropdown.",
        )
    finally:
        os.unlink(tmp_path)
    return text, loader.format_name


@app.post("/api/ingest")
async def ingest(file: UploadFile = File(...), format: str = Form("auto")):
    """Load an uploaded file to plain text (no extraction)."""
    text, format_used = await _load_upload(file, format)
    return {
        "filename": file.filename,
        "format_used": format_used,
        "characters": len(text),
        "text": text,
    }


@app.post("/api/extract", response_model=ExtractionResponse)
async def extract(
    file: UploadFile | None = File(None),
    text: str = Form(""),
    categories: str = Form("ioc"),  # comma-separated category ids
    format: str = Form("auto"),
):
    """Run the LLM extraction pipeline over an uploaded file and/or pasted text."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise HTTPException(
            status_code=503,
            detail="The server has no ANTHROPIC_API_KEY configured, so extraction "
            "cannot run. Add the key in Vercel's environment variables and redeploy.",
        )

    category_ids = [c.strip() for c in categories.split(",") if c.strip()]
    extractors = get_extractors(category_ids)
    if not extractors:
        raise HTTPException(status_code=400, detail="No valid extraction categories selected.")

    filename = None
    format_used = None
    document = text or ""
    if file is not None and file.filename:
        file_text, format_used = await _load_upload(file, format)
        filename = file.filename
        document = (document + "\n\n" + file_text).strip() if document else file_text

    if not document.strip():
        raise HTTPException(status_code=400, detail="Attach a file or paste some text to analyze.")

    findings, errors, chunk_count = await run_extraction(document, extractors)
    selected = [ex.category_id for ex in extractors]
    return ExtractionResponse(
        filename=filename,
        format_used=format_used,
        characters=len(document),
        chunks=chunk_count,
        categories=selected,
        findings=findings,
        summary=build_summary(findings, selected, errors),
        errors=errors,
    )
