from __future__ import annotations

import hashlib

import pytest

from app.schemas.match import MatchResult
from app.utils.hash_utils import sha256_bytes
from app.utils.json_utils import parse_json_object
from app.utils.regex_utils import extract_contacts, extract_email, extract_phone
from app.utils.skill_normalizer import normalize_skill, skill_match
from app.utils.text_utils import clean_text


def test_text_cleaning_preserves_paragraphs() -> None:
    raw = "  教育经历\r\n\r\n\r\n 北京大学   计算机\t本科 \x00\r工作经历  "
    assert clean_text(raw) == "教育经历\n\n北京大学 计算机 本科\n工作经历"


def test_sha256_file_hash() -> None:
    content = b"resume-pdf-content"
    assert sha256_bytes(content) == hashlib.sha256(content).hexdigest()


def test_phone_and_email_regex_extraction() -> None:
    phone, email = extract_contacts("联系 138-0013-8000，邮箱 Candidate.Test+job@example.com")
    assert phone == "138-0013-8000"
    assert email == "Candidate.Test+job@example.com"
    assert extract_phone("no phone") is None
    assert extract_email("bad@example") is None


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("SpringBoot", "spring boot"),
        ("Spring Boot", "spring boot"),
        ("JS", "javascript"),
        ("TS", "typescript"),
        ("Postgres", "postgresql"),
        ("K8s", "kubernetes"),
        ("AI", "artificial intelligence"),
        ("ML", "machine learning"),
    ],
)
def test_skill_normalization(raw: str, expected: str) -> None:
    assert normalize_skill(raw) == expected


def test_skill_match_rate_uses_aliases_and_ignores_case() -> None:
    matched, missing, score = skill_match(
        ["Spring Boot", "PostgreSQL", "Kubernetes", "TypeScript"],
        ["SPRINGBOOT", "postgres", "k8s"],
    )
    assert matched == ["kubernetes", "postgresql", "spring boot"]
    assert missing == ["typescript"]
    assert score == 75.0


def test_all_match_scores_are_clamped_to_boundaries() -> None:
    result = MatchResult(
        overallScore=120,
        skillScore=-5,
        experienceScore=101,
        projectScore=50,
        educationScore=80,
        aiScore=-1,
        summary="test",
        recommendationLevel="test",
    )
    assert result.overallScore == 100
    assert result.skillScore == 0
    assert result.experienceScore == 100
    assert result.aiScore == 0


def test_markdown_wrapped_ai_json_is_parsed() -> None:
    raw = '```json\n{"name": "张三", "skills": ["Python"],}\n```'
    assert parse_json_object(raw) == {"name": "张三", "skills": ["Python"]}


def test_illegal_ai_json_fails_safely() -> None:
    with pytest.raises(ValueError, match="valid JSON"):
        parse_json_object("I cannot provide structured output")

