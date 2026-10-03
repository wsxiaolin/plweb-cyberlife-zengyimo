---
name: plweb-skill
description: 面向 Physics Lab / 物理实验室 AR 社区 API 的实用指南。用户要登录、查作品/用户/评论/收件箱消息、发布或管理作品、互动或开发 plweb2/API 客户端时使用。包含可运行请求范例、认证和分页处理、错误排查与写操作注意事项。中国区 API 为 physics-api-cn.turtlesim.com；跨区时按用户所在区选择服务域名。
---

# 物理实验室 AR 社区 API 调用技能

本技能说明如何调用「物理实验室 AR」（Physics Lab / 烧杯实验室）社区 API。端点与字段参考父目录 `physics-lab-turtle-services` 的 `Quantum API/Controllers`、`Quantum Models` 和 `Quantum Logics` 实现；服务端代码优先于旧示例。写操作前先确认目标 ID、权限和影响范围。

## 快速上手

1. 选对区域域名：中国区 `https://physics-api-cn.turtlesim.com`，国际区 `https://physics-api-us.turtlesim.com`。不要默认跨区复用登录凭据。
2. 先匿名登录或用用户明确提供的账号登录。不要索要、打印或写入源码用户密码、Token；从安全的秘密存储或环境变量读取。匿名登录适合读取公开数据，不能假定它具备写权限。
3. 除明确为 GET 的路由外，使用 `POST` JSON，并检查响应 JSON 的 `Status`、`Message` 和 `Data`；HTTP 200 本身不代表业务成功。
4. 需要认证的请求同时带 `x-API-Token` 与 `x-API-AuthCode`。登录响应顶层或后续响应头可能提供更新值。
5. 分页使用 `Skip`/`Take`，逐页读取并控制请求速率；不要并发轰击 API。
6. 发布、删除、评论、关注、点赞等写操作先读取并确认目标，再执行并检查响应。会影响真实社区的操作须有用户明确指示。

端到端 Python 示例见 [`docs/quickstart.md`](docs/quickstart.md)。

返回 JSON 的字段含义、对象嵌套、数组包装和各接口 `Data` 类型见 [`docs/responses.md`](docs/responses.md)。使用响应时以该页字段表和父目录模型源码为准。

## 一、API 概览

### 基础信息

| 项目 | 值 |
|------|-----|
| 协议 | HTTPS（端口 443） |
| 中国区域名 | `physics-api-cn.turtlesim.com` |
| 国际区域名 | `physics-api-us.turtlesim.com` |
| 请求方法 | 绝大多数为 `POST`，少数为 `GET` |
| 请求体格式 | JSON（`Content-Type: application/json`） |
| 响应体格式 | JSON |
| 字符编码 | UTF-8 |
| 响应可能启用 | gzip 压缩 |

### 响应统一结构

控制器成功/失败响应通常使用以下 JSON 包装（静态文件、下载或特殊路由可能不同）：

```json
{
  "Status": 200,
  "Message": "",
  "Data": { ... }
}
```

- `Status`：JSON 内的业务状态码，`200` 表示成功，其他值表示失败；不要把它和 HTTP 传输状态混为一谈
- `Message`：成功时为空字符串；失败时为错误标识符（如 `"Login.Password.Invalid"`、`"Input.Field.Missing"`）
- `Data`：成功时为数据对象或数组；失败时通常为 `null`

**常见错误 Message：**
- `Login.Password.Invalid` — 邮箱或密码错误
- `Input.Field.Missing` — 请求体缺少必填字段
- `Content.Not.Exists` — 内容不存在
- `Permission.Denied` — 权限不足

> **注意**：对象集合可能序列化为带 `$type` 和 `$values` 的结构，也可能直接是数组。解析时兼容两种形式，不要假设所有列表包装相同。

### 路由与源码的对应

以服务端控制器为准：用户接口在 `Users`，内容/实验在 `Contents`，评论接口也由 `Messages` 控制器提供。点赞端点是 `Contents/StarContent`；发布入口为 `Contents/SubmitExperiment`，可能需要后续 `ConfirmExperiment`。查询字段参见 `Quantum Models/Contents/ExperimentQuery.cs`。旧字段示例与源码不一致时，以控制器实际读取字段和模型定义为准。

### 身份认证

登录成功后，响应体会返回 `Token` 和 `AuthCode` 两个字段（位于顶层，不在 `Data` 内）。后续所有需要认证的接口都需在请求头中携带：

```
x-API-Token: <Token>
x-API-AuthCode: <AuthCode>
```

匿名登录也会返回 `AuthCode`（`Token` 可能为 `null`），可用于访问部分公开接口。

## 二、登录认证

### 1. 邮箱登录（Users/Authenticate）

```http
POST /Users/Authenticate
Content-Type: application/json
```

**请求体：**
```json
{
  "Login": "user@example.com",
  "Password": "yourpassword",
  "Version": 2609,
  "Device": {
    "Identifier": "7db01528cf13e2199e141c402d79190e",
    "Language": "Chinese"
  }
}
```

**成功响应（Status 200）：**
```json
{
  "Status": 200,
  "Message": "",
  "Token": "xxxxxxxxxxxx",
  "AuthCode": "xxxxxxxxxxxx",
  "Data": {
    "User": {
      "ID": "5d0f4390ca68215906d1a0fd",
      "Nickname": "用户昵称",
      "Signature": "个性签名",
      "Gold": 350,
      "Diamond": 0,
      "Level": 1,
      "Experience": 0,
      "Avatar": 0,
      "AvatarRegion": 0,
      "Decoration": 0,
      "Verification": null,
      "IsBinded": true
    },
    "DeviceToken": "...",
    "Statistic": { ... }
  }
}
```

### 2. 匿名登录

将 `Login` 和 `Password` 设为 `null` 即可匿名登录，返回一个匿名用户身份，可访问公开内容。

### 3. Token 登录（免密续期）

在请求头中携带已有的 `x-API-Token` 和 `x-API-AuthCode`，同时请求体中 `Login`/`Password` 设为 `null`，即可刷新登录状态。

> **Version 字段**：对应物理实验室客户端版本号，格式为 `YYMM`（如 `2411` 表示 2024 年 11 月版本）。版本过旧可能导致登录被拒。

## 三、核心接口速查

### 用户相关（Users）

| 接口 | 路径 | 方法 | 说明 |
|------|------|------|------|
| 登录认证 | `Users/Authenticate` | POST | 邮箱/匿名/Token 登录 |
| 获取用户 | `Users/GetUser` | POST | 按用户名或 ID 查询用户资料 |
| 关注用户 | `Users/Follow` | POST | 关注/取关指定用户 |
| 修改昵称 | `Users/Rename` | POST | 修改当前用户昵称 |
| 修改信息 | `Users/ModifyInformation` | POST | 修改个人签名等信息 |
| 领取奖励 | `Users/ReceiveBonus` | POST | 领取活动奖励 |
| 封禁用户 | `Users/Ban` | POST | 管理员封禁用户 |
| 解封用户 | `Users/Unban` | POST | 管理员解封用户 |
| 获取关系 | `Users/GetRelations` | POST | 获取粉丝/关注列表 |

### 内容相关（Contents）

| 接口 | 路径 | 方法 | 说明 |
|------|------|------|------|
| 查询实验 | `Contents/QueryExperiments` | POST | 按条件搜索实验/讨论 |
| 获取实验 | `Contents/GetExperiment` | POST | 获取实验完整内容 |
| 获取摘要 | `Contents/GetSummary` | POST | 获取实验摘要信息 |
| 获取衍生 | `Contents/GetDerivatives` | POST | 获取改编/衍生作品 |
| 获取支持者 | `Contents/GetSupporters` | POST | 获取点赞/支持者列表 |
| 点赞内容 | `Contents/StarContent` | POST | 点赞/取消点赞 |
| 获取评论 | `Messages/GetComments` | POST | 获取内容评论列表 |
| 发表评论 | `Messages/PostComment` | POST | 发表评论/回复 |
| 删除评论 | `Messages/RemoveComment` | POST | 删除指定评论 |
| 提交实验 | `Contents/SubmitExperiment` | POST | 新建/更新实验作品；请求结构复杂，按源码模型构造 |
| 更新封面 | `Contents/ConfirmExperiment` | POST | 确认封面序号或上传封面文件 |
| 删除实验 | `Contents/RemoveExperiment` | POST | 删除已发布实验 |
| 获取资料页 | `Contents/GetProfile` | POST | 获取用户主页内容 |
| 获取社区库 | `Contents/GetLibrary` | POST | 获取首页/讨论区/实验区 |

### 消息相关（Messages）

| 接口 | 路径 | 方法 | 说明 |
|------|------|------|------|
| 获取消息列表 | `Messages/GetMessages` | POST | 获取当前用户收件箱 |
| 获取单条消息 | `Messages/GetMessage` | POST | 获取指定消息详情 |
| 批量模板消息 | `Messages/SendMessages` | POST | 管理员专用；发送服务端模板，不是自由文本私信 |

### 公开接口（无需认证）

| 接口 | 路径 | 方法 | 说明 |
|------|------|------|------|
| 社区首页 | `Users` | GET | 获取首页导航数据 |
| 获取头像/封面 | `https://<domain>/Avatars/...` | GET | 获取用户头像或实验封面图 |

## 四、枚举值参考

### Category（内容分类）
- `"Experiment"` — 实验区
- `"Discussion"` — 讨论区（黑洞）

### Tag（社区标签）
**实验区标签：** `知识库`、`精选`、`小学`、`初中`、`高中`、`大学`、`专科`、`娱乐实验`、`小作品`、`教学实验`、`禁止改编`、`精选申请`

**讨论区标签：** `BUG`、`交流`、`小说专区`、`聊天`、`问与答`

**历史标签：** `逻辑电路`、`直流电路`、`交流电路`、`电子电路`、`兴趣`

### Sort（排序方式，QueryExperiments 用）
- `0` — 最新
- `1` — 最热（热门）

### MessageCategoryID（消息分类）
- `0` — 全部
- `1` — 系统邮件
- `2` — 关注与粉丝
- `3` — 评论与回复
- `4` — 作品通知
- `5` — 管理记录

### DisplayType（关系类型，GetRelations 用）
- `"Follower"` — 粉丝
- `"Following"` — 关注

## 五、调用示例

```bash
# 登录
curl -X POST "https://physics-api-cn.turtlesim.com/Users/Authenticate" \
  -H "Content-Type: application/json" \
  -d '{"Login":"user@example.com","Password":"<secret>","Version":2609,"Device":{"Identifier":"7db01528cf13e2199e141c402d79190e","Language":"Chinese"}}'

# 查询实验（需替换 TOKEN 和 AUTHCODE）
curl -X POST "https://physics-api-cn.turtlesim.com/Contents/QueryExperiments" \
  -H "Content-Type: application/json" \
  -H "x-API-Token: TOKEN" \
  -H "x-API-AuthCode: AUTHCODE" \
  -d '{"Query":{"Category":"Experiment","Languages":[],"ExcludeLanguages":[],"Tags":null,"ExcludeTags":null,"ModelTags":null,"ModelID":null,"ParentID":null,"UserID":null,"Special":null,"From":null,"Skip":0,"Take":10,"Days":0,"Sort":0,"ShowAnnouncement":false}}'
```

## 六、详细接口文档

各接口的完整请求/响应字段说明请参阅 `docs/` 目录下的详细文档：

- [`docs/authentication.md`](docs/authentication.md) — 登录认证详解
- [`docs/users.md`](docs/users.md) — 用户接口详解
- [`docs/content.md`](docs/content.md) — 内容/实验接口详解
- [`docs/messages.md`](docs/messages.md) — 消息接口详解
- [`docs/comments.md`](docs/comments.md) — 评论接口详解
- [`docs/market.md`](docs/market.md) — 社区/资料页接口详解
- [`docs/enums.md`](docs/enums.md) — 枚举值完整参考
- [`docs/examples.md`](docs/examples.md) — 完整代码示例（Python / Node.js / curl）
- [`docs/quickstart.md`](docs/quickstart.md) — 安全登录、分页查询、错误处理快速入门
- [`docs/responses.md`](docs/responses.md) — 通用响应壳、Data 对象结构和字段说明

## 七、注意事项

1. **域名选择**：中国区使用 `physics-api-cn.turtlesim.com`，国际区可能使用不同域名，请根据用户所在区域选择。
2. **HTTPS 证书**：保持证书验证开启。遇到证书错误时先核对域名、系统时间和证书链；不要用 `curl -k` 或关闭 Python TLS 验证规避问题，以免凭据被中间人窃取。
3. **Token 有效期**：Token 有有效期，过期后需重新登录或使用 Token 登录刷新。
4. **频率限制**：API 可能有频率限制，批量操作时建议适当间隔请求。
5. **Version 字段**：登录时的 `Version` 是客户端版本整数（常见格式 `YYMM`）；示例值会过时，应使用目标客户端实际版本，不要机械复制。
6. **返回体解析**：列表可能直接是 JSON 数组，也可能包装为 `{"$type":"...","$values":[...]}`；部分接口的 `Data` 是包含数组的对象包（例如 `Messages`、`Comments`），先按接口响应说明取对应属性。
7. **管理员接口**：`Ban`、`Unban` 等接口需要管理员权限，普通用户调用会返回权限错误。
8. **实验内容格式**：实验内容（`GetExperiment` 返回的 `Data`）为序列化的电路/天体物理模型 JSON，结构复杂，修改时需保留原有结构。
