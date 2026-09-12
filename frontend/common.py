"""Shared helpers for the Streamlit pages."""

import os

import requests

API_URL = os.environ.get("CYBERSIFT_API_URL", "https://cybersift.vercel.app").rstrip("/")


def api_post(path: str, timeout: int = 240, **kwargs):
    try:
        res = requests.post(f"{API_URL}{path}", timeout=timeout, **kwargs)
    except requests.RequestException as exc:
        raise RuntimeError(f"Could not reach the CyberSift API at {API_URL}: {exc}")
    if not res.ok:
        try:
            detail = res.json().get("detail")
        except Exception:
            detail = None
        raise RuntimeError(detail or f"API request failed ({res.status_code}).")
    return res.json()
