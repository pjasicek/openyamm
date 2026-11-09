#!/usr/bin/env python3
"""
Compare the converted Isle of Ashes against the original, as surfaces: where MM9 has land or structure above the sea
and the native map has neither (lost), where the native map has land MM9 does not (added), and for every native
structure how its foundation meets the ground: the gap between its lowest vertices and the native terrain under
them, against the same gap over MM9's terrain. A foundation that met MM9's ground but floats over ours marks
terrain the conversion lost.

    python3 level_generation/projects/mm9r_isleofashes/check_placement.py
Writes work/placement.png (red lost, blue added, yellow floating foundations, magenta buried) and
work/placement.json.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT))
import convert  # noqa: E402

STEP = 64
SIZE = convert.GRID * convert.CELL // STEP
ORIGIN = -convert.HALF + STEP / 2
INVISIBLE = {"invisible", "firethrough", "skymarker", "soundonly", "greenscreen", "perception", "rail", "aibarrier"}
SKIP_MODELS = ("bluewater", "clearwater", "ocean", "water", "visbsp", "skybox", "tod_sky", "aitrk", "aibarrier",
               "perceptionbrush", "invisiblebrush")
FOUNDATION_BAND = 48            # vertices this close to a structure's lowest point form its foundation
SURFACE = 16                    # above the sea


def mm9_surfaces(transform):
    """Top surfaces of MM9's visible geometry: terrain alone and everything (terrain, structures, props)."""
    world = convert.read_dat_world(convert.DAT)
    groups = {"terrain": [], "all": []}
    for model in world.world_models:
        name = model.name.lower()
        if name.startswith(SKIP_MODELS):
            continue
        for poly in model.polies:
            texture = model.textures[model.surfaces[poly.surface_index].texture_index].replace("\\", "/").lower()
            stem = texture.rsplit("/", 1)[-1].rsplit(".", 1)[0]
            if stem in INVISIBLE or texture.endswith(".spr"):
                continue
            points = [model.points[vertex.vertex_index] for vertex in poly.disk_verts]
            for index in range(1, len(points) - 1):
                triangle = (points[0], points[index], points[index + 1])
                groups["all"].append(triangle)
                if "/terrain/" in texture and name != "physicsbsp":
                    groups["terrain"].append(triangle)
    result = {}
    for key, triangles in groups.items():
        t = np.array(triangles, dtype=np.float64)
        x = t[:, :, 0] * transform["scale"] - transform["offset_x"]
        y = t[:, :, 2] * transform["scale"] - transform["offset_y"]
        z = (t[:, :, 1] - transform["sea_level_lt"]) * transform["scale"]
        top, _, _, _ = convert.rasterize(x, y, z, np.zeros(len(t), int), ORIGIN, -ORIGIN, STEP, SIZE)
        result[key] = top
    return result


def native_surfaces(native):
    heights = np.array(native["height_map"], dtype=np.float64).reshape(convert.GRID, convert.GRID) * 32
    xs = ORIGIN + STEP * np.arange(SIZE)            # columns run west to east
    ys = -ORIGIN - STEP * np.arange(SIZE)           # rows run north to south, as the rasters
    columns = (xs + convert.HALF) / convert.CELL
    rows = (convert.HALF - ys) / convert.CELL
    c0 = np.clip(np.floor(columns).astype(int), 0, convert.GRID - 2)
    r0 = np.clip(np.floor(rows).astype(int), 0, convert.GRID - 2)
    fc, fr = np.meshgrid(columns - c0, rows - r0)
    C, R = np.meshgrid(c0, r0)
    h00, h10, h01, h11 = heights[R, C], heights[R, C + 1], heights[R + 1, C], heights[R + 1, C + 1]
    lower = fc + fr <= 1
    terrain = np.where(lower, h00 + (h10 - h00) * fc + (h01 - h00) * fr,
                       h11 + (h01 - h11) * (1 - fc) + (h10 - h11) * (1 - fr))
    triangles = []
    for bmodel in native["bmodels"]:
        if bmodel["name"] == "BMODEL_colliders":
            continue
        vertices = np.array([[v["x"], v["y"], v["z"]] for v in bmodel["vertices"]], dtype=np.float64)
        for face in bmodel["faces"]:
            ids = face["vertex_indices"][:face["vertex_count"]]
            for index in range(1, len(ids) - 1):
                triangles.append(vertices[[ids[0], ids[index], ids[index + 1]]])
    t = np.array(triangles)
    structures, _, _, _ = convert.rasterize(t[:, :, 0], t[:, :, 1], t[:, :, 2], np.zeros(len(t), int),
                                            ORIGIN, -ORIGIN, STEP, SIZE)
    return terrain, structures


def sample(grid, x, y):
    column = int(np.clip((x - ORIGIN) / STEP, 0, SIZE - 1))
    row = int(np.clip((-ORIGIN - y) / STEP, 0, SIZE - 1))
    return float(grid[row, column])


def main() -> int:
    transform = json.loads((convert.WORK / "transform.json").read_text())
    native = convert.parse_odm_file(convert.review_root.mirror_path(Path("worlds/mm9/maps") / convert.MAP))["payload"]
    mm9 = mm9_surfaces(transform)
    terrain, structures = native_surfaces(native)
    mm9_surface = mm9["all"] > SURFACE
    native_surface = (terrain > SURFACE) | (structures > SURFACE)
    lost = mm9_surface & ~native_surface
    added = (terrain > SURFACE) & ~mm9_surface
    mm9_ground = np.where(mm9["terrain"] > -1e8, np.maximum(mm9["terrain"], 0), 0)

    report = {"lost_area": int(lost.sum() * STEP * STEP), "added_area": int(added.sum() * STEP * STEP),
              "structures": []}
    image = np.zeros((SIZE, SIZE, 3), np.uint8)
    image[:] = (20, 40, 90)
    image[terrain > SURFACE] = (90, 90, 90)
    image[structures > SURFACE] = (200, 200, 200)
    image[lost] = (230, 40, 40)
    image[added] = (60, 110, 255)
    for bmodel in native["bmodels"]:
        if bmodel["name"] == "BMODEL_colliders":
            continue
        vertices = np.array([[v["x"], v["y"], v["z"]] for v in bmodel["vertices"]], dtype=np.float64)
        foundation = vertices[vertices[:, 2] <= vertices[:, 2].min() + FOUNDATION_BAND]
        native_gaps = [v[2] - max(sample(terrain, v[0], v[1]), 0.0) for v in foundation]
        mm9_gaps = [v[2] - sample(mm9_ground, v[0], v[1]) for v in foundation]
        entry = {"name": bmodel["name"], "faces": bmodel["face_count"],
                 "x": int(foundation[:, 0].mean()), "y": int(foundation[:, 1].mean()), "z": int(foundation[:, 2].min()),
                 "native_gap": [int(np.min(native_gaps)), int(np.median(native_gaps)), int(np.max(native_gaps))],
                 "mm9_gap": [int(np.min(mm9_gaps)), int(np.median(mm9_gaps)), int(np.max(mm9_gaps))]}
        report["structures"].append(entry)
        floating = np.median(native_gaps) > 64 and np.median(native_gaps) - np.median(mm9_gaps) > 64
        buried = np.median(native_gaps) < -64 and np.median(native_gaps) - np.median(mm9_gaps) < -64
        if floating or buried:
            for v in foundation:
                column = int((v[0] - ORIGIN) / STEP)
                row = int((-ORIGIN - v[1]) / STEP)
                image[max(row - 2, 0):row + 3, max(column - 2, 0):column + 3] = \
                    (255, 220, 0) if floating else (255, 0, 255)
    rows, columns = np.nonzero(mm9_surface | native_surface)
    crop = image[rows.min() - 8:rows.max() + 8, columns.min() - 8:columns.max() + 8]
    Image.fromarray(crop).save(convert.WORK / "placement.png")
    (convert.WORK / "placement.json").write_text(json.dumps(report, indent=1) + "\n")
    print(f"lost {report['lost_area'] / 1e6:.1f} M units^2 of MM9 surface above the sea, added "
          f"{report['added_area'] / 1e6:.1f} M")
    print("structure                 faces   native gap (min/median/max)   MM9 gap (min/median/max)")
    for entry in sorted(report["structures"], key=lambda e: -e["faces"])[:20]:
        print(f"{entry['name']:24s} {entry['faces']:6d}   {str(entry['native_gap']):28s} {entry['mm9_gap']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
