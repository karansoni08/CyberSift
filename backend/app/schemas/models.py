"""schemas.models
Pydantic models shared by the pipeline and the API layer.
"""

from pydantic import BaseModel, Field


class Finding(BaseModel):
    """One extracted item, in normalized form plus how it appeared in the source."""

    category: str
    subtype: str
    value: str
    original_form: str
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str = ""
    severity: str | None = None  # anomaly category only: high | medium | low
    verified: bool = True


class CategoryResult(BaseModel):
    category: str
    findings: list[Finding]
    error: str | None = None


class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class ChatDocument(BaseModel):
    filename: str | None = None
    text: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    document: ChatDocument | None = None


class ExtractionResponse(BaseModel):
    filename: str | None = None
    format_used: str | None = None
    characters: int
    chunks: int
    categories: list[str]
    findings: list[Finding]
    summary: str
    errors: list[str] = []
