import re
import unicodedata
from typing import Tuple, Optional

class BaseParser:
    """Base class for all stat block parsers."""

    @staticmethod
    def normalize_text(text: str) -> str:
        """Strip text and remove non-breaking spaces."""
        return unicodedata.normalize('NFKC', text).strip()

    @staticmethod
    def split_name_description(text: str) -> Tuple[str, str]:
        """Split text into name and description based on first period or colon."""
        parts = re.split(r'[\.:]', text, maxsplit=1)
        if len(parts) == 2:
            return parts[0].strip(), parts[1].strip()
        return text.strip(), ""

    @staticmethod
    def extract_parenthetical(text: str) -> Tuple[str, Optional[str]]:
        """Extract text within parentheses from a string."""
        match = re.search(r'(.*?)\s*\((.*?)\)\s*(.*)$', text)
        if match:
            return (match.group(1) + ' ' + match.group(3)).strip(), match.group(2)
        return text.strip(), None
