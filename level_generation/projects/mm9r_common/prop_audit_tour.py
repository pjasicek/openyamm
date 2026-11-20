#!/usr/bin/env python3
"""
Screenshot tours of decorations in a built review-root BLV (prop_audit.py's visual pass): one shot per named entity,
the camera 110-260 units away in the first of 16 directions whose eye sees the prop's centre past every map face,
standing on the floor under the eye, pitched at the prop.

    python3 level_generation/projects/mm9r_common/prop_audit_tour.py <stem> <tour name> <entity> [<entity> ...]
    -> output/mm9_rework/prop_audit_20261107/<stem>/<tour name>.yml (shots in .../<stem>/<tour name>/)
Run it: ./tools/run_game.sh --isolated <name> --world mm9 --map <stem>.blv --assets output/mm9_rework/assets_dev
        --set debug.screenshot_tour_path=<yml>
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[2]))

import prop_audit as pa                                          # noqa: E402
from util.map_export import parse_blv_file                       # noqa: E402

EYE = 160.0                 # native units: the party's eye over its feet (approximate; only the pitch uses it)
DISTANCES = (130.0, 180.0, 240.0, 320.0)


def blocked(tris: np.ndarray, a: np.ndarray, b: np.ndarray) -> bool:
    """Whether the segment a-b crosses a map triangle (Moller-Trumbore), short of b by 20 units."""
    d = b - a
    length = float(np.linalg.norm(d))
    d = d / length
    e1, e2 = tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0]
    p = np.cross(d, e2)
    det = np.einsum("ij,ij->i", e1, p)
    ok = np.abs(det) > 1e-9
    inv = np.zeros_like(det)
    inv[ok] = 1.0 / det[ok]
    s = a - tris[:, 0]
    u = np.einsum("ij,ij->i", s, p) * inv
    q = np.cross(s, e1)
    v = (q @ d) * inv
    t = np.einsum("ij,ij->i", e2, q) * inv
    hit = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 1.0) & (t < length - 20.0)
    return bool(hit.any())


def main(argv: list[str]) -> None:
    stem, tour_name, names = argv[0], argv[1], set(argv[2:])
    blv = parse_blv_file(pa.MAPS / f"{stem}.blv")["payload"]
    geometry = pa.Geometry(blv)
    decorations, binds = pa.decoration_names(), pa.bindings()
    out = pa.OUT / stem
    # every decoration's triangles (the views must see past the furniture too)
    placed = {}
    for entity in blv["entities"]:
        binding = binds.get(decorations.get(entity["decoration_list_id"], ""))
        if binding is None:
            continue
        position = entity["position"]
        points, triangles = pa.placed_ours(binding, (position["x"], position["y"], position["z"]),
                                           float(entity["facing"]))
        placed[entity["name"]] = points[triangles]
    shots = []
    for entity in blv["entities"]:
        if entity["name"] not in names:
            continue
        binding = binds.get(decorations.get(entity["decoration_list_id"], ""))
        position = entity["position"]
        if binding is None:
            continue
        points, _ = pa.placed_ours(binding, (position["x"], position["y"], position["z"]), float(entity["facing"]))
        centre = (points.min(0) + points.max(0)) / 2
        size = float(np.max(np.ptp(points, 0)))
        reach = 400 + 2 * size
        others = [t for name, t in placed.items() if name != entity["name"]]
        tris = np.concatenate([geometry.tris] + others)
        near = np.all(tris.max(1) >= centre - reach, 1) & np.all(tris.min(1) <= centre + reach, 1)
        tris = tris[near]
        found = None
        distances = sorted(set(DISTANCES) | {0.9 * size + 60}, key=lambda d: abs(d - (0.9 * size + 60)))
        # past the furniture first, else past the map's faces only
        for view_tris in (tris, geometry.tris[np.all(geometry.tris.max(1) >= centre - reach, 1)
                                              & np.all(geometry.tris.min(1) <= centre + reach, 1)]):
            for distance in distances:
                for k in range(16):
                    angle = math.radians(float(entity["facing"]) + 22.5 * k)
                    xy = centre[:2] + distance * np.array([math.cos(angle), math.sin(angle)])
                    floor = pa.support_heights(geometry.up, xy[None], centre[2] + 120)[0]
                    if not np.isfinite(floor):
                        continue
                    eye = np.array([xy[0], xy[1], floor + EYE])
                    if not blocked(view_tris, eye, centre):
                        found = (xy, floor, eye)
                        break
                if found:
                    break
            if found:
                break
        if not found:
            print(f"{entity['name']}: no clear view")
            continue
        xy, floor, eye = found
        to = centre - eye
        shots.append({"name": entity["name"], "position": [round(float(xy[0])), round(float(xy[1])), round(float(floor)) + 1],
                      "yaw": round(math.atan2(to[1], to[0]), 4),
                      "pitch": round(math.atan2(to[2], float(np.linalg.norm(to[:2]))), 4)})
    out.mkdir(parents=True, exist_ok=True)
    tour = {"output_dir": str(out / tour_name), "settle_seconds": 1.5, "exit": True, "shots": shots}
    path = out / f"{tour_name}.yml"
    path.write_text(yaml.safe_dump(tour, sort_keys=False))
    print(path, len(shots), "shots")


if __name__ == "__main__":
    main(sys.argv[1:])
