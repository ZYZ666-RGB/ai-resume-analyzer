<script setup>
defineProps({
  jobTitle: {
    type: String,
    default: '',
  },
  jobDescription: {
    type: String,
    default: '',
  },
  disabled: {
    type: Boolean,
    default: false,
  },
})

defineEmits(['update:jobTitle', 'update:jobDescription', 'fill-sample'])
</script>

<template>
  <div class="job-form">
    <div class="field-group">
      <div class="field-heading">
        <label for="job-title">岗位名称 <span aria-hidden="true">*</span></label>
        <span>用于确定评估方向</span>
      </div>
      <input
        id="job-title"
        class="field-input"
        type="text"
        :value="jobTitle"
        :disabled="disabled"
        maxlength="120"
        autocomplete="organization-title"
        placeholder="例如：Python 后端开发工程师"
        required
        @input="$emit('update:jobTitle', $event.target.value)"
      />
    </div>

    <div class="field-group">
      <div class="field-heading">
        <label for="job-description">岗位描述 <span aria-hidden="true">*</span></label>
        <button class="sample-button" type="button" :disabled="disabled" @click="$emit('fill-sample')">
          <span aria-hidden="true">✦</span> 一键填入示例
        </button>
      </div>
      <textarea
        id="job-description"
        class="field-textarea"
        :value="jobDescription"
        :disabled="disabled"
        maxlength="5000"
        rows="9"
        aria-describedby="jd-help"
        placeholder="粘贴完整岗位职责、技能要求、经验与学历要求。描述越具体，匹配结果越有参考价值。"
        required
        @input="$emit('update:jobDescription', $event.target.value)"
      ></textarea>
      <div id="jd-help" class="field-footer">
        <span>建议至少填写 20 个字符</span>
        <span>{{ jobDescription.length }} / 5000</span>
      </div>
    </div>
  </div>
</template>
