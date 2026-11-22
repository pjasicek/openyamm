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
                "low": min(p[2] for p in points), "point": points[0]})
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


def check(stem, data, classes, listing):
    errors = []
    lines = []
    faces = door_faces(data, classes)
    stairs = steps_models(data)
    for group in group_doors(faces):
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
    return errors, lines


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
        errors, lines = check(stem, data, classes, args.list)
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
