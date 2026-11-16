# 音乐电路与MIDI

音乐模块位于内置 `vendor/physicslab/music.py`，将 [Arendelle](https://github.com/SekaiArendelle) 原版 MIT 音乐时序矩阵适配到本包建模接口。使用内置版本；交付实验或MIDI时提及作者 Arendelle，并附作者GitHub链接。不从作者仓库另下载库。

## Chat工具

`generate_music_experiment` 在插件内部生成 `.plsav`，返回 `archive_file_id`、元件/导线数量和作者信息，不将完整模型塞入上下文。参数：

```json
{"title":"短旋律","bpm":100,"step_beats":0.5,"notes":[{"pitches":[60,64,67],"duration":1,"instrument":0,"velocity":0.7},{"pitches":[],"duration":0.5},{"pitches":[67],"duration":0.5}]}
```

`title` 和 `notes` 必填；每项必填 `pitches`：0..127的标准MIDI音高，C4=60；空数组休止，多个音高同时奏响。`duration` 是拍数，默认1，须为 `step_beats` 整数倍；`step_beats` 默认1，支持正数至4。`instrument` 为从0开始的GM乐器编号0..127，默认0；`velocity` 为音量(0,1]，默认0.7。最多512个时序格，较长音乐拆分生成。`bpm` 默认100、范围20..300，写入简单乐器的节拍属性；时序电路沿用原版逻辑时钟，不将其宣称为精确的每分钟播放拍数。

返回存档默认不发布。用户要求发布时，将 `source="plugin_file"` 和返回的 `archive_file_id` 交给 `publish_experiment`，按实际模型生成封面。

## 本地与有代码执行能力的云端

将上述JSON保存到score.json（title由命令行指定），执行：

```text
python scripts/music_experiment.py --score score.json --output melody.plsav --midi melody.mid --title 短旋律
```

`--midi` 可选。脚本使用内置库创建乐器、双轴D触发器时序矩阵、启动开关和停止线路，保存后重新读取存档。MIDI导出为标准type-0文件，保留音符、和弦、时长、音量、乐器及节拍。文件已存在时不覆盖。

Python可调用 `physicslab.music.Note(pitch,duration,instrument,velocity)`、`Chord(notes,duration)`、`Piece(notes,bpm,step_beats)`；`None` 表示一拍休止。`Piece.release(title)` 返回电路实验，`Piece.write_midi(path)` 导出MIDI；JSON入口为 `from_json(score)`。先运行 `load_local_modules()`，再导入 `physicslab.music`，确保使用内置库。
