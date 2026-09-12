"""core.agent
The conversational agent behind /api/chat: a manual tool-use loop.

Each turn: send history + tools, execute any tool calls Claude makes,
feed results back, repeat until Claude answers in text (or the loop
cap is hit). Findings returned by extraction tool calls are collected
so the UI can render them richly.
"""

import json

from app.core.llm_client import get_async_client, get_model
from app.core.prompts import CHAT_SYSTEM_PROMPT
from app.core.tools import TOOL_DEFINITIONS, run_tool

MAX_TOOL_ROUNDS = 5


async def run_chat(messages: list[dict], document: dict | None) -> dict:
    """messages: [{"role": "user"|"assistant", "content": str}, ...]
    document: {"filename": str, "text": str} or None.
    Returns {"reply": str, "findings": [...], "tool_calls": [...], "summary": str|None}.
    """
    client = get_async_client()

    system = CHAT_SYSTEM_PROMPT
    if document and document.get("text", "").strip():
        system += (
            f"\n\nA document is currently attached: \"{document.get('filename') or 'pasted text'}\" "
            f"({len(document['text'])} characters). Use the tools to inspect or extract from it."
        )
    else:
        system += "\n\nNo document is currently attached to this conversation."

    convo = [{"role": m["role"], "content": m["content"]} for m in messages]
    collected_findings: list[dict] = []
    tool_calls_made: list[str] = []
    last_summary = None

    for _ in range(MAX_TOOL_ROUNDS):
        response = await client.messages.create(
            model=get_model(),
            max_tokens=4000,
            output_config={"effort": "low"},
            system=system,
            tools=TOOL_DEFINITIONS,
            messages=convo,
        )

        if response.stop_reason != "tool_use":
            reply = "".join(b.text for b in response.content if b.type == "text")
            if response.stop_reason == "refusal" and not reply:
                reply = "I can't help with that request."
            return {
                "reply": reply,
                "findings": collected_findings,
                "tool_calls": tool_calls_made,
                "summary": last_summary,
            }

        # Execute every tool call in this assistant turn, reply with all results at once.
        convo.append({"role": "assistant", "content": response.content})
        results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            tool_calls_made.append(block.name)
            result_json = await run_tool(block.name, block.input, document)
            try:
                parsed = json.loads(result_json)
                if isinstance(parsed, dict):
                    if isinstance(parsed.get("findings"), list):
                        collected_findings = parsed["findings"]
                    if parsed.get("summary"):
                        last_summary = parsed["summary"]
            except json.JSONDecodeError:
                pass
            results.append(
                {"type": "tool_result", "tool_use_id": block.id, "content": result_json}
            )
        convo.append({"role": "user", "content": results})

    return {
        "reply": "I hit the tool-call limit for one turn. Here is what I have so far: "
        + (last_summary or "no completed extraction."),
        "findings": collected_findings,
        "tool_calls": tool_calls_made,
        "summary": last_summary,
    }
