# 快速入门：读取 Physics Lab 社区数据

本例使用 Python 3 和 `requests`，演示匿名/账号登录、响应检查和分页查询。端点来自父目录 `physics-lab-turtle-services` 的 `UserController`、`ContentController` 和 `ExperimentQuery`。服务端可能继续演进，遇到字段校验错误时先对照这些源码，不要盲目重试。

## 1. 准备

```powershell
py -m pip install requests
$env:PL_API_DOMAIN = 'physics-api-cn.turtlesim.com'
$env:PL_API_VERSION = '2609' # 改成实际客户端版本
# 可选：账号登录。通过系统凭据库/秘密管理器注入 PL_EMAIL、PL_PASSWORD，别在终端命令或脚本里粘贴真实密码。
$env:PL_EMAIL = 'user@example.com'
```

中国区使用 `physics-api-cn.turtlesim.com`，国际区使用 `physics-api-us.turtlesim.com`。TLS 证书验证默认开启；不要设置 `verify=False`。

## 2. 登录并分页查找作品

保存为 `pl_read.py` 后运行 `py pl_read.py`：

```python
import os
import requests


domain = os.environ.get("PL_API_DOMAIN", "physics-api-cn.turtlesim.com")
base = f"https://{domain}"
version = int(os.environ.get("PL_API_VERSION", "2609"))
session = requests.Session()
session.headers.update({"Content-Type": "application/json"})


def check(response):
    response.raise_for_status()  # 传输层错误（TLS、DNS、HTTP 4xx/5xx）
    payload = response.json()
    if payload.get("Status") != 200:
        raise RuntimeError(
            f"API failed: Status={payload.get('Status')} "
            f"Message={payload.get('Message')}"
        )
    # 服务端可在响应头续发认证字段，收到时更新本地会话。
    for header, key in (("x-API-Token", "x-API-Token"),
                        ("x-API-AuthCode", "x-API-AuthCode")):
        value = response.headers.get(header)
        if value:
            session.headers[key] = value
    return payload


login = {
    "Login": os.environ.get("PL_EMAIL") or None,
    "Password": os.environ.get("PL_PASSWORD") or None,
    "Version": version,
    "Device": {
        "Identifier": "replace-with-a-stable-device-id",
        "Language": "Chinese",
    },
}
auth = check(session.post(f"{base}/Users/Authenticate", json=login, timeout=30))

# Token/AuthCode 在响应顶层。匿名登录可能没有 Token；公开读取可以先试。
if auth.get("Token"):
    session.headers["x-API-Token"] = auth["Token"]
if auth.get("AuthCode"):
    session.headers["x-API-AuthCode"] = auth["AuthCode"]


def as_items(data):
    """兼容 Newtonsoft 的 $values 包装和直接数组。"""
    if isinstance(data, dict) and "$values" in data:
        return data["$values"]
    if isinstance(data, list):
        return data
    return []


skip = 0
take = 20
while True:
    query = {
        "Category": "Experiment",
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
        "Days": 0,
        "Sort": 0,
        "ShowAnnouncement": False,
    }
    result = check(session.post(
        f"{base}/Contents/QueryExperiments",
        json={"Query": query},
        timeout=30,
    ))
    rows = as_items(result.get("Data"))
    for row in rows:
        print(row.get("ID"), row.get("Subject"), (row.get("User") or {}).get("Nickname"))
    if len(rows) < take:
        break
    skip += len(rows)
```

匿名登录的实际行为受设备字段和服务端策略影响。需要账号权限时设置 `PL_EMAIL`、`PL_PASSWORD`，并确保调用者已授权使用该账号。不要输出整个登录响应，因为它包含凭据 Token。

## 3. 读取单个作品

`QueryExperiments` 的每个摘要有两个容易混淆的 ID：`ID` 是社区作品摘要 ID；`ContentID` 是关联的实验保存 ID。`GetSummary` 请求体的字段虽然也叫 `ContentID`，这里应传摘要的 `ID` 并同时传 `Category`；`GetExperiment` 的 `ContentID` 则传摘要对象中的保存 ID。

```python
payload = check(session.post(
    f"{base}/Contents/GetSummary",
    json={"Category": "Experiment", "ContentID": "<summary-ID>"},
    timeout=30,
))
print(payload["Data"])

payload = check(session.post(
    f"{base}/Contents/GetExperiment",
    json={"ContentID": "<summary.ContentID-save-ID>"},
    timeout=30,
))
experiment_data = payload["Data"]
```

完整实验保存结构可能很大；响应 `Data` 字段说明见 [`responses.md`](responses.md#43-完整保存-contentsgetexperiment)。读取失败时先核对 ID 类型、作品可见性和当前区域。对不可见或不存在的 ID，不要通过重复请求猜测其他对象。

## 4. 认证与失败排查

- `Status` 非 200：按 `Message` 分支处理；`Login.Password.Invalid` 检查账号密码，`Login.Expired` 重新登录，`Permission.Denied`/`User.Not.Allowed` 检查权限。
- `Input.Field.Missing` 或字段校验错误：检查 JSON 嵌套层级与必填字段。`QueryExperiments` 的查询对象放在外层 `Query` 属性中。
- HTTP/TLS 错误：检查区域域名、网络和系统证书。保持 TLS 验证，不用 `-k` 或 `verify=False`。
- 遇到限流或临时错误：停止密集请求，退避后重试；写操作不要自动重放，避免重复发布/评论。
- 列表可能是数组，也可能是 `{ "$type": ..., "$values": [...] }`；解析时兼容两种形状。

## 5. 常用真实路由

以当前父目录源码为准：`Users/Authenticate`、`Users/GetUser`、`Users/GetRelations`、`Contents/QueryExperiments`、`Contents/GetSummary`、`Contents/GetExperiment`、`Contents/GetDerivatives`、`Contents/StarContent`、`Contents/SubmitExperiment`、`Contents/RemoveExperiment`、`Messages/GetComments`、`Messages/PostComment`、`Messages/RemoveComment`、`Messages/GetMessages`、`Messages/GetMessage`、`Messages/SendMessages`。写接口的请求体和副作用应先阅读对应控制器实现及本 skill 的专题文档。
