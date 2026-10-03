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
  "NoTemplates": true
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `CategoryID` | int | 消息分类 ID，`0` 表示全部 |
| `Skip` | int | 跳过条数（分页偏移） |
| `Take` | int | 获取条数（默认 16） |
| `NoTemplates` | bool | 是否排除模板消息（系统通知模板） |

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
        "Unread": 1, "Handled": 0, "Fields": {}, "Numbers": {} }
    ],
    "Templates": []
  }
}
```

响应的 `Data` 是 `MessagesPackage`；消息数组在 `Data.Messages`，模板在 `Data.Templates`。当 `Skip != 0` 或 `NoTemplates=true` 时，`Templates` 可能为 `null`。

请求第一页（`Skip=0`）会把当前用户统计中的未读消息/信件计数清零，这是有状态读取操作。

### Message 字段说明

| 字段 | 说明 |
|------|------|
| `ID` | 消息唯一 ID |
| `CategoryID` | 消息分类 ID |
| `TemplateID` | 服务端消息模板 ID |
| `TargetID` | 消息目标用户 ID |
| `Users` / `UserNames` | 相关用户 ID 与昵称数组 |
| `CategoryID` | 消息类别枚举，0 至 5 |
| `Timestamp` / `TimestampInitial` | 毫秒级 Unix 时间戳 |
| `Unread` / `Handled` | 未读数量/邀请处理状态数值 |
| `Fields` / `Numbers` | 模板文本替换用字符串/数值字典，不是已渲染正文 |

## 2. 获取单条站内信（Messages/GetMessage）

获取指定 ID 的单条站内信详情。

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
| `MessageID` | string | 消息 ID |

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
| `TargetID` | string[] | 目标用户 ID，1 至 50 个 |
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
