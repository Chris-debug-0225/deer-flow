// DeerFlow 流程图集 - 导航生成
const CHAPTERS = [{"num": "00", "title": "流程图总索引", "file": "00-index.html"}, {"num": "01", "title": "系统架构", "file": "01-architecture.html"}, {"num": "02", "title": "数据流", "file": "02-data-flow.html"}, {"num": "03", "title": "Lead Agent 调用链", "file": "03-lead-agent-calls.html"}, {"num": "04", "title": "子代理执行", "file": "04-subagent-execution.html"}, {"num": "05", "title": "Sandbox 执行", "file": "05-sandbox-execution.html"}, {"num": "06", "title": "记忆系统", "file": "06-memory-system.html"}, {"num": "07", "title": "前端架构（上）", "file": "07-frontend-architecture.html"}, {"num": "08", "title": "前端架构（下）", "file": "08-frontend-architecture.html"}, {"num": "09", "title": "配置与技能工具", "file": "09-config-skills-tools.html"}, {"num": "10", "title": "高级特性", "file": "10-advanced-features.html"}];

function getCurrentPage() {
  const path = window.location.pathname;
  const filename = path.split('/').pop() || 'index.html';
  return CHAPTERS.find(ch => ch.file === filename);
}

function buildSidebar() {
  const sidebar = document.querySelector('.sidebar');
  if (!sidebar) return;

  const brand = document.createElement('div');
  brand.className = 'brand';
  brand.innerHTML = `
    <a href="index.html">
      <h1><span class="logo">🦌</span> DeerFlow 流程图</h1>
      <p>Mermaid 可视化文档集</p>
    </a>
  `;
  sidebar.appendChild(brand);

  // 索引链接
  const idxLink = document.createElement('a');
  idxLink.className = 'nav-link';
  idxLink.href = 'index.html';
  if ((window.location.pathname.split('/').pop() || 'index.html') === 'index.html') {
    idxLink.classList.add('active');
  }
  idxLink.innerHTML = `<span class="num">00</span> <span>总索引首页</span>`;
  sidebar.appendChild(idxLink);

  const group = document.createElement('div');
  group.className = 'nav-group';
  const title = document.createElement('div');
  title.className = 'nav-group-title';
  title.textContent = '流程图章节';
  group.appendChild(title);

  CHAPTERS.forEach(ch => {
    if (ch.num === '00') return;
    const link = document.createElement('a');
    link.className = 'nav-link';
    link.href = ch.file;
    const current = getCurrentPage();
    if (current && current.num === ch.num) link.classList.add('active');
    link.innerHTML = `<span class="num">${ch.num}</span> <span>${ch.title}</span>`;
    group.appendChild(link);
  });
  sidebar.appendChild(group);
}

function buildPageNav() {
  const pageNav = document.querySelector('#page-nav');
  if (!pageNav) return;
  const current = getCurrentPage();
  if (!current) return;
  const ordered = CHAPTERS.filter(c => c.num !== '00');
  const idx = ordered.findIndex(ch => ch.num === current.num);
  if (idx === -1) return;
  const prev = idx > 0 ? ordered[idx - 1] : null;
  const next = idx < ordered.length - 1 ? ordered[idx + 1] : null;
  const nav = document.createElement('div');
  nav.className = 'page-nav';
  if (prev) {
    const a = document.createElement('a');
    a.href = prev.file;
    a.innerHTML = `<div class="dir">← 上一章</div><div class="ttl">${prev.title}</div>`;
    nav.appendChild(a);
  } else { nav.appendChild(document.createElement('div')); }
  if (next) {
    const a = document.createElement('a');
    a.className = 'next';
    a.href = next.file;
    a.innerHTML = `<div class="dir">下一章 →</div><div class="ttl">${next.title}</div>`;
    nav.appendChild(a);
  } else { nav.appendChild(document.createElement('div')); }
  pageNav.appendChild(nav);
}

function setupMenuToggle() {
  const toggle = document.querySelector('.menu-toggle');
  const sidebar = document.querySelector('.sidebar');
  if (!toggle || !sidebar) return;
  toggle.addEventListener('click', () => sidebar.classList.toggle('open'));
  document.addEventListener('click', (e) => {
    if (!e.target.closest('.sidebar') && !e.target.closest('.menu-toggle')) sidebar.classList.remove('open');
  });
}

document.addEventListener('DOMContentLoaded', () => {
  buildSidebar();
  buildPageNav();
  setupMenuToggle();
});
