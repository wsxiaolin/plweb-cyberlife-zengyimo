# 用户接口详解

用户接口位于 `Users/` 路径下，提供用户资料查询、关注关系管理、个人信息修改、管理员操作等功能。

需要用户身份的接口通过 `x-API-Token` 和 `x-API-AuthCode` 认证；可公开访问的读取操作是否接受匿名会话取决于控制器权限检查。

## 1. 获取用户信息（Users/GetUser）

按用户名或用户 ID 查询用户资料。

### 请求

```http
POST /Users/GetUser
```

**请求体（按用户名查询）：**
```json
{
  "Name": "用户昵称"
}
```

**请求体（按用户 ID 查询）：**
```json
{
  "ID": "5d0f4390ca68215906d1a0fd"
}
```

> 推荐只传一个字段；两者同时传入时控制器最终按 `ID` 查询，`Name` 只在未传 `ID` 时生效。

### 响应

成功时 `Data` 是 `UserPackage`：其中 `User` 是目标用户，`Statistic` 是统计数据，`Relation` 是当前登录者与目标用户的关系枚举；`Backpack`、`Bonuses`、`UserToken`、`TargetLink` 是可空扩展。字段级 JSON 结构和枚举说明见 [`responses.md`](responses.md#5-用户接口返回)。

### 字段说明

| 字段 | 说明 |
|------|------|
| `Data.User` | 用户模型；具体字段取决于权限和接口 |
| `Data.Statistic` | `UserStatistic` 统计及活动数据 |
| `Data.Backpack` | 背包模型或 `null` |
| `Data.Bonuses` | 本次操作奖励或 `null` |
| `Data.Relation` | `RelationType` 数值：0 None、1 Following、2 Followed、3 Friend、4 Blocking、5 Blocked、6 BothBlocked |

## 2. 关注/取关用户（Users/Follow）

关注或取消关注指定用户。

### 请求

```http
POST /Users/Follow
```

**请求体：**
```json
{
  "TargetID": "5d0f4390ca68215906d1a0fd",
  "Action": 1
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `TargetID` | string | 目标用户 ID |
| `Action` | int | `1` 关注，`0` 取消关注 |

### 响应

```json
{
  "Status": 200,
  "Message": "",
  "Data": true
}
```

`Data` 是 `bool`（关系变更是否成功），顶层 `Message` 可能携带关系提示；失败时查 `Status`/`Message`，而不是把 `Data` 解析为关系对象。

## 3. 获取关注/粉丝列表（Users/GetRelations）

获取指定用户的关注列表或粉丝列表。

### 请求

```http
POST /Users/GetRelations
```

**请求体：**
```json
{
  "UserID": "5d0f4390ca68215906d1a0fd",
  "DisplayType": 0,
  "Skip": 0,
  "Take": 20,
  "Query": ""
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `UserID` | string | 目标用户 ID |
| `DisplayType` | int | `0` 粉丝（Followed），`1` 关注（Following）；更多筛选值见源码枚举 |
| `Skip` | int | 跳过条数（分页） |
| `Take` | int | 获取条数（默认 20） |
| `Query` | string | 搜索关键词（可为空字符串） |

### 响应

```json
{
  "Status": 200,
  "Message": "",
  "Data": {
    "$type": "...",
    "$values": [
      { "User": { "ID": "...", "Nickname": "...", "Avatar": 0 }, "Statistic": { "FollowerCount": 0 }, "Relation": 0 }
    ]
  }
}
```

## 4. 修改昵称（Users/Rename）

修改当前登录用户的昵称。

### 请求

```http
POST /Users/Rename
```

**请求体：**
```json
{
  "Target": "新昵称"
}
```

### 响应

成功时 `Data` 为 `UserPackage`，常见字段是更新后的 `User`；无关扩展字段可能为 `null`。

## 5. 修改个人信息（Users/ModifyInformation）

修改当前用户的个人签名等信息。

### 请求

```http
POST /Users/ModifyInformation
```

**请求体：**
```json
{
  "Field": "Signature",
  "Target": "新的个性签名内容"
}
```

成功时 `Data` 是 `UserPackage`，含更新后的 `User`；不适用的扩展字段可能为空。签名字段长度与审核规则由服务端校验。

## 6. 领取活动奖励（Users/ReceiveBonus）

领取指定活动的奖励。

### 请求

```http
POST /Users/ReceiveBonus
```

**请求体：**
```json
{
  "ActivityID": "activity_id_string",
  "Index": 0
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `ActivityID` | string | 活动 ID |
| `Index` | int | 奖励索引 |

## 7. 封禁用户（Users/Ban）— 管理员

封禁指定用户，需要管理员权限。

### 请求

```http
POST /Users/Ban
```

**请求体：**
```json
{
  "TargetID": "5d0f4390ca68215906d1a0fd",
  "Reason": "违规原因",
  "Length": 7
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `TargetID` | string | 被封禁用户 ID |
| `Reason` | string | 封禁原因 |
| `Length` | int | 封禁天数（必须大于 0） |

## 8. 解封用户（Users/Unban）— 管理员

解封指定用户，需要管理员权限。

### 请求

```http
POST /Users/Unban
```

**请求体：**
```json
{
  "TargetID": "5d0f4390ca68215906d1a0fd",
  "Reason": "解封原因"
}
```

## 9. 获取头像图片

获取用户头像或实验封面图片，无需认证。

### 请求

```http
GET https://physics-api-cn.turtlesim.com/Avatars/{category}/{target_id}_{index}_{size_category}.png
```

| 参数 | 说明 |
|------|------|
| `category` | `"users"` 用户头像，`"experiments"` 实验封面 |
| `target_id` | 用户 ID 或实验 ID |
| `index` | 历史图片索引（通常为 0） |
| `size_category` | `"small.round"` 小圆头像，`"thumbnail"` 缩略图，`"full"` 完整图 |

### 示例

```
https://physics-api-cn.turtlesim.com/Avatars/users/5d0f4390ca68215906d1a0fd_0_small.round.png
```

> 由于证书与域名不匹配，获取图片时需关闭 SSL 验证。
