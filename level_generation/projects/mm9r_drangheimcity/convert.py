#!/usr/bin/env python3
"""
Drangheim City, MM9 rework: MM9's DRANGHEIMCITY.dat as a native BLV open to the sky, on the shared dungeon converter
(../mm9r_common/dungeon) and its city extension (../mm9r_common/city, ../mm9r_common/CITY_PLAYBOOK.md).

    python3 level_generation/projects/mm9r_drangheimcity/convert.py            # build, compile, install (review root)
    python3 level_generation/projects/mm9r_drangheimcity/convert.py --plan     # rooms only: work/rooms*.png

overrides.yml holds the model rules, the glass and the city settings (roof line, hand cuts); this file adds what is
Drangheim's own: the air under the terrain taken out of the flood (terrain.py), the city's population (props.json from
../../props/mm9_drangheimcity_claude, the townsfolk with their RUDE dialogues, Sigmund, the bandit Guaire A'Velsi), the
three ladders (one of them diagonal) and the scripted objects as native Lua (citylua.py), each citing its .scr
(README.md, "Scripted objects").
"""

from __future__ import annotations

import json
import math
import struct
import sys
from pathlib import Path

import numpy as np
import yaml

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
sys.path.insert(0, str(PROJECT))
import dungeon  # noqa: E402
from city.hooks import CityHooks  # noqa: E402
from dungeon.bodies import mm9_bodies  # noqa: E402
from dungeon.rotation import DEFAULT_REACH, grabs_at_top  # noqa: E402
from dungeon.source import ROOT, SCALE  # noqa: E402
from mm9_ai_placement import townsperson_walks  # noqa: E402
from mm9_monster_bodies import native_body  # noqa: E402
from transcode_mm9_dat_to_odm import mm9_npc_rude_id, read_mm9_npc_names  # noqa: E402

import citylua  # noqa: E402
import terrain  # noqa: E402
from city import structure  # noqa: E402
from dungeon import build as dungeon_build  # noqa: E402
from collections import Counter  # noqa: E402

from dungeon.geometry import clip, sample_polygon  # noqa: E402
from dungeon.rooms import label_rooms  # noqa: E402
from scipy import ndimage  # noqa: E402

PROPS = PROJECT / "props.json"
OLD_SCENE = ROOT / "assets_editor_dev/worlds/mm9/maps/drangheimcity.scene.yml"
NPC_NAMES = ROOT / "mm9/extracted/RUDE/RUDE/NPCNAME.rude"

# NPC rows for objects the old import did not place: the stand-in peasant row 367 (Peasant Human2 MaleA), as Sturmford.
FALLBACK_ROW = 367
BANDIT = "CommonerElfMaleA1"        # Guaire A'Velsi (class Bandit, NPC95.scr): Atli's assassination target
BANDIT_HP = 300                     # NPC95.scr :Init setstat Hitpoints 300 (AC 50)
GROUP_TOWNSFOLK, GROUP_BANDIT = 1, 2
PEASANT_ROWS = range(301, 383)      # the Peasant family rows (monster_data.txt)
PEACEFUL_ALLY = (352 - 1) // 3 + 1   # monster type of row 352 (Peasant Human1 FemaleB A): neutral to the party

# Ladders not along an axis (overrides.yml `ladders` takes only those): MM9's Ladder volumes with their rung objects.
# TowerLadder1 climbs to the walkway along the north wall (Klusos House's window at its end): its rung face (WorldObject2)
# runs from LT (6609, -3166) to (6743, -3325); the climber faces it from the face's front. HouseLadder stands in a corner
# of the diamond-shaped small house (SmalHouse1) against its south-west wall (rungs WorldObject5, a 29 LT box) and climbs
# from the ground floor (576) to the loft (744) beyond that wall; the climber faces south-west. top_exit_lt: where the
# party stands after climbing off (on the walkway at 920, on the loft at 744).
# TowerLadder1 leans (its top 170 LT on from its foot): the engine climbs it along the line from foot to top, out from
# under the walkway's landing that overhangs its foot (devdocs/INDOOR_ROTATING_MOVERS_AND_LADDERS.md, "Leaning
# ladders"). It rises through a slot in the walkway; the top exit is on the walkway beside its top, and `grab_at_top`
# takes a party walking from there toward the top back down (the only way down for one arriving by the window).
# `grab_at_top` (optional) defaults to the shared `grabs_at_top`, as for the ladders of overrides.yml.
DIAGONAL_LADDERS = {
    "TowerLadder1": {"rungs": "WorldObject2", "top_exit_lt": [6768, 922, -3258]},
    "HouseLadder": {"rungs": "WorldObject5", "facing_lt": [-0.7071, -0.7071], "top_exit_lt": [3965, 746, -3565]},
}


def float_property(value) -> float:
    """A float MM9 stores in an int property (NPCNbr 1118699520 = 87.0)."""
    if isinstance(value, int) and abs(value) > 1_000_000:
        return struct.unpack("<f", struct.pack("<I", value & 0xFFFFFFFF))[0]
    return float(value or 0)


class DrangheimCity(CityHooks):
    generator = "mm9r_drangheimcity"
    mover_events = citylua.MOVER_EVENTS

    # --- geometry ---------------------------------------------------------------------------------------------------
    def extra_portals(self, build) -> list:
        """The air under the terrain out of the flood first (terrain.py), then the city's open-air portals. Keeps the
        open air's voxels (the districts, as city/structure.py finds them) for the face fix below."""
        self.terrain_report = terrain.prune_underground(build)
        print("underground air:", {k: v for k, v in self.terrain_report.items() if k != "seeds_under_terrain"},
              "seeds under the terrain:", [s["name"] for s in self.terrain_report["seeds_under_terrain"]])
        labels, count = label_rooms(build.grid, build.air, build.portals)
        sizes = ndimage.sum(np.ones_like(labels), labels, range(count + 1))
        districts = [r for r in range(1, count + 1) if sizes[r] >= structure.settings_of(build.project)[
            "district_min_voxels"]]
        OPEN_AIR["voxels"] = np.isin(labels, districts)
        return super().extra_portals(build)

    # --- population -------------------------------------------------------------------------------------------------
    def populate(self, build) -> None:
        content = build.content
        if PROPS.exists():
            content.props(self.lifted_props(build), events=citylua.prop_events(build), cogs=citylua.prop_cogs(build))
        else:
            print("note: props.json is missing; no decorations placed")
        self.points = citylua.marker_points(build)

    def lifted_props(self, build) -> Path:
        """props.json with the burning logs' bases on their hearths: MM9 sinks the log piles 15-31 units into the hearth
        floor and the BLV drew none of them (v02: every fireplace empty); lifted onto the floor under them they draw.
        Written to work/props_lifted.json (props.json stays the props project's, fitted against the old bake)."""
        entries = json.loads(PROPS.read_text())
        lifted = {}
        for entry in entries:
            if entry["prop"] != "logsburning":
                continue
            lt = build.project.lt_from_native((entry["x"], entry["y"], entry["z"]))
            floor = build.content.floor_at(lt[0], lt[2], lt[1] + 40)
            if floor is None:
                continue
            z = round(floor * SCALE - build.project.offset[2], 1)
            if z > entry["z"]:
                lifted[entry["source_name"]] = round(z - entry["z"], 1)
                entry["z"] = z
        build.content.report["logs_lifted"] = lifted
        path = build.project.work / "props_lifted.json"
        path.write_text(json.dumps(entries, indent=1) + "\n")
        return path

    # --- actors -----------------------------------------------------------------------------------------------------
    def actors(self, build, sector_of_room: dict) -> list[dict]:
        """Every person of the DAT: the old import's NPC records (row, name, RUDE dialogue) where it placed them (its
        actor for the AmbientSound "Dog0" was an importer slip and is not carried), MM9's body (the object's model's
        initial dims x its Scale), RUDE ids from the object. All friendly; townsfolk stand where MM9 placed them (MM9's
        wander rails are not carried). The bandit Guaire A'Velsi is hidden until Atli gives his task (NPC95.scr)."""
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
            group, hidden = GROUP_TOWNSFOLK, False
            if name == BANDIT:
                # NPC95.scr: Guaire A'Velsi (RUDE 95 on a click), shown with key 222, removed with 225 (his death)
                group, hidden, rude = GROUP_BANDIT, True, 95
                base.update(name="Guaire A'Velsi", hp=BANDIT_HP)
            extents = bodies.model_extents(str(p.get("Filename", "")))
            if extents is not None:
                height, radius = native_body(extents[1], float(p.get("Scale", 1.0) or 1.0))
                base["height"], base["radius"] = height, radius
            actor = content.actor(o, base, sector_of_room, group=group, friendly=True, hidden=hidden,
                                  floor_query_lt=p["Pos"][1] + 24)
            actor["mm9_source_object_index"] = o["index"]
            if rude:
                actor["mm9_rude_id"] = rude
            actor["immobile"] = name != BANDIT and not townsperson_walks(actor.get("mm9_ai") or {})
            if base["monster_id"] not in PEASANT_ROWS:
                # Sigmund's picture row 403 (Swordsman A) and Guaire's 9101 (MM9 Bandit) belong to families the
                # relation table may set against the party: they take a peasant family's relations (Hall of the Gods'
                # and Thjorgard City's route), so a click talks to them
                actor["ally"] = PEACEFUL_ALLY
            self.actor[name], self.objects[name], self.rude[name] = actor["actor_index"], o["index"], rude
            out.append(actor)
        self.records = out
        return out

    # --- map script -------------------------------------------------------------------------------------------------
    def map_script(self, build) -> str:
        return citylua.map_script(self, build)

    def scene(self, build, scene: dict) -> None:
        super().scene(build, scene)
        ladders = [self.diagonal_ladder(build, name, rule) for name, rule in DIAGONAL_LADDERS.items()]
        scene.setdefault("ladders", []).extend(ladder for ladder in ladders if ladder)

    def diagonal_ladder(self, build, name: str, rule: dict) -> dict | None:
        """A scene ladder from a rung object: facing from overrides (facing_lt) or from the rung face's normal (the
        climber stands in front of it and faces it), bottom and top on the rungs' centre line, offset to the climber's
        side by half the rung object's depth."""
        source = build.source
        if rule["rungs"] not in source.models:
            return None
        rungs = [p for p in source.polygons(rule["rungs"]) if "ladder" in p.texture.lower()]
        if not rungs:
            return None
        pts = np.concatenate([p.points for p in rungs])
        if "facing_lt" in rule:
            facing = np.array([rule["facing_lt"][0], 0.0, rule["facing_lt"][1]], float)
        else:
            facing = -rungs[0].normal.copy()
            facing[1] = 0.0
        facing /= np.linalg.norm(facing)
        across = np.array([-facing[2], 0.0, facing[0]])
        depth = float(np.ptp(pts @ facing))
        # bottom and top on the rungs' climber-side face: a leaning ladder (TowerLadder1's face slopes, normal y 0.41)
        # has its top 160 LT further on than its foot
        low_pts = pts[pts[:, 1] <= pts[:, 1].min() + 1]
        high_pts = pts[pts[:, 1] >= pts[:, 1].max() - 1]
        offset = facing * (depth / 2) if "facing_lt" in rule else np.zeros(3)
        bottom = low_pts.mean(0) - offset
        top = high_pts.mean(0) - offset
        native = build.project.native
        record = {"id": name, "bottom": [round(float(v), 2) for v in native(bottom)],
                  "top": [round(float(v), 2) for v in native(top)],
                  "facing_degrees": round(math.degrees(math.atan2(facing[2], facing[0])) % 360.0, 2),
                  "width": round(min(max(float(np.ptp(pts @ across)) * SCALE, 60.0), 400.0), 2), "reach": DEFAULT_REACH,
                  "top_exit": [round(float(v), 2) for v in native(np.asarray(rule["top_exit_lt"], float))]}
        if rule.get("grab_at_top", grabs_at_top(record)):
            record["grab_at_top"] = True
        build.content.report.setdefault("diagonal_ladders", {})[name] = record
        return record

    def report(self, build) -> dict:
        (build.project.work / "interior_faces_moved.json").write_text(
            json.dumps({"moved": build.log.get("interior_faces_moved", []),
                        "split": build.log.get("interior_faces_split", []),
                        "watch": build.log.get("interior_faces_watch", [])}, indent=0) + "\n")
        return dict(super().report(build), terrain=getattr(self, "terrain_report", None),
                    scripted={"actors": self.actor, "objects": self.objects, "rude": self.rude})


OPEN_AIR = {}                       # the districts' voxels of this run (DrangheimCity.extra_portals)
WATCH_LT = np.array([7711.0, 469.0, -2436.0])   # a face logged by the fix (work/interior_faces_moved.json "watch")


def interior_faces(assign_faces):
    """Faces of thin walls (under a voxel) between a walk-in interior and the open air: the shared assignment
    (rooms.NearestRoom.front, nearest labelled voxel) gave some interior faces near the ceilings to the street room
    outside (the blacksmith's and the town hall's upper walls: sky through them in v02). After it, a face given to an
    open-air room whose air straight ahead (1-2 voxels along its normal) is an interior room in 60 % or more of the
    samples that find air goes to that room (the tower's thin inner wall over the town hall, above the roof line:
    sky through it in v03). A wall face whose samples see the interior below a height and the open air above it is
    split there (the tower's outer wall rising out of the town hall, v07). Map-local (wraps the shared function for this run only)."""
    def wrapped(rooms, polygons, portals, stats, log, **settings):
        result = assign_faces(rooms, polygons, portals, stats, log, **settings)
        open_air = OPEN_AIR.get("voxels")
        if open_air is None:
            return result
        labels, grid = rooms.labels, rooms.grid
        # a room is open air when most of its voxels are the districts' (a door portal's barrier voxels take a
        # neighbour's label, so "any voxel" would count an interior beside a door into the open air)
        counts = np.bincount(labels[labels > 0], minlength=int(labels.max()) + 1)
        in_open = np.bincount(labels[open_air & (labels > 0)], minlength=int(labels.max()) + 1)
        open_rooms = set(int(r) for r in np.flatnonzero(in_open > 0.5 * np.maximum(counts, 1)))
        moved, split = [], []
        out = []
        queue = [(polygon, 0) for polygon in result]
        while queue:
            polygon, depth = queue.pop()
            lo, hi = polygon.points.min(0), polygon.points.max(0)
            watched = bool(np.all(lo - 2 <= WATCH_LT) and np.all(WATCH_LT <= hi + 2))
            if polygon.label not in open_rooms or polygon.role == "glass":
                out.append(polygon)
                continue
            samples = sample_polygon(polygon.points, 12.0)
            ahead = []
            for reach in (1.0, 1.5, 2.0):
                cells = grid.index(samples + polygon.normal * grid.size * reach)
                ahead.append(labels[cells[:, 0], cells[:, 1], cells[:, 2]])
            per_sample = np.stack(ahead, axis=1)
            ahead = per_sample.ravel()
            air = ahead[ahead > 0]
            inside = air[~np.isin(air, list(open_rooms))]
            if watched:
                log.setdefault("interior_faces_watch", []).append(
                    {"label": int(polygon.label), "lo": lo.round().tolist(), "hi": hi.round().tolist(),
                     "normal": polygon.normal.round(2).tolist(), "samples": len(samples), "depth": depth,
                     "ahead": {int(k): int(v) for k, v in Counter(ahead.tolist()).items()}})
            if len(air) >= 0.3 * len(ahead) and len(inside) >= 0.6 * len(air):
                room = int(np.bincount(inside).argmax())
                moved.append({"texture": polygon.texture.split("\\")[-1],
                              "centre_lt": polygon.points.mean(0).round(1).tolist(), "from": int(polygon.label),
                              "to": room, "area_lt": round(polygon.area)})
                polygon.label = room
                out.append(polygon)
                continue
            # A wall that sees an interior over part of its height and the open air over the rest (the tower's outer
            # wall rising out of the town hall and past the mayor's floor): cut it at the first change between them
            # going up, and look at both pieces again.
            if abs(polygon.normal[1]) < 0.5 and len(inside) >= 3 and depth < 8:
                best = []
                for row in per_sample:
                    found = [v for v in row if v > 0]
                    best.append(Counter(found).most_common(1)[0][0] if found else 0)
                best = np.array(best)
                kind = np.where(best == 0, 0, np.where(np.isin(best, list(open_rooms)), 2, 1))
                heights = np.unique(np.round(samples[kind > 0, 1], 1))
                rows = [(y, set(kind[(np.abs(samples[:, 1] - y) < 0.05) & (kind > 0)].tolist())) for y in heights]
                cut = None
                for (y0, k0), (y1, k1) in zip(rows, rows[1:]):
                    if k0 != k1 and len(k0) == 1 and len(k1) == 1:
                        cut = (y0 + y1) / 2
                        break
                if cut is not None:
                    upper, lower = clip(polygon, np.array([0.0, 1.0, 0.0]), cut, "interior_split")
                    if upper is not None and lower is not None:
                        upper.label = lower.label = polygon.label
                        split.append({"texture": polygon.texture.split("\\")[-1],
                                      "centre_lt": polygon.points.mean(0).round(1).tolist(), "cut_lt": round(float(cut), 1)})
                        queue += [(upper, depth + 1), (lower, depth + 1)]
                        continue
            out.append(polygon)
        result[:] = out
        stats["interior_faces_split_at_ceiling"] = len(split)
        log["interior_faces_split"] = split
        stats["interior_faces_moved_from_open_air"] = len(moved)
        log["interior_faces_moved"] = moved
        return result
    return wrapped


def grow_exits(transitions_text):
    """Klusos House's window (ExitTrigger1, a 16 LT thick box in the window's plane, z -3976..-3944) is touched by MM9's
    party box from the north wall's walkway; the native exit tests the party's centre, which the window frame keeps
    short of the box. The row's box reaches EXIT_GROW_LT further onto the walkway (the Training Hall's route,
    map-local: the shared writer keeps MM9's box)."""
    def wrapped(project, polygons, current_text, facings=None):
        text, changes = transitions_text(project, polygons, current_text, facings)
        lines = text.split("\n")
        header = next(line for line in lines if line.startswith("CanonicalId") or "\tSourceMapFile\t" in line)
        column = {name: i for i, name in enumerate(header.split("\t"))}
        for k, line in enumerate(lines):
            cells = line.split("\t")
            if len(cells) < len(column) or cells[column["SourceMapFile"]] != project.map:
                continue
            grow = EXIT_GROW_LT.get(cells[column["SourceName"]])
            if grow is None:
                continue
            for axis, amount in zip("XYZ", grow):          # native axes: a negative amount grows toward -axis
                if amount:
                    centre, half = float(cells[column[f"Center{axis}"]]), float(cells[column[f"HalfExtent{axis}"]])
                    low, high = centre - half, centre + half
                    low, high = (low + amount * SCALE, high) if amount < 0 else (low, high + amount * SCALE)
                    cells[column[f"Center{axis}"]] = str(int(round((low + high) / 2)))
                    cells[column[f"HalfExtent{axis}"]] = str(int(round((high - low) / 2)))
            lines[k] = "\t".join(cells)
        return "\n".join(lines), changes
    return wrapped


EXIT_GROW_LT = {"ExitTrigger1": (0, -48, 0)}      # native y = LT z: 48 LT south onto the walkway


if __name__ == "__main__":
    from dungeon import tables
    tables.transitions_text = grow_exits(tables.transitions_text)
    dungeon_build.assign_faces = interior_faces(dungeon_build.assign_faces)
    hooks = DrangheimCity()
    code = dungeon.main(PROJECT, hooks)
    if code == 0 and not {"--plan", "--scratch"} & set(sys.argv):
        # Hrolf and Alfrigg's quarrel (citylua.scenes): the engine loads it beside the map
        import cutscenes
        monsters = {name: hooks.records[hooks.actor[name]]["monster_id"] for name in ("Hrolf", "Alfrigg")}
        print(f"cinematics installed: {cutscenes.install('drangheimcity', citylua.scenes(hooks.actor, monsters))}")
    sys.exit(code)
