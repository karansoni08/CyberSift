# Vercel entrypoint -- the backend package lives in backend/, so put it on
# the path and re-export the FastAPI app.
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.main import app  # noqa: E402
