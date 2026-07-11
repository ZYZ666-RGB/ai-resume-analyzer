from __future__ import annotations

import re
import unicodedata


def clean_text(text: str) -> str:
    """Normalize PDF text while preserving meaningful paragraph boundaries."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = unicodedata.normalize("NFKC", text)
    text = "".join(
        char
        for char in text
        if char in {"\n", "\t"} or unicodedata.category(char) not in {"Cc", "Cf"}
    )
    text = text.replace("\t", " ")
    lines = [re.sub(r"[ \u00a0]+", " ", line).strip() for line in text.split("\n")]
    text = "\n".join(lines)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def compact_for_matching(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().casefold()

