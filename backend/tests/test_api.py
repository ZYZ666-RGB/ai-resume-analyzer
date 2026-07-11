from __future__ import annotations


def test_health_check(client) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {
        "code": 200,
        "message": "success",
        "data": {"status": "ok", "service": "ai-resume-analyzer"},
    }


def test_parse_rejects_non_pdf_file(client) -> None:
    response = client.post(
        "/api/resumes/parse",
        files={"file": ("resume.txt", b"not a pdf", "text/plain")},
    )
    assert response.status_code == 400
    assert response.json()["data"] is None
    assert "PDF" in response.json()["message"]


def test_parse_rejects_spoofed_or_corrupt_pdf(client) -> None:
    response = client.post(
        "/api/resumes/parse",
        files={"file": ("resume.pdf", b"%PDF-corrupt", "application/pdf")},
    )
    assert response.status_code == 400
    assert response.json()["code"] == 400


def test_parse_rejects_multiple_files(client, make_pdf) -> None:
    pdf = make_pdf(["Python resume"])
    response = client.post(
        "/api/resumes/parse",
        files=[
            ("file", ("one.pdf", pdf, "application/pdf")),
            ("file", ("two.pdf", pdf, "application/pdf")),
        ],
    )
    assert response.status_code == 400
    assert "只能上传一个" in response.json()["message"]


def test_parse_rejects_pdf_without_extractable_text(client, make_pdf) -> None:
    response = client.post(
        "/api/resumes/parse",
        files={"file": ("blank.pdf", make_pdf([""]), "application/pdf")},
    )
    assert response.status_code == 400
    assert "没有可提取文本" in response.json()["message"]


def test_parse_rejects_file_over_default_size_limit(client) -> None:
    oversized = b"%PDF-" + b"0" * (10 * 1024 * 1024 + 1)
    response = client.post(
        "/api/resumes/parse",
        files={"file": ("large.pdf", oversized, "application/pdf")},
    )
    assert response.status_code == 413
    assert response.json()["code"] == 413


def test_parse_and_match_rule_fallback(client, make_pdf) -> None:
    pdf = make_pdf(
        [
            "Zhang San\nPhone: 13800138000\nEmail: zhang@example.com\n"
            "5 years experience\nPython FastAPI Redis PostgreSQL Docker",
            "Education\nExample University Bachelor\nProject: REST API with Python and Redis",
        ]
    )
    parsed_response = client.post(
        "/api/resumes/parse",
        files={"file": ("resume.pdf", pdf, "application/pdf")},
    )
    assert parsed_response.status_code == 200
    parsed = parsed_response.json()["data"]
    assert parsed["pageCount"] == 2
    assert parsed["resumeId"].startswith("res_")
    assert len(parsed["resumeHash"]) == 64
    assert "python" in parsed["resume"]["background"]["skills"]

    matched_response = client.post(
        "/api/resumes/match",
        json={
            "resumeId": parsed["resumeId"],
            "jobTitle": "Python 后端工程师",
            "jobDescription": "负责使用 Python、FastAPI、Redis 和 PostgreSQL 开发后端服务，本科及以上。",
        },
    )
    assert matched_response.status_code == 200
    data = matched_response.json()["data"]
    assert data["resumeId"] == parsed["resumeId"]
    assert 0 <= data["match"]["overallScore"] <= 100
    assert "python" in data["match"]["matchedKeywords"]
    assert data["cacheHit"] is False


def test_analyze_combined_endpoint_contract(client, make_pdf) -> None:
    pdf = make_pdf(["Li Ming\nPython Django MySQL Docker\nli@example.com\n13900139000"])
    response = client.post(
        "/api/resumes/analyze",
        files={"file": ("resume.pdf", pdf, "application/pdf")},
        data={
            "jobTitle": "Python 工程师",
            "jobDescription": "负责 Python、Django、MySQL 后端系统设计开发和维护，熟悉 Docker。",
        },
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert {
        "resumeId",
        "pageCount",
        "resumeHash",
        "cleanedText",
        "resume",
        "job",
        "match",
        "cacheHit",
    } <= data.keys()
    assert data["job"]["jobTitle"] == "Python 工程师"


def test_empty_job_description_returns_parameter_error(client) -> None:
    response = client.post(
        "/api/resumes/match",
        json={"resumeId": "missing", "jobTitle": "Engineer", "jobDescription": ""},
    )
    assert response.status_code == 400
    assert response.json()["data"] is None
