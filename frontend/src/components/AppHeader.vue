<template>
  <header class="hero">
    <nav class="topbar container" aria-label="主导航">
      <a class="brand" href="#top" aria-label="知选 AI 简历分析首页">
        <span class="brand-mark" aria-hidden="true">知</span>
        <span>知选 AI</span>
      </a>
      <a class="topbar-link" href="#analyzer">开始分析 <span aria-hidden="true">↘</span></a>
    </nav>

    <div class="hero-content container" id="top">
      <div class="hero-copy">
        <div class="eyebrow"><span class="pulse-dot"></span> AI + 规则混合评估</div>
        <h1>让每一份简历，<br /><span>更接近合适的岗位。</span></h1>
        <p class="hero-lead">
          上传候选人简历，结合岗位要求提取关键信息、识别能力差距，并生成清晰可解释的匹配报告。
        </p>
        <div class="hero-points" aria-label="产品能力">
          <span><b>01</b> 结构化解析</span>
          <span><b>02</b> 关键词匹配</span>
          <span><b>03</b> 多维度评分</span>
        </div>
      </div>

      <aside class="privacy-card" aria-label="隐私与使用提示">
        <div class="privacy-icon" aria-hidden="true">✓</div>
        <div>
          <p class="privacy-title">隐私与使用提示</p>
          <ul>
            <li>上传文件仅用于本次分析，不做长期存储</li>
            <li>简历内容会发送至已配置的 AI 服务</li>
            <li>当前仅支持可提取文字的 PDF，最大 10MB</li>
            <li>分析结果仅供招聘辅助，不应作为唯一决策依据</li>
          </ul>
        </div>
      </aside>
    </div>
  </header>
</template>
