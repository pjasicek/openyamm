#!/usr/bin/env python3
"""Linings and the waist backstop tube through the outer cloth (Peasant boy reduction check, 2026-11-05; after the Dwarf boy's
lining_gate.py). Body primitive only (the head primitive has no linings). Outer surface = the body faces with painted UVs (non-zero
UV area: cloth, belt, boots, Meshy's own inner layer); every one-texel face (linings, rim strips, the tube) is left out of it.
Points checked per clip at FPS, signed distance to the posed outer surface (closest point on the 8 nearest faces by centroid,
sign along that face's normal: at rest a lining lies inside):
  lining  vertices of the installed paired lining faces (work/twins.npz), found in the candidate by exact position;
  tube    the tube faces' corners, edge midpoints and centroids (a coarser tube's chords are what moved), against the posed
          INSTALLED tube (outward faces): a reduced tube that stays inside the installed one cannot reach the cloth where the
          installed tube did not (the distance to the cloth is meaningless for the tube: it sits inside several layers).
Reports per set and clip the largest outward distance and the most points more than TOL outside (a dark speck through the cloth).
Usage: lining_gate.py <glb> <out json> [fps] [tol m]"""
import json
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor')); sys.path.insert(0, str(HERE.parent / 'claude_shared'))
from glb_pose import Glb, Model  # noqa: E402
from detached_parts_audit import closest_on_triangles  # noqa: E402
glb, out = sys.argv[1:3]; FPS = float(sys.argv[3]) if len(sys.argv) > 3 else 10.0
TOL = float(sys.argv[4]) if len(sys.argv) > 4 else 0.0005
m = Model(Glb(glb)); src = Model(Glb(str(HERE / 'before' / 'mm9_peasantboy.glb')))
tw = np.load(HERE / 'work' / 'twins.npz'); sets = np.load(HERE / 'work' / 'glb_sets_a.npz')
sp = src.primitives[0]; cp = m.primitives[0]; ns = len(sp['triangles'])
lin = tw['lining'][:ns]; tube = sets['part'][:ns] == 6
T = cp['triangles']; U = cp['texcoords'] if 'texcoords' in cp else None
if U is None:
    import bglbio
    doc, b = bglbio.read(glb); nd = next(n for n in doc['nodes'] if n.get('name') == 'PeasantBoy' and 'mesh' in n)
    U = bglbio.prims(doc, b, nd['mesh'])[0]['TEXCOORD_0'].astype(np.float64)
ua = np.abs((U[T[:, 1], 0] - U[T[:, 0], 0]) * (U[T[:, 2], 1] - U[T[:, 0], 1]) - (U[T[:, 2], 0] - U[T[:, 0], 0]) * (U[T[:, 1], 1] - U[T[:, 0], 1]))
outer = T[ua > 1e-10]
kd = cKDTree(cp['positions'])
lv_src = np.unique(sp['triangles'][lin].ravel()); d, j = kd.query(sp['positions'][lv_src]); linv = np.unique(j[d < 1e-7])
tv_src = np.unique(sp['triangles'][tube].ravel()); d, j = kd.query(sp['positions'][tv_src])
istube = np.zeros(len(cp['positions']), bool); istube[j[d < 1e-7]] = True
tubeT = T[istube[T].all(1)]
print('outer faces', len(outer), 'lining verts', len(linv), 'tube faces', len(tubeT))
W = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1], [.5, .5, 0], [0, .5, .5], [.5, 0, .5], [1 / 3, 1 / 3, 1 / 3]])


def signed(X, Q, F=None):
    tr = X[outer if F is None else F]; c = tr.mean(1); n = np.cross(tr[:, 1] - tr[:, 0], tr[:, 2] - tr[:, 0])
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    _, ids = cKDTree(c).query(Q, k=8); best = np.full(len(Q), 1e9); sd = np.zeros(len(Q))
    for k in range(8):
        i = ids[:, k]; q, _ = closest_on_triangles(Q, tr[i, 0], tr[i, 1], tr[i, 2]); dd = np.linalg.norm(q - Q, axis=1); u = dd < best
        best[u] = dd[u]; sd[u] = ((Q - q) * n[i])[u].sum(1)
    return sd


rep = {}
for clip in ['bind'] + list(m.clips):
    times = [0.0] if clip == 'bind' else np.append(np.arange(0, m.clip_times(clip)[-1], 1 / FPS), m.clip_times(clip)[-1])
    res = {'lining': [-1.0, 0, 0], 'tube': [-1.0, 0, 0]}
    srcT = sp['triangles'][tube]
    for t in times:
        X = cp['positions'].astype(np.float64) if clip == 'bind' else m.skinned_positions(m.world(m.sample(clip, t)))[0][0]
        XS = sp['positions'].astype(np.float64) if clip == 'bind' else src.skinned_positions(src.world(src.sample(clip, t)))[0][0]
        for key, Q in (('lining', X[linv]), ('tube', np.einsum('sk,fkc->fsc', W, X[tubeT]).reshape(-1, 3))):
            sd = signed(X, Q) if key == 'lining' else signed(XS, Q, srcT); r = res[key]
            r[0] = max(r[0], float(sd.max())); c = int((sd > TOL).sum()); r[1] = max(r[1], c); r[2] += c > 0
    rep[clip] = {k: dict(max_out_mm=round(v[0] * 1000, 2), max_points_out=v[1], frames_out=v[2]) for k, v in res.items()}
    print(f'{clip:12s} ' + ' | '.join(f'{k}: max out {v[0] * 1000:6.2f} mm, most points > {TOL * 1000:.1f} mm {v[1]:4d}, frames {v[2]:3d}'
                                     for k, v in res.items()), flush=True)
Path(out).write_text(json.dumps(rep, indent=1))
