// DeerFlow 学习系列 - 导航生成脚本

const CHAPTERS = [
  // 第一部分：基础概念
  { num: '00', title: 'Agent 基础概念与设计思想', file: '00-agent-fundamentals.html', group: '第一部分：基础概念', desc: '建立 Agent 基础认知，为后续 DeerFlow 源码学习做准备。' },
  { num: '01', title: 'LangGraph 框架基础', file: '01-langgraph-basics.html', group: '第一部分：基础概念', desc: '补齐 LangGraph 主概念，帮助理解 DeerFlow 的 graph 运行主线。' },
  { num: '02', title: 'LLM调用与工具系统', file: '02-llm-and-tools.html', group: '第一部分：基础概念', desc: '从 DeerFlow 的模型与工具装配路径理解 agent 能力底座。' },
  { num: '03', title: 'DeerFlow 整体架构概览', file: '03-deerflow-overview.html', group: '第一部分：基础概念', desc: '先建立 DeerFlow 默认系统主路径与组件关系的整体心智图。' },
  
  // 第二部分：核心模块
  { num: '10', title: 'Agent执行引擎的设计与实现', file: '10-agent-execution-engine.html', group: '第二部分：核心模块深度学习', desc: '追踪 DeerFlow 的 agent 构建、middleware 链和 run/stream 所有权。' },
  { num: '11', title: 'Skills系统：Agent的能力扩展', file: '11-skills-system.html', group: '第二部分：核心模块深度学习', desc: '理解 skills 如何被发现、管理并进入 DeerFlow 的提示面。' },
  { num: '12', title: 'Sandbox与安全执行环境', file: '12-sandbox-execution.html', group: '第二部分：核心模块深度学习', desc: '看清 DeerFlow 的虚拟路径契约、provider 分层与安全边界。' },
  { num: '13', title: '长期记忆系统', file: '13-memory-system.html', group: '第二部分：核心模块深度学习', desc: '把长期记忆和 checkpoint、summary、event store 严格区分开。' },
  { num: '14', title: 'Sub-Agents：多Agent协作', file: '14-sub-agents.html', group: '第二部分：核心模块深度学习', desc: '理解 task 式结构化委派，而不是泛化多智能体协商幻想。' },
  { num: '15', title: 'Gateway API：与外界的接口', file: '15-gateway-api.html', group: '第二部分：核心模块深度学习', desc: '明确 Gateway 是默认运行时承载体，而不只是薄代理层。' },
  
  // 第三部分：高级特性
  { num: '20', title: '上下文工程：提升Agent智能', file: '20-context-engineering.html', group: '第三部分：高级特性与扩展', desc: '从 prompt、memory、tools、uploads 和 middleware 联动理解上下文塑形。' },
  { num: '21', title: '模型集成：支持多种LLM', file: '21-model-integration.html', group: '第三部分：高级特性与扩展', desc: '围绕配置与运行时解析理解 DeerFlow 的模型选择链。' },
  { num: '22', title: '多渠道集成：从IM到API', file: '22-channels-integration.html', group: '第三部分：高级特性与扩展', desc: '看 IM 渠道如何复用 Gateway、thread、auth 与 streaming 语义。' },
  { num: '23', title: '高级模式和最佳实践', file: '23-advanced-patterns.html', group: '第三部分：高级特性与扩展', desc: '总结 DeerFlow 当前已落地的组合模式，而不是空泛经验谈。' },
  
  // 第四部分：实战
  { num: '30', title: '自定义Skills完全指南', file: '30-custom-skills-guide.html', group: '第四部分：实战与扩展', desc: '面向使用者，讲如何定义、安装和维护自己的自定义 skill。' },
  { num: '31', title: '构建自定义Agent', file: '31-building-custom-agents.html', group: '第四部分：实战与扩展', desc: '沿 DeerFlow 现有 client 与 factory 边界做受控定制。' },
  { num: '32', title: '从零构建Agent系统', file: '32-from-scratch-guide.html', group: '第四部分：实战与扩展', desc: '从 DeerFlow 当前实现中抽取真正可复用的系统设计经验。' },
  
  // 第五部分：参考
  { num: '40', title: '源码导航与阅读指南', file: '40-source-code-guide.html', group: '第五部分：参考与工具', desc: '给你一张 DeerFlow 源码地图，知道先看哪里再看哪里。' },
  { num: '41', title: '常见问题与故障排除', file: '41-troubleshooting-faq.html', group: '第五部分：参考与工具', desc: '按配置、Gateway、streaming、auth、channels 分层定位问题。' },
].map((chapter, index) => ({
  ...chapter,
  order: index + 1,
  displayNum: String(index + 1).padStart(2, '0'),
}));

function getCurrentPage() {
  const path = window.location.pathname;
  const filename = path.split('/').pop();
  return CHAPTERS.find(ch => ch.file === filename);
}

function buildSidebar() {
  const sidebar = document.querySelector('.sidebar');
  if (!sidebar) return;

  const brand = document.createElement('div');
  brand.className = 'brand';
  brand.innerHTML = `
    <a href="index.html">
      <h1><span class="logo">🦌</span> DeerFlow</h1>
      <p>DeerFlow-first 源码课程</p>
    </a>
  `;
  sidebar.appendChild(brand);

  const groups = {};
  CHAPTERS.forEach(ch => {
    if (!groups[ch.group]) groups[ch.group] = [];
    groups[ch.group].push(ch);
  });

  Object.entries(groups).forEach(([groupName, chapters]) => {
    const group = document.createElement('div');
    group.className = 'nav-group';
    
    const title = document.createElement('div');
    title.className = 'nav-group-title';
    title.textContent = groupName;
    group.appendChild(title);

    chapters.forEach(ch => {
      const link = document.createElement('a');
      link.className = 'nav-link';
      link.href = ch.file;
      
      const current = getCurrentPage();
      if (current && current.file === ch.file) {
        link.classList.add('active');
      }

      link.innerHTML = `
        <span class="num">${ch.displayNum}</span>
        <span class="nav-copy">
          <span class="nav-title">${ch.title}</span>
          <span class="nav-desc">${ch.desc || ''}</span>
        </span>
      `;
      group.appendChild(link);
    });

    sidebar.appendChild(group);
  });
}

function buildPageNav() {
  const pageNav = document.querySelector('#page-nav');
  if (!pageNav) return;

  const current = getCurrentPage();
  if (!current) return;

  const currentIdx = CHAPTERS.findIndex(ch => ch.file === current.file);
  const prev = currentIdx > 0 ? CHAPTERS[currentIdx - 1] : null;
  const next = currentIdx < CHAPTERS.length - 1 ? CHAPTERS[currentIdx + 1] : null;

  const nav = document.createElement('div');
  nav.className = 'page-nav';

  if (prev) {
    const prevLink = document.createElement('a');
    prevLink.href = prev.file;
    prevLink.innerHTML = `<div class="dir">← 上一章</div><div class="ttl">${prev.title}</div>`;
    nav.appendChild(prevLink);
  } else {
    nav.appendChild(document.createElement('div'));
  }

  if (next) {
    const nextLink = document.createElement('a');
    nextLink.className = 'next';
    nextLink.href = next.file;
    nextLink.innerHTML = `<div class="dir">下一章 →</div><div class="ttl">${next.title}</div>`;
    nav.appendChild(nextLink);
  } else {
    nav.appendChild(document.createElement('div'));
  }

  pageNav.appendChild(nav);
}

function syncPageSubtitle() {
  const subtitle = document.querySelector('.page-subtitle');
  const current = getCurrentPage();
  if (!subtitle || !current) return;

  subtitle.textContent = `DeerFlow 学习系列 - 第 ${current.displayNum} 章`;
}

function setupMenuToggle() {
  const toggle = document.querySelector('.menu-toggle');
  const sidebar = document.querySelector('.sidebar');
  
  if (!toggle || !sidebar) return;

  toggle.addEventListener('click', () => {
    sidebar.classList.toggle('open');
  });

  document.addEventListener('click', (e) => {
    if (!e.target.closest('.sidebar') && !e.target.closest('.menu-toggle')) {
      sidebar.classList.remove('open');
    }
  });
}

// 初始化
document.addEventListener('DOMContentLoaded', () => {
  buildSidebar();
  syncPageSubtitle();
  buildPageNav();
  setupMenuToggle();
});
