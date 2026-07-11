<script setup>
import { computed, nextTick, onBeforeUnmount, ref } from 'vue'
import { analyzeResume, getRequestErrorMessage } from './api/resume'
import AnalysisProgress from './components/AnalysisProgress.vue'
import AnalysisResults from './components/AnalysisResults.vue'
import AppHeader from './components/AppHeader.vue'
import JobDescriptionForm from './components/JobDescriptionForm.vue'
import ResumeUpload from './components/ResumeUpload.vue'
import { normalizeAnalysisResult } from './utils/normalizeResult'

const MIN_JOB_DESCRIPTION_LENGTH = 10

const sampleJob = {
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

const resumeFile = ref(null)
const fileError = ref('')
const jobTitle = ref('')
const jobDescription = ref('')
const requestError = ref('')
const isSubmitting = ref(false)
const hasProgress = ref(false)
const currentStage = ref(0)
const progress = ref(0)
const result = ref(null)
const analyzerRef = ref(null)

let stageTimers = []
let activeController = null

const canSubmit = computed(
  () =>
    Boolean(resumeFile.value) &&
    jobTitle.value.trim().length > 0 &&
    jobDescription.value.trim().length >= MIN_JOB_DESCRIPTION_LENGTH &&
    !isSubmitting.value,
)

const submitHint = computed(() => {
  if (isSubmitting.value) return '分析通常需要数秒，请勿重复提交'
  if (!resumeFile.value) return '请先选择一份 PDF 简历'
  if (!jobTitle.value.trim()) return '请填写岗位名称'
  if (jobDescription.value.trim().length < MIN_JOB_DESCRIPTION_LENGTH) {
    return `岗位描述还需填写 ${MIN_JOB_DESCRIPTION_LENGTH - jobDescription.value.trim().length} 个字符`
  }
  return '材料已就绪，可以开始分析'
})

function clearStageTimers() {
  stageTimers.forEach((timer) => window.clearTimeout(timer))
  stageTimers = []
}

function setProgressStage(stage, value) {
  if (!isSubmitting.value) return
  currentStage.value = stage
  progress.value = Math.max(progress.value, value)
}

function startProgress() {
  clearStageTimers()
  hasProgress.value = true
  currentStage.value = 0
  progress.value = 5
  const schedule = [
    [900, 1, 25],
    [2_300, 2, 45],
    [4_500, 3, 66],
    [7_000, 4, 84],
  ]
  stageTimers = schedule.map(([delay, stage, value]) =>
    window.setTimeout(() => setProgressStage(stage, value), delay),
  )
}

function wait(milliseconds) {
  return new Promise((resolve) => window.setTimeout(resolve, milliseconds))
}

function preferredScrollBehavior() {
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth'
}

async function finishProgress() {
  clearStageTimers()
  const stageValues = [18, 35, 55, 76, 92]
  for (let stage = currentStage.value + 1; stage <= 4; stage += 1) {
    currentStage.value = stage
    progress.value = Math.max(progress.value, stageValues[stage])
    await wait(140)
  }
  currentStage.value = 5
  progress.value = 100
  await wait(260)
}

function handleUploadProgress(event) {
  if (!event.total || currentStage.value > 0) return
  const uploadPercent = Math.min(18, 5 + (event.loaded / event.total) * 13)
  progress.value = Math.max(progress.value, uploadPercent)
}

function fillSample() {
  jobTitle.value = sampleJob.title
  jobDescription.value = sampleJob.description
  requestError.value = ''
}

function handleFileValidation(message) {
  fileError.value = message
  requestError.value = ''
}

function validateForm() {
  if (!resumeFile.value) return '请选择一份 PDF 简历'
  if (!jobTitle.value.trim()) return '请填写有效的岗位名称'
  if (jobDescription.value.trim().length < MIN_JOB_DESCRIPTION_LENGTH) {
    return `岗位描述至少需要 ${MIN_JOB_DESCRIPTION_LENGTH} 个字符`
  }
  return ''
}

async function submitAnalysis() {
  if (isSubmitting.value) return
  const validationError = validateForm()
  if (validationError) {
    requestError.value = validationError
    return
  }

  requestError.value = ''
  fileError.value = ''
  result.value = null
  isSubmitting.value = true
  activeController = new AbortController()
  startProgress()

  try {
    const data = await analyzeResume({
      file: resumeFile.value,
      jobTitle: jobTitle.value,
      jobDescription: jobDescription.value,
      signal: activeController.signal,
      onUploadProgress: handleUploadProgress,
    })
    await finishProgress()
    result.value = normalizeAnalysisResult(data)
    await nextTick()
    document.querySelector('#results-title')?.focus({ preventScroll: true })
    document
      .querySelector('#results')
      ?.scrollIntoView({ behavior: preferredScrollBehavior(), block: 'start' })
  } catch (error) {
    clearStageTimers()
    hasProgress.value = false
    progress.value = 0
    requestError.value = getRequestErrorMessage(error)
  } finally {
    isSubmitting.value = false
    activeController = null
  }
}

function returnToForm() {
  const behavior = preferredScrollBehavior()
  analyzerRef.value?.scrollIntoView({ behavior, block: 'start' })
  window.setTimeout(
    () => document.querySelector('#job-title')?.focus({ preventScroll: true }),
    behavior === 'smooth' ? 450 : 0,
  )
}

onBeforeUnmount(() => {
  clearStageTimers()
  activeController?.abort()
})
</script>

<template>
  <div class="app-shell">
    <a class="skip-link" href="#analyzer">跳到简历分析表单</a>
    <AppHeader />

    <main>
      <section id="analyzer" ref="analyzerRef" class="analyzer-section container" aria-labelledby="form-title">
        <div class="section-intro">
          <div>
            <span class="eyebrow dark-eyebrow">智能分析工作台</span>
            <h2 id="form-title">用一份简历，找到匹配答案</h2>
          </div>
          <p>完成两步信息输入，系统将自动解析简历并生成岗位匹配报告。</p>
        </div>

        <form class="analysis-form" novalidate @submit.prevent="submitAnalysis">
          <section class="form-step" aria-labelledby="upload-title">
            <div class="step-heading">
              <span class="step-number">01</span>
              <div>
                <h3 id="upload-title">上传候选人简历</h3>
                <p>文件不会被长期保存</p>
              </div>
            </div>
            <ResumeUpload
              v-model="resumeFile"
              :disabled="isSubmitting"
              @validation-error="handleFileValidation"
            />
            <p v-if="fileError" class="inline-alert" role="alert">
              <span aria-hidden="true">!</span>{{ fileError }}
            </p>
          </section>

          <div class="form-divider" aria-hidden="true"></div>

          <section class="form-step" aria-labelledby="job-title-heading">
            <div class="step-heading">
              <span class="step-number">02</span>
              <div>
                <h3 id="job-title-heading">填写目标岗位</h3>
                <p>信息越完整，匹配结果越准确</p>
              </div>
            </div>
            <JobDescriptionForm
              v-model:job-title="jobTitle"
              v-model:job-description="jobDescription"
              :disabled="isSubmitting"
              @fill-sample="fillSample"
            />
          </section>

          <div v-if="requestError" class="request-error" role="alert">
            <span class="error-symbol" aria-hidden="true">!</span>
            <div>
              <strong>暂时无法完成分析</strong>
              <p>{{ requestError }}</p>
            </div>
          </div>

          <div class="submit-area">
            <button class="primary-button" type="submit" :disabled="!canSubmit">
              <span v-if="isSubmitting" class="button-spinner" aria-hidden="true"></span>
              <span>{{ isSubmitting ? 'AI 正在分析…' : '开始智能分析' }}</span>
              <span v-if="!isSubmitting" aria-hidden="true">→</span>
            </button>
            <p :class="{ 'is-ready': canSubmit }">
              <span aria-hidden="true">{{ canSubmit ? '✓' : '·' }}</span>{{ submitHint }}
            </p>
          </div>

          <AnalysisProgress
            v-if="hasProgress"
            :current-stage="currentStage"
            :progress="progress"
          />
        </form>
      </section>

      <AnalysisResults v-if="result" :result="result" @reanalyze="returnToForm" />
    </main>

    <footer class="site-footer">
      <div class="container footer-content">
        <a class="brand footer-brand" href="#top">
          <span class="brand-mark" aria-hidden="true">知</span>
          <span>知选 AI</span>
        </a>
        <p>AI 分析仅供招聘辅助，请以公平、审慎和人工复核为前提使用。</p>
        <span>© {{ new Date().getFullYear() }} AI Resume Analyzer</span>
      </div>
    </footer>
  </div>
</template>
