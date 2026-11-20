#!/usr/bin/env python3
"""
The props of MM9's outdoor regions (the BLVs of level_generation/projects/mm9r_<region>_blv) as decorations:
writes each region's props.json (overrides.yml `outdoor: {props: props.json}`, outdoor_blv.py populate) from
work/inventory.json (inventory.py).

- **Props with an installed model** (status installed: the (model, skin) another map's props project built): placed
  as the city props are (Drangheim City's placements.py): the finished model at the DAT position, scaled and turned,
  moved onto the old import's baked copy of the same object (MM9_*_<object index>_* in the region's old ODM: its
  centre, when that fits better), in the old ODM's frame (LT x 2.56, no offset), then into the BLV's (minus the
  map's `offset`). MoveToFloor ones then stand on the remade ground (the BLV's highest floor face under them: the
  terrain was smoothed, so it differs from the old ODM's by some units). A scale no map placed yet gets its row
  (rows.py, `mm9_<prop>_x<scale x 100>`, hint and radius from the prop's existing row).
- **Vegetation** (vegetation.py): MM9's trees, bushes and flowers as MM6-MM8 models at MM9's sizes, on the ground.
- **Left out** (listed): posed figures (the townsfolk, soldiers and creatures: they wait for the NPC work, user
  2026-11-04), props with no model yet (status new: the next step builds them), tilted props whose tilt no variant
  carries (MM9 pitch or roll), and the Isle of Ashes (its pilot props.json stays).

Kinds as the cities': prop, torch (CandleProp, WallTorch, Brazier; `light` = the nearest DAT Light within 400 units
or null, which gets a lamp light at its flame, dungeon/content.py). A DAT name that repeats or is a decoration's
name gets _<object index>.

    python3 level_generation/props/mm9_outdoor_regions_claude/scripts/placements.py [--dry-run] [region ...]
"""

from __future__ import annotations

import ast
import collections
import glob
import json
import math
import sys
from pathlib import Path

import numpy as np
import yaml
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parents[1]
REPO = HERE.parents[2]
sys.path.insert(0, str(HERE / "scripts"))
# appended, not inserted: the isle's scripts have a props_table.py of their own
sys.path.append(str(REPO / "level_generation/props/mm9_isleofashes_claude/scripts"))
sys.path.insert(0, str(REPO))
import props_table  # noqa: E402
import pose_bake  # noqa: E402
import rows  # noqa: E402
import vegetation  # noqa: E402
from glbio import array, read_glb, world_positions  # noqa: E402

REGIONS = ["sturmford", "thjorgard", "thronheim", "drangheim", "guberland", "frosgard", "lindisfarne", "yorwick",
           "mountainpass", "bootcamp", "afterworld"]
CLASS_KIND = {"Prop": "prop", "CandleProp": "torch", "Brazier": "torch", "WallTorch": "torch", "Torch": "torch",
              "TreasureChest": "chest"}
LIGHT_MAX = 400.0
SCALE = 2.56
# Hints of the props built here (scripts/props_table.py), for their rows.
HINTS = {"stone": "stone", "arrow": "arrow", "lantern1": "lantern", "longsword": "sword", "longswordrune": "sword",
         "broadsword": "sword", "dwarfaxe": "pickaxe", "haybale01": "hay bale", "stool03": "chair",
         "toyboat": "toy boat",
         "bellnobeam": "bell", "banner": "awning", "tableround4": "table", "woodshed": "woodshed",
         "farmerplow": "plough", "girldolly": "doll", "greatbook": "book", "windmill": "windmill",
         "hairbrush": "hairbrush", "penancequest": "rune stone", "portalbroken": "portal", "axerusty": "axe",
         "statstone": "stat stone", "battlewitch": "axe",
         "runestone": "rune stone"}


def hint_of(prop: str) -> str:
    base = props_table.source_prop(prop)
    return next((v for k, v in sorted(HINTS.items(), key=lambda kv: -len(kv[0])) if base.startswith(k)), base)


def tilt_oy(local, pitch, roll):
    """The transcoder's object pitch (about x) then roll (about y), in OpenYAMM-local axes (the cities' placements)."""
    cx, sx, cy, sy = math.cos(pitch), math.sin(pitch), math.cos(roll), math.sin(roll)
    rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    ryy = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    return local @ (ryy @ rx).T


def tilted_variant(prop: str, rotation) -> str | None:
    """The baked variant of a prop at MM9's pitch and roll (props_table.TILTS: <prop>p<pitch>[r<roll>])."""
    pitch, roll = round(math.degrees(float(rotation[0]))) % 360, round(math.degrees(float(rotation[2]))) % 360
    name = f"{prop}p{pitch}" + (f"r{roll}" if roll else "")
    return name if name in props_table.TILTS else None


def rot(yaw):
    c, s = math.cos(yaw), math.sin(yaw)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def literal(path: Path, name: str):
    for node in ast.parse(path.read_text()).body:
        if isinstance(node, ast.Assign) and any(getattr(t, "id", None) == name for t in node.targets):
            try:
                return ast.literal_eval(node.value)
            except ValueError:
                return None
    return None



# Objects a region's script keeps hidden in play and the map does not carry (none now). Yorwick's battlefield (the
# guard, Kira, the fallen, the swords and arrows: SvenShowTake.inc's RemoveAll) is placed: its regionlua.py shows it
# only for Svenspeech.scr's cutscene (the cinematic battlefield_sven, key 95 and not 97); Sven himself is an actor
# there (overrides.yml people). Afterworld's copies stay: nothing there hides them (SixFires.inc's Absolution only
# shows them again).
SCRIPT_HIDDEN = {}
# Objects left out by name: Yorwick's dead Bjarni (Kira0, bjarni.abc), Sigmund (sigmund) and Tryggva lie on the
# battlefield (PropAnim.scr Static_die1); their dead figures have no decoration rows yet (bjarnidead, sigmunddead and
# tryggvadead are baked but unbound) and the seated stand-ins posed_bake picks would sit among the dead, in the air
# (the seated Sigmund, playthrough note 2026-11-11). Sven19, a fallen soldier MM9 keeps hidden (DAT Visible 0, Gravity
# 0, MoveToFloor 0: about 215 units above the ground; no script shows it, SvenShowTake.inc skips it) floated over
# the field.
DEAD_HERO = "dead hero figure without a row (Svenspeech.scr battlefield)"
LEFT_OUT = {"yorwick": {"Kira0": DEAD_HERO, "sigmund": DEAD_HERO, "Tryygva": DEAD_HERO,
                        "Sven19": "hidden in MM9 (DAT Visible 0) and shown by no script"}}
_hidden = {}


def script_hidden(region: str) -> set:
    if region not in _hidden:
        import re
        text = (REPO / "mm9/extracted/SCRIPTS/SCRIPTS" / SCRIPT_HIDDEN[region][0]).read_bytes().decode("latin-1")
        _hidden[region] = set(re.findall(r"getobjecthandle\s+(\S+)", text, re.I))
    return _hidden[region]


def posed_bake(item: dict, p: dict) -> str | None:
    """The pose_bake.py figure an object shows (MM9's posed Props: the battlefield's dead, the seated heroes, Boot
    Camp's creatures), or None."""
    model = item["model"].split("/")[-1]
    skin = item["skin"].split("/")[-1]
    params = str(p.get("ScriptParams") or "").strip().lower()
    if model == "clansoldier.abc":
        if skin == "beldshield1.dtx":
            return "clansoldierdeada"
        return "clansoldierdead2b" if params.startswith("static_die2") else "clansoldierdeadb"
    if item.get("prop") in POSED_SWAPS:
        return POSED_SWAPS[item["prop"]]
    return POSED_MODELS.get(model)


# MM9 model -> figure (pose_bake.POSED); the cities' seated heroes (MM9's own meshes) -> ours
POSED_MODELS = {"kira.abc": "kiradead", "bjarni.abc": "bjarnidead", "sigmund.abc": "sigmunddead",
                "tryggva.abc": "tryggvadead", "dragonfly.abc": "dragonflyfigure", "evileyeterror.abc": "eyefigure",
                "gezzampt.abc": "gezzamptfigure", "jellyspore.abc": "jellysporefigure",
                "lizardorc.abc": "lizardorcfigure", "nosferatu.abc": "nosferatufigure",
                "skeleton.abc": "skeletonfigure", "skeletonwarrior.abc": "skeletonwarriorfigure",
                "troglodyte.abc": "troglodytefigure",
                "goose.abc": "goosefigure"}
POSED_SWAPS = {"bjarnisitting": "bjarniseated", "sigmundsit": "sigmundseated", "tryggvasit": "tryggvaseated"}

def posed_props() -> set:
    """Every props project's posed figures (props_table POSES, PLACE_POSES)."""
    out = set()
    for f in glob.glob(str(REPO / "level_generation/props/mm9_*_claude/scripts/props_table.py")):
        for name in ("POSES", "PLACE_POSES"):
            value = literal(Path(f), name)
            if isinstance(value, dict):
                out |= set(value)
    return out


def tilted_props() -> set:
    out = set()
    for f in glob.glob(str(REPO / "level_generation/props/mm9_*_claude/scripts/props_table.py")):
        for name in ("TILTS", "TILTED"):
            value = literal(Path(f), name)
            if isinstance(value, dict):
                out |= set(value)
    return out


def home(prop: str) -> Path:
    """The props project that built a prop (its work/<prop>_meta.json and raw export)."""
    for f in sorted(glob.glob(str(REPO / f"level_generation/props/mm9_*_claude/work/{prop}_meta.json"))):
        project = Path(f).parents[1]
        origins = project / "work/binding_origins.json"
        if (project / f"work/raw/{prop}/{prop}.glb").exists() and origins.exists() \
                and prop in json.loads(origins.read_text()):
            return project
    raise SystemExit(f"{prop}: no props project has its meta and raw export")


def lod0(path: Path):
    """All LOD0 positions and those without flame cards (the old bake has no flames)."""
    document, binary = read_glb(path)
    node = next(n for n in document["nodes"] if "mesh" in n)
    primitives = document["meshes"][node["mesh"]]["primitives"]
    solid = [p for p in primitives if document["materials"][p["material"]]["name"] not in ("Fire", "Halo")]
    full = np.concatenate([array(document, binary, p["attributes"]["POSITION"]) for p in primitives
                           if document["materials"][p["material"]]["name"] != "Halo"])
    return full, np.concatenate([array(document, binary, p["attributes"]["POSITION"]) for p in solid])


class Floors:
    """The BLV's upward faces (normal z >= 0.7) for 'highest floor under a point'."""

    def __init__(self, blv_path: Path):
        from util.map_export import parse_blv_file
        blv = parse_blv_file(blv_path)["payload"]
        vertices = np.array([[v["x"], v["y"], v["z"]] for v in blv["vertices"]], float)
        tris = []
        for f in blv["faces"]:
            if f["is_portal"]:
                continue
            ring = vertices[f["vertex_indices"]]
            for k in range(1, len(ring) - 1):
                a, b, c = ring[0], ring[k], ring[k + 1]
                n = np.cross(b - a, c - a)
                length = np.linalg.norm(n)
                if length > 1e-6 and n[2] / length >= 0.7:
                    tris.append((a, b, c))
        self.tris = np.array(tris)
        lo, hi = self.tris.min(1), self.tris.max(1)
        self.lo, self.hi = lo, hi

    def below(self, x: float, y: float, z_from: float) -> float | None:
        near = np.nonzero((self.lo[:, 0] <= x) & (x <= self.hi[:, 0]) & (self.lo[:, 1] <= y) & (y <= self.hi[:, 1])
                          & (self.lo[:, 2] <= z_from))[0]
        best = None
        p = np.array([x, y])
        for i in near:
            a, b, c = self.tris[i]
            v0, v1, v2 = b[:2] - a[:2], c[:2] - a[:2], p - a[:2]
            den = v0[0] * v1[1] - v1[0] * v0[1]
            if abs(den) < 1e-9:
                continue
            u = (v2[0] * v1[1] - v1[0] * v2[1]) / den
            v = (v0[0] * v2[1] - v2[0] * v0[1]) / den
            if u < -1e-6 or v < -1e-6 or u + v > 1 + 1e-6:
                continue
            z = a[2] + u * (b[2] - a[2]) + v * (c[2] - a[2])
            if z <= z_from and (best is None or z > best):
                best = z
        return best


def region_objects(region: str) -> dict:
    raw = yaml.safe_load((REPO / f"assets_editor_dev/worlds/mm9/maps/{region}.raw_objects.yml").read_text())
    return {o["object_index"]: (o["name"], {p["name"]: json.loads(p["value_json"]) for p in o["properties"]
                                            if p.get("value_json")}) for o in raw["objects"]}


def old_bakes(region: str) -> dict:
    from util.map_export import parse_odm_file
    bmodels = parse_odm_file(REPO / f"assets_editor_dev/worlds/mm9/maps/{region}.odm")["payload"]["bmodels"]
    out = {}
    for b in bmodels:
        if b["name"].startswith("MM9_"):
            parts = b["name"].split("_")
            for part in parts:
                if part.isdigit():
                    out.setdefault(int(part), np.array([[a["x"], a["y"], a["z"]] for a in b["vertices"]], float))
                    break
    return out


class Variants:
    """(prop, scale) -> a decoration name: an existing MM9 row bound to the prop's model at that height, else a
    new row (rows.py)."""

    def __init__(self):
        self.bindings = rows.bindings()
        self.table = rows.table_rows()
        self.new = {}

    def name(self, prop: str, scale: float, height_units: float, meta: dict | None = None, solid: bool = True) -> str:
        model = f"worlds/mm9/models/mm9_deco_{prop}.glb"
        target = height_units * scale
        same = [b for b in self.bindings if b["model"] == model] + \
            [dict(r["binding"], name=r["name"]) for r in self.new.values() if r["binding"]["model"] == model]
        for b in same:
            if abs(float(b["height"]) - target) <= max(0.6, target * 0.002) and (
                    b["name"].lower() in self.table or b["name"] in self.new):
                return b["name"]
        if not same:
            # a prop built here (props_table.py): its first row, from its build meta (radius: half its smaller
            # footprint side when MM9 makes it solid)
            name = f"mm9_{prop}" if abs(scale - 1.0) < 1e-3 else f"mm9_{prop}_x{int(round(scale * 100))}"
            extent = meta["extent_m"] if meta else [0.0, 0.0]
            radius = round(min(extent[0], extent[1]) * 81.7 * scale / 2) if solid else 0
            self.new[name] = {"name": name, "hint": hint_of(prop), "radius": min(radius, 255), "height": target,
                              "binding": {"model": model, "height": round(target, 1), "yaw": "facing"}}
            return name
        base = min(same, key=lambda b: abs(float(b["height"]) - target))
        if base["name"] in self.new:            # a prop built here, its first row added by this run
            first = self.new[base["name"]]
            hint, radius = first["hint"], float(first["radius"])
        else:
            cells = self.table[base["name"].lower()]
            hint, radius = cells[2].strip(), float(cells[4])
        ratio = target / float(base["height"])
        name = f"mm9_{prop}_x{int(round(scale * 100))}"
        if name.lower() in self.table or any(b["name"].lower() == name.lower() for b in self.bindings):
            name = f"mm9_{prop}_h{int(round(target))}"
        if name not in self.new:
            binding = {k: v for k, v in base.items() if k != "name"}
            binding["height"] = round(target, 1)
            self.new[name] = {"name": name, "hint": hint, "radius": round(radius * ratio),
                              "height": target, "binding": binding}
        return name


def main() -> int:
    dry = "--dry-run" in sys.argv
    wanted = [a for a in sys.argv[1:] if not a.startswith("--")] or REGIONS
    inventory = json.loads((HERE / "work/inventory.json").read_text())
    posed, tilted = posed_props(), tilted_props()
    engine = vegetation.engine_bindings()
    variants = Variants()
    vegetation_rows = {}
    decoration_names = set(rows.table_rows())
    for line in (REPO / "assets_dev/engine/data_tables/decoration_data.txt").read_text(encoding="latin-1").splitlines():
        cells = line.split("\t")
        if len(cells) > 1 and cells[0].strip().isdigit():
            decoration_names.add(cells[1].strip().lower())
    homes, metas, glbs = {}, {}, {}
    pose_metas = {}
    summary = {}
    for region in wanted:
        project = REPO / f"level_generation/projects/mm9r_{region}_blv"
        offset = np.array(yaml.safe_load((project / "overrides.yml").read_text())["map"].get("offset", [0, 0, 0]),
                          float)
        objects = region_objects(region)
        bakes = old_bakes(region)
        floors = Floors(REPO / f"output/mm9_rework/isleofashes_blv_root/worlds/mm9/maps/{region}.blv")
        lights = [(p["Name"], np.array([p["Pos"][0], p["Pos"][2], p["Pos"][1]]) * SCALE - offset)
                  for name, p in objects.values() if name == "Light"]
        entries, left_out = [], collections.Counter()
        for item in (e for e in inventory if e["region"] == region):
            name, p = objects[item["object"]]
            s = float(p.get("Scale", 1.0) or 1.0)
            rotation = p.get("Rotation", [0, 0, 0, 0])
            ry = float(rotation[1])
            raw_pos = np.array([p["Pos"][0], p["Pos"][2], p["Pos"][1]]) * SCALE
            species = vegetation.mm9_species(item["model"])
            entry = {"source_object": item["object"], "source_name": p["Name"], "class": item["class"],
                     "kind": CLASS_KIND.get(item["class"], "prop"), "source_model": p.get("Filename"),
                     "source_skin": p.get("Skin"), "script": p.get("ScriptName") or None,
                     "script_params": p.get("ScriptParams") or None}
            if species is not None:
                ours = vegetation.pick(species, item["object"], region)
                row = vegetation.row(species, ours, s, engine)
                vegetation_rows[row["name"]] = row
                position = raw_pos - offset
                floor = floors.below(position[0], position[1], position[2] + 400)
                if floor is not None:
                    position[2] = floor - row["sink"]
                entry.update({"prop": species, "decoration": row["name"], "vegetation": ours,
                              "floor_z": None if floor is None else round(float(floor), 1)})
            elif region in SCRIPT_HIDDEN and p["Name"] in script_hidden(region):
                left_out[SCRIPT_HIDDEN[region][1]] += 1
                continue
            elif p["Name"] in LEFT_OUT.get(region, {}):
                left_out[LEFT_OUT[region][p["Name"]]] += 1
                continue
            elif posed_bake(item, p) is not None:
                # a posed figure: our 3D model baked in MM9's pose (pose_bake.py), at the DAT position (its origin is
                # the actor's, between the feet), on the floor under it; corpses walk-through, figures MM9's Solid
                prop = posed_bake(item, p)
                meta = pose_metas.setdefault(prop, json.loads((HERE / f"work/{prop}_meta.json").read_text()))
                extent = [v * pose_bake.UNITS_PER_METRE / 81.7 for v in (meta["extent_m"][0], meta["extent_m"][2])]
                solid = bool(p.get("Solid", 1)) and not prop.endswith(("dead", "dead2b", "deadb", "deada"))
                decoration = variants.name(prop, s, float(meta["height_units"]), {"extent_m": extent}, solid)
                position = raw_pos - offset
                floor = floors.below(position[0], position[1], position[2] + 200)
                if floor is not None:
                    position[2] = floor
                entry.update({"prop": prop, "decoration": decoration, "fit_median_units": None, "pose": meta["clip"],
                              "floor_z": None if floor is None else round(float(floor), 1)})
            elif item["status"] != "installed":
                left_out[f"no model yet: {item['model'].split('/')[-1]}"] += 1
                continue
            elif item["prop"] in posed:
                left_out[f"posed figure (waits for the NPC work): {item['prop']}"] += 1
                continue
            elif (abs(float(rotation[0])) > 1e-3 or abs(float(rotation[2])) > 1e-3) and item["prop"] not in tilted \
                    and tilted_variant(item["prop"], rotation) is None:
                left_out[f"tilted, no tilted variant: {item['prop']}"] += 1
                continue
            else:
                prop = item["prop"]
                tilt = None
                if abs(float(rotation[0])) > 1e-3 or abs(float(rotation[2])) > 1e-3:
                    variant = tilted_variant(prop, rotation)
                    if variant is not None:
                        prop, tilt = variant, props_table.TILTS[variant]
                if prop not in homes:
                    homes[prop] = home(prop)
                    metas[prop] = json.loads((homes[prop] / f"work/{prop}_meta.json").read_text())
                    origins = json.loads((homes[prop] / "work/binding_origins.json").read_text())
                    origin = origins.get(prop)
                    raw = homes[prop] / f"work/raw/{prop}/{prop}.glb"
                    full = raw.with_name(raw.stem + "_full.glb")
                    g = world_positions(full if full.exists() else raw) + np.array(origin) * SCALE
                    local = np.stack([g[:, 0], g[:, 2], g[:, 1]], 1)
                    if tilt is not None:
                        local = tilt_oy(local, *tilt)
                    glbs[prop] = (local, lod0(REPO / f"assets_source/worlds/mm9/models/mm9_deco_{prop}.glb"))
                meta = metas[prop]
                local, (full, solid) = glbs[prop]
                decoration = variants.name(prop, s, float(meta["height_units"]), meta, bool(p.get("Solid", 1)))
                inst = (local * s) @ rot(-ry).T + raw_pos
                bake = bakes.get(item["object"])
                extra = np.zeros(3) if bake is None else \
                    (bake.min(0) + bake.max(0)) / 2 - (inst.min(0) + inst.max(0)) / 2
                position = raw_pos + extra + rot(-ry) @ (np.array(meta["origin_local_units"]) * s)
                height = float(meta["height_units"]) * s
                engine_scale = height / (full[:, 1].max() - full[:, 1].min())
                placed = np.stack([-solid[:, 0], solid[:, 2], solid[:, 1]], 1) * engine_scale @ rot(-ry).T + position
                fit = None
                if bake is not None:
                    tree = cKDTree(bake)
                    shift = (bake.min(0) + bake.max(0)) / 2 - (placed.min(0) + placed.max(0)) / 2
                    if np.median(tree.query(placed + shift)[0]) < np.median(tree.query(placed)[0]):
                        position, placed = position + shift, placed + shift
                    fit = round(float(np.median(tree.query(placed)[0])), 2)
                position = position - offset
                placed = placed - offset
                floor = None
                if p.get("MoveToFloor"):
                    floor = floors.below(position[0], position[1], placed[:, 2].min() + 200)
                    if floor is not None:
                        lift = floor - placed[:, 2].min()
                        position[2] += lift
                entry.update({"prop": prop, "decoration": decoration, "fit_median_units": fit,
                              "floor_z": None if floor is None else round(float(floor), 1)})
                if entry["kind"] == "torch":
                    best = min(lights, key=lambda l: np.linalg.norm(l[1] - position), default=None)
                    distance = None if best is None else float(np.linalg.norm(best[1] - position))
                    entry["light"] = None if distance is None or distance > LIGHT_MAX else \
                        {"name": best[0], "distance": round(distance)}
                    if entry["light"] is None:
                        entry["light_note"] = "no MM9 Light of its own"
            entry.update({"x": round(float(position[0]), 1), "y": round(float(position[1]), 1),
                          "z": round(float(position[2]), 1), "yaw_degrees": round(math.degrees(-ry) % 360.0, 2)})
            entries.append(entry)
        seen = set()
        for entry in entries:
            if entry["source_name"] in seen or entry["source_name"].lower() in decoration_names \
                    or ("obj_" + entry["source_name"]).lower() in decoration_names:
                entry["dat_name"] = entry["source_name"]
                entry["source_name"] = f"{entry['source_name']}_{entry['source_object']}"
            seen.add(entry["source_name"])
        summary[region] = {"placed": len(entries), "kinds": dict(collections.Counter(e["kind"] for e in entries)),
                           "vegetation": sum(1 for e in entries if "vegetation" in e),
                           "no_floor": sum(1 for e in entries if e.get("floor_z") is None and (
                               "vegetation" in e or objects[e["source_object"]][1].get("MoveToFloor"))),
                           "left_out": dict(left_out)}
        fits = [e["fit_median_units"] for e in entries if e.get("fit_median_units") is not None]
        summary[region]["fit_median_of_medians"] = round(float(np.median(fits)), 2) if fits else None
        if not dry:
            (project / "props.json").write_text(json.dumps(entries, indent=1) + "\n")
    new_rows = list(vegetation_rows.values()) + list(variants.new.values())
    print(json.dumps(summary, indent=1))
    print(f"rows: {len(vegetation_rows)} vegetation, {len(variants.new)} prop scale variants")
    if not dry:
        added = rows.ensure(new_rows)
        print(f"rows added: {len(added)}")
        (HERE / "work/placements_summary.json").write_text(json.dumps(summary, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
