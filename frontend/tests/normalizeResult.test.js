import { describe, expect, it } from 'vitest'
import { normalizeAnalysisResult } from '../src/utils/normalizeResult'

describe('analysis result normalization', () => {
  it('supports camelCase and clamps scores', () => {
    const result = normalizeAnalysisResult({
      resumeId: 'res_1',
      resume: { basicInfo: { name: 'Alice' }, background: { skills: ['Python'] } },
      job: { jobTitle: 'Engineer', coreSkills: ['Python'] },
      match: { overallScore: 120, skillScore: -10, matchedKeywords: ['Python'] },
    })

    expect(result.resume.basicInfo.name).toBe('Alice')
    expect(result.job.title).toBe('Engineer')
    expect(result.match.overallScore).toBe(100)
    expect(result.match.skillScore).toBe(0)
  })

  it('supports snake_case payloads and flattened matching fields', () => {
    const result = normalizeAnalysisResult({
      resume_id: 'res_2',
      cache_hit: true,
      resume_info: {
        basic_info: { full_name: 'Bob' },
        background: { work_years: 3, skills: 'Python, Redis' },
      },
      job_analysis: { job_title: 'Backend Engineer', core_skills: ['Python'] },
      overall_score: 80,
      ai_used: true,
      analysis_mode: 'ai',
      warnings: ['人工复核'],
      recommendation_level: '较为匹配',
    })

    expect(result.resumeId).toBe('res_2')
    expect(result.cacheHit).toBe(true)
    expect(result.resume.background.skills).toEqual(['Python', 'Redis'])
    expect(result.match.overallScore).toBe(80)
    expect(result.match.aiUsed).toBe(true)
    expect(result.match.analysisMode).toBe('ai')
    expect(result.match.warnings).toEqual(['人工复核'])
    expect(result.match.recommendationLevel).toBe('较为匹配')
  })

  it('treats legacy responses without provenance as a rules fallback', () => {
    const result = normalizeAnalysisResult({ match: { aiScore: 70 } })
    expect(result.match.aiUsed).toBe(false)
    expect(result.match.analysisMode).toBe('rules')
  })
})
