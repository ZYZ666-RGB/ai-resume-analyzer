# 全面代码审查与交付评估报告

审查日期：2026-07-12
审查对象：`ai-resume-analyzer` 当前 `main` 分支（提交 `37c43a0`）
审查原则：结论以源码、配置、测试、构建和本地运行证据为准，不以 README 声明替代实现。

> 修复说明（2026-07-12）：本报告保留为提交 `37c43a0` 的审查基线，不回写历史判断。报告列出的 P1 已在后续工作区修复；修复后的权威状态、测试数字和仍需账号完成的 P0/P2 见 [acceptance-checklist.md](acceptance-checklist.md)。

## 1. 结论摘要

项目的核心业务链路已经实现，代码运行层面没有 P0：单份 PDF 上传、多页文本提取、文本清洗、结构化简历抽取、JD 分析、规则与 AI 混合评分、Redis 可降级缓存、统一响应和 Vue 可视化页面均有真实代码。后端 30 项测试、前端生产构建、Compose 配置、Docker 镜像构建和容器健康检查均已通过。

当前不建议立即向招聘方提交，原因不是主程序不可运行，而是两项硬性交付仍无法验收：仓库没有 Git remote，README 的 GitHub、前端演示和 FC 地址仍为占位；真实百炼、真实 Redis 缓存命中、FC/Vercel 公网联调和远端 GitHub Actions 状态也未验证。完成公开部署、替换链接并补做端到端检查后，建议提交。

模拟得分：**82 / 100**。这是“代码质量较好、交付外部状态未完成”的项目，而不是需要从零重做的项目。

## 2. 审查范围与可复现证据

| 验证项 | 结果 | 证据/说明 |
| --- | --- | --- |
| Git 状态 | 通过 | 当前分支 `main`，1 个提交，工作区审查前干净；仅 1 名贡献者，历史不足以分析热点 |
| 后端测试 | 通过 | `backend/.venv/Scripts/python.exe -m pytest`：30 passed |
| 前端构建 | 通过 | `npm run build`：75 modules transformed，生成 `dist` |
| Compose 配置 | 通过 | `docker compose config` 正确展开后端、Redis、端口、环境变量和健康检查 |
| Docker 镜像 | 通过 | `docker compose build` 成功生成 `ai-resume-analyzer-backend:latest` |
| 容器健康 | 通过 | 临时映射 `18000:8000` 且 `REDIS_ENABLED=false`，`GET /api/health` 返回 200；日志确认监听 `0.0.0.0:8000` |
| 完整 Compose 启动 | 环境阻塞 | 本机已有程序占用 6379；创建的测试容器和网络已清理，不能据此判定项目失败 |
| 桌面页面 | 通过 | 真实浏览器加载首屏，表单、上传区、隐私提示和提交状态完整，无控制台错误 |
| 表单交互 | 通过 | “一键填入示例”写入 456 字 JD；未选 PDF 时提交按钮保持禁用 |
| 移动页面 | 通过 | 390px 视口下 `body.scrollWidth=375 < viewportWidth=390`，无横向溢出或控制台错误 |
| 真实百炼请求 | 未验证 | 测试使用 MockTransport；未配置或使用真实 API Key |
| 真实 Redis 命中 | 未验证 | Redis 降级有 mock 测试；本次未连接未知的本机 6379 服务 |
| 公网 FC/Vercel/Pages | 未验证 | README 明确为占位地址，没有可访问 URL |
| GitHub 公开仓库/CI | 未验证 | `git remote -v` 为空，无法验证公开性与远端 Actions |
| 密钥扫描 | 通过（当前文件） | 只发现 `.env.example`、文档占位值和测试 `mock-key`；Git 未跟踪 `.env`、PDF、PEM 或 KEY |

测试出现的 PyMuPDF SWIG 弃用警告和 pytest 缓存目录权限警告来自本地运行环境，不影响 30 项断言结果。

## 3. 招聘笔试模拟评分

| 维度 | 权重 | 当前得分 | 扣分原因 |
| --- | ---: | ---: | --- |
| 功能完整性 | 30 | 26 | 主链路完整；真实 AI/Redis 和公网端到端未验；扫描 PDF/OCR 不支持但已如实声明 |
| 代码质量 | 25 | 21 | 分层、类型和异常处理较好；后端 JD 长度无上限、缓存旧值校验和 AI 来源标识仍需补强 |
| 工程化实践 | 20 | 15 | 有测试、CI、Docker、Compose、环境变量和部署文档；无公开 remote/线上地址，前端无自动化测试，远端 CI 未验 |
| 技术深度 | 15 | 12 | 有混合评分、AI 结构校验、哈希缓存和降级；Prompt 注入防护、缓存版本、质量评测和公平性校准不足 |
| 加分项 | 10 | 8 | Redis、FC 适配、响应式 UI、技能别名、脱敏日志和 CI 均有实现；未形成实际云端闭环 |
| **总分** | **100** | **82** | **完成外部交付 P0 后可作为较强笔试项目提交** |

最值得优先修复的三项：

1. 完成公开 GitHub、FC 和前端部署，替换所有占位链接并实测端到端。
2. 将 `RETURN_CLEANED_TEXT` 默认改为 `false`，同时为后端岗位字段增加长度上限和 PDF 页数/解析资源保护。
3. 为 Prompt 和 Redis key 引入版本与注入防护，并在响应中明确 `aiUsed`/`analysisMode`，避免规则回退仍显示为“AI 评价”。

## 4. 功能完整性审查

### 4.1 PDF 与简历解析

- `backend/app/api/resume.py` 使用 `list[UploadFile]` 并通过 `_require_single_file` 强制一次只上传一份文件。
- `backend/app/services/pdf_service.py` 同时检查 `.pdf` 扩展名、受控 MIME、10 MB 默认上限、空内容和 `%PDF-` 文件头。
- PyMuPDF 逐页遍历 `document.page_count`，支持多页；损坏、无页、无可提取文本均映射为可读 400。
- `backend/app/utils/text_utils.py` 处理 CRLF、Unicode NFKC、控制字符、制表符、连续空格和多余空行。
- PDF 原始内容仅以字节读入并在内存交给 PyMuPDF，业务代码不创建持久上传文件。
- 扫描件/OCR 未实现，但题目并未强制 OCR；README 已准确限制为文本型 PDF。

风险：没有 PDF 页数上限、解析 CPU/时间预算、恶意文件扫描或独立解析进程；10 MB 文件仍可能构造高页数/高计算量输入。

### 4.2 信息抽取

- 姓名、电话、邮箱、地址、求职意向、期望薪资、工作年限、教育、工作、项目、技能和证书都有 schema 和提取路径。
- 电话/邮箱由正则提取，并在 AI 合并时优先使用原文可验证值。
- AI 返回的姓名、地址、求职意向、薪资、教育、公司、项目、证书和技能会做不同程度的原文证据检查。
- 纯规则回退可运行，但姓名、教育、工作和项目规则以启发式为主，复杂中文简历的召回率有限。

### 4.3 岗位分析与匹配

- JD 提取核心/加分技能、学历、年限、职责、行业和其他要求。
- 匹配实现技能、经验、项目、学历和 AI 五项分数，返回总分、命中/缺失关键词、优势、风险、总结和推荐等级。
- 所有分数经服务和 Pydantic 双重限幅到 0～100。
- AI 不可用或 AI 正文非法时使用规则结果，主接口仍可返回确定性分析。

问题：`MatchRequest.jobDescription`、`MatchRequest.jobTitle` 以及 `/analyze` 的 Form 字段在后端没有最大长度；前端的 120/5000 限制不是安全边界。超长请求仍会参与哈希、规则扫描并进入 Prompt 截断前的业务处理。

### 4.4 前端

- 主请求为 `POST /api/resumes/analyze`，multipart 字段 `file`、`jobTitle`、`jobDescription` 与后端完全一致。
- `VITE_API_BASE_URL` 可配置，未配置时使用同源相对路径；没有生产代码写死后端域名。
- 文件数量、扩展名、MIME、大小和空文件均有前端提示，但后端仍独立复验。
- 页面有加载阶段、防重复提交、取消控制器、错误映射、空状态和结构化结果视图。
- 桌面和 390px 移动视口已真实加载，无横向溢出和控制台错误。

未覆盖：没有前端单元测试或端到端测试；本次没有在浏览器上传真实简历并请求后端完整结果，因为不应将未知真实简历发送给服务，且没有授权测试 PDF 附件。

## 5. 前后端字段对照表

### 5.1 主请求

| 前端 | 后端 | 类型/位置 | 结论 |
| --- | --- | --- | --- |
| `POST /api/resumes/analyze` | `POST /api/resumes/analyze` | 路径 | 一致 |
| `file` | `file: list[UploadFile]` | multipart | 一致；后端强制 1 个 |
| `jobTitle` | `jobTitle: str = Form(...)` | multipart | 一致 |
| `jobDescription` | `jobDescription: str = Form(...)` | multipart | 一致 |
| `VITE_API_BASE_URL` | `CORS_ORIGINS` | 环境配置 | 可配置；部署时必须互相对应 |

### 5.2 响应

| 后端权威字段 | 前端读取字段 | 结论 |
| --- | --- | --- |
| `code/message/data` | `resume.js` 校验外壳并返回 `data` | 一致 |
| `resumeId/pageCount/resumeHash/cacheHit` | `normalizeResult.js` 同名读取并兼容 snake_case | 一致 |
| `resume.basicInfo.{name,phone,email,address}` | `ResumeDetails.vue` 展示 | 一致 |
| `resume.jobInfo.{jobIntention,expectedSalary}` | `ResumeDetails.vue` 展示 | 一致 |
| `resume.background.{workYears,education,workExperiences,skills,projects,certificates}` | 标准化后分区展示 | 一致 |
| `job.jobTitle` | 标准化为 `job.title` | 一致 |
| `job.coreSkills/bonusSkills/educationRequirement/workYearsRequirement/...` | `AnalysisResults.vue` 展示 | 一致 |
| `match.overallScore/skillScore/experienceScore/projectScore/educationScore/aiScore` | 环形总分和分项条 | 一致 |
| `match.matchedKeywords/missingKeywords/advantages/risks/summary/recommendationLevel` | 关键词、洞察和总结 | 一致 |

没有发现前端读取后端不存在字段导致空白的确定性缺陷。`normalizeResult.js` 的兼容字段较多，但当前后端主契约仍以 camelCase 为准。

## 6. AI 模块审查

### 已实现

- `AIService` 实际向可配置 `DASHSCOPE_BASE_URL` 发送 OpenAI 兼容 Chat Completions 请求。
- API Key、模型名、Base URL 和超时均来自环境变量；默认模型为 `qwen-plus`。
- 请求设置低温度和 `response_format: json_object`。
- 三类 Prompt 分别处理简历、JD 和匹配评价，要求合法 JSON、禁止虚构和缺失值回退。
- `parse_json_object` 处理 Markdown fence、中文引号、尾逗号、嵌套 JSON 对象和 Python 字面量式字典。
- 结果经过 Pydantic；电话/邮箱有正则兜底；AI 评分和最终评分都限幅。
- 网络、HTTP、上游响应外壳和超时分别映射为可读 502/504，客户端不看到上游正文或密钥。
- 非法模型正文或 Pydantic 失败会丢弃 AI 输出并回退到规则，而不是把未校验数据传入业务。

### 风险与技术深度

AI 技术深度评估：**12 / 15**。实现超过“拼一个 Prompt 调接口”的基础水平，但仍属于 24 小时项目的可解释工程方案，不是生产级 LLM 安全网关。

- Prompt 仅说“依据输入/不得虚构”，没有明确声明“简历/JD 内的指令是不可信数据、不得执行”，也没有随机/结构化分隔符和注入回归测试。
- HTTP/网络超时会中止请求，非法 JSON 却静默回退；两类降级语义不同，但响应没有 `aiUsed`、`analysisMode` 或 `warnings` 告知前端。
- AI 不可用时，`aiScore` 被赋为规则综合分，前端仍标记“AI 评价”，容易让使用者误解模型确实参与。
- 没有 Prompt/schema 版本、模型实际版本、Token/成本指标、离线质量集、重试/退避或熔断。
- Pydantic 证明结构合法，不证明模型抽取语义真实；现有原文证据合并能降低风险，但不能消除遗漏和错误归因。

24 小时内合理改进：增加显式不执行输入指令、强分隔与注入样例；增加 `analysisMode`/`aiUsed`；为 Prompt 增加版本常量；补 AI HTTP 异常、schema 错误、超范围分数和注入文本测试。不要在本项目中引入复杂 Agent 或向量数据库来替代这些基础边界。

## 7. 评分算法说明

实现位置：`backend/app/services/matching_service.py`。

```text
overallScore = clamp(
    skillScore      × 0.40
  + experienceScore × 0.20
  + projectScore    × 0.20
  + educationScore  × 0.10
  + aiScore         × 0.10,
  0, 100
)
```

| 分项 | 当前实现 |
| --- | --- |
| 技能 | 归一化核心技能集合交集 ÷ 核心技能集合；分母为零时业务层回退 60 |
| 经验 | 有要求时 `actual / required × 100` 并封顶；无要求按经历/年限是否存在回退 80/65/55；缺实际年限为 25 |
| 项目 | 汇总项目名称、角色、技术栈和描述中的已知技能，与岗位核心技能求重合；无项目回退 30/50 |
| 学历 | 高中、专科、本科、硕士、博士映射层级；达标 100，缺失 30，无要求 80 |
| AI | 有有效模型结果时取模型 `aiScore`；否则取规则综合 `45%/25%/20%/10%` |

技能统一 casefold、空白/符号清理和显式别名映射；`skill_match` 对空 required 集合返回 100，但业务层主动改成 60，避免零分母和虚高。推荐边界为 `>=85` 高度匹配、`>=70` 较为匹配、`>=50` 一般匹配、其余匹配度较低。后端 schema 再次将各项和总分限幅。

算法可解释且与 README 一致。局限是固定回退分会形成先验偏置，技能集合只证明文本命中，项目相关性仍依赖有限别名字典；正式招聘场景应按岗位族用脱敏样本校准，不得把分数作为唯一淘汰条件。

## 8. Redis 缓存审查

### 已实现

- PDF 使用原始字节 SHA-256；JD 使用 `jobTitle + jobDescription` 的 SHA-256。
- 解析与匹配 key 分离：`resume:parse:{resume_hash}`、`resume:match:{resume_hash}:{jd_hash}`。
- 默认 TTL 86400 秒，可关闭 Redis；连接和读写超时都很短。
- GET/SET/反序列化异常统一降级为 cache miss，不影响主流程。
- 解析缓存经 `StructuredResume.model_validate` 重建；FC 冷启动可用完整哈希 `resumeId` 回取 Redis。
- Redis 失败有 mock 测试；缓存 JSON 使用 UTF-8 友好的稳定序列化。

### 问题

- key 没有 schema、Prompt、模型或评分版本。升级后可能命中旧值，当前文档已补充这一限制。
- `jd_hash` 直接拼接标题和正文，理论上存在边界碰撞；建议使用长度前缀或 JSON canonicalization。
- 匹配缓存只检查 `job`/`match` 为 dict，没有在服务层先用 `JobAnalysis`/`MatchResult` 验证；旧值可能直到 FastAPI 响应校验时才触发 500。
- 没有真实 Redis set/get/TTL/cacheHit 集成测试，也没有损坏缓存、旧版本缓存测试。

## 9. 代码质量与工程化

优点：

- 路由薄，配置、schema、服务、Prompt 和 utils 分层清楚；业务没有堆在 `main.py`。
- 主要数据结构有 Pydantic/类型注解，函数命名清楚，未发现硬编码真实密钥、生产域名或本地文件路径。
- 外部 I/O 为异步；PDF 文档在 `finally` 关闭；httpx/Redis 客户端在 lifespan 关闭。
- 异常响应统一，未知异常只向客户端返回通用 500；日志不记录简历正文或联系方式。
- 依赖版本锁定，有 `.gitignore`、`.dockerignore`、CI、Dockerfile、Compose、环境示例和部署文档。

可改进：

- 容器级单例服务让测试替换依赖不够直接，可后续改为 FastAPI dependency provider；当前规模可以接受。
- Redis 故意捕获所有异常作为非关键边界，但应增加错误类型指标，避免长期静默降级。
- 后端输入长度、PDF 页数和请求限流缺失；公网服务容易被高成本请求占用。
- `RETURN_CLEANED_TEXT=true` 的安全默认值不理想；公网响应会额外返回完整清洗简历。
- Python 依赖仅精确版本，没有哈希锁文件或依赖扫描；前端依赖有 lockfile。

## 10. 安全与隐私审查

- 未发现真实 API Key、`.env`、PEM/KEY 或 PDF 被 Git 跟踪。
- `.gitignore` 覆盖环境文件、虚拟环境、构建产物、日志、上传目录和 Redis 持久化文件。
- CORS 从环境变量读取；通配 Origin 时自动关闭 credentials。
- PDF 类型和大小双端校验，内部堆栈不返回前端。
- README 已说明简历会发送给 AI、Redis 可能缓存个人信息、评分仅作辅助。
- 日志中间件只记录 request ID、方法、路径、状态和耗时。

主要风险：默认返回 `cleanedText`；无鉴权、限流、页数/CPU 防护和恶意文件检测；Prompt 注入防护较弱；Redis 生产 TLS 只能靠基础设施而不是当前客户端配置项。这些限制已在 README 说明，但公开部署仍应采用最小暴露配置。

## 11. 测试审查

### 已覆盖

- 健康检查和统一响应。
- 非 PDF、伪造/损坏 PDF、多文件、空文本 PDF、超限文件。
- 多页 PDF 提取和组合 `/analyze` 契约。
- 文本清洗、SHA-256、电话/邮箱正则。
- 技能别名、大小写、匹配率和分数限幅。
- 推荐等级边界、空/过短 JD。
- AI 非法 JSON和 Markdown JSON；AI 使用 MockTransport，不访问真实网络。
- Redis 连接失败降级和 FC 冷启动从缓存恢复记录。

### 缺失

- 真实或容器化 Redis 的 SET/GET、TTL、二次请求 `cacheHit=true`、损坏/旧版本缓存。
- AI 401/429/500、网络错误、超时、上游外壳异常、超范围分数、Prompt 注入文本。
- PDF 大小边界恰好等于限制、大小写扩展名、`application/x-pdf`、超高页数和解析资源上限。
- 姓名、地址、求职意向、薪资、教育、工作、项目和证书的规则/AI 合并细节。
- 经验、项目、学历每个评分分支和总分公式的精确数值断言。
- 前端 API/normalizer/component 单测及真实浏览器端到端上传分析。
- FC/Vercel/Pages 公网 smoke test、CORS 预检和 GitHub Actions 远端状态。

现有测试足以证明核心规则和接口能作为笔试代码提交，但不足以证明真实云端交付。建议在提交前至少补缓存命中、完整评分公式、输入长度、Prompt 注入和一条前端契约测试。

## 12. 部署审查

- Dockerfile 采用 Python 3.12 slim、非 root 用户、环境端口、`0.0.0.0` 监听和健康检查，适合 FC 自定义容器。
- 镜像构建与临时容器健康检查已实际通过。
- Compose 的后端依赖 Redis 健康状态，服务有健康检查；本机 6379 冲突可用 `REDIS_EXPOSE_PORT` 解决。
- 前端 API 和 base path 均可用环境变量；Vercel rewrite 能处理 SPA 刷新。
- GitHub Pages 只提供文档工作流示例，没有仓库内实际 Pages 部署 workflow；当前应用无前端路由，因此刷新 404 风险较低。
- FC、ACR、Vercel 和 Pages 文档步骤基本可执行，但没有云账号状态、域名、触发器、CORS 或公网健康证据。

## 13. 分级问题

### P0：阻止最终提交

#### P0-1：公开仓库和线上演示未完成

- 位置：`README.md:39-44`（加入亮点后行号可能变化）、`docs/deployment.md:372`，以及当前空的 `git remote -v`。
- 事实：GitHub、Vercel 和 FC URL 都是占位；没有 remote，无法验证公开访问、线上端到端或 Actions。
- 影响：不满足原始硬性交付“公开前端部署、阿里云 FC、GitHub 公开仓库”，因此当前不应直接发送给招聘方。
- 处理：由项目所有者创建云资源和公开仓库，部署后替换链接并按验收清单实测；这一步需要账号/凭据，不能仅靠本地代码自动完成。

代码运行层面没有 P0。

### P1：明显影响评分或公网安全

#### P1-1：公网上传默认返回完整清洗文本

- 位置：`backend/app/core/config.py:93`、`backend/.env.example:19`、`docker-compose.yml:38`。
- 问题：`RETURN_CLEANED_TEXT` 默认 `true`，响应比结构化展示额外暴露完整简历文本。
- 建议：代码、示例和 Compose 默认统一为 `false`；本地调试需要时显式开启，并补测试。

#### P1-2：后端 JD/岗位名称缺少最大长度

- 位置：`backend/app/schemas/job.py:17-20`、`backend/app/api/resume.py:36-37`。
- 问题：前端 120/5000 限制可绕过，后端会处理超长 JSON/Form 字段。
- 建议：schema 和 Form 统一 `jobTitle<=200`、`jobDescription<=20000`（或更严格），返回统一 422/400，并补边界测试。

#### P1-3：AI 参与状态不透明

- 位置：`backend/app/services/matching_service.py:95-103`、`frontend/src/components/ScoreBreakdown.vue`。
- 问题：AI 不可用/非法时 `aiScore` 是规则综合分，UI 仍显示“AI 评价”。
- 建议：响应增加 `analysisMode: ai|rules`、`aiUsed: bool`、可选 `warnings`；前端按来源显示“AI 评价”或“规则回退分”。

#### P1-4：Prompt 注入防护和回归测试不足

- 位置：`backend/app/prompts/*.py`、`backend/tests/test_services.py`。
- 问题：没有明确忽略简历/JD 内指令，也没有注入测试。
- 建议：加入不执行输入指令、强分隔和数据标签；测试恶意文本仍只能输出 schema 且不得覆盖事实。

#### P1-5：缓存没有版本且匹配缓存缺少服务层 schema 校验

- 位置：`backend/app/services/analysis_service.py:71,106,121`。
- 问题：发布新 schema/Prompt/算法后可能复用旧值；无效 match dict 可能转成 500。
- 建议：加入 `CACHE_SCHEMA_VERSION` namespace，并用 `JobAnalysis`/`MatchResult` 校验命中值，失败时删除/忽略并重算。

#### P1-6：关键自动化测试缺口

- 位置：`backend/tests/`、缺失的 `frontend/src/**/*.test.*` 或 `frontend/tests/`。
- 问题：缓存命中、评分公式、输入上限、AI 错误分支和前端契约没有自动证明。
- 建议：提交前补最小高价值集合；真实 AI 继续 Mock，Redis 可用 fake 或 CI service container。

### P2：后续优化

- `jd_hash` 使用无分隔拼接；改为版本化 canonical JSON 或长度前缀。
- 增加 PDF 页数、解析超时/进程隔离、恶意文件检测、鉴权、限流和配额。
- Compose 默认发布 Redis 6379；只供后端使用时可取消 host port，需本机调试再用 profile 开启。
- 健康接口只表示进程存活；可增加不泄密的 `degraded` 依赖状态和独立 readiness。
- 技能别名中的 `go`、`es`、`ai` 等短词可能误命中；增加语境测试和词典版本。
- 固定回退分和岗位统一权重需要脱敏评测集校准，并开展公平性/误伤率评估。
- 增加前端无障碍自动检查、性能预算和端到端截图回归。
- Python 引入带哈希的 lock/constraints 和依赖、容器漏洞扫描。

## 14. 可直接交给 Codex 的精确修复清单

以下清单不要求重写项目。

### P0-1：完成公开交付并替换占位信息

- 文件：`README.md`、`docs/deployment.md`、部署平台配置。
- 当前问题：README 含 `your-project.vercel.app`、`your-fc-domain.example.com` 和 `github.com/<your-account>`；本地 Git 无 remote。
- 预期结果：公开 GitHub 可匿名访问；FC HTTPS 健康接口返回 200；Vercel/Pages 可上传授权测试 PDF 并展示完整结果；README 只保留真实 URL。
- 修改后运行/检查：

```bash
git remote -v
curl -i https://<fc-domain>/api/health
git grep -n "your-project\|your-fc-domain\|<your-account>"
```

再在无登录浏览器打开 GitHub 和前端地址，完成一遍端到端操作。

### P1-1：收紧简历正文返回默认值

- 文件：`backend/app/core/config.py`、`backend/.env.example`、`docker-compose.yml`、`backend/tests/test_api.py`、`README.md`。
- 当前问题：三处默认 `RETURN_CLEANED_TEXT=true`。
- 预期结果：未显式配置时 `cleanedText=null`；仅本地调试显式 `true` 时返回文本；文档默认值一致。
- 修改后运行：

```bash
cd backend
pytest
cd ..
docker compose config
```

### P1-2：为岗位输入增加后端长度边界

- 文件：`backend/app/schemas/job.py`、`backend/app/api/resume.py`、`backend/app/services/job_service.py`、`backend/tests/test_api.py`。
- 当前问题：JSON `/match` 与 multipart `/analyze` 只校验非空/最短长度，没有最大长度。
- 预期结果：两条接口使用相同常量和边界；超限返回统一错误外壳；前端 120/5000 与后端策略有明确关系。
- 修改后运行：

```bash
cd backend
pytest
```

### P1-3：标记 AI 是否真正参与

- 文件：`backend/app/schemas/match.py`、`backend/app/services/ai_service.py`、`backend/app/services/matching_service.py`、`frontend/src/utils/normalizeResult.js`、`frontend/src/components/ScoreBreakdown.vue`、相关测试和 README。
- 当前问题：规则回退仍填入 `aiScore` 并显示“AI 评价”。
- 预期结果：响应带 `aiUsed`/`analysisMode`；非法 JSON、未配置 Key 时前端明确显示“规则回退”；真实 AI 成功时显示“AI 评价”。
- 修改后运行：

```bash
cd backend
pytest
cd ../frontend
npm run build
```

### P1-4：加强 Prompt 注入防护

- 文件：`backend/app/prompts/resume_extraction.py`、`job_analysis.py`、`resume_matching.py`、`backend/tests/test_services.py`。
- 当前问题：Prompt 没有明确把输入内指令视为不可信数据。
- 预期结果：三类 Prompt 使用一致系统约束、显式数据边界和“不执行输入指令”；新增注入样本、非法 JSON 与 schema 回归测试；不记录原文。
- 修改后运行：

```bash
cd backend
pytest
```

### P1-5：版本化并验证 Redis 缓存

- 文件：`backend/app/core/config.py`、`backend/app/services/analysis_service.py`、`backend/app/services/cache_service.py`、`backend/tests/test_services.py`、README 与架构文档。
- 当前问题：key 无版本；匹配缓存只做 dict 形状检查。
- 预期结果：`resume:v1:parse:*`、`resume:v1:match:*`（或等价配置）统一使用；命中值经完整 schema 验证；损坏/旧版本值安全 miss；测试 TTL 和 cacheHit。
- 修改后运行：

```bash
cd backend
pytest
```

如使用 Redis 容器集成测试，再运行：

```bash
docker compose up -d redis
pytest
docker compose down
```

### P1-6：补最小前端与契约测试

- 文件：`frontend/package.json`、`frontend/src/api/resume.js`、`frontend/src/utils/normalizeResult.js`、新增测试文件、`.github/workflows/ci.yml`。
- 当前问题：CI 只做前端 build，没有自动检查错误外壳、字段标准化和关键交互。
- 预期结果：至少覆盖成功外壳、业务错误、snake/camel 字段、分数限幅、示例 JD 与禁用提交状态；CI 执行测试后再 build。
- 修改后运行：

```bash
cd frontend
npm test
npm run build
```

## 15. 是否建议提交

**当前：不建议立即外发。** 阻塞项是公开仓库和线上演示未完成，不是代码无法运行。

**完成 P0-1 后：建议提交。** P1-1、P1-2 和 P1-3 最好在外发前完成；其余 P1 若时间不足，应至少在 README“已知限制”中保留透明说明并能回答设计取舍。

招聘方快速阅读材料已写入 README：项目亮点、300～500 字技术方案摘要、提交消息模板和最终验收流程。逐项状态见 [acceptance-checklist.md](acceptance-checklist.md)。
