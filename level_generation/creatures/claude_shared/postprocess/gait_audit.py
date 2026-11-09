#!/usr/bin/env python3
"""Walk/run choice and playback rate of every 3D actor binding of a world, as the game plays them.

Mirrors game/gameplay/ActorModelPresentation.h: an actor wanders at its monster_data.txt Spd, pursues at
PURSUE (2) times that and flees at FLEE (2) times, at most 1000 world units/s (the original doubles both). Its
hurried speed is the pursuit, or the flight for a Wimp (which only flees: peasants); actorModelGait picks walk, run or
the optional sprint from that and each clip's authored speed (stride over clip length); the clip then plays at speed /
authored speed, so the feet do not slide, up to the binding's `animation.gait_rate: [min, max]` (default
[0, MAX_RATE]; max 0 uncapped): above it the feet slide.
With --ruleset maw the speeds are MAW's: a melee monster faster than 150 moves at Spd / 2 + 300
(MawMonsterRules.cpp, hostile only; its calm wandering keeps Spd, the audit shows the hostile speed for both).
Reported per descriptor for wandering and chasing:

  clip, model speed (model units/s), playback rate, slide (body speed over what the capped clip covers; 1 = none)

    gait_audit.py [--world mm8] [--match <descriptor glob>] [--ruleset maw]

Flags (<<) a body with foot contact (gait_rate min 0) whose playback rate leaves [0.75, 1.5]: below, slow motion;
above, scurrying. Fliers and swimmers (min > 0) glide by design, and rolling bodies (ROLLING) look right at any rate.
A world whose actors.yml says `gait: intent` (MM9) plays the clip its AI asks for (actorModelIntendedGait: walk while
wandering, run or sprint while hurrying) while its rate stays within [1 / sqrt(max), max], else the best suited one; its monsters move at their
modifiers.yml `mm9_ai` walk_speed and run_speed (MM9's WalkVelocity and RunVelocity) where a row has them.
Run `stride_audit.py` first: the rates are only as right as the binding strides. Whatever stays flagged is clip
authoring: the clip covers far less (or more) ground per cycle than the game moves the monster. A summary per model
(every tier, wandering and chasing) follows the list. Exits non-zero when any binding is flagged.
"""
import argparse
import fnmatch
import math
from pathlib import Path
import sys

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "floor"))
import floor_audit  # noqa: E402
import glb_pose  # noqa: E402

ROOT = floor_audit.ROOT
# The playback rates that read as natural steps for a body with foot contact.
WINDOW = (0.75, 1.5)
# Bodies that roll: their contact follows the distance at any rate.
ROLLING = ("Malevolent Boulder*", "Juggernaut*")
# PursueMoveSpeedMultiplier and FleeMoveSpeedMultiplier (GameplayActorAiSystem.cpp): speed over Spd.
PURSUE = 2.0
FLEE = 2.0
# ActorModelDefaultMaxGaitRate: the playback-rate ceiling of a binding without `gait_rate`.
MAX_RATE = 2.0
PREFERENCE = math.log(1.25)
HOLD = math.log(1.08)


def misfit(speed, clip_speed):
    """actorModelGaitMisfit (ActorModelPresentation.h)."""
    rate = math.log(speed / clip_speed)
    return rate if rate >= 0 else -2 * rate


def gait(speed, clip_speeds, hurrying, current):
    """actorModelGait (ActorModelPresentation.h): index 0 walk, 1 run, 2 sprint; clip_speeds 0 for a missing clip."""
    if speed <= 0 or clip_speeds[0] <= 0 or clip_speeds[1] <= 0:
        return 1 if hurrying else 0
    best, best_misfit = 0, None
    for index, clip_speed in enumerate(clip_speeds):
        if clip_speed <= 0:
            continue
        value = misfit(speed, clip_speed) - (PREFERENCE if (index > 0) == hurrying else 0) \
            - (HOLD if index == current else 0)
        if best_misfit is None or value < best_misfit:
            best, best_misfit = index, value
    return best


def intended_gait(speed, clip_speeds, hurrying, current, max_rate):
    """actorModelIntendedGait (ActorModelPresentation.h): the AI's walk, or hurrying its run or sprint, when it fits
    (misfit at most the cap's); else the best suited clip when that fits or the AI's clip is too slow; else the AI's."""
    intended = 1 if hurrying else 0
    if speed <= 0 or clip_speeds[0] <= 0 or clip_speeds[1] <= 0:
        return intended

    def cost(index):
        return misfit(speed, clip_speeds[index]) - (HOLD if index == current else 0)

    if hurrying and clip_speeds[2] > 0 and cost(2) < cost(1):
        intended = 2

    def fits(index):
        return max_rate <= 0 or (clip_speeds[index] > 0 and cost(index) <= math.log(max_rate))

    if fits(intended):
        return intended
    best = gait(speed, clip_speeds, hurrying, current)
    return best if fits(best) or speed < clip_speeds[intended] else intended


def mm9_speeds(world):
    """Descriptor name -> (walk, run) from the world's modifiers.yml `mm9_ai` walk_speed and run_speed (its ids by the
    world's monster_descriptors.txt); empty for a world without them."""
    path = ROOT / f"assets_dev/worlds/{world}/modifiers.yml"
    if not path.exists():
        return {}
    names = {int(fields[0]): fields[1] for fields in
             floor_audit.read_table(ROOT / f"assets_dev/worlds/{world}/data_tables/monster_descriptors.txt")}
    speeds = {}
    for key, items in (yaml.safe_load(path.read_text()).get("monsters") or {}).items():
        first, _, last = str(key).partition("-")
        profile = next((item["mm9_ai"] for item in items if isinstance(item, dict) and "mm9_ai" in item), None)
        if profile is None or not profile.get("walk_speed"):
            continue
        for number in range(int(first), int(last or first) + 1):
            if number in names:
                speeds[names[number]] = (float(profile["walk_speed"]), float(profile.get("run_speed") or 0))
    return speeds


def monster_speeds(ruleset="standard"):
    """Descriptor name (monster_data.txt Picture) -> Spd of its first row; 0 for a stationary monster (Move "stand").
    ruleset "maw": a hostile melee monster faster than 150 moves at Spd / 2 + 300 (MawMonsterRules.cpp)."""
    speeds = {}
    for fields in floor_audit.read_table(ROOT / "assets_dev/engine/data_tables/monster_data.txt"):
        speed = 0 if fields[10].lower() in ("stand", "stationary") else int(fields[13])
        if ruleset == "maw" and speed > 150 and fields[19].strip() in ("", "0"):
            speed = speed + (400 - speed) // 2 + 100
        speeds.setdefault(fields[2], speed)
    return speeds


def hurry_multipliers():
    """Descriptor name -> its hurried speed over Spd: FLEE for a Wimp (it only flees), else PURSUE."""
    multipliers = {}
    for fields in floor_audit.read_table(ROOT / "assets_dev/engine/data_tables/monster_data.txt"):
        multipliers.setdefault(fields[2], FLEE if fields[11].lower() == "wimp" else PURSUE)
    return multipliers


def audit(world, match, actors=None, ruleset="standard"):
    """actors: the bindings to judge in place of the world's actors.yml (a model path may be absolute)."""
    manifest = yaml.safe_load((ROOT / f"assets_dev/worlds/{world}/models/actors.yml").read_text())
    actors = actors or manifest["actors"]
    follows_intent = manifest.get("gait") == "intent"
    sprite_scales = floor_audit.standing_sprite_scales()
    speeds = monster_speeds(ruleset)
    hurry = hurry_multipliers()
    for name, (walk, run) in mm9_speeds(world).items():
        speeds[name] = walk
        hurry[name] = run / walk if run > 0 else PURSUE
    models, results = {}, []
    for actor in actors:
        name = actor["descriptor"]
        animation = actor.get("animation") or {}
        if (match and not fnmatch.fnmatch(name, match)) or "stride_length" not in animation \
                or speeds.get(name, 0) <= 0:
            continue  # unmatched, not animated by distance, or stationary
        scale = float(actor["scale"])
        if "scale_reference" in actor:
            scale *= sprite_scales[name] / sprite_scales[actor["scale_reference"]]
        model = models.setdefault(actor["model"], glb_pose.Model(glb_pose.Glb(ROOT / "assets_source" / actor["model"])))
        walk_stride = float(animation["stride_length"])
        clips = [actor["clips"]["walking"], animation["run"], animation.get("sprint")]
        strides = [walk_stride, float(animation.get("run_stride_length", walk_stride * 1.55)),
                   float(animation.get("sprint_stride_length", 0.0))]
        clip_speeds = [stride / model.clip_times(clip)[-1] if clip else 0.0 for clip, stride in zip(clips, strides)]
        min_rate, max_rate = animation.get("gait_rate", [0.0, MAX_RATE])
        contact = min_rate == 0 and not any(fnmatch.fnmatch(name, pattern) for pattern in ROLLING)
        rows = []
        for label, world_speed, hurrying in (("wander", speeds[name], False),
                                             ("chase", min(hurry[name] * speeds[name], 1000), True)):
            speed = world_speed / scale
            current = 1 if hurrying else 0
            for _ in range(3):  # settle the hysteresis from the preferred clip
                current = intended_gait(speed, clip_speeds, hurrying, current, max_rate) if follows_intent \
                    else gait(speed, clip_speeds, hurrying, current)
            rate = speed / clip_speeds[current]
            played = max(min(rate, max_rate) if max_rate > 0 else rate, min_rate)
            rows.append({"state": label, "clip": clips[current], "speed": round(speed, 2),
                         "rate": round(played, 2), "slide": round(rate / played, 2)})
        flagged = contact and any(not WINDOW[0] <= row["rate"] <= WINDOW[1] for row in rows)
        results.append({"descriptor": name, "model": actor["model"], "walk_speed": round(clip_speeds[0], 2),
                        "run_speed": round(clip_speeds[1], 2), "sprint_speed": round(clip_speeds[2], 2),
                        "rows": rows, "flagged": flagged})
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--world", default="mm8")
    parser.add_argument("--match")
    parser.add_argument("--ruleset", choices=("standard", "maw"), default="standard")
    args = parser.parse_args()
    results = audit(args.world, args.match, ruleset=args.ruleset)
    for result in results:
        cells = "  ".join(f"{row['state']}: {row['clip']} {row['speed']:.2f} m/s x{row['rate']:.2f}"
                          + (f" slide {row['slide']:.2f}" if abs(row["slide"] - 1.0) > 0.005 else "")
                          for row in result["rows"])
        sprint = f" sprint {result['sprint_speed']:.2f}" if result["sprint_speed"] else ""
        print(f"{result['descriptor'][:34]:34} walk {result['walk_speed']:.2f} run {result['run_speed']:.2f}{sprint}  "
              f"{cells}"
              + ("  <<" if result["flagged"] else ""))
    flagged = [result for result in results if result["flagged"]]
    print(f"\n{len(results)} bindings, {len(flagged)} flagged (playback rate outside {WINDOW[0]}-{WINDOW[1]})")
    models = {}
    for result in flagged:
        models.setdefault(Path(result["model"]).name, []).append(result)
    if models:
        print(f"\n{len(models)} models flagged, worst first (rates over every tier, wandering / chasing):")

    def worst(rows):
        return max(max(row["rate"], 1 / row["rate"]) for result in rows for row in result["rows"])

    for model, rows in sorted(models.items(), key=lambda item: -worst(item[1])):
        wander = [result["rows"][0]["rate"] for result in rows]
        chase = [result["rows"][1] for result in rows]
        clips = sorted({row["clip"] for row in chase})
        print(f"  {model:26} {rows[0]['descriptor'][:28]:28} wander x{min(wander):.2f}-{max(wander):.2f}  "
              f"chase x{min(row['rate'] for row in chase):.2f}-{max(row['rate'] for row in chase):.2f} "
              f"({'/'.join(clips)})")
    return 1 if flagged else 0


if __name__ == "__main__":
    sys.exit(main())
