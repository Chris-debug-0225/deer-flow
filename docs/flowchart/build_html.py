#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DeerFlow 流程图 Markdown -> HTML 静态站点生成器。
读取 docs/flowchart 下的 11 个 .md 文件，生成风格统一的深色主题 HTML，
Mermaid 图表由 mermaid.js 忠实渲染（源码经 HTML 转义后放入 <pre class="mermaid">，
mermaid 读取 textContent 渲染，确保与 .md 内容完全一致）。
"""
import os
import re
import html
import json

HERE = os.path.dirname(os.path.abspath(__file__))
HTML_DIR = os.path.join(HERE, "html")
ASSETS_DIR = os.path.join(HTML_DIR, "assets")

# 11 个源文档（顺序即导航顺序）
DOCS = [
    ("00", "流程图总索引", "00-index.md", "00-index.html"),
    ("01", "系统架构", "01-architecture.md", "01-architecture.html"),
    ("02", "数据流", "02-data-flow.md", "02-data-flow.html"),
    ("03", "Lead Agent 调用链", "03-lead-agent-calls.md", "03-lead-agent-calls.html"),
    ("04", "子代理执行", "04-subagent-execution.md", "04-subagent-execution.html"),
    ("05", "Sandbox 执行", "05-sandbox-execution.md", "05-sandbox-execution.html"),
    ("06", "记忆系统", "06-memory-system.md", "06-memory-system.html"),
    ("07", "前端架构（上）", "07-frontend-architecture.md", "07-frontend-architecture.html"),
    ("08", "前端架构（下）", "08-frontend-architecture.md", "08-frontend-architecture.html"),
    ("09", "配置与技能工具", "09-config-skills-tools.md", "09-config-skills-tools.html"),
    ("10", "高级特性", "10-advanced-features.md", "10-advanced-features.html"),
]

# ====================== Markdown -> HTML 转换 ======================

def esc(text):
    """HTML 转义普通文本（保留可读性，& < > 转义）"""
    return html.escape(text, quote=False)


def inline_md(text):
    """处理行内 Markdown：**bold**, *italic*, `code`, [t](u)。
    先转义，再施加格式。"""
    # 1. 提取行内代码（`code`）保护起来
    code_holders = []

    def stash_code(m):
        code_holders.append(m.group(1))
        return f"\x00CODE{len(code_holders) - 1}\x00"

    text = re.sub(r"`([^`]+)`", stash_code, text)

    # 2. 转义剩余文本
    text = esc(text)

    # 3. 加粗 **x** 与斜体 *x*
    text = re.sub(r"\*\*([^*]+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"<em>\1</em>", text)

    # 4. 链接 [t](u)
    text = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        lambda m: f'<a href="{esc_attr(m.group(2))}">{m.group(1)}</a>',
        text,
    )

    # 5. 还原行内代码（代码内容需转义）
    def restore_code(m):
        idx = int(m.group(1))
        return f'<code>{esc(code_holders[idx])}</code>'

    text = re.sub(r"\x00CODE(\d+)\x00", restore_code, text)
    return text


def esc_attr(text):
    return html.escape(text, quote=True)


def slugify(text):
    """生成锚点 id：保留中英文/数字，其余转 -"""
    s = re.sub(r"[^\w\u4e00-\u9fff]+", "-", text.strip()).strip("-")
    return s.lower() or "section"


def md_to_html(md_text):
    """把 Markdown 正文（不含代码块隔离）转成 HTML 片段。
    返回 (html, mermaid_count, code_count, section_meta)。
    section_meta: [(level, title, slug), ...] 供生成目录。
    """
    lines = md_text.split("\n")
    out = []
    section_meta = []
    mermaid_count = 0
    code_count = 0
    i = 0
    n = len(lines)

    # 列表状态
    list_type = None  # 'ul' | 'ol' | None

    def close_list():
        nonlocal list_type
        if list_type:
            out.append(f"</{list_type}>")
            list_type = None

    while i < n:
        raw = lines[i]
        line = raw.rstrip("\n")
        stripped = line.strip()

        # 空行
        if not stripped:
            close_list()
            i += 1
            continue

        # 围栏代码块 ```
        if stripped.startswith("```"):
            lang = stripped[3:].strip()
            code_lines = []
            i += 1
            while i < n and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            i += 1  # 跳过结束 ```
            close_list()
            code_src = "\n".join(code_lines)
            if lang.lower() == "mermaid":
                mermaid_count += 1
                # 转义后放入 pre.mermaid，mermaid.js 读 textContent 渲染（忠实源码）
                out.append(
                    f'<div class="diagram-card"><div class="diagram-label">'
                    f'<span class="d-icon">∿</span> Mermaid 图 #{mermaid_count}</div>'
                    f'<pre class="mermaid">{esc(code_src)}</pre></div>'
                )
            else:
                code_count += 1
                label = lang or "code"
                out.append(
                    f'<div class="code-block"><div class="code-lang">{esc(label)}</div>'
                    f'<pre><code>{esc(code_src)}</code></pre></div>'
                )
            continue

        # 分隔线 ---
        if re.match(r"^-{3,}$", stripped):
            close_list()
            out.append('<hr/>')
            i += 1
            continue

        # 标题
        hm = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if hm:
            close_list()
            level = len(hm.group(1))
            title = hm.group(2).strip()
            sl = slugify(title)
            # 保证锚点唯一
            base = sl
            k = 2
            used = {m[2] for m in section_meta}
            while sl in used:
                sl = f"{base}-{k}"
                k += 1
            section_meta.append((level, title, sl))
            inner = inline_md(title)
            out.append(f'<h{level} id="{sl}">{inner}</h{level}>')
            i += 1
            continue

        # 引用 >
        if stripped.startswith(">"):
            close_list()
            quote_lines = []
            while i < n and lines[i].strip().startswith(">"):
                quote_lines.append(re.sub(r"^>\s?", "", lines[i].strip()))
                i += 1
            content = "<br/>".join(inline_md(l) for l in quote_lines if l)
            out.append(f'<blockquote>{content}</blockquote>')
            continue

        # 表格 | a | b |
        if stripped.startswith("|") and "|" in stripped[1:]:
            # 收集连续表格行
            tbl = []
            while i < n and lines[i].strip().startswith("|"):
                tbl.append(lines[i].strip())
                i += 1
            close_list()
            out.append(render_table(tbl))
            continue

        # 无序列表 - / * / +
        lm = re.match(r"^[-*+]\s+(.*)$", stripped)
        if lm:
            if list_type != "ul":
                close_list()
                out.append("<ul>")
                list_type = "ul"
            out.append(f"<li>{inline_md(lm.group(1))}</li>")
            i += 1
            continue

        # 有序列表 1.
        om = re.match(r"^\d+\.\s+(.*)$", stripped)
        if om:
            if list_type != "ol":
                close_list()
                out.append("<ol>")
                list_type = "ol"
            out.append(f"<li>{inline_md(om.group(1))}</li>")
            i += 1
            continue

        # 普通段落（连续非空行合并）
        close_list()
        para = [line]
        i += 1
        while i < n:
            nxt = lines[i].strip()
            if (
                not nxt
                or nxt.startswith("```")
                or nxt.startswith("#")
                or nxt.startswith(">")
                or nxt.startswith("|")
                or re.match(r"^[-*+]\s+", nxt)
                or re.match(r"^\d+\.\s+", nxt)
                or re.match(r"^-{3,}$", nxt)
            ):
                break
            para.append(lines[i])
            i += 1
        para_html = " ".join(inline_md(p.strip()) for p in para)
        out.append(f"<p>{para_html}</p>")

    close_list()
    return "\n".join(out), mermaid_count, code_count, section_meta


def render_table(rows):
    """渲染 GFM 表格行（每行以 | 分隔）"""
    def split_cells(r):
        r = r.strip()
        if r.startswith("|"):
            r = r[1:]
        if r.endswith("|"):
            r = r[:-1]
        return [c.strip() for c in r.split("|")]

    cells = [split_cells(r) for r in rows]
    # 第二行可能是分隔行 |---|---|
    has_sep = len(cells) >= 2 and all(re.match(r"^:?-+:?$", c.replace(" ", "")) for c in cells[1] if c)
    header = cells[0]
    body = cells[2:] if has_sep else cells[1:]
    h = ['<div class="table-wrap"><table><thead><tr>']
    for c in header:
        h.append(f"<th>{inline_md(c)}</th>")
    h.append("</tr></thead><tbody>")
    for row in body:
        if not any(row):
            continue
        h.append("<tr>")
        for c in row:
            h.append(f"<td>{inline_md(c)}</td>")
        h.append("</tr>")
    h.append("</tbody></table></div>")
    return "".join(h)


# ====================== 页面组装 ======================

PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} · DeerFlow 流程图</title>
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
<button class="menu-toggle" id="menu-toggle">☰</button>
<div class="layout">
  <nav class="sidebar" id="sidebar"></nav>
  <main class="main">
    <div class="content">
{toc}
{body}
      <div id="page-nav"></div>
    </div>
  </main>
</div>
<script src="assets/nav.js"></script>
<script type="module">
  import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';
  mermaid.initialize({{ startOnLoad: false, theme: 'dark', securityLevel: 'loose',
    flowchart: {{ curve: 'stepAfter', htmlLabels: true, nodeSpacing: 55, rankSpacing: 65, useMaxWidth: true }},
    themeVariables: {{ darkMode: true, background: '#0d1117', primaryColor: '#1f2937',
      primaryTextColor: '#e6edf3', primaryBorderColor: '#58a6ff', lineColor: '#9aa4b2',
      secondaryColor: '#161b22', tertiaryColor: '#1a2029', textColor: '#e6edf3' }} }});
  const renderAll = () => mermaid.run({{ querySelector: 'pre.mermaid' }})
    .catch(e => console.error('mermaid render error:', e));
  if (document.readyState === 'loading') {{
    document.addEventListener('DOMContentLoaded', renderAll);
  }} else {{
    renderAll();
  }}
</script>
</body>
</html>
"""


def build_toc(section_meta):
    """根据 h2/h3 生成页内目录"""
    items = [(lvl, t, sl) for (lvl, t, sl) in section_meta if lvl in (2, 3)]
    if not items:
        return ""
    lis = []
    for lvl, t, sl in items:
        cls = "toc-sub" if lvl >= 3 else ""
        lis.append(f'<li class="{cls}"><a href="#{sl}">{html.escape(t)}</a></li>')
    return (
        '<div class="toc"><div class="toc-title">📖 本页目录</div><ul>'
        + "".join(lis)
        + "</ul></div>"
    )


def build_doc_page(num, title, md_path, out_path, doc_index):
    with open(md_path, encoding="utf-8") as f:
        md_text = f.read()
    body_html, m_count, c_count, section_meta = md_to_html(md_text)

    # 把指向本图集 .md 的内部链接改为对应 .html，保证站内导航可用
    for (_, _, md_name, html_name) in DOCS:
        body_html = body_html.replace(f'href="./{md_name}"', f'href="{html_name}"')
        body_html = body_html.replace(f'href="{md_name}"', f'href="{html_name}"')

    # 在最前面加一个页面标题徽标条
    banner = (
        f'<div class="page-head">'
        f'<span class="page-num">{num}</span>'
        f'<div class="page-stats">'
        f'<span class="ps-item"><b>{m_count}</b> Mermaid 图</span>'
        f'<span class="ps-dot">·</span>'
        f'<span class="ps-item"><b>{len(section_meta)}</b> 章节</span>'
        f"</div></div>"
    )

    toc = build_toc(section_meta)
    full_body = banner + body_html
    page = PAGE_TEMPLATE.format(title=html.escape(title), toc=toc, body=full_body)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(page)
    return m_count


# ====================== 索引页 ======================

def build_index_page(meta):
    """meta: [(num, title, file, m_count)]"""
    cards = []
    desc_map = {
        "00": "DeerFlow 完整流程图文档体系总览、学习路径与图表统计。",
        "01": "整体系统架构、请求处理流程、组件依赖、数据流架构、中间件链、配置系统。",
        "02": "请求、流式响应（SSE）、状态、工具调用、记忆、Sandbox、子代理数据流。",
        "03": "Lead Agent 工厂构建、请求处理、中间件链、LLM 节点、工具调用、错误处理。",
        "04": "子代理生命周期、执行引擎、状态流转、并发控制、结果轮询、清理机制。",
        "05": "Sandbox 生命周期、中间件调用、虚拟文件系统、Docker/本地执行、资源管理。",
        "06": "记忆系统架构、提取时序、检索注入、去重合并、更新清理、评分机制。",
        "07": "前端整体架构、页面路由、工作区布局、组件层级、API 通信架构。",
        "08": "输入框交互、技能建议、状态管理、消息去重合并、流式处理、命令面板。",
        "09": "配置系统、Skills 加载、工具注册、文件上传、频道、模型路由、认证授权、部署。",
        "10": "MCP 协议、流式处理、并发控制、缓存优化、安全机制、国际化、插件、CI/CD。",
    }
    total = 0
    for num, title, file, m_count in meta:
        if num == "00":
            continue
        total += m_count
        cards.append(
            f'<a class="feature" href="{file}">'
            f'<div class="ic">{num}</div>'
            f'<h4>{html.escape(title)}</h4>'
            f'<p>{desc_map.get(num, "")}</p>'
            f'<div class="feature-meta"><span class="badge blue">{m_count} 张图</span></div>'
            f"</a>"
        )

    body = f"""
      <div class="hero">
        <span class="tag">deerflow · mermaid · 流程图集</span>
        <h1>DeerFlow 完整流程图</h1>
        <p>基于 <strong>11 篇文档</strong>、约 <strong>{total}+ 张 Mermaid 图表</strong>，覆盖 DeerFlow 架构、数据流、Agent 执行、Sandbox、记忆、前端、配置与高级特性的完整可视化文档。所有图表均忠实还原源 Markdown，支持深色主题在线渲染。</p>
        <div class="stats">
          <div class="stat"><div class="n">11</div><div class="l">文档章节</div></div>
          <div class="stat"><div class="n">{total}</div><div class="l">Mermaid 图表</div></div>
          <div class="stat"><div class="n">100%</div><div class="l">对照源文档</div></div>
        </div>
      </div>

      <div class="callout info">
        <div class="callout-title">📖 如何使用本图集</div>
        <p>左侧导航选择章节；每个 Mermaid 图表会在页面打开时由浏览器自动渲染（需联网加载 mermaid.js）。图表内容与 <code>docs/flowchart/*.md</code> 源文件<strong>完全一致</strong>，未做任何修改。</p>
      </div>

      <h2>🗂️ 章节速览</h2>
      <div class="grid cols-3">
        {''.join(cards)}
      </div>

      <h2>🎯 推荐阅读路径</h2>
      <div class="diagram">
        <div class="dbox">01 系统架构</div>
        <div class="darrow">▼</div>
        <div class="dbox alt">02 数据流 → 03 Lead Agent</div>
        <div class="darrow">▼</div>
        <div class="dbox green">04 子代理 → 05 Sandbox → 06 记忆</div>
        <div class="darrow">▼</div>
        <div class="dbox orange">07/08 前端 → 09 配置 → 10 高级特性</div>
      </div>
      <div id="page-nav"></div>
    """
    page = PAGE_TEMPLATE.format(title="流程图总索引", toc="", body=body)
    out = os.path.join(HTML_DIR, "index.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(page)


# ====================== 资源文件 ======================

def write_assets():
    os.makedirs(ASSETS_DIR, exist_ok=True)
    with open(os.path.join(ASSETS_DIR, "style.css"), "w", encoding="utf-8") as f:
        f.write(STYLE_CSS)
    with open(os.path.join(ASSETS_DIR, "nav.js"), "w", encoding="utf-8") as f:
        chapters = json.dumps(
            [{"num": n, "title": t, "file": fn} for (n, t, _, fn) in DOCS],
            ensure_ascii=False,
        )
        f.write(NAV_JS % chapters)


# ====================== 主流程 ======================

def main():
    os.makedirs(ASSETS_DIR, exist_ok=True)
    meta = []
    for num, title, md_name, html_name in DOCS:
        md_path = os.path.join(HERE, md_name)
        out_path = os.path.join(HTML_DIR, html_name)
        m_count = build_doc_page(num, title, md_path, out_path, DOCS)
        meta.append((num, title, html_name, m_count))
        print(f"  [OK] {html_name}  ({m_count} mermaid 图)")

    build_index_page(meta)
    write_assets()
    print(f"  [OK] index.html")
    print(f"  [OK] assets/style.css")
    print(f"  [OK] assets/nav.js")
    total = sum(m for _, _, _, m in meta)
    print(f"\n完成：11 个文档，共 {total} 张 Mermaid 图表。")


# ====================== 样式与脚本内容 ======================

STYLE_CSS = r"""/* ============================================================
   DeerFlow 流程图集 — 深色文档主题（与 .learning/html 风格一致）
   ============================================================ */
:root {
  --bg: #0d1117;
  --bg-soft: #161b22;
  --bg-card: #1a2029;
  --bg-code: #0b1622;
  --border: #2b3340;
  --border-soft: #222a35;
  --text: #e6edf3;
  --text-soft: #aeb9c5;
  --text-dim: #7d8896;
  --accent: #58a6ff;
  --accent-2: #79c0ff;
  --green: #3fb950;
  --green-soft: #56d364;
  --orange: #f0883e;
  --purple: #bc8cff;
  --pink: #ff7b9c;
  --yellow: #e3b341;
  --red: #f85149;
  --shadow: 0 8px 30px rgba(0, 0, 0, 0.4);
  --radius: 12px;
  --sidebar-w: 290px;
  --mono: "JetBrains Mono", "Fira Code", "Cascadia Code", "SF Mono", Consolas, monospace;
  --sans: -apple-system, "Segoe UI", "PingFang SC", "Microsoft YaHei", Roboto, sans-serif;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
html { scroll-behavior: smooth; scroll-padding-top: 24px; }
body { font-family: var(--sans); background: var(--bg); color: var(--text); line-height: 1.75; font-size: 16px; -webkit-font-smoothing: antialiased; }

/* ============ 布局 ============ */
.layout { display: flex; min-height: 100vh; }
.sidebar { width: var(--sidebar-w); flex-shrink: 0; background: var(--bg-soft); border-right: 1px solid var(--border); position: fixed; top: 0; left: 0; bottom: 0; overflow-y: auto; padding: 22px 0 60px; z-index: 100; }
.sidebar::-webkit-scrollbar { width: 8px; }
.sidebar::-webkit-scrollbar-thumb { background: var(--border); border-radius: 4px; }
.brand { padding: 0 22px 18px; border-bottom: 1px solid var(--border); margin-bottom: 14px; }
.brand a { text-decoration: none; }
.brand h1 { font-size: 16px; color: var(--text); display: flex; align-items: center; gap: 9px; font-weight: 700; }
.brand .logo { width: 30px; height: 30px; background: linear-gradient(135deg, #667eea, #764ba2); border-radius: 8px; display: grid; place-items: center; font-size: 16px; flex-shrink: 0; }
.brand p { font-size: 12px; color: var(--text-dim); margin-top: 5px; padding-left: 39px; }
.nav-group { margin-bottom: 6px; }
.nav-group-title { font-size: 11px; text-transform: uppercase; letter-spacing: 0.09em; color: var(--text-dim); padding: 14px 22px 6px; font-weight: 700; }
.nav-link { display: flex; align-items: center; gap: 10px; padding: 8px 22px; color: var(--text-soft); text-decoration: none; font-size: 14px; border-left: 2.5px solid transparent; transition: all 0.15s; }
.nav-link:hover { background: var(--bg-card); color: var(--text); }
.nav-link.active { color: var(--accent-2); border-left-color: var(--accent); background: linear-gradient(90deg, rgba(88,166,255,0.10), transparent); font-weight: 600; }
.nav-link .num { font-family: var(--mono); font-size: 11px; color: var(--text-dim); width: 22px; flex-shrink: 0; }
.nav-link.active .num { color: var(--accent); }

.main { margin-left: var(--sidebar-w); flex: 1; min-width: 0; }
.content { max-width: 980px; margin: 0 auto; padding: 54px 48px 120px; }

/* ============ 页头 ============ */
.page-head { display: flex; align-items: center; gap: 14px; margin-bottom: 22px; padding-bottom: 20px; border-bottom: 1px solid var(--border); }
.page-head .page-num { font-family: var(--mono); font-size: 15px; font-weight: 700; color: var(--accent-2); background: rgba(88,166,255,0.10); border: 1px solid var(--accent); border-radius: 10px; padding: 6px 14px; }
.page-head .page-stats { display: flex; align-items: center; gap: 8px; color: var(--text-dim); font-size: 13px; }
.page-head .ps-item b { color: var(--text); font-family: var(--mono); }

/* ============ 排版 ============ */
.content h1 { font-size: 33px; line-height: 1.25; margin-bottom: 10px; font-weight: 800; letter-spacing: -0.01em; }
.content h2 { font-size: 24px; margin: 52px 0 16px; padding-bottom: 10px; border-bottom: 1px solid var(--border); font-weight: 700; scroll-margin-top: 20px; }
.content h3 { font-size: 19px; margin: 32px 0 12px; color: var(--accent-2); font-weight: 650; }
.content h4 { font-size: 16px; margin: 22px 0 8px; color: var(--text); font-weight: 650; }
.content h5, .content h6 { font-size: 14.5px; margin: 18px 0 8px; color: var(--text-soft); font-weight: 650; }
.content p { margin: 12px 0; color: var(--text-soft); }
.content ul, .content ol { margin: 12px 0 12px 8px; padding-left: 22px; color: var(--text-soft); }
.content li { margin: 7px 0; }
.content li::marker { color: var(--accent); }
.content a { color: var(--accent); text-decoration: none; border-bottom: 1px dotted var(--accent); }
.content a:hover { border-bottom-style: solid; }
.content strong { color: var(--text); font-weight: 650; }
.content em { color: var(--accent-2); font-style: italic; }
.content hr { border: none; border-top: 1px solid var(--border); margin: 34px 0; }
.content blockquote { border-left: 4px solid var(--purple); background: var(--bg-card); border: 1px solid var(--border); border-left: 4px solid var(--purple); border-radius: var(--radius); padding: 14px 18px; margin: 18px 0; color: var(--text-soft); }

/* ============ 代码 ============ */
code { font-family: var(--mono); font-size: 0.875em; background: var(--bg-card); padding: 2px 7px; border-radius: 5px; color: var(--orange); border: 1px solid var(--border-soft); }
pre { background: var(--bg-code); border: 1px solid var(--border); border-radius: var(--radius); padding: 18px 20px; overflow-x: auto; margin: 0; }
pre code { background: none; border: none; padding: 0; color: var(--text); font-size: 13.5px; line-height: 1.65; }
pre::-webkit-scrollbar { height: 9px; width: 9px; }
pre::-webkit-scrollbar-thumb { background: var(--border); border-radius: 4px; }
.code-block { margin: 18px 0; border-radius: var(--radius); overflow: hidden; border: 1px solid var(--border); }
.code-block .code-lang { font-family: var(--mono); font-size: 11px; color: var(--text-dim); background: var(--bg-soft); padding: 5px 14px; border-bottom: 1px solid var(--border); text-transform: uppercase; letter-spacing: 0.05em; }
.code-block pre { border: none; border-radius: 0; margin: 0; }

/* ============ Mermaid 图表卡片 ============ */
.diagram-card { margin: 22px 0; background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius); overflow: hidden; box-shadow: var(--shadow); }
.diagram-card .diagram-label { display: flex; align-items: center; gap: 8px; font-family: var(--mono); font-size: 12px; color: var(--accent-2); background: var(--bg-soft); padding: 8px 16px; border-bottom: 1px solid var(--border); }
.diagram-card .d-icon { color: var(--green-soft); font-weight: 700; }
.diagram-card pre.mermaid { background: #0d1117; border: none; margin: 0; padding: 26px 20px; text-align: center; overflow-x: auto; }
.diagram-card pre.mermaid svg { max-width: 100%; height: auto; }

/* ============ 表格 ============ */
.table-wrap { overflow-x: auto; margin: 18px 0; }
table { border-collapse: collapse; width: 100%; font-size: 14px; background: var(--bg-card); border-radius: var(--radius); overflow: hidden; }
th, td { text-align: left; padding: 11px 15px; border-bottom: 1px solid var(--border); vertical-align: top; }
th { background: var(--bg-soft); color: var(--text); font-weight: 650; font-size: 13px; text-transform: uppercase; letter-spacing: 0.03em; }
td { color: var(--text-soft); }
tr:last-child td { border-bottom: none; }
tr:hover td { background: rgba(88,166,255,0.04); }

/* ============ 目录 ============ */
.toc { background: var(--bg-card); border: 1px solid var(--border); border-left: 4px solid var(--accent); border-radius: var(--radius); padding: 18px 22px; margin: 0 0 32px; }
.toc-title { font-size: 13px; text-transform: uppercase; letter-spacing: 0.06em; color: var(--text-dim); margin-bottom: 10px; font-weight: 700; }
.toc ul { list-style: none; margin: 0; padding: 0; columns: 2; column-gap: 32px; }
.toc li { margin: 5px 0; break-inside: avoid; }
.toc li.toc-sub { padding-left: 16px; }
.toc a { color: var(--text-soft); font-size: 14px; border: none; }
.toc a:hover { color: var(--accent); }

/* ============ 卡片/提示 ============ */
.callout { border-radius: var(--radius); padding: 15px 18px; margin: 18px 0; border: 1px solid var(--border); border-left: 4px solid var(--accent); background: var(--bg-card); font-size: 14.5px; }
.callout .callout-title { font-weight: 700; margin-bottom: 5px; display: flex; align-items: center; gap: 7px; }
.callout p { margin: 5px 0; color: var(--text-soft); }
.callout.tip { border-left-color: var(--green); }
.callout.tip .callout-title { color: var(--green-soft); }
.callout.info { border-left-color: var(--accent); }
.callout.info .callout-title { color: var(--accent-2); }

/* ============ 网格 ============ */
.grid { display: grid; gap: 16px; margin: 20px 0; }
.grid.cols-2 { grid-template-columns: repeat(2, 1fr); }
.grid.cols-3 { grid-template-columns: repeat(3, 1fr); }
.feature { background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius); padding: 18px 20px; transition: transform 0.15s, border-color 0.15s; text-decoration: none; color: inherit; display: block; }
.feature:hover { transform: translateY(-3px); border-color: var(--accent); }
.feature .ic { font-family: var(--mono); font-size: 20px; color: var(--accent-2); margin-bottom: 10px; font-weight: 700; }
.feature h4 { margin: 0 0 6px; color: var(--text); }
.feature p { font-size: 13.5px; margin: 0 0 10px; color: var(--text-dim); }
.feature a { border: none; }
.feature-meta { display: flex; gap: 8px; }

/* ============ 徽章 ============ */
.badge { display: inline-block; font-size: 11px; font-family: var(--mono); padding: 2px 9px; border-radius: 20px; font-weight: 600; border: 1px solid; }
.badge.blue { color: var(--accent-2); border-color: var(--accent); background: rgba(88,166,255,0.1); }
.badge.green { color: var(--green-soft); border-color: var(--green); background: rgba(63,185,80,0.1); }
.badge.purple { color: var(--purple); border-color: var(--purple); background: rgba(188,140,255,0.1); }
.badge.orange { color: var(--orange); border-color: var(--orange); background: rgba(240,136,62,0.1); }

/* ============ 首页 Hero ============ */
.hero { text-align: center; padding: 40px 0 30px; border-bottom: 1px solid var(--border); margin-bottom: 36px; }
.hero .tag { display: inline-block; font-family: var(--mono); font-size: 12px; color: var(--accent-2); border: 1px solid var(--accent); background: rgba(88,166,255,0.08); padding: 4px 14px; border-radius: 20px; margin-bottom: 18px; }
.hero h1 { font-size: 42px; background: linear-gradient(135deg, var(--text), var(--accent)); -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 14px; }
.hero p { font-size: 17px; color: var(--text-soft); max-width: 680px; margin: 0 auto; }
.hero .stats { display: flex; justify-content: center; gap: 36px; margin-top: 28px; flex-wrap: wrap; }
.hero .stat .n { font-size: 28px; font-weight: 800; color: var(--accent-2); font-family: var(--mono); }
.hero .stat .l { font-size: 13px; color: var(--text-dim); }

/* ============ 流程盒子 ============ */
.diagram { display: flex; flex-direction: column; align-items: center; gap: 0; margin: 24px 0; }
.dbox { background: var(--bg-card); border: 1.5px solid var(--accent); border-radius: 10px; padding: 12px 22px; text-align: center; font-size: 14px; font-weight: 600; min-width: 220px; color: var(--text); }
.dbox.alt { border-color: var(--purple); }
.dbox.green { border-color: var(--green); }
.dbox.orange { border-color: var(--orange); }
.darrow { color: var(--text-dim); font-size: 20px; line-height: 1.4; padding: 2px 0; }

/* ============ 页脚导航 ============ */
.page-nav { display: flex; justify-content: space-between; gap: 16px; margin-top: 70px; padding-top: 28px; border-top: 1px solid var(--border); }
.page-nav a { flex: 1; border: 1px solid var(--border); border-radius: var(--radius); padding: 16px 20px; text-decoration: none; color: var(--text-soft); transition: all 0.15s; background: var(--bg-card); border-bottom: 1px solid var(--border); }
.page-nav a:hover { border-color: var(--accent); color: var(--text); transform: translateY(-2px); }
.page-nav a.next { text-align: right; }
.page-nav .dir { font-size: 12px; color: var(--text-dim); display: block; margin-bottom: 3px; }
.page-nav .ttl { font-weight: 650; font-size: 15px; }

/* ============ 移动端 ============ */
.menu-toggle { display: none; position: fixed; top: 14px; left: 14px; z-index: 200; background: var(--bg-soft); border: 1px solid var(--border); color: var(--text); width: 42px; height: 42px; border-radius: 9px; font-size: 20px; cursor: pointer; }
@media (max-width: 1000px) {
  .sidebar { transform: translateX(-100%); transition: transform 0.25s; box-shadow: var(--shadow); }
  .sidebar.open { transform: translateX(0); }
  .main { margin-left: 0; }
  .menu-toggle { display: block; }
  .content { padding: 70px 22px 90px; }
  .grid.cols-2, .grid.cols-3 { grid-template-columns: 1fr; }
  .toc ul { columns: 1; }
  .content h1 { font-size: 27px; }
  .hero h1 { font-size: 32px; }
}
"""

NAV_JS = r"""// DeerFlow 流程图集 - 导航生成
const CHAPTERS = %s;

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
"""


if __name__ == "__main__":
    main()
