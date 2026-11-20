#!/usr/bin/env python3
"""The desert's four mirrors (DAT WorldObjects Mirror0-3, PassageMirror.scr; MM9 turns each 10 degrees a click) as one
decoration model, so the map can turn them (evt.AimDecoration). Reads their polygons from the DAT (the map converter's
reader and ring, MM9's surface mapping in texels / the texture's size), checks that all four share one shape about
their box centres, and writes work/mirror/mirror.json (Mirror0's triangles in LT about its box centre, in front-facing
order, UVs, material: `mirror` the rusty frame, `mirror_glass` the Icebolt glass) and the four placements (native
position of the model's base centre, yaw 0) in ../../projects/mm9r_darkpassageway/mirrors.json, with the worst distance
of each DAT point to the placed model.

The DAT keeps a WorldObject's brush in world space: its Rotation (yaw 90 for Mirror0 and Mirror2, 270 for Mirror1 and
Mirror3) does not turn the geometry, and the four brushes are the same shape the same way round (the glass faces world
-y). So every placement has facing 0. The map's beams leave along the object's facing (its Rotation, convert.py),
not along the glass.
The pivot is the box centre: MM9 turns a mirror about its Pos, which is 1 LT (2.6 units) off it.
Usage: mirror_source.py"""
import json
import sys

import numpy as np

import props_table

REPO = props_table.REPO
sys.path.insert(0, str(REPO / 'level_generation/projects/mm9r_common'))
from dungeon.geometry import newell, poly_ring  # noqa: E402
from dungeon.source import read_dat_world  # noqa: E402

DAT = REPO / 'mm9/extracted/WORLDS/WORLDS/DARKPASSAGEWAY.dat'
NAMES = ['Mirror0', 'Mirror1', 'Mirror2', 'Mirror3']
TEXTURE = 128.0            # refinerysolidrusta.dtx and Icebolt.dtx are 128 x 128
OUT = props_table.HERE / 'work/mirror'
PLACEMENTS = REPO / 'level_generation/projects/mm9r_darkpassageway/mirrors.json'


def native(points_lt):
    return np.stack([points_lt[:, 0], points_lt[:, 2], points_lt[:, 1]], 1) * 2.56


def polygons(model):
    """[(points LT, uv, material)] in the DAT ring order (its Newell vector is the polygon's front)."""
    out = []
    for poly in model.polies:
        ring = poly_ring(poly)
        if len(ring) < 3:
            continue
        surface = model.surfaces[poly.surface_index]
        texture = model.textures[surface.texture_index].lower()
        points = np.array([model.points[i] for i in ring], float)
        if np.linalg.norm(newell(points)) < 1e-6:
            continue
        rel = points - np.array(surface.uv_origin)
        uv = np.stack([rel @ np.array(surface.uv_u), rel @ np.array(surface.uv_v)], 1) / TEXTURE
        material = 'mirror_glass' if 'icebolt' in texture else 'mirror'
        out.append((points, uv, material))
    return out


def worst(a, b):
    """The largest distance from a point of `a` to the nearest point of `b`."""
    return float(np.linalg.norm(a[:, None] - b[None], axis=2).min(1).max())


def main():
    world = read_dat_world(DAT)
    models = {m.name: m for m in world.world_models}
    params = {}
    for o in world.objects:
        values = {p.name: p.value for p in o.properties}
        if str(values.get('Name')) in NAMES:
            params[str(values['Name'])] = values.get('ScriptParams')
    points, centre = {}, {}
    for name in NAMES:
        pts = native(np.concatenate([p for p, _, _ in polygons(models[name])]))
        points[name] = pts
        centre[name] = (pts.min(0) + pts.max(0)) / 2
    shape = points[NAMES[0]] - centre[NAMES[0]]
    for name in NAMES[1:]:
        other = points[name] - centre[name]
        gap = max(worst(shape, other), worst(other, shape))
        print(f'{name}: worst distance to {NAMES[0]}\'s shape {gap:.2f} units')
        if gap > 3.0:
            raise SystemExit(f'{name} is not {NAMES[0]}\'s shape')
    # Mirror0's triangles in LT about its box centre (the frame build_mirror.py exports)
    first = NAMES[0]
    centre_lt = np.array([centre[first][0], centre[first][2], centre[first][1]]) / 2.56
    triangles = []
    for ring, uv, material in polygons(models[first]):
        lt = ring - centre_lt
        for k in range(1, len(ring) - 1):
            idx = [0, k, k + 1]
            triangles.append({'p': lt[idx].round(4).tolist(), 'uv': uv[idx].round(5).tolist(),
                              'material': material})
    lo, hi = shape.min(0), shape.max(0)
    base = np.array([(lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, lo[2]])
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'mirror.json').write_text(json.dumps({'source': first, 'triangles': triangles,
                                                 'height_units': round(float(hi[2] - lo[2]), 2)}, indent=0))
    entries = []
    for name in NAMES:
        position = centre[name] + base
        fit = worst(points[name], shape - base + position)
        entries.append({'source_name': name, 'decoration': 'mm9_mirror', 'x': round(float(position[0]), 1),
                        'y': round(float(position[1]), 1), 'z': round(float(position[2]), 1), 'yaw_degrees': 0.0,
                        'fit_worst_units': round(fit, 2), 'script_params': params[name]})
        print(f'{name}: base {position.round(1).tolist()}, worst fit {fit:.2f}')
    PLACEMENTS.write_text(json.dumps(entries, indent=1) + '\n')
    print('wrote', len(triangles), 'triangles, height', round(float(hi[2] - lo[2]), 1), 'units')


if __name__ == '__main__':
    main()
