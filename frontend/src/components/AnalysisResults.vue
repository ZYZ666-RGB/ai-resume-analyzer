<script setup>
import { computed } from 'vue'
import ResumeDetails from './ResumeDetails.vue'
import ScoreBreakdown from './ScoreBreakdown.vue'
import ScoreRing from './ScoreRing.vue'
import { displayValue, formatWorkYears, safeScore } from '../utils/formatters'

const props = defineProps({
  result: {
    type: Object,
    required: true,
  },
})

defineEmits(['reanalyze'])

const recommendation = computed(() => {
  if (props.result.match.recommendationLevel) return props.result.match.recommendationLevel
  const score = safeScore(props.result.match.overallScore)
  if (score >= 85) return '高度匹配'
  if (score >= 70) return '较为匹配'
  if (score >= 50) return '一般匹配'
  return '匹配度较低'
})

const hasJobDetails = computed(() => {
  const job = props.result.job
  return Boolean(
    job.title ||
      job.coreSkills.length ||
      job.bonusSkills.length ||
      job.educationRequirement ||
      job.workYearsRequirement ||
      job.responsibilities.length ||
      job.industry ||
      job.otherRequirements.length,
  )
})
</script>

<template>
  <section id="results" class="results" aria-labelledby="results-title">
    <div class="results-heading">
      <div>
        <span class="eyebrow result-eyebrow"><span class="pulse-dot"></span> 分析已完成</span>
        <h2 id="results-title" tabindex="-1">候选人匹配报告</h2>
        <p>评分由规则计算与 AI 综合评价共同生成，请结合面试判断。</p>
      </div>
      <div class="results-actions">
        <div class="result-meta" aria-label="分析元数据">
          <span v-if="result.pageCount">{{ result.pageCount }} 页 PDF</span>
          <span :class="result.cacheHit ? 'cache-hit' : 'cache-miss'">
            <i aria-hidden="true"></i>{{ result.cacheHit ? '缓存加速' : '实时分析' }}
          </span>
        </div>
        <button class="secondary-button" type="button" @click="$emit('reanalyze')">
          调整岗位并重新分析
        </button>
      </div>
    </div>

    <div class="score-overview">
      <ScoreRing :score="result.match.overallScore" :recommendation="recommendation" />
      <div class="summary-panel">
        <span class="summary-label">AI 综合评价</span>
        <blockquote>
          {{ displayValue(result.match.summary, '暂未生成综合评价，请结合分项评分与履历信息判断。') }}
        </blockquote>
        <div class="recommendation-row">
          <span>推荐等级</span>
          <strong>{{ recommendation }}</strong>
        </div>
      </div>
      <div class="breakdown-panel">
        <div class="mini-heading">
          <h3>分项评分</h3>
          <span>0–100</span>
        </div>
        <ScoreBreakdown :match="result.match" />
      </div>
    </div>

    <div class="keyword-grid">
      <section class="keyword-card matched-card">
        <div class="keyword-heading">
          <span class="keyword-icon" aria-hidden="true">✓</span>
          <div>
            <h3>已匹配关键词</h3>
            <p>{{ result.match.matchedKeywords.length }} 项能力得到印证</p>
          </div>
        </div>
        <div v-if="result.match.matchedKeywords.length" class="tag-cloud">
          <span v-for="keyword in result.match.matchedKeywords" :key="keyword" class="tag matched-tag">
            {{ keyword }}
          </span>
        </div>
        <p v-else class="empty-state small">暂无明确匹配的岗位关键词</p>
      </section>

      <section class="keyword-card missing-card">
        <div class="keyword-heading">
          <span class="keyword-icon" aria-hidden="true">!</span>
          <div>
            <h3>待补充关键词</h3>
            <p>{{ result.match.missingKeywords.length }} 项岗位要求未体现</p>
          </div>
        </div>
        <div v-if="result.match.missingKeywords.length" class="tag-cloud">
          <span v-for="keyword in result.match.missingKeywords" :key="keyword" class="tag missing-tag">
            {{ keyword }}
          </span>
        </div>
        <p v-else class="empty-state small">未发现明显缺失的岗位关键词</p>
      </section>
    </div>

    <div class="insight-grid">
      <section class="insight-card advantage-card">
        <div class="insight-title">
          <span aria-hidden="true">↗</span>
          <h3>候选人优势</h3>
        </div>
        <ol v-if="result.match.advantages.length">
          <li v-for="(advantage, index) in result.match.advantages" :key="advantage">
            <span>{{ String(index + 1).padStart(2, '0') }}</span>
            <p>{{ advantage }}</p>
          </li>
        </ol>
        <p v-else class="empty-state">暂未识别到明确优势</p>
      </section>

      <section class="insight-card risk-card">
        <div class="insight-title">
          <span aria-hidden="true">↘</span>
          <h3>潜在风险</h3>
        </div>
        <ol v-if="result.match.risks.length">
          <li v-for="(risk, index) in result.match.risks" :key="risk">
            <span>{{ String(index + 1).padStart(2, '0') }}</span>
            <p>{{ risk }}</p>
          </li>
        </ol>
        <p v-else class="empty-state">暂未识别到明确风险</p>
      </section>
    </div>

    <section class="result-section job-analysis-section">
      <div class="section-heading">
        <div>
          <span class="section-index">JD</span>
          <h3>岗位要求识别</h3>
        </div>
        <span class="section-note">AI 结构化提取</span>
      </div>
      <div v-if="hasJobDetails" class="job-analysis-grid">
        <div class="job-title-block">
          <span>目标岗位</span>
          <strong>{{ displayValue(result.job.title) }}</strong>
          <p>{{ displayValue(result.job.industry, '行业方向未提供') }}</p>
        </div>
        <dl class="job-requirements">
          <div>
            <dt>学历要求</dt>
            <dd>{{ displayValue(result.job.educationRequirement) }}</dd>
          </div>
          <div>
            <dt>经验要求</dt>
            <dd>{{ formatWorkYears(result.job.workYearsRequirement) }}</dd>
          </div>
        </dl>
        <div class="job-skill-block">
          <h4>核心技能</h4>
          <div v-if="result.job.coreSkills.length" class="tag-cloud compact-tags">
            <span v-for="skill in result.job.coreSkills" :key="skill" class="tag skill-tag">{{ skill }}</span>
          </div>
          <p v-else class="item-empty">暂未提取到核心技能</p>
        </div>
        <div class="job-skill-block">
          <h4>加分技能</h4>
          <div v-if="result.job.bonusSkills.length" class="tag-cloud compact-tags">
            <span v-for="skill in result.job.bonusSkills" :key="skill" class="tag">{{ skill }}</span>
          </div>
          <p v-else class="item-empty">暂未提取到加分技能</p>
        </div>
      </div>
      <p v-else class="empty-state">接口未返回结构化岗位要求，匹配评分仍可正常查看</p>
    </section>

    <ResumeDetails :resume="result.resume" />
  </section>
</template>
