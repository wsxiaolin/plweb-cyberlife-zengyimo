# 自动分页、批量接口与账号选择

通用版使用Python方法或CLI；下文JSON为已连接ChatGPT插件时的工具入参。两种入口共享接口规则，不把插件参数当作Python方法参数。

这些是辅助接口，不是新增的物理实验室服务端路径。本仓库在支持Python的本地或云端执行环境使用 `scripts/community_reads.py` 中的 `CommunityReads`。

## 硬限制

- 同时最多两个工作线程、两个社区网络请求。批量任务不能额外开子进程、任务或多份客户端来绕过限制。本地辅助程序共享两请求信号量并错开请求。多个进程/远程适配器也不得自行绕过这一任务上限。
- 每批评论合计最多 **1000 条**，作品或用户合计最多 **20 个**。限制对本批所有目标/查询的总和生效，不能把每个目标都当作独立额度。超限直接拒绝，不能自行拆批绕过上限。
- 单页 `Take` 不超过 **16**：实测更大的值会让服务端不返回、拖到超时，看起来像网络故障。翻页一律靠 `Skip`/游标，见 [实测补充](field-notes.md#1-列表分页take-大于-16-会让服务端挂起)。
- 接口接受多个对象 ID；不要把昵称、作品名当 ID。不得因可批量写入就推定用户授权了额外目标或操作。
- 遇限流/繁忙停止未开始的请求，不自动重试。写请求超时先核对实际状态；批量结果逐项记录成功、错误与未执行项，不能把部分成功说成全部成功。
- 用 `python scripts/community_cli.py accounts` 查看已保存账号；调用时明确 `--account 用户ID` 与区域。一批固定同一账号，不能在翻页中途切换。多账号间的密码、Token、AuthCode不得混用或回显。

## 指定数量与多个目标

### fetch_comments

```json
{"targets":[{"target_id":"用户ID","target_type":"User","count":30},{"target_id":"作品摘要ID","target_type":"Experiment","count":20}],"account_id":"已关联实验室账号ID"}
```

也接受单目标 `target_id,target_type,count,cursor?`。内部持续调用 GetComments，`CommentID` 传上一页末条 ID，`Skip=0`。服务端包含边界评论，因此按 ID 去重；不能盲删每页首条。只差一条时仍可请求边界与下一条，直到取得指定数量。每批全部目标 count 之和不超过1000。

### fetch_works

```json
{"queries":[{"category":"Experiment","user_id":"作者ID甲","count":10},{"category":"Discussion","user_id":"作者ID乙","count":10}]}
```

也接受单查询 `category,count,user_id?,tags?,languages?,sort?,cursor?`。内部循环 QueryExperiments，`From` 使用上一页末条摘要 ID，`Skip=0`。全部查询 count 之和最多20。这不是标题或作者名搜索。

两种接口均返回 `requested,returned,complete,stopReason,pages,nextCursor,items`（批量时位于各项 data）。只有 returned 达到 requested 时 complete 才为 true。耗尽、重复页、时间/页数限制或请求失败均如实返回部分结果与停止原因；继续时用 nextCursor。用户只要求“找某个对象”时仍遵守 finding.md 中有界查找规则，不转成无限遍历。

### read_community / write_community

保留单个 `body`，另支持同一路径的多个 `bodies`，两者必须选其一。例如批量读取用户：

```json
{"path":"/Users/GetUser","bodies":[{"ID":"用户ID甲"},{"ID":"用户ID乙"}]}
```

逐项先校验已核对路径与参数，再以两个工作线程处理。作品详情传摘要 ID 或保存 ID 的规则按 practical-api.md；评论写操作仍需明确目标、正文和授权。账号选择针对整批，不能通过 body 注入凭据或其他 ChatGPT 用户身份。

### get_available_tags

实时从 Authenticate.Data.ContentTags 返回 Identifier、Subject、Flags、Conflicts、Tips、Available 等字段及获取时间，不依赖静态标签表。`category?` 仅按 Flags 提供筛选线索；默认返回全部配置。本仓库每个CommunityReads实例固定一个账号。托管适配器如提供account_ids，最多20个且须按已授权账号隔离；这不是本仓库同名Python方法的参数。匿名会话可读取公开配置。

`Available` 为无效账号权限信号，忽略真假；`normalTagIdentifiers` 用于普通标签选择，`managedTagIdentifiers` 列出系统/管理/编辑限制标签。修改标签前读取实时配置，核对 Flags、Conflicts、Tips、系统类型与不可变规则；最终服从提交接口的权限判断。

## 大结果

通用版将完整大结果保存在当前用户任务目录，仅显示摘要和文件位置，实验分页用experiment_view.py。ChatGPT插件使用私人结果ID、24小时链接及read_batch_result(result_id,index?,offset?,limit?)切片。两种文件引用不互换；offset是归档切片，不是社区Skip。

## 通用版接入

```python
from community_reads import CommunityReads

# request 是本地安全登录辅助进程内的适配函数；不得打印或返回认证凭据。
client = CommunityReads(request)
comments = client.fetch_comments_batch([
    {"target_id": target_a, "target_type": "User", "count": 30},
    {"target_id": target_b, "target_type": "Experiment", "count": 20},
])
works = client.fetch_works_batch([
    {"category": "Experiment", "user_id": author_a, "count": 10},
    {"category": "Discussion", "user_id": author_b, "count": 10},
])
users = client.get_users([user_a, user_b])
exact_users = client.get_users_by_name(["完整昵称甲", "完整昵称乙"])
tags = client.get_available_tags()
```

本地CLI例子（从仓库根目录执行，输入文件不含密码或会话）：

```text
python scripts/login_gui.py
python scripts/community_cli.py accounts
python scripts/community_cli.py --account <用户ID> tags
python scripts/community_cli.py --account <用户ID> works --input <查询数组.json>
python scripts/community_cli.py --account <用户ID> comments --input <目标数组.json>
python scripts/community_cli.py --account <用户ID> batch --input <请求对象.json>
python scripts/community_cli.py --account <用户ID> inspect <保存ID甲> <保存ID乙> --output-dir <私人任务目录>
python scripts/experiment_view.py <实验JSON> --collection Elements --offset 0 --limit 20
```

works/comments文件分别是上文queries/targets的数组本身；batch文件形如`{"path":"/Users/GetUser","bodies":[{"ID":"用户ID"}],"write":false}`。写任务的`write:true`必须已有相应授权，不能仅靠这个开关推定授权。

适配函数固定正常 API 基址与当前账号，在进程内部读取安全存储、添加认证头、检查 HTTP 与业务 Status，并在响应头或 Authenticate 顶层续发凭据时更新安全存储。标签辅助方法只返回标签，不返回原始登录响应。登录仍按 local-login.md（通用版）或已有安全凭据流程处理；本模块不读取密码文件、不要求聊天密码，也不使用 physicslab.web。

`call_batch(path,bodies,write=False)` 支持已核对路径的通用批量操作；写操作必须显式 write=True 且已经得到任务授权，完成后仍逐项读回核验。它不会因为标为 write=True 就自动获得业务权限。

## 随附适配器

`CommunityClient.from_saved(account_id, domain=...)` 在进程内部读取会话，`CommunityReads(api.request)` 可直接接入。AI不得打印api内部认证状态。`python scripts/community_cli.py --help` 提供账号列表、移除会话、实时标签、批量请求、指定数量评论/作品和大实验概览入口；不会接受命令行密码。示例里的read_community/write_community属于可选托管工具名；在本仓库对应call_batch，不是额外服务端路由。

Messages/GetMessages虽然业务名称为读取，但首批可能改变聚合未读计数，与GetMessage、SendMessages一起放在write=True白名单。SendMessages单次和整批的目标用户数仍受20人总限额约束。

## 发布、图片和合作者

```python
from community_actions import CommunityActions
actions = CommunityActions(api)
result = actions.publish(archive_path, title="标题", description="介绍", tags=tag_identifiers)
avatar_result = actions.set_avatar(image_path)
cover_result = actions.set_cover(summary_id, image_path)
invitation = actions.invite_coauthor(summary_id, target_id)
accepted = actions.handle_invitation(message_id)
removed = actions.remove_coauthor(summary_id, target_id)
```

publish默认按模型生成并上传封面，亦可指定cover图片。run_batch接收1到20个`{action,args}`任务，支持publish/avatar/cover/remove/restore/invite/remove_coauthor/accept_invitation/set_featured/set_knowledge_base，最多两个工作线程。CLI使用actions --input任务数组.json；云端用run_actions，整批固定账号。

fetch_messages与fetch_supporters按Skip条数续页，最多20条并返回nextOffset。消息读取会更新未读提示，按收件箱任务调用。
