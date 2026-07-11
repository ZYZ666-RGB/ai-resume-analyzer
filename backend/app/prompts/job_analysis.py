def build_job_prompt(job_title: str, description: str) -> str:
    return f"""
你是招聘岗位信息抽取器。只能依据岗位名称和描述抽取，不得补充未出现的要求。
只返回一个合法 JSON 对象，禁止 Markdown。结构必须是：
{{
  "jobTitle": "{job_title}",
  "coreSkills": [],
  "bonusSkills": [],
  "educationRequirement": null,
  "workYearsRequirement": null,
  "responsibilities": [],
  "industry": null,
  "otherRequirements": []
}}

岗位名称：{job_title}
岗位描述：
{description[:20000]}
""".strip()

