# 常用枚举值参考

物理实验室 AR API 中使用多种枚举值来标识内容类型、排序方式、标签等。以下列出调用所需的常用值。

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
| `0` | 最新列表；实际时间字段与排序以响应为准 |
| `1` | 热门列表 |
| `2` | 随机列表 |

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
| `0` | 粉丝列表（Followed） |
| `1` | 关注列表（Following） |

中国区2026-10-31实测：字符串Following及任意无效字符串可返回200但实际回退到0，不能作为可用枚举。扩展整数见 responses.md。

## 6. Library Identifier（社区板块标识符）

用于 `Contents/GetLibrary` 接口的 `Identifier` 字段。

| 值 | 说明 |
|----|------|
| `"Homepage"` | 社区首页 |
| `"Discussions"` | 讨论区 |
| `"Workspace"` | 工作区导航 |

## 7. Language（语言）

用于 `Device.Language`、`GetLibrary` 的 `Language` 字段。

| 值 | 说明 |
|----|------|
| `"Chinese"` | 中文 |
| `"English"` | 英文 |

## 8. Tags（标签）

用于 `QueryExperiments` 的 `Query.Tags` 字段筛选。通过 `CommunityReads.get_available_tags()` 读取 `Authenticate.Data.ContentTags` 的实时配置；不保存静态标签快照。GetLibrary是导航板块接口，不能据此承诺得到完整标签。完整规则见 [实时标签](practical-values.md#6-实时标签配置)。

## 9. Message CategoryID（消息分类）

用于 `Messages/GetMessages` 的 `CategoryID` 字段。

| 值 | 说明 |
|----|------|
| `0` | 全部消息 |
| `1` | 系统邮件（Letter） |
| `2` | 关注、社交（Attention） |
| `3` | 评论与回复（Comment） |
| `4` | 作品通知（Experiment） |
| `5` | 管理记录（Management） |

> 与 responses.md 的分类保持一致；正文仍依模板解释。GetMessages首批读取可能清零聚合未读计数，不为验证枚举擅自读取收件箱。

## 10. Experiment Type（实验类型）

实验摘要中的 `Type` 字段。

| 值 | 说明 |
|----|------|
| `0` | 电学实验（Circuit） |
| `3` | 天体物理实验（Celestial） |
| `4` | 电磁实验（Electromagnet） |

## 11. 图片样式后缀

静态图片路径以实际序号的 `.jpg` 结尾；网页可追加 `!block`、`!tiny.round`、`!small.round` 等处理样式。这些不是API枚举参数，也不是上传Extension，见 [图片路径与上传](uploads.md)。

## 12. 协议版本

认证请求体Version=2411，请求头x-API-Version=2502；不要按日期猜值，见 [认证](authentication.md#协议版本)。
