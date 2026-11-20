#!/usr/bin/env python3
"""Fix pass, step 2: pick each group's step from work/fix/sweep.json (mp_pieces.py) and assemble the candidate.
A step is allowed when its rest error stays within MAXMM / MEANMM (two-way max / mean, mm), a closed piece keeps VOL_MIN of its
volume and no rest gap to a neighbouring piece grows by more than GAPMM; the group takes the allowed step with the fewest faces
(a group with none stays exact). Floors: hands >= HAND_MIN (0.6), cranium dome and ropes (groups 45, 61) >= 0.7.
Writes work/mp_r<TAG>.npz (per primitive triangles into the installed GLB's LOD0 vertices, linings and kept faces as installed)
and work/mesh_r<TAG>.npz (the same faces, linings excluded, on work/mesh_in.npz with src_index) for reduce_ladder.py.
Usage: mp_plan.py <TAG> <MAXMM> <MEANMM>   (env GAPMM 1.0, VOL_MIN 0.8, HAND_MIN 0.6, SFX: the sweep's suffix, KEEP_GROUPS: groups kept exactly)"""
import json, os, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import bglbio as glbio  # noqa: E402
tag, MAXMM, MEANMM = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
GAPMM = float(os.environ.get('GAPMM', '1.0')); VOL_MIN = float(os.environ.get('VOL_MIN', '0.8'))
HAND_MIN = float(os.environ.get('HAND_MIN', '0.6')); FLOOR07 = {45, 61}
KEEP_GROUPS = {int(x) for x in os.environ.get('KEEP_GROUPS', '').split(',') if x}
SFX = os.environ.get('SFX', '')
SW = json.loads((HERE / 'work' / 'fix' / f'sweep{SFX}.json').read_text()); SN = np.load(HERE / 'work' / 'fix' / f'sweep_T{SFX}.npz')
sets = np.load(HERE / 'work' / 'fix' / 'glb_sets.npz'); group, prim_of, lining = sets['group'], sets['prim'], sets['lining']
doc, binary = glbio.read(HERE / 'before' / 'mm9_skeleton.glb')
node = next(n for n in doc['nodes'] if n.get('name') == 'Skel' and 'mesh' in n)
prims = glbio.prims(doc, binary, node['mesh'])
off = np.cumsum([0] + [len(p['T']) for p in prims])
newT = {i: [p['T'][group[off[i]:off[i + 1]] == 0]] for i, p in enumerate(prims)}
cats, pick = {}, {}
for gs, e in SW.items():
    gid = int(gs); rows = [r for r in e['rows'] if r[2] <= MAXMM and r[3] <= MEANMM and r[4] >= VOL_MIN and r[5] <= GAPMM]
    if e['cat'] == 'hand':
        rows = [r for r in rows if r[0] >= HAND_MIN - 1e-6]
    if gid in KEEP_GROUPS:   # both tali (42, 103): reduced at 0.7 they parted from the calf in 61-277 of 659 poses (b76 audit)
        rows = []
    if e['cat'] == 'sheet':   # back panel: the hem is locked (open boundary); 0.4 keeps its painted tears' interior rows
        rows = [r for r in rows if r[0] >= 0.4 - 1e-6]
    if e['cat'] == 'dome' or gid in FLOOR07:
        rows = [r for r in rows if r[0] >= 0.7 - 1e-6]
    pi = e['prim']
    if rows:
        best = min(rows, key=lambda r: (r[1], r[3])); pick[gid] = best[0]
        newT[pi].append(SN[f'g{gid}_r{int(round(best[0] * 100))}']); k = best[1]
    else:
        pick[gid] = 1.0; newT[pi].append(prims[pi]['T'][group[off[pi]:off[pi + 1]] == gid]); k = e['n']
    c = cats.setdefault(e['cat'], [0, 0]); c[0] += e['n']; c[1] += k
# back panel cut: its installed lining faces (same piece, dark texel) are replaced by the reversed lining twins of the surviving
# outer faces (each outer vertex has a lining vertex at the same position with the same joints and weights)
comp = sets['comp']
for gid, r in pick.items():
    e = SW[str(gid)]
    if e['cat'] != 'sheet' or r >= 1.0:
        continue
    p0 = prims[0]; P = p0['POSITION'].astype(np.float64); J = p0['JOINTS_0']; W = p0['WEIGHTS_0'].astype(np.float64)
    gf = np.flatnonzero(group[:off[1]] == gid); pc = np.unique(comp[gf])
    linf = np.flatnonzero(lining[:off[1]] & np.isin(comp[:off[1]], pc))
    key = lambda i: (tuple(np.round(P[i], 6)), tuple(J[i]), tuple(np.round(W[i], 4)))
    twin = {key(int(v)): int(v) for v in np.unique(p0['T'][linf])}
    cut = SN[f'g{gid}_r{int(round(r * 100))}']
    linT = np.array([[twin[key(int(v))] for v in t] for t in cut])[:, ::-1]
    kept = newT[0][0]; drop = np.isin(np.sort(kept, 1).view([('', kept.dtype)] * 3).ravel(),
                                      np.sort(p0['T'][linf], 1).view([('', kept.dtype)] * 3).ravel())
    newT[0][0] = kept[~drop]; newT[0].append(linT)
    print(f'LINING group {gid}: {len(linf)} installed lining faces -> {len(linT)} (dropped {int(drop.sum())})')
out = {prims[i]['material']: np.concatenate(v) for i, v in newT.items()}
np.savez(HERE / 'work' / f'mp_r{tag}.npz', **out)
(HERE / 'work' / f'mp_r{tag}.json').write_text(json.dumps({'max': MAXMM, 'mean': MEANMM, 'gap': GAPMM, 'pick': pick}))
# ladder mesh: GLB vertices -> mesh_in vertices by position (Blender z-up, the MM9_Rig offset), linings left out
d_in = np.load(HERE / 'work' / 'mesh_in.npz'); tree = cKDTree(d_in['verts'])
bl_faces, bl_wuv = [], []
for pi, pr in enumerate(prims):
    T = out[pr['material']]
    if pi == 0:   # drop lining faces: they sit on the dark texel
        uvT = pr['TEXCOORD_0'][T]; T = T[~(np.ptp(uvT, axis=1).max(1) == 0)]
    P = pr['POSITION'].astype(np.float64); pb = np.c_[P[:, 0], -P[:, 2], P[:, 1] - 1.10451340675354]
    dist, bid = tree.query(pb); bf = bid[T]
    ok = (bf[:, 0] != bf[:, 1]) & (bf[:, 1] != bf[:, 2]) & (bf[:, 0] != bf[:, 2])
    uv = pr['TEXCOORD_0'].astype(np.float64); w = np.stack([uv[T][..., 0] + 2.0 * pi, 1.0 - uv[T][..., 1]], -1)
    bl_faces.append(bf[ok]); bl_wuv.append(w[ok].reshape(-1, 2))
    assert dist[np.unique(T)].max() < 2e-4, dist.max()
F = np.concatenate(bl_faces); used = np.unique(F); m = -np.ones(len(d_in['verts']), np.int64); m[used] = np.arange(len(used))
np.savez(HERE / 'work' / f'mesh_r{tag}.npz', verts=d_in['verts'][used], faces=m[F], wuv=np.concatenate(bl_wuv), src_index=used)
tot = sum(len(v) for v in out.values())
print(f'TAG {tag} MAX {MAXMM} MEAN {MEANMM}: LOD0 {tot} ({(tot / 12438 - 1) * 100:+.1f} %), ladder faces {len(F)} |',
      ' '.join(f'{c} {a}->{b}' for c, (a, b) in cats.items()))
