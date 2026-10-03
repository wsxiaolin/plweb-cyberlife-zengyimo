# API 返回体结构参考

本页以父目录 `physics-lab-turtle-services` 当前的 `BaseController`、`Quantum Models` 和控制器实现为准。接口响应外壳、业务对象和客户端解析方式分开说明。字段以当前模型为依据；不同版本、权限、匿名脱敏、作品类别和空值会让实例略有差异。

## 1. 通用外壳

控制器通过 `Succeeded` / `Failed` 返回 JSON。成功时形状为：

```json
{
  "Status": 200,
  "Message": "",
  "Data": {}
}
```

认证信息存在时，`Token` 和 `AuthCode` 也会出现在外层；认证接口的业务数据仍然放在 `Data`：

```json
{
  "Status": 200,
  "Message": "",
  "Token": "<token>",
  "AuthCode": "<auth-code>",
  "Data": {}
}
```

失败通常仍使用同一外壳：`Status` 是业务状态码，`Message` 是机器可读错误码，`Data` 可能是 `null`，也可能是出错字段名或约束对象。比如缺字段时常见 `Data: "Query"`；不能只检查 HTTP 状态码，应解析 JSON 后判断 `Status == 200`。传输层 HTTP/TLS 错误则另外由 HTTP 客户端处理。

```json
{
  "Status": 400,
  "Message": "Input.Field.Missing",
  "Data": "Query"
}
```

若一次有 Token 的操作刷新了凭据，服务端也可能通过 `x-API-Token`、`x-API-AuthCode` 响应头返回新值。保存有效的新值，不要记录完整认证响应或凭据到日志。

## 2. 列表、类型标记与空值

Newtonsoft JSON 的 `TypeNameHandling.Auto` 会令某些多态对象或数组带 `$type` 元信息。数组有时序列化为 `$values` 包装：

```json
{
  "$type": "<runtime-type>",
  "$values": [ { "ID": "..." }, { "ID": "..." } ]
}
```

解析规则：

- 若 `Data` 是数组，直接迭代；若 `Data` 是带 `$values` 的对象，迭代 `Data["$values"]`。
- `$type` 是运行时/程序集类型提示，不是业务字段，也不应硬编码或作为稳定 discriminator。
- `null`、空数组 `[]`、字段缺省和空字符串 `""` 含义不同。尤其可选关联对象和权限隐藏字段可能为 `null` 或未出现。
- 数字枚举按 JSON number 输出；时间可能是 ISO 日期时间，也可能是 Unix ticks/秒数数值，须按具体字段说明解读。

## 3. 登录：`Users/Authenticate`

`Data` 是 `StartupPackage`，不是只有一个 User。常见结构如下（为便于阅读删去了大量可选表项）：

```json
{
  "Status": 200,
  "Message": "",
  "Token": "<token>",
  "AuthCode": "<auth-code>",
  "Data": {
    "User": { "ID": "<user-id>", "Nickname": "昵称", "Signature": "签名", "Level": 1 },
    "Statistic": { "ID": "<user-id>", "UnreadMessages": 0, "UnreadLetters": 0 },
    "Backpack": {},
    "UserToken": { "Email": "user@example.com", "Mobile": null },
    "DeviceToken": "<device-token>",
    "Activities": [],
    "ChargePrices": [],
    "ObjectPrices": [],
    "ContentTags": [],
    "Surveys": [],
    "Blacklist": [],
    "Library": {},
    "Features": []
  }
}
```

`Token`/`AuthCode` 在最外层；后续认证请求把它们放进 `x-API-Token`、`x-API-AuthCode` 请求头。`Data.User` 是完整 User 模型（字段多于示例）；`Data.Statistic` 是登录统计；`Backpack` 是背包/道具；`UserToken` 是账号绑定信息；启动包的价格、标签、活动、首页资料可能按区域、客户端版本、绑定状态而为空或省略。匿名登录的 User 和凭据也可能不同，不要假定匿名账号可以写入社区。

## 4. 作品数据

### 4.1 列表：`Contents/QueryExperiments`

`Data` 是 `ExperimentSummary[]`。真实模型字段名是 `ID`、`Subject`、`User` 等；旧文档中的 `Title`、`Author`、`Thumbnail`、`PublishDate` 不是该模型的字段名。

```json
{
  "Status": 200,
  "Message": "",
  "Data": {
    "$type": "<ExperimentSummary[] runtime type>",
    "$values": [
      {
        "ID": "64a1b2c3d4e5f67890123456",
        "Category": "Experiment",
        "Subject": "欧姆定律实验",
        "Image": 2,
        "ImageRegion": 1,
        "User": { "ID": "<author-id>", "Nickname": "作者", "Avatar": 3 },
        "Visibility": 0,
        "Type": 0,
        "ParentID": null,
        "ParentName": null,
        "ParentCategory": null,
        "ContentID": "<save-id>",
        "Editor": null,
        "Coauthors": [],
        "Description": ["测量电压与电流的关系。"],
        "LocalizedDescription": null,
        "Tags": ["高中"],
        "ModelID": null,
        "ModelName": null,
        "ModelTags": [],
        "Version": 1,
        "Language": "Chinese",
        "Visits": 120,
        "Stars": 8,
        "Supports": 0,
        "Remixes": 1,
        "Comments": 2,
        "Price": 0,
        "Popularity": 120,
        "CreationDate": 1720000000000,
        "UpdateDate": 1720000000000,
        "SortingDate": 1720000000000
      }
    ]
  }
}
```

关键字段：

| 字段 | 含义 |
|---|---|
| `ID` | 社区作品摘要 ID；传给 `GetSummary`/`GetExperiment` 时也要按端点要求提供 `Category` 或字段 `ContentID`。 |
| `Category` | 内容类别，如 `Experiment`、`Discussion`、`Model`。 |
| `Subject` / `LocalizedSubject` | 标题及本地化标题；不能用 `Title` 替代。 |
| `User` / `Coauthors` | 作者与合作者摘要对象。用户摘要常见 `ID`、`Nickname`、`Signature`、`Avatar`、`AvatarRegion`、`Decoration`、`Verification`。 |
| `Image` / `ImageRegion` | 封面序号和存储区域，不是图片内容本身。 |
| `ContentID` | 关联的实验保存 ID；可能为空，和摘要 `ID` 不要混为一谈。 |
| `Description` / `LocalizedDescription` | 描述段落数组或多语言文本对象；可能因裁剪/本地化策略缺省。 |
| `Visibility` | 数字枚举：`0` Public、`1` Private、`2` Hidden、`3` Removed；没有权限时作品可能不会返回。 |
| `Visits`、`Stars`、`Supports`、`Remixes`、`Comments` | 访问、普通点赞、支持、衍生和评论计数。 |
| `CreationDate`、`UpdateDate`、`SortingDate` | 模型中的 `long` 时间值；通常是 Unix 毫秒。应检查数据并按毫秒解析，不按 ISO 字符串解析。 |

数组顺序是服务端查询排序结果。接口不返回统一的 `Pages`/`Count` 包装；按当前查询条件用 `Skip`/`Take` 继续翻页。

### 4.2 摘要：`Contents/GetSummary`

`Data` 是单个 `ExperimentSummary` 对象，字段结构与上表中的数组元素相同，不会额外套一个 `Summary` 属性。

### 4.3 完整保存：`Contents/GetExperiment`

`Data` 是 `Quantum.Models.Contents.Experiment`：

```json
{
  "Status": 200,
  "Message": "",
  "Data": {
    "ID": "<save-id>",
    "Type": 0,
    "Components": 12,
    "Subject": "欧姆定律实验",
    "StatusSave": "<serialized-status>",
    "CameraSave": "<serialized-camera>",
    "Version": 2411,
    "CreationDate": 1720000000000,
    "Paused": false,
    "Summary": { "ID": "<summary-id>", "Category": "Experiment", "Subject": "欧姆定律实验" },
    "Plots": []
  }
}
```

`Type` 是实验类型枚举：`-1` Unloaded、`0` Circuit、`1` Diagram、`2` Optics、`3` Celestial、`4` Electromagnet、`5` Mechanics。保存内容位于 `StatusSave`、`CameraSave`、`Plots` 等字段，并非 `Data.Content` 字符串。它们可能包含很大的客户端序列化数据；读取后应原样保留未知字段。

### 4.4 衍生作品：`Contents/GetDerivatives`

`Data` 是 `ContentPackage`，其中 `Experiments` 是按服务端标签分组的字典，值是作品摘要数组。根据 `WithSummary` 请求值，`Summary` 可能出现；关联作品不存在时 `Parent`、`Model` 可为 `null`，支持者数组也可能为空：

```json
{
  "Status": 200,
  "Message": "",
  "Data": {
    "Experiments": { "Children-Models": [] },
    "Survey": null,
    "Summary": null,
    "Parent": null,
    "Model": null,
    "Supporters": []
  }
}
```

字典键是服务端分组名，不要假设固定只有 `Children-Models`；根据作品关联关系可能为空或出现其他分组。

### 4.5 支持者：`Contents/GetSupporters`

`Data` 是 `UserSummary[]`，每个元素是简要用户对象（`ID`、`Nickname`、`Signature`、`Avatar`、`AvatarRegion`、`Decoration`、`Verification` 等），不是 `{Supporters:[...]}` 包装。该接口的 `Take` 最大被限制为 50。

## 5. 用户接口返回

`Users/GetUser` 的 `Data` 是 `UserPackage`：

```json
{
  "Status": 200,
  "Message": "",
  "Data": {
    "User": { "ID": "<user-id>", "Nickname": "昵称", "Signature": "签名", "Avatar": 3 },
    "Statistic": { "ID": "<user-id>", "UnreadMessages": 2, "UnreadLetters": 0 },
    "Backpack": null,
    "Bonuses": null,
    "UserToken": null,
    "Relation": 0,
    "TargetLink": null
  }
}
```

`User` 的具体属性视端点权限和是否为完整 User 而变；`Statistic` 是统计/活动状态；`Backpack`、`Bonuses`、`UserToken`、`Relation`、`TargetLink` 是 UserPackage 的可选扩展。匿名化结果、没绑定的用户或当前关系不存在时，字段可能为空。

`Users/Follow` 返回关系操作结果作为 `Data`，顶层 `Message` 可能带操作说明；它不是完整用户对象。调用方若需要最新用户统计，应再请求 `Users/GetUser`。

`Users/GetRelations` 的 `Data` 是 `UserPackage[]`，而非纯 `UserSummary[]`。每项包含 `User`、`Statistic`、`Relation` 等字段，供关系列表显示用户和当前查看者之间的关系；支持数组直接返回或 `$values` 包装。`DisplayType` 是整数枚举：`-1` Blacklist、`0` Followed（粉丝）、`1` Following（关注）、`2` Banned、`3` Volunteers、`4` Editors、`5` Emeritus。

关注接口响应示意：

```json
{ "Status": 200, "Message": "", "Data": true }
```

`Data` 是是否成功建立/取消关系的布尔值；失败时 `Status` 非 200、`Message` 给出错误码，`Data` 可能为 false。不要把 `Data` 当作用户对象。

## 6. 评论返回

`Messages/GetComments` 的 `Data` 是 `CommentsPackage<ExperimentSummary>` 或 `CommentsPackage<User>`，结构是：

```json
{
  "Status": 200,
  "Message": "",
  "Data": {
    "Count": 23,
    "Target": { "ID": "<target-id>", "Category": "Experiment", "Subject": "作品标题" },
    "Comments": [
      {
        "TargetID": "<target-id>",
        "ID": "<comment-id>",
        "UserID": "<commenter-id>",
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

`Count` 是该目标的评论总数，不是本页长度；`Comments` 是分页数组；每条评论的 `Replies` 是子评论内容数组。模型不保证有旧文档示例中的 `Author`、`SendDate`、`Floor`、`IsEdited` 字段。匿名化和隐藏权限会影响可见字段/内容。`PostComment` 的 `Data` 是新建的 Comment；删除接口成功时 `Data` 可能为 `null`。

## 7. 收件箱返回

`Messages/GetMessages` 的 `Data` 是 `MessagesPackage`，而不是消息数组本身：

```json
{
  "Status": 200,
  "Message": "",
  "Data": {
    "Messages": [
      {
        "ID": "<message-id>",
        "CategoryID": 3,
        "TemplateID": "<template-id>",
        "TargetID": "<target-user-id>",
        "Users": ["<source-user-id>"],
        "UserNames": ["发送者"],
        "UserAvatar": 0,
        "Timestamp": 1720000000000,
        "TimestampInitial": 1720000000000,
        "Unread": 1,
        "Handled": 0,
        "Fields": {},
        "Numbers": {}
      }
    ],
    "Templates": []
  }
}
```

`Messages` 是消息条目列表；`Templates` 只在 `Skip == 0` 且 `NoTemplates` 为 false 时加载，否则可能是 `null`。消息正文不是稳定的 `Content` 字段：根据 `TemplateID`，文本替换值放在 `Fields`（字符串字典）和 `Numbers`（数字字典）里。`CategoryID` 是枚举：0 Everything、1 Letter、2 Attention、3 Comment、4 Experiment、5 Management。`Timestamp`、`TimestampInitial` 及读/处理标记是毫秒级 Unix 时间值。

`Unread`、`Handled` 在模型中是 `long` 标记值，不是布尔值或未读条数；读取消息时服务端会更新 `Unread` 标记，处理邀请会把 `Handled` 的待处理标记改成处理时间。业务判断应结合消息类别和客户端约定，不要把这些字段直接当计数。

## 8. 用户资料页与社区库

`Contents/GetProfile` 返回 `ProfilePackage`：

```json
{
  "Status": 200,
  "Message": "",
  "Data": {
    "Experiments": {
      "Featured-Discussions": [], "Popular-Discussions": [], "Latest-Discussions": [],
      "Featured-Experiments": [], "Popular-Experiments": [], "Latest-Experiments": []
    },
    "Survey": null
  }
}
```

`Experiments` 是分组名到 `ExperimentSummary[]` 的字典；热门组可能因精选数量而不出现。`Survey` 为关联问卷摘要或 `null`。

`Contents/GetLibrary` 和 `GET /Users` 成功时，`Data` 是 `Library` 对象，核心字段是 `ID`、`Identifier`、`Subject`、`Language`、`IsNavigation`、`IsDevelopment`、`Blocks`。每个 block 有 `Type`、`Header`、`TargetLink`、`FetchSource`、`FetchConfiguration`、`Permission`、`Locations`、`Summaries` 等基础字段，并会按 block 类型附带 `Subject`、`Background` 等字段；这是多态对象，需保留未知扩展字段。

## 9. 写操作常见返回

- `Contents/StarContent`：`Data` 通常是 `UserPackage`（当前 `User` 及可能的 `Statistic`/`Bonuses`）；操作状态还可结合顶层 `Message`。字段取决于支持/点赞类型、是否绑定和是否产生奖励。
- `Contents/SubmitExperiment`：`Data` 是 `ExperimentPackage`。关键字段为 `Summary`（创建/更新后的 `ExperimentSummary`）和 `User`；首次发布可能含 `Bonuses`，提交图片上传请求时可能含 `Token` 或 `AliyunToken`。上传 Token 是存储服务凭据，应按秘密处理。
- `Contents/ConfirmExperiment`：成功时 `Data` 是更新后的 `ExperimentSummary`，不是上传状态布尔值。
- `Contents/RemoveExperiment`、`Contents/VisitExperiment`：`Data` 是操作成功布尔值。
- `Users/Rename`、`Users/ModifyInformation`：`Data` 是 `UserPackage`；通常仅 `User` 有值，部分操作返回 `Statistic`。
- `Messages/PostComment`：`Data` 是新建的 `Comment`；`Messages/RemoveComment` 成功时 `Data` 为空。

上传类响应里 `Token`/`AliyunToken` 是用于将二进制图片传到对象存储的短期授权资料，不是 API 登录 Token；不要混用或记录到日志。

## 10. 解析器示例

```python
def get_items(data):
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and isinstance(data.get("$values"), list):
        return data["$values"]
    return []

payload = response.json()
if payload.get("Status") != 200:
    raise RuntimeError(f"{payload.get('Message')}: {payload.get('Data')}")
experiments = get_items(payload.get("Data"))
```

`GetDerivatives`、`GetUser`、`GetMessages`、`GetComments` 返回对象包，不应直接传给 `get_items`；先取 `Data["Experiments"]`、`Data["User"]`、`Data["Messages"]` 或 `Data["Comments"]`，再按实际 JSON 形状解包数组。
