# 消息接口详解

消息接口位于 `Messages/` 路径下，提供当前用户收件箱读取，以及管理员批量发送服务端模板消息。需要认证；批量发送接口另要求管理员权限。

成功响应的真实 `Data` 类型及字段解读见 [`responses.md`](responses.md#7-收件箱返回)。

## 1. 获取站内信列表（Messages/GetMessages）

获取当前用户的站内信列表，支持按分类筛选和分页。

### 请求

```http
POST /Messages/GetMessages
```

**请求体：**
```json
{
  "CategoryID": 0,
  "Skip": 0,
  "Take": 16,
  "NoTemplates": false
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `CategoryID` | int | 消息分类 ID，`0` 表示全部 |
| `Skip` | int | 跳过条数；续页累加实际返回条数，fetch_messages可自动循环 |
| `Take` | int | 获取条数（默认 16） |
| `NoTemplates` | bool | 是否省略Templates对象；不是排除使用模板的消息条目 |

### 响应

```json
{
  "Status": 200,
  "Message": "",
  "Data": {
    "Messages": [
      { "ID": "<message-id>", "CategoryID": 3, "TemplateID": "<template-id>",
        "TargetID": "<target-id>", "Users": ["<sender-id>"], "UserNames": ["发送者"],
        "UserAvatar": 0, "Timestamp": 1720000000000, "TimestampInitial": 1720000000000,
        "Unread": 1720000000123, "Handled": 0, "Fields": {}, "Numbers": {} }
    ],
    "Templates": []
  }
}
```

响应的 `Data` 是 `MessagesPackage`；消息数组在 `Data.Messages`，模板在 `Data.Templates`。当 `Skip != 0` 或 `NoTemplates=true` 时，`Templates` 可能为 `null`。

请求第一页（`Skip=0`）会把当前用户统计中的未读消息/信件计数清零，这是有状态读取操作。

GetMessages负责列出消息及正文模板。确认某条消息已读使用下节的GetMessage，以消息条目的Unread判断该条状态。

### Message 字段说明

| 字段 | 说明 |
|------|------|
| `ID` | 消息唯一 ID |
| `CategoryID` | 消息分类 ID |
| `TemplateID` | 服务端消息模板 ID |
| `TargetID` | 消息目标用户 ID |
| `Users` / `UserNames` | 相关用户 ID 与昵称数组 |
| `Timestamp` / `TimestampInitial` | 毫秒级 Unix 时间戳 |
| `Unread` / `Handled` | long状态标记，不是数量；Unread=0未读，非零为读取时间戳；Handled单独解释 |
| `Fields` / `Numbers` | 模板文本替换用字符串/数值字典，不是已渲染正文 |

## 2. 确认单条消息已读（Messages/GetMessage）

将GetMessages返回的消息条目ID传给MessageID，服务器执行该条消息的已读处理。正文通过GetMessages条目与Templates解读。

### 请求

```http
POST /Messages/GetMessage
```

**请求体：**
```json
{
  "MessageID": "message_id_string"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `MessageID` | string | 必填，取GetMessages中目标消息条目的ID |

### 调用与确认

ChatGPT插件使用write_community调用，因为此接口会更新已读状态。

```json
{"path":"/Messages/GetMessage","body":{"MessageID":"<消息条目的ID>"}}
```

通用版可直接调用已登录的CommunityClient。

```python
result = client.request("/Messages/GetMessage", {"MessageID": message["ID"]})
```

通过CommunityReads.call_batch批量确认时，传入消息ID请求列表并设置write=True。检查业务Status=200，然后按同一消息ID重新读取列表中的条目，确认Unread为非零读取时间戳。Unread=0表示未读。Statistic.UnreadMessages和UnreadLetters表示聚合提示，Handled表示关联事项的处理状态。

### 响应

`Data` 是 `UserPackage`，包含当前 `User`、更新后的 `Statistic`，有时还有领取到的 `Bonuses`；虽然服务端读取并标记了对应消息、信件可能发放奖励，但当前响应包不含该消息对象本身。完整字段参见 [`responses.md`](responses.md#7-收件箱返回)。

## 3. 管理员批量发送模板消息（Messages/SendMessages）

这是管理员使用的批量模板消息接口，不是普通用户的自由文本私信接口。源码要求提供 `TargetID`、`Category`、`SummaryID` 和 `TemplateID`，并且调用者必须是管理员。

### 请求

```http
POST /Messages/SendMessages
```

**请求体：**
```json
{
  "TargetID": ["5d0f4390ca68215906d1a0fd"],
  "Category": "Experiment",
  "SummaryID": [],
  "TemplateID": "<template-id>"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `TargetID` | string[] | 目标用户ID数组，本技能每批合计最多20个 |
| `Category` | string | 关联作品类别；即使不传关联作品仍须提供字段 |
| `SummaryID` | string[] | 可选关联作品 ID 列表；长度需与目标用户数量一致或为空 |
| `TemplateID` | string | 服务端消息模板 ID |

### 响应

```json
{
  "Status": 200,
  "Message": "",
  "Data": null
}
```

### 注意事项

- 该接口只允许管理员调用，且只能发送服务器定义的模板消息；普通用户不能用它发送任意文本私信。

## 批量与副作用

仓库辅助层把GetMessages与GetMessage视作有状态操作，调用通用批量方法时须显式write=True并有相应任务授权；这不改变接口仍为“消息读取”的业务名称。消息列表使用Skip条数分页；完整性以实际返回数量和停止原因为准。

SendMessages每批用户总计最多20个。模板正文的本地渲染规则见 [通知](practical-api.md#7-通知)。`Notifications/Get` 实测会偶发不返回，单次尝试失败即放弃，不要循环重试；靠 GetMessages 覆盖主要通知，更多现场差异见 [实测补充](field-notes.md#5-收件箱messagesgetmessages的正确读法)。
