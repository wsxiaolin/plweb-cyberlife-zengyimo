# 富文本排版与对象引用

社区文本可直接使用标签排版。将标签字符串写入标题Subject、介绍Description的段落、评论Content或签名Signature；用正常JSON序列化保留字符串。正文需要展示效果时直接提交标签，不将尖括号转成`&lt;`/`&gt;`，也不把整段包进Markdown代码块。

## 文字样式

| 功能 | 写法 |
|---|---|
| 加粗 | `<b>重点</b>` |
| 斜体 | `<i>说明</i>` |
| 蓝字 | `<a>蓝色文字</a>` |
| 指定颜色 | `<color=#FF0000>红色</color>` |
| 指定字号 | `<size=40>标题</size>` |
| 下划线 | `<u>文字</u>` |
| 段内换行 | `第一行<br>第二行` |

使用半角`< > / = #`。新写标签使用单层、成对闭合；`br`为换行标记。按先进后出的顺序嵌套，例如`<b><i>重点</i></b>`。编辑已有正文时保留原有有效标签结构，不自动给整篇重复套两层或三层。标题和列表预览使用简洁排版；完整介绍可使用字号、下划线与段内换行。字号参数是排版值，不将其等同于所有显示环境中的像素尺寸。

颜色优先用六位HEX：`#RRGGBB`，例如红色`#FF0000`、绿色`#00FF00`、蓝色`#0000FF`。HEX后面不拼接RGB数字；`#FF0000255,0,0`不是颜色码。不需要把整张颜色表放进上下文。

## 用户与作品引用

| 目标 | 写法 | ID来源 |
|---|---|---|
| 用户 | `<user=用户ID>显示昵称或说明</user>` | User.ID |
| 实验区作品 | `<experiment=作品摘要ID>显示标题或说明</experiment>` | Summary.ID，Category=Experiment |
| 黑洞作品 | `<discussion=作品摘要ID>显示标题或说明</discussion>` | Summary.ID，Category=Discussion |

先核对目标与当前Category，再填实际ID。两个作品引用标签均使用**摘要ID**，不使用Summary.ContentID保存ID。GetSummary虽然把请求字段命名为ContentID，这里仍传摘要ID；GetExperiment才使用保存ID。用户昵称和展示标题是可读文字，不能代替ID。

user标签负责用户引用。需要回复通知时，PostComment同时填写ReplyID，并保留可被服务器识别的正文@完整昵称。CommunityClient和ChatGPT插件会自动核对昵称并补齐该格式，具体字段见[回复与通知](comments.md#回复指定用户)。

作品移动分区后，按当前Category选择experiment或discussion标签。引用时只写必要的显示文字，不为了取得链接而将完整实验载入上下文。用户引用应符合本次任务及社区规则。

## 组合效果

- 加粗彩色标题：`<b><color=#1E90FF>实验说明</color></b>`。
- 渐变或彩虹文字：逐字或逐小段设置颜色，例如`<color=#FF0000>红</color><color=#00AA00>绿</color><color=#0000FF>蓝</color>`；这不是独立的渐变标签。
- 删除线：可在文字后加入组合字符U+0336，例如`旧̶说̶法̶`；旧式排版也用`<size=60>̶</size>`调整划线位置与大小。彩色删除线再嵌套color。它与下划线u不同。
- 字体图标或表情：作为Unicode字符写入，保留原码点。已有心形、皇冠、保存等私用区字符时可复用原字符，不编造其码点，也不把它当成独立标签。

## 识别已有特殊标记

读取或编辑既有内容时，识别并保留`<internal=friend>显示文字</internal>`（好友入口）、`<internal=activity>显示文字</internal>`（活动入口），以及quad旧式图块标记。它们属于已有内容的特殊排版；新建普通正文使用上面的基础文字样式和对象引用。quad用于彩色方块/像素排列，编辑时原样保留已有完整标记。

## 提交与维护

介绍仍使用段落字符串数组，例如：

```json
{"Description":["<b>实验说明</b>","<color=#1E90FF>关键结论</color>","第一行<br>第二行"]}
```

只改排版时，读取原摘要、更新目标文本字段并提交，保留原模型、ID、作者和标签。读回文本确认标签及内容未丢失。颜色或字号语法无需新增API；发布和编辑沿用SubmitExperiment，评论沿用PostComment，签名沿用ModifyInformation(Field=Signature)。相关调用见practical-api.md。
