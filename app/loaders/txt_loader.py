"""loaders.txt_loader
Plain-text loader. Also the fallback for unrecognized text-like files.
"""

from app.loaders.base import BaseLoader


class TxtLoader(BaseLoader):
    format_name = "txt"
    extensions = (".txt", ".log", ".md")

    def load(self, filepath: str) -> str:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
