"""core.tools
The tools the CyberSift chat agent can call. Each tool has a JSON-schema
definition (sent to the model) and an async implementation that runs
against the document attached to the current chat request.

Adding a tool = add one definition to TOOL_DEFINITIONS and one entry to
TOOL_HANDLERS.
"""

import json

from app.core.chunker import chunk_text
from app.core.pipeline import build_summary, run_extraction
from app.core.registry import get_extractors, supported_categories, supported_formats

TOOL_DEFINITIONS = [
    {
        "name": "extract_security_data",
        "description": (
            "Run CyberSift's verified extraction pipeline over the document attached to "
            "this conversation. Returns findings as JSON: each has category, subtype, "
            "normalized value, original_form as it appeared in the source, confidence "
            "(0-1), and reasoning. Only call when a document is attached."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "categories": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["ioc", "pii", "creds", "network", "forensic", "anomaly"],
                    },
                    "description": "Which extraction categories to run.",
                }
            },
            "required": ["categories"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "name": "get_document_info",
        "description": (
            "Get metadata about the document attached to this conversation: filename, "
            "character count, how many chunks it will be processed in, and a preview of "
            "its first 1500 characters. Use this to check what is attached before "
            "extracting, or to answer questions about the document itself."
        ),
        "input_schema": {"type": "object", "properties": {}, "additionalProperties": False},
        "strict": True,
    },
    {
        "name": "get_capabilities",
        "description": (
            "List CyberSift's supported file formats and extraction categories with "
            "their ids and labels. Use when the user asks what the tool can do."
        ),
        "input_schema": {"type": "object", "properties": {}, "additionalProperties": False},
        "strict": True,
    },
]


async def _extract_security_data(document: dict | None, tool_input: dict) -> dict:
    if not document or not document.get("text", "").strip():
        return {"error": "No document is attached to this conversation. Ask the user to attach a file or paste report text."}
    extractors = get_extractors(tool_input.get("categories", []))
    if not extractors:
        return {"error": "No valid categories requested."}
    findings, errors, chunks = await run_extraction(document["text"], extractors)
    selected = [ex.category_id for ex in extractors]
    return {
        "summary": build_summary(findings, selected, errors),
        "chunks_processed": chunks,
        "errors": errors,
        "findings": [f.model_dump() for f in findings],
    }


async def _get_document_info(document: dict | None, tool_input: dict) -> dict:
    if not document or not document.get("text", "").strip():
        return {"attached": False}
    text = document["text"]
    return {
        "attached": True,
        "filename": document.get("filename"),
        "characters": len(text),
        "chunks": len(chunk_text(text)),
        "preview": text[:1500],
    }


async def _get_capabilities(document: dict | None, tool_input: dict) -> dict:
    return {"formats": supported_formats(), "categories": supported_categories()}


TOOL_HANDLERS = {
    "extract_security_data": _extract_security_data,
    "get_document_info": _get_document_info,
    "get_capabilities": _get_capabilities,
}


async def run_tool(name: str, tool_input: dict, document: dict | None) -> str:
    """Execute one tool call and return its result as a JSON string."""
    handler = TOOL_HANDLERS.get(name)
    if handler is None:
        return json.dumps({"error": f"Unknown tool: {name}"})
    try:
        return json.dumps(await handler(document, tool_input))
    except Exception as exc:
        return json.dumps({"error": f"Tool failed: {exc}"})
