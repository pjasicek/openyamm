#!/usr/bin/env python3
"""gait_gate.py for the MM9 wolf. The shared gate reads MM6-MM8 speeds (monster_data.txt Spd: the MM9 rows come out
"stationary"), while MM9's AI moves its wolves at their profile speeds (assets_dev/worlds/mm9/modifiers.yml `mm9_ai`):
wandering at walk_speed (MM9's WalkVel, GameplayActorAiSystem.cpp), chasing at run_speed (RunVelocity), slower only
when hindered. So this gate takes those speeds and repeats the engine's choice (ActorModelPresentation.h
actorModelGait: log misfit, doubled below the authored speed, a 1.25 preference for walk when wandering and run or
sprint when hurrying; rate capped at 2) for every descriptor, before and after, plus a sweep of speeds in between.
Stride and floor use the shared stride_audit.py and floor_audit.py on the candidate (the stride also from the paw
joints, as mm9_wolf_claude/scripts/gait_measure.py: the MM9 joints carry no foot names for stride_audit.py).

    wolf_gate.py <candidate.glb> [--set run=Trot --set run_stride_length=3.04 --set sprint=Running ...]
"""
import argparse
import copy
import math
from pathlib import Path
import sys

import numpy as np
import yaml

SHARED = Path(__file__).resolve().parents[3] / "claude_shared"
sys.path.insert(0, str(SHARED / "postprocess"))
sys.path.insert(0, str(SHARED / "floor"))
import floor_audit  # noqa: E402
import stride_audit  # noqa: E402
import glb_pose  # noqa: E402

ROOT = floor_audit.ROOT
MODEL = "mm9_wolf.glb"
MONSTER = {"MM9 Wolf A": 9114, "MM9 Wolf B": 9115, "MM9 Wolf C": 9116}
WINDOW = (0.75, 1.5)
MAX_RATE = 2.0
PREFERENCE = math.log(1.25)
PAWS = ("Bone19", "Bone05", "Bone09", "Bone42")


def profile_speeds():
    """monster id -> (walk_speed, run_speed) from the MM9 modifiers."""
    data = yaml.safe_load((ROOT / "assets_dev/worlds/mm9/modifiers.yml").read_text())
    rows = data.get("monsters", data)
    out = {}
    for key, mods in rows.items():
        ids = str(key).split("-")
        first, last = int(ids[0]), int(ids[-1])
        for mod in mods:
            if isinstance(mod, dict) and "mm9_ai" in mod:
                for i in range(first, last + 1):
                    out[i] = (float(mod["mm9_ai"].get("walk_speed", 0)), float(mod["mm9_ai"].get("run_speed", 0)))
    return out


def misfit(speed, clip_speed):
    r = math.log(speed / clip_speed)
    return r if r >= 0 else -2 * r


def choose(speed, clip_speeds, hurrying):
    best, best_misfit = None, None
    for index, clip_speed in enumerate(clip_speeds):
        if clip_speed <= 0:
            continue
        suits = (index != 0) == hurrying
        value = misfit(speed, clip_speed) - (PREFERENCE if suits else 0)
        if best is None or value < best_misfit:
            best, best_misfit = index, value
    return best


def gaits(actor, model):
    animation = actor["animation"]
    names = [actor["clips"]["walking"], animation["run"], animation.get("sprint")]
    strides = [float(animation["stride_length"]), float(animation["run_stride_length"]),
               float(animation.get("sprint_stride_length", 0))]
    speeds = [s / model.clip_times(n)[-1] if n else 0.0 for n, s in zip(names, strides)]
    return names, speeds


def window(actors, label):
    speeds = profile_speeds()
    failed = False
    print(f"\n2. window ({label}; world units/s -> clip x rate)")
    models = {}
    for actor in actors:
        model = models.setdefault(actor["model"], glb_pose.Model(glb_pose.Glb(ROOT / "assets_source" / actor["model"])
                                                                if not Path(actor["model"]).is_absolute()
                                                                else glb_pose.Glb(actor["model"])))
        names, clip_speeds = gaits(actor, model)
        scale = float(actor["scale"])
        walk, run = speeds[MONSTER[actor["descriptor"]]]
        cells = []
        for state, speed, hurrying in (("wander", walk, False), ("chase", run, True)):
            g = choose(speed / scale, clip_speeds, hurrying)
            rate = speed / scale / clip_speeds[g]
            bad = not WINDOW[0] <= rate <= WINDOW[1]
            failed |= bad
            cells.append(f"{state} {speed:.0f}: {names[g]} x{min(rate, MAX_RATE):.2f}"
                         + (f" (slides {rate / MAX_RATE:.2f})" if rate > MAX_RATE else "") + (" OUT" if bad else ""))
        print(f"  {actor['descriptor']:12} scale {scale:.0f}  " + "  ".join(cells))
        sweep = []
        for speed in range(100, 851, 50):
            row = []
            for hurrying in (False, True):
                g = choose(speed / scale, clip_speeds, hurrying)
                rate = speed / scale / clip_speeds[g]
                row.append(f"{names[g][:4]}{min(rate, MAX_RATE):.2f}" + ("!" if rate > MAX_RATE else ""))
            sweep.append(f"{speed}:{'/'.join(row)}")
        print("      sweep (calm/hurrying): " + " ".join(sweep))
    return failed


def paw_stride(model, clip):
    names = [n.get("name") for n in model.glb.json["nodes"]]
    T = model.clip_times(clip)[-1]
    ts = np.linspace(0, T, 121)
    out = []
    for paw in PAWS:
        P = np.array([np.asarray(model.world(model.sample(clip, t))[names.index(paw)])[:3, 3] for t in ts])
        z, y = P[:, 2], P[:, 1]
        vz = np.gradient(z, ts)
        stance = (y < y.min() + 0.25 * (y.max() - y.min())) & (vz < 0)
        out.append(-vz[stance].mean() * T if stance.any() else 0.0)
    return float(np.median(out)), out


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--set", action="append", default=[], metavar="KEY=VALUE")
    args = parser.parse_args()
    actors = yaml.safe_load((ROOT / "assets_dev/worlds/mm9/models/actors.yml").read_text())["actors"]
    mine = [a for a in actors if Path(a["model"]).name == MODEL]
    failed = []
    window(mine, "installed")
    settings = dict(item.split("=", 1) for item in args.set)
    new = copy.deepcopy(mine)
    for actor in new:
        actor["model"] = str(args.candidate.resolve())
        for key, value in settings.items():
            if key == "walking":
                actor["clips"]["walking"] = value
            else:
                actor["animation"][key] = float(value) if key.endswith("stride_length") else value
    model = glb_pose.Model(glb_pose.Glb(args.candidate.resolve()))

    print("\n1. stride (binding / floor vertices / paw joints, model units per loop)")
    for role, key in (("walking", "stride_length"), ("run", "run_stride_length"), ("sprint", "sprint_stride_length")):
        clip = new[0]["clips"]["walking"] if role == "walking" else new[0]["animation"].get(role)
        if not clip:
            continue
        bound = float(new[0]["animation"][key])
        measured, share = stride_audit.measure(model, clip)
        paws, each = paw_stride(model, clip)
        near = [v for v in (measured, paws) if v and abs(bound / v - 1) <= 0.1]
        bad = not near
        failed += ["stride"] if bad else []
        print(f"  {role:8} {clip:8} binding {bound:.3f}  vertices {measured if measured is None else round(measured, 3)}"
              f" (contact {share:.2f})  paws {paws:.3f} {[round(v, 3) for v in each]}" + ("  FAIL" if bad else ""))

    if window(new, "candidate"):
        failed.append("window")

    print("\n3. floor")
    for result in floor_audit.audit("mm9", None, 2.5, 0.01, new):
        print(f"  {result['descriptor']:12} " + ("; ".join(result["problems"]) + "  FAIL" if result["problems"]
                                                 else "ok"))
        if result["problems"]:
            failed.append("floor")
    print("FAILED: " + ", ".join(sorted(set(failed))) if failed else "PASSED")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
