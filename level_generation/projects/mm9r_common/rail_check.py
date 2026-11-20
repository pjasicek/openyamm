#!/usr/bin/env python3
"""
Rail reachability: does the built map's monster path map join what MM9's own AI navigation joined?

MM9 hand-placed its monsters' navigation as AIRail volumes (the AITrk brushes, about 8 100 in 32 maps) linked to one
another (RailLink0-3): MM9's AI walked from each rail into the ones it links. Every link is a pair of points a walking
monster should be able to reach in our BLV as well. This plans a walking monster's path for each link on the
installed map's monster path map (the engine's `--headless-check-indoor-reachability`, barriers included) and lists the
links it cannot join, with positions: a crack in a floor, a slope the monster's rule refuses, a step the path map
misses or a barrier in the way; each is given a likely cause (`classify`: door, barrier, climb, level). Ladder rails
are left out. A failed link is retried between points over both boxes (MM9 links boxes, not their centres), in
parallel. It changes nothing; run it after convert.py (about 20 s a map).

    python3 level_generation/projects/mm9r_common/rail_check.py level_generation/projects/mm9r_<map> [--assets ROOT]

ROOT is the review root the map is installed in (default output/mm9_rework/assets_dev; the outdoor-as-BLV pilots use
output/mm9_rework/isleofashes_blv_root). Writes work/rail_reachability.json.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dungeon.source import ROOT, Project, Source  # noqa: E402

sys.path.insert(0, str(ROOT))
from util.map_export import parse_blv_file  # noqa: E402

GAME = ROOT / "build/game/openyamm"
SETTINGS_TEMPLATE = ROOT / "output/mm9_rework/scenario_run/settings.ini"
UNTOUCHABLE, INVISIBLE = 0x20000000, 0x00002000
# A rail is a thin slab (about 41 high) lying on its floor: the floor is the highest one at most a step over the slab's
# bottom (a floor 225 over it is the storey above, Klusos House's balconies) and at most FLOOR_REACH under it (rails
# float a little over stairs). Native units.
FLOOR_ABOVE = 48.0
FLOOR_REACH = 256.0
# The walking monster the paths are planned for (native units): a man-sized MM9 monster.
BODY = {"radius": 32.0, "height": 128.0}
# Retries of a failed link: search limit per plan and parallel runs.
RETRY_NODE_LIMIT = 2000
RETRY_PROCESSES = 8


def floor_faces(blv: dict) -> list:
    """The BLV's walkable floor faces as (ring xy, plane), the faces a monster stands on."""
    vertices = np.array([[v["x"], v["y"], v["z"]] if isinstance(v, dict) else v for v in blv["vertices"]], float)
    floors = []
    for face in blv["faces"]:
        if face["is_portal"] or face["attributes"] & UNTOUCHABLE or len(face["vertex_indices"]) < 3:
            continue
        points = vertices[face["vertex_indices"]]
        normal = np.zeros(3)
        for k in range(1, len(points) - 1):
            normal += np.cross(points[k] - points[0], points[k + 1] - points[0])
        length = np.linalg.norm(normal)
        if length < 1e-6 or normal[2] / length < 0.6:
            continue
        floors.append((points, normal / length))
    return floors


def floor_under(floors: list, x: float, y: float, z_top: float):
    """The highest floor under (x, y) at most z_top, or None."""
    best = None
    for points, normal in floors:
        if not (points[:, 0].min() <= x <= points[:, 0].max() and points[:, 1].min() <= y <= points[:, 1].max()):
            continue
        ring = points[:, :2]
        inside = False
        for (x1, y1), (x2, y2) in zip(ring, np.roll(ring, -1, axis=0)):
            if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
                inside = not inside
        if not inside:
            continue
        height = points[0, 2] - (normal[0] * (x - points[0, 0]) + normal[1] * (y - points[0, 1])) / normal[2]
        if height <= z_top and (best is None or height > best):
            best = height
    return best


def rail_points(project: Project, source: Source, floors: list, boxes: dict | None = None) -> dict:
    """Each walkable rail's floor point (native feet position) under the middle of its volume's bottom; `boxes`
    receives each rail's plan extent and floor height for the retries."""
    points = {}
    for o in source.objects:
        if o["class"] != "AIRail" or o["properties"].get("IsLadder"):
            continue
        model = source.models.get(o["name"])
        if model is None:
            continue
        native = project.native(np.array(model.points, float))
        low, high = native.min(axis=0), native.max(axis=0)
        x, y = (low[0] + high[0]) / 2, (low[1] + high[1]) / 2
        floor = floor_under(floors, x, y, low[2] + FLOOR_ABOVE)
        if floor is not None and floor >= low[2] - FLOOR_REACH:
            points[o["name"]] = [round(float(x), 1), round(float(y), 1), round(float(floor), 1)]
            if boxes is not None:
                boxes[o["name"]] = (low, high, floor)
        else:
            points[o["name"]] = None
    return points


def box_samples(floors: list, box) -> list:
    """Points over a rail box's floor: a 3 x 3 grid inside its plan extent, each on the floor under it (the box's own
    floor height, a step up allowed)."""
    low, high, floor = box
    points = []
    for fx in (0.2, 0.5, 0.8):
        for fy in (0.2, 0.5, 0.8):
            x, y = low[0] + (high[0] - low[0]) * fx, low[1] + (high[1] - low[1]) * fy
            z = floor_under(floors, x, y, floor + FLOOR_ABOVE)
            if z is not None and z >= floor - FLOOR_REACH:
                points.append([round(float(x), 1), round(float(y), 1), round(float(z), 1)])
    return points


def crosses_faces(vertices: np.ndarray, faces: list, face_ids, a, b) -> bool:
    """Whether the segment a-b, lifted 40 and 100 over the feet, passes through one of the faces."""
    for face_id in face_ids:
        points = vertices[faces[face_id]["vertex_indices"]]
        normal = np.cross(points[1] - points[0], points[2] - points[0])
        if np.linalg.norm(normal) < 1e-6:
            continue
        normal /= np.linalg.norm(normal)
        axis = int(np.argmax(np.abs(normal)))
        keep = [i for i in range(3) if i != axis]
        for lift in (40.0, 100.0):
            start, end = np.array(a, float) + [0, 0, lift], np.array(b, float) + [0, 0, lift]
            da, db = np.dot(start - points[0], normal), np.dot(end - points[0], normal)
            if da * db > 0 or da == db:
                continue
            hit = start + (end - start) * da / (da - db)
            x, y = hit[keep]
            ring = points[:, keep]
            inside = False
            for (x1, y1), (x2, y2) in zip(ring, np.roll(ring, -1, axis=0)):
                if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
                    inside = not inside
            if inside:
                return True
    return False


def classify(project: Project, blv: dict, unreached: list) -> None:
    """Each unreached link's likely cause: `door` (it passes a door, closed in the map's starting pose: monsters do
    not open doors, expected), `barrier` (one of the monster barriers stands across it), `climb` (over 60 up or down:
    stairs, ramps) or `level` (neither): the last two are the ones to look at."""
    scene = yaml.safe_load((project.work / "runtime" / f"{project.stem}.scene.yml").read_text())
    vertices = np.array([[v["x"], v["y"], v["z"]] if isinstance(v, dict) else v for v in blv["vertices"]], float)
    doors = {face for door in scene["initial_state"]["doors"] for face in door["face_ids"]}
    barriers = set((scene.get("actor_barriers") or {}).get("faces", []))
    for link in unreached:
        # The face the engine's straight walk stops at decides first (a rail's centre can lie just short of a door,
        # where a body's radius already meets it); then whatever the segment itself passes through.
        if link.get("walk_face") in doors:
            link["cause"] = "door"
        elif link.get("walk_face") in barriers:
            link["cause"] = "barrier"
        elif crosses_faces(vertices, blv["faces"], barriers, link["from"], link["to"]):
            link["cause"] = "barrier"
        elif crosses_faces(vertices, blv["faces"], doors, link["from"], link["to"]):
            link["cause"] = "door"
        else:
            link["cause"] = "climb" if abs(link["to"][2] - link["from"][2]) > 60 else "level"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("project", type=Path)
    parser.add_argument("--assets", type=Path, default=ROOT / "output/mm9_rework/assets_dev")
    args = parser.parse_args()
    project = Project.load(args.project.resolve())
    source = Source(project)
    blv = parse_blv_file(project.work / "runtime" / project.map)["payload"]
    floors = floor_faces(blv)
    boxes = {}
    points = rail_points(project, source, floors, boxes)
    rails = {o["name"]: o for o in source.objects if o["class"] == "AIRail"}
    pairs, no_floor, seen = [], set(), set()
    for name, rail in rails.items():
        for slot in range(4):
            other = rail["properties"].get(f"RailLink{slot}") or ""
            if not other or other not in rails or (other, name) in seen or (name, other) in seen:
                continue
            seen.add((name, other))
            if points.get(name) is None or points.get(other) is None:
                no_floor.update(n for n in (name, other) if points.get(n) is None and n in points)
                continue
            pairs.append({"id": f"{name}>{other}", "from": points[name], "to": points[other]})

    run = project.work / "rail_check_run"
    run.mkdir(parents=True, exist_ok=True)
    settings = SETTINGS_TEMPLATE.read_text().split("\n")
    settings = [f"root={args.assets.resolve()}" if line.startswith("root=") else line for line in settings]
    (run / "settings.ini").write_text("\n".join(settings))
    (run / "pairs.yml").write_text(yaml.safe_dump({"object": BODY, "pairs": pairs}))
    result = subprocess.run([str(GAME), "--world", "mm9", "--headless-check-indoor-reachability", project.map,
                             str(run / "pairs.yml"), str(run / "result.yml")], cwd=run, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stdout[-2000:], result.stderr[-2000:])
        return 1
    plans = {entry["id"]: entry for entry in yaml.safe_load((run / "result.yml").read_text())["pairs"] or []}
    keys = ("status", "source_valid", "target_valid", "walk", "walk_at", "walk_face", "walk_step")
    unreached = [dict(pair, **{k: plans[pair["id"]].get(k) for k in keys})
                 for pair in pairs if not plans[pair["id"]].get("reached", plans[pair["id"]]["status"] == "success")]
    # MM9 links boxes, not their centres: a centre can fall inside a pillar's base or a coffin standing in the box.
    # A failed link is tried again between points spread over both boxes, and counts when any pair connects.
    # Not retried: a link the straight walk finds shut by a door (monsters open no doors, no box point gets through).
    # Each link's retries share a group, stop at the first that connects and search at most RETRY_NODE_LIMIT nodes
    # (the boxes are neighbours); the links are split over parallel runs.
    scene = yaml.safe_load((project.work / "runtime" / f"{project.stem}.scene.yml").read_text())
    door_faces = {face for door in scene["initial_state"]["doors"] for face in door["face_ids"]}
    groups = []
    for link in unreached:
        if link.get("walk_face") in door_faces:
            continue
        first, second = link["id"].split(">")
        groups.append([{"id": f"{link['id']}#{k}.{l}", "group": link["id"], "from": a, "to": b}
                       for k, a in enumerate(box_samples(floors, boxes[first]))
                       for l, b in enumerate(box_samples(floors, boxes[second]))])
    jobs = []
    for index in range(min(RETRY_PROCESSES, len(groups))):
        chunk = [pair for group in groups[index::RETRY_PROCESSES] for pair in group]
        (run / f"retries_{index}.yml").write_text(
            yaml.safe_dump({"object": BODY, "node_limit": RETRY_NODE_LIMIT, "pairs": chunk}))
        jobs.append(subprocess.Popen([str(GAME), "--world", "mm9", "--headless-check-indoor-reachability",
                                      project.map, str(run / f"retries_{index}.yml"),
                                      str(run / f"retries_{index}_result.yml")], cwd=run,
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
    connected = set()
    for index, job in enumerate(jobs):
        if job.wait() != 0:
            raise SystemExit(f"retry run {index} failed")
        entries = yaml.safe_load((run / f"retries_{index}_result.yml").read_text())["pairs"] or []
        connected |= {entry["id"].split("#")[0] for entry in entries if entry.get("reached")}
    unreached = [link for link in unreached if link["id"] not in connected]
    classify(project, blv, unreached)
    causes = {cause: sum(1 for link in unreached if link["cause"] == cause)
              for cause in ("door", "barrier", "climb", "level")}
    report = {"map": project.map, "rails": len(rails), "links": len(pairs), "reached": len(pairs) - len(unreached),
              "unreached_by_cause": causes, "unreached": unreached, "rails_without_floor": sorted(no_floor)}
    (project.work / "rail_reachability.json").write_text(json.dumps(report, indent=1) + "\n")
    print(f"{project.map}: {report['reached']} of {len(pairs)} MM9 rail links reachable on the monster path map; "
          f"unreached by cause {causes}; {len(no_floor)} rails without a floor under them; "
          "work/rail_reachability.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
