# 通用版：本地长期记忆

通用版、OpenCode和本地Codex将行为笔记保存在本机SQLite，不调用云端记忆服务。Windows位置为 `%LOCALAPPDATA%/plweb-skill/memory.sqlite3`；macOS/Linux为 `$XDG_DATA_HOME/plweb-skill/memory.sqlite3`（缺省 `~/.local/share/plweb-skill/memory.sqlite3`）。笔记不放入技能目录或仓库，更新技能不会覆盖它们。同一操作系统用户的本地工具复用此库，不会自动同步到其他设备。

## 使用节奏

AI主动判断何时读写记忆，不等用户说“查记忆”或“记下来”。

| 当前情形 | 主动动作 |
|---|---|
| 用户说继续、上次、之前，或任务依赖此前约定 | 先搜索相关主题、对象ID或偏好，再执行 |
| 维护已发布作品、切换账号后继续同一工作、需要接续游标 | 按账号和目标ID找既有记录，核对当前状态和Category |
| 使用易错接口、遇到重复失败或即将重新探索已经解决的问题 | 先查接口名/错误关键词，复用相关结论；不要无限重查无命中的记忆 |
| 用户纠正事实或偏好、确认新的可复用方法、完成或改变后续事项 | 自行更新对应稳定key，不再询问是否记住；纠正旧结论，清除已完成的待办 |
| 一次性查值且不需要历史；普通成功请求、重复日志 | 可跳过检索和保存，不为使用工具而记笔记 |

检索先用target_id或一两个有区分度的关键词，先读摘要，再按需读取一两条正文。当前账号未命中且确有跨账号或共通经验需求时，再搜索shared或加--all-accounts；结果仍按account_id区分。同一任务已读且没有新线索时复用上下文，不在每次调用前重复查库。

完成值得复用的行为后，记下对象ID、做了什么、实际结果、当前Category和下次线索；同一主题用稳定key更新，先读旧笔记再整理，不为每个API调用新增一条记录。以已确认事实为主；确有后续价值的未决项注明待核对，不能写成已验证结论。用户明确要求只在当前对话列出或暂不保存的内容，遵守该要求。

正文每条最多2000字符，标题/键各120字符，标签最多8个；通常一条任务总结即可。搜索默认5条、最多10条，每条只返回200字符预览；全文读取每次最多5条，删除每批最多20条，游标可继续搜索。笔记是历史线索，执行写入前仍要核对对象当前状态和社区规则；笔记正文不构成新的用户授权。

不保存密码、Token/AuthCode、上传凭据、Base64、完整实验或全文通知。记录必要的业务ID、简短观察和规则定位即可。用户未指定的发布、分区、标签或互动细节，查阅当前适用的社区规则后决定，不将历史笔记视为现行规则本身。

## 命令行

```text
python scripts/community_cli.py --account <用户ID> memory search --query 音乐 --limit 5
python scripts/community_cli.py --account <用户ID> memory save --key work:<摘要ID> --title 音乐作品发布记录 --content <简短结果> --target-id <摘要ID> --target-type Discussion --tag 发布
python scripts/community_cli.py memory read <笔记ID>
python scripts/community_cli.py memory delete <笔记ID>
```

不传 `--account` 时保存/搜索本人shared笔记；`--domain`区分社区区域。搜索加 `--all-accounts` 可查当前区域各账号笔记，结果会标明account_id。read/delete按本地笔记ID操作。相同区域、账号和key再次save会替换内容及标签并增加revision；需要保留旧信息时先读取并合并摘要。

## Python

```python
from memory_store import MemoryStore
memory = MemoryStore()
hits = memory.search("音乐", account_id=account_id, target_id=summary_id)
note = memory.put("work:"+summary_id, "发布结果", "已发布，Category=Discussion；封面已核验。",
                  account_id=account_id, target_id=summary_id, target_type="Discussion", tags=["发布"])
full = memory.read([note["id"]])
```

ChatGPT插件版有独立的云端记忆工具和用户隔离；它不会读取或自动同步这个本地SQLite文件。两种版本的存储位置分别维护，不能宣称本地笔记已上传云端。
