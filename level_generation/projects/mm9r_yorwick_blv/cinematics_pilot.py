#!/usr/bin/env python3
"""
Sven's battlefield speech (battlefield_sven) without a map conversion: writes yorwick.cinematics.yml and the installed
yorwick.lua as the changed converter would write it (regionlua.py: the battlefield() helper, the load that starts the
cinematic, the cutscene block) into the scratch root output/mm9_rework/cinematics_pilot_root (cutscenes.pilot).

The installed map has neither Sven nor the tableau (placements.py left them out before; the conversion adds both): the
scratch root's yorwick.scene.yml gets Sven as the actor the conversion would place (outdoor_blv.py npcs with
overrides.yml people: row 9249, its body from SVEN.abc, on the floor under his DAT position, the next actor index), so
his face and Talk cues play. The tableau's decorations stay missing there (they are in the BLV).

    python3 level_generation/projects/mm9r_yorwick_blv/cinematics_pilot.py
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools/mm9_import_discovery"))
import cutscenes  # noqa: E402

STEM = "yorwick"
spec = importlib.util.spec_from_file_location("regionlua_yorwick", PROJECT / "regionlua.py")
regionlua = importlib.util.module_from_spec(spec)
spec.loader.exec_module(regionlua)

OLD_LOAD = """-- Hidemodel.scr :Init (Prop2) shows the Penance Quest's prop once key 102 is held; Svenspeech.scr :Init with the
-- prize delivered (key 95) and the battle not seen (97) plays the battlefield cutscene, whose :Award (at Sven's
-- fourth line) gives key 97 and 114 000 experience: here the reward without the scene.
handlers.regionLoad = function()
    evt.SetSprite(400, (has(102)) and 1 or 0, "0")   -- Prop2 (hidemodel.scr "102 Unhide")
    if has(95) and not has(97) then reward(97, 114000, 0) end   -- Sven (svenspeech.scr)
end
"""


def new_load(sven_actor: int) -> str:
    lines = regionlua.battlefield_lines(sven_actor) + [
        "",
        "-- Hidemodel.scr :Init (Prop2) shows the Penance Quest's prop once key 102 is held.",
        "handlers.regionLoad = function()",
        "    evt.SetSprite(400, (has(102)) and 1 or 0, \"0\")   -- Prop2 (hidemodel.scr \"102 Unhide\")",
    ] + regionlua.battlefield_load_lines() + ["end", ""]
    return "\n".join(lines)


def floor_under(x: float, y: float, z_from: float):
    """The highest floor face under (x, y) below z_from in the installed BLV: (z, sector)."""
    from util.map_export import parse_blv_file
    blv = parse_blv_file(ROOT / f"assets_dev/worlds/mm9/maps/{STEM}.blv")["payload"]
    vertices = [(v["x"], v["y"], v["z"]) for v in blv["vertices"]]
    best = None
    for face in blv["faces"]:
        if face["is_portal"]:
            continue
        ring = [vertices[i] for i in face["vertex_indices"]]
        for k in range(1, len(ring) - 1):
            a, b, c = ring[0], ring[k], ring[k + 1]
            den = (b[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (b[1] - a[1])
            if abs(den) < 1e-9:
                continue
            u = ((x - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (y - a[1])) / den
            v = ((b[0] - a[0]) * (y - a[1]) - (x - a[0]) * (b[1] - a[1])) / den
            if u < -1e-6 or v < -1e-6 or u + v > 1 + 1e-6:
                continue
            z = a[2] + u * (b[2] - a[2]) + v * (c[2] - a[2])
            if z <= z_from and (best is None or z > best[0]):
                best = (z, face["room_number"])
    return best


def sven_scene() -> int:
    """The scratch root's yorwick.scene.yml with Sven appended (the conversion's people actor); his index."""
    from dungeon.bodies import mm9_bodies
    from mm9_monster_bodies import native_body
    scene = json.loads((ROOT / f"assets_dev/worlds/mm9/maps/{STEM}.scene.yml").read_text())
    actors = scene["initial_state"]["actors"]
    objects = cutscenes.Objects.load(STEM)
    values = objects.named(regionlua.SVEN)["values"]
    x, y, z = cutscenes.Frame(PROJECT).point(values["Pos"])
    floor, sector = floor_under(x, y, z + 24 * cutscenes.SCALE)
    height, radius = native_body(mm9_bodies().model_extents(values["Filename"])[1], float(values.get("Scale") or 1.0))
    template = next(a for a in actors if a.get("mm9_civilian") and a.get("immobile"))
    sven = json.loads(json.dumps(template))
    for key in ("mm9_rude_id",):
        sven.pop(key, None)
    sven.update({"actor_index": len(actors), "name": "Sven Svenssen", "monster_info_id": 9249, "monster_id": 9249,
                 "hp": 20, "height": height, "radius": radius,
                 "position": {"x": int(round(x)), "y": int(round(y)), "z": int(round(floor))},
                 "initial_yaw_units": 512, "sector_id": sector, "ally": (352 - 1) // 3 + 1,
                 "mm9_source_object_index": objects.named(regionlua.SVEN)["index"]})
    actors.append(sven)
    target = cutscenes.PILOT_ROOT / f"worlds/mm9/maps/{STEM}.scene.yml"
    if target.exists():
        target.unlink()
    target.write_text(json.dumps(scene, indent=1))
    print(f"scratch scene: Sven actor {sven['actor_index']} at {sven['position']} sector {sector}")
    return sven["actor_index"]


def main() -> int:
    sven_actor = sven_scene()
    scenes = regionlua.scenes(sven_actor)
    path = cutscenes.pilot(STEM, scenes, [(OLD_LOAD, new_load(sven_actor))])
    cinema = scenes[0].cinema
    print(f"{path}\n{cinema.id}: {cinema.shots_seconds:.2f} s, {len(cinema.shots)} shots, {len(cinema.cues)} cues, "
          f"steps {[(name, event) for name, _, event in scenes[0].steps]}")
    for cue in sorted(cinema.cues, key=lambda c: c["at"]):
        print(f"  {cue['at']:7.3f} {cue.get('note', '')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
