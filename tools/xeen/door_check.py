#!/usr/bin/env python3
"""Outdoor door check (F2, 2026-11-21): every door face of an outdoor map as the game draws it.

  tools/xeen/door_check.py <stem | built .odm>... [--root assets_dev] [--export <export.json>] [--list]

A door face is an upright model face whose texture has a door class (texture_classes.yml `door`: single, wing, tile)
and that carries an event. Faces of one door in one plane side by side (within 16) are one door; its middle is the
middle of its faces. Errors:

- `doors.lone_wing`: a wing (one half of a double door) on a door of one leaf: the other half is blank wall (Vertigo
  Town Hall's 7hhr1d2, the user 2026-11-21). A double door is two leaves, each a wing, the second mirrored or its twin.
- `doors.part_picture`: a door picture (single or wing) shown less than 0.75 times across its leaf: the leaf shows a
  slice of the door (a 256-wide picture on a 128 leaf). A single door's picture split half and half over a pair is
  whole across the opening and passes.
- `doors.narrow_pair`: two leaves less than 192 wide together: a double door squeezed into one door's bay.
- `doors.twin_singles` (F74, X6 p16, 2026-11-26): two leaves each showing a single door's whole picture (its arch and
  frame): two doors side by side with their frames meeting (the Warzone's arena gate). A double door hangs a wing on
  each leaf (classic_kit.WINGS); square blast-door leaves made to pair (LEAF_PICTURES) pass.
- `doors.crowded` (F74): two doors of one wall plane (any models: two houses sharing a facade) less than CROWD_GAP
  apart along it, at overlapping heights: their frames run into each other. Doors on one wall keep a bay between.
- `doors.small_for_building` (D-180 rule b, 2026-11-26): a big building's door (its door wall at least BIG_WALL high
  and either a temple, castle, keep, gatehouse, guild or tower by its id or title, or its door wall at least BIG_FRONT
  wide) that is not a double door at least BIG_DOOR wide and BIG_DOOR high (BIG_DOOR_TALL where the wall is
  TALL_WALL or more; walls measured at the wall's ends, a gable's peak left out; a wall narrower than the door and
  its jambs, BIG_DOOR + 128 = 512, is left to rule a): a house door on a huge wall (the Temple of Yak, X2 p14). Town
  houses, shops and the town temples at house scale (walls under BIG_WALL) keep MM6-MM8's 128 x 256. D-190: the wall
  height applies to the type words too; "front" is the face the door is cut in (one facet of a round tower). A slim
  front (under 512) that leads nowhere (no rule a) on a building rule b would take by its type word does not fall back
  to 128 x 256: one leaf as wide as the front holds with 64 jambs (SLIM_LEAF, 192 to 384) and at least SLIM_HIGH high
  (SLIM_HIGH_TALL on walls of TALL_WALL or more).
- `doors.inside_mismatch` (D-180 rule a): a building door into a dungeon (its event's MoveToMap names a .blv) narrower
  than the BLV's way back out (the door faces of the BLV event that moves to this map, the one landing nearest the
  door) or more than INSIDE_SLACK off its height: the door seen from inside is another door (XD-06's 224 x 448 exit
  behind X2's 128 x 256).
- `doors.black_built` (D-189, 2026-11-26): a built door (a `doorway` thing, or a building's door) whose face is a flat
  black BLACK_FACES texture: read as a texture missing (X3 p10/p8, the tomb). A built door shows its kit's door picture,
  its leaf at most LEAF_DEPTH behind the frame's face (in the studio it stands at the hood's back; D-197: measured on
  the built model, the doorway's door-picture faces behind the frontmost face of the same facing, `hood` as a
  fallback, never the block's `depth`; a deeper one is a `doors.deep_leaf` warning in --list). Openings into rock or
  earth stay dark:
  cave mouths, hatches (pits, wedges), culverts, and by id a mine adit, a stair down, a cleft (DARK_WORDS); a
  deliberate dark built door goes into DARK_KEPT with its reason (the sketch schema has no field for it).
- `doors.off_steps`: a door with steps before it (a model named `..._steps` or `..._stairs` whose box starts within
  128 of the door's wall and lies before it) whose middle is more than 32 from the steps' middle along the wall.

With --sketch <sketch.yml>: `caves.wings` (a cave mouth into a hill wider than its mouth and rim: the shell beside the
rim stands as rock wings) and `caves.blind_mouth` (a dark way in that leads nowhere), tools/xeen/house_doors.py.

The tiled and half-wing faults of the studio's own check (`oymap audit --doors`) are not repeated here. Exit 1 on an
error. With --list every door is printed with its numbers (the before/after tables of F2).
"""
import argparse
import json
import math
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
OYMAP = ROOT / "openyamm-studio" / "build-xeen" / "oymap"
LEAST_COPIES = 0.75
PLANE_SLACK = 8.0
PAIR_GAP = 16.0
STEPS_REACH = 128.0
STEPS_OFFSET = 32.0
CROWD_GAP = 64.0
BIG_WALL = 640.0
BIG_FRONT = 1024.0
BIG_DOOR = 384.0
BIG_DOOR_TALL = 448.0
TALL_WALL = 896.0
SIZE_SLACK = 8.0
INSIDE_SLACK = 64.0
BIG_WORDS = ("temple", "castle", "keep", "gatehouse", "guild", "tower")
SLIM_LEAF = (192.0, 384.0)
SLIM_HIGH = 320.0
SLIM_HIGH_TALL = 384.0
# D-189: flat black faces, and the openings into rock or earth that keep them
BLACK_FACES = {"7solid01", "solid01", "solid10"}
LEAF_DEPTH = 128.0
DARK_KINDS = {"cave_mouth", "hatch", "culvert"}
DARK_WORDS = ("adit", "culvert", "stair", "cleft", "shaft", "hole", "pit")
DARK_KEPT = {}      # thing id -> reason: a deliberate dark built door
# Single door pictures that are one leaf of a pair by design (each leaf framed): MM6's Control Center blast doors.
LEAF_PICTURES = {"swdoora"}


def load_classes(root):
    classes = {}
    for path in (root / "engine" / "models" / "texture_classes.yml", root / "worlds" / "xeen" / "models" / "texture_classes.yml"):
        if path.exists():
            data = yaml.safe_load(path.read_text()) or {}
            for name, row in (data.get("textures") or data).items():
                if isinstance(row, dict):
                    classes[str(name).lower()] = row
    return classes


def export_of(stem, root):
    """An installed stem, or a built map's .odm path."""
    path = Path(stem) if stem.endswith(".odm") else root / "worlds" / "xeen" / "maps" / f"{stem}.odm"
    with tempfile.TemporaryDirectory() as scratch:
        out = Path(scratch) / "export.json"
        subprocess.run([str(OYMAP), "export", str(path), "--world", "xeen",
                        "--assets", str(root), "--out", str(out)], check=True, stdout=subprocess.DEVNULL)
        return json.loads(out.read_text())


def door_faces(data, classes):
    found = []
    for model_index, model in enumerate(data["map"]["bmodels"]):
        vertices = model["vertices"]
        for face_index, face in enumerate(model["faces"]):
            row = classes.get(face["texture"].lower())
            if not row or not row.get("door") or not face.get("cog_triggered"):
                continue
            normal = [component / 65536.0 for component in face["plane_normal"]]
            if abs(normal[2]) > 0.1:
                continue
            points = [vertices[index] for index in face["vertices"]]
            # Along the wall: the horizontal axis with the face's front to its left seen from above.
            along = (-normal[1], normal[0])
            positions = [p[0] * along[0] + p[1] * along[1] for p in points]
            width = max(positions) - min(positions)
            if width < 1.0:
                continue
            us = face["texture_us"]
            texels = (max(us) - min(us)) if us else width
            size = row.get("size") or [128, 256]
            found.append({
                "model": model_index, "name": model["name"], "face": face_index, "texture": face["texture"].lower(),
                "door": row["door"], "normal": normal, "along": along, "from": min(positions), "to": max(positions),
                "plane": points[0][0] * normal[0] + points[0][1] * normal[1], "width": width,
                "copies": texels / float(size[0]), "event": face["cog_triggered"],
                "low": min(p[2] for p in points), "high": max(p[2] for p in points), "point": points[0]})
    return found


def group_doors(faces):
    """Faces in one plane touching along it: one door (one leaf, or the two leaves of a pair)."""
    groups = []
    for face in sorted(faces, key=lambda f: (f["model"], f["from"])):
        for group in groups:
            other = group[-1]
            if (other["model"] == face["model"] and sum(a * b for a, b in zip(other["normal"], face["normal"])) > 0.99
                    and abs(other["plane"] - face["plane"]) <= PLANE_SLACK
                    and face["from"] - other["to"] <= PAIR_GAP and other["from"] - face["to"] <= PAIR_GAP):
                group.append(face)
                break
        else:
            groups.append([face])
    return groups


def steps_models(data):
    found = []
    for model in data["map"]["bmodels"]:
        name = model["name"].lower()
        if name.endswith("_steps") or name.endswith("_stairs") or "steps" in name.split(":")[-1].split("_"):
            xs = [v[0] for v in model["vertices"]]
            ys = [v[1] for v in model["vertices"]]
            found.append({"name": model["name"], "box": (min(xs), min(ys), max(xs), max(ys))})
    return found


def event_moves(lua_text):
    """{event id: (x, y, target map)} for every RegisterEvent block of a generated map script that moves the party."""
    import re
    moves = {}
    blocks = re.split(r"(?m)^RegisterEvent\(", lua_text)
    for block in blocks[1:]:
        head = re.match(r"(\d+)", block)
        move = re.search(r'evt\.MoveToMap\((-?\d+),\s*(-?\d+),[^"]*"([^"]+)"\)', block)
        if head and move:
            moves[int(head.group(1))] = (float(move.group(1)), float(move.group(2)), move.group(3))
    return moves


def blv_exit(root, blv, stem, door_point):
    """(width, height) of the BLV's door faces whose event moves the party to `stem` landing nearest door_point;
    None when the BLV or such a face is missing."""
    lua = root / "worlds" / "xeen" / "events" / "maps" / blv.replace(".blv", ".lua")
    if not lua.exists() or not (root / "worlds" / "xeen" / "maps" / blv).exists():
        return None
    moves = {e: m for e, m in event_moves(lua.read_text()).items() if m[2].lower() == stem.lower() + ".odm"}
    if not moves:
        return None
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import check_door_leaves
    data = check_door_leaves.export(str(root), blv.replace(".blv", ""))["map"]
    best = None
    for event, (x, y, _) in moves.items():
        points = []
        for face in data["faces"]:
            normal = [c / 65536.0 for c in face["plane_normal"]]
            if face.get("cog_triggered") != event or abs(normal[2]) > 0.1 or face.get("is_portal"):
                continue
            points += [data["vertices"][i] for i in face["vertices"]]
            along = (-normal[1], normal[0])
        if not points:
            continue
        spread = [p[0] * along[0] + p[1] * along[1] for p in points]
        size = (max(spread) - min(spread), max(p[2] for p in points) - min(p[2] for p in points))
        far = math.hypot(x - door_point[0], y - door_point[1])
        if best is None or far < best[0]:
            best = (far, size)
    return best[1] if best else None


def door_wall(data, first):
    """(front width, wall height over the door's foot) of the door's model faces in the door's plane."""
    model = data["map"]["bmodels"][first["model"]]
    spread, top = [], first["high"]
    for face in model["faces"]:
        normal = [c / 65536.0 for c in face["plane_normal"]]
        if sum(a * b for a, b in zip(normal, first["normal"])) < 0.99:
            continue
        points = [model["vertices"][i] for i in face["vertices"]]
        if abs(points[0][0] * normal[0] + points[0][1] * normal[1] - first["plane"]) > PLANE_SLACK:
            continue
        spread += [(p[0] * first["along"][0] + p[1] * first["along"][1], p[2]) for p in points]
    if not spread:
        return 0.0, top - first["low"]
    # the walls' height at the wall's two ends (a gable's peak over the door is not the walls' height)
    left, right = min(a for a, _ in spread), max(a for a, _ in spread)
    ends = [max(z for a, z in spread if abs(a - end) <= 16.0) for end in (left, right)]
    return right - left, max(top, min(ends)) - first["low"]


def building_rules(stem, data, groups, root, sketch, lua_text, errors, lines):
    """D-180: doors.small_for_building and doors.inside_mismatch (see the module's docstring)."""
    things = {s.get("id"): s for s in (sketch or {}).get("structures") or [] if isinstance(s, dict)}
    moves = event_moves(lua_text) if lua_text else {}
    for group in groups:
        first = group[0]
        name = first["name"]
        base = name.split("#")[0]
        thing = things.get(base) or {}
        if not (name.startswith("building:") or thing.get("kind") == "building"):
            continue
        left = min(f["from"] for f in group)
        right = max(f["to"] for f in group)
        width = right - left
        low = min(f["low"] for f in group)
        height = max(f["high"] for f in group) - low
        front, wall = door_wall(data, first)
        words = (name + " " + str(thing.get("title") or "")).lower()
        # a wall narrower than the door and its jambs (a slim tower's) cannot hold it: rule (a) still applies
        big = (wall >= BIG_WALL and front >= BIG_DOOR + 128.0
               and (any(w in words for w in BIG_WORDS) or front >= BIG_FRONT))
        need = BIG_DOOR_TALL if wall >= TALL_WALL else BIG_DOOR
        where = f"model {first['model']} ({name}) face {first['face']}"
        row = f"{stem} {where} door {width:.0f} x {height:.0f} leaves {len(group)} wall {front:.0f} x {wall:.0f}"
        if big:
            row += f" big (needs {BIG_DOOR:.0f} x {need:.0f}, two leaves)"
            if len(group) < 2 or width < BIG_DOOR - SIZE_SLACK or height < need - SIZE_SLACK:
                errors.append(f"error doors.small_for_building: {where} is a door {width:.0f} x {height:.0f} "
                              f"({len(group)} leaf/leaves) in a wall {front:.0f} wide, {wall:.0f} high: a big "
                              f"building's door is a double door of its kit's wing, {BIG_DOOR:.0f} x {need:.0f} (D-180)")
        move = moves.get(first["event"])
        if move and move[2].lower().endswith(".blv"):
            inside = blv_exit(root, move[2], stem, (first["point"][0], first["point"][1]))
            if inside and inside[0] >= 64.0:     # a sliver (a frame's side) is not the way out
                row += f" inside {move[2]} {inside[0]:.0f} x {inside[1]:.0f}"
                if width < inside[0] - SIZE_SLACK or abs(height - inside[1]) > INSIDE_SLACK:
                    errors.append(f"error doors.inside_mismatch: {where} is a door {width:.0f} x {height:.0f}; "
                                  f"{move[2]}'s way back out is {inside[0]:.0f} x {inside[1]:.0f}: the outside door "
                                  f"is at least as wide and within {INSIDE_SLACK:.0f} of its height (D-180)")
        slim = (not big and wall >= BIG_WALL and front < BIG_DOOR + 128.0 and any(w in words for w in BIG_WORDS)
                and not (move and move[2].lower().endswith(".blv")))
        if slim:
            leaf = min(SLIM_LEAF[1], max(SLIM_LEAF[0], front - 128.0))
            high = SLIM_HIGH_TALL if wall >= TALL_WALL else SLIM_HIGH
            row += f" slim (needs {leaf:.0f} x {high:.0f})"
            if width < leaf - SIZE_SLACK or height < high - SIZE_SLACK:
                errors.append(f"error doors.small_for_building: {where} is a door {width:.0f} x {height:.0f} in a "
                              f"slim front {front:.0f} wide, {wall:.0f} high leading nowhere: one leaf {leaf:.0f} x "
                              f"{high:.0f}, never a house door (D-190)")
        lines.append(row)


def leaf_setback(data, base, classes):
    """D-197: how far a built doorway's door picture stands behind its frame's face: over the models of `base`, the
    door-picture faces' plane behind the frontmost upright face of the same facing (None without a door picture)."""
    faces = []
    for model in data["map"]["bmodels"]:
        if model["name"].split("#")[0] != base:
            continue
        for face in model["faces"]:
            normal = [component / 65536.0 for component in face["plane_normal"]]
            if abs(normal[2]) > 0.1:
                continue
            point = model["vertices"][face["vertices"][0]]
            row = classes.get(face["texture"].lower()) or {}
            faces.append((normal, point[0] * normal[0] + point[1] * normal[1], bool(row.get("door"))))
    setback = None
    for normal, plane, door in faces:
        if not door:
            continue
        front = max(other_plane for other, other_plane, _ in faces
                    if sum(a * b for a, b in zip(other[:2], normal[:2])) > 0.99)
        setback = max(setback or 0.0, front - plane)
    return setback


def black_built(stem, data, sketch, errors, lines, classes):
    """D-189: doors.black_built (see the module's docstring)."""
    things = {s.get("id"): s for s in (sketch or {}).get("structures") or [] if isinstance(s, dict)}
    seen = set()
    for model in data["map"]["bmodels"]:
        base = model["name"].split("#")[0]
        thing = things.get(base) or {}
        kind = thing.get("kind") or ("building" if base.startswith("building:") else "")
        if kind not in ("doorway", "building") or base in seen:
            continue
        tid = base.split(":")[-1].lower()
        dark = (kind in DARK_KINDS or thing.get("form") in ("pit", "wedge") or any(w in tid for w in DARK_WORDS)
                or base in DARK_KEPT)
        for face in model["faces"]:
            texture = face["texture"].lower()
            if not face.get("cog_triggered") or abs(face["plane_normal"][2]) / 65536.0 > 0.1:
                continue
            if texture in BLACK_FACES:
                if dark:
                    lines.append(f"{stem} {base} dark ({texture}): an opening into rock or earth"
                                 + (f" ({DARK_KEPT[base]})" if base in DARK_KEPT else ""))
                else:
                    errors.append(f"error doors.black_built: {base} ({kind}) shows a flat black {texture} door: a built "
                                  "door shows its kit's door picture, its leaf at most 128 behind the frame (D-189)")
                seen.add(base)
                break
        else:
            # a picture laid deep: said, not failed (D-197: the leaf's setback on the built model, not `depth`)
            if kind == "doorway" and not dark:
                setback = leaf_setback(data, base, classes)
                if setback is None:
                    setback = float(thing.get("hood") or 0)
                if setback > LEAF_DEPTH:
                    lines.append(f"warning doors.deep_leaf: {base} (doorway) lays its door {setback:.0f} behind its "
                                 f"frame's face (D-189 holds built doors to {LEAF_DEPTH:.0f})")
                seen.add(base)


def check(stem, data, classes, listing):
    errors = []
    lines = []
    faces = door_faces(data, classes)
    stairs = steps_models(data)
    groups = group_doors(faces)
    for index, group in enumerate(groups):
        first = group[0]
        left = min(f["from"] for f in group)
        right = max(f["to"] for f in group)
        middle = (left + right) * 0.5
        where = f"model {first['model']} ({first['name']}) face {first['face']}"
        wings = [f for f in group if f["door"] == "wing"]
        if len(group) == 2 and right - left < 192.0:
            errors.append(f"error doors.narrow_pair: {where} ({first['texture']}) is a pair of leaves {right - left:.0f} "
                          "wide: each leaf shows its picture squeezed to half; a double door is 256 wide (two 128 leaves)")
        if wings and len(group) == 1:
            errors.append(f"error doors.lone_wing: {where} ({first['texture']}, {first['width']:.0f} wide) hangs one "
                          "wing of a double door alone: the other half is blank wall. Make it a double door (two "
                          "leaves, 256 wide, the second mirrored or its twin) or use a single door's picture")
        if (len(group) == 2 and all(f["door"] == "single" and f["copies"] > 0.75 for f in group)
                and not all(f["texture"] in LEAF_PICTURES for f in group)):
            errors.append(f"error doors.twin_singles: {where} ({first['texture']}) hangs a single door's whole picture "
                          f"on each of its two leaves ({right - left:.0f} wide): two doors side by side, their frames "
                          "meeting; a double door hangs a wing on each leaf (the kit's wing, the second mirrored)")
        for other in groups[index + 1:]:
            near = other[0]
            if (sum(a * b for a, b in zip(near["normal"], first["normal"])) < 0.99
                    or abs(near["plane"] - first["plane"]) > PLANE_SLACK
                    or min(f["high"] for f in other) <= max(f["low"] for f in group)
                    or max(f["high"] for f in group) <= min(f["low"] for f in other)):
                continue
            o_left = min(f["from"] for f in other)
            o_right = max(f["to"] for f in other)
            gap = max(o_left - right, left - o_right)
            if gap < CROWD_GAP:
                errors.append(f"error doors.crowded: {where} ({first['texture']}) and model {near['model']} "
                              f"({near['name']}) face {near['face']} ({near['texture']}) are two doors on one wall "
                              f"{gap:.0f} apart (under {CROWD_GAP:.0f}): their frames run into each other")
        # One single door's picture split over the two leaves of a pair (half on each, the second mirrored: the
        # Control Center's blast doors on D6) shows the picture's width over the opening: not a slice.
        split = len(group) == 2 and all(f["door"] == "single" and abs(f["copies"] - 0.5) < 0.05 for f in group)
        for face in group:
            if face["door"] in ("single", "wing") and face["copies"] < LEAST_COPIES and not split:
                errors.append(f"error doors.part_picture: model {face['model']} ({face['name']}) face {face['face']} "
                              f"({face['texture']}, {face['width']:.0f} wide) shows {face['copies']:.2f} of its door "
                              "picture across: a door picture is laid whole over its leaf")
        # Steps before the door: their box reaches the door's wall and lies before it.
        normal = first["normal"]
        along = first["along"]
        stepped = ""
        for step in stairs:
            x0, y0, x1, y1 = step["box"]
            corners = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
            out = [c[0] * normal[0] + c[1] * normal[1] - first["plane"] for c in corners]
            side = [c[0] * along[0] + c[1] * along[1] for c in corners]
            if min(out) > STEPS_REACH or max(out) < 32.0 or max(side) < left or min(side) > right:
                continue
            centre = (min(side) + max(side)) * 0.5
            stepped = f" steps {step['name']} off {middle - centre:+.0f}"
            if abs(middle - centre) > STEPS_OFFSET:
                errors.append(f"error doors.off_steps: {where} ({first['texture']}) stands {middle - centre:+.0f} along "
                              f"its wall from the middle of {step['name']} before it: a door is centred on its steps")
        if listing:
            lines.append(f"{stem} {where} leaves {len(group)} tex {'/'.join(f['texture'] for f in group)} "
                         f"({'/'.join(f['door'] for f in group)}) width {right - left:.0f} copies "
                         f"{'/'.join('%.2f' % f['copies'] for f in group)} event {first['event']}{stepped}")
    return errors, lines, groups


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("stems", nargs="*")
    parser.add_argument("--root", type=Path, default=ROOT / "assets_dev")
    parser.add_argument("--export", type=Path, help="a built map's export.json instead of an installed stem")
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--sketch", type=Path, action="append", default=[],
                        help="also check a project's sketch.yml for the cave-mouth rules (caves.wings, caves.blind_mouth)")
    args = parser.parse_args()
    classes = load_classes(args.root)
    jobs = [(args.export.stem, json.loads(args.export.read_text()))] if args.export else []
    jobs += [(stem, None) for stem in args.stems]
    total = 0
    for stem, data in jobs:
        data = data or export_of(stem, args.root)
        errors, lines, groups = check(stem, data, classes, args.list)
        # D-180: the building rules read the map's sketch and its generated script (beside a built .odm, else the
        # installed one)
        key = Path(stem).stem
        built = Path(stem) if stem.endswith(".odm") else None
        lua = built.with_suffix(".lua") if built else args.root / "worlds" / "xeen" / "events" / "maps" / f"{key}.lua"
        sketch_path = ROOT / "devdocs" / "xeen" / "briefs" / key.replace("xeen_", "") / "L4" / "sketch.yml"
        sketch = yaml.safe_load(sketch_path.read_text()) if sketch_path.exists() else None
        table = []
        building_rules(key, data, groups, args.root, sketch, lua.read_text() if lua.exists() else "", errors, table)
        black_built(key, data, sketch, errors, table, classes)
        if args.list:
            lines += ["D-180 " + row for row in table]
        for line in lines + errors:
            print(line)
        print(f"{stem}: {len(errors)} door errors")
        total += len(errors)
    for sketch in args.sketch:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import house_doors
        errors = house_doors.check_sketch(yaml.safe_load(sketch.read_text()))
        for line in errors:
            print(line)
        print(f"{sketch}: {len(errors)} cave errors")
        total += len(errors)
    sys.exit(1 if total else 0)


if __name__ == "__main__":
    main()
