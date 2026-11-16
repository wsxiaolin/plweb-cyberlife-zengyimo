# 发布、图片与合作者接口

| 接口 | 请求字段 | 返回与用法 |
|---|---|---|
| `/Contents/SubmitExperiment` | `Summary, Experiment?, Workspace?, Request?` | 新建模型、修改摘要及申请封面上传；新建返回Data.Summary |
| `/Contents/SelectExperiment` | `Category, SummaryID, Status:boolean` | 添加/撤销精选，Status=true添加、false撤销；读回Tags |
| `/Contents/AcknowledgeExperiment` | `Category, SummaryID, Tag:"知识库", Status:boolean` | 仅用于添加/撤销知识库；作品不能带小作品标签，读回Tags |
| `/Contents/ConfirmExperiment` | `Category, SummaryID, Image, Extension` | 确认作品图片序号 |
| `/Users/RequestAvatar` | `Request:{Extension:".jpg",FileSize:-实际字节数}` | Data为上传凭据，留在程序内部 |
| `/Users/ConfirmAvatar` | `Avatar:integer` | 确认头像序号 |
| `/Contents/InviteCoauthor` | `Category, SummaryID, TargetID` | 发送合作邀请；消耗100金币 |
| `/Contents/RemoveCoauthor` | `Category, SummaryID, TargetID` | 移除合作者，读回Coauthors核验 |
| `/Messages/HandleInvitation` | `MessageID` | 接受邀请；不处理即忽略，没有拒绝字段 |
| `/Contents/VisitExperiment` | `Category, SummaryID` | 记录访问，Data为布尔值 |
| `/Messages/SendMessages` | `TargetID:[], Category, SummaryID:[], TemplateID` | 管理员发送服务端模板通知，每批目标最多20人 |
| `/Users/Logout` | `{}` | 退出服务端会话 |

上传优先使用 `CommunityActions.set_avatar/set_cover` 或 `upload_avatar/upload_cover`，完整流程由辅助代码执行。头像最多1MB，封面最多8MB，支持JPEG/PNG/WebP；上传凭据不返回聊天。详见 [上传流程](uploads.md)。
