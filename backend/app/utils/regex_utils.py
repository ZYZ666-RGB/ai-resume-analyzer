from __future__ import annotations

import re

EMAIL_PATTERN = re.compile(r"(?<![\w.+-])[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}(?![\w.-])", re.I)
PHONE_PATTERNS = (
    re.compile(r"(?<!\d)(?:\+?86[-\s]?)?1[3-9]\d(?:[-\s]?\d{4}){2}(?!\d)"),
    re.compile(r"(?<!\d)\+?\d{1,3}[-\s]?(?:\(?\d{2,4}\)?[-\s]?){2,4}\d{2,4}(?!\d)"),
)


def extract_email(text: str) -> str | None:
    match = EMAIL_PATTERN.search(text)
    return match.group(0) if match else None


def extract_phone(text: str) -> str | None:
    for pattern in PHONE_PATTERNS:
        match = pattern.search(text)
        if match:
            phone = re.sub(r"\s+", "", match.group(0))
            return phone
    return None


def extract_contacts(text: str) -> tuple[str | None, str | None]:
    return extract_phone(text), extract_email(text)

