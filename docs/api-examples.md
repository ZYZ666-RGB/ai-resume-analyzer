# API 调用示例

默认本地地址为 `http://localhost:8000`。以下示例用于手工联调，字段的最终权威定义以运行中的 `http://localhost:8000/docs` 和 OpenAPI schema 为准。示例中的姓名、联系方式和 ID 均为虚构/占位内容。

## 1. 通用约定

成功响应：

```json
{
  "code": 200,
  "message": "success",
  "data": {}
}
```

失败响应：

```json
{
  "code": 400,
  "message": "请求参数错误",
  "data": null
}
```

- `Content-Type: application/json` 用于 `/match`。
- `multipart/form-data` 用于上传；让 curl 或浏览器自动生成 boundary，不要手写。
- 默认单文件上限 10 MB，仅支持具有可提取文本层的 PDF。
- `/parse` 的 `cacheHit` 表示解析缓存命中，`/match`/`/analyze` 的 `cacheHit` 表示完整岗位匹配缓存命中；它们都不表示数据永久保存。

## 2. 健康检查

```bash
curl -i http://localhost:8000/api/health
```

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "status": "ok",
    "service": "ai-resume-analyzer"
  }
}
```

健康接口用于进程/HTTP 存活检查，不应因 Redis 暂时不可用而把整个服务标记为不可用；若实现了依赖状态，应区分 `ok` 与 `degraded`。

## 3. 解析简历

```bash
curl -X POST "http://localhost:8000/api/resumes/parse" \
  -H "Accept: application/json" \
  -F "file=@./resume.pdf;type=application/pdf"
```

响应示意：

```json
{
  "code": 200,
  "message": "简历解析成功",
  "data": {
    "resumeId": "res_2f1c...full-sha256",
    "resumeHash": "2f1c...full-sha256",
    "pageCount": 2,
    "cleanedText": null,
    "resume": {
      "basicInfo": {
        "name": "示例候选人",
        "phone": "13800000000",
        "email": "candidate@example.com",
        "address": null
      },
      "jobInfo": {
        "jobIntention": "Python 开发工程师",
        "expectedSalary": null
      },
      "background": {
        "workYears": 3,
        "education": [
          {
            "school": "示例大学",
            "major": "计算机科学与技术",
            "degree": "本科",
            "startDate": "2018-09",
            "endDate": "2022-06"
          }
        ],
        "workExperiences": [],
        "skills": ["Python", "FastAPI", "Redis"],
        "projects": [],
        "certificates": []
      }
    },
    "cacheHit": false
  }
}
```

`RETURN_CLEANED_TEXT` 安全默认值为 `false`，因此 `cleanedText` 为 `null`；仅本地调试显式设为 `true` 时返回正文。`resumeHash` 和 `resumeId` 仍是可关联标识，不应写入公开分析平台。PDF 默认同时受 10 MB 与 50 页上限保护。

## 4. 使用解析结果匹配岗位

先调用 `/parse` 获取 `resumeId`，再调用：

```bash
curl -X POST "http://localhost:8000/api/resumes/match" \
  -H "Content-Type: application/json" \
  -d '{
    "resumeId": "res_2f1c...full-sha256",
    "jobTitle": "Python AI 应用工程师",
    "jobDescription": "负责 FastAPI 服务和大模型应用开发；要求熟悉 Python、Redis、Docker，有 3 年以上相关经验。"
  }'
```

Windows PowerShell 可使用：

```powershell
$body = @{
  resumeId = "res_2f1c...full-sha256"
  jobTitle = "Python AI 应用工程师"
  jobDescription = "负责 FastAPI 服务和大模型应用开发；要求熟悉 Python、Redis、Docker，有 3 年以上相关经验。"
} | ConvertTo-Json

Invoke-RestMethod -Method Post `
  -Uri "http://localhost:8000/api/resumes/match" `
  -ContentType "application/json" `
  -Body $body
```

响应示意：

```json
{
  "code": 200,
  "message": "匹配分析成功",
  "data": {
    "resumeId": "res_2f1c...full-sha256",
    "job": {
      "jobTitle": "Python AI 应用工程师",
      "coreSkills": ["python", "fastapi", "redis", "docker"],
      "bonusSkills": [],
      "educationRequirement": null,
      "workYearsRequirement": 3,
      "responsibilities": [],
      "industry": null,
      "otherRequirements": []
    },
    "match": {
      "overallScore": 82,
      "skillScore": 90,
      "experienceScore": 80,
      "projectScore": 75,
      "educationScore": 80,
      "aiScore": 80,
      "aiUsed": true,
      "analysisMode": "ai",
      "warnings": null,
      "matchedKeywords": ["python", "fastapi", "redis"],
      "missingKeywords": ["docker"],
      "advantages": ["后端技术栈与岗位核心要求相符"],
      "risks": ["简历未提供容器生产运维证据"],
      "summary": "具备主要后端能力，建议人工核验项目深度。",
      "recommendationLevel": "较为匹配"
    },
    "cacheHit": false
  }
}
```

如果版本化解析缓存过期且服务内也没有相应记录，`resumeId` 无法还原原简历，应返回 404；客户端需提示重新上传，而不是永久依赖该 ID。未配置 AI 或模型正文未通过校验时，匹配结果会返回 `aiUsed=false`、`analysisMode="rules"` 和告警，前端应显示“规则回退分”。

## 5. 一次性完整分析

这是前端主调用：

```bash
curl -X POST "http://localhost:8000/api/resumes/analyze" \
  -H "Accept: application/json" \
  -F "file=@./resume.pdf;type=application/pdf" \
  -F "jobTitle=Python AI 应用工程师" \
  -F "jobDescription=负责 FastAPI 服务和大模型应用开发；要求熟悉 Python、Redis、Docker，有 3 年以上相关经验。"
```

响应将包含解析信息、岗位结构化结果、AI 参与状态、分项匹配结果和 `cacheHit`。岗位名称限制 1～120 字符，JD 限制 10～5000 字符；JSON 与 multipart 接口使用同一后端策略。同一 PDF 字节、岗位标题和 JD 再次提交时通常命中版本化匹配缓存；若 Redis 被禁用或不可用，则正常重新分析并返回 `cacheHit: false`。

## 6. 浏览器 Axios 示例

```js
import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 120_000,
})

export async function analyzeResume(file, jobTitle, jobDescription) {
  const form = new FormData()
  form.append('file', file)
  form.append('jobTitle', jobTitle)
  form.append('jobDescription', jobDescription)

  const response = await api.post('/api/resumes/analyze', form)
  return response.data.data
}
```

不要在浏览器代码中设置百炼 API Key。上传时不必手写 multipart boundary。

## 7. 常见错误示例

### 非 PDF

```bash
curl -X POST "http://localhost:8000/api/resumes/parse" \
  -F "file=@./notes.txt;type=text/plain"
```

```http
HTTP/1.1 400 Bad Request
Content-Type: application/json

{"code":400,"message":"仅支持 PDF 格式文件","data":null}
```

### 超过大小上限

```http
HTTP/1.1 413 Payload Too Large
Content-Type: application/json

{"code":413,"message":"上传文件不能超过 10MB","data":null}
```

### 空或过短 JD

```http
HTTP/1.1 400 Bad Request
Content-Type: application/json

{"code":400,"message":"岗位描述不能为空且至少需要 10 个字符","data":null}
```

### Schema 校验失败

```http
HTTP/1.1 422 Unprocessable Entity
Content-Type: application/json

{"code":422,"message":"请求数据校验失败","data":null}
```

### AI 上游失败或超时

```http
HTTP/1.1 502 Bad Gateway
Content-Type: application/json

{"code":502,"message":"AI 服务调用失败","data":null}
```

```http
HTTP/1.1 504 Gateway Timeout
Content-Type: application/json

{"code":504,"message":"AI 服务调用超时","data":null}
```

模型消息正文为非法 JSON 或未通过 Pydantic 校验时，当前服务回退到规则结果；网络错误、非成功 HTTP 状态和上游响应外壳异常才返回 502。错误响应不得包含 Python 堆栈、上游响应全文、API Key、Redis URL/密码或简历正文。

## 8. 手工联调顺序

1. 调 `/api/health` 确认 HTTP 和统一响应。
2. 用一个经过授权的最小文本型 PDF 调 `/parse`。
3. 用其 `resumeId` 调 `/match`，检查 0～100 分值和推荐边界。
4. 调 `/analyze`，检查组合返回能被前端展示。
5. 重复相同请求观察 `cacheHit`；关闭 Redis 后确认业务仍可运行。
6. 分别尝试伪 PDF、损坏 PDF、空文本 PDF、超限文件、空 JD 和无效 `resumeId`。
7. 查看日志确认只有脱敏元数据，没有全文、手机号、邮箱或密钥。
