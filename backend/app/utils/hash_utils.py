import hashlib
import json
from typing import Any


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def sha256_text(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def sha256_canonical_json(value: Any) -> str:
    """Hash JSON-compatible data without depending on mapping insertion order.

    Compact JSON still preserves field boundaries, so inputs such as
    ``{"title": "ab", "description": "c"}`` and
    ``{"title": "a", "description": "bc"}`` cannot collapse to the same
    preimage as they do when the two strings are concatenated directly.
    """

    canonical = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    return sha256_text(canonical)


def sha256_job_description(job_title: str, job_description: str) -> str:
    """Return a stable, boundary-safe hash for a validated job description."""

    return sha256_canonical_json(
        {"jobDescription": job_description, "jobTitle": job_title}
    )
