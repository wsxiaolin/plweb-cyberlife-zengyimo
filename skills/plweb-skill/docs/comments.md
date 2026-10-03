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
| `Skip` | int | 跳过条数（分页偏移） |
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
  "Content": "评论内容文本"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `TargetID` | string | 目标内容或用户 ID |
| `TargetType` | string | `"Experiment"`、`"Discussion"` 或 `"User"` |
| `Content` | string | 评论内容（纯文本） |

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

## 4. 已移除的旧路径

`Contents/GetDiscussionComments` 不存在于当前服务端控制器中。讨论作品评论使用 `Messages/GetComments`，请求的 `TargetType` 设为 `Discussion`，其响应与本页的评论包相同。
