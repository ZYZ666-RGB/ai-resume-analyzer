<script setup>
import { computed } from 'vue'

const props = defineProps({
  currentStage: {
    type: Number,
    default: 0,
  },
  progress: {
    type: Number,
    default: 0,
  },
})

const stages = [
  '正在上传简历',
  '正在解析 PDF',
  '正在提取简历信息',
  '正在分析岗位要求',
  '正在计算匹配度',
  '分析完成',
]

const currentLabel = computed(() => stages[Math.min(props.currentStage, stages.length - 1)])
</script>

<template>
  <section class="progress-panel" aria-live="polite" aria-label="分析进度">
    <div class="progress-copy">
      <div>
        <span class="progress-kicker">处理进度</span>
        <p>{{ currentLabel }}</p>
      </div>
      <strong>{{ Math.round(progress) }}%</strong>
    </div>

    <div
      class="progress-track"
      role="progressbar"
      aria-label="简历分析进度"
      aria-valuemin="0"
      aria-valuemax="100"
      :aria-valuenow="Math.round(progress)"
    >
      <span :style="{ width: `${progress}%` }"></span>
    </div>

    <ol class="stage-list">
      <li
        v-for="(stage, index) in stages"
        :key="stage"
        :class="{
          'is-complete': index < currentStage || currentStage === stages.length - 1,
          'is-current': index === currentStage,
        }"
      >
        <span class="stage-dot" aria-hidden="true">{{ index < currentStage ? '✓' : index + 1 }}</span>
        <span>{{ stage }}</span>
      </li>
    </ol>
  </section>
</template>
