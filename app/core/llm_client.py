"""core.llm_client
Thin async wrapper around the Anthropic SDK for extraction calls.

Each call sends one document chunk with one category's extraction prompt
and returns the parsed JSON list of raw findings. JSON parsing is
deliberately forgiving (the verifier is the real guardrail downstream).
"""

import asyncio
import json
import os
import re

from anthropic import AsyncAnthropic

DEFAULT_MODEL = "claude-sonnet-5"
MAX_CONCURRENT_CALLS = 4

_client: AsyncAnthropic | None = None
_semaphore: asyncio.Semaphore | None = None


def get_model() -> str:
    return os.environ.get("CYBERSIFT_MODEL", DEFAULT_MODEL)


def _get_client() -> AsyncAnthropic:
    global _client
    if _client is None:
        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set. Add it to the environment "
                "(Vercel: Project Settings > Environment Variables) and redeploy."
            )
        _client = AsyncAnthropic()
    return _client


def _get_semaphore() -> asyncio.Semaphore:
    global _semaphore
    if _semaphore is None:
        _semaphore = asyncio.Semaphore(MAX_CONCURRENT_CALLS)
    return _semaphore


def parse_json_array(raw: str) -> list[dict]:
    """Parse the model's response into a list of dicts.

    Accepts a bare JSON array, an array inside a ```json fence, or an
    object wrapping the array. Anything unparseable returns []."""
    raw = raw.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", raw, re.DOTALL)
    if fence:
        raw = fence.group(1).strip()
    if not raw.startswith(("[", "{")):
        bracket = raw.find("[")
        if bracket == -1:
            return []
        raw = raw[bracket:]
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        # Trailing junk after the array — cut at the last closing bracket.
        end = raw.rfind("]")
        if end == -1:
            return []
        try:
            data = json.loads(raw[: end + 1])
        except json.JSONDecodeError:
            return []
    if isinstance(data, dict):
        for value in data.values():
            if isinstance(value, list):
                data = value
                break
        else:
            return []
    if not isinstance(data, list):
        return []
    return [item for item in data if isinstance(item, dict)]


async def extract_from_chunk(system_prompt: str, chunk: str) -> list[dict]:
    """Run one extraction call: one category prompt over one text chunk."""
    client = _get_client()
    async with _get_semaphore():
        response = await client.messages.create(
            model=get_model(),
            max_tokens=8000,
            output_config={"effort": "low"},
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": (
                        "Document text:\n<document>\n" + chunk + "\n</document>\n\n"
                        "Return the JSON array of findings now."
                    ),
                }
            ],
        )
    if response.stop_reason == "refusal":
        return []
    text = "".join(block.text for block in response.content if block.type == "text")
    return parse_json_array(text)
