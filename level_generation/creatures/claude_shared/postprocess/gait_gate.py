#!/usr/bin/env python3
"""Gate for a new or changed walk/run/sprint of one installed 3D actor model, before it is installed.

Without --candidate it prints the targets: for every descriptor bound to the model and every ruleset (Standard, and
MAW, whose fast melee monsters move at Spd / 2 + 300), the speeds the game moves it at (model units per second;
wandering at its Spd, chasing at 2 times that, fleeing Wimps at 2), and the authored speed (stride over clip length) a
walk, a run and a sprint should have so that every tier plays inside the gait window: the walk for Standard's
wandering, the run for Standard's chasing, the sprint for MAW's chasing (the engine picks the clip that suits the speed,
gait_audit.gait). Only the stride decides the look in game (one loop per stride of travel), so author the stride: for a
clip of length T, stride = authored speed x T.

With --candidate it judges a candidate GLB in place of the installed one, with the binding changes given by --set
(applied to every descriptor of the model; `walking` is the walking role's clip, the others are `animation` keys):

  1. stride  the binding strides match what the planted feet cover (stride_audit.py: trusted, or within tolerance of
             one of its two measurements when they disagree, as for a robed body)
  2. window  every tier plays inside gait_audit.WINDOW, wandering and chasing, under Standard; MAW's chase (gait_audit.py)
  3. floor   the floor rules hold on every living clip (floor/floor_audit.py)

A stride left out of --set is taken from the trusted measurement when there is one. Prints the actors.yml values that
passed. Exits non-zero when a check fails.

    gait_gate.py --world mm8 --model mm8_m472.glb
    gait_gate.py --world mm8 --model mm8_m472.glb --candidate export/mm8_m472.glb --set walking=WalkRobe --set run=Jog
    gait_gate.py --world mm6 --model mm6_ogr.glb --candidate export/mm6_ogr.glb --set sprint=Sprint
"""
import argparse
import copy
import math
from pathlib import Path
import sys

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "floor"))
import floor_audit  # noqa: E402
import gait_audit  # noqa: E402
import stride_audit  # noqa: E402

ROOT = floor_audit.ROOT
TOLERANCE = 0.1
RULESETS = ("standard", "maw")


def bindings(world, model):
    actors = yaml.safe_load((ROOT / f"assets_dev/worlds/{world}/models/actors.yml").read_text())["actors"]
    return actors, [actor for actor in actors if Path(actor["model"]).name == model]


def targets(world, mine):
    sprite_scales = floor_audit.standing_sprite_scales()
    hurry = gait_audit.hurry_multipliers()
    wander, chase, sprint = [], [], []
    standard = gait_audit.monster_speeds("standard")
    for ruleset in RULESETS:
        speeds = gait_audit.monster_speeds(ruleset)
        for actor in mine:
            name = actor["descriptor"]
            if speeds.get(name, 0) <= 0:
                continue
            scale = float(actor["scale"])
            if "scale_reference" in actor:
                scale *= sprite_scales[name] / sprite_scales[actor["scale_reference"]]
            speed = speeds[name] / scale
            hurried = min(hurry[name] * speeds[name], 1000) / scale
            if ruleset == "standard":
                wander.append(speed)
                chase.append(hurried)
            elif speeds[name] != standard[name]:
                sprint.append(hurried)
            print(f"  {ruleset:8} {name:34} wander {speed:.2f}  chase {hurried:.2f} model units/s")
    if not wander:
        print("  stationary: no gait")
        return
    if not sprint:
        print("  MAW leaves these speeds unchanged: no sprint needed")
    low, high = gait_audit.WINDOW

    def fit(values):
        """(lowest, highest) authored speed that keeps every speed inside the window, and the middle of that range
        (in log terms); lowest > highest when no authored speed fits them all."""
        lowest, highest = max(values) / high, min(values) / low
        return lowest, highest, math.sqrt(lowest * highest)

    for label, values in (("walk", wander), ("run", chase), ("sprint (MAW chase)", sprint),
                          ("run or sprint, one clip", chase + sprint)):
        if not values:
            continue
        lowest, highest, middle = fit(values)
        print(f"{label} authored speed {middle:.2f} " + (f"(fits every tier from {lowest:.2f} to {highest:.2f})"
                                                         if lowest <= highest else
                                                         f"(no speed fits every tier: {lowest:.2f} > {highest:.2f})"))
    lowest, highest, middle = fit(wander + chase)
    if highest / lowest >= 1.05:
        print(f"one clip for both: {middle:.2f} (from {lowest:.2f} to {highest:.2f}); bind it as walk and run with "
              f"the same stride")
    else:
        print("one clip cannot serve both: wandering and chasing differ by about the window or more")


def apply(actors, mine, candidate, settings):
    actors = copy.deepcopy(actors)
    names = {actor["descriptor"] for actor in mine}
    for actor in actors:
        if actor["descriptor"] not in names:
            continue
        actor["model"] = str(candidate)
        for key, value in settings.items():
            if key == "walking":
                actor["clips"]["walking"] = value
            else:
                actor.setdefault("animation", {})[key] = float(value) if key.endswith("stride_length") else value
    return actors, [actor for actor in actors if actor["descriptor"] in names]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--world", required=True)
    parser.add_argument("--model", required=True, help="installed GLB name, e.g. mm8_m472.glb")
    parser.add_argument("--candidate", type=Path)
    parser.add_argument("--set", action="append", default=[], metavar="KEY=VALUE",
                        help="walking, run, sprint, stride_length, run_stride_length or sprint_stride_length")
    args = parser.parse_args()
    actors, mine = bindings(args.world, args.model)
    if not mine:
        sys.exit(f"no binding uses {args.model}")
    print(f"targets for {args.model}:")
    targets(args.world, mine)
    if not args.candidate:
        return 0
    settings = dict(item.split("=", 1) for item in args.set)
    actors, mine = apply(actors, mine, args.candidate.resolve(), settings)
    model = stride_audit.glb_pose.Model(stride_audit.glb_pose.Glb(args.candidate.resolve()))
    roles = [("stride_length", "walking", mine[0]["clips"]["walking"]),
             ("run_stride_length", "run", mine[0]["animation"]["run"])]
    if "sprint" in mine[0]["animation"]:
        roles.append(("sprint_stride_length", "sprint", mine[0]["animation"]["sprint"]))
    for key, clip_key, role in roles:
        # An unchanged clip keeps the stride it is bound with.
        if key in settings or (clip_key not in settings and key in mine[0]["animation"]):
            continue
        measured, _ = stride_audit.measure(model, role)
        feet = stride_audit.measure_feet(model, role)
        if measured and feet and abs(feet / measured - 1.0) <= stride_audit.AGREE:
            settings[key] = f"{measured:.4f}"
        else:
            sys.exit(f"{role}: no trusted stride (vertices {measured}, feet {feet}); pass --set {key}=<stride>")
    actors, mine = apply(actors, mine, args.candidate.resolve(), settings)
    failed = []

    print("\n1. stride")
    for result in stride_audit.audit(args.world, None, TOLERANCE, mine):
        measured = "-" if result["measured"] is None else f"{result['measured']:.3f}"
        feet = "-" if result["feet"] is None else f"{result['feet']:.3f}"
        strides = ", ".join(f"{binding['stride']:.3f}" for binding in result["bindings"])
        bad = result["flagged"] or result["doubtful"] or (result["measured"] is None and result["feet"] is None)
        print(f"  {result['clip']:20} measured {measured} feet {feet} trusted {result['trusted']}  binding {strides}"
              + ("  FAIL" if bad else ""))
        if bad:
            failed.append("stride")

    print("\n2. window")
    for ruleset in RULESETS:
        for result in gait_audit.audit(args.world, None, mine, ruleset):
            cells = "  ".join(f"{row['state']}: {row['clip']} x{row['rate']:.2f}"
                              + (f" slide {row['slide']:.2f}" if abs(row["slide"] - 1.0) > 0.005 else "")
                              for row in result["rows"])
            # MAW's faster wandering is for the walk and run to share; the gate holds its chase (the sprint's job).
            rows = result["rows"] if ruleset == "standard" else result["rows"][1:]
            bad = result["flagged"] and any(not gait_audit.WINDOW[0] <= row["rate"] <= gait_audit.WINDOW[1]
                                            for row in rows)
            print(f"  {ruleset:8} {result['descriptor']:34} {cells}" + ("  FAIL" if bad else ""))
            if bad:
                failed.append("window")

    print("\n3. floor")
    for result in floor_audit.audit(args.world, None, 2.5, 0.01, mine):
        print(f"  {result['descriptor']:34} " + ("; ".join(result["problems"]) + "  FAIL" if result["problems"]
                                                 else "ok"))
        if result["problems"]:
            failed.append("floor")

    print("\nactors.yml for every descriptor of the model: " + ", ".join(f"{key}: {value}"
                                                                         for key, value in settings.items()))
    print("FAILED: " + ", ".join(sorted(set(failed))) if failed else "PASSED")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
