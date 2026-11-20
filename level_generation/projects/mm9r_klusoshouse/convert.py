#!/usr/bin/env python3
"""
Klusos House, MM9 rework: MM9's KLUSOSHOUSE.dat as a native BLV on the shared dungeon converter
(../mm9r_common/dungeon, ../mm9r_common/DUNGEON_PLAYBOOK.md).

    python3 level_generation/projects/mm9r_klusoshouse/convert.py            # build, compile, install (review root)
    python3 level_generation/projects/mm9r_klusoshouse/convert.py --plan     # rooms only: work/rooms*.png

overrides.yml holds the model rules and the archway cut; this file adds the house's population (props.json from
../../props/mm9_klusoshouse_claude, 20 actors) and its scripted objects as native Lua, each citing its .scr (README.md,
"Scripted objects"):
- the Blackheart (Blackheart.scr): item 29 and key 223, the alarm bell; taking it breaks the guards' object link:
- the hidden guards (KlusosHidden.scr): invisible and not solid until the Blackheart is taken, then they appear;
- the sleepers (KlusosSleeper.scr): asleep (dormant) until the Blackheart is taken or they are hurt;
- the letter on the kitchen table (BookLetter.scr 456 Letter): MM9's "Post to the Kitchen".
"""

from __future__ import annotations

import csv
import dataclasses
import sys
from pathlib import Path

import numpy as np

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
import dungeon  # noqa: E402
from dungeon import lua  # noqa: E402
from dungeon.geometry import clip  # noqa: E402
from dungeon.source import ROOT, SCALE  # noqa: E402

PROPS = PROJECT / "props.json"
WINDOW_MODEL = "Transparent Window Grate13"
CEILING_SPLIT_AREA = 20000         # LT²: the ceilings over several rooms (split_at_walls)
WALL_SPLIT_AREA = 6000             # LT²: the long walls behind several rooms
LETTERS = ROOT / "mm9/extracted/DATA/DATA/BOOK AND SCROLL TEXT.csv"

EV_BLACKHEART, EV_LETTER = 75, 76
EV_GREAT_HALL_DOOR = 120            # RDoor2/RDoor6: no doorway portal (overrides.yml), so the map's own click event
# Blackheart.scr: giveitem 29 (the Elite Dagger), givekey 223. MM9 keeps Black's Heart (item 180) in TreasureChest1
# (fixed slot 1, trap 18), not on the mantel (user play-test 2026-11-06: the mantel gives the Elite Dagger, as in MM9).
KEY_BLACKHEART, ITEM_BLACKHEART = 223, 29
LETTER_ID = 456                                     # Prop46: BookLetter.scr "456 Letter"
GROUP_HIDDEN, GROUP_PATROL = 1, 2
# MM9's bodies (playbook: ABC AnimBinding extents x MONSTERS.txt Scale x 2.56): guard.abc (15, 36) LT half extents at
# Scale 1 for every GuardCaptain; Count Kluso's DAT model is PeasantM2.abc (12, 34).
BODIES = {"GuardCaptain": (15, 36), "Count": (12, 34)}


def lua_string(text: str) -> str:
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


def letter(number: int) -> tuple[str, str]:
    with open(LETTERS, newline="", encoding="latin-1") as stream:
        for row in csv.reader(stream):
            if row and row[0].strip() == str(number):
                return row[1].strip(), row[2].replace("\r", "").strip()
    raise SystemExit(f"letter {number}: not in {LETTERS}")


class KlusosHouse(dungeon.Hooks):
    generator = "mm9r_klusoshouse"
    mover_events = {"RDoor2": (EV_GREAT_HALL_DOOR, "click")}

    # --- geometry -------------------------------------------------------------------------------------------------
    def edit_polygons(self, build, polygons: list) -> list:
        """The west window's leaded pane (Transparent Window Grate13, window_03) faces out of the house, toward the
        hillside MM9 shows through it; outside is no air here, so the pane would be dropped and the window left a
        black hole. It is turned to face the room (the same ring reversed), drawn opaque as the Temple of Honk's
        skylight panes: the pane's light texels read as MM9's bright glass."""
        out = []
        for polygon in polygons:
            if polygon.model == WINDOW_MODEL and "window_03" in polygon.texture.lower():
                polygon = dataclasses.replace(polygon, points=polygon.points[::-1].copy(), keys=polygon.keys[::-1])
                self.window_flipped = getattr(self, "window_flipped", 0) + 1
            out.append(polygon)
        return self.split_at_walls(out)

    def split_at_walls(self, polygons: list) -> list:
        """The house's ceilings (one 320 LT polygon over the eight bedrooms and the corridors, one 144 LT polygon over
        the ground floor's rooms) and its long walls run over the partitions between rooms. The shared converter
        splits a face only where a second room holds 15 % of its samples, so each bedroom's share went to the corridor
        room and drew black from inside the bedroom (u02 of review v02). Each large ceiling is cut at the plane of every
        axis-aligned partition (48 LT or taller: not the beams) whose top meets it, and each long wall at every partition
        whose end meets it; a cut only splits the pieces the partition reaches. The pieces over or behind the
        partitions see no air and are dropped, the rest each lie in one room."""
        static = [p for p in polygons if p.role == "static"]
        walls = []
        for p in static:
            n = p.normal
            axis = next((a for a in (0, 2) if abs(n[a]) > 0.999), None)
            # partitions only: beams and cornices (16-32 LT tall) touch the ceiling too but stand inside rooms
            if axis is not None and np.ptp(p.points[:, 1]) >= 48:
                walls.append((axis, float(p.points[:, axis].mean()), p.points.min(0), p.points.max(0)))
        out, self.wall_splits = [], 0
        for polygon in polygons:
            n = polygon.normal
            ceiling = n[1] < -0.999
            wall_axis = next((a for a in (0, 2) if abs(n[a]) > 0.999), None)
            big = polygon.area >= (CEILING_SPLIT_AREA if ceiling else WALL_SPLIT_AREA)
            if polygon.role != "static" or not big or not (ceiling or wall_axis is not None):
                out.append(polygon)
                continue
            low, high = polygon.points.min(0), polygon.points.max(0)
            planes = []                  # (axis, coordinate, axis it must overlap along, low, high)
            for axis, coord, wlow, whigh in walls:
                if axis == wall_axis or not low[axis] + 4 < coord < high[axis] - 4:
                    continue
                if ceiling:              # a partition's top on the ceiling
                    third = 2 - axis
                    touches = abs(whigh[1] - low[1]) < 1.5
                else:                    # a partition's end on the wall
                    third = 1
                    touches = min(abs(wlow[wall_axis] - low[wall_axis]), abs(whigh[wall_axis] - low[wall_axis])) < 1.5
                if touches and wlow[third] < high[third] - 4 and whigh[third] > low[third] + 4:
                    planes.append((axis, round(coord, 2), third, float(wlow[third]), float(whigh[third])))
            pieces = [polygon]
            for axis, coord, third, wlow, whigh in sorted(set(planes)):
                normal = np.zeros(3)
                normal[axis] = 1.0
                cut = []
                for piece in pieces:
                    plow, phigh = piece.points[:, third].min(), piece.points[:, third].max()
                    if wlow < phigh - 4 and whigh > plow + 4:     # only pieces this wall actually meets
                        front, back = clip(piece, normal, coord, f"wall{axis}_{coord}")
                        cut += [part for part in (front, back) if part is not None]
                    else:
                        cut.append(piece)
                pieces = cut
            self.wall_splits += len(pieces) - 1
            out += pieces
        return out

    # --- population -------------------------------------------------------------------------------------------------
    def populate(self, build) -> None:
        if PROPS.exists():
            # the Blackheart is a world item (dungeon/pickups.py); its pickup runs EV_BLACKHEART
            build.content.props(PROPS, events={"Blackheart": EV_BLACKHEART, "Prop46": EV_LETTER})
        else:
            print("note: props.json is missing; no decorations or chests placed")
        report = build.content.report["omitted"]
        report.append({"anchor": "GuardTrigger", "class": "Trigger",
                       "reason": "a relay KlusosPatrol.scr's AlertOthers triggers to send 'charge' to the patrols; not "
                                 "built (the native AI pursues on sight; README, Scripted objects)"})

    # --- actors -----------------------------------------------------------------------------------------------------
    def actors(self, build, sector_of_room: dict) -> list[dict]:
        content, source = build.content, build.source
        bases = content.monster_bases()
        out, self.sleepers, self.hidden, self.patrols, self.actor = [], [], [], [], {}
        for o in source.objects:
            if o["name"] not in bases:
                continue
            name, p = o["name"], o["properties"]
            script = str(p.get("ScriptName") or "").lower()
            hidden = "klusoshidden" in script
            group = GROUP_HIDDEN if hidden else GROUP_PATROL if "klusospatrol" in script else 0
            half, tall = BODIES[o["class"]]
            scale = float(p.get("Scale", 1.0) or 1.0)
            actor = content.actor(o, bases[name], sector_of_room, group=group, hidden=hidden,
                                  floor_query_lt=p["Pos"][1] + 24,
                                  radius=int(round(half * scale * SCALE)), height=int(round(2 * tall * scale * SCALE)))
            if "klusossleeper" in script:
                actor["dormant"] = True          # LoopAnim sleep until OnObjectLinkBroken or OnDamage
                self.sleepers.append(actor["actor_index"])
            if hidden:
                self.hidden.append(actor["actor_index"])
            if group == GROUP_PATROL:
                self.patrols.append(actor["actor_index"])
            self.actor[name] = actor["actor_index"]
            out.append(actor)
        return out

    # --- map script -----------------------------------------------------------------------------------------------
    def map_script(self, build) -> str:
        script = lua.Script(build, "Klusos House")
        script.doors()
        script.chests()
        script.add([
            "-- RDoor2/RDoor6, the great hall's east door: a click swings both leaves (no doorway portal: the hall is one",
            "-- room with the gallery above it).",
            f"handlers[{EV_GREAT_HALL_DOOR}] = function() evt.SetDoorState(DOORS.RDoor2, DoorAction.Trigger); "
            "evt.SetDoorState(DOORS.RDoor6, DoorAction.Trigger) end",
            ""], (EV_GREAT_HALL_DOOR, "Door", "Door"))
        title, text = letter(LETTER_ID)
        sleepers = ", ".join(map(str, self.sleepers))
        script.add([
            f"-- The Blackheart (Blackheart.scr :OnUse): a world item ({ITEM_BLACKHEART}); its pickup gives key {KEY_BLACKHEART} "
            "and rings the alarm bell.",
            "-- Removing it breaks the guards' object link (KlusosHidden.scr, KlusosSleeper.scr :OnObjectLinkBroken): the "
            "hidden guards",
            "-- become visible and solid, the sleepers stand up; all run baseMelee.scr.",
            f"local SLEEPERS = {{{sleepers}}}",
            "local function linkBroken()",
            f"    evt.SetMonGroupBit({GROUP_HIDDEN}, MonsterBits.Invisible, false)",
            "    for _, index in ipairs(SLEEPERS) do evt.WakeActor(index) end",
            "end",
            f"handlers[{EV_BLACKHEART}] = function()",
            f"    if MM9.hasKey({KEY_BLACKHEART}) == 1 then return end",
            f"    MM9.giveKey({KEY_BLACKHEART})",
            "    evt.PlaySoundName(\"events/alarmbell.wav\", 0, 0, 0)",
            "    linkBroken()",
            "end",
            "",
            f"-- The letter on the kitchen table (BookLetter.scr, ScriptParams \"{LETTER_ID} Letter\": DoLetter {LETTER_ID}).",
            f"handlers[{EV_LETTER}] = function() evt.SimpleMessage({lua_string(title + chr(10) + chr(10) + text)}) end",
            "",
            ""],
            (EV_BLACKHEART, "Blackheart", None), (EV_LETTER, "Letter", "Letter"))
        return script.finish()

    def report(self, build) -> dict:
        return {"window_panes_turned": getattr(self, "window_flipped", 0), "wall_splits": getattr(self, "wall_splits", 0),
                "scripted": {"actors": self.actor, "sleepers": self.sleepers, "hidden": self.hidden,
                             "patrols": self.patrols}}


if __name__ == "__main__":
    sys.exit(dungeon.main(PROJECT, KlusosHouse()))
