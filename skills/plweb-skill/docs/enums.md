# 枚举值完整参考

物理实验室 AR API 中使用多种枚举值来标识内容类型、排序方式、标签等。以下是完整参考。

## 1. Category（内容分类）

用于 `QueryExperiments`、`GetSummary`、`GetExperiment`、`Star`、`PostComment` 等接口。

| 值 | 说明 |
|----|------|
| `"Experiment"` | 实验作品 |
| `"Discussion"` | 讨论帖 |

## 2. Sort（排序方式）

用于 `QueryExperiments` 的 `Query.Sort` 字段。

| 值 | 说明 |
|----|------|
| `0` | 最新发布（按发布时间降序） |
| `1` | 最热门（按点赞数降序） |

## 3. Star Type（互动类型）

用于 `Contents/StarContent` 接口的 `Type` 字段。

| 值 | 说明 |
|----|------|
| `0` | 普通点赞（Star） |
| `1` | 支持（Support；可能消耗金币，且不能支持自己的作品） |

是否添加或取消点赞由布尔字段 `Status` 控制：`true` 添加，`false` 取消。

## 4. Follow Action（关注操作）

用于 `Users/Follow` 接口的 `Action` 字段。

| 值 | 说明 |
|----|------|
| `1` | 关注 |
| `0` | 取消关注 |

## 5. DisplayType（关系列表类型）

用于 `Users/GetRelations` 接口的 `DisplayType` 字段。

| 值 | 说明 |
|----|------|
| `"Follower"` | 粉丝列表（关注了该用户的用户） |
| `"Following"` | 关注列表（该用户关注的用户） |

## 6. Library Identifier（社区板块标识符）

用于 `Contents/GetLibrary` 接口的 `Identifier` 字段。

| 值 | 说明 |
|----|------|
| `"Homepage"` | 社区首页 |
| `"Discussions"` | 讨论区 |
| `"Experiments"` | 实验区 |

## 7. Language（语言）

用于 `Device.Language`、`GetLibrary` 的 `Language` 字段。

| 值 | 说明 |
|----|------|
| `"Chinese"` | 中文 |
| `"English"` | 英文 |

## 8. Tags（标签）

用于 `QueryExperiments` 的 `Query.Tags` 字段筛选。常见标签包括：

| 标签 | 说明 |
|------|------|
| `"精选"` | 精选作品 |
| `"官方"` | 官方发布 |
| `"教程"` | 教程类作品 |
| `"转载"` | 转载作品 |

> 标签列表可能随版本更新而变化，可通过 `GetLibrary` 接口获取当前可用标签。

## 9. Message CategoryID（消息分类）

用于 `Messages/GetMessages` 的 `CategoryID` 字段。

| 值 | 说明 |
|----|------|
| `0` | 全部消息 |
| `1` | 评论相关 |
| `2` | 点赞相关 |
| `3` | 关注相关 |
| `4` | 系统通知 |

> 具体分类 ID 可能随版本变化，建议先用 `0` 获取全部消息后查看 `CategoryID` 字段。

## 10. Experiment Type（实验类型）

实验摘要中的 `Type` 字段。

| 值 | 说明 |
|----|------|
| `0` | 电学实验（Circuit） |
| `1` | 天体物理实验（Celestial） |

## 11. Avatar Size Category（头像尺寸）

用于获取头像图片 URL 的尺寸参数。

| 值 | 说明 |
|----|------|
| `"small.round"` | 小圆头像（列表用） |
| `"thumbnail"` | 缩略图 |
| `"full"` | 完整图 |

## 12. Version（客户端版本）

用于登录接口的 `Version` 字段，格式为 `YYMM`。

| 值 | 对应版本 |
|----|---------|
| `2411` | 2024 年 11 月 |
| `2406` | 2024 年 6 月 |
| `2311` | 2023 年 11 月 |

> 版本过旧可能被拒绝登录，建议使用较新的版本号。
