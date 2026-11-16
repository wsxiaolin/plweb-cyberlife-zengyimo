# 创建与发布实验

使用本包 `vendor/physicslab` 内置的本地建模库（Python 3.10+），由 [Arendelle](https://github.com/SekaiArendelle) 的 [physicslab](https://github.com/SekaiArendelle/physicslab) 适配，保留 MIT 许可。网络、上传和登录缓存读取部分已移除。先通过 `scripts/offline_physicslab.py` 的 `load_local_modules()` 加载 circuit、celestial、electromagnetism 和 coordinate_system；可运行随附示例生成存档。

**使用随包内置库，不从作者GitHub或PyPI另取库。AI交付由此库生成的结果时，提及作者 Arendelle 并附 https://github.com/SekaiArendelle 。** ChatGPT插件在有代码执行能力的环境用 `get_modeling_library` 获取下载地址：Work优先下载返回的公开固定版本快照，解压后进入archiveRoot，保留scripts/vendor目录关系；不需要用户每次上传ZIP。该快照来自插件自有仓库，包含已适配的内置库。账号、发布和笔记仍用插件云端工具，不切换到快照中的通用版登录或本地记忆流程。音乐生成见 [音乐电路](music.md)，Chat可直接调用 `generate_music_experiment`。

```text
python scripts/experiment_example.py --type circuit --output <新文件.plsav> --title <标题>
python scripts/experiment_example.py --type celestial --output <新文件.plsav> --title <标题>
python scripts/experiment_example.py --type electromagnetism --output <新文件.plsav> --title <标题>
```

示例分别创建逻辑输入/输出及导线、太阳与地球、正负电荷。扩展实验时按目标设置元件、位置、参数和连接；保存后重新载入，核对元件标识、导线端点与数量。修改现有存档时保留原件。

## 发布

用户要求发布时直接调用 `CommunityActions.publish` 或ChatGPT插件工具 `publish_experiment`。用户只要求制作时交付存档。

```text
python scripts/community_cli.py --account <用户ID> publish --archive <文件.plsav> --title <标题> --description <介绍> --tag <实时标签Identifier>
```

发布方法提交 `Summary`、`Experiment` 和 `Workspace`，读取返回的摘要ID与保存ContentID。默认按实际模型布局生成PNG封面并上传，也可传 `--cover <图片>`。最后读回摘要、模型和封面序号，返回 `published`、`modelVerified`、`coverUploaded`。

直接请求形式：`POST /Contents/SubmitExperiment`，正文为 `{Summary:{ID:null,ContentID:null,Category:"Experiment",Subject,Description,Tags,Language,...},Experiment:{ID:null,Type,StatusSave,CameraSave,...},Workspace:null}`。使用 `.plsav` 中的 Summary/Experiment 构造完整对象，标题、介绍、标签按任务替换，保留模型字段。

`publish_experiment` 专门从模型存档发布作品；标题和介绍不能代替 `.plsav` 模型。参数必填 `source`：

- `source="archive_json"`：仅填 `archive_json`，值是完整 `.plsav` 对象的JSON序列化字符串，包含 `Experiment` 对象和 `StatusSave` 模型字符串。
- `source="plugin_file"`：仅填 `archive_file_id`，值必须是插件保存的完整archive文件ID。

可选 `title:string`、`description:string[]`、`tags:string[]`、`category:"Experiment"|"Discussion"|"Model"`、`language:string`、`account_id:string`。封面可选 `cover_base64:string` 或 `cover_file_id:string`，二选一；省略则自动生成。

大型存档和图片先分块调用 `store_file_chunk`，`kind` 选 `archive` 或 `image`，`encoding` 选 `utf8` 或 `base64`，单块不超过60000字符。首块index=0且不传file_id，续块传上一响应的 `plugin_file_id` 作为file_id，index连续递增，末块complete=true。返回 `plugin_file_id`（`fileId`同值）具有 `plfile_` 前缀；不是ChatGPT附件ID。发布传 `source="plugin_file"` 与 `archive_file_id`，图片工具传 `image_source="plugin_file"` 与 `image_file_id`。完整模型在文件和程序中处理，不全文输出到聊天。

本地建模示例验证存档构造、保存和重载；实验说明中的测量值应来自实际计算或测量。模型类型0为电路、3为天体、4为电磁。

## 坐标、朝向与封面

内置库使用 `Position(x,y,z)`：y为高度，电路通常放在x-z平面（y=0）；相邻元件改变x或z。存档中的Position字符串按 `x,z,y` 序列化，例如 `Position(1,0,2)` 保存为 `"1,2,0"`，不要将存档第三个分量当作平面纵轴。Rotation也按x,z,y序列化，电路元件构造器默认 `Rotation(0,0,180)`，按具体元件的构造参数设置朝向。

默认封面为800×600（4:3）的简化布局预览，按x-z投影并保持比例，显示导线、简化元件符号和编号；编号对应Elements顺序。它不复现完整三维外观和旋转。需要文字标题、详细外观或特定视角时提供自定义封面，按4:3设计并留出边距。

发布时传入tags默认与存档原标签合并，保留“禁止改编”等既有标签；只有明确指定 `replace_tags=true`（命令行 `--replace-tags`）才替换普通标签，Type-*仍保留。发布前核对实时标签及冲突，不能静默去掉原存档限制标签。

作品提交后封面或核验步骤失败时，错误context.publication（插件为publication）会保留已创建的摘要ID、保存ID和Category。先检查该作品并继续未完成步骤，不重复新建。
