"""loaders.base
Abstract base class all file-format loaders implement.

Adding a new input format = create one loader file in this package that
subclasses BaseLoader, then add one instance to the LOADERS list in
app/core/registry.py. Nothing in app/core/ changes.
"""

from abc import ABC, abstractmethod


class BaseLoader(ABC):
    # Value used by the chat bar's format-override dropdown (e.g. "pdf").
    format_name: str = ""

    # Lowercase file extensions (with dot) claimed on auto-detect.
    extensions: tuple = ()

    @abstractmethod
    def load(self, filepath: str) -> str:
        """Read the file at filepath and return its full text content."""
        raise NotImplementedError

    def handles_extension(self, extension: str) -> bool:
        return extension.lower() in self.extensions
