import { describe, expect, it } from 'vitest'
import { getRequestErrorMessage, unwrapApiEnvelope } from '../src/api/resume'

describe('API response envelope', () => {
  it('returns data from a successful unified response', () => {
    const data = { resumeId: 'res_test' }
    expect(unwrapApiEnvelope({ code: 200, message: 'success', data })).toEqual(data)
  })

  it('surfaces a backend business error without leaking internals', () => {
    expect(() =>
      unwrapApiEnvelope({ code: 400, message: '岗位描述过短', data: null }),
    ).toThrow('岗位描述过短')
  })

  it('maps validation errors from the unified response', () => {
    const message = getRequestErrorMessage({
      response: { status: 422, data: { message: '请求数据校验失败' } },
    })
    expect(message).toBe('请求数据校验失败')
  })
})
