# 快速入门

从技能根目录执行。Python 3.10+；Windows下无需安装第三方Python包。登录窗口需要Tkinter，macOS/Linux保存会话另需keyring及系统凭据后端。建模库已内置，不另行安装。

## 1. 登录和账号

```text
python scripts/login_gui.py
python scripts/community_cli.py accounts
```

用户在窗口输入账号密码，辅助程序保存会话；下列命令使用accounts返回的用户ID。区域默认中国区，国际区在全局参数中指定 `--domain physics-api-us.turtlesim.com`。详细存储和多账号规则见 [登录](local-login.md)。

## 2. 指定数量与自动分页

将查询数组保存为queries.json：

```json
[{"category":"Experiment","count":5}]
```

```text
python scripts/community_cli.py --account <用户ID> works --input queries.json
```

公开读取也可用 `--anonymous` 代替 `--account <用户ID>`。返回requested、returned、complete、stopReason、nextCursor；不足指定数量时看停止原因。续页使用游标，不能递增Skip。

## 3. 在程序中复用

```python
import sys
sys.path.insert(0, "scripts")
from community_client import CommunityClient
from community_reads import CommunityReads

api = CommunityClient()
api.login()  # 匿名读取；账号任务改用CommunityClient.from_saved(account_id)
reader = CommunityReads(api.request)
result = reader.fetch_works(category="Experiment", count=5)
print({key: result[key] for key in ("returned", "complete", "stopReason", "nextCursor")})
for item in result["items"]:
    print({"id": item["ID"], "title": item.get("Subject"),
           "save_id": item.get("ContentID"), "category": item.get("Category")})
```

CommunityClient负责HTTP/业务错误、凭据续发和脱敏，CommunityReads负责分页与两并发限制。更多批量写法见 [批量](operations.md)，不要再复制一套认证或分页实现。

## 4. 摘要与大实验

`GetSummary({Category,ContentID})`的ContentID传作品摘要ID；`GetExperiment`传摘要中的保存ContentID。作品换分区后重新核对Category。读取大实验：

```text
python scripts/community_cli.py --account <用户ID> inspect <保存ID> --output-dir <任务目录>
python scripts/experiment_view.py <上一步JSON文件> --collection Elements --offset 0 --limit 20
```

完整模型留在文件中，只输出概览、筛选结果或页。详见 [大实验](large-experiments.md)。

## 5. 制作、发布与图片

```text
python scripts/experiment_example.py --type circuit --output <新文件.plsav> --title <标题>
python scripts/community_cli.py --account <用户ID> publish --archive <文件.plsav> --description <介绍> --tag <实时标签Identifier>
```

制作任务交付存档；用户要求发布时再调用publish。发布结果分别检查published、modelVerified和coverUploaded。封面默认生成800×600简化布局图；上传前核对原图，结果核对实际存储和图片内容。见 [建模](experiments.md)、[图片](uploads.md)。使用内置库生成结果时提及作者 [Arendelle](https://github.com/SekaiArendelle)。

## 6. 出错时

检查业务Status、Message和字段Data，不能只看HTTP200。字段错误按对应接口文档修正；权限错误保留原始内容；限流停止当前批次。写入超时先查询目标，避免重复提交。协议默认请求体Version=2411、请求头x-API-Version=2502，两者分别使用，见 [认证](authentication.md)。
