<script setup>
import { nextTick, ref } from 'vue'
import { formatFileSize } from '../utils/formatters'

const MAX_FILE_SIZE = 10 * 1024 * 1024

const props = defineProps({
  modelValue: {
    type: Object,
    default: null,
  },
  disabled: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['update:modelValue', 'validation-error'])

const inputRef = ref(null)
const dropzoneRef = ref(null)
const reselectButtonRef = ref(null)
const isDragging = ref(false)

function focusDropzone() {
  nextTick(() => dropzoneRef.value?.focus())
}

function focusSelectedFileAction() {
  nextTick(() => reselectButtonRef.value?.focus())
}

function clearInput() {
  if (inputRef.value) inputRef.value.value = ''
}

function validateAndSelect(files) {
  if (props.disabled) return
  const list = Array.from(files || [])

  if (list.length !== 1) {
    emit('validation-error', '每次只能上传一份 PDF 简历')
    clearInput()
    focusDropzone()
    return
  }

  const file = list[0]
  const hasPdfExtension = file.name.toLowerCase().endsWith('.pdf')
  const normalizedMime = file.type.toLowerCase()
  const hasPdfMime =
    !normalizedMime || normalizedMime === 'application/pdf' || normalizedMime === 'application/x-pdf'

  if (!hasPdfExtension || !hasPdfMime) {
    emit('validation-error', '仅支持 PDF 格式文件，请重新选择')
    clearInput()
    focusDropzone()
    return
  }

  if (file.size > MAX_FILE_SIZE) {
    emit('validation-error', '文件超过 10MB，请压缩后重新上传')
    clearInput()
    focusDropzone()
    return
  }

  if (file.size === 0) {
    emit('validation-error', '文件内容为空，请重新选择')
    clearInput()
    focusDropzone()
    return
  }

  emit('validation-error', '')
  emit('update:modelValue', file)
  focusSelectedFileAction()
}

function handleInput(event) {
  validateAndSelect(event.target.files)
}

function handleDrop(event) {
  isDragging.value = false
  validateAndSelect(event.dataTransfer.files)
}

function openFilePicker() {
  if (!props.disabled) inputRef.value?.click()
}

function removeFile() {
  if (props.disabled) return
  clearInput()
  emit('validation-error', '')
  emit('update:modelValue', null)
  focusDropzone()
}
</script>

<template>
  <div class="upload-control">
    <input
      id="resume-file"
      ref="inputRef"
      class="visually-hidden"
      type="file"
      accept=".pdf,application/pdf"
      :disabled="disabled"
      tabindex="-1"
      aria-label="选择 PDF 简历"
      @change="handleInput"
    />

    <div
      v-if="!modelValue"
      ref="dropzoneRef"
      class="dropzone"
      :class="{ 'is-dragging': isDragging, 'is-disabled': disabled }"
      role="button"
      :tabindex="disabled ? -1 : 0"
      :aria-disabled="disabled"
      aria-describedby="upload-help"
      @click="openFilePicker"
      @keydown.enter.prevent="openFilePicker"
      @keydown.space.prevent="openFilePicker"
      @dragenter.prevent="isDragging = true"
      @dragover.prevent="isDragging = true"
      @dragleave.prevent="isDragging = false"
      @drop.prevent="handleDrop"
    >
      <div class="upload-symbol" aria-hidden="true"><span>↑</span></div>
      <p class="dropzone-title">拖拽简历到这里，或 <span>点击选择</span></p>
      <p id="upload-help" class="dropzone-help">仅支持单个文本型 PDF · 最大 10MB</p>
    </div>

    <div v-else class="selected-file" aria-live="polite">
      <div class="pdf-badge" aria-hidden="true">PDF</div>
      <div class="file-meta">
        <p class="file-name" :title="modelValue.name">{{ modelValue.name }}</p>
        <p>{{ formatFileSize(modelValue.size) }} · 已准备好分析</p>
      </div>
      <div class="file-actions">
        <button
          ref="reselectButtonRef"
          class="text-button"
          type="button"
          :disabled="disabled"
          @click="openFilePicker"
        >
          重选
        </button>
        <button
          class="icon-button"
          type="button"
          :disabled="disabled"
          aria-label="移除已选择的简历"
          title="移除文件"
          @click="removeFile"
        >
          ×
        </button>
      </div>
    </div>
  </div>
</template>
