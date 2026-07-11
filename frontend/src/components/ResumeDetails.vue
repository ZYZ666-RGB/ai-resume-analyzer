<script setup>
import { descriptionLines, displayValue, formatPeriod, formatWorkYears } from '../utils/formatters'

defineProps({
  resume: {
    type: Object,
    required: true,
  },
})
</script>

<template>
  <div class="resume-details">
    <section class="result-section profile-section">
      <div class="section-heading">
        <div>
          <span class="section-index">01</span>
          <h3>候选人概览</h3>
        </div>
        <span class="section-note">从简历原文提取</span>
      </div>

      <div class="profile-card">
        <div class="avatar" aria-hidden="true">
          {{ displayValue(resume.basicInfo.name, '?').slice(0, 1) }}
        </div>
        <div class="profile-main">
          <h4>{{ displayValue(resume.basicInfo.name, '姓名未识别') }}</h4>
          <p>{{ displayValue(resume.jobInfo.jobIntention, '求职意向未提供') }}</p>
        </div>
        <dl class="profile-facts">
          <div>
            <dt>电话</dt>
            <dd>{{ displayValue(resume.basicInfo.phone) }}</dd>
          </div>
          <div>
            <dt>邮箱</dt>
            <dd class="breakable">{{ displayValue(resume.basicInfo.email) }}</dd>
          </div>
          <div>
            <dt>所在地</dt>
            <dd>{{ displayValue(resume.basicInfo.address) }}</dd>
          </div>
          <div>
            <dt>工作年限</dt>
            <dd>{{ formatWorkYears(resume.background.workYears) }}</dd>
          </div>
          <div>
            <dt>期望薪资</dt>
            <dd>{{ displayValue(resume.jobInfo.expectedSalary) }}</dd>
          </div>
        </dl>
      </div>
    </section>

    <section class="result-section">
      <div class="section-heading">
        <div>
          <span class="section-index">02</span>
          <h3>专业技能</h3>
        </div>
        <span class="section-note">{{ resume.background.skills.length }} 项</span>
      </div>
      <div v-if="resume.background.skills.length" class="tag-cloud skill-cloud">
        <span v-for="skill in resume.background.skills" :key="skill" class="tag skill-tag">{{ skill }}</span>
      </div>
      <p v-else class="empty-state">简历中暂未识别到明确的技能标签</p>
    </section>

    <section class="result-section">
      <div class="section-heading">
        <div>
          <span class="section-index">03</span>
          <h3>教育经历</h3>
        </div>
        <span class="section-note">{{ resume.background.education.length }} 段</span>
      </div>
      <div v-if="resume.background.education.length" class="timeline-list">
        <article
          v-for="(education, index) in resume.background.education"
          :key="`${education.school}-${index}`"
          class="timeline-item"
        >
          <span class="timeline-marker" aria-hidden="true"></span>
          <div class="timeline-copy">
            <div class="timeline-title">
              <div>
                <h4>{{ displayValue(education.school, '学校未提供') }}</h4>
                <p>{{ displayValue(education.major, '专业未提供') }} · {{ displayValue(education.degree, '学历未提供') }}</p>
              </div>
              <time>{{ formatPeriod(education.startDate, education.endDate) }}</time>
            </div>
          </div>
        </article>
      </div>
      <p v-else class="empty-state">简历中暂未识别到教育经历</p>
    </section>

    <section class="result-section">
      <div class="section-heading">
        <div>
          <span class="section-index">04</span>
          <h3>工作经历</h3>
        </div>
        <span class="section-note">{{ resume.background.workExperiences.length }} 段</span>
      </div>
      <div v-if="resume.background.workExperiences.length" class="timeline-list">
        <article
          v-for="(work, index) in resume.background.workExperiences"
          :key="`${work.company}-${index}`"
          class="timeline-item"
        >
          <span class="timeline-marker" aria-hidden="true"></span>
          <div class="timeline-copy">
            <div class="timeline-title">
              <div>
                <h4>{{ displayValue(work.company, '公司未提供') }}</h4>
                <p>{{ displayValue(work.position, '职位未提供') }}</p>
              </div>
              <time>{{ formatPeriod(work.startDate, work.endDate) }}</time>
            </div>
            <ul v-if="descriptionLines(work.description).length" class="description-list">
              <li v-for="line in descriptionLines(work.description)" :key="line">{{ line }}</li>
            </ul>
            <p v-else class="item-empty">工作内容未提供</p>
          </div>
        </article>
      </div>
      <p v-else class="empty-state">简历中暂未识别到工作经历</p>
    </section>

    <section class="result-section">
      <div class="section-heading">
        <div>
          <span class="section-index">05</span>
          <h3>项目经历</h3>
        </div>
        <span class="section-note">{{ resume.background.projects.length }} 个</span>
      </div>
      <div v-if="resume.background.projects.length" class="project-grid">
        <article
          v-for="(project, index) in resume.background.projects"
          :key="`${project.name}-${index}`"
          class="project-card"
        >
          <div class="project-number" aria-hidden="true">{{ String(index + 1).padStart(2, '0') }}</div>
          <h4>{{ displayValue(project.name, '项目名称未提供') }}</h4>
          <p class="project-role">{{ displayValue(project.role, '角色未提供') }}</p>
          <div v-if="project.technologies.length" class="tag-cloud compact-tags">
            <span v-for="technology in project.technologies" :key="technology" class="tag">{{ technology }}</span>
          </div>
          <ul v-if="descriptionLines(project.description).length" class="description-list">
            <li v-for="line in descriptionLines(project.description)" :key="line">{{ line }}</li>
          </ul>
          <p v-else class="item-empty">项目说明未提供</p>
        </article>
      </div>
      <p v-else class="empty-state">简历中暂未识别到项目经历</p>
    </section>

    <section class="result-section">
      <div class="section-heading">
        <div>
          <span class="section-index">06</span>
          <h3>证书与荣誉</h3>
        </div>
        <span class="section-note">{{ resume.background.certificates.length }} 项</span>
      </div>
      <div v-if="resume.background.certificates.length" class="certificate-list">
        <span v-for="certificate in resume.background.certificates" :key="certificate">
          <i aria-hidden="true">✓</i>{{ certificate }}
        </span>
      </div>
      <p v-else class="empty-state">简历中暂未识别到证书或荣誉</p>
    </section>
  </div>
</template>
