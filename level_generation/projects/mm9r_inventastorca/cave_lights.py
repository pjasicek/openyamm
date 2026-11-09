#!/usr/bin/env python3
"""
Bake-only lights for the cave shaft (map-local; README "Baked lighting"). MM9 lights the shaft from DirLights and its
lightmaps read a lit purple-grey; the map's own lights leave it nearly black. These lights stand on the shaft's axis,
one per height band, coloured from MM9's own DAT lightmaps of the cave polygons in that band (area-weighted mean,
normalised to the brightest channel) and as strong as the band's MM9 brightness relative to the brightest band, times
STRENGTH (calibrated against the tour views l07/l08).

    python3 level_generation/projects/mm9r_inventastorca/cave_lights.py      # -> work/cave_lights.json (native)
"""

from __future__ import annotations

import json
import pickle
import sys
from pathlib import Path

import numpy as np

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
from dungeon.lighting import LIGHT_ALPHA  # noqa: E402
from dungeon.source import SCALE, Project, Source  # noqa: E402

CAVE = (np.array([-450.0, -640.0, -500.0]), np.array([50.0, 616.0, 0.0]))     # LT box (x, y, z), hue_zones.py
BAND_LT = 160.0                     # one light per this much shaft height
RADIUS_LT = 420.0
STRENGTH = 2.05                     # calibration: the cave zone's lightmap mean to MM9's (README "Brightness and hue")
BLUE = 1.25                         # the bake's warm fill dilutes the purple: B/R 0.78 against MM9's 0.84
OUT = PROJECT / "work/cave_lights.json"


def main() -> int:
    project = Project.load(PROJECT, install=False)
    source = Source(project)
    model = source.models["PhysicsBSP"]
    low, high = CAVE
    bands = {}
    for poly in model.polies:
        pixels = getattr(poly, "lightmap_pixels_bgra", None)
        centre = np.array(poly.center, float)
        if not pixels or not ((centre >= low).all() and (centre <= high).all()):
            continue
        value = np.array(pixels, np.int64)
        texels = np.stack([(value >> 16) & 255, (value >> 8) & 255, value & 255], 1).astype(float) / 255
        band = int((centre[1] - low[1]) // BAND_LT)
        bands.setdefault(band, []).append(texels)
    # the shaft's air at each band's middle height: the centroid of the air voxels in the cave box (work/cutlab.pkl,
    # tools/cutlab.py's cache of the converter's voxels)
    grid, air, _ = pickle.loads((PROJECT / "work/cutlab.pkl").read_bytes())
    lo_cell, hi_cell = grid.index(low[None])[0], grid.index(high[None])[0]
    means = {band: np.concatenate(t).mean(0) for band, t in bands.items()}
    top = max(float(m.max()) for m in means.values())
    lights = []
    for band in sorted(means):
        y = low[1] + (band + 0.5) * BAND_LT
        j = grid.index(np.array([[0.0, y, 0.0]]))[0][1]
        cells = np.argwhere(air[lo_cell[0]:hi_cell[0] + 1, j, lo_cell[2]:hi_cell[2] + 1])
        if not len(cells):
            continue
        cx, cz = cells.mean(0)
        centre = grid.centre(np.array([[lo_cell[0] + cx, j, lo_cell[2] + cz]]))[0]
        mean = means[band]
        tinted = mean * np.array([1.0, 1.0, BLUE])
        colour = [int(round(255 * c / tinted.max())) for c in tinted]
        lights.append({"name": f"cave:band{band}", "position": [int(round(v)) for v in project.native(centre)],
                       "radius": int(round(RADIUS_LT * SCALE)), "color": colour,
                       "alpha": round(LIGHT_ALPHA * STRENGTH * float(mean.max()) / top, 4),
                       "mm9_lightmap_mean": [round(float(v), 3) for v in mean]})
    OUT.write_text(json.dumps(lights, indent=1) + "\n")
    for light in lights:
        print(light["name"], light["position"], light["color"], light["alpha"], light["mm9_lightmap_mean"])
    print("WROTE", OUT, len(lights))
    return 0


if __name__ == "__main__":
    sys.exit(main())
