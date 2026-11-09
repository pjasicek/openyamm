#!/usr/bin/env python3
"""Lining poke by geometry (after the reductions' lining_gate.py): every lining vertex (line.py role 'twin': the band twins and
the rim strips' inner corners; 'centre': cap centres) against the outer cloth of its own piece(s), posed, every clip at FPS:
signed distance to the nearest original triangle of those pieces (closest point over the 32 nearest by centroid; PeasantM1: 8 missed the own face under the large shoulder triangles and read the collar fold 8.5 mm away, sign along that
face's outward normal; at rest the twins lie 0.5-3 mm inside). A vertex more than TOL outside is the dark lining showing through
the cloth. Reports per clip and op the largest outward distance, frames with a vertex out and the most vertices out at once,
plus the installed cloth's own self-crossing for comparison is not measured (same clips, same outer vertices).
Usage: [CLIPS=a,b] lining_gate.py <lined glb> <lining npz> <out json> [fps 10] [tol m 0.0005]"""
import json, sys
from collections import defaultdict
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor')); sys.path.insert(0, str(HERE.parent / 'claude_shared'))
from glb_pose import Glb, Model  # noqa: E402
from detached_parts_audit import closest_on_triangles  # noqa: E402
glb, linz, out = sys.argv[1:4]; FPS = float(sys.argv[4]) if len(sys.argv) > 4 else 10.0
TOL = float(sys.argv[5]) if len(sys.argv) > 5 else 0.0005
m = Model(Glb(glb)); z = np.load(linz)
names = [m.glb.json['materials'][p['material']]['name'] for p in m.glb.json['meshes'][m.primitives[0]['node'].get('mesh', 0)]['primitives']] \
    if False else None
doc = m.glb.json
nd = next(n for n in doc['nodes'] if n.get('name') == 'PeasantM1' and 'mesh' in n)
pnames = [doc['materials'][p['material']]['name'] for p in doc['meshes'][nd['mesh']]['primitives']]
groups = []          # (prim k, op, vertex ids, outer triangles)
for k, name in enumerate(pnames):
    tags = z[f'vtag_{name}']; n0 = int(z[f'nvert_{name}']); piece = z[f'piece_{name}']
    T = m.primitives[k]['triangles']; T0 = T[(T < n0).all(1)]
    byop = defaultdict(list)
    for i, t in enumerate(tags):
        op, role, pcs = t.split('|')
        if role in ('twin', 'centre') and pcs:
            byop[(op, pcs)].append(n0 + i)
    for (op, pcs), vs in byop.items():
        ps = [int(x) for x in pcs.split(',')]
        tri = T0[np.isin(piece[T0[:, 0]], ps)]
        if not len(tri):          # a cap placed in another primitive (PeasantM1's neck cap on the jacket's paint): no own cloth here
            print('skip', op, 'no outer faces of its pieces in', name); continue
        groups.append((k, op, np.array(vs), tri))
print('groups', [(g[1], len(g[2]), len(g[3])) for g in groups])


def signed(X, vs, tri):
    tr = X[tri]; c = tr.mean(1); n = np.cross(tr[:, 1] - tr[:, 0], tr[:, 2] - tr[:, 0])
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    Q = X[vs]; _, ids = cKDTree(c).query(Q, k=min(32, len(c))); best = np.full(len(Q), 1e9); sd = np.zeros(len(Q))
    for kk in range(ids.shape[1]):
        i = ids[:, kk]; q, _ = closest_on_triangles(Q, tr[i, 0], tr[i, 1], tr[i, 2]); d = np.linalg.norm(q - Q, axis=1); u = d < best
        best[u] = d[u]; sd[u] = ((Q - q) * n[i])[u].sum(1)
    return sd


rest = m.skinned_positions(m.world({}))
rep = {'rest_max_out_mm': {g[1]: round(float(signed(rest[g[0]][0], g[2], g[3]).max()) * 1000, 2) for g in groups}, 'clips': {}}
print('rest max outward mm', rep['rest_max_out_mm'])
import os
for clip in [c for c in m.clips if not os.environ.get('CLIPS') or c in os.environ['CLIPS'].split(',')]:
    t1 = m.clip_times(clip)[-1]; r = rep['clips'][clip] = {}
    for t in np.append(np.arange(0, t1, 1 / FPS), t1):
        posed = m.skinned_positions(m.world(m.sample(clip, t)))
        for k, op, vs, tri in groups:
            sd = signed(posed[k][0], vs, tri); e = r.setdefault(op, {'max_out_mm': -99.0, 'frames_out': 0, 'max_verts_out': 0})
            e['max_out_mm'] = max(e['max_out_mm'], round(float(sd.max()) * 1000, 2)); nout = int((sd > TOL).sum())
            e['frames_out'] += nout > 0; e['max_verts_out'] = max(e['max_verts_out'], nout)
    print(f'{clip:12s}', ', '.join(f'{op} {e["max_out_mm"]:.1f}mm/{e["frames_out"]}f/{e["max_verts_out"]}v' for op, e in r.items()), flush=True)
Path(out).write_text(json.dumps(rep, indent=1))
