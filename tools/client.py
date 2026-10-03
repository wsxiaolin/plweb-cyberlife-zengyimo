"""plweb 社区 API 客户端 —— 赛博生命的"手"。

确定性工具层：无 LLM 依赖，Python >= 3.9。
职责：
  - 登录（Token 优先 -> 邮箱兜底，失败自动重试，多层回退）
  - 封装社区常用 API（浏览/评论/私信/点赞/关注/资料）
  - 请求重试 + 退避 + 人味限速 + 动作日志
凭据来源（优先级）：PLWEB_TOKEN/PLWEB_AUTHCODE 环境变量
                 > PLWEB_EMAIL/PLWEB_PASSWORD 环境变量
                 > tmp/session.json（同一唤醒周期内复用）
"""

from __future__ import annotations

import json
import os
import random
import ssl
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Optional

BASE_URL = "https://physics-api-cn.turtlesim.com"
DEVICE_ID = "7db01528cf13e2199e141c402d79190e"  # 文档推荐固定设备标识
CLIENT_VERSION = 2411  # 登录协议版本（YYMM）
REQUEST_TIMEOUT = 30
RETRY_BACKOFF = [3, 8, 20]  # 秒
MIN_INTERVAL = 1.2  # 相邻请求最小间隔（秒），叠加随机抖动
ROOT = Path(__file__).resolve().parent.parent
TMP = ROOT / "tmp"
SESSION_FILE = TMP / "session.json"
ACTION_LOG = TMP / "actions.log"

_SSL_CTX = ssl._create_unverified_context()  # 文档注明：域名与证书不匹配，需关验证


class PlwebError(Exception):
    """社区 API 错误。code: 2=登录失败 3=接口失败 4=权限/封禁"""

    def __init__(self, message: str, code: int = 3, status: Optional[int] = None):
        super().__init__(message)
        self.code = code
        self.status = status


def _log_action(entry: dict) -> None:
    TMP.mkdir(parents=True, exist_ok=True)
    entry["ts"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    with ACTION_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


class PlwebClient:
    """物理实验室 AR 社区客户端。"""

    def __init__(self, log_actions: bool = True):
        self.token: Optional[str] = None
        self.auth_code: Optional[str] = None
        self.user_id: Optional[str] = None
        self.nickname: Optional[str] = None
        self._last_request_ts = 0.0
        self.log_actions = log_actions

    # ---------- 底层请求 ----------

    def _post(self, path: str, body: dict, _relogin: bool = True,
              max_retries: Optional[int] = None,
              timeout: int = REQUEST_TIMEOUT,
              extra_headers: Optional[dict] = None) -> dict:
        url = f"{BASE_URL}/{path}"
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if extra_headers:
            headers.update(extra_headers)
        if self.token:
            headers["x-API-Token"] = self.token
        if self.auth_code:
            headers["x-API-AuthCode"] = self.auth_code
        self._throttle()
        schedule = RETRY_BACKOFF + [0]
        if max_retries is not None:
            schedule = schedule[: max_retries + 1]
        last_err: Optional[PlwebError] = None
        for attempt, backoff in enumerate(schedule):
            try:
                req = urllib.request.Request(url, data=data, headers=headers, method="POST")
                with urllib.request.urlopen(req, timeout=timeout, context=_SSL_CTX) as resp:
                    payload = json.loads(resp.read().decode("utf-8"))
                status = payload.get("Status")
                message = payload.get("Message", "")
                if status == 200:
                    return payload
                # 401/403 统一视为会话失效，尝试重登录一次
                if status in (401, 403) and _relogin and path != "Users/Authenticate":
                    if "Login" in message or "Permission" in message:
                        saved = self._relogin()
                        if saved:
                            return self._post(path, body, _relogin=False)
                raise PlwebError(f"{path} -> {status} {message}", code=3, status=status)
            except urllib.error.HTTPError as e:
                last_err = PlwebError(f"{path} HTTP {e.code}", code=3, status=e.code)
            except urllib.error.URLError as e:
                last_err = PlwebError(f"{path} 网络错误: {e.reason}", code=3)
            except json.JSONDecodeError:
                last_err = PlwebError(f"{path} 响应非 JSON", code=3)
            except PlwebError as e:
                last_err = e
            if backoff:
                time.sleep(backoff + random.uniform(0, 1.5))
                time.sleep(backoff + random.uniform(0, 1.5))
        raise last_err or PlwebError(f"{path} 未知失败", code=3)

    def _throttle(self) -> None:
        wait = MIN_INTERVAL + random.uniform(0, 0.8)
        since = time.time() - self._last_request_ts
        if since < wait:
            time.sleep(wait - since)
        self._last_request_ts = time.time()

    # ---------- 登录与会话 ----------

    def authenticate(
        self,
        login: Optional[str],
        password: Optional[str],
        token: Optional[str] = None,
        auth_code: Optional[str] = None,
    ) -> dict:
        """邮箱或 Token 登录。成功后填充会话并持久化到 tmp/session.json。"""
        body: dict[str, Any] = {
            "Login": login,
            "Password": password,
            "Version": CLIENT_VERSION,
            "Device": {"Identifier": DEVICE_ID, "Language": "Chinese"},
        }
        if token and auth_code:
            # Token 免密续期：走请求头
            self.token, self.auth_code = token, auth_code
            payload = self._post("Users/Authenticate", body, _relogin=False)
        else:
            self.token = self.auth_code = None
            payload = self._post("Users/Authenticate", body, _relogin=False)
        status = payload.get("Status")
        if status != 200:
            raise PlwebError(f"登录失败: {payload.get('Message')}", code=2, status=status)
        self.token = payload.get("Token") or self.token
        self.auth_code = payload.get("AuthCode") or self.auth_code
        user = (payload.get("Data") or {}).get("User") or {}
        self.user_id = user.get("ID")
        self.nickname = user.get("Nickname")
        self._save_session()
        return payload

    def _relogin(self) -> bool:
        """会话失效后的回退：Token 续期 -> 邮箱重登。"""
        try:
            email = os.environ.get("PLWEB_EMAIL")
            password = os.environ.get("PLWEB_PASSWORD")
            if email and password:
                self.authenticate(email, password)
            else:
                self.authenticate(None, None, self.token, self.auth_code)
            return True
        except PlwebError:
            return False

    def _save_session(self) -> None:
        TMP.mkdir(parents=True, exist_ok=True)
        SESSION_FILE.write_text(
            json.dumps(
                {
                    "token": self.token,
                    "auth_code": self.auth_code,
                    "user_id": self.user_id,
                    "nickname": self.nickname,
                    "saved_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    @classmethod
    def from_env(cls, log_actions: bool = True) -> "PlwebClient":
        """按凭据优先级建立会话：环境变量 Token > 环境变量邮箱 > 本地 session.json。"""
        client = cls(log_actions=log_actions)
        token = os.environ.get("PLWEB_TOKEN")
        auth_code = os.environ.get("PLWEB_AUTHCODE")
        email = os.environ.get("PLWEB_EMAIL")
        password = os.environ.get("PLWEB_PASSWORD")
        if token and auth_code:
            try:
                client.authenticate(None, None, token, auth_code)
                return client
            except PlwebError:
                pass  # Token 失效，回退邮箱
        if email and password:
            client.authenticate(email, password)
            return client
        if SESSION_FILE.exists():
            saved = json.loads(SESSION_FILE.read_text(encoding="utf-8"))
            try:
                client.authenticate(None, None, saved.get("token"), saved.get("auth_code"))
                return client
            except PlwebError:
                pass
        raise PlwebError(
            "无法建立会话：请设置 PLWEB_EMAIL/PLWEB_PASSWORD（或 PLWEB_TOKEN/PLWEB_AUTHCODE）",
            code=2,
        )

    # ---------- 浏览类 ----------

    def query_experiments(
        self,
        category: str = "Experiment",
        take: int = 16,
        skip: int = 0,
        sort: int = 0,
        days: int = 0,
    ) -> list[dict]:
        """列表查询。注意：服务端对 Take>16 会挂起，此处强制 <=16，翻页用 skip。"""
        take = max(1, min(take, 16))

        payload = self._post(
            "Contents/QueryExperiments",
            {
                "Query": {
                    "Category": category,
                    "Languages": [],
                    "ExcludeLanguages": [],
                    "Tags": None,
                    "ExcludeTags": None,
                    "ModelTags": None,
                    "ModelID": None,
                    "ParentID": None,
                    "UserID": None,
                    "Special": None,
                    "From": None,
                    "Skip": skip,
                    "Take": take,
                    "Days": days,
                    "Sort": sort,
                    "ShowAnnouncement": False,
                }
            },
        )
        return ((payload.get("Data") or {}).get("$values")) or []

    def get_summary(self, content_id: str, category: str = "Experiment") -> dict:
        """作品详情（标题/描述/数据）。content_id 用列表里的 ID 字段。"""
        payload = self._post(
            "Contents/GetSummary", {"ContentID": content_id, "Category": category}
        )
        return payload.get("Data") or {}

    def get_experiment(self, workspace_id: str) -> dict:
        """实验工作区数据（序列化电路/天体模型）。workspace_id 用列表里的 ContentID 字段。"""
        payload = self._post(
            "Contents/GetExperiment", {"ContentID": workspace_id, "Category": "Experiment"}
        )
        return payload.get("Data") or {}

    def get_comments(self, target_id: str, target_type: str = "Experiment",
                     take: int = 16, skip: int = 0) -> list[dict]:
        """评论列表。target_type: Experiment / Discussion / User。target_id 用作品的 ID 字段。"""
        payload = self._post(
            "Messages/GetComments",
            {
                "TargetID": target_id,
                "TargetType": target_type,
                "CommentID": None,
                "Take": take,
                "Skip": skip,
            },
        )
        return ((payload.get("Data") or {}).get("$values")) or []

    def get_user(self, name: Optional[str] = None, user_id: Optional[str] = None) -> dict:
        body = {"Name": name} if name else {"ID": user_id}
        payload = self._post("Users/GetUser", body)
        return (payload.get("Data") or {}).get("User") or {}

    def get_profile(self, user_id: str) -> dict:
        payload = self._post("Contents/GetProfile", {"ID": user_id})
        return payload.get("Data") or {}

    def get_messages(self, take: int = 16, skip: int = 0,
                     category_id: int = 0, no_templates: bool = True) -> list[dict]:
        payload = self._post(
            "Messages/GetMessages",
            {"CategoryID": category_id, "Skip": skip, "Take": take,
             "NoTemplates": no_templates},
        )
        return ((payload.get("Data") or {}).get("$values")) or []

    def get_message(self, message_id: str) -> dict:
        payload = self._post("Messages/GetMessage", {"ID": message_id})
        return payload.get("Data") or {}

    def get_notifications(self, take: int = 10, skip: int = 0) -> list[dict]:
        """系统通知。注：该端点偶发挂起，只做 1 次快速尝试，失败即返回空。"""
        try:
            payload = self._post("Notifications/Get", {"Skip": skip, "Take": take},
                                 max_retries=0, timeout=12)
            return ((payload.get("Data") or {}).get("$values")) or []
        except PlwebError:
            return []

    def get_relations(self, user_id: Optional[str] = None, display_type: str = "Following",
                      skip: int = 0, take: int = 16) -> dict:
        """关注/粉丝列表。display_type: 'Following' 或 'Follower'。"""
        body = {
            "UserID": user_id or self.user_id,
            "DisplayType": 1 if display_type == "Following" else 0,
            "Skip": skip,
            "Take": max(1, min(take, 16)),
            "Query": None,
        }
        return self._post("Users/GetRelations", body)

    def get_library(self, identifier: str = "Discussions") -> dict:
        payload = self._post(
            "Contents/GetLibrary", {"Identifier": identifier, "Language": "Chinese"}
        )
        return payload.get("Data") or {}

    # ---------- 互动类（写操作，自动记动作日志） ----------

    def post_comment(self, content_id: str, category: str, text: str,
                     reply_to: Optional[str] = None) -> dict:
        """发评论。走 Messages/PostComment（Contents/PostComment 会使服务端挂起）。
        content_id：作品列表的 ID 字段（summary ID）；reply_to：被回复的评论 ID（可选）。"""
        payload = self._post(
            "Messages/PostComment",
            {
                "TargetID": content_id,
                "TargetType": category,
                "Language": "Chinese",
                "ReplyID": reply_to,
                "Content": text,
                "Special": None,
            },
        )
        if self.log_actions:
            _log_action({"action": "comment", "content_id": content_id,
                         "category": category, "text": text})
        return payload

    def remove_comment(self, comment_id: str, category: str) -> dict:
        payload = self._post(
            "Messages/RemoveComment",
            {"TargetType": category, "CommentID": comment_id},
        )
        if self.log_actions:
            _log_action({"action": "remove_comment", "comment_id": comment_id})
        return payload

    def star(self, content_id: str, category: str, action: int = 1) -> dict:
        """点赞。action: 1 点赞 0 取消。优先 Contents/Star，失败回退 Contents/StarContent。"""
        try:
            payload = self._post(
                "Contents/Star",
                {"ContentID": content_id, "Category": category, "Action": action},
            )
        except PlwebError:
            payload = self._post(
                "Contents/StarContent",
                {"ContentID": content_id, "Category": category, "Action": action},
            )
        if self.log_actions:
            _log_action({"action": "star", "content_id": content_id,
                         "category": category, "on": bool(action)})
        return payload

    def follow(self, target_id: str, action: bool = True) -> dict:
        payload = self._post("Users/Follow", {"TargetID": target_id, "Action": action})
        if self.log_actions:
            _log_action({"action": "follow", "target_id": target_id, "on": action})
        return payload

    def send_message(self, receiver_id: str, content: str) -> dict:
        payload = self._post(
            "Messages/SendMessage", {"ReceiverID": receiver_id, "Content": content}
        )
        if self.log_actions:
            _log_action({"action": "private_message", "receiver_id": receiver_id,
                         "text": content})
        return payload

    def rename(self, nickname: str) -> dict:
        payload = self._post("Users/Rename", {"Target": nickname})
        if self.log_actions:
            _log_action({"action": "rename", "nickname": nickname})
        return payload

    def modify_information(self, field: str, target: str) -> dict:
        """修改资料。field 如 'Signature'（空值会被服务器拒绝，用单个空格）。"""
        if not target:
            target = " "
        payload = self._post(
            "Users/ModifyInformation", {"Field": field, "Target": target}
        )
        if self.log_actions:
            _log_action({"action": "modify_information", "field": field})
        return payload

    def remove_experiment(self, summary_id: str, category: str,
                          reason: str = "清理") -> dict:
        """删除/隐藏自己的作品。实测：必须带 Hiding/Reason 且带 x-API-Version 头。"""
        payload = self._post(
            "Contents/RemoveExperiment",
            {
                "SummaryID": summary_id,
                "Category": category,
                "Hiding": True,
                "Reason": reason,
            },
            extra_headers={"x-API-Version": "2503"},
        )
        if self.log_actions:
            _log_action({"action": "remove_experiment", "content_id": summary_id})
        return payload

    # ---------- 发布类（实验/讨论帖底层通道） ----------

    def me(self) -> dict:
        """当前登录用户的公开资料（发布时填充 Summary.User 用）。"""
        if not self.user_id:
            return {}
        payload = self._post("Users/GetUser", {"ID": self.user_id})
        return (payload.get("Data") or {}).get("User") or {}

    def post_raw(self, path: str, raw_body: bytes,
                 extra_headers: Optional[dict] = None) -> dict:
        """提交原始（可 gzip 的）请求体，用于 SubmitExperiment 这类特殊通道。"""
        url = f"{BASE_URL}/{path}"
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["x-API-Token"] = self.token
        if self.auth_code:
            headers["x-API-AuthCode"] = self.auth_code
        if extra_headers:
            headers.update(extra_headers)
        self._throttle()
        last_err: Optional[PlwebError] = None
        for attempt, backoff in enumerate(RETRY_BACKOFF + [0]):
            try:
                req = urllib.request.Request(url, data=raw_body, headers=headers,
                                             method="POST")
                with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT,
                                            context=_SSL_CTX) as resp:
                    return json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                last_err = PlwebError(f"{path} HTTP {e.code}", code=3, status=e.code)
            except urllib.error.URLError as e:
                last_err = PlwebError(f"{path} 网络错误: {e.reason}", code=3)
            except json.JSONDecodeError:
                last_err = PlwebError(f"{path} 响应非 JSON", code=3)
            if backoff:
                time.sleep(backoff + random.uniform(0, 1.5))
        raise last_err or PlwebError(f"{path} 未知失败", code=3)

    def confirm_experiment(self, summary_id: str, category: str,
                           image_counter: int, extension: str = ".jpg") -> dict:
        """确认发布（SubmitExperiment 成功后调用）。"""
        payload = self._post(
            "Contents/ConfirmExperiment",
            {
                "SummaryID": summary_id,
                "Category": category,
                "Image": image_counter,
                "Extension": extension,
            },
        )
        return payload


def brief(item: dict, max_len: int = 60) -> str:
    """把作品/评论条目压成一行摘要（写日志/控制台用）。"""
    subject = item.get("Subject") or item.get("Title") or ""
    nickname = ((item.get("User") or {}).get("Nickname")) or (
        (item.get("Author") or {}).get("Nickname")
    ) or ""
    desc = item.get("Description")
    if isinstance(desc, list):
        desc = " ".join(str(x) for x in desc if x)
    text = (item.get("Content") or desc or "") if isinstance(
        item.get("Content") or desc, str) else ""
    return f"[{item.get('ID')}] {subject} @{nickname} :: {text[:max_len]}"
