"""extractors.base
Abstract base class all category extractors implement.

Adding a new category = create one extractor file in this package that
subclasses BaseExtractor (category_id, label, subtypes, guidance), then
add one instance to the EXTRACTORS list in app/core/registry.py.
The prompt text itself lives in app/core/prompts.py.
"""

from abc import ABC

from app.core.prompts import extraction_system_prompt


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
        return extraction_system_prompt(self.label, self.subtypes, self.guidance)
