export const JOB_TITLE_MAX_LENGTH = 120
export const JOB_DESCRIPTION_MIN_LENGTH = 10
export const JOB_DESCRIPTION_MAX_LENGTH = 5000

export const SAMPLE_JOB = {
  title: 'Python AI 应用工程师',
  description: `岗位职责：
1. 负责基于 Python 与 FastAPI 的 AI 应用和后端服务设计、开发及性能优化；
2. 结合大语言模型完成提示词设计、RAG 检索、结构化信息提取与评测体系建设；
3. 参与 RESTful API、异步任务、Redis 缓存及云端部署方案建设；
4. 与产品、前端和算法团队协作，推动 AI 能力在真实业务场景稳定落地。

任职要求：
1. 本科及以上学历，计算机或相关专业，3 年以上 Python 开发经验；
2. 熟悉 Python、FastAPI、Pydantic、Redis、PostgreSQL，具备良好的工程化能力；
3. 有通义千问、OpenAI 或其他大模型 API 接入经验，理解 Prompt Engineering 与 RAG；
4. 熟悉 Docker、Git、Linux，了解云原生或 Serverless 部署；
5. 具备良好的沟通能力、问题分析能力和隐私安全意识。

加分项：有 Vue 3 前端经验、AI 应用效果评测经验或招聘科技领域项目经验。`,
}

export function canAnalyze({ file, jobTitle, jobDescription, isSubmitting = false }) {
  const titleLength = String(jobTitle ?? '').trim().length
  const descriptionLength = String(jobDescription ?? '').trim().length
  return Boolean(file) &&
    titleLength >= 1 &&
    titleLength <= JOB_TITLE_MAX_LENGTH &&
    descriptionLength >= JOB_DESCRIPTION_MIN_LENGTH &&
    descriptionLength <= JOB_DESCRIPTION_MAX_LENGTH &&
    !isSubmitting
}
