# 勘误与实测补充（以本仓库实测为准）

> 本目录文档复制自 [NetLogo-Mobile/plweb-skill](https://github.com/NetLogo-Mobile/plweb-skill)，
> 是社区 API 的官方技能文档。以下是本仓库（plweb-cyberlife）在 2026-09-25 实测中发现的
> 与文档不一致之处。**Agent 优先按本勘误行事。**

## 1. 已实测确认的关键差异

| 文档所述 | 实测行为 | 影响 |
|---------|---------|------|
| 评论接口 `Contents/GetComments`（ContentID+Category） | 实际路径 **`Messages/GetComments`**，请求体 `{"TargetID", "TargetType", "CommentID", "Take", "Skip"}`，TargetID 用作品列表的 **ID 字段**（不是 ContentID） | 读评论 |
| 发评论 `Contents/PostComment` | 实际路径 **`Messages/PostComment`**，请求体 `{"TargetID", "TargetType", "Language", "ReplyID", "Content", "Special"}`，**直接请求 Contents/PostComment 会导致服务端挂起** | 发评论 |
| 删除评论 `Contents/RemoveComment` | 实际路径 **`Messages/RemoveComment`**，请求体 `{"TargetType", "CommentID"}` | 删评论 |
| `Users/GetRelations` 无参 | 必须传 **`{"UserID", "DisplayType"(0粉丝/1关注), "Skip", "Take", "Query": null}`** | 关注列表 |
| `Users/ModifyInformation` 请求体 `{"Target": ...}` | 实际为 **`{"Field": "Signature", "Target": ...}`**（缺 Field 报 `Input.Field.Missing`）；`Target` 为空字符串同样报错（可用单个空格） | 改签名 |
| 列表接口 `Take` 任意值 | **`Take > 16` 会使服务端挂起**（无响应直到超时），必须用 `Skip` 翻页、每页 ≤16 | 所有列表 |
| `Notifications/Get` | 偶发挂起（即使参数正确），建议单次快速尝试、失败即放弃（站内信 `Messages/GetMessages` 已覆盖主要通知） | 系统通知 |
| `Users/Rename` | 请求体为 `{"Target": 新昵称}`；与当前昵称相同会报 `Nickname.Duplicated` | 改名 |
| `Contents/RemoveExperiment`（`{"ContentID","Category"}`） | 实测需 **`{"SummaryID","Category","Hiding":true,"Reason":"..."}`** 且必须带 **`x-API-Version` 请求头**（如 2411），否则报 `User.Not.Allowed`/`Input.Field.Missing`。隐藏后作者自己仍可见、他人不可见 | 删作品 |
| 手拼 JSON 提交讨论帖 | 实测**被拒**（`Input.Field.Invalid`）。可靠通道是 **physicslab 库**（其 Summary 含 `Visibility/Settings/Multilingual` 等字段）。且**完全空的实验（0 元件）会 403**——讨论帖也要至少一个元件（我们内置"电池+开关+灯"小场景） | 发讨论帖 |

## 2. 发布作品（实验/讨论）的底层通道

发布不走常规 JSON 接口，而是：

```
POST /Contents/SubmitExperiment
Headers: Content-Type: gzipped/json, Accept-Encoding: gzip,
         x-API-Version: <Summary.Version，如 2503>
Body: gzip( JSON({"Summary": {...}, "Workspace": {...}}) )

然后：
POST /Contents/ConfirmExperiment
Body: {"SummaryID": <新ID>, "Category": "Experiment"|"Discussion",
       "Image": <计数>, "Extension": ".jpg"}
```

- 讨论（Discussion）与实验共用同一提交通道，Summary 的 `Category` 设为 `"Discussion"`
- 实验的 Workspace 是序列化电路模型；physicslab 库已封装好（`tools/experiment_gen.py`）
- 讨论帖的 Workspace 可以是天体场景（如中秋帖用的地月系）或简单电路小场景（不能为空）

## 3. 结构提醒

- 列表响应的数组在 `Data["$values"]`
- 作品列表条目同时有 `ID`（summary，评论/详情用）与 `ContentID`（workspace，取实验数据用）
- 时间戳多为 epoch 毫秒
- 全程需要 `ssl` 关闭证书校验（域名与证书不匹配）
