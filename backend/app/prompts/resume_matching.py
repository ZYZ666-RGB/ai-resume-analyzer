import json

from app.schemas.job import JobAnalysis
from app.schemas.resume import StructuredResume


def build_match_prompt(resume: StructuredResume, job: JobAnalysis) -> str:
    resume_json = json.dumps(resume.model_dump(), ensure_ascii=False)
    job_json = json.dumps(job.model_dump(), ensure_ascii=False)
    return f"""
你是招聘辅助分析器。基于给定结构化简历和岗位要求，给出审慎的辅助评价。
不得虚构经历，不得输出年龄、性别等敏感属性判断。只返回合法 JSON，禁止 Markdown。
结构：{{"aiScore": 0, "advantages": [], "risks": [], "summary": ""}}
aiScore 必须在 0 到 100 之间。评价仅作为规则评分中 10% 的补充。

简历：{resume_json[:18000]}
岗位：{job_json[:10000]}
""".strip()

