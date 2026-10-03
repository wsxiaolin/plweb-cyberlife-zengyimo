#!/usr/bin/env python3
"""作息门卫 · schedule_gate.py

判断"现在该不该醒"。CI 在安装依赖之前调用（stdlib-only，无需 pip）。

判定逻辑（优先级从高到低）：
  1. 手动唤醒（workflow_dispatch） -> 一律放行
  2. config/life.json 的 calendar.vacations 命中当天 -> 自由日（寒暑假，本地权威）
  3. 在线节假日 API（timor.tech）-> 工作日/周末/法定节假日/调休补班
  4. API 不可达 -> 按星期兜底（周一~五=上学日，周六日=自由日）

上学日只开 school 槽位，自由日只开 free 槽位（槽位表在 config/life.json 的 wake_slots，
与 .github/workflows/wakeup.yml 的 cron 对齐）。GitHub cron 有随机延迟，容差 ±100 分钟。

输出：单行 JSON（stdout），退出码 0。脚本自身异常时输出 {"open": true, "error": ...}
（fail-open：宁可多醒一次让 Agent 决定潜水，也不要错过一次生命）。

本地测试：
  python3 tools/schedule_gate.py --date 2026-10-01 --time 09:40
  python3 tools/schedule_gate.py --date 2027-01-20 --time 07:00   # 寒假
  python3 tools/schedule_gate.py --event workflow_dispatch
"""

import argparse
import datetime as dt
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

BJT = dt.timezone(dt.timedelta(hours=8))  # 北京时间无夏令时
SLOT_TOLERANCE_MIN = 100                  # cron 随机延迟容差
API_TIMEOUT_S = 6
API_URL = "https://timor.tech/api/holiday/info/{date}"

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "config" / "life.json"


def load_config() -> dict:
    try:
        return json.loads(CONFIG.read_text(encoding="utf-8"))
    except Exception as exc:  # 配置坏了也 fail-open
        return {"_error": f"life.json 读取失败: {exc}"}


def parse_hhmm(s: str) -> int:
    h, m = s.strip().split(":")
    return int(h) * 60 + int(m)


def in_range(day: str, v: dict) -> bool:
    return str(v.get("from")) <= day <= str(v.get("to"))


def day_type_from_api(day: str) -> dict:
    """timor.tech: type.type 0=工作日 1=周末 2=节假日 3=调休补班。失败返回 fallback。"""
    url = API_URL.format(date=day)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "plweb-cyberlife/1.0"})
        with urllib.request.urlopen(req, timeout=API_TIMEOUT_S) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        t = int(data["type"]["type"])
        name = data.get("type", {}).get("name", "")
        if t == 0:
            return {"day_type": "school", "source": "api", "reason": f"工作日（{name}）"}
        if t == 1:
            return {"day_type": "free", "source": "api", "reason": f"周末（{name}）"}
        if t == 2:
            return {"day_type": "free", "source": "api", "reason": f"法定节假日（{name}）"}
        if t == 3:
            return {"day_type": "school", "source": "api", "reason": f"调休补班（{name}）"}
        return {"day_type": "school", "source": "api", "reason": f"未知类型 {t}，保守按上学日"}
    except Exception as exc:
        # 兜底：按星期
        weekday = dt.date.fromisoformat(day).weekday()  # 0=周一
        if weekday >= 5:
            return {"day_type": "free", "source": "fallback",
                    "reason": f"API 不可达（{exc}），按周末处理"}
        return {"day_type": "school", "source": "fallback",
                "reason": f"API 不可达（{exc}），按工作日处理"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=None, help="YYYY-MM-DD，默认今天（北京时间）")
    ap.add_argument("--time", default=None, help="HH:MM，默认现在（北京时间）")
    ap.add_argument("--event", default="schedule",
                    help="触发方式：schedule 或 workflow_dispatch（手动唤醒直接放行）")
    args = ap.parse_args()

    now = dt.datetime.now(BJT)
    day = args.date or now.strftime("%Y-%m-%d")
    minute_of_day = parse_hhmm(args.time) if args.time else now.hour * 60 + now.minute

    cfg = load_config()
    if "_error" in cfg:
        print(json.dumps({"open": True, "error": cfg["_error"]}, ensure_ascii=False))
        return 0

    # 1) 手动唤醒：放行
    if args.event == "workflow_dispatch":
        info = {"day_type": "unknown", "source": "manual",
                "reason": "手动唤醒，门卫不拦截"}
    else:
        # 2) 寒暑假/运营者设定的假期（本地权威）
        vacations = cfg.get("calendar", {}).get("vacations", [])
        hit = next((v for v in vacations if in_range(day, v)), None)
        if hit:
            info = {"day_type": "free", "source": "life.json",
                    "reason": f"{hit.get('name', '假期')}（{hit.get('from')}~{hit.get('to')}）"}
        else:
            # 3/4) API / 兜底
            info = day_type_from_api(day)

    # 槽位匹配（手动唤醒不做槽位判定）
    if args.event == "workflow_dispatch":
        matched, slots_key = None, "n/a"
    else:
        slots_key = "school" if info["day_type"] == "school" else "free"
        slots = cfg.get("wake_slots", {}).get(slots_key, [])
        matched = None
        for slot in slots:
            if abs(minute_of_day - parse_hhmm(slot)) <= SLOT_TOLERANCE_MIN:
                matched = slot
                break

    result = {
        "open": args.event == "workflow_dispatch" or matched is not None,
        "date": day,
        "time": f"{minute_of_day // 60:02d}:{minute_of_day % 60:02d}",
        "day_type": info["day_type"],
        "source": info["source"],
        "reason": info["reason"],
        "matched_slot": matched,
        "slots": slots_key,
    }
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
