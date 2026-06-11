// DeerFlow 学习系列 - 导航生成脚本

const CHAPTERS = [
  // 第一部分：基础概念
  { num: '00', title: 'Agent 基础概念与设计思想', file: '00-agent-fundamentals.html', group: '第一部分：基础概念' },
  { num: '01', title: 'LangGraph 框架基础', file: '01-langgraph-basics.html', group: '第一部分：基础概念' },
  { num: '02', title: 'LLM调用与工具系统', file: '02-llm-and-tools.html', group: '第一部分：基础概念' },
  { num: '03', title: 'DeerFlow 整体架构概览', file: '03-deerflow-overview.html', group: '第一部分：基础概念' },
  
  // 第二部分：核心模块
  { num: '10', title: 'Agent执行引擎的设计与实现', file: '10-agent-execution-engine.html', group: '第二部分：核心模块深度学习' },
  { num: '11', title: 'Skills系统：Agent的能力扩展', file: '11-skills-system.html', group: '第二部分：核心模块深度学习' },
  { num: '12', title: 'Sandbox与安全执行环境', file: '12-sandbox-execution.html', group: '第二部分：核心模块深度学习' },
  { num: '13', title: '长期记忆系统', file: '13-memory-system.html', group: '第二部分：核心模块深度学习' },
  { num: '14', title: 'Sub-Agents：多Agent协作', file: '14-sub-agents.html', group: '第二部分：核心模块深度学习' },
  { num: '15', title: 'Gateway API：与外界的接口', file: '15-gateway-api.html', group: '第二部分：核心模块深度学习' },
  
  // 第三部分：高级特性
  { num: '20', title: '上下文工程：提升Agent智能', file: '20-context-engineering.html', group: '第三部分：高级特性与扩展' },
  { num: '21', title: '模型集成：支持多种LLM', file: '21-model-integration.html', group: '第三部分：高级特性与扩展' },
  { num: '22', title: '多渠道集成：从IM到API', file: '22-channels-integration.html', group: '第三部分：高级特性与扩展' },
  { num: '23', title: '高级模式和最佳实践', file: '23-advanced-patterns.html', group: '第三部分：高级特性与扩展' },
  
  // 第四部分：实战
  { num: '30', title: '自定义Skills完全指南', file: '30-custom-skills-guide.html', group: '第四部分：实战与扩展' },
  { num: '31', title: '构建自定义Agent', file: '31-building-custom-agents.html', group: '第四部分：实战与扩展' },
  { num: '32', title: '从零构建Agent系统', file: '32-from-scratch-guide.html', group: '第四部分：实战与扩展' },
  
  // 第五部分：参考
  { num: '40', title: '源码导航与阅读指南', file: '40-source-code-guide.html', group: '第五部分：参考与工具' },
  { num: '41', title: '常见问题与故障排除', file: '41-troubleshooting-faq.html', group: '第五部分：参考与工具' },
];

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
      <p>Agent 学习系列</p>
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
      if (current && current.num === ch.num) {
        link.classList.add('active');
      }

      link.innerHTML = `<span class="num">${ch.num}</span> <span>${ch.title}</span>`;
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

  const currentIdx = CHAPTERS.findIndex(ch => ch.num === current.num);
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
  buildPageNav();
  setupMenuToggle();
});
