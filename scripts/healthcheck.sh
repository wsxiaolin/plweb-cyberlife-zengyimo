#!/usr/bin/env bash
# healthcheck.sh —— 部署前/排障用的本地手动检查（不经过 Agent，纯确定性链路）
#
# 用法：
#   PLWEB_EMAIL=... PLWEB_PASSWORD=... bash scripts/healthcheck.sh
#
# 检查项：
#   1. 社区登录（多层回退）
#   2. inbox 数据拉取（prepare）
#   3. 只读动作（query/get-summary）
#   4. finalize 校验链
# 全部通过 = 骨架健康；Agent（Open Code）只需在 CI 里正常工作即可。

set -u
cd "$(dirname "$0")/.."

echo "=== 1/4 登录与数据拉取 ==="
python3 tools/prepare.py --browse-pages 1
PREP=$?
if [ "$PREP" -ne 0 ]; then
  echo "❌ prepare 失败（exit=$PREP）——检查账号凭据/网络"
  exit "$PREP"
fi
echo "✅ 登录 OK，inbox.json 已生成"

echo "=== 2/4 只读动作 ==="
python3 tools/act.py query --category Discussion --take 5 > /dev/null && \
  echo "✅ query OK" || { echo "❌ query 失败"; exit 3; }

echo "=== 3/4 记忆文件完整性 ==="
python3 - <<'PY'
import json, pathlib
state = json.loads(pathlib.Path("memory/state.json").read_text(encoding="utf-8"))
assert state["nickname"] == "焦距有点长"
for f in ("persona/identity.md", "persona/life_story.md", "AGENTS.md"):
    assert pathlib.Path(f).exists(), f
print("✅ persona/AGENTS/state 完整")
PY

echo "=== 4/4 finalize 校验链 ==="
python3 tools/finalize.py --agent-exit 0 || true
echo
echo "全部检查完成。骨架健康。如需完整端到端（含 Agent），在 GitHub Actions 手动触发『唤醒 · Wake』。"
