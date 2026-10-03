"""act.py —— 赛博生命的动作执行器（Agent 调用的 CLI）。

Agent（Open Code）通过 bash 调用本脚本执行社区动作。所有动作：
  - 自动复用 prepare.py 建立的会话（tmp/session.json）
  - 自动追加到 tmp/actions.log（动作流水，供 finalize 校验与运营者审计）
  - 输出 JSON 到 stdout（Agent 读取结果）

常用动作：
  python tools/act.py comment   --content-id <id> --category Experiment --text "..."
  python tools/act.py star      --content-id <id> --category Experiment [--off]
  python tools/act.py follow    --user-id <id> [--off]
  python tools/act.py send-message --to <用户ID或昵称> --text "..."
  python tools/act.py post-discussion --subject "标题" --body "正文（\\n换行）" [--tag 交流]
  python tools/act.py remove-my-post --content-id <id> --category Discussion
  python tools/act.py rename --nickname "新昵称"
  python tools/act.py signature --text "新签名"
  python tools/act.py get-summary --content-id <id> --category Experiment
  python tools/act.py get-comments --content-id <id> --category Experiment
  python tools/act.py query --category Discussion --take 16 --skip 0 [--days 7]
  python tools/act.py get-user --name 昵称
  python tools/act.py get-messages --take 16        # 会话中途查新消息（挂机用）
  python tools/act.py get-profile --user-id <id>
  python tools/act.py publish-experiment ...（转调 experiment_gen.py，需 Python3.14+physicslab）
"""

from __future__ import annotations

import argparse
import gzip
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from client import ROOT, TMP, ACTION_LOG, PlwebClient, PlwebError  # noqa: E402


def _out(payload: dict) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def _log_action(entry: dict) -> None:
    ACTION_LOG.parent.mkdir(parents=True, exist_ok=True)
    entry["ts"] = time.strftime("%Y-%m-%d %H:%M:%S")
    with ACTION_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


DISCUSSION_WORKSPACE_TEMPLATE = {
    "$type": "Quantum.Models.Contents.Experiment, Quantum Models",
    "ID": None,
    "Type": 0,
    "Components": 0,
    "Subject": None,
    "StatusSave": '{"MainIdentifier":null,"Elements":{},"WorldTime":0,'
    '"ScalingName":"太阳系","LengthScale":1.0,"SizeLinear":1.0,'
    '"SizeNonlinear":1.0,"StarPresent":false,"Setting":null}',
    "CameraSave": '{"Mode":1,"Distance":10.0,"VisionCenter":"0,0,0",'
    '"TargetRotation":"0,0,0"}',
    "Version": 2411,
    "CreationDate": None,
    "Paused": False,
}


def cmd_post_discussion(client: PlwebClient, args: argparse.Namespace) -> dict:
    """发布讨论帖：SubmitExperiment(gzip) -> ConfirmExperiment。"""
    now_ms = int(time.time() * 1000)
    me = client.me()
    summary = {
        "Type": 0,
        "ParentID": None,
        "ParentName": None,
        "ParentCategory": None,
        "ContentID": None,
        "Editor": None,
        "Coauthors": [],
        "Description": [line for line in args.body.split("\\n")],
        "LocalizedDescription": None,
        "Tags": ["Type-0"] + [t for t in (args.tag or "").split(",") if t.strip()],
        "ModelID": None,
        "ModelName": None,
        "ModelTags": [],
        "Version": 2411,
        "Language": "Chinese",
        "Visits": 0,
        "Stars": 0,
        "Supports": 0,
        "Remixes": 0,
        "Comments": 0,
        "Price": 0,
        "Popularity": 0,
        "CreationDate": now_ms,
        "UpdateDate": now_ms,
        "SortingDate": now_ms,
        "ID": None,
        "Category": "Discussion",
        "Subject": args.subject,
        "LocalizedSubject": None,
        "Image": 0,
        "ImageRegion": 0,
        "Visibility": 0,
        "Settings": {},
        "Multilingual": False,
        "User": {
            "ID": client.user_id,
            "Nickname": me.get("Nickname"),
            "Signature": me.get("Signature") or "",
            "Avatar": me.get("Avatar") or 0,
            "AvatarRegion": me.get("AvatarRegion") or 0,
            "Decoration": me.get("Decoration") or 0,
            "Verification": me.get("Verification") or "",
        },
    }
    workspace = dict(DISCUSSION_WORKSPACE_TEMPLATE)
    workspace["CreationDate"] = now_ms

    submit_body = {"Summary": summary, "Workspace": workspace}
    raw = json.dumps(submit_body).encode("utf-8")
    resp = client.post_raw(
        "Contents/SubmitExperiment",
        gzip.compress(raw),
        extra_headers={
            "Content-Type": "gzipped/json",
            "Accept-Encoding": "gzip",
            "x-API-Version": "2411",
        },
    )
    if resp.get("Status") != 200:
        raise PlwebError(f"SubmitExperiment 失败：{resp.get('Message')}", code=3,
                         status=resp.get("Status"))
    new_id = (resp.get("Data") or {}).get("Summary", {}).get("ID")
    confirm = client.confirm_experiment(new_id, "Discussion", 0, ".jpg")
    result = {
        "action": "post-discussion",
        "subject": args.subject,
        "summary_id": new_id,
        "confirm_status": confirm.get("Status"),
    }
    _log_action(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("comment")
    p.add_argument("--content-id", required=True)
    p.add_argument("--category", default="Experiment",
                   choices=["Experiment", "Discussion", "User"])
    p.add_argument("--text", required=True)
    p.add_argument("--reply-to", default=None, help="被回复的评论 ID（楼层回复）")

    p = sub.add_parser("remove-comment")
    p.add_argument("--comment-id", required=True)
    p.add_argument("--category", default="Experiment",
                   choices=["Experiment", "Discussion", "User"])

    p = sub.add_parser("star")
    p.add_argument("--content-id", required=True)
    p.add_argument("--category", default="Experiment")
    p.add_argument("--off", action="store_true", help="取消点赞")

    p = sub.add_parser("follow")
    p.add_argument("--user-id", required=True)
    p.add_argument("--off", action="store_true", help="取关")

    p = sub.add_parser("send-message")
    p.add_argument("--to", required=True, help="用户 ID 或昵称")
    p.add_argument("--text", required=True)

    p = sub.add_parser("post-discussion")
    p.add_argument("--subject", required=True)
    p.add_argument("--body", required=True, help="正文，\\n 表示换行")
    p.add_argument("--tag", default="交流", help="附加标签，逗号分隔（如 问与答）")

    p = sub.add_parser("remove-my-post")
    p.add_argument("--content-id", required=True)
    p.add_argument("--category", default="Discussion")

    p = sub.add_parser("rename")
    p.add_argument("--nickname", required=True)

    p = sub.add_parser("signature")
    p.add_argument("--text", required=True)

    for name in ("get-summary", "get-comments"):
        p = sub.add_parser(name)
        p.add_argument("--content-id", required=True)
        p.add_argument("--category", default="Experiment")

    p = sub.add_parser("query")
    p.add_argument("--category", default="Experiment")
    p.add_argument("--take", type=int, default=16)
    p.add_argument("--skip", type=int, default=0)
    p.add_argument("--days", type=int, default=0)

    p = sub.add_parser("get-user")
    p.add_argument("--name")
    p.add_argument("--user-id")

    p = sub.add_parser("get-profile")
    p.add_argument("--user-id", required=True)

    p = sub.add_parser("get-messages")
    p.add_argument("--take", type=int, default=16)
    p.add_argument("--skip", type=int, default=0)

    p = sub.add_parser("publish-experiment")
    p.add_argument("--template", required=True, help="experiment_gen.py 的模板名")
    p.add_argument("--subject", required=True)
    p.add_argument("--description", default="", help="作品描述，\\n 换行")

    args = parser.parse_args()

    try:
        if args.cmd == "publish-experiment":
            # 需 physicslab（Python3.14），转调独立脚本
            import subprocess
            venv_py = ROOT / "tools" / ".venv" / "bin" / "python"
            py = str(venv_py) if venv_py.exists() else sys.executable
            proc = subprocess.run(
                [py, str(ROOT / "tools" / "experiment_gen.py"),
                 "--template", args.template,
                 "--subject", args.subject,
                 "--description", args.description],
                capture_output=True, text=True, timeout=600,
            )
            print(proc.stdout)
            if proc.returncode != 0:
                print(proc.stderr, file=sys.stderr)
                return 3
            return 0

        client = PlwebClient.from_env()

        if args.cmd == "comment":
            r = client.post_comment(args.content_id, args.category, args.text,
                                    reply_to=args.reply_to)
            result = {"action": "comment", "status": r.get("Status"),
                      "content_id": args.content_id,
                      "comment_id": (r.get("Data") or {}).get("ID")}
        elif args.cmd == "remove-comment":
            r = client.remove_comment(args.comment_id, args.category)
            result = {"action": "remove-comment", "status": r.get("Status"),
                      "comment_id": args.comment_id}
        elif args.cmd == "star":
            r = client.star(args.content_id, args.category,
                            0 if args.off else 1)
            result = {"action": "star", "status": r.get("Status"),
                      "content_id": args.content_id, "off": args.off}
        elif args.cmd == "follow":
            r = client.follow(args.user_id, not args.off)
            result = {"action": "follow", "status": r.get("Status"),
                      "user_id": args.user_id, "off": args.off}
        elif args.cmd == "send-message":
            target = args.to
            if not target or not all(c in "0123456789abcdef" for c in target):
                u = client.get_user(name=target)
                target = u.get("ID")
                if not target:
                    raise PlwebError(f"找不到用户：{args.to}")
            r = client.send_message(target, args.text)
            result = {"action": "send-message", "status": r.get("Status"),
                      "to": target}
        elif args.cmd == "post-discussion":
            # 委托给 experiment_gen.py（需要 Python3.14+physicslab 的可靠通道）
            import subprocess
            candidates = [sys.executable]
            if os.environ.get("PYTHON314_BIN"):
                candidates.insert(0, os.environ["PYTHON314_BIN"])
            for cand in ("python3.14", "python3"):
                if cand not in candidates:
                    candidates.append(cand)
            gen = str(ROOT / "tools" / "experiment_gen.py")
            for interp in candidates:
                try:
                    proc = subprocess.run(
                        [interp, gen, "post-discussion",
                         "--subject", args.subject,
                         "--body", args.body,
                         "--tag", args.tag or "交流"],
                        capture_output=True, text=True, timeout=180,
                        env={**dict(os.environ)})
                except (subprocess.SubprocessError, OSError):
                    continue
                if proc.stdout.strip():
                    print(proc.stdout.strip())
                if proc.returncode == 4:
                    continue  # 该解释器没有 physicslab，换下一个
                from client import _log_action as _la
                _la({"action": "post-discussion-delegate", "interp": interp,
                     "exit": proc.returncode})
                return proc.returncode
            _out({"ok": False,
                  "error": "没有可用的 Python3.14+physicslab 解释器，"
                           "请直接运行 tools/experiment_gen.py post-discussion"})
            return 4
        elif args.cmd == "remove-my-post":
            r = client.remove_experiment(args.content_id, args.category)
            result = {"action": "remove-my-post", "status": r.get("Status"),
                      "content_id": args.content_id}
        elif args.cmd == "rename":
            r = client.rename(args.nickname)
            result = {"action": "rename", "status": r.get("Status"),
                      "nickname": args.nickname}
        elif args.cmd == "signature":
            r = client.modify_information("Signature", args.text)
            result = {"action": "signature", "status": r.get("Status")}
        elif args.cmd == "get-messages":
            r = client.get_messages(take=args.take, skip=args.skip)
            _out({"count": len(r), "messages": r})
            return 0
        elif args.cmd == "get-summary":
            r = client.get_summary(args.content_id, args.category)
            _out(r)
            return 0
        elif args.cmd == "get-comments":
            r = client.get_comments(args.content_id, args.category, take=16)
            _out(r)
            return 0
        elif args.cmd == "query":
            r = client.query_experiments(category=args.category,
                                         take=args.take, skip=args.skip,
                                         days=args.days)
            _out(r)
            return 0
        elif args.cmd == "get-user":
            r = client.get_user(name=args.name, user_id=args.user_id)
            _out(r)
            return 0
        elif args.cmd == "get-profile":
            r = client.get_profile(args.user_id)
            _out(r)
            return 0
        else:  # pragma: no cover
            parser.error(f"未知命令 {args.cmd}")

        _log_action(result)
        _out(result)
        return 0
    except PlwebError as e:
        _out({"ok": False, "error": str(e), "code": e.code})
        _log_action({"action": args.cmd, "error": str(e)})
        return e.code


if __name__ == "__main__":
    sys.exit(main())
