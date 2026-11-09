#!/usr/bin/env python3
"""The 117 translucent blue orbs over the invisible candles (DAT WorldObjects, Alpha 0.4, not Solid, 84 polygons,
Sprites/Water/water123.spr), listed by the map agent in ../../projects/mm9r_1000terrors/work/orb_models.json: reads
their polygons from the DAT (the map converter's reader: read_dat_world, the v66 second ring of geometry.poly_ring,
MM9's surface mapping in texels / 128), checks that all share one shape (vertices about the bounding-box centre), and
writes work/waterorb/orb.json, work/waterorb/points_native.npz (each orb's DAT points, native), (one orb's triangles in LT about its box centre, UVs, texture size), and
work/waterorb/centres.json (name -> box centre in LT and native, alpha). Usage: waterorb_source.py"""
import json
import sys
from pathlib import Path

import numpy as np

import props_table

REPO = props_table.REPO
sys.path.insert(0, str(REPO / 'level_generation/projects/mm9r_common'))
from dungeon.geometry import poly_ring  # noqa: E402
from dungeon.source import read_dat_world  # noqa: E402

DAT = REPO / 'mm9/extracted/WORLDS/WORLDS/1000TERRORS.dat'
NAMES = json.loads((props_table.PROJECT / 'work/orb_models.json').read_text())
TEXTURE = 128.0       # water123.spr frames are 128 x 128 (material aliases)


def polygons(model):
    out = []
    for poly in model.polies:
        ring = poly_ring(poly)
        if len(ring) < 3:
            continue
        surface = model.surfaces[poly.surface_index]
        points = np.array([model.points[i] for i in ring], float)
        rel = points - np.array(surface.uv_origin)
        uv = np.stack([rel @ np.array(surface.uv_u), rel @ np.array(surface.uv_v)], 1) / TEXTURE
        out.append((points, uv, model.textures[surface.texture_index], surface.flags))
    return out


def main():
    world = read_dat_world(DAT)
    models = {m.name: m for m in world.world_models}
    alpha = {}
    for o in world.objects:
        props = {p.name: p.value for p in o.properties}
        if str(props.get('Name')) in NAMES:
            alpha[str(props['Name'])] = float(props.get('Alpha', 1.0))
    shapes, centres, textures, native = {}, {}, set(), {}
    for name in NAMES:
        polys = polygons(models[name])
        pts = np.concatenate([p for p, _, _, _ in polys])
        lo, hi = pts.min(0), pts.max(0)
        c = (lo + hi) / 2
        native[name] = np.stack([pts[:, 0], pts[:, 2], pts[:, 1]], 1) * 2.56
        textures |= {t for _, _, t, _ in polys}
        key = tuple(np.round(np.sort(np.round(pts - c, 1), axis=0).ravel(), 0))
        shapes.setdefault(key, []).append(name)
        centres[name] = {'centre_lt': c.round(3).tolist(), 'size_lt': (hi - lo).round(2).tolist(),
                         'native': [round(c[0] * 2.56, 1), round(c[2] * 2.56, 1), round(c[1] * 2.56, 1)],
                         'polygons': len(polys), 'alpha': alpha.get(name)}
    print(len(NAMES), 'orbs,', len(shapes), 'distinct shapes', [len(v) for v in shapes.values()], 'textures', textures)
    print('sizes', sorted({tuple(v['size_lt']) for v in centres.values()}), 'alpha', sorted({v['alpha'] for v in
                                                                                             centres.values()}))
    first = NAMES[0]
    polys = polygons(models[first])
    c = np.array(centres[first]['centre_lt'])
    tris = []
    for points, uv, _, _ in polys:
        for k in range(1, len(points) - 1):
            tris.append({'p': (points[[0, k, k + 1]] - c).round(4).tolist(), 'uv': uv[[0, k, k + 1]].round(5).tolist()})
    out = props_table.HERE / 'work/waterorb'
    out.mkdir(exist_ok=True)
    (out / 'orb.json').write_text(json.dumps({'source': first, 'triangles': tris}, indent=0))
    (out / 'centres.json').write_text(json.dumps(centres, indent=1))
    np.savez_compressed(out / 'points_native.npz', **native)
    print('wrote', len(tris), 'triangles from', first)


if __name__ == '__main__':
    main()
