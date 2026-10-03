"""唤醒数据准备 —— "睁眼"。

在 Agent（Open Code）启动之前运行：
  1. 建立社区会话（含自动回退登录）
  2. 拉取"自上次唤醒以来发生的一切"：消息/通知/自己作品的评论/社区最新动态
  3. 汇总写入 tmp/inbox.json（Agent 的唯一事实输入，只读）

用法：python tools/prepare.py [--browse-pages N]
退出码：0=成功 2=登录失败 3=社区不可达
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from client import ROOT, TMP, PlwebClient, PlwebError, brief  # noqa: E402


def _load_state() -> dict:
    state_file = ROOT / "memory" / "state.json"
    if state_file.exists():
        return json.loads(state_file.read_text(encoding="utf-8"))
    return {}


def _dt(ms: int) -> str:
    if not ms:
        return ""
    return time.strftime("%Y-%m-%d %H:%M", time.gmtime(ms / 1000 + 8 * 3600))  # 北京时间


def _trim(item: dict) -> dict:
    """保留 Agent 决策需要的字段，控制 inbox 体积。"""
    user = item.get("User") or {}
    author = item.get("Author") or {}
    desc = item.get("Description")
    if isinstance(desc, list):
        desc = "\n".join(str(x) for x in desc if str(x).strip())
    out = {
        "id": item.get("ID"),
        "content_id": item.get("ContentID"),
        "subject": item.get("Subject"),
        "description": desc,
        "category": item.get("Category"),
        "tags": item.get("Tags"),
        "author": {
            "id": (user or author).get("ID"),
            "nickname": (user or author).get("Nickname"),
        },
        "stars": item.get("Stars"),
        "comments": item.get("Comments"),
        "creation_date": _dt(item.get("CreationDate") or 0),
    }
    if item.get("Floor") is not None:  # 评论对象
        out.update(
            {
                "floor": item.get("Floor"),
                "content": item.get("Content"),
                "send_date": item.get("SendDate"),
            }
        )
    if item.get("Title") is not None:  # 消息对象
        out.update(
            {
                "title": item.get("Title"),
                "content": item.get("Content"),
                "send_date": item.get("SendDate"),
                "is_read": item.get("IsRead"),
            }
        )
    return {k: v for k, v in out.items() if v is not None}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--browse-pages", type=int, default=2,
                        help="每个板块翻页数（每页16条）")
    parser.add_argument("--my-works", type=int, default=3, help="检查自己最近作品数")
    args = parser.parse_args()

    TMP.mkdir(parents=True, exist_ok=True)
    state = _load_state()
    inbox: dict = {
        "now": time.strftime("%Y-%m-%d %H:%M:%S"),
        "weekday": time.strftime("%A"),
        "identity": {
            "nickname": state.get("nickname"),
            "user_id": state.get("user_id"),
            "wake_count": state.get("wake_count", 0) + 1,
        },
        "errors": [],
    }

    try:
        client = PlwebClient.from_env()
    except PlwebError as e:
        inbox["errors"].append(f"会话建立失败：{e}")
        (TMP / "inbox.json").write_text(
            json.dumps(inbox, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"[prepare] 登录失败：{e}", file=sys.stderr)
        return 2

    print(f"[prepare] 会话 OK：{client.nickname} ({client.user_id})")

    # ---- 1. 站内信（评论/回复/私信通知） ----
    try:
        messages = client.get_messages(take=20)
        inbox["messages"] = [_trim(m) for m in messages]
        print(f"[prepare] 站内信 {len(messages)} 条")
    except PlwebError as e:
        inbox["errors"].append(f"消息拉取失败：{e}")

    # ---- 2. 系统通知 ----
    try:
        notes = client.get_notifications(take=10)
        inbox["notifications"] = [
            {"title": n.get("Title"), "content": n.get("Content"),
             "date": n.get("SendDate")} for n in notes
        ]
        print(f"[prepare] 通知 {len(notes)} 条")
    except PlwebError as e:
        inbox["errors"].append(f"通知拉取失败：{e}")

    # ---- 3. 自己最近作品的评论（谁 @ 我/回复我） ----
    try:
        profile = client.get_profile(client.user_id)
        latest = ((profile.get("Experiments") or {}).get("Latest-Experiments") or {})
        if isinstance(latest, dict):
            latest = latest.get("$values") or []
        my_works = []
        for work in latest[: args.my_works]:
            comments = client.get_comments(
                work.get("ID"), work.get("Category") or "Experiment", take=10
            )
            my_works.append(
                {
                    "work": _trim(work),
                    "recent_comments": [
                        _trim(c) for c in comments if not (
                            (c.get("Author") or {}).get("ID") == client.user_id
                        )
                    ],
                }
            )
        inbox["my_works"] = my_works
        print(f"[prepare] 自己作品 {len(my_works)} 个")
    except PlwebError as e:
        inbox["errors"].append(f"自己作品检查失败：{e}")

    # ---- 4. 社区最新动态（实验区+讨论区）----
    # 注意：服务端对 Take>16 的查询会挂起，必须用 16 条/页翻页
    for category in ("Experiment", "Discussion"):
        try:
            items: list[dict] = []
            for page in range(args.browse_pages):
                batch = client.query_experiments(
                    category=category, take=16, skip=16 * page, sort=0
                )
                items.extend(batch)
                if len(batch) < 16:
                    break
            print(f"[prepare] {category} 最新 {len(items)} 条", flush=True)
            inbox[f"latest_{category.lower()}s"] = [_trim(i) for i in items]
        except PlwebError as e:
            inbox["errors"].append(f"{category} 拉取失败：{e}")

    # ---- 5. 我关注的人的最新作品（社交圈的动态） ----
    try:
        relations = client.get_relations()
        following = (relations.get("Following") or {})
        if isinstance(following, dict):
            following = following.get("$values") or []
        if following:
            inbox["following"] = [
                {"id": u.get("ID"), "nickname": u.get("Nickname")} for u in following[:20]
            ]
    except PlwebError as e:
        inbox["errors"].append(f"关注列表拉取失败：{e}")

    (TMP / "inbox.json").write_text(
        json.dumps(inbox, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    size = (TMP / "inbox.json").stat().st_size
    print(f"[prepare] inbox.json 就绪（{size} bytes）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
