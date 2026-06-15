#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
HTML_DIR = ROOT / ".learning" / "html"
REQUIRED_HEADINGS = [
    "这项能力在 DeerFlow 中解决什么问题",
    "这项能力在代码库中的位置",
    "真实运行链路或数据链路",
    "配置面与使用方式",
    "关键实现细节与权衡",
    "当前限制、边界与非目标",
    "它与 DeerFlow 其他能力的关系",
]

TARGETS: dict[str, dict[str, object]] = {
    "02-llm-and-tools.html": {
        "title": "LLM调用与工具系统",
        "required_headings": REQUIRED_HEADINGS,
        "required_paths": [
            "backend/packages/harness/deerflow/tools/tools.py",
            "backend/packages/harness/deerflow/agents/factory.py",
        ],
    },
    "03-deerflow-overview.html": {
        "title": "DeerFlow 整体架构概览",
        "required_headings": REQUIRED_HEADINGS,
        "required_paths": [
            "backend/docs/ARCHITECTURE.md",
            "backend/app/gateway/app.py",
        ],
    },
    "10-agent-execution-engine.html": {
        "title": "Agent执行引擎的设计与实现",
        "required_headings": REQUIRED_HEADINGS,
        "required_paths": [
            "backend/packages/harness/deerflow/agents/lead_agent/agent.py",
            "backend/packages/harness/deerflow/runtime/runs/worker.py",
        ],
    },
    "11-skills-system.html": {
        "title": "Skills系统：Agent的能力扩展",
        "required_headings": REQUIRED_HEADINGS,
        "required_paths": [
            "backend/packages/harness/deerflow/skills/installer.py",
            "backend/app/gateway/routers/skills.py",
        ],
    },
    "12-sandbox-execution.html": {
        "title": "Sandbox与安全执行环境",
        "required_headings": REQUIRED_HEADINGS,
        "required_paths": [
            "backend/packages/harness/deerflow/sandbox/tools.py",
            "backend/packages/harness/deerflow/sandbox/local/local_sandbox_provider.py",
        ],
    },
    "13-memory-system.html": {
        "title": "长期记忆系统",
        "required_headings": REQUIRED_HEADINGS,
        "required_paths": [
            "backend/packages/harness/deerflow/agents/memory/storage.py",
            "backend/packages/harness/deerflow/agents/memory/updater.py",
        ],
    },
    "14-sub-agents.html": {
        "title": "Sub-Agents：多Agent协作",
        "required_headings": REQUIRED_HEADINGS,
        "required_paths": [
            "backend/packages/harness/deerflow/tools/builtins/task_tool.py",
            "backend/packages/harness/deerflow/subagents/executor.py",
        ],
    },
    "15-gateway-api.html": {
        "title": "Gateway API：与外界的接口",
        "required_headings": REQUIRED_HEADINGS,
        "required_paths": [
            "backend/app/gateway/app.py",
            "backend/app/gateway/routers/thread_runs.py",
        ],
    },
    "20-context-engineering.html": {
        "title": "上下文工程：提升Agent智能",
        "required_headings": REQUIRED_HEADINGS,
        "required_paths": [
            "backend/packages/harness/deerflow/agents/lead_agent/prompt.py",
            "backend/packages/harness/deerflow/agents/middlewares",
        ],
    },
    "21-model-integration.html": {
        "title": "模型集成：支持多种LLM",
        "required_headings": REQUIRED_HEADINGS,
        "required_paths": [
            "backend/packages/harness/deerflow/config/app_config.py",
            "backend/app/gateway/routers/models.py",
        ],
    },
    "22-channels-integration.html": {
        "title": "多渠道集成：从IM到API",
        "required_headings": REQUIRED_HEADINGS,
        "required_paths": [
            "backend/app/channels/manager.py",
            "backend/app/gateway/routers/channel_connections.py",
        ],
    },
    "23-advanced-patterns.html": {
        "title": "高级模式和最佳实践",
        "required_headings": REQUIRED_HEADINGS,
        "required_paths": [
            "backend/packages/harness/deerflow/tools/builtins/tool_search.py",
            "backend/packages/harness/deerflow/tools/builtins/task_tool.py",
        ],
    },
    "30-custom-skills-guide.html": {
        "title": "自定义Skills完全指南",
        "required_headings": REQUIRED_HEADINGS,
        "required_paths": [
            "backend/packages/harness/deerflow/skills",
            "backend/packages/harness/deerflow/skills/installer.py",
        ],
    },
    "31-building-custom-agents.html": {
        "title": "构建自定义Agent",
        "required_headings": REQUIRED_HEADINGS,
        "required_paths": [
            "backend/packages/harness/deerflow/agents/factory.py",
            "backend/packages/harness/deerflow/client.py",
        ],
    },
    "32-from-scratch-guide.html": {
        "title": "从零构建Agent系统",
        "required_headings": REQUIRED_HEADINGS,
        "required_paths": [
            "backend/docs/ARCHITECTURE.md",
            "backend/docs/API.md",
        ],
    },
    "40-source-code-guide.html": {
        "title": "源码导航与阅读指南",
        "required_headings": REQUIRED_HEADINGS,
        "required_paths": [
            "backend/app/gateway",
            "backend/packages/harness/deerflow/agents",
        ],
    },
    "41-troubleshooting-faq.html": {
        "title": "常见问题与故障排除",
        "required_headings": REQUIRED_HEADINGS,
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
    errors: list[str] = []
    file_path = HTML_DIR / filename

    try:
        text = file_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        errors.append(f"{filename}: file not found at {file_path}")
        return errors
    except OSError as exc:
        errors.append(f"{filename}: unable to read file ({exc})")
        return errors

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
