# 调用示例

本页复用随附程序；完整参数见专题文档。Python示例从技能根目录运行，写入片段仅在用户已指定目标及操作时执行。

## Python

```python
import sys
sys.path.insert(0, "scripts")
from community_client import CommunityClient
from community_reads import CommunityReads
from community_actions import CommunityActions

api = CommunityClient.from_saved(account_id)
reader = CommunityReads(api.request)
actions = CommunityActions(api)
```

公开读取可替换为 `api=CommunityClient(); api.login()`。账号会话通过login_gui.py保存，不在示例中另行收集密码。

### 查找、评论和通知

```python
user = api.request("/Users/GetUser", {"Name": exact_nickname})["Data"]["User"]
works = reader.fetch_works(category="Experiment", user_id=user["ID"], count=10)
comments = reader.fetch_comments(target_id=summary_id, target_type="Experiment", count=30)
notifications = reader.fetch_messages(count=10)  # 有通知任务时读取，会改变未读提示
print({"works": works["returned"], "comments": comments["returned"]})
```

通知正文在GetMessages返回的条目及Templates里，GetMessage用于标记读取及处理相关状态，不返回正文。主页GetProfile只是精选/热门/最新展示，不是作者全部作品；完整历史候选用fetch_works按作者分页。

### 操作示例

```python
api.request("/Contents/StarContent", {"Category":"Experiment", "ContentID":summary_id,
                                    "Status":True, "Type":0})
api.request("/Messages/PostComment", {"TargetType":"Experiment", "TargetID":summary_id,
                                    "Content":comment_text, "Language":"Chinese"})
api.request("/Messages/RemoveComment", {"TargetType":"Experiment", "CommentID":comment_id})
actions.set_featured(summary_id, True)
actions.set_knowledge_base(summary_id, True)
```

这些是不同任务的独立片段，不是要求顺序执行。读取后核对对象及结果；删除作品使用 `actions.remove(summary_id, hide=False)`，隐藏用hide=True，恢复用actions.restore。金币支持Type=1消耗100金币，不能用Status=false退款。

### 其他原有接口

| 需求 | 复用入口或请求体 |
|---|---|
| 关注/取消关注 | `api.request('/Users/Follow', {'TargetID':user_id,'Action':1或0})` |
| 关系候选 | `api.request('/Users/GetRelations', {'UserID':user_id,'DisplayType':0或1,'Skip':0,'Take':20,'Query':''})` |
| 主页展示 | `api.request('/Contents/GetProfile', {'ID':user_id})` |
| 衍生作品 | `api.request('/Contents/GetDerivatives', {'Category':category,'ContentID':summary_id,'WithSummary':True,'Language':'Chinese'})` |
| 支持者 | `reader.fetch_supporters(summary_id,count=20)` |
| 导航板块 | `api.request('/Contents/GetLibrary', {'Identifier':'Homepage','Language':'Chinese'})` |
| 公共首页 | `api.get_start_page()` |
| 管理员模板通知 | `/Messages/SendMessages`的字段和副作用见[messages.md](messages.md) |

### 批量与大模型

```python
works = reader.fetch_works_batch([
    {"category":"Experiment", "user_id":author_a, "count":10},
    {"category":"Discussion", "user_id":author_b, "count":10},
])
views = reader.inspect_experiments([save_id], task_directory)
summary = api.request("/Contents/GetSummary", {"Category":category,"ContentID":summary_id})["Data"]
print({"id":summary["ID"],"title":summary.get("Subject"),"model_files":views})
```

批量方法返回每项结果，完整实验在私人任务文件中；页读取使用experiment_view.py。详情见 [批量](operations.md) 和 [大实验](large-experiments.md)。

## Node.js（匿名读取）

使用Node.js 18+自带fetch，无npm依赖；认证凭据只在闭包内使用，不打印整个认证包。账号任务使用已有安全会话适配器。

```javascript
const base = "https://physics-api-cn.turtlesim.com";
let token, authCode;
async function post(path, body) {
  const headers = {"Content-Type":"application/json", "x-API-Version":"2502"};
  if (token) headers["x-API-Token"] = token;
  if (authCode) headers["x-API-AuthCode"] = authCode;
  const response = await fetch(base + path, {method:"POST", headers,
    body:JSON.stringify(body), redirect:"error", signal:AbortSignal.timeout(30000)});
  const result = await response.json();
  if (!response.ok || result.Status !== 200)
    throw new Error(`HTTP ${response.status}; Status ${result.Status}; ${result.Message}`);
  token = response.headers.get("x-API-Token") || result.Token || token;
  authCode = response.headers.get("x-API-AuthCode") || result.AuthCode || authCode;
  return result;
}
async function main() {
  await post("/Users/Authenticate", {Login:null,Password:null,Version:2411,
    Device:{Identifier:"0d1a760b44023875d2123f2cfcb56dad",Language:"Chinese"}});
  const result = await post("/Users/GetUser", {Name:"<完整昵称>"});
  console.log({id:result.Data.User.ID, nickname:result.Data.User.Nickname});
}
main().catch(error => console.error(error.message));
```

需要持续分页或批量时使用[分页规则](finding.md)，整批最多两个并发；不要为每页再登录一次。

## curl（协议对照）

公共首页可直接读取：

```sh
curl --fail-with-body --max-time 30 https://physics-api-cn.turtlesim.com/Users
```

需要会话的请求体可对照各接口文档中的JSON；实际任务优先使用community_cli.py，使认证头由安全程序管理。自建curl适配器时，通过程序内部stdin注入配置并捕获响应，不把真实Token、AuthCode或密码写到命令参数、文件或聊天中；同时检查HTTP状态及JSON业务Status。
