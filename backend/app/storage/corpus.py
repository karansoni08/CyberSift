"""storage.corpus
Layer 2: the cross-scan corpus memory behind novelty scoring.

Every scan appends one immutable record to Vercel Blob storage
(corpus/scans/<id>.json). Reading the corpus = list + fetch records,
aggregated into {digest: {scans, first_seen, categories}} and cached
in-process for the life of the (warm) serverless instance.

Privacy: blob URLs are public, so raw finding values NEVER leave the
process — records hold only HMAC-SHA256 digests keyed with the store's
own secret token, plus category/subtype metadata. Nobody without the
token can test whether a given value is in the corpus.

Without BLOB_READ_WRITE_TOKEN configured, everything degrades to
no-ops and findings simply carry no novelty data.
"""

import asyncio
import hashlib
import hmac
import json
import os
import time
import uuid

import httpx

BLOB_API = "https://blob.vercel-storage.com"
SCAN_PREFIX = "corpus/scans/"
MAX_SCANS_READ = 300

_cache = {"aggregate": None, "fetched_at": 0.0, "known_paths": set()}
_CACHE_TTL_SECONDS = 60


def _token() -> str | None:
    return os.environ.get("BLOB_READ_WRITE_TOKEN")


def enabled() -> bool:
    return bool(_token())


def value_digest(value: str) -> str:
    """HMAC digest of a normalized finding value — the only form stored."""
    key = (_token() or "local").encode()
    return hmac.new(key, value.strip().lower().encode(), hashlib.sha256).hexdigest()[:32]


async def _list_scan_blobs(client: httpx.AsyncClient) -> list[dict]:
    blobs, cursor = [], None
    for _ in range(10):  # paginate defensively
        params = {"prefix": SCAN_PREFIX, "limit": "1000"}
        if cursor:
            params["cursor"] = cursor
        res = await client.get(
            BLOB_API, params=params,
            headers={"Authorization": f"Bearer {_token()}", "x-api-version": "7"},
        )
        res.raise_for_status()
        data = res.json()
        blobs.extend(data.get("blobs", []))
        if not data.get("hasMore") or not data.get("cursor"):
            break
        cursor = data["cursor"]
    blobs.sort(key=lambda b: b.get("uploadedAt", ""), reverse=True)
    return blobs[:MAX_SCANS_READ]


async def _fetch_scan(client: httpx.AsyncClient, blob: dict) -> dict | None:
    try:
        res = await client.get(blob["url"])
        res.raise_for_status()
        return res.json()
    except Exception:
        return None


async def load_aggregate(force: bool = False) -> dict:
    """{digest: {"scans": int, "first_seen": iso, "last_seen": iso,
    "categories": [...], "subtypes": [...]}} plus {"_scan_count": int}."""
    if not enabled():
        return {"_scan_count": 0}
    now = time.time()
    if not force and _cache["aggregate"] is not None and now - _cache["fetched_at"] < _CACHE_TTL_SECONDS:
        return _cache["aggregate"]

    async with httpx.AsyncClient(timeout=20) as client:
        blobs = await _list_scan_blobs(client)
        records = await asyncio.gather(*(_fetch_scan(client, b) for b in blobs))

    agg: dict = {}
    scan_count = 0
    for rec in records:
        if not rec or not isinstance(rec.get("digests"), dict):
            continue
        scan_count += 1
        ts = rec.get("ts", "")
        for digest, meta in rec["digests"].items():
            entry = agg.setdefault(
                digest,
                {"scans": 0, "first_seen": ts, "last_seen": ts, "categories": [], "subtypes": []},
            )
            entry["scans"] += 1
            entry["first_seen"] = min(entry["first_seen"], ts) if entry["first_seen"] else ts
            entry["last_seen"] = max(entry["last_seen"], ts)
            for key in ("categories", "subtypes"):
                for v in meta.get(key, []):
                    if v not in entry[key]:
                        entry[key].append(v)
    agg["_scan_count"] = scan_count
    _cache["aggregate"] = agg
    _cache["fetched_at"] = now
    return agg


async def record_scan(findings: list, source: str | None) -> None:
    """Append this scan's digests to the corpus (fire-and-forget safe)."""
    if not enabled() or not findings:
        return
    digests: dict = {}
    for f in findings:
        d = value_digest(f.value)
        entry = digests.setdefault(d, {"categories": [], "subtypes": []})
        if f.category not in entry["categories"]:
            entry["categories"].append(f.category)
        if f.subtype not in entry["subtypes"]:
            entry["subtypes"].append(f.subtype)
    record = {
        "scan_id": uuid.uuid4().hex,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        # only a hash of the source name — no raw filenames in public storage
        "source_digest": value_digest(source or "pasted-text"),
        "digests": digests,
    }
    path = f"{SCAN_PREFIX}{record['ts'].replace(':', '')}-{record['scan_id'][:8]}.json"
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            await client.put(
                f"{BLOB_API}/{path}",
                content=json.dumps(record),
                headers={
                    "Authorization": f"Bearer {_token()}",
                    "x-api-version": "7",
                    "x-content-type": "application/json",
                    "x-add-random-suffix": "0",
                },
            )
        # fold into the warm cache immediately so back-to-back scans see it
        if _cache["aggregate"] is not None:
            agg = _cache["aggregate"]
            agg["_scan_count"] = agg.get("_scan_count", 0) + 1
            for digest, meta in digests.items():
                entry = agg.setdefault(
                    digest,
                    {"scans": 0, "first_seen": record["ts"], "last_seen": record["ts"],
                     "categories": [], "subtypes": []},
                )
                entry["scans"] += 1
                entry["last_seen"] = record["ts"]
                for key in ("categories", "subtypes"):
                    for v in meta.get(key, []):
                        if v not in entry[key]:
                            entry[key].append(v)
    except Exception:
        pass  # corpus writes must never fail a scan


async def annotate_novelty(findings: list) -> dict:
    """Set novelty fields on each finding from the corpus aggregate.
    Returns corpus stats {"scans": int, "known_values": int}."""
    if not enabled():
        return {"scans": 0, "known_values": 0}
    try:
        agg = await load_aggregate()
    except Exception:
        return {"scans": 0, "known_values": 0}
    for f in findings:
        entry = agg.get(value_digest(f.value))
        if entry:
            f.novel = False
            f.times_seen = entry["scans"]
            f.first_seen = entry["first_seen"]
        else:
            f.novel = True
            f.times_seen = 0
            f.first_seen = None
    return {"scans": agg.get("_scan_count", 0), "known_values": len(agg) - 1}
