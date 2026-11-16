# 大实验：概览、分页与文件处理

**禁止直接把 GetExperiment 原始响应、StatusSave 或 CameraSave 全文输出给聊天模型。** 作品可能有大量元件、导线和长属性；截取原文并不能保证 JSON 完整，也不能代替对整个实验的分析。

## ChatGPT插件：云端归档和分页

本节用于已连接插件的对话；通用版使用下一节的本地Python方法。

1. 先读摘要得到保存 `ContentID`，不要混用摘要 ID。调用 `inspect_experiments({content_ids:[保存ID,...],account_id?})`，每批最多20个、最多两个社区请求并发。
2. 默认返回实验类型、标题、各集合实际数量、元件类型分布、最多两个小样本、`resultId` 和私人文件链接。完整存档写入文件，不进入工具上下文。`read_community` 的 `/Contents/GetExperiment` 也默认走这个概览流程。
3. 按概览中的集合名称调用 `read_experiment_page({result_id,collection:"Elements",offset:0,limit:20,fields:["Identifier","ModelID","Position"]})`。导线用 Wires；其他类型按实际返回集合名称处理。offset 是已归档文件中的切片，**不是社区 Skip**。
4. 根据 nextOffset 继续，只取当前任务需要的范围与字段。长字段、深层对象、数组样本有显式截断/省略标记；需要未裁剪的值时在完整私人文件中处理，不把预览当原始完整数据。
5. 在线结构预处理上限为8MB。超过上限时只归档完整响应并返回 `file_only`；不把截断片段冒充模型，不报告未核实的数量。让云端 Work/本地安全辅助程序下载文件并运行下面的本地分析。若在线归档也因大小或环境限制失败，明确说明，使用安全本地适配器直接保存。
6. 私人归档按 ChatGPT 用户隔离、24小时有效，账号凭据不会放进链接。需要多个实验时，逐项报告解析成功、仅文件及失败，不把某一页代表整个实验。

## 本地 / OpenCode / 通用版

在安全辅助进程内部使用 `CommunityReads.inspect_experiments(content_ids, output_dir)`；它内部读取并保存响应，给 AI 的结果只有概览与文件路径。传入任务工作目录，不能写入技能目录、公共同步目录或覆盖用户原件。

```python
views = client.inspect_experiments([content_a, content_b], task_cache_dir)
```

随后在代码进程里运行（路径为上一步返回的文件）：

```text
python scripts/experiment_view.py <实验JSON路径>
python scripts/experiment_view.py <实验JSON路径> --collection Elements --offset 0 --limit 20 --fields Identifier ModelID Position
python scripts/experiment_view.py <实验JSON路径> --collection Wires --offset 20 --limit 20
```

不要用 Read/Get-Content/cat 把该 JSON 全文交给模型。Python 帮助脚本解析发生在进程内，只输出受限概览或页。更大文件可在本地编写流式统计/筛选程序，将“找到目标元件、关联导线、汇总参数”等工作留在代码中完成，仅把摘要送回模型。

## 分析结论的范围

先用全量数据在代码中统计和筛选，再读取相关元件及其关联导线。仅看前20个元件不能断言整个实验没有某种结构；未知/未解析的集合不能当作空集合。生成图或解释电路时，明确哪些关系已从全量导线索引核实，哪些仍是抽样观察。

本仓库已随附scripts/experiment_view.py和scripts/community_reads.py；get_helper_script是ChatGPT插件的脚本分发入口，不要求用户调用不存在的工具。

本仓库Python实现仍需在内存解析完整响应，默认本地文件处理上限256MB，并非任意大小的流式解析。在线8MB预处理和私人链接属于插件实现，不适用于只安装技能文件的本地环境。
