"""CyberSift -- FastAPI entrypoint.

Minimal app for Phase 1: health check plus a file-ingestion endpoint that
loads an uploaded file to text via the loader registry. Extraction routes
arrive in later phases.
"""

import os
import tempfile

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.core.registry import get_loader, supported_formats

app = FastAPI(title="CyberSift")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok", "formats": supported_formats()}


@app.post("/api/ingest")
async def ingest(file: UploadFile = File(...), format: str = Form("auto")):
    """Load an uploaded file to plain text. Phase 1 scope only --
    extraction is wired in from Phase 3 onward."""
    suffix = os.path.splitext(file.filename or "")[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name
    try:
        loader = get_loader(file.filename or tmp_path, format_override=format)
        text = loader.load(tmp_path)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    finally:
        os.unlink(tmp_path)
    return {
        "filename": file.filename,
        "format_used": loader.format_name,
        "characters": len(text),
        "text": text,
    }
