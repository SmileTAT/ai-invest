#!/usr/bin/env python3
"""生成 reports/index.html 总览页。

扫描 decisions/ 与 companies/ 的 frontmatter，汇总为一张自包含的静态 HTML
（内联 CSS，无外部依赖）。用法：

    python3 tools/build_dashboard.py [仓库根目录]
"""

import html
import sys
from datetime import date
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent

ACTION_LABEL = {"buy": "买入", "sell": "卖出", "hold": "持有不动"}
STATUS_LABEL = {"open": "进行中", "closed": "已了结"}
WATCH_LABEL = {"research": "研究中", "hold": "持有", "pass": "已放弃"}


def parse_frontmatter(path: Path) -> dict:
    """解析 YAML frontmatter 的扁平 key: value 字段（不依赖第三方库）。"""
    meta = {}
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return meta
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" not in line or line.strip().startswith("#"):
            continue
        key, _, value = line.partition(":")
        value = value.split(" #")[0].strip().strip('"').strip("'")
        meta[key.strip()] = value
    return meta


def collect(dirname: str) -> list[dict]:
    d = ROOT / dirname
    if not d.is_dir():
        return []
    records = []
    for f in sorted(d.glob("*.md")):
        if f.name.startswith("_"):
            continue
        meta = parse_frontmatter(f)
        meta["_file"] = f"../{dirname}/{f.name}"
        meta["_filename"] = f.name
        records.append(meta)
    return records


def esc(value: str) -> str:
    return html.escape(value or "—")


def table(headers: list[str], rows: list[str], empty_hint: str) -> str:
    if not rows:
        return f'<p class="empty">{empty_hint}</p>'
    head = "".join(f"<th>{h}</th>" for h in headers)
    return (
        '<div class="scroll"><table><thead><tr>'
        + head
        + "</tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table></div>"
    )


def build() -> str:
    decisions = sorted(collect("decisions"), key=lambda m: m.get("date", ""), reverse=True)
    companies = sorted(collect("companies"), key=lambda m: m.get("updated", ""), reverse=True)

    open_count = sum(1 for m in decisions if m.get("status") == "open")
    ungrilled = sum(
        1 for m in decisions if m.get("status") == "open" and m.get("grilled") != "true"
    )

    decision_rows = []
    for m in decisions:
        status = m.get("status", "")
        grilled_ok = m.get("grilled") == "true"
        decision_rows.append(
            "<tr>"
            f"<td>{esc(m.get('date'))}</td>"
            f"<td><a href=\"{esc(m['_file'])}\">{esc(m.get('name') or m.get('ticker'))}</a></td>"
            f"<td>{esc(ACTION_LABEL.get(m.get('action', ''), m.get('action')))}</td>"
            f"<td>{esc(m.get('price'))}</td>"
            f"<td>{esc(m.get('position'))}</td>"
            f"<td><span class=\"badge {esc(status)}\">{esc(STATUS_LABEL.get(status, status))}</span></td>"
            f"<td>{'✅' if grilled_ok else '⚠️ 未拷问'}</td>"
            "</tr>"
        )

    company_rows = []
    for m in companies:
        watch = m.get("watch", "")
        company_rows.append(
            "<tr>"
            f"<td><a href=\"{esc(m['_file'])}\">{esc(m.get('name') or m.get('ticker'))}</a></td>"
            f"<td>{esc(m.get('ticker'))}</td>"
            f"<td>{esc(m.get('market'))}</td>"
            f"<td><span class=\"badge {esc(watch)}\">{esc(WATCH_LABEL.get(watch, watch))}</span></td>"
            f"<td>{esc(m.get('updated'))}</td>"
            "</tr>"
        )

    warn = (
        f'<p class="warn">⚠️ 有 {ungrilled} 笔进行中的决策尚未通过 grilling 拷问。</p>'
        if ungrilled
        else ""
    )

    return f"""<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ai-invest 总览</title>
<style>
  :root {{ --fg: #1a1a1a; --muted: #6b7280; --line: #e5e7eb; --bg: #ffffff; --card: #f8f9fa; }}
  @media (prefers-color-scheme: dark) {{
    :root {{ --fg: #e5e7eb; --muted: #9ca3af; --line: #374151; --bg: #111827; --card: #1f2937; }}
  }}
  body {{ font: 15px/1.7 -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif;
         color: var(--fg); background: var(--bg); max-width: 960px; margin: 0 auto; padding: 2rem 1rem; }}
  h1 {{ font-size: 1.4rem; }} h2 {{ font-size: 1.1rem; margin-top: 2.2rem; }}
  .meta {{ color: var(--muted); font-size: .85rem; }}
  .scroll {{ overflow-x: auto; }}
  table {{ border-collapse: collapse; width: 100%; }}
  th, td {{ text-align: left; padding: .45rem .7rem; border-bottom: 1px solid var(--line); white-space: nowrap; }}
  th {{ color: var(--muted); font-weight: 600; font-size: .82rem; }}
  a {{ color: inherit; }}
  .badge {{ font-size: .78rem; padding: .1rem .5rem; border-radius: 99px; background: var(--card); border: 1px solid var(--line); }}
  .empty {{ color: var(--muted); background: var(--card); padding: 1rem; border-radius: 8px; }}
  .warn {{ background: var(--card); border-left: 3px solid #d97706; padding: .6rem .9rem; border-radius: 4px; }}
</style>
<h1>ai-invest 总览</h1>
<p class="meta">生成于 {date.today().isoformat()} · 决策 {len(decisions)} 笔（进行中 {open_count}）· 个股档案 {len(companies)} 份</p>
{warn}
<h2>决策记录</h2>
{table(["日期", "标的", "动作", "价格", "仓位", "状态", "拷问"], decision_rows, "暂无决策记录 — 从 decisions/_template.md 复制开始第一笔。")}
<h2>个股档案</h2>
{table(["名称", "代码", "市场", "状态", "更新"], company_rows, "暂无个股档案 — 从 companies/_template.md 复制开始第一份。")}
"""


def main() -> None:
    out = ROOT / "reports" / "index.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text(build(), encoding="utf-8")
    print(f"written: {out}")


if __name__ == "__main__":
    main()
