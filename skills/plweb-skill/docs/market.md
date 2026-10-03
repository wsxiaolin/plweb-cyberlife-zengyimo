# 社区/资料页接口详解

社区接口提供社区首页、讨论区、实验区导航内容，以及用户资料页展示数据。所有接口均需认证。

## 1. 获取社区库（Contents/GetLibrary）

获取社区各板块的导航与结构内容，是社区浏览的入口接口。

### 请求

```http
POST /Contents/GetLibrary
```

**请求体：**
```json
{
  "Identifier": "Homepage",
  "Language": "Chinese"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `Identifier` | string | 板块标识符 |
| `Language` | string | `"Chinese"` 或 `"English"` |

### Identifier 取值

| 值 | 说明 |
|----|------|
| `"Homepage"` | 社区首页 |
| `"Discussions"` | 讨论区 |
| `"Experiments"` | 实验区 |

### 响应

```json
{
  "Status": 200,
  "Message": "",
  "Data": {
    "ID": "<library-id>",
    "Identifier": "Discussions",
    "Subject": "讨论区",
    "Language": "Chinese",
    "IsNavigation": false,
    "IsDevelopment": false,
    "Blocks": [
      { "Type": 0, "Header": "最新讨论", "TargetLink": null,
        "FetchSource": "...", "FetchConfiguration": {}, "Permission": null,
        "Locations": [], "Summaries": [] }
    ]
  }
}
```

### Library 字段说明

| 字段 | 说明 |
|------|------|
| `Data.Identifier` | 当前板块标识符 |
| `Data.Language` | 语言 |
| `Data.Subject` | 页面标题 |
| `Data.IsNavigation` / `IsDevelopment` | 导航页及开发内容标记 |
| `Data.Blocks` | 多态内容块数组，块有 `Summaries`、`Locations` 和配置字段 |

不同 block 类型会带不同扩展字段；没有固定 `Categories` 或 `Announcements` 顶层字段。字段详情见 `LibraryBlock` 及派生类型。完整解析说明见 [`responses.md`](responses.md#8-用户资料页与社区库)。

## 2. 获取用户资料页（Contents/GetProfile）

获取用户主页的展示数据，包括该用户的精选/热门/最新作品。

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

### Experiments 字段说明

`Data.Experiments` 包含六个分类列表，每个列表为 `ExperimentSummary` 数组：

| 字段 | 说明 |
|------|------|
| `Featured-Discussions` | 精选讨论 |
| `Popular-Discussions` | 热门讨论 |
| `Latest-Discussions` | 最新讨论 |
| `Featured-Experiments` | 精选实验 |
| `Popular-Experiments` | 热门实验 |
| `Latest-Experiments` | 最新实验 |

每个列表中的元素结构与 `QueryExperiments` 返回的 `ExperimentSummary` 相同。

`Data` 的确切字段说明见 [`responses.md`](responses.md#8-用户资料页与社区库)。

## 3. 获取社区首页（GET /Users）

获取社区首页的初始化数据，无需认证（匿名可访问）。

### 请求

```http
GET /Users
```

### 响应

```json
{
  "Status": 200,
  "Message": "",
  "Data": { "ID": "<library-id>", "Identifier": "Homepage", "Subject": "首页", "Language": "Chinese", "IsNavigation": true, "IsDevelopment": false, "Blocks": [] }
}
```

`Data` 是与 `Contents/GetLibrary` 相同的 `Library` 类型，不是含 `Version`/`Announcement`/`Homepage`/`Library` 的额外包装。

## 当前控制器中不存在的旧路径

`Contents/GetDiscussion`、`Contents/GetAnnouncement` 和 `Notifications/Get` 不在当前 `Quantum API/Controllers` 路由中，不要调用这些旧文档路径。讨论作品通过 `Contents/QueryExperiments`、`Contents/GetSummary` 和 `Contents/GetExperiment`（类别设为 `Discussion`）读取；收件箱消息/通知使用 `Messages/GetMessages`。这些端点的 `Data` 结构见 [`responses.md`](responses.md)。
