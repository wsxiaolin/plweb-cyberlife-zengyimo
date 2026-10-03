---
name: physicslab-usage
description: 用 physicslab Python 库（SekaiArendelle/physicslab）在本地生成物理实验室 AR 的实验存档并发布到社区。当赛博生命需要发布实验作品（电路实验等）时使用本技能。需要 Python 3.14+。
---

# physicslab 使用技能（发布实验用）

## 快速路径（推荐）

**不要手写调用 physicslab**——用仓库封装好的生成器：

```bash
# 查看全部可用模板
python tools/experiment_gen.py list

# 生成实验并存档到 tmp/（不发布，先预览）
python tools/experiment_gen.py preview --template rheostat-dim

# 正式发布（需要社区会话已建立，即 prepare.py 已跑过）
python tools/experiment_gen.py publish --template half-adder \
    --subject "半加器练习" \
    --description "第一行\n\n第三行（支持换行）" \
    --tags 高中,逻辑电路
```

`--tags` 可用值（常用）：`高中`、`初中`、`教学实验`、`小作品`、`娱乐实验`、
`直流电路`、`逻辑电路`、`交流电路`、`电子电路`、`问与答`（讨论区用）、`交流`。

## 模板与曾以沫的匹配

| 模板 | 内容 | 人设匹配度 |
|------|------|-----------|
| series-lamps | 两灯串联，一亮一暗 | 高二物理课刚学的内容，最像她 |
| parallel-lamps | 两灯并联 | 初中学过，稳妥 |
| rheostat-dim | 滑动变阻器调光 | 初中底子+社区学的接法 |
| half-adder | 半加器逻辑电路 | "从社区教程学的"，要谦虚表述 |
| doorbell | 电铃 | 有情感分（小学烧灯泡的故事） |
| led-555-blink | NE555 闪烁灯 | 有点炫，适合"我终于做出来了"的剧情 |

**选题原则**：高二学生做不出大学水平的东西。发布描述要写"做了什么、卡在哪、
想请教什么"（学生视角），不要写成产品说明书。

## 发布的完整链路（tools/experiment_gen.py 内部做的事）

1. `crt_circuit_experiment(name)` 创建实验对象
2. 摆放元件、接线（`expe.crt_elements(...)`、`expe.crt_a_wire(a.red, b.black)` 等）
3. 设置 `expe.summary.subject / description / tags`
4. `physicslab.publish.upload_experiment(expe, user, Category.Experiment)`：
   - 库内部完成 gzip 提交 `Contents/SubmitExperiment` + `Contents/ConfirmExperiment`
5. 更新 `memory/state.json` 的 `last_publish_date`

## 直接用 physicslab 造新电路（模板不够用时）

```python
from physicslab import (
    crt_circuit_experiment, BatterySource, IncandescentLamp,
    SimpleSwitch, Resistor, SlideRheostat, LogicInput, LogicOutput,
    Position, Tag,
)
from physicslab.enums import Category
from physicslab.publish import upload_experiment

with crt_circuit_experiment("我的实验名") as expe:
    bat = BatterySource(Position(-0.3, 0, 0))          # 电压默认 1.5V
    lamp = IncandescentLamp(Position(0.3, 0, 0))
    sw = SimpleSwitch(Position(0, 0.1, 0))
    expe.crt_elements(bat, lamp, sw)
    expe.crt_a_wire(bat.red, sw.red)                   # 引脚是 .red/.black
    expe.crt_a_wire(sw.black, lamp.red)
    expe.crt_a_wire(lamp.black, bat.black)
    expe.summary.subject = "标题"
    expe.summary.description = "描述"
    expe.summary.tags = {Tag.HighSchool, Tag.SmallProject}

# 发布（需要已登录的 User 对象——用 tools 里的会话）
# upload_experiment(expe, user, Category.Experiment)
```

## 常用元件引脚速查

- `BatterySource` / `IncandescentLamp` / `SimpleSwitch` / `LightEmittingDiode` / `Buzzer`：`.red` / `.black`
- `LogicInput`：`.o`（输出）；`LogicOutput`：`.i`（输入）
- 门电路（And/Or/Xor…）：`.i1 .i2 .o`（三脚门）
- `HalfAdder` / `FullAdder`：`.i_up .i_low .o_up .o_low`
- `SlideRheostat`：`.l_low .r_low .l_up .r_up`
- `NE555`：`.vcc .dis .thr .ctrl .trig .out .reset .ground`
- `Position(x, y, z)` 单位是米，元件间距 0.1~0.3 比较美观

## 注意

- physicslab 要求 **Python 3.14+**（PEP 758 语法）。CI 已配置；本地低版本会 SyntaxError
- 库文档：https://github.com/SekaiArendelle/physicslab （docs/ 有完整 API 文档）
- 天体物理实验（CelestialExperiment）曾以沫还没学到，发布前想想人设
- 发布频率受 config/life.json 约束（默认 10 天一个），AGENTS.md 的能量系统会扣分
