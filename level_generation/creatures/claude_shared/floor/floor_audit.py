#!/usr/bin/env python3
"""Floor contact of every 3D actor binding of a world (assets_dev/worlds/<world>/models/actors.yml), in world units.

For each descriptor it poses the installed source GLB (assets_source) at every key of the clips its binding plays and
reports the lowest visible point, scaled by the binding's effective scale (scale, times the standing sprite scale ratio
with scale_reference) and moved by z_offset and hover. The rules (README.md):

  ground actors   standing on the floor, walking never below it nor with every foot off it, corpse on the floor
  fliers/hoverers (canFly in monster_data.txt, or HOVERERS below) the lowest point over the living clips on the floor,
                  baked into the clips with floor_fix.py --hover (the amount printed as "suggested hover", model
                  units); the death clip eases it out and the corpse rests on the floor.
  swimmers        (S in monster_data.txt's Fly cell: MM9's AISwimFly rows) keep MM9's body: the clips' MM9 origin at the
                  centre of the body box (half the descriptor height up, floor_fix.py --swim), so a swimmer centred
                  in its water is drawn where MM9 draws it; the living clips hang below the box as MM9's do and are
                  not judged, nor is the death (it starts in the water); the corpse rests on the floor (it sinks to the bed).
  z_offset        bindings that keep a z_offset are listed as exceptions, never judged.
  dying           the death clip never sinks below the floor (except the notes in ACCEPTED). A binding with a
                  death_effect (burn, disintegration, explosion) leaves no ordinary corpse: its death and corpse are
                  not judged.

    floor_audit.py [--world mm8] [--match <descriptor glob>] [--tolerance 2.5] [--relative 0.01] [--json out.json]

The tolerance is the larger of --tolerance (world units) and --relative times the standing height. Exits non-zero when
a binding breaks a rule by more than it.
"""
import argparse
import fnmatch
import json
from pathlib import Path
import sys

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import glb_pose  # noqa: E402

ROOT = Path(__file__).resolve().parents[4]
LIVING_ROLES = ("standing", "walking", "attack_melee", "attack_ranged", "hit", "fidget")
# Descriptor families (descriptor without its tier letter) that hover by design without canFly.
HOVERERS = {
    "Efreeti": "a genie on a flame tail",
    "Dragon Turtle": "swims through the air with a bobbing stroke, as the native sprite floats",
    "MM9 Banshee": "floats on her dress (FlyRange.inc); the row has no canFly, so the AI keeps her on the ground",
}
# Families whose listed check ("dying" or "corpse") is reported as a note, not a problem, and why.
ACCEPTED = {
    ("Efreeti", "dying"): "the flame-vortex tail tip whips up to 14 cm under the floor for 0.3 s while the body "
                          "contracts into the flask; the body stays above it",
    ("SeaSerpent", "dying"): "the native death sinks the body away; no corpse remains",
    ("SeaSerpent", "corpse"): "Dead is fully sunk (no corpse, as the sprite)",
    ("ElemWater", "dying"): "the native sinking death; foam closes and no corpse remains",
    ("ElemWater", "corpse"): "no corpse (sunk)",
    ("zDemonQueen", "dying"): "she sinks as the rock collapses; the corpse satchel then removes the body",
    ("zDemonQueen", "corpse"): "sunk; removed by the corpse satchel",
    ("ElemFire", "corpse"): "the native corpse is empty: Dead holds everything shrunk away",
    ("ElemAir", "corpse"): "the native corpse is empty: Death thins it to nothing",
    ("Druidess", "corpse"): "the left leg keeps the source's 6 cm sink under the cloak, which lies on the floor",
    ("Druidess", "dying"): "the left leg dips up to 8 cm under the floor inside the cloak as she falls",
    ("Cleric", "dying"): "the legs dip up to 13 cm under the floor inside the cloak during the fall",
    ("ElemFire", "dying"): "only the FxEmbers effect cards drift under the floor in the last 0.05 s of the death",
}


def read_table(path):
    rows = []
    for line in path.read_text(encoding="latin-1").splitlines():
        fields = line.split("\t")
        if len(fields) > 10 and fields[0].strip().isdigit():
            rows.append([field.strip() for field in fields])
    return rows


def standing_sprite_scales():
    """Descriptor name -> scale of its standing sprite's first frame (the engine's scale_reference ratio)."""
    frames = {}
    paths = [ROOT / "assets_dev/engine/rendering/sprite_frame_data_common.yml"]  # MM6 monster sprites live here
    paths += sorted((ROOT / "assets_dev/engine/rendering/sprite_frames/monsters").glob("*.yml"))
    for path in paths:
        for sprite in (yaml.safe_load(path.read_text()) or {}).get("sprites", []):
            frames[sprite["sprite_name"].lower()] = float(sprite["frames"][0].get("scale", 1.0))
    scales = {}
    for fields in read_table(ROOT / "assets_dev/engine/data_tables/monster_descriptors.txt"):
        scales[fields[1]] = frames.get(fields[11].lower(), 1.0)
    return scales


def flying_descriptors(world=None, cell="Y"):
    """Descriptor names (monster_data.txt Picture) of monsters that fly (cell Y) or swim (cell S, MM9's swimmers: S or
    YS): the engine table plus a world's own monster_data contribution (MM9 appends its monsters in
    worlds/mm9/data_tables/monster_data.txt)."""
    paths = [ROOT / "assets_dev/engine/data_tables/monster_data.txt"]
    if world and (ROOT / f"assets_dev/worlds/{world}/data_tables/monster_data.txt").exists():
        paths.append(ROOT / f"assets_dev/worlds/{world}/data_tables/monster_data.txt")
    if cell == "S":
        return {fields[2] for path in paths for fields in read_table(path) if "S" in fields[9].upper()}
    return {fields[2] for path in paths for fields in read_table(path) if fields[9] == cell}


class ModelFloor:
    """Lowest visible point (model units) at every key of a model's clips, computed once per model."""

    def __init__(self, path):
        self.model = glb_pose.Model(glb_pose.Glb(path))
        self.series = {}

    def keyed(self, clip):
        """(time, lowest) at every key of the clip; lowest is None where nothing is visible (a hidden corpse)."""
        if clip not in self.series:
            self.series[clip] = [(time, self.model.lowest(clip, time)) for time in self.model.clip_times(clip)]
        return self.series[clip]

    def lows(self, clip):
        return [low for _, low in self.keyed(clip) if low is not None]


def audit(world, match, absolute, relative, actors=None):
    """actors: the bindings to judge in place of the world's actors.yml (a model path may be absolute)."""
    actors = actors or yaml.safe_load((ROOT / f"assets_dev/worlds/{world}/models/actors.yml").read_text())["actors"]
    sprite_scales = standing_sprite_scales()
    flying = flying_descriptors(world)
    swimming = flying_descriptors(world, "S")
    models, results = {}, []
    for actor in actors:
        name = actor["descriptor"]
        if match and not fnmatch.fnmatch(name, match):
            continue
        source = ROOT / "assets_source" / actor["model"]
        floor = models.setdefault(source, ModelFloor(source))
        scale = float(actor["scale"])
        if "scale_reference" in actor:
            scale *= sprite_scales[name] / sprite_scales[actor["scale_reference"]]
        clips = actor["clips"]
        animation = actor.get("animation") or {}
        living = {clips[role] for role in LIVING_ROLES if role in clips}
        living.update(animation[key] for key in ("run", "sprint", "cast") if key in animation)
        living &= set(floor.model.clips)
        z_offset = float(actor.get("z_offset", 0.0))
        lift = z_offset
        family = name[:-2] if name[-2:-1] == " " else name

        def world_lows(clip, extra):
            return [value * scale + extra for value in floor.lows(clip)] if clip in floor.model.clips else []

        standing = world_lows(clips["standing"], lift)
        walking = world_lows(clips["walking"], lift)
        living_min = min(min(floor.lows(clip)) for clip in living)
        dead = world_lows(clips["dead"], z_offset)
        top = max(floor.model.highest(clips["standing"], floor.model.clip_times(clips["standing"])[0]) * scale, 0.0)
        tolerance = max(absolute, relative * top)
        dying = [low * scale + z_offset for low in floor.lows(clips["dying"])]
        kind = "z_offset" if z_offset else "swimmer" if name in swimming \
            else "flier" if name in flying or family in HOVERERS else "ground"
        problems = []
        if kind == "ground":
            if abs(standing[0]) > tolerance:
                problems.append(f"standing at {standing[0]:+.1f}")
            if min(walking) < -tolerance:
                problems.append(f"walking sinks to {min(walking):+.1f}")
            if max(walking) > tolerance:
                problems.append(f"walking lifts every foot by {max(walking):+.1f}")
            for clip in living:
                low = min(floor.lows(clip)) * scale
                if low < -tolerance:
                    problems.append(f"{clip} sinks to {low:+.1f}")
        elif kind == "flier":
            low = living_min * scale + lift
            if abs(low) > tolerance:
                problems.append(f"living lowest at {low:+.1f} (suggested hover {-living_min:.6f})")
        notes = []
        judged = kind != "z_offset" and "death_effect" not in actor
        if judged and dead and abs(dead[-1]) > tolerance:
            (notes if (family, "corpse") in ACCEPTED else problems).append(f"corpse at {dead[-1]:+.1f}")
        # A swimmer's death starts in the water, where the floor is not the bed: only its corpse is judged.
        if judged and kind != "swimmer" and dying and min(dying) < -tolerance:
            (notes if (family, "dying") in ACCEPTED else problems).append(f"dying sinks to {min(dying):+.1f}")
        results.append({"descriptor": name, "model": actor["model"], "kind": kind, "scale": round(scale, 4),
                        "tolerance": round(tolerance, 2),
                        "z_offset": z_offset, "suggested_hover": round(-living_min, 6), "notes": notes,
                        "standing": [round(min(standing), 2), round(max(standing), 2)],
                        "walking": [round(min(walking), 2), round(max(walking), 2)] if walking else None,
                        "living_lowest": round(living_min * scale + lift, 2),
                        "dead": round(dead[-1], 2) if dead else None, "problems": problems})
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--world", default="mm8")
    parser.add_argument("--match", help="descriptor glob, e.g. 'Phoenix*'")
    parser.add_argument("--tolerance", type=float, default=2.5, help="world units (default 2.5)")
    parser.add_argument("--relative", type=float, default=0.01, help="of the standing height (default 0.01)")
    parser.add_argument("--json", type=Path, help="write the full results here")
    args = parser.parse_args()
    results = audit(args.world, args.match, args.tolerance, args.relative)
    for result in results:
        walking = result["walking"] or result["standing"]
        status = "; ".join(result["problems"]) or "ok" + "".join(f" (accepted: {note})" for note in result["notes"])
        print(f"{result['descriptor'][:34]:34} {result['kind']:8} stand {result['standing'][0]:+7.1f}..{result['standing'][1]:+7.1f}"
              f"  walk {walking[0]:+7.1f}..{walking[1]:+7.1f}  living {result['living_lowest']:+7.1f}"
              f"  dead {result['dead'] if result['dead'] is not None else '-':>6}  {status}")
    if args.json:
        args.json.write_text(json.dumps(results, indent=1) + "\n")
    failing = [result for result in results if result["problems"]]
    print(f"\n{len(results)} bindings, {len(failing)} with floor problems (tolerance {args.tolerance} world units or "
          f"{args.relative:g} of the standing height)")
    return 1 if failing else 0


if __name__ == "__main__":
    sys.exit(main())
