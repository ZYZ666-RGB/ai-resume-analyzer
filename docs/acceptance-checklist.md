# 项目验收清单

验收日期：2026-07-12
状态含义：`已完成`＝源码和本地证据均支持；`部分完成`＝有实现但覆盖/验证不足；`未完成`＝当前不存在或明确为占位；`无法验证`＝依赖外部账号、服务或授权数据。

## 修复复验摘要

- P0：代码运行层面无 P0；公开 GitHub、FC 与前端 URL 仍需要项目所有者的账号授权和云资源，当前保持“未完成/无法验证”，没有用虚假链接规避门禁。
- P1：安全默认值、岗位输入边界、AI 来源透明、Prompt 注入防护、版本化缓存/完整校验、前端最小契约测试均已修复。
- 已处理 P2：新增 PDF 50 页保护、canonical JD 哈希和仓库内 GitHub Pages 工作流。
- 本清单记录修复后状态；原始问题与当时证据保留在 [review-report.md](review-report.md)。

| 问题 | 修复后状态 | 复验证据 |
| --- | --- | --- |
| P1-1 清洗正文默认暴露 | 已修复 | 代码、`.env.example`、Compose 默认 `false`；默认/显式开启测试 |
| P1-2 岗位输入无上限 | 已修复 | JSON/multipart/服务层共享 120/5000 边界；边界与 422 测试 |
| P1-3 AI 参与不透明 | 已修复 | `aiUsed/analysisMode/warnings` + 前端动态标签 + 新旧契约测试 |
| P1-4 Prompt 注入防护 | 已修复 | v2 系统约束、可转义 JSON 边界、恶意指令与 Schema 回归测试 |
| P1-5 缓存无版本/弱校验 | 已修复 | `resume:parse:v1` / `resume:match:v1`、strict Pydantic、损坏值/TTL/cacheHit 测试 |
| P1-6 自动化缺口 | 已修复核心项 | 后端 56 项；前端 9 项；CI 依次运行 pytest、Vitest、Vite build |

## 1. 原始硬性交付

| 状态 | 验收项 | 证据/说明 |
| --- | --- | --- |
| 已完成 | 上传单个 PDF 简历 | `/api/resumes/parse`、`/analyze` 强制单文件，前端也限制单文件 |
| 已完成 | 解析多页 PDF | PyMuPDF 遍历全部页面；多页自动测试通过 |
| 已完成 | 清洗和结构化文本 | `clean_text` 与 Pydantic 简历 schema 已实现并测试 |
| 已完成 | AI/规则提取姓名、电话、邮箱、地址 | 有规则、AI、原文校验和联系方式正则优先 |
| 已完成 | 尽量提取求职意向、薪资、年限、学历、项目 | schema、Prompt 和规则路径均存在；复杂版式准确率有限 |
| 已完成 | 接收岗位描述 | multipart 和 JSON 两种接口均支持 |
| 已完成 | 提取岗位关键词 | 核心/加分技能与其他岗位字段均返回 |
| 已完成 | 计算简历与岗位匹配度 | 五项分数、总分和推荐等级真实实现 |
| 已完成 | 返回结构化 JSON | 统一 `code/message/data` 外壳和 Pydantic 响应模型 |
| 已完成 | Redis 可选缓存 | 实现 TTL、开关、解析/匹配分离和异常降级 |
| 已完成 | 可用前端页面 | 构建和真实浏览器首屏/交互/移动视口检查通过 |
| 未完成 | 前端公开部署 | README 仍为 Vercel 占位地址 |
| 部分完成 | 后端适配阿里云 FC | Docker/端口/文档完成且本地容器健康；未验证真实 FC |
| 未完成 | GitHub 公开仓库 | 本地无 remote，README 为占位地址 |
| 已完成 | README 架构、技术、部署、使用方式 | 已覆盖并补充审查报告链接 |

## 2. PDF、抽取与业务功能

| 状态 | 验收项 | 证据/说明 |
| --- | --- | --- |
| 已完成 | 真正实现 PDF 上传 | FastAPI `UploadFile` + multipart |
| 已完成 | 校验 PDF 扩展名 | `.pdf` 大小写不敏感 |
| 已完成 | 校验 MIME | 仅 `application/pdf`、`application/x-pdf` |
| 已完成 | 校验 PDF 文件头 | 要求 `%PDF-` |
| 已完成 | 限制文件大小 | 默认 10 MB，读取最大值 + 1 字节 |
| 已完成 | 处理损坏 PDF | PyMuPDF 异常转 400；测试通过 |
| 已完成 | 处理无文本 PDF | 清洗后为空转 400；测试通过 |
| 已完成 | 支持多页 | 测试断言两页内容和页数 |
| 已完成 | 文本清洗 | 换行、NFKC、控制字符、空格、空行 |
| 已完成 | 姓名提取 | 显式标签/首行规则 + AI 原文校验 |
| 已完成 | 电话提取 | 中国手机号/国际样式正则 + 测试 |
| 已完成 | 邮箱提取 | 正则 + 测试 |
| 已完成 | 地址提取 | 显式标签规则 + AI 原文校验 |
| 已完成 | 求职意向 | 显式标签规则 + AI 原文校验 |
| 已完成 | 期望薪资 | 显式标签规则 + AI 原文校验 |
| 已完成 | 工作年限 | 规则 + AI 字段 |
| 已完成 | 学历经历 | 规则 + AI 结构数组 |
| 已完成 | 工作经历 | 规则 + AI 结构数组 |
| 已完成 | 项目经历 | 规则 + AI 结构数组 |
| 已完成 | 技能与证书 | 已知技能词典、AI 合并、证书规则 |
| 已完成 | 岗位核心/加分技能 | 规则与 AI 合并，原文 grounding |
| 已完成 | 技能匹配 | 别名标准化、交集、命中率 |
| 已完成 | 经验相关性 | 年限比例和缺失回退 |
| 已完成 | 项目相关性 | 项目文本技能与核心技能重合度 |
| 已完成 | 学历匹配 | 学历层级比较 |
| 已完成 | 规则评分 + AI 评分 | AI 权重 10%，不可用时规则回退 |
| 已完成 | 综合分 | 五项加权并限幅 |
| 已完成 | 命中/缺失关键词 | `matchedKeywords`、`missingKeywords` |
| 已完成 | 优势和风险 | AI 结果 + 规则补充 |
| 已完成 | 推荐等级 | 85/70/50 边界实现并测试 |
| 已完成 | AI 参与状态透明 | 返回 `aiUsed/analysisMode/warnings`；前端区分 AI 评价与规则回退分 |
| 部分完成 | 公网资源保护 | 有 10 MB、50 页、岗位 120 字和 JD 5000 字限制；仍无 CPU 隔离、鉴权和限流 |

## 3. 前后端联调

| 状态 | 验收项 | 证据/说明 |
| --- | --- | --- |
| 已完成 | 请求路径一致 | 前后端均为 `/api/resumes/analyze` |
| 已完成 | multipart 字段一致 | `file/jobTitle/jobDescription` 一致 |
| 已完成 | 两段式 JSON 参数一致 | `resumeId/jobTitle/jobDescription` 一致 |
| 已完成 | 响应外壳一致 | 前端正确解包 `code/message/data` |
| 已完成 | 简历字段一致 | camelCase 主契约，前端兼容 snake_case |
| 已完成 | 岗位字段一致 | `jobTitle` 在前端标准化为 `title` |
| 已完成 | 匹配字段一致 | 六项分数、关键词、洞察和等级全部对应 |
| 已完成 | API Base URL 环境变量 | `VITE_API_BASE_URL` |
| 已完成 | CORS 可配置 | `CORS_ORIGINS` 逗号分隔 |
| 已完成 | 统一错误格式 | 400/404/413/422/500/502/504 均统一外壳 |
| 已完成 | HTTP 状态码合理 | 主要业务错误映射合理 |
| 已完成 | 加载与错误状态 | 进度、禁用、取消、错误提示均存在 |
| 已完成 | 结构化结果展示 | 不只显示原始 JSON |
| 已完成 | 页面无明显空白/启动报错 | 桌面与 390px 浏览器检查无控制台错误 |
| 已完成 | 后端输入长度与前端一致 | JSON/multipart/服务层统一岗位 1～120、JD 10～5000；边界与超限测试通过 |
| 无法验证 | 云端 CORS 实际联调 | 没有真实前后端域名 |

### 字段对照

| 请求/响应区 | 后端字段 | 前端字段/用途 | 状态 |
| --- | --- | --- | --- |
| 请求 | `file` | `FormData.file` | 已完成 |
| 请求 | `jobTitle` | `FormData.jobTitle` | 已完成 |
| 请求 | `jobDescription` | `FormData.jobDescription` | 已完成 |
| 元数据 | `resumeId/pageCount/resumeHash/cacheHit` | 结果元数据与缓存标签 | 已完成 |
| 基本信息 | `resume.basicInfo.*` | 姓名、电话、邮箱、所在地 | 已完成 |
| 求职信息 | `resume.jobInfo.*` | 意向、薪资 | 已完成 |
| 背景 | `resume.background.*` | 年限、教育、工作、技能、项目、证书 | 已完成 |
| 岗位 | `job.jobTitle/coreSkills/bonusSkills/...` | 岗位识别面板 | 已完成 |
| 评分 | `match.*Score` | 总分环和五项分数条 | 已完成 |
| 解释 | `matchedKeywords/missingKeywords/advantages/risks/summary` | 关键词与洞察面板 | 已完成 |

## 4. AI 模块

| 状态 | 验收项 | 证据/说明 |
| --- | --- | --- |
| 已完成 | 真实百炼/千问调用代码 | OpenAI 兼容 Chat Completions HTTP 请求 |
| 无法验证 | 真实百炼账号调用成功 | 未使用真实 API Key；测试正确使用 Mock |
| 已完成 | 模型名可配置 | `DASHSCOPE_MODEL` |
| 已完成 | API Key 来自环境变量 | `DASHSCOPE_API_KEY` |
| 已完成 | 请求超时 | `DASHSCOPE_TIMEOUT` + httpx client timeout |
| 已完成 | Prompt 要求合法 JSON | 三类 Prompt 均有字段结构 |
| 已完成 | Prompt 禁止虚构 | 简历和匹配 Prompt 明确约束 |
| 已完成 | 处理 Markdown 代码块 | `parse_json_object` |
| 已完成 | 处理非法 JSON | 丢弃 AI 输出并规则回退；测试通过 |
| 已完成 | Pydantic 校验 | `StructuredResume/JobAnalysis/AIMatchEvaluation` |
| 已完成 | 电话/邮箱正则兜底 | 正则优先并校验 AI 值来自原文 |
| 已完成 | AI 上游失败明确错误 | 网络/HTTP/外壳 502，超时 504 |
| 已完成 | 不直接信任 AI 总分 | AI 只占 10%，所有分数限幅 |
| 已完成 | 分数范围限制 | schema + service 双重 clamp |
| 已完成 | Prompt 注入防护 | 版本化系统约束、可转义不可信 JSON 边界、“不执行输入指令”及注入回归测试 |
| 已完成 | AI 降级可观察性 | 响应包含 `aiUsed/analysisMode/warnings`，UI 明确标识规则回退 |

## 5. 评分算法

| 状态 | 验收项 | 证据/说明 |
| --- | --- | --- |
| 已完成 | 权重清晰 | 40/20/20/10/10 |
| 已完成 | 总分正确计算 | `matching_service.py` 加权并 clamp |
| 已完成 | 技能匹配率正确 | 集合交集/required；空核心技能业务回退 60 |
| 已完成 | 零分母处理 | `skill_match` 有保护，业务层再覆盖中性值 |
| 已完成 | 忽略大小写 | casefold |
| 已完成 | 技能别名标准化 | 显式字典与参数化测试 |
| 已完成 | 项目相关性 | 项目文本技能重合 |
| 已完成 | 工作经验 | 年限比例与回退 |
| 已完成 | 学历要求 | 层级比较 |
| 已完成 | AI 权重合理 | 10% |
| 已完成 | 所有分数限幅 | 0～100 |
| 已完成 | 推荐边界 | 85/70/50，边界测试通过 |
| 部分完成 | 算法校准 | 无脱敏基准数据集和岗位族校准 |

## 6. Redis 缓存

| 状态 | 验收项 | 证据/说明 |
| --- | --- | --- |
| 已完成 | PDF 内容哈希 | SHA-256 原始字节 |
| 已完成 | JD 哈希 | SHA-256 canonical JSON，保留标题/正文边界 |
| 已完成 | Key 稳定 | 确定性 hash key 与 `v1` 缓存合同版本 |
| 已完成 | 解析/评分缓存分开 | `parse` 与 `match` namespace |
| 已完成 | 过期时间 | `REDIS_TTL`，SET `ex` |
| 已完成 | 支持关闭 | `REDIS_ENABLED=false` |
| 已完成 | Redis 异常不阻断 | 所有异常转 cache miss；测试通过 |
| 已完成 | JSON 反序列化 | dict 检查，解析缓存再 Pydantic 验证 |
| 已完成 | 匹配缓存完整 schema 校验 | Parse/Match 命中前严格验证完整 Pydantic schema、ID/哈希和岗位标题 |
| 已完成 | 缓存版本兼容 | `resume:parse:v1:*` / `resume:match:v1:*`；旧 Parse 仅严格校验只读过渡 |
| 无法验证 | 真实 Redis 二次命中 | 当前自动化使用 in-memory fake；本轮最终镜像执行审批受限，仍需容器/生产 Redis 复验 |
| 已完成 | JD hash 边界唯一性 | canonical JSON 字段边界测试通过 |

## 7. 代码质量、安全与隐私

| 状态 | 验收项 | 证据/说明 |
| --- | --- | --- |
| 已完成 | 路由不堆业务 | `main.py` 与路由较薄 |
| 已完成 | 配置/schema/service/utils 分层 | 目录职责清楚 |
| 已完成 | 类型注解与命名 | 主要接口和领域结构完整 |
| 已完成 | 避免内部堆栈暴露 | 未知错误返回通用 500 |
| 已完成 | 未发现真实 API Key | 扫描只见占位/Mock |
| 已完成 | 未提交 `.env` | Git 未跟踪；`.gitignore` 完整 |
| 已完成 | 不记录完整简历/联系方式 | 日志仅路径、耗时、状态、错误类型 |
| 已完成 | 不永久保存上传原件 | 业务代码不落盘；Redis 只缓存结果 |
| 已完成 | CORS 配置 | 环境白名单 |
| 已完成 | README 说明发送给 AI | 已明确 |
| 已完成 | README 说明评分仅辅助 | 已明确 |
| 已完成 | 最小化响应个人信息 | `RETURN_CLEANED_TEXT=false` 为代码、示例和 Compose 安全默认值 |
| 部分完成 | 公网滥用保护 | 已有 50 页限制；仍无鉴权、限流、配额、CPU 时间预算和解析隔离 |
| 部分完成 | Redis 生产 TLS | 文档要求，但客户端没有 TLS URL/证书专门配置 |
| 已完成 | 无硬编码密钥/生产域名 | 只有占位和本地开发默认值 |

## 8. 自动化测试

| 状态 | 验收项 | 证据/说明 |
| --- | --- | --- |
| 已完成 | 健康检查 | API 测试 |
| 已完成 | PDF 解析 | 合法/伪造/损坏/空文本 |
| 已完成 | 多页 PDF | 服务与 API 测试 |
| 已完成 | 文本清洗 | 精确断言 |
| 已完成 | 文件哈希 | SHA-256 精确断言 |
| 已完成 | 电话/邮箱正则 | 有效/无效样本 |
| 已完成 | 技能标准化 | 多组别名参数化 |
| 已完成 | 技能匹配 | 大小写、别名、75% 匹配率 |
| 已完成 | 分数限幅 | schema 与 helper |
| 已完成 | AI 非法 JSON | MockTransport，不访问真实网络 |
| 已完成 | Redis 降级 | BrokenRedis fake |
| 已完成 | 非 PDF 文件 | API 测试 |
| 已完成 | 空岗位描述 | API/服务测试 |
| 已完成 | AI 在测试中 Mock | 环境清空 Key + MockTransport |
| 已完成 | 缓存 cacheHit/TTL/损坏值 | In-memory fake 验证 TTL、版本 key、合法命中、损坏值 miss 和 FC 冷启动恢复 |
| 已完成 | 完整评分公式分支 | 精确断言技能/经验/项目/学历、规则回退 AI 分和最终 40/20/20/10/10 公式 |
| 已完成 | AI HTTP/超时/注入分支 | 401/429/500、网络、超时、上游外壳、注入与 Schema 错误均由 MockTransport 覆盖 |
| 部分完成 | 前端单元/组件测试 | 新增 9 项 API/normalizer/表单策略 Vitest；尚无 Vue 组件挂载测试 |
| 部分完成 | 前端端到端 | 本次人工浏览器验收首屏/示例/响应式；未上传 PDF |
| 已完成 | 当前测试可作为笔试基础 | 后端 56 项、前端 9 项全通过；真实 AI 仍正确使用 Mock |

## 9. 部署与工程化

| 状态 | 验收项 | 证据/说明 |
| --- | --- | --- |
| 已完成 | Dockerfile | 非 root、依赖锁定、健康检查 |
| 已完成 | 监听 `0.0.0.0` | Uvicorn CMD 与容器日志确认 |
| 已完成 | 端口环境变量 | `${PORT:-8000}` |
| 已完成 | 不依赖本地永久存储 | 无业务持久卷/上传目录 |
| 已完成 | 密钥环境变量 | Key 未进镜像 |
| 已完成 | 健康检查 | Dockerfile、Compose、API |
| 已完成 | 适合 FC 自定义容器 | 本地镜像构建和健康通过 |
| 部分完成 | README FC 步骤可执行 | 文档完整；未在真实账号执行 |
| 已完成 | Vercel 配置 | `vercel.json` build/output/rewrite |
| 已完成 | GitHub Pages 支持 | 已有 `.github/workflows/pages.yml`，含 test/build/artifact/deploy 与自动 base path |
| 已完成 | API 地址环境变量 | `VITE_API_BASE_URL` |
| 已完成 | 生产路径处理 | Vite `base`，Vercel SPA rewrite |
| 无法验证 | FC 公网触发器/CORS | 无真实域名/账号 |
| 无法验证 | Vercel/Pages 公网刷新 | 无线上页面 |
| 无法验证 | GitHub Actions 远端状态 | 无 Git remote |
| 已完成 | 本地前端生产构建 | 成功 |
| 已完成 | Docker 镜像构建 | 成功 |
| 已完成 | 容器 HTTP 健康 | 200 |
| 部分完成 | 完整 Compose 启动 | 本机 6379 冲突；配置已通过，测试资源已清理 |

## 10. 文档交付

| 状态 | 文件/内容 | 说明 |
| --- | --- | --- |
| 已完成 | `README.md` | 介绍、亮点、摘要、架构、时序、技术、目录、启动、环境、API、评分、AI、缓存、安全、部署、测试、限制、优化 |
| 已完成 | `docs/architecture.md` | 分层、数据流、AI、评分、缓存、信任边界 |
| 已完成 | `docs/api-examples.md` | curl、PowerShell、Axios、成功/错误示例 |
| 已完成 | `docs/deployment.md` | 本地、Compose、ACR/FC、Vercel、Pages、GitHub、安全基线 |
| 已完成 | `docs/review-report.md` | 总评、分数、P0/P1/P2、修复清单、提交结论 |
| 已完成 | `docs/acceptance-checklist.md` | 本文件，逐项状态与证据 |
| 已完成 | Mermaid 系统架构图 | README/architecture |
| 已完成 | Mermaid 分析时序图 | README |
| 已完成 | 5～8 条项目亮点 | README 7 条 |
| 已完成 | 300～500 字技术方案摘要 | README |
| 已完成 | 招聘方消息模板 | README |
| 已完成 | 提交前最终流程 | README 10 步 |

## 11. 暂未处理的 P2

- PDF 已有 10 MB/50 页保护，但尚无独立解析进程、CPU 时间预算、病毒/恶意文件检测。
- 尚无登录鉴权、租户隔离、接口限流、并发配额和费用熔断；公开部署前应由网关/FC 补齐。
- Compose 仍默认发布 Redis 宿主机 6379 端口，方便笔试本地调试；生产不得直接公网暴露。
- 健康接口仍以进程存活为主，没有独立 readiness/degraded 依赖状态。
- 技能短别名、固定回退分和统一权重仍需脱敏数据集做语境、公平性与误伤率校准。
- 尚无 Vue 组件挂载/E2E、自动无障碍和视觉回归；当前已有 9 项纯契约/策略测试与人工响应式证据。
- Python 尚未使用带哈希 lock/constraints，CI 也尚未加入依赖、Secret 与容器漏洞扫描。

## 12. 最终提交门禁

| 状态 | 提交前动作 | 通过条件 |
| --- | --- | --- |
| 未完成 | 创建公开 GitHub 仓库并设置 remote | 匿名窗口可访问，README 地址真实 |
| 未完成 | 部署 FC 后端 | 公网 HTTPS `/api/health` 200 |
| 未完成 | 部署 Vercel 或 Pages | 公网 HTTPS 页面可访问 |
| 无法验证 | 上传授权测试简历 + 测试 JD | 页面显示完整结构化结果和评分 |
| 无法验证 | 真实 Redis 重复请求 | 第二次 `cacheHit=true`，关闭 Redis 仍成功 |
| 无法验证 | 云端 CORS/控制台 | 无 CORS、混合内容或 JavaScript 错误 |
| 无法验证 | GitHub Actions | 后端测试与前端构建均绿色 |
| 部分完成 | 本地测试/构建/镜像 | 56 个后端测试、9 个前端测试、前端 build、Compose config 通过；基线镜像曾通过，但本轮最终镜像构建审批受产品用量限制，需手动复跑 |
| 已完成 | 当前文件秘密扫描 | 未发现真实密钥；发布前仍需扫描完整 Git 历史和镜像 |
| 未完成 | 替换 README 全部占位 | `git grep` 不再命中占位 URL/账号 |

**验收结论：代码主体通过，外部交付未通过。完成公开仓库、云端部署、真实链接和端到端验证后，可改为“建议提交”。**
