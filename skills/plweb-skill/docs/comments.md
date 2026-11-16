# 评论接口详解

评论接口由 `Messages` 控制器提供，提供对实验/讨论作品或用户留言板的评论发表、获取、删除功能。需要有效用户会话；发表还要求账号已绑定。

本文的成功响应示例基于当前 `Comment`/`CommentsPackage` 模型；通用数组解包、时间字段和字段字典见 [`responses.md`](responses.md#6-评论返回)。

## 1. 获取评论列表（Messages/GetComments）

获取指定作品的评论列表。

### 请求

```http
POST /Messages/GetComments
```

**请求体：**
```json
{
  "TargetID": "16a627bdb25f77131ba28018",
  "TargetType": "Experiment",
  "Skip": 0,
  "Take": 16
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `TargetID` | string | 目标内容或用户 ID |
| `TargetType` | string | `"Experiment"`、`"Discussion"` 或 `"User"` |
| `Skip` | int | 固定0；条数偏移实测可能返回空页 |
| `CommentID` | string | 首页空字符串，续页为末条评论ID；边界包含，须去重 |
| `Take` | int | 获取条数（默认 16） |

### 响应

`Data` 是评论包对象而不是裸数组，主要字段为 `Count`（总评论数）、`Target`（目标用户或作品摘要）和 `Comments`（本页评论数组）。

```json
{
  "Status": 200,
  "Message": "",
  "Data": {
    "Count": 23,
    "Target": { "ID": "16a627bdb25f77131ba28018", "Category": "Experiment", "Subject": "作品标题" },
    "Comments": [
      {
        "TargetID": "16a627bdb25f77131ba28018",
        "ID": "<comment-id>",
        "UserID": "<user-id>",
        "Nickname": "评论者",
        "Verification": null,
        "Avatar": 0,
        "Content": "评论内容",
        "Language": "Chinese",
        "Timestamp": 1720000000000,
        "Hidden": false,
        "Flags": [],
        "Replies": []
      }
    ]
  }
}
```

### Comment 字段说明

| 字段 | 说明 |
|------|------|
| `TargetID` | 评论所属作品或用户 ID |
| `ID` | 评论唯一 ID |
| `UserID` / `Nickname` | 评论者账号 ID 与昵称 |
| `Content` | 评论正文 |
| `Timestamp` | Unix 毫秒时间戳 |
| `Replies` | 子评论数组，元素是 `CommentContent` |
| `Flags` / `Hidden` | 特殊标记与隐藏状态 |

## 2. 发表评论（Messages/PostComment）

在指定作品或用户留言板下发表评论。

### 请求

```http
POST /Messages/PostComment
```

**请求体：**
```json
{
  "TargetID": "16a627bdb25f77131ba28018",
  "TargetType": "Experiment",
  "Content": "评论内容文本",
  "ReplyID": ""
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `TargetID` | string | 评论所在位置，作品用Summary.ID摘要ID，留言板用所属用户ID |
| `TargetType` | string | `"Experiment"`、`"Discussion"` 或 `"User"` |
| `Content` | string | 评论正文，支持社区富文本 |
| `ReplyID` | string | 被回复用户的ID，取原评论的UserID，与正文中可识别的@完整昵称配合产生回复通知。普通留言填空字符串 |

### 回复指定用户

在已有作品或留言板下回复某位评论者时，沿用所在位置的TargetID和TargetType，将原评论的UserID写入ReplyID，并保留正文中的`回复@完整昵称: `。

```json
{
  "TargetID": "<当前作品的摘要ID>",
  "TargetType": "Discussion",
  "Content": "回复@目标完整昵称: 收到，你提到的问题已经修正。",
  "ReplyID": "<原评论的UserID>"
}
```

| ID | 用途 |
|---|---|
| 原评论.UserID → ReplyID | 指定被回复的用户 |
| 原评论.ID → CommentID | 定位、分页或删除评论 |
| 作品Summary.ID或留言板用户ID → TargetID | 指定评论所在位置 |

CommunityClient.request和ChatGPT插件write_community会按ReplyID读取当前昵称、核对昵称定位的用户ID，并自动补齐正文中的@完整昵称。已有完整@引用时沿用原正文。CommunityReads.call_batch(write=True)复用相同流程。直接发送HTTP请求时，按上例同时填写ReplyID与正文@引用。

| 提交内容 | 通知效果 |
|---|---|
| ReplyID加可识别的正文@昵称 | 产生回复通知 |
| ReplyID为空，正文有可识别的@昵称 | 产生提及通知 |
| 仅填写ReplyID，正文为普通文字 | 评论会发布，回复通知未触发 |
| 仅写user富文本标签 | 用于显示和跳转用户 |

服务器会解析正文中的@昵称，昵称中的标点可能导致截断或同名误匹配。辅助层在发布前核对目标，无法安全定位时返回具体错误。成功后保留评论ID并在原位置读回正文。需要核实通知时，从收件账号GetMessages中查找Fields.CommentID等于本条评论ID的条目，区分回复与提及模板。

### 响应

```json
{
  "Status": 200,
  "Message": "",
  "Data": {
    "TargetID": "16a627bdb25f77131ba28018",
    "ID": "<new-comment-id>",
    "UserID": "<current-user-id>",
    "Nickname": "评论者",
    "Avatar": 0,
    "Content": "评论内容文本",
    "Language": "Chinese",
    "Timestamp": 1720000000000,
    "Hidden": false,
    "Replies": [],
    "Flags": []
  }
}
```

`Data` 是新建评论本身（`Comment`），不是带 `Author`、`Floor` 的对象。字段说明见本页的评论列表结构。

### 注意事项

- 评论内容不能为空
- 评论内容有长度限制
- 匿名用户无法发表评论
- 被作者拉黑后可能无法评论

## 3. 删除评论（Messages/RemoveComment）

删除指定评论。仅评论作者或内容作者或管理员可删除。

### 请求

```http
POST /Messages/RemoveComment
```

**请求体：**
```json
{
  "TargetType": "Experiment",
  "CommentID": "comment_id_string"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `TargetType` | string | `"Experiment"`、`"Discussion"` 或 `"User"` |
| `CommentID` | string | 要删除的评论 ID |

### 响应

```json
{
  "Status": 200,
  "Message": "",
  "Data": null
}
```

### 权限说明

- 评论作者可以删除自己的评论
- 内容（实验/讨论）作者可以删除其作品下的任何评论
- 管理员可以删除任何评论
- 无权限删除会返回 `Permission.Denied` 错误

## 自动分页、回复与警告

指定条数或多个目标使用 [fetch_comments](operations.md)，每批所有目标合计最多1000条。返回数组可能有$values包装。续页不能仅依Count判断完成。

原有发表评论/删除能力保留；PostComment还支持ReplyID（被回复的用户ID，非评论ID）、Language、Special及社区用户引用。管理警告仅在权限和目标类型正确时生效，字段与副作用见 [评论与警告](practical-api.md#6-评论回复-与警告)。
