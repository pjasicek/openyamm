#!/usr/bin/env python3
"""
Sturmford, MM9 rework: MM9's STURMFORD.dat (a 51 200-unit wilderness region) as a native BLV open to the sky, the
large-region check of converting MM9's outdoor maps as BLVs (../mm9r_common/outdoor_blv.py; the pilot:
../mm9r_isleofashes_blv/). Installs into the outdoor pilots' own review root, output/mm9_rework/isleofashes_blv_root.

    python3 level_generation/projects/mm9r_sturmford_blv/convert.py            # build, compile, install
    python3 level_generation/projects/mm9r_sturmford_blv/convert.py --plan     # rooms only: work/rooms*.png

**The pathing check** (overrides.yml `outdoor: {test_population}`, placed by outdoor_blv.py): MM9 places 56 monsters
here (22 dragonflies, 16 field thralls, mites, basilisks, spores); MM6-MM8 outdoor maps carry 100-220.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
import review_root  # noqa: E402

review_root.ASSETS = review_root.REVIEW / "isleofashes_blv_root"
review_root.OWNED = review_root.REVIEW / "isleofashes_blv_owned.txt"

import dungeon  # noqa: E402
import outdoor_blv  # noqa: E402
import terrain_blend  # noqa: E402


import numpy as np  # noqa: E402
from mm9_units import MM9_TO_OPENYAMM_COORDINATE_SCALE as SCALE  # noqa: E402

# Anskram Keep's drawbridge chains (DestructableBrush0/1): MM9's RayHit boxes are 21 x 10 (native) across, a sliver
# under the gatehouse chamber's ceiling that a blow hits only within about 1.5 degrees of aim. Deviation (the user,
# 2026-11-08): the invisible hit boxes are grown to CHAIN_HIT_BOX across (the visible chain is unchanged), so a blow
# from the chamber floor reaches them as MM9 let it, and missiles still do.
CHAINS = ("DestructableBrush0", "DestructableBrush1")
CHAIN_HIT_BOX = 96                 # native units, the box's height and depth (its length is MM9's)


def grow_chain_hit_boxes(polygons: list) -> int:
    grown = 0
    for name in CHAINS:
        box = [p for p in polygons if p.model == name and p.role == "invisible"]
        if not box:
            continue
        points = np.concatenate([p.points for p in box])
        low, high = points.min(0), points.max(0)
        centre, half = (low + high) / 2, CHAIN_HIT_BOX / 2 / SCALE
        for polygon in box:
            for axis in range(3):
                if high[axis] - low[axis] < 2 * half:       # the thin axes (LT y is up, LT z is native y)
                    side = np.sign(polygon.points[:, axis] - centre[axis])
                    polygon.points[:, axis] = centre[axis] + side * half
        grown += 1
    return grown


class Sturmford(outdoor_blv.OutdoorBlvHooks):
    generator = "mm9r_sturmford_blv"

    def edit_polygons(self, build, polygons: list) -> list:
        polygons = super().edit_polygons(build, polygons)
        build.stats["chain_hit_boxes_grown"] = grow_chain_hit_boxes(polygons)
        return polygons


if __name__ == "__main__":
    if not review_root.ASSETS.exists():
        sys.exit(f"{review_root.ASSETS} is missing: create it first (../mm9r_isleofashes_blv/README.md)")
    code = dungeon.main(PROJECT, Sturmford(PROJECT))
    if code == 0 and not {"--plan", "--scratch"} & set(sys.argv):
        project = dungeon.source.Project.load(PROJECT)
        print(f"boat arrivals rewritten: {outdoor_blv.rewrite_transport(project)}")
        print(terrain_blend.install(PROJECT))
    sys.exit(code)
