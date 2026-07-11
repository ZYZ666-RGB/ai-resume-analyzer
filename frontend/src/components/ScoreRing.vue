<script setup>
import { computed } from 'vue'
import { safeScore } from '../utils/formatters'

const props = defineProps({
  score: {
    type: Number,
    default: 0,
  },
  recommendation: {
    type: String,
    default: '',
  },
})

const normalizedScore = computed(() => safeScore(props.score))
const scoreColor = computed(() => {
  if (normalizedScore.value >= 85) return '#0f9f80'
  if (normalizedScore.value >= 70) return '#3f6df6'
  if (normalizedScore.value >= 50) return '#d28a18'
  return '#d95656'
})
const ringStyle = computed(() => ({
  '--score-angle': `${normalizedScore.value * 3.6}deg`,
  '--score-color': scoreColor.value,
}))
</script>

<template>
  <div class="score-figure">
    <div
      class="score-ring"
      :style="ringStyle"
      role="img"
      :aria-label="`综合岗位匹配分 ${normalizedScore} 分，${recommendation || '暂无推荐等级'}`"
    >
      <div class="score-ring-inner">
        <strong>{{ normalizedScore }}</strong>
        <span>/ 100</span>
      </div>
    </div>
    <div class="score-caption">
      <span>综合匹配分</span>
      <strong :style="{ color: scoreColor }">{{ recommendation || '待评估' }}</strong>
    </div>
  </div>
</template>
