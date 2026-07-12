import { describe, expect, it } from 'vitest'
import {
  JOB_DESCRIPTION_MAX_LENGTH,
  JOB_DESCRIPTION_MIN_LENGTH,
  JOB_TITLE_MAX_LENGTH,
  SAMPLE_JOB,
  canAnalyze,
} from '../src/utils/analyzer'

describe('analyzer form policy', () => {
  it('ships a complete example JD that satisfies backend limits', () => {
    expect(SAMPLE_JOB.title.length).toBeLessThanOrEqual(JOB_TITLE_MAX_LENGTH)
    expect(SAMPLE_JOB.description.length).toBeGreaterThanOrEqual(JOB_DESCRIPTION_MIN_LENGTH)
    expect(SAMPLE_JOB.description.length).toBeLessThanOrEqual(JOB_DESCRIPTION_MAX_LENGTH)
  })

  it('keeps submission disabled until every required input is ready', () => {
    const ready = {
      file: { name: 'resume.pdf' },
      jobTitle: SAMPLE_JOB.title,
      jobDescription: SAMPLE_JOB.description,
    }
    expect(canAnalyze({ ...ready, file: null })).toBe(false)
    expect(canAnalyze({ ...ready, jobTitle: ' ' })).toBe(false)
    expect(canAnalyze({ ...ready, jobDescription: 'too short' })).toBe(false)
    expect(canAnalyze({ ...ready, isSubmitting: true })).toBe(false)
    expect(canAnalyze(ready)).toBe(true)
  })

  it('rejects values beyond the client and server contract', () => {
    expect(
      canAnalyze({
        file: {},
        jobTitle: 'x'.repeat(JOB_TITLE_MAX_LENGTH + 1),
        jobDescription: SAMPLE_JOB.description,
      }),
    ).toBe(false)
    expect(
      canAnalyze({
        file: {},
        jobTitle: SAMPLE_JOB.title,
        jobDescription: 'x'.repeat(JOB_DESCRIPTION_MAX_LENGTH + 1),
      }),
    ).toBe(false)
  })
})
