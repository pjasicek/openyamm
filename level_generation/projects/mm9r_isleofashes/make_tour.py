#!/usr/bin/env python3
"""
Write a screenshot tour of the converted Isle of Ashes (aerial views, eye-level views on the larger islands, a shore)
from the map installed in the review root. Positions are the party's feet; the game adds the eye height.

    python3 level_generation/projects/mm9r_isleofashes/make_tour.py <name>
    ./tools/run_game.sh --isolated mm9isle --world mm9 --map isleofashes.odm \
        --assets "$PWD/output/mm9_rework/assets_dev" --set debug.screenshot_tour_path=<printed tour path>

With --original the same views are written for the current (bmodel_world) map in assets_dev, shifted by the
conversion's transform (work/transform.json), for a side-by-side comparison; run it without --assets.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import yaml
from scipy import ndimage

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
sys.path.insert(0, str(ROOT))
from util.map_export import parse_odm_file  # noqa: E402

MAP = ROOT / "output/mm9_rework/assets_dev/worlds/mm9/maps/isleofashes.odm"
GRID = 128
CELL = 512
HALF = GRID * CELL // 2


def main() -> int:
    arguments = [argument for argument in sys.argv[1:] if not argument.startswith("--")]
    original = "--original" in sys.argv
    name = (arguments[0] if arguments else "terrain") + ("_original" if original else "")
    native = parse_odm_file(MAP)["payload"]
    heights = np.array(native["height_map"], dtype=np.float64).reshape(GRID, GRID) * 32
    centre_x = lambda column: column * CELL - HALF + CELL / 2      # noqa: E731
    centre_y = lambda row: HALF - row * CELL - CELL / 2           # noqa: E731

    def ground(x, y):
        column = int(np.clip((x + HALF) / CELL, 0, GRID - 2))
        row = int(np.clip((HALF - y) / CELL, 0, GRID - 2))
        return float(heights[row:row + 2, column:column + 2].max())

    def look(label, eye, target, lift=0.0, target_lift=150.0):
        (ex, ey), (tx, ty) = eye, target
        z = ground(ex, ey) + lift
        pitch = math.atan2(ground(tx, ty) + target_lift - z - 176, math.hypot(tx - ex, ty - ey))
        return {"name": label, "position": [round(ex), round(ey), round(z)],
                "yaw": round(math.atan2(ty - ey, tx - ex), 4), "pitch": round(max(pitch, -1.45), 4)}

    corners = np.stack([heights[:-1, :-1], heights[1:, :-1], heights[:-1, 1:], heights[1:, 1:]])
    land = corners.max(0) > 0
    rows, columns = np.nonzero(land)
    middle = (centre_x(columns.mean()), centre_y(rows.mean()))
    span = max(np.ptp(columns), np.ptp(rows)) * CELL

    # Aerials stay under the fog's reach: a high camera sees only fog.
    shots = [
        {"name": "top_down", "position": [round(middle[0]), round(middle[1]), 9000], "yaw": 1.5708, "pitch": -1.5},
        look("aerial_south", (middle[0], middle[1] - span * 0.4), middle, lift=4500),
        look("aerial_west", (middle[0] - span * 0.4, middle[1]), middle, lift=4500),
    ]
    # Eye level on the four largest islands: from the flattest cell near each island's middle towards its highest
    # ground, and the same spot looking out to the next island.
    labels, count = ndimage.label(land)
    sizes = ndimage.sum(land, labels, range(1, count + 1))
    slope = corners.max(0) - corners.min(0)
    islands = sorted(range(1, count + 1), key=lambda index: -sizes[index - 1])[:4]
    middles = []
    for island in islands:
        r, c = np.nonzero(labels == island)
        middles.append((centre_x(c.mean()), centre_y(r.mean())))
    for number, island in enumerate(islands):
        r, c = np.nonzero(labels == island)
        distance = np.hypot(r - r.mean(), c - c.mean())
        best = np.argmin(slope[r, c] + distance * 24)
        eye = (centre_x(c[best]), centre_y(r[best]))
        high = np.argmax(corners.max(0)[r, c])
        shots.append(look(f"island{number + 1}_to_peak", eye, (centre_x(c[high]), centre_y(r[high]))))
        other = middles[(number + 1) % len(middles)]
        shots.append(look(f"island{number + 1}_outward", eye, other, target_lift=0))
    # A shore: the land cell beside the sea nearest the main island's middle, looking out.
    sea = ~land
    shore = land & ndimage.binary_dilation(sea)
    r, c = np.nonzero(shore & (labels == islands[0]))
    pick = np.argmin(np.hypot(centre_x(c) - middles[0][0], centre_y(r) - middles[0][1]))
    eye = (centre_x(c[pick]), centre_y(r[pick]))
    outward = (2 * eye[0] - middles[0][0], 2 * eye[1] - middles[0][1])
    shots.append(look("shore_out", eye, outward, target_lift=0))
    shots.append(look("shore_back", (eye[0] + (eye[0] - middles[0][0]) * 0.3, eye[1] + (eye[1] - middles[0][1]) * 0.3),
                      eye, lift=0, target_lift=300))

    # The largest structures: each framed from the side facing the island's middle, far enough to fit it.
    if "--structures" in sys.argv:
        shots = []
        bmodels = sorted((b for b in native["bmodels"] if b["name"] != "BMODEL_colliders"),
                         key=lambda b: -b["face_count"])[:10]
        for number, bmodel in enumerate(bmodels):
            low = np.array([bmodel["bounds_min"][k] for k in ("x", "y", "z")], dtype=float)
            high = np.array([bmodel["bounds_max"][k] for k in ("x", "y", "z")], dtype=float)
            centre = (low + high) / 2
            towards = np.array(middle) - centre[:2]
            towards = towards / max(np.linalg.norm(towards), 1.0)
            reach = max(np.ptp([low[:2], high[:2]], axis=0).max() * 0.9, 600.0) + 500
            eye = centre[:2] + towards * reach
            z = max(ground(*eye), 0.0) + 250
            pitch = math.atan2(centre[2] - z - 176, reach)
            shots.append({"name": f"structure{number:02d}", "position": [round(eye[0]), round(eye[1]), round(z)],
                          "yaw": round(math.atan2(centre[1] - eye[1], centre[0] - eye[0]), 4),
                          "pitch": round(pitch, 4)})
    if original:
        transform = json.loads((PROJECT / "work/transform.json").read_text())
        shift = (transform["offset_x"], transform["offset_y"], transform["sea_level_lt"] * transform["scale"])
        for shot in shots:
            shot["position"] = [round(value + delta) for value, delta in zip(shot["position"], shift)]
    output = PROJECT / "review" / name
    output.mkdir(parents=True, exist_ok=True)
    tour = {"output_dir": str(output), "settle_seconds": 2.5, "exit": True, "shots": shots}
    path = PROJECT / f"review_tour_{name}.yml"
    path.write_text(yaml.safe_dump(tour, sort_keys=False))
    first = shots[min(3, len(shots) - 1)]["position"]
    print(path)
    print(f"start: --position {first[0]} {first[1]} {first[2]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
