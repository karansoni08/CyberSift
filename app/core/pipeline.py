"""core.pipeline
Orchestrates one extraction run: chunk the text, fan out one LLM call per
(category, chunk) pair, verify each batch against its source chunk, then
dedupe across chunks.
"""

import asyncio

from app.core.chunker import chunk_text
from app.core.llm_client import extract_from_chunk
from app.core.verifier import dedupe_findings, verify_findings
from app.schemas.models import Finding


async def _run_one(extractor, chunk: str) -> list[Finding]:
    raw = await extract_from_chunk(extractor.system_prompt(), chunk)
    return verify_findings(raw, extractor.category_id, extractor.subtypes, chunk)


async def run_extraction(text: str, extractors: list) -> tuple[list[Finding], list[str], int]:
    """Returns (findings, errors, chunk_count)."""
    chunks = chunk_text(text)
    if not chunks:
        return [], ["Document contained no extractable text."], 0

    tasks = [(ex, chunk, asyncio.create_task(_run_one(ex, chunk))) for ex in extractors for chunk in chunks]

    findings: list[Finding] = []
    errors: list[str] = []
    failed_categories: set[str] = set()
    for extractor, _chunk, task in tasks:
        try:
            findings.extend(await task)
        except Exception as exc:  # one failed call shouldn't sink the run
            if extractor.category_id not in failed_categories:
                failed_categories.add(extractor.category_id)
                errors.append(f"{extractor.label} extraction failed: {exc}")

    return dedupe_findings(findings), errors, len(chunks)


def build_summary(findings: list[Finding], categories: list[str], errors: list[str]) -> str:
    if not findings:
        base = "No verified findings were extracted from this document."
        return base + (" Some extraction calls failed." if errors else "")
    counts: dict[str, int] = {}
    for f in findings:
        counts[f.category] = counts.get(f.category, 0) + 1
    parts = [f"{n} {cat.upper()}" for cat, n in sorted(counts.items())]
    summary = f"Extracted {len(findings)} verified finding(s): " + ", ".join(parts) + "."
    empty = [c for c in categories if c not in counts]
    if empty:
        summary += f" Nothing found for: {', '.join(c.upper() for c in empty)}."
    return summary
