from __future__ import annotations

import re
from collections.abc import Iterable


SKILL_ALIASES: dict[str, set[str]] = {
    "java": {"java"},
    "python": {"python"},
    "go": {"golang", "go language", "go语言"},
    "c++": {"c++", "cpp"},
    "c#": {"c#", "csharp"},
    "javascript": {"javascript", "java script", "js"},
    "typescript": {"typescript", "type script", "ts"},
    "spring boot": {"springboot", "spring boot"},
    "spring cloud": {"springcloud", "spring cloud"},
    "fastapi": {"fastapi", "fast api"},
    "django": {"django"},
    "flask": {"flask"},
    "vue": {"vue", "vue.js", "vuejs", "vue 3", "vue3"},
    "react": {"react", "react.js", "reactjs"},
    "node.js": {"node", "node.js", "nodejs"},
    "mysql": {"mysql"},
    "postgresql": {"postgresql", "postgres", "postgre sql"},
    "redis": {"redis"},
    "mongodb": {"mongodb", "mongo db"},
    "elasticsearch": {"elasticsearch", "elastic search", "es"},
    "docker": {"docker"},
    "kubernetes": {"kubernetes", "k8s"},
    "linux": {"linux"},
    "git": {"git"},
    "aws": {"aws", "amazon web services"},
    "aliyun": {"aliyun", "阿里云"},
    "machine learning": {"machine learning", "ml", "机器学习"},
    "artificial intelligence": {"artificial intelligence", "ai", "人工智能"},
    "llm": {"llm", "large language model", "大语言模型"},
    "pytorch": {"pytorch", "torch"},
    "tensorflow": {"tensorflow"},
    "sql": {"sql"},
    "restful api": {"restful", "rest api", "restful api"},
    "microservices": {"microservice", "microservices", "微服务"},
    "apache kafka": {"apache kafka", "kafka"},
    "rabbitmq": {"rabbitmq", "rabbit mq"},
    "nginx": {"nginx"},
    "maven": {"maven"},
    "gradle": {"gradle"},
    "jenkins": {"jenkins"},
    "ci/cd": {"ci/cd", "cicd", "continuous integration"},
    "numpy": {"numpy"},
    "pandas": {"pandas"},
    "scikit-learn": {"scikit-learn", "sklearn"},
    "langchain": {"langchain", "lang chain"},
    "milvus": {"milvus"},
    "openai": {"openai", "open ai"},
    "qwen": {"qwen", "通义千问", "千问"},
    "prompt engineering": {"prompt engineering", "提示词工程"},
    "celery": {"celery"},
    "sqlalchemy": {"sqlalchemy", "sql alchemy"},
    "grpc": {"grpc"},
    "html": {"html", "html5"},
    "css": {"css", "css3"},
    "tailwind css": {"tailwind", "tailwindcss", "tailwind css"},
    "element plus": {"element plus", "element-plus"},
    "pytest": {"pytest"},
}


def _normalized_token(value: str) -> str:
    return re.sub(r"[\s._-]+", "", value.strip().casefold())


ALIAS_LOOKUP = {
    _normalized_token(alias): canonical
    for canonical, aliases in SKILL_ALIASES.items()
    for alias in aliases | {canonical}
}


def normalize_skill(skill: str) -> str:
    token = _normalized_token(skill)
    return ALIAS_LOOKUP.get(token, re.sub(r"\s+", " ", skill.strip().casefold()))


def normalize_skills(skills: Iterable[str]) -> list[str]:
    values = {normalize_skill(skill) for skill in skills if skill and skill.strip()}
    return sorted(values)


def extract_known_skills(text: str) -> list[str]:
    lowered = text.casefold()
    found: set[str] = set()
    for canonical, aliases in SKILL_ALIASES.items():
        for alias in aliases | {canonical}:
            escaped = re.escape(alias.casefold())
            if re.search(rf"(?<![a-z0-9+#]){escaped}(?![a-z0-9+#])", lowered):
                found.add(canonical)
                break
    return sorted(found)


def skill_match(required: Iterable[str], available: Iterable[str]) -> tuple[list[str], list[str], float]:
    required_set = set(normalize_skills(required))
    available_set = set(normalize_skills(available))
    matched = sorted(required_set & available_set)
    missing = sorted(required_set - available_set)
    score = 100.0 if not required_set else len(matched) / len(required_set) * 100
    return matched, missing, round(score, 1)
