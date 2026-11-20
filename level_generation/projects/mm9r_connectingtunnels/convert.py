#!/usr/bin/env python3
"""
Connecting Tunnels, MM9 rework: MM9's CONNECTINGTUNNELS.dat as a native BLV on the shared dungeon converter
(../mm9r_common/dungeon, ../mm9r_common/DUNGEON_PLAYBOOK.md).

    python3 level_generation/projects/mm9r_connectingtunnels/convert.py            # build, compile, install
    python3 level_generation/projects/mm9r_connectingtunnels/convert.py --plan     # rooms only: work/rooms*.png

overrides.yml holds the model rules, the frame offset and the archway cuts (work/cuts/); this file adds the tunnels'
population (props.json from ../../props/mm9_connectingtunnels_claude, 38 actors with MM9's bodies) and the DAT's
object wiring as native Lua (the map has no .scr scripts: README.md, "Scripted objects"):
- the coffin (`coffin door left/right`, a RotatingDoor pair, Sticky): opening it unlocks TreasureChest1 inside, closing
  it locks it again (coffin door right's OpenTriggerTarget0 'unlock' / CloseTriggerTarget0 'lock');
- the rock fall (DestructableBrush0, HitPoints 10; its DeathTriggerTarget destroys DestructableBrush1): scene
  destructibles that weapons break (a click still does), the second with the first.

The frame: the DAT spans LT x -1 184..14 512 (native -3 031..37 151, over int16), so overrides.yml shifts native x by
17 000. The shared table writer (dungeon/tables.py) moves this map's exit volumes and the arrivals into it by the
offset (README, Frame).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))

import dungeon  # noqa: E402
from dungeon import lua  # noqa: E402
from dungeon.content import CHEST_EVENT  # noqa: E402
from dungeon.source import SCALE  # noqa: E402
from dungeon.bodies import placed_body  # noqa: E402

PROPS = PROJECT / "props.json"                   # the old map's frame (no offset): shifted here

EV_COFFIN, EV_ROCKFALL = 60, 61
COFFIN_CHEST = "TreasureChest1"
ROCKFALL = ("DestructableBrush0", "DestructableBrush1")
# The player light's stand-in (AGENT_BRIEF "No pitch-black rooms", README: Baked lighting). MM9 lights the party's
# surroundings with its player light (WorldProperties PlayerLightOn 1), which the native engine lacks; the tunnels far
# from any lantern have MM9 lightmaps of 0.03-0.08 and drew at screen luma 8.7-9.9 when matched (review b01). Each room
# below (an LT point in it) gets a sector minimum light level against the map's `ambient` 20, which the bake turns into
# an ambient floor of (31 - level) / 31 x 0.97 x the profile's ambient_scale x ambient_colour: level 14 about 1.55 times
# the map's floor (views 8.7-9.9 -> about 13), level 17 about 1.27 times (views 11-12 -> about 13). Level 10/15 (review
# v02) gave 15-16.5, as bright as the lit tunnels. Revert: ROOM_LEVELS = [] (rebuild and rebake).
ROOM_LEVELS = [
    *[(point, 14) for point in ((7995, -515, -5128), (4028, -460, -3968), (9027, -268, -1412), (2581, -140, -667),
                                (8896, -321, -293), (7904, -44, 464), (9384, -172, 1092), (-1019, 1708, 2384),
                                (2540, -150, -1250))],    # the last: the junction under the rock fall (a04, 8.9)
    *[(point, 17) for point in ((227, 564, -3038), (4838, -252, -2590), (448, 881, 2440), (955, 849, 2605))],
]
LANTERN_SCALE = 0.35                # the BrightScale of the tunnels' 45 mine-lantern lights (scale_lights)


class ConnectingTunnels(dungeon.Hooks):
    generator = "mm9r_connectingtunnels"
    mover_events = {"coffin": (EV_COFFIN, "click")}

    def destructible_events(self, build) -> dict:
        """DestructableBrush0's death runs EV_ROCKFALL (its DeathTrigger destroys DestructableBrush1)."""
        return {ROCKFALL[0]: (EV_ROCKFALL, 0)}

    # --- population -------------------------------------------------------------------------------------------------
    def populate(self, build) -> None:
        content, project = build.content, build.project
        if PROPS.exists():
            entries = json.loads(PROPS.read_text())
            for entry in entries:                     # props.json is in the old map's frame
                entry["x"] = round(entry["x"] - project.offset[0], 1)
                entry["y"] = round(entry["y"] - project.offset[1], 1)
                entry["z"] = round(entry["z"] - project.offset[2], 1)
            shifted = project.work / "props_native.json"
            shifted.write_text(json.dumps(entries, indent=1) + "\n")
            content.props(shifted)
        else:
            print("note: props.json is missing; no decorations or chests placed")
        self.scale_lights(build)
        levels = {content.owner(np.array(point, float)): level for point, level in ROOM_LEVELS}
        self.room_levels = levels
        write = build.package.write

        def write_with_levels(*args, **kwargs):
            for room in build.package.metadata["rooms"]:
                if room["id"] in levels:
                    room["min_ambient_light_level"] = levels[room["id"]]
            return write(*args, **kwargs)
        build.package.write = write_with_levels
        self.rock_centre = project.native(np.mean([np.array(build.source.models[m].points, float).mean(0)
                                                   for m in ROCKFALL], axis=0)).round().astype(int).tolist()

    def scale_lights(self, build) -> None:
        """MM9 weights each Light by its BrightScale: the 45 lantern lights (255/215/132) at 0.35, the 28 candle lights
        (47/47/255, radius 115 LT) at 0.8, two cyan lights at 1.0, the blue fills (0/73/147, 0/0/255) at 0.12-0.35. The
        shared converter writes the colour as authored. As Thjorad Mine: the BLV carries colour x min(1, BrightScale /
        0.35), the lanterns as authored (model lighting light_scale 1, MM9 lights its models at full colour) and the fills
        at their share; the capped fills are bake-only with the same weight (dungeon/lighting.py write_extra_lights:
        BrightScale / the median kept, 0.35). The candles and cyan lights cannot go over 255: they bake at 0.44 and 0.35
        of MM9's weight relative to the lanterns (README, Baked lighting)."""
        scale = {light["name"]: light["bright_scale"] for light in build.lights}
        for record in build.package.metadata["lights"]:
            factor = min(1.0, scale.get(record["id"], LANTERN_SCALE) / LANTERN_SCALE)
            record["color"] = [int(round(c * factor)) for c in record["color"]]
        for light in build.lights:
            light["colour_in_blv"] = [int(round(c * min(1.0, light["bright_scale"] / LANTERN_SCALE)))
                                      for c in light["colour"]]

    # --- actors -----------------------------------------------------------------------------------------------------
    def actors(self, build, sector_of_room: dict) -> list[dict]:
        content, source = build.content, build.source
        bases = content.monster_bases()
        out, self.bodies = [], {}
        for o in source.objects:
            if o["name"] not in bases:
                continue
            p, base = o["properties"], bases[o["name"]]
            changes = placed_body(base["monster_id"], p)        # MM9's body: the row's, or at the DAT's own Scale
            self.bodies[o["name"]] = changes or {k: base[k] for k in ("radius", "height")}
            actor = content.actor(o, base, sector_of_room, floor_query_lt=p["Pos"][1] + 24, **changes)
            actor["mm9_source_object_index"] = o["index"]
            out.append(actor)
        return out

    # --- map script -----------------------------------------------------------------------------------------------
    def map_script(self, build) -> str:
        script = lua.Script(build, "Connecting Tunnels")
        # MM9 names the coffin's leaves "coffin door left": the DOORS table keys them with underscores (Dook's Castle).
        script.door = {name.replace(" ", "_"): door for name, door in script.door.items()}
        index = next(i for i, line in enumerate(script.lines) if line.startswith("local DOORS = {"))
        script.lines[index] = "local DOORS = {" + ", ".join(f"{k} = {v}" for k, v in sorted(script.door.items())) + "}"
        script.lines.insert(index + 1, "local function sound(name) evt.PlaySoundName(name, 0, 0, 0) end")
        script.doors()
        coffin = " ".join(f"evt.SetDoorState({d}, DoorAction.Trigger)" for d in script.groups["coffin"])
        rock1 = build.source.by_name[ROCKFALL[1].lower()]["index"]
        script.add([
            "-- The coffin (RotatingDoor pair 'coffin door left/right', Sticky, PushOpen): a click swings both lids; opening",
            f"-- it unlocks {COFFIN_CHEST} inside (OpenTriggerTarget0 'unlock'), closing it locks it again (CloseTrigger0 'lock').",
            f"handlers[{EV_COFFIN}] = function()",
            f"    {coffin}",
            "    set(\"CoffinOpen\", 1 - var(\"CoffinOpen\"))",
            "end",
            "",
            "-- The rock fall (DestructableBrush0, HitPoints 10, DeathTriggerTarget DestructableBrush1 'Destroy'): scene",
            "-- destructibles; weapons (or a click) break DestructableBrush0, whose death breaks DestructableBrush1.",
            f"handlers[{EV_ROCKFALL}] = function()",
            "    set(\"RockFall\", 1)",
            f"    evt.DestroyDestructible({rock1})",
            f"    evt.SpawnWorldEffect(\"mm9:smoke\", {', '.join(map(str, self.rock_centre))}, 2)",
            "end",
            ""], (EV_COFFIN, "Coffin", "Coffin"), (EV_ROCKFALL, "Rocks", None))
        lines = ["-- Chests (MM9 TreasureChest objects; loot records in the scene)."]
        for c in build.content.report["chests"]:
            if c["anchor"] == COFFIN_CHEST:
                lines += [f"-- {COFFIN_CHEST} (Locked 1) lies in the coffin: it opens only while the coffin is open.",
                          f"handlers[{c['event']}] = function()",
                          f"    if var(\"CoffinOpen\") == 1 then evt.OpenChest({c['container_id']}) else "
                          "sound(\"door/locked_door01.wav\") evt.StatusText(\"The chest is locked.\") end",
                          "end"]
            else:
                lines.append(f"handlers[{c['event']}] = function() evt.OpenChest({c['container_id']}) end   -- {c['anchor']}")
            script.registrations.append((c["event"], "Chest", "Chest", "event"))
        script.add(lines + [""])
        return script.finish()

    def report(self, build) -> dict:
        return {"scripted": {"bodies": self.bodies,
                             "rock_centre": self.rock_centre}, "room_levels": self.room_levels}


if __name__ == "__main__":
    sys.exit(dungeon.main(PROJECT, ConnectingTunnels()))
