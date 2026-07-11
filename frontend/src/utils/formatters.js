export function formatFileSize(bytes = 0) {
  if (!Number.isFinite(bytes) || bytes <= 0) return '0 KB'
  const units = ['B', 'KB', 'MB', 'GB']
  const index = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1)
  const value = bytes / 1024 ** index
  const digits = index === 0 || value >= 10 ? 0 : 1
  return `${value.toFixed(digits)} ${units[index]}`
}

export function displayValue(value, fallback = '未提供') {
  if (value === null || value === undefined || value === '') return fallback
  if (Array.isArray(value)) return value.filter(Boolean).join('、') || fallback
  if (typeof value === 'object') {
    return value.name || value.title || value.value || fallback
  }
  return String(value)
}

export function toArray(value) {
  if (Array.isArray(value)) return value.filter((item) => item !== null && item !== undefined)
  if (value === null || value === undefined || value === '') return []
  return [value]
}

export function toTextArray(value) {
  if (typeof value === 'string') {
    return value
      .split(/[\n,，;；、]/)
      .map((item) => item.trim())
      .filter(Boolean)
  }

  return toArray(value)
    .map((item) => {
      if (typeof item === 'string' || typeof item === 'number') return String(item)
      return item?.name || item?.skill || item?.title || item?.value || ''
    })
    .filter(Boolean)
}

export function safeScore(value) {
  const score = Number(value)
  if (!Number.isFinite(score)) return 0
  return Math.round(Math.min(100, Math.max(0, score)))
}

export function formatPeriod(startDate, endDate) {
  const start = displayValue(startDate, '')
  const end = displayValue(endDate, '')
  if (!start && !end) return '时间未提供'
  return `${start || '未知'} — ${end || '至今'}`
}

export function formatWorkYears(value) {
  if (value === null || value === undefined || value === '') return '未提供'
  if (typeof value === 'number' && Number.isFinite(value)) return `${value} 年`
  const text = String(value)
  return /^\d+(?:\.\d+)?$/.test(text.trim()) ? `${text} 年` : text
}

export function descriptionLines(value) {
  if (Array.isArray(value)) return value.map((line) => displayValue(line, '')).filter(Boolean)
  if (typeof value !== 'string') return value ? [displayValue(value)] : []
  return value
    .split(/\n+/)
    .map((line) => line.replace(/^[-•·]\s*/, '').trim())
    .filter(Boolean)
}
