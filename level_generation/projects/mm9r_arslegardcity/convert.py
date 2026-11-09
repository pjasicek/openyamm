#!/usr/bin/env python3
"""
Arslegard City, MM9 rework: MM9's ARSLEGARDCITY.dat as a native BLV open to the sky, on the shared dungeon converter
(../mm9r_common/dungeon) and its city extension (../mm9r_common/city, ../mm9r_common/CITY_PLAYBOOK.md).

    python3 level_generation/projects/mm9r_arslegardcity/convert.py            # build, compile, install (review root)
    python3 level_generation/projects/mm9r_arslegardcity/convert.py --plan     # rooms only: work/rooms*.png

overrides.yml holds the model rules and the city settings (roof line, cuts); this file adds what is Arslegard's own:

- **The frame offset.** The DAT spans native y -34 488..-5 734, over int16: overrides.yml `offset` shifts native y by
  +20 000. The shared writers keep the old map's frame, so this file moves props.json (written by the props project in
  the old frame) and the transition rows (the shared writer, dungeon/tables.py) by the same offset (the
  shared catalog writer moves the painted minimap's bounds).
- the bank counter's bars (thjorbars in an invisible shell): untouchable cut-out faces, so the teller behind them
  takes a click (The Arena's route);
- the population: props.json from ../../props/mm9_arslegardcity_claude, the townsfolk and shopkeepers with their
  RUDE dialogues (the old import's NPC records), Hanndl (two: the talking gatekeeper and the Great Gate's cinema
  actor behind the peephole), Sven Forkbeard, Njam the Meddler;
- the scripted objects as native Lua (citylua.py), each citing its .scr (README.md, "Scripted objects");
- the Great Gate scenes (FateMan.scr, WritMan.scr) as the camera cinemas gate_fate and gate_writ
  (gate_cinematics.py, built by citylua.map_script), installed as worlds/mm9/maps/arslegardcity.cinematics.yml
  (README.md, "Cinematics").
"""

from __future__ import annotations

import json
import struct
import sys
from pathlib import Path

import numpy as np
import yaml

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
sys.path.insert(0, str(PROJECT))
import cutscenes  # noqa: E402
import dungeon  # noqa: E402
import liquids  # noqa: E402
from city import structure  # noqa: E402
from city.hooks import CityHooks  # noqa: E402
from dungeon import tables  # noqa: E402
from dungeon.bodies import mm9_bodies  # noqa: E402
from dungeon.geometry import clip  # noqa: E402
from dungeon.source import ROOT, floor_below  # noqa: E402
from mm9_ai_placement import townsperson_walks  # noqa: E402
from mm9_monster_bodies import native_body  # noqa: E402
from transcode_mm9_dat_to_odm import mm9_npc_rude_id, read_mm9_npc_names  # noqa: E402

import citylua  # noqa: E402

PROPS = PROJECT / "props.json"                   # the old map's frame (no offset): shifted in populate
OLD_SCENE = ROOT / "assets_editor_dev/worlds/mm9/maps/arslegardcity.scene.yml"
NPC_NAMES = ROOT / "mm9/extracted/RUDE/RUDE/NPCNAME.rude"
FALLBACK_ROW = 367                  # the stand-in peasant row (Peasant Human2 MaleA), as Sturmford's
NJAM = "NjamtheMeddler0"
NJAM_ROW = 9261                     # MM9 261 Njam the Meddler
BARS_MODEL = "WorldObject4"         # the bank counter's bars (thjorbars) in an invisible shell
GROUP_TOWNSFOLK, GROUP_GATEKEEPER, GROUP_SVEN, GROUP_NJAM = 1, 2, 3, 4
AGGRESSOR_BIT = 0x00080000          # ActorAttribute aggressor (dungeon.content)
PEACEFUL_ALLY = (352 - 1) // 3 + 1  # monster type of row 352 (Peasant Human1 FemaleB A): neutral to the party
SPLIT_AREA_LT2 = 8000              # floors and ceilings this big are cut at the walls on them (split_at_walls)
SEAL_ABOVE_LT = 150                 # invisible wall strips above this (LT y) are solid in the voxel pass (edit_polygons)


def float_property(value) -> float:
    """A float MM9 stores in an int property (NPCNbr 1135181824 = 339.0)."""
    if isinstance(value, int) and abs(value) > 1_000_000:
        return struct.unpack("<f", struct.pack("<I", value & 0xFFFFFFFF))[0]
    return float(value or 0)


class ArslegardCity(CityHooks):
    generator = "mm9r_arslegardcity"
    mover_events = citylua.MOVER_EVENTS

    # --- geometry ---------------------------------------------------------------------------------------------------
    def edit_polygons(self, build, polygons: list) -> list:
        """The bank's bars: MM9 wraps the thjorbars brush in an invisible box (solid), which stops the indoor pick
        before the teller behind it (The Arena's 'talking through bars'). The box is dropped and the bars become an
        untouchable cut-out (role nonsolid; the scene hook draws them as translucent cut-outs); the counter under them
        keeps the party out. Then the city's half steps (CityHooks)."""
        kept, bars = [], 0
        for p in polygons:
            if p.model == BARS_MODEL:
                if p.role == "invisible":
                    continue
                p.role = "nonsolid"
                bars += 1
            kept.append(p)
        build.stats["bank_bar_faces"] = bars
        kept = polygons = split_at_walls(super().edit_polygons(build, kept), build.stats)
        # The voxel pass makes only static faces solid. MM9 closes a few wall tops under the eaves with Invisible.dtx
        # strips (a 32 LT strip between a hollow house's stucco and its roof, LT (4608..4864, 208..240, -13216)): the air
        # flood ran through it into the house's unbuilt, floorless inside, down under the whole city and out to the
        # border (leaked_to_border, 48 M voxels; tools/leak_path.py). Such strips (invisible, vertical, above LT 150)
        # are solid for the flood only: extra_portals gives them back their role before the faces are assigned.
        self.wall_strips = [q for q in kept if q.role == "invisible" and abs(q.normal[1]) < 0.3
                            and q.points[:, 1].min() >= SEAL_ABOVE_LT]
        for q in self.wall_strips:
            q.role = "static"
        build.stats["invisible_wall_strips_sealed"] = len(self.wall_strips)
        return polygons

    def extra_portals(self, build) -> list:
        """The sealed wall strips back to invisible (edit_polygons), then the city's open-air portals. The top portals
        are the shared merged ones (overrides.yml `city: {merged_top_portals: true}`, city/structure.py; 2026-11-01):
        this file's own cover (rectangles grown over solid, 1 024 -> 169 top portals, and every footprint cell kept as
        a barrier) is replaced by it."""
        for q in getattr(self, "wall_strips", []):
            q.role = "invisible"
        portals = structure.city_portals(build)
        report = getattr(build, "city_report", None) or {}
        print("city:", {k: v for k, v in report.items() if k not in ("tops", "cuts", "dropped_cuts")}, flush=True)
        return portals

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
            content.props(shifted, events=citylua.prop_events(build))
        else:
            print("note: props.json is missing; no decorations placed")
        self.pads = citylua.pads(self, build)

    # --- actors -----------------------------------------------------------------------------------------------------
    def actors(self, build, sector_of_room: dict) -> list[dict]:
        """Every person of the DAT: the old import's NPC records (row, name, RUDE dialogue), MM9's body (the object's
        model's initial dims x its Scale), RUDE ids from the object. All friendly and standing where MM9 placed them
        (MM9's wander rails are not carried), except Njam the Meddler: his own row, not hostile until the chase
        (NjamChase.scr: Addenemy player), his hostility type kept so the group bit makes him engage."""
        content, source = build.content, build.source
        old = {a["mm9_source_object_index"]: a for a in
               yaml.load(OLD_SCENE.read_text(), Loader=yaml.CSafeLoader)["initial_state"]["actors"]}
        names = read_mm9_npc_names(NPC_NAMES)
        bodies = mm9_bodies()
        out, self.actor, self.objects, self.rude = [], {}, {}, {}
        for o in source.objects:
            if o["class"] not in build.project.monster_classes:
                continue
            name, p = o["name"], o["properties"]
            record = old.get(o["index"])
            if record is not None:
                rude = int(record.get("mm9_rude_id") or 0)
                base = {key: record[key] for key in ("name", "attributes", "hp", "hostility_type", "monster_info_id",
                                                     "monster_id", "radius", "height", "move_speed")}
            else:
                rude = mm9_npc_rude_id({key: p.get(key) for key in ("DoRude", "ScriptName", "GreetingSound",
                                                                      "NPCNbr")})
                base = {"name": names.get(rude, name), "attributes": 0, "hp": 20, "hostility_type": 0,
                        "monster_info_id": FALLBACK_ROW, "monster_id": FALLBACK_ROW, "radius": 43, "height": 120,
                        "move_speed": 0}
            group, friendly = GROUP_TOWNSFOLK, True
            if o["class"] == "Hanndl":
                group = GROUP_GATEKEEPER
            elif o["class"] == "SvenSvenssen":
                group = GROUP_SVEN
            elif name == NJAM:
                group, friendly, rude = GROUP_NJAM, False, 0
                base["monster_id"] = base["monster_info_id"] = NJAM_ROW
                base["attributes"] = int(base["attributes"]) & ~AGGRESSOR_BIT
            extents = bodies.model_extents(str(p.get("Filename", "")))
            if extents is not None:
                height, radius = native_body(extents[1], float(p.get("Scale", 1.0) or 1.0))
                base["height"], base["radius"] = height, radius
            actor = content.actor(o, base, sector_of_room, group=group, friendly=friendly,
                                  floor_query_lt=p["Pos"][1] + 24)
            actor["mm9_source_object_index"] = o["index"]
            if rude:
                actor["mm9_rude_id"] = rude
            actor["immobile"] = not townsperson_walks(actor.get("mm9_ai") or {})
            if friendly:
                # Hanndl's picture row (555 Guard C) and Sven's are hostile to the party by the monster relation table
                # even with the aggressor bit clear (the actor refuses talk): every friendly actor takes the relations
                # of a peasant family (the Hall of the Gods' route).
                actor["ally"] = PEACEFUL_ALLY
            self.actor[name], self.objects[name], self.rude[name] = actor["actor_index"], o["index"], rude
            out.append(actor)
        return out

    # --- map script -------------------------------------------------------------------------------------------------
    def map_script(self, build) -> str:
        return citylua.map_script(self, build)

    def scene(self, build, scene: dict) -> None:
        super().scene(build, scene)
        sys.path.insert(0, str(ROOT))
        from util.map_export import parse_blv_file
        blv = parse_blv_file(build.runtime / build.project.map)["payload"]
        # The bank's bars: an untouchable cut-out (the texture's alpha), drawn two-sided.
        bars = sorted(f["index"] for f in blv["faces"] if "thjorbars" in str(f.get("texture_name", "")).lower()
                      or str(f.get("texture_name", "")).lower() == self.bars_alias(build))
        if bars:
            scene.setdefault("translucent_faces", []).append(
                {"faces": bars, "opacity": 1.0, "tint": [1.0, 1.0, 1.0], "two_sided": True})
        build.stats["bank_bar_translucent_faces"] = len(bars)
        liquids.apply(build, scene)

    @staticmethod
    def bars_alias(build) -> str:
        for texture, entry in build.source.aliases.items():
            if texture.endswith("thjorbars.dtx"):
                return str(entry["alias"]).lower()
        return "-"

    def report(self, build) -> dict:
        return dict(super().report(build),
                    scripted={"actors": self.actor, "objects": self.objects, "rude": self.rude,
                              "pads": getattr(self, "pads", {})})


def split_at_walls(polygons: list, stats) -> list:
    """Floors and ceilings that run on under (over) the walls between rooms, cut at those walls (Klusos House's
    split_at_walls for MM9's diagonal walls). MM9 lays one polygon over a whole block: the floor of the armour shop,
    Njam's house and the street between them (FloorBrick2, 651 762 LT2), the ceiling over the weapon shop and its
    neighbours (hostagebluebrick). The shared converter splits a face only at portal planes, so each went whole to one
    room and showed the sky through it from the others (the weapon shop's ceiling, review v03). Each horizontal face
    of at least SPLIT_AREA_LT2 is cut by the plane of every vertical wall (48 LT or taller, any direction) standing on
    it (a floor) or reaching up to it (a ceiling), wherever the wall's plan segment meets the piece; the pieces under
    the walls see no air and are dropped, the rest each lie in one room."""
    walls = []
    for p in polygons:
        if p.role != "static" or abs(p.normal[1]) > 0.05 or np.ptp(p.points[:, 1]) < 48:
            continue
        n = np.array([p.normal[0], 0.0, p.normal[2]])
        n /= np.linalg.norm(n)
        walls.append((n, float(n @ p.points[0]), p.points.min(0), p.points.max(0)))
    out, splits = [], 0
    for polygon in polygons:
        horizontal = abs(polygon.normal[1]) > 0.99
        if polygon.role != "static" or not horizontal or polygon.area < SPLIT_AREA_LT2:
            out.append(polygon)
            continue
        y = float(polygon.points[0, 1])
        floor = polygon.normal[1] > 0
        low, high = polygon.points.min(0), polygon.points.max(0)
        pieces = [polygon]
        for n, d, wlow, whigh in walls:
            touches = abs(wlow[1] - y) < 1.5 if floor else abs(whigh[1] - y) < 1.5
            if not touches or whigh[0] < low[0] + 4 or wlow[0] > high[0] - 4 or whigh[2] < low[2] + 4 \
                    or wlow[2] > high[2] - 4:
                continue
            cut = []
            for piece in pieces:
                plow, phigh = piece.points.min(0), piece.points.max(0)
                if whigh[0] < plow[0] + 4 or wlow[0] > phigh[0] - 4 or whigh[2] < plow[2] + 4 or wlow[2] > phigh[2] - 4:
                    cut.append(piece)
                    continue
                front, back = clip(piece, n, d, f"wall_{round(d, 1)}")
                cut += [part for part in (front, back) if part is not None]
            pieces = cut
        splits += len(pieces) - 1
        out += pieces
    stats["wall_splits"] = splits
    return out


def catch_transitions(transitions_text):
    """The shared writer (tables.transitions_text, which moves the rows into this map's frame by overrides.yml
    `offset`), then the chasm's catch row (add_catch_row)."""
    def wrapped(project, polygons, current_text, facings=None):
        text, changes = transitions_text(project, polygons, current_text, facings)
        lines = text.split("\n")
        header = next(line for line in lines if "\tSourceMapFile\t" in line)
        column = {name: i for i, name in enumerate(header.split("\t"))}
        add_catch_row(project, lines, column, changes)
        return "\n".join(lines), changes
    return wrapped


# ExitTrigger3 (DAT object 638, to Thjorgard): MM9's catch volume in the chasm through the city (the canal whose
# floor is sky, LT -320): a party that falls in lands in Thjorgard. The old import made no row for it; this map adds
# one, a copy of ExitTrigger4's row (the same destination, Thjorgard's default start) with its own volume: LT centre
# (3888, -287, -10000), Dims (2048, 32, 4096), reached down to the chasm's floor (-326) as `exits: bottom_lt` does.
CATCH_ROW = "mm9:transition/arslegardcity/638"
CATCH_LIKE = "mm9:transition/arslegardcity/648"
CATCH_BOX_LT = {"centre": (3888.0, -287.0, -10000.0), "dims": (2048.0, 32.0, 4096.0), "bottom": -326.0}


def add_catch_row(project, lines: list, column: dict, changes: list) -> None:
    rows = {line.split("\t")[0]: k for k, line in enumerate(lines) if line}
    like = rows.get(CATCH_LIKE)
    if like is None:
        return
    cells = lines[like].split("\t")
    (x, y, z), (dx, dy, dz) = CATCH_BOX_LT["centre"], CATCH_BOX_LT["dims"]
    top, low = (y + dy) * 2.56, CATCH_BOX_LT["bottom"] * 2.56
    centre = project.native([x, y, z])
    cells[column["CanonicalId"]] = CATCH_ROW
    cells[column["SourceObjectIndex"]] = "638"
    cells[column["SourceName"]] = "ExitTrigger3"
    cells[column["CenterX"]], cells[column["CenterY"]] = str(int(round(centre[0]))), str(int(round(centre[1])))
    cells[column["CenterZ"]] = str(int(round((top + low) / 2)))
    cells[column["HalfExtentX"]], cells[column["HalfExtentY"]] = str(int(round(dx * 2.56))), str(int(round(dz * 2.56)))
    cells[column["HalfExtentZ"]] = str(int(round((top - low) / 2)))
    cells[column["Provenance"]] = "dat+mm9r_arslegardcity"
    text = "\t".join(cells)
    if CATCH_ROW in rows:
        lines[rows[CATCH_ROW]] = text
    else:
        lines.insert(like + 1, text)
    changes.append({"id": CATCH_ROW, "source": project.map, "name": "ExitTrigger3", "facing": cells[column["FacingDegrees"]],
                    "destination": cells[column["DestinationMapFile"]],
                    "centre": [cells[column[c]] for c in ("CenterX", "CenterY", "CenterZ")],
                    "arrival": [cells[column[c]] for c in ("ArrivalX", "ArrivalY", "ArrivalZ")]})


if __name__ == "__main__":
    tables.transitions_text = catch_transitions(tables.transitions_text)
    hooks = ArslegardCity()
    code = dungeon.main(PROJECT, hooks)
    if code == 0 and not {"--plan", "--scratch"} & set(sys.argv) and getattr(hooks, "scenes", None):
        # The Great Gate's camera cinemas (citylua.map_script, gate_cinematics.py): the engine loads them beside the map
        print(f"cinematics installed: {cutscenes.install('arslegardcity', hooks.scenes)} (gate_fate, gate_writ)")
    sys.exit(code)
