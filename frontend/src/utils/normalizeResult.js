import { safeScore, toArray, toTextArray } from './formatters'

const firstDefined = (...values) =>
  values.find((value) => value !== undefined && value !== null)

const asObject = (value) => (value && typeof value === 'object' && !Array.isArray(value) ? value : {})

function normalizeEducation(value) {
  return toArray(value).map((item) => {
    const source = asObject(item)
    return {
      school: firstDefined(source.school, source.schoolName, source.school_name),
      major: firstDefined(source.major, source.specialty),
      degree: firstDefined(source.degree, source.education),
      startDate: firstDefined(source.startDate, source.start_date),
      endDate: firstDefined(source.endDate, source.end_date),
    }
  })
}

function normalizeWorkExperiences(value) {
  return toArray(value).map((item) => {
    const source = asObject(item)
    return {
      company: firstDefined(source.company, source.companyName, source.company_name),
      position: firstDefined(source.position, source.title, source.jobTitle, source.job_title),
      startDate: firstDefined(source.startDate, source.start_date),
      endDate: firstDefined(source.endDate, source.end_date),
      description: firstDefined(source.description, source.responsibilities, source.content),
    }
  })
}

function normalizeProjects(value) {
  return toArray(value).map((item) => {
    const source = asObject(item)
    return {
      name: firstDefined(source.name, source.projectName, source.project_name),
      role: firstDefined(source.role, source.position),
      technologies: toTextArray(
        firstDefined(source.technologies, source.techStack, source.tech_stack, source.skills),
      ),
      description: firstDefined(source.description, source.content, source.responsibilities),
    }
  })
}

function normalizeMatch(raw) {
  const source = asObject(
    firstDefined(raw.match, raw.matchResult, raw.match_result, raw.matchingResult, raw.matching_result),
  )
  // Some backends flatten matching fields directly into data.
  const definedSource = Object.fromEntries(
    Object.entries(source).filter(([, value]) => value !== undefined && value !== null),
  )
  const match = { ...raw, ...definedSource }
  const explicitAiUsed = firstDefined(match.aiUsed, match.ai_used)
  const requestedMode = firstDefined(match.analysisMode, match.analysis_mode)
  const claimsAi = explicitAiUsed === true || (explicitAiUsed == null && requestedMode === 'ai')
  const aiUsed = claimsAi && requestedMode !== 'rules'

  return {
    overallScore: safeScore(firstDefined(match.overallScore, match.overall_score, match.score)),
    skillScore: safeScore(firstDefined(match.skillScore, match.skill_score)),
    experienceScore: safeScore(firstDefined(match.experienceScore, match.experience_score)),
    projectScore: safeScore(firstDefined(match.projectScore, match.project_score)),
    educationScore: safeScore(firstDefined(match.educationScore, match.education_score)),
    aiScore: safeScore(firstDefined(match.aiScore, match.ai_score)),
    matchedKeywords: toTextArray(
      firstDefined(match.matchedKeywords, match.matched_keywords, match.matchedSkills),
    ),
    missingKeywords: toTextArray(
      firstDefined(match.missingKeywords, match.missing_keywords, match.missingSkills),
    ),
    advantages: toTextArray(firstDefined(match.advantages, match.strengths)),
    risks: toTextArray(firstDefined(match.risks, match.concerns, match.weaknesses)),
    summary: firstDefined(match.summary, match.evaluation, match.aiSummary, match.ai_summary),
    recommendationLevel: firstDefined(
      match.recommendationLevel,
      match.recommendation_level,
      match.recommendation,
    ),
    aiUsed,
    analysisMode: aiUsed ? 'ai' : 'rules',
    warnings: toTextArray(firstDefined(match.warnings, match.warning)),
  }
}

function normalizeJob(raw) {
  const source = asObject(
    firstDefined(raw.job, raw.jobAnalysis, raw.job_analysis, raw.jobInfo, raw.job_info),
  )
  return {
    title: firstDefined(source.title, source.jobTitle, source.job_title, raw.jobTitle),
    coreSkills: toTextArray(firstDefined(source.coreSkills, source.core_skills, source.requiredSkills)),
    bonusSkills: toTextArray(firstDefined(source.bonusSkills, source.bonus_skills, source.preferredSkills)),
    educationRequirement: firstDefined(
      source.educationRequirement,
      source.education_requirement,
      source.education,
    ),
    workYearsRequirement: firstDefined(
      source.workYearsRequirement,
      source.work_years_requirement,
      source.experienceRequirement,
    ),
    responsibilities: toTextArray(firstDefined(source.responsibilities, source.duties)),
    industry: firstDefined(source.industry, source.businessDirection, source.business_direction),
    otherRequirements: toTextArray(firstDefined(source.otherRequirements, source.other_requirements)),
  }
}

export function normalizeAnalysisResult(payload) {
  const raw = asObject(payload?.data ?? payload)
  const resumeSource = asObject(
    firstDefined(raw.resume, raw.resumeInfo, raw.resume_info, raw.parsedResume, raw.parsed_resume),
  )
  const resume = Object.keys(resumeSource).length ? resumeSource : raw
  const basic = asObject(firstDefined(resume.basicInfo, resume.basic_info))
  const jobInfo = asObject(firstDefined(resume.jobInfo, resume.job_info))
  const background = asObject(firstDefined(resume.background, resume.experience))

  return {
    resumeId: firstDefined(raw.resumeId, raw.resume_id),
    pageCount: firstDefined(raw.pageCount, raw.page_count),
    resumeHash: firstDefined(raw.resumeHash, raw.resume_hash),
    cacheHit: Boolean(firstDefined(raw.cacheHit, raw.cache_hit, false)),
    resume: {
      basicInfo: {
        name: firstDefined(basic.name, basic.fullName, basic.full_name),
        phone: firstDefined(basic.phone, basic.mobile),
        email: basic.email,
        address: firstDefined(basic.address, basic.location),
      },
      jobInfo: {
        jobIntention: firstDefined(
          jobInfo.jobIntention,
          jobInfo.job_intention,
          jobInfo.targetPosition,
        ),
        expectedSalary: firstDefined(jobInfo.expectedSalary, jobInfo.expected_salary),
      },
      background: {
        workYears: firstDefined(background.workYears, background.work_years, background.experienceYears),
        education: normalizeEducation(firstDefined(background.education, background.educations)),
        workExperiences: normalizeWorkExperiences(
          firstDefined(background.workExperiences, background.work_experiences, background.experience),
        ),
        skills: toTextArray(firstDefined(background.skills, resume.skills)),
        projects: normalizeProjects(firstDefined(background.projects, resume.projects)),
        certificates: toTextArray(
          firstDefined(background.certificates, background.honors, resume.certificates),
        ),
      },
    },
    job: normalizeJob(raw),
    match: normalizeMatch(raw),
  }
}
