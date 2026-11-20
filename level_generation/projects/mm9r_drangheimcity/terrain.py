"""
Drangheim City's terrain (Terrain0: the hills, cliffs and lawns the city stands on, a height field of 1 637
up-facing polygons) and the air under it.

MM9's sky box is one L-shaped box from LT y -304 to 1 456; the terrain does not reach its walls, and north-east and west
of the city walls it does not exist at all (a void down to the box's sky floor). The air flood therefore runs from the
open air over the walls down into the void and under the whole terrain (5.7 M voxels, a third of all air): one room with
the streets, its street cuts reaching under the ground, walls below the ground kept as faces. `prune_underground` takes
every air voxel whose centre lies under the terrain surface of its column out of the air before the rooms are
labelled (Hooks.extra_portals runs after the flood), keeps only the air components that still hold a seed (the
pockets under paved streets and building floors, which reached the underground only, go too) and reports any seed object
that stood under the terrain. A voxel counts as under the surface when its centre lies 1 LT or more below it (a margin
of 1.5 voxels / normal y, tried in v02, kept a thin sheet of air under the flat ground that took the walls' feet into
rooms of their own: white seams at every wall's base).
"""

from __future__ import annotations

import numpy as np
from scipy import ndimage

from dungeon.geometry import SIX


def terrain_heights(polygons: list, grid) -> tuple[np.ndarray, np.ndarray]:
    """The terrain's surface height (LT y) at each grid column's centre, NaN where no terrain polygon covers it, and the
    normal y of the polygon giving it."""
    nx, _, nz = grid.shape
    size, origin = grid.size, grid.origin
    heights = np.full((nx, nz), np.nan)
    slopes = np.ones((nx, nz))
    xs = origin[0] + (np.arange(nx) + 0.5) * size
    zs = origin[2] + (np.arange(nz) + 0.5) * size
    for polygon in polygons:
        pts = polygon.points
        lo, hi = pts.min(0), pts.max(0)
        ix = np.flatnonzero((xs >= lo[0]) & (xs <= hi[0]))
        iz = np.flatnonzero((zs >= lo[2]) & (zs <= hi[2]))
        if not len(ix) or not len(iz):
            continue
        gx, gz = np.meshgrid(xs[ix], zs[iz], indexing="ij")
        inside = np.zeros(gx.shape, bool)
        count = len(pts)
        for i in range(count):
            x1, z1 = pts[i, 0], pts[i, 2]
            x2, z2 = pts[(i + 1) % count, 0], pts[(i + 1) % count, 2]
            if z1 == z2:
                continue
            crosses = (z1 > gz) != (z2 > gz)
            at = x1 + (gz - z1) / (z2 - z1) * (x2 - x1)
            inside ^= crosses & (gx < at)
        if not inside.any():
            continue
        n = polygon.normal
        y = (n @ pts[0] - n[0] * gx - n[2] * gz) / n[1]
        block = heights[np.ix_(ix, iz)]
        take = inside & (np.isnan(block) | (y > block))
        block[take] = y[take]
        heights[np.ix_(ix, iz)] = block
        slope = slopes[np.ix_(ix, iz)]
        slope[take] = max(float(n[1]), 0.05)
        slopes[np.ix_(ix, iz)] = slope
    return heights, slopes


def prune_underground(build, terrain_model: str = "Terrain0") -> dict:
    """Air voxels under the terrain surface out of build.air (in place). Returns the report."""
    grid = build.grid
    heights, slopes = terrain_heights(build.source.polygons(terrain_model), grid)
    margin = 1.0
    ys = build.grid.origin[1] + (np.arange(grid.shape[1]) + 0.5) * grid.size
    under = ys[None, :, None] < (heights - margin)[:, None, :]      # NaN compares False: no terrain, no pruning
    pruned = build.air & under
    count = int(pruned.sum())
    build.air &= ~under
    # The seeds build_voxels used (rooms.build_voxels): keep the air components that hold one.
    classes = build.project.seed_classes | build.project.monster_classes
    excluded = {name.lower() for name in (build.project.overrides.get("seed_exclude") or [])}
    seeds, lost = [], []
    for o in build.source.objects:
        if o["class"] not in classes or o["name"].lower() in excluded:
            continue
        p = np.asarray(o["properties"]["Pos"], float)
        seeds.append(p)
        if pruned[tuple(grid.index(p[None])[0])]:
            lost.append({"name": o["name"], "class": o["class"], "pos": p.round().tolist()})
    seeds += [np.asarray(s, float) for s in build.hooks.extra_seeds(build)]
    labels, _ = ndimage.label(build.air, structure=SIX)
    cells = grid.index(np.array(seeds))
    keep = sorted(set(int(v) for v in labels[cells[:, 0], cells[:, 1], cells[:, 2]]) - {0})
    kept = np.isin(labels, keep)
    unseeded = int((build.air & ~kept).sum())
    build.air &= kept
    report = {"air_voxels_pruned": count, "unseeded_pockets_removed": unseeded,
              "terrain_columns": int(np.isfinite(heights).sum()), "seeds_under_terrain": lost}
    build.stats["underground_air_pruned"] = count
    build.stats["underground_pockets_removed"] = unseeded
    return report
