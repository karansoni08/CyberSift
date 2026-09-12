"""core.chunker
Splits loaded document text into overlapping chunks sized for one LLM call.

Chunks break on line boundaries where possible so values (URLs, hashes,
key material) are not cut in half, and overlap so items spanning a
boundary are still seen whole by at least one call.
"""

MAX_CHUNK_CHARS = 12_000
OVERLAP_CHARS = 400
MAX_TEXT_CHARS = 120_000  # hard cap on total input per request


def chunk_text(text: str) -> list[str]:
    text = text[:MAX_TEXT_CHARS]
    if len(text) <= MAX_CHUNK_CHARS:
        return [text] if text.strip() else []

    chunks = []
    start = 0
    while start < len(text):
        end = min(start + MAX_CHUNK_CHARS, len(text))
        if end < len(text):
            # Prefer to break at the last newline inside the window.
            newline = text.rfind("\n", start + MAX_CHUNK_CHARS // 2, end)
            if newline != -1:
                end = newline
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk)
        if end >= len(text):
            break
        start = max(end - OVERLAP_CHARS, start + 1)
    return chunks
