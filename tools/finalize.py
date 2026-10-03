"""finalize.py —— 唤醒收尾与校验（Agent 跑完之后运行）。

校验 Agent 是否完成了"最小闭环"（AGENTS.md 第 6 节）：
  1. memory/diary/<今天>.md 存在且非空
  2. memory/state.json 合法且 last_wake 已更新
  3. 动作日志合法（tmp/actions.log 每行 JSON）
  4. 无占位符残留

未达标时自动打"补丁"（写入失败日记 + 状态回退），保证仓库永不处于破损状态，
并把结果写成 tmp/wake_report.json 供 CI 判断成功/失败/触发回退。

用法：python tools/finalize.py [--agent-exit N]
退出码：0=完全达标 1=已自动修复 3=严重失败（建议 CI 触发回退重跑）
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from client import ROOT, TMP  # noqa: E402

TZ = dt.timezone(dt.timedelta(hours=8))  # 北京时间


def now() -> dt.datetime:
    return dt.datetime.now(TZ)


def load_actions() -> list[dict]:
    log = TMP / "actions.log"
    actions: list[dict] = []
    if log.exists():
        for line in log.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                actions.append(json.loads(line))
            except json.JSONDecodeError:
                actions.append({"action": "(解析失败)", "raw": line[:120]})
    return actions


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent-exit", type=int, default=0)
    args = parser.parse_args()

    report = {
        "finished_at": now().isoformat(timespec="seconds"),
        "agent_exit": args.agent_exit,
        "checks": {},
        "actions": [],
        "auto_repaired": [],
        "severity": "ok",
    }
    actions = load_actions()
    report["actions"] = actions[-30:]

    today = now().strftime("%Y-%m-%d")
    diary = ROOT / "memory" / "diary" / f"{today}.md"
    state_file = ROOT / "memory" / "state.json"

    # ---- 校验 1：日记 ----
    diary_ok = diary.exists() and diary.read_text(encoding="utf-8").strip() != ""
    report["checks"]["diary"] = diary_ok
    if not diary_ok:
        diary.parent.mkdir(parents=True, exist_ok=True)
        fallback_text = (
            f"# {today}\n\n（这次醒来有点迷糊，没留下完整的日记。"
            f"只记得做了 {len([a for a in actions if 'error' not in a])} 件事就又睡了。）\n"
        )
        diary.write_text(fallback_text, encoding="utf-8")
        report["auto_repaired"].append("diary")
        report["severity"] = "repaired"

    # ---- 校验 2：state.json ----
    state_ok = False
    state: dict = {}
    try:
        state = json.loads(state_file.read_text(encoding="utf-8"))
        state_ok = bool(state.get("last_wake"))
    except Exception:
        state_ok = False
    report["checks"]["state"] = state_ok
    if not state_ok:
        try:
            state = json.loads((ROOT / "memory" / "state.json").read_text(encoding="utf-8"))
        except Exception:
            state = {}
        state["last_wake"] = now().isoformat(timespec="seconds")
        state.setdefault("wake_count", 0)
        state["wake_count"] += 1
        state.setdefault("wake_failures", 0)
        state["wake_failures"] += 1
        state["notes_for_next_wake"] = "（上次唤醒未正常完成，我好像断片了……）"
        state_file.write_text(
            json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        report["auto_repaired"].append("state")
        report["severity"] = "repaired"

    # ---- 校验 3：动作日志合法性 ----
    actions_ok = not any("(解析失败)" in str(a.get("action")) for a in actions)
    report["checks"]["actions_log"] = actions_ok

    # ---- 校验 4：占位符残留 ----
    placeholders = []
    for folder in (ROOT / "memory").rglob("*.md"):
        content = folder.read_text(encoding="utf-8")
        if "TODO" in content or "占位" in content:
            if folder.name != "_template.md":
                placeholders.append(folder.relative_to(ROOT).as_posix())
    report["checks"]["placeholders"] = not placeholders
    if placeholders:
        report["severity"] = "repaired"

    # ---- 校验 5：社区认知是否往前走了一步（软性，不影响成败）----
    # 只看 memory/community.md、memory/people/、memory/knowledge/ 有没有改动：
    # 哪怕没对外说话，今天也认识/学到/记下了点什么——这是"像人"和"慢慢混成熟人"的地基。
    try:
        changed = subprocess.run(
            ["git", "status", "--porcelain", "--",
             "memory/community.md", "memory/people", "memory/knowledge"],
            cwd=ROOT, capture_output=True, text=True, timeout=10,
        ).stdout.strip()
    except Exception:
        changed = ""
    report["checks"]["community_progress"] = bool(changed)

    # ---- 汇总 ----
    if args.agent_exit != 0 and report["severity"] == "ok":
        report["severity"] = "repaired"  # Agent 非零退出但产物齐全：仍算修复级
    if not (report["checks"]["state"] or "state" in report["auto_repaired"]):
        report["severity"] = "fatal"

    TMP.mkdir(parents=True, exist_ok=True)
    (TMP / "wake_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"[finalize] severity={report['severity']} "
          f"checks={report['checks']} repaired={report['auto_repaired']}")
    return {"ok": 0, "repaired": 1}.get(report["severity"], 3)


if __name__ == "__main__":
    sys.exit(main())
