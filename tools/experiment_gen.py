"""experiment_gen.py —— 用 physicslab 本地生成实验并发布到社区。

需要 Python 3.14 + physicslab（pip install git+.../SekaiArendelle/physicslab）。
Agent 用它发布"曾以沫水平"的物理实验作品。

内置模板（对应高二理科生能力范围）：
  series-lamps    两灯串联（一亮一暗，额定电压对比）
  parallel-lamps  两灯并联
  rheostat-dim    滑动变阻器调光台灯（限流接法）
  half-adder      半加器（从社区教程学的逻辑电路）
  doorbell        电铃（致敬小学烧灯泡的那节课）
  led-555-blink   NE555 LED 闪烁灯

用法：
  python tools/experiment_gen.py list
  python tools/experiment_gen.py preview --template rheostat-dim
  python tools/experiment_gen.py publish --template rheostat-dim \
      --subject "滑动变阻器调光" --description "正文，支持\n换行" [--tags 高中,直流电路]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

ROOT = Path(__file__).resolve().parent.parent
TMP = ROOT / "tmp"

try:
    from physicslab import (
        BatterySource,
        IncandescentLamp,
        LogicInput,
        LogicOutput,
        Position,
        SimpleSwitch,
        SlideRheostat,
        crt_circuit_experiment,
    )
    from physicslab.circuit.elements import (  # noqa: E402
        Buzzer,
        HalfAdder,
        LightEmittingDiode,
        NE555,
    )
    from physicslab.enums import Category, Tag
    from physicslab.publish import upload_experiment
    from physicslab import web

    HAS_PHYSICSLAB = True
except ImportError:  # 未安装或 Python 版本不足
    HAS_PHYSICSLAB = False


def build_series_lamps(expe):
    bat = BatterySource(Position(0, 0, 0), voltage=3.0)
    lamp1 = IncandescentLamp(Position(0.3, 0.15, 0))
    lamp2 = IncandescentLamp(Position(0.3, -0.15, 0))
    sw = SimpleSwitch(Position(-0.3, 0, 0))
    expe.crt_elements(bat, lamp1, lamp2, sw)
    expe.crt_a_wire(bat.red, sw.black)
    expe.crt_a_wire(sw.red, lamp1.black)
    expe.crt_a_wire(lamp1.red, lamp2.black)
    expe.crt_a_wire(lamp2.red, bat.black)
    return ("两灯串联分压：导线电阻不同的两个小灯泡，一个亮一个暗。\n\n"
            "记录一下我的猜想：亮度不同的原因是两灯电阻不同，串联分压不同。")


def build_parallel_lamps(expe):
    bat = BatterySource(Position(0, 0, 0), voltage=3.0)
    lamp1 = IncandescentLamp(Position(0.3, 0.15, 0))
    lamp2 = IncandescentLamp(Position(0.3, -0.15, 0))
    sw = SimpleSwitch(Position(-0.3, 0, 0))
    expe.crt_elements(bat, lamp1, lamp2, sw)
    expe.crt_a_wire(bat.red, sw.black)
    expe.crt_a_wire(sw.red, lamp1.black)
    expe.crt_a_wire(lamp1.black, lamp2.black)
    expe.crt_a_wire(lamp1.red, lamp2.red)
    expe.crt_a_wire(lamp2.red, bat.black)
    return "两灯并联：亮度应该一样（等电压），和串联做对比实验。"


def build_rheostat_dim(expe):
    bat = BatterySource(Position(0, 0, 0), voltage=3.0)
    lamp = IncandescentLamp(Position(0.4, 0, 0))
    rheo = SlideRheostat(Position(0.0, 0.2, 0))
    expe.crt_elements(bat, lamp, rheo)
    expe.crt_a_wire(bat.red, rheo.l_low)
    expe.crt_a_wire(rheo.r_low, lamp.black)
    expe.crt_a_wire(lamp.red, bat.black)
    return ("滑动变阻器调光：一端接下接线柱、一端接另一端（限流接法变体）。\n"
            "滑到最右灯会变暗——这个现象还没完全想明白，欢迎大佬指教。")


def build_half_adder(expe):
    i1 = LogicInput(Position(-0.4, 0.2, 0))
    i2 = LogicInput(Position(-0.4, -0.2, 0))
    adder = HalfAdder(Position(0.1, 0, 0))
    s_out = LogicOutput(Position(0.5, 0.2, 0))
    c_out = LogicOutput(Position(0.5, -0.2, 0))
    expe.crt_elements(i1, i2, adder, s_out, c_out)
    expe.crt_a_wire(i1.o, adder.i_up)
    expe.crt_a_wire(i2.o, adder.i_low)
    expe.crt_a_wire(adder.o_up, s_out.i)
    expe.crt_a_wire(adder.o_low, c_out.i)
    return ("半加器：照着社区教程搭的，两个输入位相加，输出和与进位。\n"
            "第一次跑通的时候真的激动。")


def build_doorbell(expe):
    bat = BatterySource(Position(0, 0, 0), voltage=3.0)
    sw = SimpleSwitch(Position(-0.3, 0, 0))
    bell = Buzzer(Position(0.35, 0, 0))
    expe.crt_elements(bat, sw, bell)
    expe.crt_a_wire(bat.red, sw.black)
    expe.crt_a_wire(sw.red, bell.black)
    expe.crt_a_wire(bell.red, bat.black)
    return "电铃电路：小学四年级烧灯泡之后念念不忘的那个\"叮\"。\n现在用蜂鸣器，按下开关就响。"


def build_led_555_blink(expe):
    bat = BatterySource(Position(0, 0, 0), voltage=6.0)
    ic = NE555(Position(0.1, 0.2, 0))
    led = LightEmittingDiode(Position(0.45, -0.1, 0))
    expe.crt_elements(bat, ic, led)
    expe.crt_a_wire(bat.red, ic.vcc)
    expe.crt_a_wire(ic.ground, bat.black)
    expe.crt_a_wire(ic.out, led.red)
    expe.crt_a_wire(led.black, bat.black)
    return ("NE555 闪烁灯：仿的一个大佬作品改的参数，闪起来像呼吸灯。\n"
            "555 内部原理还没吃透（是模拟电路），先记录现象。")


TEMPLATES = {
    "series-lamps": build_series_lamps,
    "parallel-lamps": build_parallel_lamps,
    "rheostat-dim": build_rheostat_dim,
    "half-adder": build_half_adder,
    "doorbell": build_doorbell,
    "led-555-blink": build_led_555_blink,
}


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list")

    p_prev = sub.add_parser("preview")
    p_prev.add_argument("--template", required=True, choices=list(TEMPLATES))
    p_prev.add_argument("--name", default=None)

    p_pub = sub.add_parser("publish")
    p_pub.add_argument("--template", required=True, choices=list(TEMPLATES))
    p_pub.add_argument("--subject", required=True)
    p_pub.add_argument("--description", required=True)
    p_pub.add_argument("--tags", default="高中,直流电路")

    p_dis = sub.add_parser("post-discussion")
    p_dis.add_argument("--subject", required=True)
    p_dis.add_argument("--body", required=True, help="正文，\\n 表示换行")
    p_dis.add_argument("--tag", default="交流", help="标签，逗号分隔（交流/问与答/聊天/BUG）")

    args = parser.parse_args()

    if args.cmd == "list":
        for name in TEMPLATES:
            print(f"  {name}")
        print("\n（publish 需要 Python 3.14 + physicslab）")
        return 0

    if args.cmd == "post-discussion":
        # 讨论帖走 physicslab 的 SubmitExperiment 通道（实测可靠；手拼 JSON 会被拒）
        if not HAS_PHYSICSLAB:
            print(json.dumps({"ok": False, "error": "需要 Python 3.14 + physicslab"},
                             ensure_ascii=False))
            return 4
        body_text = args.body.replace("\\n", "\n")
        user = web.email_login(os.environ.get("PLWEB_EMAIL"),
                               os.environ.get("PLWEB_PASSWORD"))
        with crt_circuit_experiment(args.subject) as expe:
            # 服务端拒绝完全空的实验——放一个简单的小场景（电池+开关+灯）
            bat = BatterySource(Position(0, 0, 0), voltage=3.0)
            sw = SimpleSwitch(Position(0.15, 0.1, 0))
            lamp = IncandescentLamp(Position(0.3, 0, 0))
            expe.crt_elements(bat, sw, lamp)
            expe.crt_a_wire(bat.red, sw.black)
            expe.crt_a_wire(sw.red, lamp.red)
            expe.crt_a_wire(lamp.black, bat.black)
            expe.summary.description = body_text
            expe.summary.tags = {Tag(t.strip()) for t in args.tag.split(",") if t.strip()}
            resp = upload_experiment(expe, user, Category.Discussion, image_path=None)
        summary_id = ((resp.get("Data") or {}).get("Summary") or {}).get("ID")
        result = {"action": "post-discussion", "ok": resp.get("Status") == 200,
                  "status": resp.get("Status"), "summary_id": summary_id,
                  "subject": args.subject}
        from client import _log_action
        _log_action(result)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["ok"] else 3

    if not HAS_PHYSICSLAB:
        print(json.dumps({
            "ok": False,
            "error": "physicslab 未安装或 Python 版本低于 3.14",
        }, ensure_ascii=False))
        return 3

    name = getattr(args, "name", None) or f"cyberlife-{args.template}"
    with crt_circuit_experiment(name) as expe:
        default_desc = TEMPLATES[args.template](expe)
        expe.summary.subject = name
        if args.cmd == "publish":
            expe.summary.subject = args.subject
            expe.summary.description = args.description.replace("\\n", "\n")
            expe.summary.tags = {Tag(t) for t in args.tags.split(",") if t.strip()}
        destination = TMP / f"{name}.plsav"
        destination.parent.mkdir(parents=True, exist_ok=True)
        expe.save_to(destination)

    if args.cmd == "preview":
        print(json.dumps({
            "ok": True,
            "template": args.template,
            "saved_to": str(destination),
            "default_description": default_desc,
        }, ensure_ascii=False, indent=2))
        return 0

    # ---- publish ----
    email = os.environ.get("PLWEB_EMAIL")
    password = os.environ.get("PLWEB_PASSWORD")
    user = web.email_login(email, password)
    resp = upload_experiment(expe, user, Category.Experiment, image_path=None)
    summary_id = ((resp.get("Data") or {}).get("Summary") or {}).get("ID")
    result = {
        "ok": resp.get("Status") == 200,
        "status": resp.get("Status"),
        "summary_id": summary_id,
        "subject": args.subject,
        "template": args.template,
    }
    from client import _log_action
    _log_action({"action": "publish_experiment", **result})

    # 更新机械状态（finalize 与下次唤醒都知道"最近发过实验"）
    import datetime as dt

    state_file = ROOT / "memory" / "state.json"
    if state_file.exists():
        state = json.loads(state_file.read_text(encoding="utf-8"))
        state["last_publish_date"] = dt.datetime.now(
            dt.timezone(dt.timedelta(hours=8))
        ).strftime("%Y-%m-%d")
        state_file.write_text(
            json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 3


if __name__ == "__main__":
    sys.exit(main())
