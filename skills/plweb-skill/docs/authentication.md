# 登录认证详解

物理实验室 AR API 提供三种登录方式，均通过 `Users/Authenticate` 接口完成。

## 接口地址

```
POST https://physics-api-cn.turtlesim.com/Users/Authenticate
Content-Type: application/json
```

外层返回结构以及登录 `Data` 中 `User`、`Statistic`、`Backpack`、`Library` 等字段说明见 [`responses.md`](responses.md#3-登录-usersauthenticate)。

## 1. 邮箱登录

使用注册邮箱和密码登录，是最常用的登录方式。

### 请求体

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `Login` | string | 是 | 用户注册邮箱 |
| `Password` | string | 是 | 用户密码 |
| `Version` | int | 是 | 客户端版本号，格式 `YYMM`，如 `2411` |
| `Device.Identifier` | string | 是 | 设备标识符，可使用固定值 `7db01528cf13e2199e141c402d79190e` |
| `Device.Language` | string | 是 | 设备语言，`"Chinese"` 或 `"English"` |

### 请求示例

```json
{
  "Login": "user@example.com",
  "Password": "mypassword",
  "Version": 2609,
  "Device": {
    "Identifier": "7db01528cf13e2199e141c402d79190e",
    "Language": "Chinese"
  }
}
```

### 成功响应（Status 200）

```json
{
  "Status": 200,
  "Message": "",
  "Token": "eyJhbGciOiJIUzI1NiIsInR5cCI6...",
  "AuthCode": "IKuoMliVTbXte15U7H8ROjaA2CQk96fh",
  "Data": {
    "User": {
      "ID": "5d0f4390ca68215906d1a0fd",
      "Nickname": "用户昵称",
      "Signature": "个性签名",
      "Gold": 350,
      "Diamond": 0,
      "Fragment": 0,
      "Level": 1,
      "Experience": 0,
      "Prestige": 0,
      "Avatar": 0,
      "AvatarRegion": 0,
      "Decoration": 0,
      "Verification": null,
      "IsBinded": true
    },
    "DeviceToken": "device_token_string",
    "Statistic": {
      "ExperimentCount": 10,
      "FollowerCount": 5,
      "FollowingCount": 20
    }
  }
}
```

### 失败响应

| Status | Message | 说明 |
|--------|---------|------|
| 403 | `Login.Password.Invalid` | 邮箱或密码错误 |
| 403 | `Login.Account.Locked` | 账号被封禁 |
| 400 | `Input.Field.Missing` | 缺少必填字段 |

## 2. 匿名登录

不提供邮箱密码，以游客身份登录，可访问公开内容但不能发表/互动。

### 请求体

```json
{
  "Login": null,
  "Password": null,
  "Version": 2609,
  "Device": {
    "Identifier": "7db01528cf13e2199e141c402d79190e",
    "Language": "Chinese"
  }
}
```

### 响应说明

匿名登录返回的 `Token` 可能为 `null`，但 `AuthCode` 有效，可用于访问公开接口（如 `QueryExperiments`、`GetLibrary`、`GetUser` 等）。匿名用户的 `Nickname` 为 `null`，`IsBinded` 为 `false`。

## 3. Token 登录（免密续期）

使用之前登录获取的 `Token` 和 `AuthCode` 重新建立会话，无需再次输入密码。适用于持久化登录状态。

### 请求头

```
x-API-Token: <已获取的Token>
x-API-AuthCode: <已获取的AuthCode>
```

### 请求体

```json
{
  "Login": null,
  "Password": null,
  "Version": 2609,
  "Device": {
    "Identifier": "7db01528cf13e2199e141c402d79190e",
    "Language": "Chinese"
  }
}
```

### 响应

与邮箱登录成功响应结构相同，返回新的 `Token` 和 `AuthCode`。

## 认证头使用

登录成功后，所有需要认证的接口都需在请求头中携带：

```
x-API-Token: <Token>
x-API-AuthCode: <AuthCode>
```

这两个值来自登录响应的顶层字段（不在 `Data` 内）。

## User 对象字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `ID` | string | 用户唯一 ID（MongoDB ObjectId 格式） |
| `Nickname` | string | 用户昵称 |
| `Signature` | string/null | 个性签名 |
| `Gold` | int | 金币数量 |
| `Diamond` | int | 钻石数量 |
| `Fragment` | int | 碎片数量 |
| `Level` | int | 用户等级 |
| `Experience` | int | 经验值 |
| `Prestige` | int | 声望值 |
| `Avatar` | int | 头像索引 |
| `AvatarRegion` | int | 头像区域索引 |
| `Decoration` | int | 装饰索引 |
| `Verification` | string/null | 认证信息 |
| `IsBinded` | bool | 是否已绑定邮箱 |

## Version 字段说明

`Version` 字段对应物理实验室客户端版本整数，常见格式为 `YYMM`：

- 示例值应与调用方实际客户端版本一致；下面的历史值仅用于识别格式，不作为建议默认值。
- `2406` — 2024 年 6 月版本

不要反复猜测版本号或把历史示例当作长期可用默认值。对接现有客户端时读取其实际版本；自建调用方应按服务端兼容约定设置，并在错误响应中检查 `Message`。
