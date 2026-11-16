---
name: plweb-skill
description: 通过物理实验室 AR / Physics Lab 社区 API 查询作品、用户、评论和通知，发布、互动及管理作品，并使用内置库制作电路、天体、电磁和音乐实验。
---

# 物理实验室社区

使用社区 HTTP 接口和随附辅助程序完成任务；接口参数、模型数据和结果都以实际返回为准。

## 运行环境

本技能用于本地、OpenCode、本地Codex或具有Python执行能力的环境。从技能根目录运行 `python scripts/community_cli.py --help`。首次账号登录运行 `python scripts/login_gui.py`，由用户在简单窗口输入账号密码；后续复用加密会话。`accounts`列出账号，每批固定 `--account 用户ID`。见 [登录与多账号](docs/local-login.md)。

建模使用本包 `vendor/physicslab`，无需另行下载库。长期记忆使用本机SQLite，见 [本地记忆](docs/memory.md)；本技能不会将笔记上传云端。ChatGPT插件有独立工具版入口，不将其云端工具当作本地Python方法。

封装方法没有覆盖全部接口。**缺少现成方法或子命令时不要回复"做不到"，直接按文档自己发请求**（换头像、改签名、签到、留言板评论、隐藏作品等单个读写操作都适用），见 [按文档自行执行](docs/by-hand.md)；现场实测的坑见 [实测补充](docs/field-notes.md)。

## 通常怎样完成任务

1. 主动判断是否需要记忆，不等用户提醒：继续之前的任务、维护已有作品、涉及用户纠正/偏好、复用接口经验或遇到重复错误时，先检索相关本地笔记。单次独立查值且无历史依赖时可跳过。再依据链接、ID、作者、完整昵称或通知核对对象；完整昵称用 `GetUser(Name)`，作品名和模糊昵称在有界候选中匹配。
2. 优先使用 `CommunityClient`、`CommunityReads`、`CommunityActions` 的分页、图片和发布方法。已有明确授权时继续执行任务范围内的操作，不重复请求同一确认。
3. 用户未指定的发布、分区、标签和互动细节，先查阅当前适用的社区规则（相关导航、公告或规则作品），再据此决定；不凭旧笔记编造规则。
4. 同时检查 HTTP 状态、JSON 的 `Status/Message/Data` 和读回结果。批量任务逐项报告完成、失败及未执行；保留真实错误，隐藏凭据。写入超时先核对已有结果，避免重复发布或扣币。确认可复用经验、收到用户纠正或产生跨对话后续事项时，自行用本地memory命令更新同主题笔记，无需另问是否记住；普通请求流水不记录。
5. 现成方法不够用时按文档自行调用，不臆造路径和字段：`405/404`是路径不存在、`Input.Field.Missing`是字段问题、`User.Not.Allowed`可能是临时限流而非封号。自行调用同样受请求间隔、并发上限、写后读回和凭据脱敏约束，见 [按文档自行执行](docs/by-hand.md)。

## 必须保持一致的约定

- **账号和区域**：中国区 `physics-api-cn.turtlesim.com`，国际区 `physics-api-us.turtlesim.com`；会话按账号与区域隔离。密码仅交给登录程序，Token/AuthCode由辅助程序内部管理，不输出到聊天。
- **三类 ID**：作品摘要 `ID` 用于社区操作，虽然 `GetSummary` 的入参名叫 `ContentID`，这里仍传摘要ID；`GetExperiment` 才传摘要里的保存 `ContentID`。插件 `plfile_…` 文件ID是上传暂存文件，不能拿ChatGPT附件ID替代。
- **分页和数量**：作品 `From=末条摘要ID, Skip=0`；评论 `CommentID=末条评论ID, Skip=0`，按ID去重。通知和支持者使用Skip条数续页。每批评论总数≤1000、作品或用户总数≤20，最多两个工作线程和两个并发请求；限流停止，不自行拆批绕过限制。
- **大实验**：先概览、再分页或在代码中筛选，完整StatusSave留在文件中。不要将一页样本当作全量分析。
- **图片和发布**：核对原图内容与字节完整性，使用完整上传流程；图片目标存在且核验通过后才确认序号。新建发布需要完整模型存档，默认生成800×600简化布局封面。制作完成、发布成功与仿真验证是不同结果，分别报告。
- **标签与管理**：实时读取标签；`Available`不是有效账号权限信号。保留系统类型及原有限制标签。精选仅用 `SelectExperiment`，知识库仅用 `AcknowledgeExperiment` 且 `Tag="知识库"`；知识库添加前移除“小作品”。隐藏可恢复，删除从服务器直接移除。
- **通知与移动**：通知可提供用户、作品和管理事件线索。作品移动分区后旧Category可能失效，核对当前分区后继续，不能据一次查询失败认定已删除。
- 确认消息已读用GetMessage，MessageID取消息条目.ID，读回Unread非零确认。回复指定用户时，ReplyID取原评论.UserID，正文保留`回复@完整昵称: `，TargetID保持作品摘要ID或留言板用户ID。辅助层会核对当前昵称并补齐@引用。批量调用这两项使用write=True。

## 按任务查阅

| 任务 | 优先入口 | 需要的资料 |
|---|---|---|
| 首次使用、认证 | `login_gui.py` | [快速入门](docs/quickstart.md)、[安全登录](docs/local-login.md)、[认证字段](docs/authentication.md) |
| 找用户或作品 | `CommunityReads.fetch_works`、`GetUser` | [查找与分页](docs/finding.md)、[用户](docs/users.md)、[内容](docs/content.md)、[社区与主页](docs/market.md) |
| 指定数量或批量 | `CommunityReads` | [批量方法、参数和额度](docs/operations.md) |
| 读实验模型 | `inspect_experiments`、`experiment_view.py` | [大实验处理](docs/large-experiments.md) |
| 做实验、生成音乐、发布 | `experiment_example.py`、`music_experiment.py` / `CommunityActions.publish` | [建模与发布](docs/experiments.md)、[音乐](docs/music.md) |
| 头像与封面 | `CommunityActions.set_avatar/set_cover` | [图片格式、传输、索引与验证](docs/uploads.md) |
| 没有现成方法（换头像、签到、改签名、隐藏等） | 按文档自行调用接口 | [自行执行与示例](docs/by-hand.md)、[字段速查](docs/interface-notes.md) |
| 接口行为和文档对不上 | 按较晚的实测判断 | [实测补充](docs/field-notes.md) |
| 富文本、字体样式、用户及作品引用 | 在文本字段直接使用标签 | [颜色、字号、组合排版与摘要ID引用](docs/rich-text.md) |
| 评论、回复、警告、通知 | `CommunityReads`、通用请求 | [评论](docs/comments.md)、[通知](docs/messages.md) |
| 合作者、精选、知识库、隐藏/删除、封禁 | `CommunityActions` | [操作权限与结果](docs/permissions.md)、[字段速查](docs/interface-notes.md)、[完整业务参数](docs/practical-api.md) |
| 解析返回值或选择枚举/标签 | 按响应结构取字段 | [响应结构](docs/responses.md)、[可填值与实时标签](docs/practical-values.md)、[枚举](docs/enums.md) |
| 长期记忆 | `memory_store.py` / `community_cli.py memory` | [本地SQLite笔记与有界检索](docs/memory.md) |
| 编写调用程序 | 复用随附辅助程序 | [Python / Node.js / curl 示例](docs/examples.md) |

建模和音乐使用随包内置库，不从作者GitHub或PyPI另取。交付该库生成的结果时，提及作者 [Arendelle](https://github.com/SekaiArendelle) 并附此链接；详细API及MIT许可随库提供。
