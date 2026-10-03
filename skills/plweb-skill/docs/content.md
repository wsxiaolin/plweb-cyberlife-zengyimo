# 内容/实验接口详解

内容接口位于 `Contents/` 路径下，提供实验/讨论的查询、获取、发布、删除、点赞、衍生作品查询等功能。所有接口均需认证。

## 1. 查询实验列表（Contents/QueryExperiments）

按多条件搜索实验或讨论作品，是最核心的列表查询接口。

### 请求

```http
POST /Contents/QueryExperiments
```

**请求体：**
```json
{
  "Query": {
    "Category": "Experiment",
    "Languages": [],
    "ExcludeLanguages": [],
    "Tags": null,
    "ExcludeTags": null,
    "ModelTags": null,
    "ModelID": null,
    "ParentID": null,
    "UserID": null,
    "Special": null,
    "From": null,
    "Skip": 0,
    "Take": 16,
    "Days": 0,
    "Sort": 0,
    "ShowAnnouncement": false
  }
}
```

### Query 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `Category` | string | `"Experiment"` 实验区，`"Discussion"` 讨论区 |
| `Languages` | array | 筛选语言列表（空数组表示不限） |
| `ExcludeLanguages` | array | 排除语言列表 |
| `Tags` | array/null | 筛选标签列表（如 `["精选"]`） |
| `ExcludeTags` | array/null | 排除标签列表 |
| `ModelTags` | array/null | 模型标签筛选 |
| `ModelID` | string/null | 筛选特定模型 ID |
| `ParentID` | string/null | 筛选特定父作品 ID（获取衍生作品时用） |
| `UserID` | string/null | 筛选特定用户的作品 |
| `Special` | string/null | 特殊筛选 |
| `From` | string/null | 起始内容 ID（游标分页） |
| `Skip` | int | 跳过条数（偏移分页） |
| `Take` | int | 获取条数（默认 16） |
| `Days` | int | 时间范围（天数，0 表示不限） |
| `Sort` | int | 排序方式：`0` 最新，`1` 最热 |
| `ShowAnnouncement` | bool | 是否显示公告 |

### 响应

```json
{
  "Status": 200,
  "Message": "",
  "Data": {
    "$type": "<runtime type hint>",
    "$values": [
      {
        "ID": "16a627bdb25f77131ba28018",
        "Category": "Experiment",
        "Subject": "实验标题",
        "Image": 0,
        "ImageRegion": 1,
        "User": { "ID": "<user-id>", "Nickname": "作者昵称", "Avatar": 0 },
        "Visibility": 0,
        "Type": 0,
        "ParentID": null,
        "ContentID": "<experiment-save-id>",
        "Editor": null,
        "Coauthors": [],
        "Description": ["作品说明"],
        "LocalizedDescription": null,
        "Tags": ["高中"],
        "ModelID": null,
        "ModelName": null,
        "ModelTags": [],
        "Version": 1,
        "Language": "Chinese",
        "Visits": 0,
        "Stars": 0,
        "Supports": 0,
        "Remixes": 0,
        "Comments": 0,
        "Price": 0,
        "Popularity": 0,
        "CreationDate": 1720000000000,
        "UpdateDate": 1720000000000,
        "SortingDate": 1720000000000
      }
    ]
  }
}
```

`Data` 也可能直接是数组，不带 `$type`/`$values` 包装。列表没有额外的 `Pages` 或 `Count` 字段。

列表元素是 `ExperimentSummary`。重点字段是 `ID`（摘要 ID）、`Category`（作品类别）、`Subject`（标题）、`User`（作者简表）、`ContentID`（可能为空的实验保存 ID）、`Description`、`Tags`、`Visibility` 和各项计数。实际字段完整说明见 [`responses.md`](responses.md#4-作品数据)。此处不使用旧示例中的 `Title`、`Author`、`Thumbnail`、`Summary` 或 `PublishDate`，这些不是当前模型字段名。


## 2. 获取实验详情（Contents/GetExperiment）

获取实验的完整内容数据，包括电路/天体物理模型。

### 请求

```http
POST /Contents/GetExperiment
```

**请求体：**
```json
{
  "ContentID": "<experiment-save-id>"
}
```

这里的 `ContentID` 是 `ExperimentSummary.ContentID` 保存 ID，不是作品摘要的 `ID`。成功时 `Data` 是单个 `Experiment` 保存对象，字段为 `ID`、`Type`、`Components`、`Subject`、`StatusSave`、`CameraSave`、`Version`、`CreationDate`、`Paused`、`Summary`、`Plots`。其中 `StatusSave`/`CameraSave` 是客户端保存数据，不是 `Content` 字符串。字段解释和样例见 [`responses.md`](responses.md#43-完整保存-contentsgetexperiment)。

## 3. 获取实验摘要（Contents/GetSummary）

获取实验的摘要信息，比列表返回的更详细。

### 请求

```http
POST /Contents/GetSummary
```

**请求体：**
```json
{
  "ContentID": "<summary-ID>",
  "Category": "Experiment"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `ContentID` | string | 内容 ID |
| `Category` | string | `"Experiment"` 或 `"Discussion"` |

### 响应

成功时 `Data` 是一个 `ExperimentSummary` 对象（直接对象，不是 `Data.Summary` 包装）。请求使用 `ContentID`；其返回字段与列表元素相同，见 [`responses.md`](responses.md#42-摘要-contentsgetsummary)。

## 4. 获取衍生作品（Contents/GetDerivatives）

获取指定作品的改编/衍生作品列表。

### 请求

```http
POST /Contents/GetDerivatives
```

**请求体：**
```json
{
  "ContentID": "<summary-ID>",
  "Category": "Experiment"
}
```

### 响应

`Data` 是 `ContentPackage`：主要包含 `Experiments` 分组字典、`Summary`（仅 `WithSummary=true` 时填充）、`Parent`、`Model`、`Supporters` 和 `Survey`。见 [`responses.md`](responses.md#44-衍生作品-contentsgetderivatives)。

## 5. 获取支持者列表（Contents/GetSupporters）

获取为指定作品点赞/支持的用户列表。

### 请求

```http
POST /Contents/GetSupporters
```

**请求体：**
```json
{
  "ContentID": "<summary-ID>",
  "Category": "Experiment",
  "Skip": 0,
  "Take": 10
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `ContentID` | string | 内容 ID（必填） |
| `Category` | string | `"Experiment"` 或 `"Discussion"` |
| `Skip` | int | 跳过条数 |
| `Take` | int | 获取条数 |

### 响应

`Data` 是 `UserSummary[]`（可能直接数组或 `$values` 包装），每项是 `ID`、`Nickname`、`Signature`、`Avatar`、`AvatarRegion`、`Decoration`、`Verification` 等简表字段。不是 `{Supporters: [...]}` 包装。更多说明见 [`responses.md`](responses.md#45-支持者-contentsgetsupporters)。

## 6. 点赞/取消点赞（Contents/StarContent）

为指定作品点赞或取消点赞。

### 请求

```http
POST /Contents/StarContent
```

**请求体：**
```json
{
  "ContentID": "16a627bdb25f77131ba28018",
  "Category": "Experiment",
  "Status": true,
  "Type": 0
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `ContentID` | string | 内容 ID |
| `Category` | string | `"Experiment"` 或 `"Discussion"` |
| `Status` | bool | `true` 点赞，`false` 取消点赞 |
| `Type` | int | `0` 普通点赞，`1` 支持（需要绑定账号及足够金币） |

## 7. 删除实验（Contents/RemoveExperiment）

删除已发布的实验作品。

### 请求

```http
POST /Contents/RemoveExperiment
```

**请求体：**
```json
{
  "SummaryID": "16a627bdb25f77131ba28018",
  "Category": "Experiment"
}
```

## 8. 确认作品封面（Contents/ConfirmExperiment）

当前服务端没有 `Contents/UploadImage` 路由。`ConfirmExperiment` 接受 `SummaryID`、`Category` 和 `Image`；需要上传新文件时，还会读取请求中的二进制文件与 `Extension`，这不是把 Base64 图片放进 JSON 的接口。上传协议依赖客户端封装，调用前应核对 `ContentController.ConfirmExperiment` 与 `BaseController.UploadStorage`，不要照搬旧的 `UploadImage` 示例。

```http
POST /Contents/ConfirmExperiment
```

JSON 元数据至少包括 `SummaryID`（24 位作品 ID）、`Category`（如 `Experiment`）和 `Image`（图片序号）；仅作者或有权限的管理账号可以更新封面。

## 9. 获取用户资料页（Contents/GetProfile）

获取用户主页的展示内容，包括精选作品、热门作品、最新作品等。

### 请求

```http
POST /Contents/GetProfile
```

**请求体：**
```json
{
  "ID": "5d0f4390ca68215906d1a0fd"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `ID` | string | 用户 ID |

### 响应

```json
{
  "Status": 200,
  "Message": "",
  "Data": {
    "Experiments": {
      "Featured-Discussions": [],
      "Popular-Discussions": [],
      "Latest-Discussions": [],
      "Featured-Experiments": [],
      "Popular-Experiments": [],
      "Latest-Experiments": []
    },
    "Survey": null
  }
}
```

`Data.Experiments` 包含六个分类列表：精选讨论、热门讨论、最新讨论、精选实验、热门实验、最新实验。

## 11. 获取社区库内容（Contents/GetLibrary）

获取社区首页、讨论区、实验区等导航与板块内容。

### 请求

```http
POST /Contents/GetLibrary
```

**请求体：**
```json
{
  "Identifier": "Discussions",
  "Language": "Chinese"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `Identifier` | string | `"Homepage"` 首页，`"Discussions"` 讨论区，`"Experiments"` 实验区 ,`Workspace` 工作区 |
| `Language` | string | `"Chinese"` 或 `"English"` |

### 响应

返回社区库的板块结构，包含导航分类、板块列表等信息。
