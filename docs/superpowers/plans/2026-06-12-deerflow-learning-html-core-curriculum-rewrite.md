# DeerFlow Learning HTML Core Curriculum Rewrite Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild DeerFlow's core `.learning/html` curriculum so the targeted chapters teach DeerFlow's real architecture and implementation, with consistent DeerFlow-first structure and automated validation of chapter coverage.

**Architecture:** Add a lightweight curriculum validation script first, then rewrite the curriculum in four coordinated chapter tracks that align with the approved spec: model/tool foundation, execution/runtime internals, integration/runtime surfaces, and extension/reference chapters. Keep filenames and navigation stable, reuse shared layout assets, and validate every rewritten chapter against required DeerFlow-first headings, code anchors, and cross-chapter consistency rules.

**Tech Stack:** Static HTML, shared CSS/JS assets, Python 3 validation script, ripgrep for content checks

---

### Task 1: Add curriculum validation script

**Files:**
- Create: `scripts/validate_learning_html.py`
- Modify: `.learning/README.md`
- Test: `scripts/validate_learning_html.py`

- [ ] **Step 1: Write the failing validator**

Create `scripts/validate_learning_html.py` with this content:

```python
#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
HTML_DIR = ROOT / ".learning" / "html"

TARGETS: dict[str, dict[str, object]] = {
    "02-llm-and-tools.html": {
        "title": "LLM调用与工具系统",
        "required_headings": [
            "这项能力在 DeerFlow 中解决什么问题",
            "这项能力在代码库中的位置",
            "真实运行链路或数据链路",
            "配置面与使用方式",
            "关键实现细节与权衡",
            "当前限制、边界与非目标",
            "它与 DeerFlow 其他能力的关系",
        ],
        "required_paths": [
            "backend/packages/harness/deerflow/tools/tools.py",
            "backend/packages/harness/deerflow/agents/factory.py",
        ],
    },
    "03-deerflow-overview.html": {
        "title": "DeerFlow 整体架构概览",
        "required_headings": [
            "这项能力在 DeerFlow 中解决什么问题",
            "这项能力在代码库中的位置",
            "真实运行链路或数据链路",
            "配置面与使用方式",
            "关键实现细节与权衡",
            "当前限制、边界与非目标",
            "它与 DeerFlow 其他能力的关系",
        ],
        "required_paths": [
            "backend/docs/ARCHITECTURE.md",
            "backend/app/gateway/app.py",
        ],
    },
    "10-agent-execution-engine.html": {
        "title": "Agent执行引擎的设计与实现",
        "required_headings": [
            "这项能力在 DeerFlow 中解决什么问题",
            "这项能力在代码库中的位置",
            "真实运行链路或数据链路",
            "配置面与使用方式",
            "关键实现细节与权衡",
            "当前限制、边界与非目标",
            "它与 DeerFlow 其他能力的关系",
        ],
        "required_paths": [
            "backend/packages/harness/deerflow/agents/lead_agent/agent.py",
            "backend/packages/harness/deerflow/runtime/runs/worker.py",
        ],
    },
    "11-skills-system.html": {
        "title": "Skills系统：Agent的能力扩展",
        "required_headings": [
            "这项能力在 DeerFlow 中解决什么问题",
            "这项能力在代码库中的位置",
            "真实运行链路或数据链路",
            "配置面与使用方式",
            "关键实现细节与权衡",
            "当前限制、边界与非目标",
            "它与 DeerFlow 其他能力的关系",
        ],
        "required_paths": [
            "backend/packages/harness/deerflow/skills/installer.py",
            "backend/app/gateway/routers/skills.py",
        ],
    },
    "12-sandbox-execution.html": {
        "title": "Sandbox与安全执行环境",
        "required_headings": [
            "这项能力在 DeerFlow 中解决什么问题",
            "这项能力在代码库中的位置",
            "真实运行链路或数据链路",
            "配置面与使用方式",
            "关键实现细节与权衡",
            "当前限制、边界与非目标",
            "它与 DeerFlow 其他能力的关系",
        ],
        "required_paths": [
            "backend/packages/harness/deerflow/sandbox/tools.py",
            "backend/packages/harness/deerflow/sandbox/local/local_sandbox_provider.py",
        ],
    },
    "13-memory-system.html": {
        "title": "长期记忆系统",
        "required_headings": [
            "这项能力在 DeerFlow 中解决什么问题",
            "这项能力在代码库中的位置",
            "真实运行链路或数据链路",
            "配置面与使用方式",
            "关键实现细节与权衡",
            "当前限制、边界与非目标",
            "它与 DeerFlow 其他能力的关系",
        ],
        "required_paths": [
            "backend/packages/harness/deerflow/agents/memory/storage.py",
            "backend/packages/harness/deerflow/agents/memory/updater.py",
        ],
    },
    "14-sub-agents.html": {
        "title": "Sub-Agents：多Agent协作",
        "required_headings": [
            "这项能力在 DeerFlow 中解决什么问题",
            "这项能力在代码库中的位置",
            "真实运行链路或数据链路",
            "配置面与使用方式",
            "关键实现细节与权衡",
            "当前限制、边界与非目标",
            "它与 DeerFlow 其他能力的关系",
        ],
        "required_paths": [
            "backend/packages/harness/deerflow/tools/builtins/task_tool.py",
            "backend/packages/harness/deerflow/subagents/executor.py",
        ],
    },
    "15-gateway-api.html": {
        "title": "Gateway API：与外界的接口",
        "required_headings": [
            "这项能力在 DeerFlow 中解决什么问题",
            "这项能力在代码库中的位置",
            "真实运行链路或数据链路",
            "配置面与使用方式",
            "关键实现细节与权衡",
            "当前限制、边界与非目标",
            "它与 DeerFlow 其他能力的关系",
        ],
        "required_paths": [
            "backend/app/gateway/app.py",
            "backend/app/gateway/routers/thread_runs.py",
        ],
    },
    "20-context-engineering.html": {
        "title": "上下文工程：提升Agent智能",
        "required_headings": [
            "这项能力在 DeerFlow 中解决什么问题",
            "这项能力在代码库中的位置",
            "真实运行链路或数据链路",
            "配置面与使用方式",
            "关键实现细节与权衡",
            "当前限制、边界与非目标",
            "它与 DeerFlow 其他能力的关系",
        ],
        "required_paths": [
            "backend/packages/harness/deerflow/agents/lead_agent/prompt.py",
            "backend/packages/harness/deerflow/agents/middlewares",
        ],
    },
    "21-model-integration.html": {
        "title": "模型集成：支持多种LLM",
        "required_headings": [
            "这项能力在 DeerFlow 中解决什么问题",
            "这项能力在代码库中的位置",
            "真实运行链路或数据链路",
            "配置面与使用方式",
            "关键实现细节与权衡",
            "当前限制、边界与非目标",
            "它与 DeerFlow 其他能力的关系",
        ],
        "required_paths": [
            "backend/packages/harness/deerflow/config/app_config.py",
            "backend/app/gateway/routers/models.py",
        ],
    },
    "22-channels-integration.html": {
        "title": "多渠道集成：从IM到API",
        "required_headings": [
            "这项能力在 DeerFlow 中解决什么问题",
            "这项能力在代码库中的位置",
            "真实运行链路或数据链路",
            "配置面与使用方式",
            "关键实现细节与权衡",
            "当前限制、边界与非目标",
            "它与 DeerFlow 其他能力的关系",
        ],
        "required_paths": [
            "backend/app/channels/manager.py",
            "backend/app/gateway/routers/channel_connections.py",
        ],
    },
    "23-advanced-patterns.html": {
        "title": "高级模式和最佳实践",
        "required_headings": [
            "这项能力在 DeerFlow 中解决什么问题",
            "这项能力在代码库中的位置",
            "真实运行链路或数据链路",
            "配置面与使用方式",
            "关键实现细节与权衡",
            "当前限制、边界与非目标",
            "它与 DeerFlow 其他能力的关系",
        ],
        "required_paths": [
            "backend/packages/harness/deerflow/tools/builtins/tool_search.py",
            "backend/packages/harness/deerflow/tools/builtins/task_tool.py",
        ],
    },
    "30-custom-skills-guide.html": {
        "title": "自定义Skills完全指南",
        "required_headings": [
            "这项能力在 DeerFlow 中解决什么问题",
            "这项能力在代码库中的位置",
            "真实运行链路或数据链路",
            "配置面与使用方式",
            "关键实现细节与权衡",
            "当前限制、边界与非目标",
            "它与 DeerFlow 其他能力的关系",
        ],
        "required_paths": [
            "backend/packages/harness/deerflow/skills",
            "backend/packages/harness/deerflow/skills/installer.py",
        ],
    },
    "31-building-custom-agents.html": {
        "title": "构建自定义Agent",
        "required_headings": [
            "这项能力在 DeerFlow 中解决什么问题",
            "这项能力在代码库中的位置",
            "真实运行链路或数据链路",
            "配置面与使用方式",
            "关键实现细节与权衡",
            "当前限制、边界与非目标",
            "它与 DeerFlow 其他能力的关系",
        ],
        "required_paths": [
            "backend/packages/harness/deerflow/agents/factory.py",
            "backend/packages/harness/deerflow/client.py",
        ],
    },
    "32-from-scratch-guide.html": {
        "title": "从零构建Agent系统",
        "required_headings": [
            "这项能力在 DeerFlow 中解决什么问题",
            "这项能力在代码库中的位置",
            "真实运行链路或数据链路",
            "配置面与使用方式",
            "关键实现细节与权衡",
            "当前限制、边界与非目标",
            "它与 DeerFlow 其他能力的关系",
        ],
        "required_paths": [
            "backend/docs/ARCHITECTURE.md",
            "backend/docs/API.md",
        ],
    },
    "40-source-code-guide.html": {
        "title": "源码导航与阅读指南",
        "required_headings": [
            "这项能力在 DeerFlow 中解决什么问题",
            "这项能力在代码库中的位置",
            "真实运行链路或数据链路",
            "配置面与使用方式",
            "关键实现细节与权衡",
            "当前限制、边界与非目标",
            "它与 DeerFlow 其他能力的关系",
        ],
        "required_paths": [
            "backend/app/gateway",
            "backend/packages/harness/deerflow/agents",
        ],
    },
    "41-troubleshooting-faq.html": {
        "title": "常见问题与故障排除",
        "required_headings": [
            "这项能力在 DeerFlow 中解决什么问题",
            "这项能力在代码库中的位置",
            "真实运行链路或数据链路",
            "配置面与使用方式",
            "关键实现细节与权衡",
            "当前限制、边界与非目标",
            "它与 DeerFlow 其他能力的关系",
        ],
        "required_paths": [
            "backend/docs/CONFIGURATION.md",
            "backend/app/gateway",
        ],
    },
}

TITLE_RE = re.compile(r"<title>(.*?)</title>", re.S)
H2_RE = re.compile(r"<h2[^>]*>(.*?)</h2>", re.S)
TAG_RE = re.compile(r"<[^>]+>")


def strip_tags(text: str) -> str:
    return TAG_RE.sub("", text).replace("&nbsp;", " ").strip()


def validate_file(filename: str, spec: dict[str, object]) -> list[str]:
    text = (HTML_DIR / filename).read_text(encoding="utf-8")
    errors: list[str] = []

    title_match = TITLE_RE.search(text)
    page_title = title_match.group(1) if title_match else ""
    if str(spec["title"]) not in page_title:
        errors.append(f"{filename}: missing expected title fragment {spec['title']!r}")

    h2s = {strip_tags(m.group(1)) for m in H2_RE.finditer(text)}
    for heading in spec["required_headings"]:
        if heading not in h2s:
            errors.append(f"{filename}: missing required heading {heading!r}")

    for path in spec["required_paths"]:
        if str(path) not in text:
            errors.append(f"{filename}: missing required code anchor {path!r}")

    if "DeerFlow" not in text:
        errors.append(f"{filename}: missing DeerFlow keyword")

    return errors


def main() -> int:
    all_errors: list[str] = []
    for filename, spec in TARGETS.items():
        all_errors.extend(validate_file(filename, spec))

    if all_errors:
        print("Curriculum validation failed:")
        for error in all_errors:
            print(f"- {error}")
        return 1

    print(f"Validated {len(TARGETS)} learning chapters successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Run validator to verify it fails on current HTML**

Run:

```bash
python3 scripts/validate_learning_html.py
```

Expected: FAIL with multiple missing-heading and missing-code-anchor errors for the current curriculum pages.

- [ ] **Step 3: Register the validator in the learning README**

Add this section near the curriculum maintenance guidance in `.learning/README.md`:

```md
## 课程一致性校验

在批量修改 `.learning/html` 章节后，运行下面的命令确认核心章节仍然满足 DeerFlow-first 约束：

```bash
python3 scripts/validate_learning_html.py
```

校验重点包括：

- 章节标题是否仍然匹配目标章节
- 是否包含统一的 DeerFlow-first 结构标题
- 是否包含该章必须出现的核心代码锚点
```

- [ ] **Step 4: Re-run the validator to verify it still fails for content reasons, not script reasons**

Run:

```bash
python3 scripts/validate_learning_html.py
```

Expected: FAIL, but only because target chapters have not been rewritten yet.

- [ ] **Step 5: Commit**

```bash
git add scripts/validate_learning_html.py .learning/README.md
git commit -m "chore: add deerflow learning curriculum validator"
```

### Task 2: Rewrite shared curriculum conventions and overview/foundation track

**Files:**
- Modify: `.learning/html/02-llm-and-tools.html`
- Modify: `.learning/html/03-deerflow-overview.html`
- Modify: `.learning/html/10-agent-execution-engine.html`
- Modify: `.learning/html/11-skills-system.html`
- Modify: `.learning/html/assets/style.css`
- Test: `scripts/validate_learning_html.py`

- [ ] **Step 1: Rewrite `02-llm-and-tools.html` around DeerFlow model/tool assembly**

Replace the chapter body structure so it includes these required `h2` headings and DeerFlow code anchors:

```html
<h2>这项能力在 DeerFlow 中解决什么问题</h2>
<p>在 DeerFlow 里，LLM 调用不是一个孤立的 API 封装层，而是和 tools、prompt、skills、memory、middleware 一起构成 agent 能力底座。</p>

<h2>这项能力在代码库中的位置</h2>
<ul>
  <li><code>backend/packages/harness/deerflow/tools/tools.py</code></li>
  <li><code>backend/packages/harness/deerflow/tools/builtins/</code></li>
  <li><code>backend/packages/harness/deerflow/agents/factory.py</code></li>
  <li><code>backend/packages/harness/deerflow/agents/lead_agent/prompt.py</code></li>
  <li><code>backend/packages/harness/deerflow/config/app_config.py</code></li>
  <li><code>backend/docs/CONFIGURATION.md</code></li>
</ul>

<h2>真实运行链路或数据链路</h2>
<p>按 “配置模型与工具 → agent factory 装配 model/tools → lead-agent prompt 公开可用能力 → runtime 在 tool call 中执行内置工具、配置工具或 MCP 工具” 的顺序展开。</p>
```

- [ ] **Step 2: Rewrite `03-deerflow-overview.html` around the real runtime map**

Ensure the chapter introduces the real DeerFlow topology with these anchors:

```html
<ul>
  <li><code>README.md</code></li>
  <li><code>backend/docs/ARCHITECTURE.md</code></li>
  <li><code>backend/app/gateway/app.py</code></li>
  <li><code>backend/packages/harness/deerflow/client.py</code></li>
  <li><code>backend/packages/harness/deerflow/agents/lead_agent/agent.py</code></li>
</ul>
<div class="key-point">
  <strong>核心事实：</strong> DeerFlow 默认 Web 运行路径是 Gateway-embedded runtime，而不是“单独 LangGraph Server + 另起一层网关”的教学简化模型。
</div>
```

- [ ] **Step 3: Rewrite `10-agent-execution-engine.html` around lead-agent execution flow**

Add the execution chain and exact file anchors:

```html
<ul>
  <li><code>backend/packages/harness/deerflow/agents/lead_agent/agent.py</code></li>
  <li><code>backend/packages/harness/deerflow/agents/factory.py</code></li>
  <li><code>backend/packages/harness/deerflow/agents/thread_state.py</code></li>
  <li><code>backend/packages/harness/deerflow/agents/middlewares/</code></li>
  <li><code>backend/packages/harness/deerflow/runtime/runs/worker.py</code></li>
  <li><code>backend/app/gateway/routers/thread_runs.py</code></li>
  <li><code>backend/docs/STREAMING.md</code></li>
</ul>
<p>把执行引擎写成“agent 构建 + middleware 链 + tool/runtime orchestration + run/stream ownership”，不要再写成通用的 while-loop 教程。</p>
```

- [ ] **Step 4: Rewrite `11-skills-system.html` around DeerFlow skill runtime mechanics**

Make the chapter distinguish skills from tools and custom-skill authoring:

```html
<ul>
  <li><code>backend/packages/harness/deerflow/skills/installer.py</code></li>
  <li><code>backend/packages/harness/deerflow/skills/</code></li>
  <li><code>backend/app/gateway/routers/skills.py</code></li>
  <li><code>backend/packages/harness/deerflow/tools/builtins/tool_search.py</code></li>
  <li><code>backend/packages/harness/deerflow/agents/lead_agent/prompt.py</code></li>
</ul>
<div class="warning">
  <strong>分工边界：</strong> 本章讲 skills 系统如何工作；<code>30-custom-skills-guide.html</code> 讲用户如何定义和构建自定义 skills。
</div>
```

- [ ] **Step 5: Add one shared callout style to reduce per-page duplication**

Append this reusable block to `.learning/html/assets/style.css`:

```css
.deerflow-map {
  background: linear-gradient(180deg, rgba(88,166,255,0.10), rgba(88,166,255,0.03));
  border: 1px solid var(--border);
  border-left: 4px solid var(--accent);
  border-radius: 10px;
  padding: 18px 20px;
  margin: 18px 0;
}

.deerflow-map h4 {
  margin: 0 0 8px;
  color: var(--accent-2);
}
```

- [ ] **Step 6: Run validator to verify the foundation track passes**

Run:

```bash
python3 scripts/validate_learning_html.py
```

Expected: PASS for `02`, `03`, `10`, `11`; FAIL for untouched later chapters.

- [ ] **Step 7: Commit**

```bash
git add .learning/html/02-llm-and-tools.html .learning/html/03-deerflow-overview.html .learning/html/10-agent-execution-engine.html .learning/html/11-skills-system.html .learning/html/assets/style.css
git commit -m "docs: rewrite deerflow learning foundation chapters"
```

### Task 3: Rewrite runtime-internals track

**Files:**
- Modify: `.learning/html/12-sandbox-execution.html`
- Modify: `.learning/html/13-memory-system.html`
- Modify: `.learning/html/14-sub-agents.html`
- Test: `scripts/validate_learning_html.py`

- [ ] **Step 1: Rewrite `12-sandbox-execution.html` with real provider boundaries**

Ensure the chapter contains these file anchors and direct boundary language:

```html
<ul>
  <li><code>backend/packages/harness/deerflow/sandbox/tools.py</code></li>
  <li><code>backend/packages/harness/deerflow/sandbox/sandbox.py</code></li>
  <li><code>backend/packages/harness/deerflow/sandbox/sandbox_provider.py</code></li>
  <li><code>backend/packages/harness/deerflow/sandbox/local/local_sandbox_provider.py</code></li>
  <li><code>backend/packages/harness/deerflow/sandbox/security.py</code></li>
  <li><code>backend/docs/CONFIGURATION.md</code></li>
  <li><code>README.md</code></li>
</ul>
<div class="warning">
  <strong>边界：</strong> Local sandbox 是路径作用域下的便捷模式，host bash 默认关闭；更强隔离路径来自 <code>AioSandboxProvider</code>。
</div>
```

- [ ] **Step 2: Rewrite `13-memory-system.html` with real storage/injection/update flow**

Add these anchors and explicit distinctions:

```html
<ul>
  <li><code>backend/packages/harness/deerflow/agents/memory/prompt.py</code></li>
  <li><code>backend/packages/harness/deerflow/agents/memory/storage.py</code></li>
  <li><code>backend/packages/harness/deerflow/agents/memory/updater.py</code></li>
  <li><code>backend/docs/MEMORY_IMPROVEMENTS_SUMMARY.md</code></li>
  <li><code>backend/docs/AUTH_DESIGN.md</code></li>
</ul>
<p>明确写出：长期记忆不是 thread checkpoint history，不是 summarization，也不是 event store。</p>
```

- [ ] **Step 3: Rewrite `14-sub-agents.html` around `task`-tool delegation**

Include the execution chain and isolation model:

```html
<ul>
  <li><code>backend/packages/harness/deerflow/tools/builtins/task_tool.py</code></li>
  <li><code>backend/packages/harness/deerflow/subagents/executor.py</code></li>
  <li><code>backend/packages/harness/deerflow/subagents/registry.py</code></li>
  <li><code>backend/packages/harness/deerflow/config/subagents_config.py</code></li>
</ul>
<div class="key-point">
  <strong>核心事实：</strong> DeerFlow 的 subagent 不是共享黑板式多智能体系统，而是通过 <code>task</code> tool 触发的结构化委派与隔离执行。
</div>
```

- [ ] **Step 4: Run validator to verify the runtime-internals track passes**

Run:

```bash
python3 scripts/validate_learning_html.py
```

Expected: PASS for `12`, `13`, `14`; FAIL only for untouched later chapters.

- [ ] **Step 5: Commit**

```bash
git add .learning/html/12-sandbox-execution.html .learning/html/13-memory-system.html .learning/html/14-sub-agents.html
git commit -m "docs: rewrite deerflow runtime internals chapters"
```

### Task 4: Rewrite runtime-surfaces and integration track

**Files:**
- Modify: `.learning/html/15-gateway-api.html`
- Modify: `.learning/html/20-context-engineering.html`
- Modify: `.learning/html/21-model-integration.html`
- Modify: `.learning/html/22-channels-integration.html`
- Modify: `.learning/html/23-advanced-patterns.html`
- Test: `scripts/validate_learning_html.py`

- [ ] **Step 1: Rewrite `15-gateway-api.html` around Gateway-owned runtime paths**

Include these anchors and runtime facts:

```html
<ul>
  <li><code>backend/app/gateway/app.py</code></li>
  <li><code>backend/app/gateway/routers/thread_runs.py</code></li>
  <li><code>backend/app/gateway/routers/threads.py</code></li>
  <li><code>backend/app/gateway/routers/uploads.py</code></li>
  <li><code>backend/app/gateway/routers/artifacts.py</code></li>
  <li><code>backend/docs/API.md</code></li>
  <li><code>backend/docs/ARCHITECTURE.md</code></li>
</ul>
<p>明确写出：Gateway 不是薄代理层，而是默认运行时承载体；<code>/api/langgraph/*</code> 是 nginx 重写后的 Gateway 兼容路径。</p>
```

- [ ] **Step 2: Rewrite `20-context-engineering.html` around DeerFlow context-shaping layers**

Use the real context inputs:

```html
<ul>
  <li><code>backend/packages/harness/deerflow/agents/lead_agent/prompt.py</code></li>
  <li><code>backend/packages/harness/deerflow/agents/factory.py</code></li>
  <li><code>backend/packages/harness/deerflow/agents/middlewares/</code></li>
  <li><code>backend/packages/harness/deerflow/agents/memory/prompt.py</code></li>
  <li><code>backend/packages/harness/deerflow/tools/builtins/tool_search.py</code></li>
</ul>
<p>把上下文工程写成 prompt、skills、memory、tools、uploads、images、summarization 和 middleware 联动的真实机制。</p>
```

- [ ] **Step 3: Rewrite `21-model-integration.html` around config and runtime resolution**

Include concrete files:

```html
<ul>
  <li><code>backend/packages/harness/deerflow/config/app_config.py</code></li>
  <li><code>backend/packages/harness/deerflow/subagents/config.py</code></li>
  <li><code>backend/packages/harness/deerflow/config/subagents_config.py</code></li>
  <li><code>backend/app/gateway/routers/models.py</code></li>
  <li><code>backend/packages/harness/deerflow/client.py</code></li>
  <li><code>backend/docs/CONFIGURATION.md</code></li>
</ul>
```

- [ ] **Step 4: Rewrite `22-channels-integration.html` and `23-advanced-patterns.html` as DeerFlow-specific surfaces**

Ensure `22` includes:

```html
<ul>
  <li><code>backend/app/channels/manager.py</code></li>
  <li><code>backend/app/channels/base.py</code></li>
  <li><code>backend/app/channels/feishu.py</code></li>
  <li><code>backend/app/gateway/routers/channels.py</code></li>
  <li><code>backend/app/gateway/routers/channel_connections.py</code></li>
  <li><code>backend/docs/AUTH_DESIGN.md</code></li>
</ul>
```

Ensure `23` includes:

```html
<ul>
  <li><code>backend/packages/harness/deerflow/tools/builtins/tool_search.py</code></li>
  <li><code>backend/packages/harness/deerflow/tools/builtins/task_tool.py</code></li>
  <li><code>backend/packages/harness/deerflow/agents/middlewares/</code></li>
  <li><code>backend/docs/STREAMING.md</code></li>
</ul>
```

- [ ] **Step 5: Run validator to verify the runtime-surfaces track passes**

Run:

```bash
python3 scripts/validate_learning_html.py
```

Expected: PASS for `15`, `20`, `21`, `22`, `23`; FAIL only for untouched extension/reference chapters.

- [ ] **Step 6: Commit**

```bash
git add .learning/html/15-gateway-api.html .learning/html/20-context-engineering.html .learning/html/21-model-integration.html .learning/html/22-channels-integration.html .learning/html/23-advanced-patterns.html
git commit -m "docs: rewrite deerflow runtime surface chapters"
```

### Task 5: Rewrite extension and reference track

**Files:**
- Modify: `.learning/html/30-custom-skills-guide.html`
- Modify: `.learning/html/31-building-custom-agents.html`
- Modify: `.learning/html/32-from-scratch-guide.html`
- Modify: `.learning/html/40-source-code-guide.html`
- Modify: `.learning/html/41-troubleshooting-faq.html`
- Test: `scripts/validate_learning_html.py`

- [ ] **Step 1: Rewrite `30-custom-skills-guide.html` as the hands-on custom-skill chapter**

Make it distinct from chapter `11` and include:

```html
<ul>
  <li><code>backend/packages/harness/deerflow/skills/</code></li>
  <li><code>backend/packages/harness/deerflow/skills/installer.py</code></li>
  <li><code>backend/app/gateway/routers/skills.py</code></li>
  <li><code>backend/packages/harness/deerflow/tools/builtins/tool_search.py</code></li>
</ul>
<div class="warning">
  <strong>分工边界：</strong> 本章讲用户如何定义和构建自定义 skills；<code>11-skills-system.html</code> 讲整个 skills 系统如何运作。
</div>
```

- [ ] **Step 2: Rewrite `31-building-custom-agents.html` and `32-from-scratch-guide.html` with explicit DeerFlow boundaries**

Ensure `31` includes:

```html
<ul>
  <li><code>backend/packages/harness/deerflow/client.py</code></li>
  <li><code>backend/packages/harness/deerflow/agents/factory.py</code></li>
  <li><code>backend/docs/rfc-create-deerflow-agent.md</code></li>
</ul>
```

Ensure `32` includes:

```html
<ul>
  <li><code>backend/docs/ARCHITECTURE.md</code></li>
  <li><code>backend/docs/API.md</code></li>
  <li><code>backend/docs/AUTH_DESIGN.md</code></li>
</ul>
```

- [ ] **Step 3: Rewrite `40-source-code-guide.html` and `41-troubleshooting-faq.html` as DeerFlow-specific reference chapters**

Ensure `40` includes repository navigation anchors:

```html
<ul>
  <li><code>backend/app/gateway/</code></li>
  <li><code>backend/packages/harness/deerflow/agents/</code></li>
  <li><code>backend/packages/harness/deerflow/runtime/</code></li>
  <li><code>backend/packages/harness/deerflow/sandbox/</code></li>
  <li><code>backend/packages/harness/deerflow/skills/</code></li>
  <li><code>backend/app/channels/</code></li>
</ul>
```

Ensure `41` includes troubleshooting anchors:

```html
<ul>
  <li><code>backend/docs/CONFIGURATION.md</code></li>
  <li><code>backend/docs/STREAMING.md</code></li>
  <li><code>backend/docs/AUTH_DESIGN.md</code></li>
  <li><code>backend/app/gateway/</code></li>
  <li><code>backend/app/channels/</code></li>
</ul>
```

- [ ] **Step 4: Run validator to verify all target chapters pass**

Run:

```bash
python3 scripts/validate_learning_html.py
```

Expected: PASS with `Validated 16 learning chapters successfully.`

- [ ] **Step 5: Commit**

```bash
git add .learning/html/30-custom-skills-guide.html .learning/html/31-building-custom-agents.html .learning/html/32-from-scratch-guide.html .learning/html/40-source-code-guide.html .learning/html/41-troubleshooting-faq.html
git commit -m "docs: rewrite deerflow extension and reference chapters"
```

### Task 6: Final curriculum consistency pass

**Files:**
- Modify: `.learning/html/assets/nav.js`
- Modify: `.learning/README.md`
- Modify: `.learning/html/index.html`
- Test: `scripts/validate_learning_html.py`

- [ ] **Step 1: Align navigation and entry copy with the rewritten curriculum**

Update `.learning/README.md` and `.learning/html/index.html` summary copy to describe the curriculum as DeerFlow-first architecture learning, not generic agent education. Use wording like:

```md
这套课程的核心目标不是泛化介绍 Agent 概念，而是帮助读者通过 DeerFlow 的真实实现掌握生产级 agent harness 的关键设计。
```

- [ ] **Step 2: Refine nav labels only if required by the rewritten chapter bodies**

If chapter titles need punctuation normalization in `.learning/html/assets/nav.js`, use this exact style:

```js
{ num: '02', title: 'LLM调用与工具系统', file: '02-llm-and-tools.html', group: '第一部分：基础概念' },
{ num: '10', title: 'Agent执行引擎的设计与实现', file: '10-agent-execution-engine.html', group: '第二部分：核心模块深度学习' },
```

- [ ] **Step 3: Run final verification**

Run:

```bash
python3 scripts/validate_learning_html.py
rg -n "Gateway-embedded runtime|shared runtime|embedded client|DeerFlow-first" .learning/html .learning/README.md
```

Expected:

- Validator PASS for all targeted chapters.
- `rg` output shows the shared curriculum vocabulary appears across the rewritten set.

- [ ] **Step 4: Commit**

```bash
git add .learning/html/assets/nav.js .learning/html/index.html .learning/README.md
git commit -m "docs: align deerflow learning curriculum navigation and overview"
```
