from __future__ import annotations

import ast
import json
import re
from typing import Any


def _find_balanced_object(text: str) -> str | None:
    start = text.find("{")
    if start < 0:
        return None
    depth = 0
    in_string = False
    escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if escaped:
            escaped = False
            continue
        if char == "\\" and in_string:
            escaped = True
            continue
        if char == '"':
            in_string = not in_string
        elif not in_string:
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    return text[start : index + 1]
    return None


def parse_json_object(raw: str) -> dict[str, Any]:
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError("AI response is empty")
    cleaned = raw.strip().replace("“", '"').replace("”", '"')
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.I)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    candidates = [cleaned]
    balanced = _find_balanced_object(cleaned)
    if balanced and balanced != cleaned:
        candidates.append(balanced)
    for candidate in candidates:
        repaired = re.sub(r",\s*([}\]])", r"\1", candidate)
        try:
            value = json.loads(repaired)
        except json.JSONDecodeError:
            try:
                value = ast.literal_eval(repaired)
            except (ValueError, SyntaxError):
                continue
        if isinstance(value, dict):
            return value
    raise ValueError("AI response does not contain a valid JSON object")

