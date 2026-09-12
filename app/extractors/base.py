"""extractors.base
Abstract base class all category extractors implement.

Adding a new category = create one extractor file in this package that
subclasses BaseExtractor (category_id, label, subtypes, guidance), then
add one instance to the EXTRACTORS list in app/core/registry.py.
"""

from abc import ABC

_OUTPUT_CONTRACT = """
Output contract — follow it exactly:
- Respond with ONLY a JSON array, no prose before or after it.
- Each element: {"value": str, "original_form": str, "subtype": str, "confidence": float, "reasoning": str}
- "original_form" MUST be copied character-for-character from the document text — it is
  checked as an exact substring of the source, and findings that fail that check are discarded.
- "value" is the normalized form: refang defanged indicators (hxxp -> http, [.] -> ., [@] -> @,
  remove spaces inserted to break up a value), strip surrounding quotes/brackets, otherwise
  keep it identical to original_form.
- "subtype" MUST be one of the listed subtypes.
- "confidence" is 0.0–1.0: how certain you are this is a true item of this category in context
  (not an example, not documentation boilerplate, not a field label).
- "reasoning" is one short sentence citing the surrounding context.
- Do NOT invent, complete, or guess values that are not present in the document.
- Do NOT extract values that appear only as schema examples, placeholders (e.g. example.com
  used as a placeholder, 127.0.0.1 in a config template), or column headers — unless the
  document is itself reporting on them as real observations.
- If the document contains nothing relevant, respond with [].
""".strip()


class BaseExtractor(ABC):
    # Stable id used by the API and the frontend category chips (e.g. "ioc").
    category_id: str = ""
    # Human label (e.g. "IOC").
    label: str = ""
    # Allowed subtype strings for this category.
    subtypes: tuple = ()
    # Category-specific extraction guidance inserted into the system prompt.
    guidance: str = ""

    def system_prompt(self) -> str:
        subtype_list = "\n".join(f"- {s}" for s in self.subtypes)
        return (
            f"You are the {self.label} extraction engine of CyberSift, a security "
            "data-extraction tool used by security analysts to process reports, logs, "
            "and case files they are authorized to analyze.\n\n"
            f"Task: read the document text and extract every {self.label} item that "
            "actually appears in it.\n\n"
            f"Allowed subtypes:\n{subtype_list}\n\n"
            f"Category guidance:\n{self.guidance.strip()}\n\n"
            f"{_OUTPUT_CONTRACT}"
        )
