# 可填值与标签

## 1. 分类与目标

| 字段 | 值 | 说明 |
|---|---|---|
| 作品 Category | `Experiment`、`Discussion` | 实验区、讨论区（黑洞） |
| 评论 TargetType | `User`、`Experiment`、`Discussion` | 用户留言板、实验评论、讨论评论 |
| MoveCategory.Target | `Experiment`、`Discussion` | 目标分区 |
| GetLibrary.Identifier | `Homepage`、`Discussions`、`Workspace` | 首页、讨论页、工作区导航；以返回的非空Library为准 |


## 2. 语言

`Chinese`、`English`、`ChineseTraditional`、`German`、`French`、`Japanese`、`Italian`、`Polish`、`Spanish`、`Ukrainian`。

传 API 名称，不传 zh-CN 等浏览器语言代码。模板某语言字段为 null 时回退到可用语言或原文本。

## 3. 查询、关系与操作值

| 字段 | 可填值 | 语义与限制 |
|---|---|---|
| Query.Special | `null`、`Support`、`Star` | null为普通列表；Support为金币支持列表，Star为收藏列表 |
| Query.Sort | `0` | 默认排序；不要把不同分区、区域和版本的数字排序含义混用 |
| Query.Sort | `1`、`2` | 1热门、2随机 |
| GetRelations.DisplayType | `0`、`1` | 粉丝、关注 |
| GetUser返回Relation | `0`、`1`、`2`、`3` | 无关注、自己关注对方、对方关注自己、互关；它是返回值，不是DisplayType |
| Follow.Action | `1`、`0` | 关注、取消关注 |
| Block.Action | `1`、`0` | 屏蔽、解除；关系副作用由后端决定 |
| StarContent.Type | `0`、`1` | 收藏、金币支持 |
| StarContent.Status | `true`、`false` | 收藏开关；不能用false退款支持 |
| PostComment.Special | `null`、`Reminder` | 普通评论、用户警告 |
| PostComment.Special | `Locked`、`Anonymous` | Locked锁定评论、Anonymous匿名评论；按返回Flags读取实际效果 |
| ModifyInformation.Field | `Signature` | 修改签名；其他资料字段需有可靠参数依据 |

分页采用正数 Take，常用20。不要硬编码“负数都取绝对值”，也不要把库中的-101当作通用可用值。

## 4. 通知类别

| CategoryID | 分类 |
|---|---|
| 0 | 全部 |
| 1 | 系统邮件 |
| 2 | 关注、社交及相关订阅通知 |
| 3 | 评论与回复 |
| 4 | 作品通知 |
| 5 | 管理记录 |

分类名称不是完整事件枚举，正文应依TemplateID和Fields解释。Unread为0表示未读取，非零为读取时间戳；Handled不等同Unread。

## 5. 身份与任命

用户 Verification 中出现的身份值：`Oldtimer`、`Volunteer`、`Junior`、`Emeritus`、`Editor`、`Administrator`、`Banned`；普通身份还可能为空或null。

任命使用Volunteer、Junior、Editor、Emeritus。管理员可任命编辑。封禁清除身份，解封不恢复；封禁天数见permissions.md。

## 6. 实时标签配置

标签不再维护静态快照。选择、校验或编辑标签之前，调用 `get_available_tags`，或通用版 `CommunityReads.get_available_tags()`，从正常 Authenticate 响应中的 `Data.ContentTags` 读取当前完整配置。失败时说明错误，不恢复旧表或自行编造标签。

发请求使用 `Identifier`，`Subject` 是多语言显示名；返回时保留 `Tips`、`ModeratorTips`、`Available`、`Flags`、`Conflicts`。Flags/Conflicts 可能是 `$values` 包装数组，辅助接口会规范为数组。不要把显示名或旧别名当作可新增 Identifier。

`Available` 是无效的账号权限信号，忽略其true/false；不能因它为false而拒绝“交流”等普通标签。辅助接口直接返回 `availableIsPermission=false`、普通标签 `normalTagIdentifiers` 与限制标签 `managedTagIdentifiers`，方便模型选择。分类筛选保留Circuit/Celestial等无显式分区标记的类型标签，仍需按实际实验类型、Conflicts和Tips匹配组合，保留正确的系统类型标签。普通 SubmitExperiment 即使返回200，也不会新增“精选”或“知识库”，编辑后须读回Tags核对。

账号会话、公开配置与不同筛选分区可能有差别。一次批次读取一次相关配置即可，不为每个对象重新登录；不得用静态表替代失败的实时读取。详见 [自动分页与批量接口](operations.md)。

## 来源

- 服务端公开配置：Authenticate.Data.ContentTags。
- [网页设备标识](https://github.com/NetLogo-Mobile/plweb2/blob/85ca269a6e1bf1ecc353882f0e38217a2b0c24be/src/services/api/getDevice.ts)。
- [网页类型与枚举线索](https://github.com/NetLogo-Mobile/plweb2/blob/85ca269a6e1bf1ecc353882f0e38217a2b0c24be/src/pl-serve-type-main/type/main.ts)。客户端类型可以陈旧，不能覆盖服务端返回的校验结果。
