#!/usr/bin/env python3
"""
Mermaid 图表静态分析脚本 v2
检查所有 .md 文件中的 mermaid 代码块。
"""

import re
import sys
import os
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Optional


@dataclass
class DiagramIssue:
    file: str
    section: str
    diagram_type: str
    severity: str  # ERROR / WARN
    description: str


def extract_mermaid_blocks(filepath: str) -> List[Tuple[str, str, int]]:
    """返回 [(section_title, code, start_line), ...]"""
    with open(filepath, encoding="utf-8") as f:
        lines = f.readlines()
    blocks = []
    current_section = ""
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if stripped.startswith("## "):
            current_section = stripped[3:].strip()
        if stripped.startswith("```mermaid"):
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            blocks.append((current_section, "\n".join(code_lines), i))
        i += 1
    return blocks


# ===== graph / flowchart 解析 =====

def strip_node_shapes(text: str) -> Tuple[str, Dict[str, str]]:
    """
    从一行文本中去掉节点形状，返回 (纯ID文本, {ID: label})
    同时处理带引号和不带引号的标签。
    """
    labels = {}

    # 1. 先匹配带引号的: ID["label"] / ID('label') / ID{"label"}
    for m in re.finditer(r'([A-Za-z_][A-Za-z0-9_]*)\s*([\[\(\{])\s*"([^"]*)"\s*([\]\)\}])', text):
        labels[m.group(1)] = m.group(3)
    # 去掉带引号的节点定义
    text_clean = re.sub(
        r'([A-Za-z_][A-Za-z0-9_]*)\s*([\[\(\{])\s*"[^"]*"\s*([\]\)\}])',
        r'\1', text)

    # 2. 匹配不带引号的: ID[label] / ID(label) / ID{label}
    # 需要递归处理，因为标签内可能有括号
    # 简化：匹配最外层括号对
    for m in re.finditer(r'([A-Za-z_][A-Za-z0-9_]*)\s*\[\s*([^\[\]]*)\s*\]', text_clean):
        labels[m.group(1)] = m.group(2).strip()
    text_clean = re.sub(
        r'([A-Za-z_][A-Za-z0-9_]*)\s*\[\s*[^\[\]]*\s*\]',
        r'\1', text_clean)

    for m in re.finditer(r'([A-Za-z_][A-Za-z0-9_]*)\s*\(\s*([^\(\)]*)\s*\)', text_clean):
        labels[m.group(1)] = m.group(2).strip()
    text_clean = re.sub(
        r'([A-Za-z_][A-Za-z0-9_]*)\s*\(\s*[^\(\)]*\s*\)',
        r'\1', text_clean)

    for m in re.finditer(r'([A-Za-z_][A-Za-z0-9_]*)\s*\{\s*([^\{\}]*)\s*\}', text_clean):
        labels[m.group(1)] = m.group(2).strip()
    text_clean = re.sub(
        r'([A-Za-z_][A-Za-z0-9_]*)\s*\{\s*[^\{\}]*\s*\}',
        r'\1', text_clean)

    # 3. 双圆 (( ))
    for m in re.finditer(r'([A-Za-z_][A-Za-z0-9_]*)\s*\(\(([^)]*)\)\)', text):
        labels[m.group(1)] = m.group(2).strip()
    text_clean = re.sub(
        r'([A-Za-z_][A-Za-z0-9_]*)\s*\(\([^)]*\)\)',
        r'\1', text_clean)

    # 4. 终点 ([])
    for m in re.finditer(r'([A-Za-z_][A-Za-z0-9_]*)\s*\(\[([^\]]*)\]\)', text):
        labels[m.group(1)] = m.group(2).strip()
    text_clean = re.sub(
        r'([A-Za-z_][A-Za-z0-9_]*)\s*\(\[[^\]]*\]\)',
        r'\1', text_clean)

    # 5. 旗形 > ]
    for m in re.finditer(r'([A-Za-z_][A-Za-z0-9_]*)\s*>\s*([^\]]*)\]', text):
        labels[m.group(1)] = m.group(2).strip()
    text_clean = re.sub(
        r'([A-Za-z_][A-Za-z0-9_]*)\s*>\s*[^\]]*\]',
        r'\1', text_clean)

    return text_clean, labels


def parse_graph_edges(text: str) -> List[Tuple[str, str]]:
    """从纯ID文本中提取所有边"""
    edges = []
    # 匹配 A --> B, A -.-> B, A ==> B, A -- text --> B 等
    # 先匹配带 -- text --> 的
    for m in re.finditer(
        r'([A-Za-z_][A-Za-z0-9_]*|\[\*\])\s*'
        r'(?:--\s*[^>|]+?\s*-->|-\.->|==>|-->|---|-\.->|~~>|--[ox]|[-=]+>)\s*'
        r'([A-Za-z_][A-Za-z0-9_]*|\[\*\])',
        text
    ):
        edges.append((m.group(1), m.group(2)))

    # 匹配 A -->|label| B, A -.->|label| B, A ==>|label| B 等
    for m in re.finditer(
        r'([A-Za-z_][A-Za-z0-9_]*|\[\*\])\s*'
        r'(?:--\s*[^>|]+?\s*-->|-?\.->|==>|-->|---|~~>|[-=]+>)\s*\|\s*([^|]*)\s*\|\s*'
        r'([A-Za-z_][A-Za-z0-9_]*|\[\*\])',
        text
    ):
        edges.append((m.group(1), m.group(3)))

    return edges


def analyze_graph(code: str, filename: str, section: str) -> List[DiagramIssue]:
    issues = []
    node_labels: Dict[str, str] = {}
    node_defined: Set[str] = set()
    all_edges: List[Tuple[str, str]] = []
    styled_nodes: Set[str] = set()
    subgraph_ids: Set[str] = set()
    # 节点ID出现顺序和首次是否有标签
    node_first_has_label: Dict[str, bool] = {}

    lines = code.split("\n")
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("%%"):
            continue
        if stripped.startswith("graph") or stripped.startswith("flowchart"):
            continue

        # subgraph
        if stripped.startswith("subgraph"):
            sm = re.match(r'subgraph\s+([A-Za-z_][A-Za-z0-9_]*)', stripped)
            if sm:
                subgraph_ids.add(sm.group(1))
            continue
        if stripped == "end":
            continue

        # style
        if stripped.startswith("style "):
            parts = stripped.split()
            if len(parts) >= 2:
                styled_nodes.add(parts[1])
            continue
        if stripped.startswith("classDef") or stripped.startswith("class "):
            continue
        if stripped.startswith("linkStyle"):
            continue

        # 提取节点标签
        _, labels = strip_node_shapes(stripped)
        for nid, label in labels.items():
            node_defined.add(nid)
            if nid not in node_first_has_label:
                node_first_has_label[nid] = True
            if nid in node_labels and node_labels[nid] != label and label:
                # 标签冲突
                issues.append(DiagramIssue(
                    filename, section, "graph", "ERROR",
                    f"节点 '{nid}' 标签冲突: '{node_labels[nid]}' vs '{label}'"
                ))
            if label:
                node_labels[nid] = label

        # 提取边（先去掉节点形状）
        clean_text, _ = strip_node_shapes(stripped)
        edges = parse_graph_edges(clean_text)
        all_edges.extend(edges)

        # 记录边中出现的裸ID
        for src, dst in edges:
            for nid in [src, dst]:
                if nid == "[*]":
                    continue
                if nid not in node_first_has_label:
                    node_first_has_label[nid] = False

    # 收集所有节点
    edge_nodes = set()
    for s, d in all_edges:
        if s != "[*]":
            edge_nodes.add(s)
        if d != "[*]":
            edge_nodes.add(d)

    all_nodes = node_defined | edge_nodes | set(node_labels.keys())

    # 检查1: style引用不存在的节点（排除subgraph）
    for sn in styled_nodes:
        if sn not in all_nodes and sn not in subgraph_ids:
            issues.append(DiagramIssue(
                filename, section, "graph", "ERROR",
                f"style 引用了不存在的节点: '{sn}'"
            ))

    # 检查2: 定义了标签但完全孤立（没有任何边连接）的节点
    for nid, label in node_labels.items():
        if nid not in edge_nodes:
            # 排除subgraph
            if nid not in subgraph_ids:
                issues.append(DiagramIssue(
                    filename, section, "graph", "WARN",
                    f"孤立节点 '{nid}' [{label}] 无任何边连接"
                ))

    # 检查3: 边引用了但从未定义标签的节点（会显示原始英文ID）
    bare_id_nodes = set()
    for src, dst in all_edges:
        for nid in [src, dst]:
            if nid == "[*]":
                continue
            if nid not in node_labels and nid not in subgraph_ids:
                bare_id_nodes.add(nid)
    for nid in sorted(bare_id_nodes):
        issues.append(DiagramIssue(
            filename, section, "graph", "WARN",
            f"节点 '{nid}' 在边中被引用但从未定义标签，将显示原始ID"
        ))

    # 检查4: 边标签中含中文括号等可能引发解析问题的字符
    # |label| 中如果有 ()[]{} 可能导致渲染问题
    for line in lines:
        stripped = line.strip()
        for m in re.finditer(r'\|([^|]*)\|', stripped):
            label = m.group(1)
            for ch in ['(', ')', '[', ']', '{', '}']:
                if ch in label:
                    issues.append(DiagramIssue(
                        filename, section, "graph", "WARN",
                        f"边标签 '{label}' 含括号字符 '{ch}'，可能导致渲染异常"
                    ))

    # 检查5: subgraph ID 与节点 ID 冲突
    for sid in subgraph_ids:
        if sid in node_labels:
            issues.append(DiagramIssue(
                filename, section, "graph", "ERROR",
                f"subgraph ID '{sid}' 与节点 ID 冲突"
            ))
        if sid in edge_nodes:
            issues.append(DiagramIssue(
                filename, section, "graph", "ERROR",
                f"subgraph ID '{sid}' 被边引用，会导致混淆"
            ))

    return issues


# ===== stateDiagram-v2 分析 =====

def analyze_state_diagram(code: str, filename: str, section: str) -> List[DiagramIssue]:
    issues = []
    lines = code.split("\n")

    composite_states: Dict[str, List[str]] = {}
    top_transitions: List[Tuple[str, str]] = []
    current_composite: Optional[str] = None

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("%%"):
            continue
        if stripped.startswith("note") or stripped.startswith("end note") or stripped.startswith("direction"):
            continue

        # state X {
        comp_m = re.match(r'state\s+([A-Za-z_][A-Za-z0-9_]*)\s*\{', stripped)
        if comp_m:
            current_composite = comp_m.group(1)
            composite_states[current_composite] = []
            continue
        if stripped.startswith("}"):
            current_composite = None
            continue

        # 转换 A --> B: label
        trans_m = re.match(
            r'([A-Za-z_][A-Za-z0-9_]*|\[\*\])\s*-->\s*([A-Za-z_][A-Za-z0-9_]*|\[\*\])',
            stripped)

        if current_composite:
            composite_states[current_composite].append(stripped)
        elif trans_m:
            top_transitions.append((trans_m.group(1), trans_m.group(2)))

    # 外部状态
    outer_states = set()
    for src, dst in top_transitions:
        if src != "[*]":
            outer_states.add(src)
        if dst != "[*]":
            outer_states.add(dst)

    # 检查复合状态内部引用外部状态
    for comp_name, inner_lines in composite_states.items():
        inner_states = set()
        inner_refs = set()
        for line in inner_lines:
            # 内部状态别名
            if re.match(r'state\s+"', line):
                m = re.match(r'state\s+"[^"]*"\s+as\s+([A-Za-z_][A-Za-z0-9_]*)', line)
                if m:
                    inner_states.add(m.group(1))
                continue
            trans_m = re.match(
                r'([A-Za-z_][A-Za-z0-9_]*|\[\*\])\s*-->\s*([A-Za-z_][A-Za-z0-9_]*|\[\*\])',
                line)
            if trans_m:
                src, dst = trans_m.group(1), trans_m.group(2)
                if src != "[*]":
                    inner_refs.add(src)
                if dst != "[*]":
                    inner_refs.add(dst)

        for ref in inner_refs:
            if ref in inner_states:
                continue
            if ref == comp_name:
                continue
            # 引用了外部终态
            if ref in outer_states:
                issues.append(DiagramIssue(
                    filename, section, "stateDiagram", "ERROR",
                    f"复合状态 '{comp_name}' 内部引用了外部状态 '{ref}'，"
                    f"会导致渲染混乱"
                ))

    # 检查无效语法: XXX: 描述
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("%%") or stripped.startswith("note"):
            continue
        if '-->' in stripped:
            continue
        colon_desc = re.match(r'([A-Za-z_][A-Za-z0-9_]*)\s*:\s*(.+)', stripped)
        if colon_desc and not stripped.startswith("direction") and not stripped.startswith("state "):
            issues.append(DiagramIssue(
                filename, section, "stateDiagram", "WARN",
                f"疑似无效语法 '{stripped}'"
            ))

    return issues


# ===== 主流程 =====

def main():
    flowchart_dir = os.path.dirname(os.path.abspath(__file__))
    target_files = [
        "00-index.md",
        "01-architecture.md",
        "02-data-flow.md",
        "03-lead-agent-calls.md",
        "04-subagent-execution.md",
        "05-sandbox-execution.md",
        "06-memory-system.md",
        "07-frontend-architecture.md",
        "08-frontend-architecture.md",
        "09-config-skills-tools.md",
        "10-advanced-features.md",
    ]

    all_issues: List[DiagramIssue] = []

    for fname in target_files:
        fpath = os.path.join(flowchart_dir, fname)
        if not os.path.exists(fpath):
            continue
        blocks = extract_mermaid_blocks(fpath)
        for section, code, _ in blocks:
            first_line = code.strip().split("\n")[0].strip() if code.strip() else ""
            if first_line.startswith("graph") or first_line.startswith("flowchart"):
                all_issues.extend(analyze_graph(code, fname, section))
            elif first_line.startswith("stateDiagram"):
                all_issues.extend(analyze_state_diagram(code, fname, section))

    if not all_issues:
        print("=" * 60)
        print("  [PASS] ALL CHECKS PASSED")
        print("=" * 60)
        return 0

    errors = [i for i in all_issues if i.severity == "ERROR"]
    warns = [i for i in all_issues if i.severity == "WARN"]

    print("=" * 60)
    print(f"  [FAIL] {len(errors)} ERRORS, {len(warns)} WARNINGS")
    print("=" * 60)

    current_file = ""
    for issue in all_issues:
        if issue.file != current_file:
            current_file = issue.file
            print(f"\n>> {issue.file}")
        icon = "[E]" if issue.severity == "ERROR" else "[W]"
        print(f"  {icon} [{issue.diagram_type}] section: {issue.section}")
        print(f"     {issue.description}")

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
