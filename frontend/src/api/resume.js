import axios from 'axios'
import http from './http'

function createBusinessError(message) {
  const error = new Error(message)
  error.name = 'ApiBusinessError'
  return error
}

export async function analyzeResume({ file, jobTitle, jobDescription, signal, onUploadProgress }) {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('jobTitle', jobTitle.trim())
  formData.append('jobDescription', jobDescription.trim())

  const response = await http.post('/api/resumes/analyze', formData, {
    signal,
    onUploadProgress,
  })
  const envelope = response.data

  if (!envelope || typeof envelope !== 'object' || Array.isArray(envelope)) {
    throw createBusinessError('分析服务返回格式异常，请检查 API 地址配置')
  }

  if (envelope && Object.hasOwn(envelope, 'code') && Number(envelope.code) !== 200) {
    throw createBusinessError(envelope.message || '分析失败，请稍后重试')
  }

  if (Object.hasOwn(envelope, 'code')) {
    if (!envelope.data || typeof envelope.data !== 'object' || Array.isArray(envelope.data)) {
      throw createBusinessError('分析服务未返回有效结果，请稍后重试')
    }
    return envelope.data
  }

  return envelope
}

function validationMessage(detail) {
  if (typeof detail === 'string') return detail
  if (!Array.isArray(detail)) return ''

  return detail
    .map((item) => item?.msg)
    .filter(Boolean)
    .slice(0, 2)
    .join('；')
}

export function getRequestErrorMessage(error) {
  if (error?.name === 'ApiBusinessError') {
    return error.message
  }

  if (axios.isCancel(error) || error?.name === 'CanceledError') {
    return '分析已取消'
  }

  if (error?.code === 'ECONNABORTED') {
    return '分析时间较长且已超时，请稍后重试'
  }

  if (!error?.response) {
    return '暂时无法连接分析服务，请检查网络或服务地址后重试'
  }

  const status = error.response.status
  const body = error.response.data
  const serverMessage =
    (typeof body?.message === 'string' && body.message) || validationMessage(body?.detail)

  if (serverMessage) return serverMessage

  const statusMessages = {
    400: '提交内容有误，请检查文件与岗位描述',
    404: '分析服务地址不存在，请检查配置',
    413: '文件超过 10MB，请压缩后重试',
    422: '文件或岗位信息未通过校验',
    500: '分析服务暂时异常，请稍后重试',
    502: 'AI 服务暂时不可用，请稍后重试',
    504: 'AI 服务响应超时，请稍后重试',
  }

  return statusMessages[status] || '分析失败，请稍后重试'
}
