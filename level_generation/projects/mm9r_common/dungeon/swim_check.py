#!/usr/bin/env python3
"""
A swim check scenario for any converted MM9 map with water (the shared water rule, dungeon/water.py): from the
installed scene's `water_volumes` and the DAT floors it writes `<project>/scenario_swim_check.yml`:

- per volume, its deepest piece's deepest bed point (at most `PIECES` pieces per volume): the party set on the bed
  under the water; a deep one (eye under) asserts state `bed` and the eye under, then Fly Up rises it to the surface
  (`surface`, the eye out); a shallow one (bed less than `EYE_UNDER` under the top) asserts the eye out (wading);
- MM9's swimmers placed in a volume (water.SWIMMER_CLASSES, work/content.json): each is still in its water 8 s later
  (near its start, over its bed).

    python3 level_generation/projects/mm9r_common/dungeon/swim_check.py level_generation/projects/mm9r_<map> [--isle]
    ./build/game/openyamm --asset-root "$PWD/output/mm9_rework/assets_dev" \\
        --headless-run-scenario level_generation/projects/mm9r_<map>/scenario_swim_check.yml --scenario-no-color

A volume with no bed point (sealed under rock, a mover's water) is listed in a note and skipped. The bed points come
from the DAT floors: on the regions (outdoor_blv.py) the far sea's seabed is not built, so do not use it there. Actor indices come
from the built scene (the density pass adds actors).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dungeon import water  # noqa: E402
from dungeon.scenarios import EYE, Floors, write  # noqa: E402
from dungeon.source import ROOT, Project  # noqa: E402

EYE_UNDER = EYE - 25.6 + 4          # the eye point (eye - 25.6) under the top, with a margin
PIECES = 2
SAMPLES = 9                         # per axis over a piece's box
COVER_STEP = 50                     # the party's step: a bed point with a floor this far over it is covered


def _inside(x, y, ring) -> bool:
    hit = False
    for (x1, y1), (x2, y2) in zip(ring, np.roll(ring, -1, axis=0)):
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            hit = not hit
    return hit


def deepest_point(floors: Floors, piece: dict):
    """(x, y, bed) of the deepest bed point of a piece inside its footprint, or None."""
    ring = np.array(piece["polygon"], float)
    lo, hi = ring.min(0), ring.max(0)
    best = None
    for fx in np.linspace(0.1, 0.9, SAMPLES):
        for fy in np.linspace(0.1, 0.9, SAMPLES):
            x, y = lo + (hi - lo) * np.array([fx, fy])
            if not _inside(x, y, ring):
                continue
            bed = floors.z(x, y, piece["top"] - 2)
            bed = None if bed is None else float(bed)
            if bed is None or bed < piece["bottom"] - 4 or bed > piece["top"] - 1:
                continue
            # a floor within a step over the bed (a ledge over the pool's brush) is what the party stands on there
            if (floors.z(x, y, bed + COVER_STEP) or bed) > bed + 1:
                continue
            if best is None or bed < best[2]:
                best = (float(x), float(y), float(bed))
    return best


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("project", type=Path)
    parser.add_argument("--isle", action="store_true", help="the regions' review root (isleofashes_blv_root)")
    args = parser.parse_args()
    project = Project.load(args.project.resolve(), install=False)
    root = ROOT / "output/mm9_rework" / ("isleofashes_blv_root" if args.isle else "assets_dev")
    scene = json.loads((root / f"worlds/mm9/maps/{project.stem}.scene.yml").read_text())
    volumes = scene.get("water_volumes") or []
    floors = Floors(project)
    map_name = project.map
    steps = [{"load_map": {"map": map_name}}]
    skipped = []
    # overrides.yml `map: {swim_check_skip: [...]}`: volumes the map's script handles otherwise (Chasm of the Dead's
    # Acid0: its Lua lifts a party in the acid to the rim every third second)
    skip = set(project.overrides["map"].get("swim_check_skip") or [])
    for volume in volumes:
        if volume["id"] in skip:
            skipped.append(f"{volume['id']} (swim_check_skip)")
            continue
        found = []
        for piece in volume["pieces"]:
            point = deepest_point(floors, piece)
            if point is not None:
                found.append((point, piece))
        found.sort(key=lambda item: item[0][2] - item[1]["top"])
        if not found:
            skipped.append(volume["id"])
            continue
        for (x, y, bed), piece in found[:PIECES]:
            depth = piece["top"] - bed
            pose = {"map": map_name, "x": int(round(x)), "y": int(round(y)), "z": int(round(bed + 1)), "yaw": 0.0,
                    "pitch": 0.0}
            steps.append({"note": {"text": f"{volume['id']}: on its bed at {bed:.0f}, {depth:.0f} under its top "
                                           f"{piece['top']}"}})
            steps.append({"set_pose": dict(pose)})
            steps.append({"advance_runtime": {"seconds": 1.0}})
            if depth > EYE_UNDER:
                steps.append({"assert": {"water": {"state": "bed", "eye_under": True,
                                                   "foot_z_max": round(bed + 12, 1)}}})
                rise = max(1.0, (depth - EYE + 40) / 384 + 0.8)
                steps.append({"movement_segment": {
                    "input": "none", "fly_up": True, "seconds": round(rise, 1), "actor_collision": False,
                    "actor_ai": False, "start": dict(pose), "expect_stop": dict(pose, z=int(round(piece["top"] - EYE + 27))),
                    "loose_tolerance": True, "tolerance_xy": 2000, "tolerance_z": 2000}})
                steps.append({"assert": {"water": {"state": "surface", "eye_under": False, "breath_min": 0.99}}})
            else:
                steps.append({"assert": {"water": {"eye_under": False, "foot_z_max": round(bed + 12, 1)}}})
    content_path = project.work / "content.json"
    swimmers = []
    if content_path.exists():
        classes = {a["actor_index"]: a["class"] for a in json.loads(content_path.read_text()).get("actors", [])}
        actors = scene["initial_state"]["actors"]
        for actor in actors:
            if classes.get(actor["actor_index"]) not in water.SWIMMER_CLASSES:
                continue
            p = actor["position"]
            for volume in volumes:
                piece = next((q for q in volume["pieces"] if _inside(p["x"], p["y"], np.array(q["polygon"], float))
                              and q["bottom"] - 4 <= p["z"] <= q["top"]), None)
                if piece is not None:
                    swimmers.append((actor, volume["id"], piece))
                    break
    if swimmers:
        steps.append({"note": {"text": "MM9's swimmers stay in their water: " + ", ".join(
            f"{a['name']} {a['actor_index']} ({v})" for a, v, _ in swimmers)}})
        steps.append({"advance_runtime": {"seconds": 8}})
        for actor, _, piece in swimmers:
            p = actor["position"]
            bed = floors.z(p["x"], p["y"], p["z"] + 2)
            steps.append({"assert": {"actor_visible": {
                "actor_index": actor["actor_index"], "report_state": True,
                "near": {"x": p["x"], "y": p["y"], "max_distance": 3000,
                         "min_z": round(float(bed if bed is not None else piece["bottom"]) - 8, 1)}}}})
    if skipped:
        steps.insert(1, {"note": {"text": "No bed point (skipped): " + ", ".join(skipped)}})
    document = {"id": f"mm9r.{project.stem}_swim_check",
                "title": f"{project.display_name} (native BLV) - swim check: the party on each volume's bed, up to "
                         "its surface; swimmers stay in their water",
                "world": "mm9", "mode": "faithful", "tags": ["mm9", "mm9_rework", "draft"], "steps": steps}
    write(project.directory / "scenario_swim_check.yml", document, "mm9r_common/dungeon/swim_check.py")
    print(f"{len(volumes)} volumes, {len(skipped)} without a bed point, {len(swimmers)} swimmers")
    return 0


if __name__ == "__main__":
    sys.exit(main())
