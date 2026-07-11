def build_resume_prompt(resume_text: str) -> str:
    return f"""
你是严格的信息抽取器。只能依据提供的简历原文，不得推测或虚构。
无法确定的标量使用 null，无法确定的列表使用 []。只返回一个合法 JSON 对象，禁止 Markdown。
JSON 结构必须是：
{{
  "basicInfo": {{"name": null, "phone": null, "email": null, "address": null}},
  "jobInfo": {{"jobIntention": null, "expectedSalary": null}},
  "background": {{
    "workYears": null,
    "education": [{{"school": null, "major": null, "degree": null, "startDate": null, "endDate": null}}],
    "workExperiences": [{{"company": null, "position": null, "startDate": null, "endDate": null, "description": null}}],
    "skills": [],
    "projects": [{{"name": null, "role": null, "technologies": [], "description": null}}],
    "certificates": []
  }}
}}

简历原文：
{resume_text[:30000]}
""".strip()

