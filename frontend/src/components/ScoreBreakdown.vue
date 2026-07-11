<script setup>
import { safeScore } from '../utils/formatters'

defineProps({
  match: {
    type: Object,
    required: true,
  },
})

const dimensions = [
  { key: 'skillScore', label: '技能匹配', weight: '40%' },
  { key: 'experienceScore', label: '工作经验', weight: '20%' },
  { key: 'projectScore', label: '项目相关', weight: '20%' },
  { key: 'educationScore', label: '学历匹配', weight: '10%' },
  { key: 'aiScore', label: 'AI 评价', weight: '10%' },
]
</script>

<template>
  <div class="score-breakdown">
    <div v-for="item in dimensions" :key="item.key" class="score-row">
      <div class="score-row-heading">
        <span>{{ item.label }} <small>权重 {{ item.weight }}</small></span>
        <strong>{{ safeScore(match[item.key]) }}</strong>
      </div>
      <div
        class="score-bar"
        role="progressbar"
        :aria-label="`${item.label}评分`"
        aria-valuemin="0"
        aria-valuemax="100"
        :aria-valuenow="safeScore(match[item.key])"
      >
        <span :style="{ width: `${safeScore(match[item.key])}%` }"></span>
      </div>
    </div>
  </div>
</template>
