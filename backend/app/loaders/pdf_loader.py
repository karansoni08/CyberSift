"""loaders.pdf_loader
PDF loader backed by pdfplumber.
"""

import pdfplumber

from app.loaders.base import BaseLoader


class PdfLoader(BaseLoader):
    format_name = "pdf"
    extensions = (".pdf",)

    def load(self, filepath: str) -> str:
        pages = []
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    pages.append(text)
        return "\n\n".join(pages)
