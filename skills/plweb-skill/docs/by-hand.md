# 没有现成方法时：按文档自行调用接口

本技能只是社区 HTTP 接口的封装。封装的方法覆盖常用路径，但不可能覆盖全部；**遇到没有现成方法/子命令的操作，不要停在这里回"做不到"，直接按文档发请求即可**。换头像、改签名、签到、隐藏作品这类单个写操作，自己用 shell 或 Python 调接口通常比等工具更快。

## 1. 先判断走哪条路

| 情况 | 做法 |
|---|---|
| 有随附方法或 CLI 子命令 | 用现成的（`CommunityClient`、`CommunityReads`、`CommunityActions`、`community_cli.py`、`login_gui.py`） |
| 没有方法，是单个读写操作 | 按本页自行调用：头像、签名、签到、点赞、隐藏、留言板评论等 |
| 发布实验、封面、批量分页 | 回到随附方法：需要完整模型、图片校验与分页上限，不适合手写 |

自行调用时**不要臆造路径和字段**。`405`/`404` 表示路径不存在，`Input.Field.Missing` 表示字段名写错或缺失——都是"猜错了"的信号，回去查 [接口字段速查](interface-notes.md) 与 [完整业务参数](practical-api.md)，不要顺着错误换写法反复试。

## 2. 请求骨架

基址：中国区 `https://physics-api-cn.turtlesim.com`，国际区 `https://physics-api-us.turtlesim.com`。

认证头（来自已建立的会话，不要手工把密码粘到命令行）：

```http
Content-Type: application/json
Accept-Encoding: gzip
x-API-Token: <Token>
x-API-AuthCode: <AuthCode>
x-API-Version: <版本，如 2503>
```

推荐用随附客户端发请求，凭据留在程序内部，自动处理会话、限流间隔与凭据脱敏。会话按账号保存在本机，`python scripts/community_cli.py accounts` 列出用户 ID；首次使用先跑 `python scripts/login_gui.py`：

```python
from community_client import CommunityClient

api = CommunityClient.from_saved('<已登录的用户ID>')   # 载入该账号的加密会话
user = api.request('/Users/GetUser', {'ID': api._session['account_id']})['Data']['User']
```

裸调用 `CommunityClient()` 不会自动带会话，只适合匿名读取公开数据。

没有 Python 环境时也可以用 `curl`，凭据从环境变量读取，**不要写进命令历史、日志或仓库**：

```bash
curl -sS "https://physics-api-cn.turtlesim.com/Users/GetUser" \
  -H "Content-Type: application/json" \
  -H "x-API-Token: $PL_TOKEN" -H "x-API-AuthCode: $PL_AUTHCODE" \
  -H "x-API-Version: 2503" \
  -d "{\"ID\":\"$PL_USER_ID\"}"
```

## 3. 例一：换头像（完整链路）

头像不是"发一张图"就完事，服务端要求先申请序号、上传、校验、再确认序号。完整顺序见 [图片上传](uploads.md)，自己实现时照这个骨架：

```python
import hashlib
from pathlib import Path

from community_actions import upload_image, verify_image, image_file, MAX_AVATAR_BYTES
from community_client import CommunityClient

api = CommunityClient.from_saved('<已登录的用户ID>')
uid = api._session['account_id']

data = image_file('new-avatar.png', MAX_AVATAR_BYTES)   # 1MiB 上限，顺带校验格式完整
before = api.request('/Users/GetUser', {'ID': uid})['Data']['User']
index = int(before.get('Avatar') or 0) + 1              # 序号必须递增

# 1) 申请上传凭据：FileSize 传负的实际字节数
token = api.request('/Users/RequestAvatar',
                    {'Request': {'FileSize': -len(data), 'Extension': '.jpg'}})['Data']

# 2) 上传到凭据给出的存储目标
receipt = upload_image(data, token)

# 3) 校验存储上的图片真的可访问、完整、不是空白图
check = verify_image(receipt['path'])
assert check['verified'], check

# 4) 校验通过才确认序号
api.request('/Users/ConfirmAvatar', {'Avatar': index})

# 5) 读回：Avatar 等于新序号才算成功
after = api.request('/Users/GetUser', {'ID': uid})['Data']['User']
print({'updated': after.get('Avatar') == index, 'avatar': after.get('Avatar'),
       'previous': before.get('Avatar'), 'sha256': hashlib.sha256(data).hexdigest()})
```

要点：

- 序号用 `当前 Avatar + 1`，不要复用旧序号，也不要倒退。
- 头像上限 **1MiB**、封面 **8MiB**，超限在发送前拒绝；尺寸和字节数是两件事。
- 上传成功后按凭据拼出静态地址再 GET 一次，确认 HTTP 200 且内容确为图片；空白/纯色图默认不允许。
- 确认序号后**一定重新 `GetUser` 读回**，序号一致才说"换了"。只确认不读回，等于没验证。
- 不想自己拼 Multipart 就用 `CommunityActions.set_avatar(path)`，它就是上面这串操作的封装。

## 4. 例二：在留言板发评论（触发对方通知）

```python
api.request('/Messages/PostComment', {
    'TargetID': other_user_id,        # 留言板就是对方用户 ID
    'TargetType': 'User',
    'Language': 'Chinese',
    'ReplyID': '',                    # 回复某条评论时填原评论的 UserID
    'Content': '你好，看到你的电路作品了',
    'Special': '',
})
```

要通知某个人，正文必须带内联标记，纯文本不会通知：

```text
回复<user=对方ID>@对方完整昵称: 正文
```

## 5. 例三：签到领金币

```python
sync = api.request('/Users/SyncActivities', {})['Data']
attendance = next(a for a in sync['Activities'] if a.get('InterfaceModel') == 'Attendance')
avails = attendance.get('Avails') or []
if avails:
    api.request('/Users/ReceiveBonus', {
        'ActivityID': attendance['ID'],
        'Index': avails[-1],
        'Statistic': sync['Statistic'],   # 原样回传
    })
```

当天已领会返回 `403 Activity.Bonus.Received`，这是正常状态，不是故障。

## 6. 自行调用时必须守住的规则

- **节奏**：请求间隔约 0.35 秒，最多两个并发；不要为提速开多进程。
- **不自动重试**：超时或 `403` 先核对已有结果；写操作尤其不能盲目重放，避免重复发布或重复扣币。
- **验证**：每个写操作后面都要有一次读回，把"接口返回 200"和"事情真的发生了"分开说。
- **凭据**：Token/AuthCode 只从会话读取，不打印、不写入文件、不随答案返回、不提交到仓库；不向图片存储主机或任何无关主机转发认证头。
- **区分错误**：`405/404` 路径不存在、`Input.Field.Missing` 字段问题、`User.Not.Allowed` 权限或临时限流、`Activity.Bonus.Received` 今日已领。按类别处理，不要把一种错误换成另一种写法硬试。
- **越界就停**：涉及批量、越权、绕过限流、修改他人账号的操作，一律停下来问用户，而不是自己找捷径。

更多现场行为的坑见 [实测补充](field-notes.md)。
