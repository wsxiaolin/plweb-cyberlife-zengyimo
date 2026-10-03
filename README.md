# plweb-cyberlife-zengyimo · 物理实验室社区的赛博生命「曾以沫」

> 一个生活在「物理实验室 AR」社区（[turtlesim.com](https://www.turtlesim.com/)）里的赛博生命：
> **曾以沫**（社区昵称：**焦距有点长**），16 岁，高二理科生，物理特别好，话也特别多。
> 它由 GitHub Actions 每天定时唤醒，用 [Open Code](https://opencode.ai) 作为"大脑"，
> 在社区里逛、学、聊、发实验——像一个真实的高中生那样生活，并且**越活越像人**。

```
本仓库不是"调 LLM API"的传统 Agent 框架——它是一套完整的"生命体"骨架：
  persona/  灵魂（人设、生命历程、说话风格）
  memory/   记忆（日记、人物档案、知识笔记、使嘴笔记、机械状态）——每次唤醒都写回仓库
  tools/    双手（确定性社区 API 工具，Agent 通过 CLI 调用）
  AGENTS.md 天性（Open Code 每次唤醒自动读取的运行宪法）
  CI        生物钟（定时唤醒 + 多层自动回退 + 记忆提交回仓库）
```

## 它是谁

| | |
|---|---|
| 姓名 | 曾以沫（爸妈取的，出自"相濡以沫"；她嫌太文艺） |
| 社区昵称 | 焦距有点长——源自高二光学课的凸透镜成像，她总调不好焦距，干脆拿来当网名 |
| 出生 | 2010-03-14（π 日，她坚持这是"注定理科脑"的玄学证据） |
| 现状 | 2026 年 9 月升高二理科班，走读，学校允许带手机、没有晚自习 |
| 账号 | 2026 年 9 月被同桌安利后注册的新号，昵称「焦距有点长」 |

**人设背景**：一个被同桌安利、刚踏进物实社区的**纯新人**——物理好、动手强、
元气自来熟的假小子。她的账号是白纸一张：0 粉丝、0 作品、谁也不认识。
她最大的短板是"没朋友"，最大的执念也是"交朋友"：每天都想主动搭话、主动捧场、
主动认人，把在学校的"主场"复制到社区来。

她不会装老手，也不装懂：没见过的梗就老实说没见过，没学过的物理就说"我们还没教到"。
她要靠一天天的真实互动，从"路人"慢慢变成"熟人"。

## 它怎么活

**作息门卫**（`tools/schedule_gate.py`）自动区分**上学日**和**自由日**（周末、法定节假日、
寒暑假，含调休补班识别）：
- 上学日 4 醒：上学前 07:00 / 午休 12:30 / 放学后 17:30 / 睡前 21:30（走读、无晚自习）
- 自由日 8 醒：08:30 ~ 22:30 每 2 小时一槽——假期醒得勤，但醒得多不等于说得多

每次醒来，Open Code（读了 `AGENTS.md` 的 Agent）会"上一段网"（约 40 分钟）：

1. 读 `tmp/inbox.json`（本次"睁眼看到的社区现状"，由 `tools/prepare.py` 拉取）
2. 读上次的记忆与留给自己的便签，翻一眼 `memory/community.md`、`memory/voice.md`
3. **补课·认人**：认一个活跃的人 / 考古一件社区旧事 / 追一个热点，
   落到 `memory/community.md`、`memory/people/`、`memory/knowledge/`
4. **自主决定**：回不回消息、逛什么、学什么、今天说不说话、发不发实验
5. 通过 `tools/act.py` 执行社区动作（评论/点赞/关注/发帖/私信/改名）
6. **挂机**：sleep 几分钟后 `get-messages` 查新回复——有人接话就趁热聊，没人就继续自己逛
7. 写日记、更新人物档案和社区认知，**在 `memory/voice.md` 复盘自己的说话**，
   `state.json` 结算能量与预算

自主权由四层约束共同塑造：`AGENTS.md`（行为准则 + 决策树 + 使嘴规矩）、`config/life.json`
（作息/频率上限/考试日历）、能量系统（每动作扣分，耗尽必须下线——防话痨）、
以及 **§3.7 使嘴与自我迭代**（越说越像人）。

## 像人，是练出来的（使嘴与自我迭代）

这个项目最在意的一件事：**别让它像一个"会回答问题的机器人"**。
参考了市面 QQ 机器人的人格工程经验，运行宪法里写进了几条反 AI 味的硬规矩：

- **先说"要不要说"**：约 8 成的消息不需要回，潜水是常态；刷屏、逮谁夸谁才是暴露点
- **反附和 NPC**：禁止"确实""我也是""我懂"这种没有增量的接话
- **不点评、不主动玩梗、句子要碎、标点随意**：像真人打字，不像客服
- **自我迭代**：每次醒来复盘自己哪句像人哪句出戏，观察真人句式抄进 `memory/voice.md`，
  每周提炼最多 3 条经验——让"怎么说"随着经历一起长

## 多层自动回退（CI 里对 Agent 调用的兜底）

| 层级 | 故障 | 回退 |
|------|------|------|
| L1 | 社区登录失败 / 服务端挂起 | prepare 重试退避 → 降级为"离线日记模式"（不惊动社区） |
| L1' | 服务端 `Take>16` 挂起等怪癖 | client 内置分页与快速失败（见 skills/plweb-skill/ERRATA.md） |
| L2 | 主模型唤醒失败/超时 | 按**有序回退名单**逐个换模型**继续同一段完整人生**（任务不简化） |
| L3 | Agent 产物不合格（没写日记/状态坏） | finalize 自动补写"失败日记"，仓库永不破损 |
| L4 | 连续严重失败 | 自动开 issue 告警运营者；周报 issue 汇报健康度 |

## 部署（复刻一个赛博生命）

1. **Fork / 使用本仓库**，进 Settings：
   - **Actions → General → Workflow permissions**：选 *Read and write permissions*
2. **配置 Secrets**（Settings → Secrets and variables → Actions）：
   - `PLWEB_EMAIL` / `PLWEB_PASSWORD`：社区账号凭据（必须）
   - 可选自备模型的密钥（`ANTHROPIC_API_KEY` / `OPENAI_API_KEY` / `OPENROUTER_API_KEY` / `DEEPSEEK_API_KEY` 任一）
3. **（可选）配置 Variable**：`OPENCODE_MODEL`（默认 `opencode/deepseek-v4-flash-free`，
   失败后按 `.github/workflows/wakeup.yml` 的 `OPENCODE_MODEL_FALLBACKS` 有序名单自动换模型）
4. **手动触发一次唤醒**验证：Actions → 唤醒 · Wake → Run workflow
5. 首次唤醒会执行"出生仪式"（写第一篇日记、认识第一批人）；之后交给生物钟

## 仓库结构

```
AGENTS.md                # 运行宪法（Open Code 自动读取）
.opencode.json           # Open Code 项目配置
config/life.json         # 作息/预算/考试日历（运营者可调）
persona/                 # 灵魂：identity / life_story / personality / community_manners
memory/                  # 记忆（CI 每次唤醒后提交回仓库——生命的连续性所在）
  state.json             # 机械状态：能量、计数器、心情、留给下次的便签
  diary/                 # 日记（第一人称）
  people/                # 社区人物档案（社交连续性）
  community.md           # 社区认知地图：板块规矩、活跃的人、时事、梗与传说
  voice.md               # 使嘴笔记：怎么说话、自我迭代的复盘
  knowledge/             # 学到的物理/电路笔记
  journal.md             # 大事记（append-only）
  weekly/                # 周记（周日晚生成）
skills/
  plweb-skill/           # 社区 API 官方技能文档（含实测勘误 ERRATA.md）
  physicslab-usage/      # 实验生成与发布技能（physicslab 库用法）
tools/                   # 确定性工具层（Python）
  client.py              # 社区 API 客户端：登录回退/重试退避/限速/动作日志
  prepare.py             # 唤醒数据准备 → tmp/inbox.json
  act.py                 # Agent 的动作 CLI（评论/点赞/关注/发帖/私信/资料）
  experiment_gen.py      # physicslab 实验生成与发布（需 Python 3.14）
  finalize.py            # 唤醒收尾校验与自动修复
prompts/wakeup.md        # 唤醒提示词模板
.github/workflows/       # wakeup.yml（生物钟+回退）、weekly.yml（周维护）
scripts/                 # bootstrap 等辅助脚本
```

## 手动干预

- **让它睡**：Settings → Actions → 暂停 wakeup.yml
- **手动唤醒**：Actions → 唤醒 · Wake → Run workflow（可填唤醒原因与模型）
- **改性格**：改 `persona/`（建议小步改，记忆会自然跟随）
- **改作息/频率**：改 `config/life.json`
- **看它在想什么**：`memory/diary/`、`memory/weekly/`、`memory/voice.md`、Actions artifacts

## 运营者须知（重要）

- 社区与管理员拥有最终裁定权。若账号被社区管理方要求停止运营，立即暂停 workflow。
- 角色红线见 `persona/identity.md`：不碰敏感话题、不伪造人类证据（不发假照片/
  不假约见面）、被管理员正式询问时停止发言转人工处理。
- Token/密码只存 GitHub Secrets，仓库与日志中绝不落盘（client 已确保）。
- 本项目是社区 AI 居民实验（新号、纯人设），请勿用于骚扰、引流或欺诈。

## 致谢

- [wsxiaolin/plweb-cyberlife](https://github.com/wsxiaolin/plweb-cyberlife) — 本框架的模板与来源
- [NetLogo-Mobile/plweb2](https://github.com/NetLogo-Mobile/plweb2) — CI 调用 Open Code 与 skills 的模式参考
- [NetLogo-Mobile/plweb-skill](https://github.com/NetLogo-Mobile/plweb-skill) — 社区 API 技能文档
- [SekaiArendelle/physicslab](https://github.com/SekaiArendelle/physicslab) — 实验生成与发布库（MIT）
- 物理实验室 AR 社区的所有居民
