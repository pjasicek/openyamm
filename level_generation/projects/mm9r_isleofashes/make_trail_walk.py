#!/usr/bin/env python3
"""
Write trail_walk.yml: a headless scenario that walks the party along MM9's trails on the converted Isle of Ashes, one
movement segment per ~400 units, and report which segments were blocked. The trails are traced on MM9's own terrain:
the cheapest line between two endpoints over MM9-walkable ground, preferring the painted map's pale trails
(convert.painted_trails). Each segment starts at a waypoint facing the next one and walks for about the time it needs.

    python3 level_generation/projects/mm9r_isleofashes/make_trail_walk.py
    cd output/mm9_rework/scenario_run && ../../../build/game/openyamm --world mm9 \\
        --headless-run-scenario ../../../level_generation/projects/mm9r_isleofashes/trail_walk.yml \\
        --scenario-no-color > /tmp/trail_walk.log
    python3 level_generation/projects/mm9r_isleofashes/make_trail_walk.py --report /tmp/trail_walk.log

A segment counts as blocked when the party covers under 85 % of it. Segments are straight, so one that clips the
corner of a steep cell can stop although the party walks round it; check a blocked segment's cells before grading.
"""

from __future__ import annotations

import heapq
import json
import math
import re
import sys
from pathlib import Path

import numpy as np
import yaml
from scipy import ndimage

import convert as C
from util.map_export import parse_odm_file

OUTPUT = C.PROJECT / "trail_walk.yml"
MAP = C.ROOT / "output/mm9_rework/assets_dev/worlds/mm9/maps/isleofashes.odm"
SPACING = 384
WALK_SPEED = 700                # units per second, measured on the isle (the party's run speed)

# Trails to walk, by endpoint (this map's frame). Added from the user's review of 2026-11-01.
TRAILS = [
    ("yrsa_hut_climb", (2214, -15596), (4597, -13247)),     # from Yrsa's hut up the valley to the ring trail
    ("ring_south", (4597, -13247), (7993, -10638)),         # the ring round the north-east mountain, east side
    ("ring_north", (7993, -10638), (4200, -9480)),          # and back over its north side
]


def trail_cost():
    x, y, z, texture, _, transform = C.load_terrain()
    size = C.GRID * C.FINE_PER_CELL
    top, _, _, _ = C.rasterize(x, y, z, texture, -C.HALF + C.FINE / 2, C.HALF - C.FINE / 2, C.FINE, size)
    land = top > C.LAND_ABOVE_SEA
    smooth = ndimage.uniform_filter(np.where(land, top, 0.0), 2)
    gradient_r, gradient_c = np.gradient(smooth, C.FINE)
    walk = land & (np.degrees(np.arctan(np.hypot(gradient_r, gradient_c))) < 50)
    trail = C.painted_trails(transform)
    cost = np.where(walk & trail, 1.0, np.where(walk, 3.0, 40.0))
    cost[~land] = 1e6
    return cost


def trace(cost, start, end):
    def sample(point):
        return (int((C.HALF - C.FINE / 2 - point[1]) // C.FINE), int((point[0] + C.HALF - C.FINE / 2) // C.FINE))

    source, target = sample(start), sample(end)
    distance, previous, queue = {source: 0.0}, {}, [(0.0, source)]
    while queue:
        cost_so_far, node = heapq.heappop(queue)
        if node == target:
            break
        if cost_so_far > distance[node]:
            continue
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                step = (node[0] + dr, node[1] + dc)
                if (dr or dc) and 0 <= step[0] < cost.shape[0] and 0 <= step[1] < cost.shape[1]:
                    total = cost_so_far + cost[step] * math.hypot(dr, dc)
                    if total < distance.get(step, math.inf):
                        distance[step], previous[step] = total, node
                        heapq.heappush(queue, (total, step))
    path = [target]
    while path[-1] != source:
        path.append(previous[path[-1]])
    points = [(c * C.FINE - C.HALF + C.FINE / 2, C.HALF - C.FINE / 2 - r * C.FINE) for r, c in reversed(path)]
    waypoints, travelled = [points[0]], 0.0
    for a, b in zip(points, points[1:]):
        travelled += math.dist(a, b)
        if travelled >= SPACING:
            waypoints.append(b)
            travelled = 0.0
    if waypoints[-1] != points[-1]:
        waypoints.append(points[-1])
    return waypoints


def write() -> None:
    heights = np.array(parse_odm_file(MAP)["payload"]["height_map"], float).reshape(C.GRID, C.GRID) * C.HEIGHT_STEP
    cost = trail_cost()
    steps = [{"new_game_flow": {"start_map": C.MAP}}]
    for name, start, end in TRAILS:
        steps.append({"note": {"text": name}})
        waypoints = trace(cost, start, end)
        for a, b in zip(waypoints, waypoints[1:]):
            yaw = round(math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])), 1)
            row, column = int((C.HALF - a[1]) // C.CELL), int((a[0] + C.HALF) // C.CELL)
            z = int(heights[row:row + 2, column:column + 2].max()) + 64
            steps.append({"movement_segment": {
                "input": "forward", "seconds": round(math.dist(a, b) / WALK_SPEED + 0.1, 2),
                "actor_collision": False, "actor_ai": False,
                "start": {"map": C.MAP, "x": int(a[0]), "y": int(a[1]), "z": z, "yaw_degrees": yaw, "pitch": 0},
                "expect_stop": {"map": C.MAP, "x": int(b[0]), "y": int(b[1]), "z": 0, "yaw_degrees": yaw, "pitch": 0},
                "loose_tolerance": True, "tolerance_xy": 5000, "tolerance_z": 5000}})
        print(f"{name}: {len(waypoints) - 1} segments")
    OUTPUT.write_text(yaml.safe_dump({"id": "mm9r.isleofashes.trail_walk", "title": "Walk MM9's trails on the isle",
                                      "world": "mm9", "mode": "faithful", "steps": steps}, sort_keys=False))
    print(OUTPUT)


def report(log: Path) -> int:
    trail, index, blocked = None, 0, 0
    for line in log.read_text().splitlines():
        note = re.search(r"\bnote\b.*text=(\S+)", line)
        if note:
            trail, index = note.group(1), 0
            continue
        walked = re.search(r"walk_xy_distance expected=([\d.]+).*actual=([\d.]+)", line)
        if walked:
            index += 1
            expected, actual = float(walked.group(1)), float(walked.group(2))
            if actual < 0.85 * expected:
                blocked += 1
                print(f"{trail} segment {index}: walked {actual:.0f} of {expected:.0f}")
    print(f"{blocked} blocked segments")
    return 1 if blocked else 0


if __name__ == "__main__":
    if "--report" in sys.argv:
        sys.exit(report(Path(sys.argv[sys.argv.index("--report") + 1])))
    write()
