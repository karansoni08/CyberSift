"""core.verifier
Hallucination guardrail: every finding must be traceable to the source.

A finding survives only if its original_form (or, failing that, its value)
appears verbatim in the chunk it was extracted from. Whitespace inside the
candidate is normalized before the substring check so loader line-wrapping
does not reject genuine findings.
"""

import re

from app.schemas.models import Finding


def _found_in(needle: str, haystack: str, haystack_squashed: str) -> bool:
    if not needle:
        return False
    if needle in haystack:
        return True
    # Tolerate whitespace differences introduced by the loader.
    squashed = re.sub(r"\s+", " ", needle.strip())
    return squashed in haystack_squashed


def verify_findings(raw_items: list[dict], category_id: str, subtypes: tuple, chunk: str) -> list[Finding]:
    """Turn raw LLM output dicts into verified Finding models."""
    haystack_squashed = re.sub(r"\s+", " ", chunk)
    findings = []
    for item in raw_items:
        value = str(item.get("value", "")).strip()
        original = str(item.get("original_form", "")).strip() or value
        subtype = str(item.get("subtype", "")).strip()
        if not value or subtype not in subtypes:
            continue
        try:
            confidence = max(0.0, min(1.0, float(item.get("confidence", 0.5))))
        except (TypeError, ValueError):
            confidence = 0.5

        verified = _found_in(original, chunk, haystack_squashed) or _found_in(
            value, chunk, haystack_squashed
        )
        if not verified:
            continue  # not traceable to the source — treat as hallucinated

        findings.append(
            Finding(
                category=category_id,
                subtype=subtype,
                value=value,
                original_form=original,
                confidence=confidence,
                reasoning=str(item.get("reasoning", "")).strip(),
                verified=True,
            )
        )
    return findings


def dedupe_findings(findings: list[Finding]) -> list[Finding]:
    """Collapse duplicates across chunks, keeping the highest-confidence copy."""
    best: dict[tuple, Finding] = {}
    for f in findings:
        key = (f.category, f.subtype, f.value.lower())
        if key not in best or f.confidence > best[key].confidence:
            best[key] = f
    return sorted(best.values(), key=lambda f: (f.category, f.subtype, -f.confidence))
