"""loaders.csv_loader
CSV loader. Cell values are kept verbatim (one row per line, cells joined
with " | ") so the hallucination guardrail's substring check still finds
extracted values in the loaded text.
"""

import csv

from app.loaders.base import BaseLoader


class CsvLoader(BaseLoader):
    format_name = "csv"
    extensions = (".csv", ".tsv")

    def load(self, filepath: str) -> str:
        with open(filepath, "r", encoding="utf-8", errors="replace", newline="") as f:
            sample = f.read(4096)
            f.seek(0)
            try:
                dialect = csv.Sniffer().sniff(sample)
            except csv.Error:
                dialect = csv.excel
            reader = csv.reader(f, dialect)
            return "\n".join(" | ".join(row) for row in reader)
