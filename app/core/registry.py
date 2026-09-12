"""core.registry
The extractor and loader registry lists. This is the only file touched
when a new category or file format is added (one import + one list entry).
"""

import os

from app.extractors.credentials_extractor import CredentialsExtractor
from app.extractors.forensic_extractor import ForensicExtractor
from app.extractors.ioc_extractor import IocExtractor
from app.extractors.network_extractor import NetworkExtractor
from app.extractors.pii_extractor import PiiExtractor
from app.loaders.csv_loader import CsvLoader
from app.loaders.docx_loader import DocxLoader
from app.loaders.pdf_loader import PdfLoader
from app.loaders.txt_loader import TxtLoader

EXTRACTORS = [
    IocExtractor(),
    PiiExtractor(),
    CredentialsExtractor(),
    NetworkExtractor(),
    ForensicExtractor(),
]


def get_extractors(category_ids: list[str]):
    """Resolve requested category ids to extractor instances (unknown ids ignored)."""
    return [ex for ex in EXTRACTORS if ex.category_id in category_ids]


def supported_categories():
    return [{"id": ex.category_id, "label": ex.label} for ex in EXTRACTORS]

LOADERS = [
    TxtLoader(),
    PdfLoader(),
    DocxLoader(),
    CsvLoader(),
]


def get_loader(filepath: str, format_override: str = None):
    """Pick a loader by explicit format override, else by file extension.

    Falls back to the plain-text loader when nothing matches, so unknown
    text-like files still flow through the pipeline.
    """
    if format_override and format_override != "auto":
        for loader in LOADERS:
            if loader.format_name == format_override:
                return loader
        raise ValueError(f"No loader registered for format '{format_override}'")

    extension = os.path.splitext(filepath)[1]
    for loader in LOADERS:
        if loader.handles_extension(extension):
            return loader
    return LOADERS[0]  # TxtLoader fallback


def supported_formats():
    return [loader.format_name for loader in LOADERS]
