#!/usr/bin/env python3
"""
Forward probes up the stairs whose invisible ramp-wedge bottoms the converter now drops (floors.invisible_bottoms,
2026-10-31; DUNGEON_PLAYBOOK.md "Package change: invisible brush bottoms"). For each dropped bottom resting on a tread
(gap <= 8 LT) under an invisible sloped ramp top, the party starts DOWNHILL LT below the ramp's centre and walks uphill
for four seconds (and again from the ramp's own lower half); the same scenario runs against the snapshot taken before the rebuild (the old BLV) and the review root:

    python3 level_generation/projects/mm9r_common/stair_probes.py <stem> [--max 8]

Writes <project>/scenario_stair_probes.yml and work/stair_probes.json (per probe: start, walked xy and z, before and
after). A stair probe whose walk grows (or whose climb grows) after the rebuild is a stair the old invisible ceiling blocked.
Blocker probes walk (+x, native) into an invisible brush resting on the floor with no ramp (Firethrough boxes) from
40 LT (102 native) outside it: its sides must stop the party short of that distance, before and after.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dungeon.source import Project, Source, classify_models, floor_below  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
BEFORE = ROOT / "output/mm9_rework/lightmap_rollout_before"
AFTER = ROOT / "output/mm9_rework/assets_dev"
DOWNHILL = 48.0


def inside_xz(points: np.ndarray, x: float, z: float) -> bool:
    ring = points[:, [0, 2]]
    inside = False
    for i in range(len(ring)):
        (x1, z1), (x2, z2) = ring[i], ring[(i + 1) % len(ring)]
        if (z1 > z) != (z2 > z) and x < x1 + (z - z1) * (x2 - x1) / (z2 - z1):
            inside = not inside
    return inside


def probes(stem: str, limit: int) -> list[dict]:
    project = Project.load(ROOT / f"level_generation/projects/mm9r_{stem}", install=False)
    bottoms = json.loads((project.work / "invisible_bottoms.json").read_text())
    source = Source(project)
    polygons = [p for name in classify_models(source)["static"] for p in source.polygons(name)]
    ramps = [p for p in polygons if p.role == "invisible" and 0.2 < p.normal[1] < 0.97]
    found, seen, blockers = [], set(), []
    for bottom in sorted(bottoms, key=lambda b: b["gap_lt"]):
        if bottom["gap_lt"] > 8:
            continue
        x, y, z = bottom["centre_lt"]
        ramp = next((r for r in ramps if inside_xz(r.points, x, z) and y - 1 <= r.points[:, 1].min() <= y + 200
                     or (inside_xz(r.points, x, z) and r.points[:, 1].max() > y)), None)
        if ramp is None:
            blockers.append(bottom)
            continue
        key = id(ramp)
        if key in seen:
            continue
        seen.add(key)
        downhill = np.array([ramp.normal[0], ramp.normal[2]])
        if np.linalg.norm(downhill) < 1e-6:
            continue
        downhill /= np.linalg.norm(downhill)
        centre = ramp.points.mean(0)
        extent = float(np.max(np.abs((ramp.points[:, [0, 2]] - centre[[0, 2]]) @ downhill)))
        sx, sz = centre[[0, 2]] + downhill * (extent + DOWNHILL)
        floor = floor_below(polygons, (sx, centre[1] + 8, sz))
        if floor is None:
            continue
        start = project.native([sx, floor, sz])
        uphill = -downhill
        yaw = math.degrees(math.atan2(uphill[1], uphill[0])) % 360
        found.append({"kind": "stair", "ramp_centre_lt": centre.round(1).tolist(), "bottom_gap_lt": bottom["gap_lt"],
                      "start": [int(round(start[0])), int(round(start[1])), int(round(start[2])) + 1],
                      "yaw_degrees": round(yaw, 1)})
        # and from the ramp's own lower half, as the Temple of Honk's stuck party stood (on one wedge, facing the next)
        on = centre[[0, 2]] + downhill * extent * 0.5
        floor = floor_below(polygons, (on[0], ramp.points[:, 1].max() + 8, on[1]))
        if floor is not None:
            start = project.native([on[0], floor, on[1]])
            found.append({"kind": "stair", "ramp_centre_lt": centre.round(1).tolist(), "bottom_gap_lt": bottom["gap_lt"],
                          "start": [int(round(start[0])), int(round(start[1])), int(round(start[2])) + 1],
                          "yaw_degrees": round(yaw, 1), "on_ramp": True})
        if len(found) >= limit:
            break
    # Brushes resting on the floor without a ramp (Firethrough boxes, invisible blocks): walk into one from outside;
    # its sides must still stop the party short of its footprint now that its bottom is gone.
    taken = 0
    for bottom in blockers:
        if taken >= max(2, limit // 2) or bottom["gap_lt"] > 8:
            continue
        x, y, z = bottom["centre_lt"]
        box = next((p for p in polygons if p.role == "invisible" and p.normal[1] < -0.3
                    and np.allclose(p.points.mean(0), bottom["centre_lt"], atol=0.2)), None)
        half = float(np.max(np.abs(box.points[:, 0] - x))) if box is not None else 32.0
        sx = x - half - 40.0
        floor = floor_below(polygons, (sx, y + 8, z))
        if floor is None or abs(floor - y) > 8:
            continue
        start = project.native([sx, floor, z])
        found.append({"kind": "blocker", "brush_centre_lt": [x, y, z], "edge_distance_native": round(40.0 * 2.56),
                      "start": [int(round(start[0])), int(round(start[1])), int(round(start[2])) + 1],
                      "yaw_degrees": 0.0})
        taken += 1
    return found


def scenario(stem: str, found: list[dict]) -> dict:
    steps = [{"load_map": {"map": f"{stem}.blv"}}]
    for probe in found:
        pose = {"map": f"{stem}.blv", "x": probe["start"][0], "y": probe["start"][1], "z": probe["start"][2],
                "yaw_degrees": probe["yaw_degrees"], "pitch": 0}
        steps.append({"movement_segment": {"input": "forward", "seconds": 2.0 if probe["kind"] == "blocker" else 4.0, "actor_collision": False,
                                           "actor_ai": False, "start": pose, "expect_stop": pose,
                                           "loose_tolerance": True, "tolerance_xy": 5000, "tolerance_z": 5000}})
    return {"id": f"lmroll.{stem}_stair_probes", "title": "stair probes over dropped invisible bottoms",
            "world": "mm9", "mode": "faithful", "tags": ["probe"], "steps": steps}


def run(path: Path, root: Path) -> list[tuple[float, float]]:
    result = subprocess.run([str(ROOT / "build/game/openyamm"), "--asset-root", str(root), "--headless-run-scenario",
                             str(path), "--scenario-no-color"], cwd=ROOT, capture_output=True, text=True)
    text = result.stdout + result.stderr
    xy = [float(v) for v in re.findall(r"movement\.walk_xy_distance .*?actual=([-\d.]+)", text)]
    z = [float(v) for v in re.findall(r"movement\.walk_z_distance .*?actual=([-\d.]+)", text)]
    return list(zip(xy, z))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("stem")
    ap.add_argument("--max", type=int, default=8)
    args = ap.parse_args()
    project_dir = ROOT / f"level_generation/projects/mm9r_{args.stem}"
    found = probes(args.stem, args.max)
    if not found:
        print(f"{args.stem}: no dropped bottom under a ramp")
        return 0
    path = project_dir / "scenario_stair_probes.yml"
    path.write_text(yaml.safe_dump(scenario(args.stem, found), sort_keys=False))
    before, after = run(path, BEFORE), run(path, AFTER)
    for probe, b, a in zip(found, before + [None] * len(found), after + [None] * len(found)):
        probe["before_xy_z"], probe["after_xy_z"] = b, a
    (project_dir / "work/stair_probes.json").write_text(json.dumps(found, indent=1) + "\n")
    for probe in found:
        print(probe["start"], probe["yaw_degrees"], "before", probe["before_xy_z"], "after", probe["after_xy_z"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
