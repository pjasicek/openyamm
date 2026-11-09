#!/usr/bin/env python3
"""MM9's own lightmap colours per zone of CHASMOFTHEDEAD.dat (the hue reference: the old bmodel_world map draws MM9's light
colours neutral, DUNGEON_PLAYBOOK "Light colours"). Mean RGB (0-255) of the lightmap texels of the polygons in each box."""
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools/mm9_import_discovery"))
from transcode_mm9_dat_to_odm import read_dat_world  # noqa: E402

ZONES = {"entry_tomb": (-5850, 440, 9240, -4640, 800, 10240), "pillar_hall": (-6080, 600, 7600, -4220, 800, 8900),
         "hall2": (-3800, 100, 4640, -2900, 320, 5200), "canyon_floor": (0, -1600, 1800, 3000, -1200, 5900),
         "canyon_rim": (0, -300, 1800, 3000, 770, 5900), "pool_hall": (3000, -1900, 4500, 3800, -1500, 6400),
         "octagon": (3650, -2100, 4450, 4550, -1800, 5550), "mummy_hall": (-4300, -1100, 700, -3100, -860, 2100),
         "south_corridor": (900, -1750, -4000, 1100, -1500, -500), "crypt": (350, -2200, -7600, 1700, -1900, -6200)}


def main() -> int:
    world = read_dat_world(ROOT / "mm9/extracted/WORLDS/WORLDS/CHASMOFTHEDEAD.dat")
    model = next(m for m in world.world_models if m.name == "PhysicsBSP")
    for name, box in ZONES.items():
        low, high = np.array(box[:3], float), np.array(box[3:], float)
        texels = []
        for poly in model.polies:
            pixels = getattr(poly, "lightmap_pixels_bgra", None)
            if not pixels:
                continue
            centre = np.array(poly.center, float)
            if (centre >= low).all() and (centre <= high).all():
                value = np.array(pixels, np.int64)
                texels.append(np.stack([value & 255, (value >> 8) & 255, (value >> 16) & 255], 1).astype(float))
        if texels:
            bgr = np.concatenate(texels).mean(0)
            print(f"{name:16s} r {bgr[2]:6.1f} g {bgr[1]:6.1f} b {bgr[0]:6.1f}  ({len(texels)} polys)")
        else:
            print(name, "no lightmapped polygons")
    return 0


if __name__ == "__main__":
    sys.exit(main())
