#!/usr/bin/env python3
"""Numbers per colour LOD (0-3) of a PeasantDF GLB: triangles, rest height, and per clip (every 30 fps frame) the lowest
point and the top, i.e. floor contact and height drift against LOD0. Usage: lod_numbers.py <glb> -> prints a table"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model  # noqa: E402
g = Glb(sys.argv[1]); doc = g.json
node = next(i for i, n in enumerate(doc['nodes']) if n.get('name') == 'PeasantDF' and 'mesh' in n)
lods = [doc['nodes'][node]['mesh']] + doc['meshes'][doc['nodes'][node]['mesh']]['extras']['openyamm_lods']
res = {}
for L, mi in enumerate(lods):
    doc['nodes'][node]['mesh'] = mi; nm = doc['meshes'][mi].get('name', ''); doc['meshes'][mi]['name'] = 'X'
    m = Model(g); doc['meshes'][mi]['name'] = nm
    tris = sum(len(p['triangles']) for p in m.primitives)
    rest = np.vstack([p['positions'] for p in m.primitives])
    row = {'tris': tris, 'height': rest[:, 1].max() - rest[:, 1].min()}
    for clip in m.clips:
        ts = m.clip_times(clip); t1 = ts[-1]; lo, hi = 9, -9
        for t in np.append(np.arange(0, t1, 1 / 30), t1):
            P = np.vstack([p for p, _ in m.skinned_positions(m.world(m.sample(clip, t)))])
            lo = min(lo, P[:, 1].min()); hi = max(hi, P[:, 1].max())
        row[clip] = (lo, hi)
    res[L] = row
doc['nodes'][node]['mesh'] = lods[0]
print('LOD tris  height  ' + '  '.join(f'{c}(low/top cm)' for c in res[0] if c not in ('tris', 'height')))
for L, r in res.items():
    print(f'{L} {r["tris"]:6d} {r["height"]:.3f}  ' + '  '.join(f'{c}:{v[0] * 100:+.2f}/{v[1] * 100:.1f}' for c, v in r.items() if c not in ('tris', 'height')))
for L in (1, 2, 3):
    d = [(c, (res[L][c][0] - res[0][c][0]) * 100) for c in res[0] if c not in ('tris', 'height')]
    print(f'LOD{L} lowest point minus LOD0, cm: worst {max(d, key=lambda x: abs(x[1]))[0]} {max(d, key=lambda x: abs(x[1]))[1]:+.2f}')
