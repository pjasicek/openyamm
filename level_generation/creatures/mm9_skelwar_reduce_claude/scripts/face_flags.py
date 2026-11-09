#!/usr/bin/env python3
"""Per-face flags over work/mesh_in.npz faces (= the faces of work/source_nolining.glb, body then head primitive; the
scimitar's 51 coincident blade pairs were merged by the weld and are not flagged; it is kept whole anyway):
- grip: right-hand (gauntlet) faces with a vertex within GRIP_MM of the scimitar surface in the posed grip (Standing 0.0 s,
  AttackMelee 0.3 s: the finger keys hold the solved fist in every clip), plus one face ring -> kept exactly;
- visible: cranium faces that any of 400 outward rays (around the face normal, from 0.3 mm off the surface) leaves without
  hitting a head-set triangle (skull, mandible, helmet, guards, horns, eyes, teeth; all rigid on Bip01 Head, so this is
  pose-independent). The visible cranium is the face; the hidden rest (crown and temples under the helmet) is cut.
- lined: outer faces of the installed linings (lining_p0/p1.npy), matched by their welded vertex positions.
Writes work/face_flags.npz (grip, visible, lined; per mesh_in face)."""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor')); sys.path.insert(0, str(HERE.parent / 'claude_shared'))
from glb_pose import Glb, Model  # noqa: E402
from detached_parts_audit import closest_on_triangles  # noqa: E402
GRIP_MM = 5.0
m = Model(Glb(str(HERE / 'work' / 'source_nolining.glb')))
nb, nh = len(m.primitives[0]['triangles']), len(m.primitives[1]['triangles'])
d = np.load(HERE / 'work' / 'mesh_in.npz'); NF = len(d['faces'])
names = [m.glb.json['nodes'][j].get('name') for j in m.joints]
p0 = m.primitives[0]
rhand = np.isin(p0['joints'][np.arange(len(p0['positions'])), p0['weights'].argmax(1)],
                [i for i, n in enumerate(names) if n and n.startswith('Bip01 R ') and any(k in n for k in ('Hand', 'Finger', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky'))])
grip = np.zeros(NF, bool)
for clip, t in (('Standing', 0.0), ('AttackMelee', 0.3)):
    pos = m.skinned_positions(m.world(m.sample(clip, t)))
    B, TB = pos[0]; S, TS = pos[2]
    a, b, c = S[TS[:, 0]], S[TS[:, 1]], S[TS[:, 2]]
    vi = np.flatnonzero(rhand); dist = np.full(len(vi), 9.0)
    cen = S[TS].mean(1); tree = cKDTree(cen)
    for k, v in enumerate(vi):
        near = tree.query_ball_point(B[v], 0.08)
        if not near: continue
        q, _ = closest_on_triangles(np.repeat(B[v][None], len(near), 0), a[near], b[near], c[near])
        dist[k] = np.linalg.norm(q - B[v], axis=1).min()
    close = np.zeros(len(B), bool); close[vi[dist < GRIP_MM / 1000]] = True
    f = close[TB].any(1)
    ring = np.isin(TB, TB[f]).any(1)   # one face ring round the contact
    grip[:nb] |= ring
    print(clip, t, 'R-hand vertices within', GRIP_MM, 'mm of the scimitar', int(close.sum()), 'faces +ring', int(ring.sum()))
print('GRIP faces', int(grip.sum()))
# --- cranium visibility (rest pose, head primitive)
P1, T1 = m.primitives[1]['positions'], m.primitives[1]['triangles']
key = np.round(P1 / 1e-6).astype(np.int64); _, wid = np.unique(key, axis=0, return_inverse=True); wid = wid.ravel()
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
t = wid[T1]; n = wid.max() + 1
r_ = np.concatenate([t[:, 0], t[:, 1], t[:, 2]]); c_ = np.concatenate([t[:, 1], t[:, 2], t[:, 0]])
_, lab = connected_components(coo_matrix((np.ones(len(r_)), (r_, c_)), shape=(n, n)), directed=False)
fl = lab[t[:, 0]]; cran = np.bincount(fl).argmax(); cf = np.flatnonzero(fl == cran)
A, Bv, C = P1[T1[:, 0]], P1[T1[:, 1]], P1[T1[:, 2]]
fn = np.cross(Bv - A, C - A); fn /= np.linalg.norm(fn, axis=1, keepdims=True) + 1e-20
rng = np.random.default_rng(1); dirs = rng.normal(size=(1200, 3)); dirs /= np.linalg.norm(dirs, axis=1, keepdims=True)
e1, e2 = Bv - A, C - A
vis = np.zeros(len(T1), bool)
for i in cf:
    dd = dirs[dirs @ fn[i] > 0.05][:400]
    o = P1[T1[i]].mean(0) + fn[i] * 3e-4
    # Moller-Trumbore, rays x triangles
    pv = np.cross(dd[:, None, :], e2[None]); det = np.einsum('tc,rtc->rt', e1, pv)
    ok = np.abs(det) > 1e-12; inv = np.where(ok, 1 / np.where(ok, det, 1), 0)
    tv = o - A; u = np.einsum('tc,rtc->rt', tv, pv) * inv
    qv = np.cross(tv, e1); v = np.einsum('rc,tc->rt', dd, qv) * inv; tt = np.einsum('tc,tc->t', e2, qv)[None] * inv
    hit = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (tt > 1e-5)
    hit[:, i] = False
    vis[i] = (~hit.any(1)).any()
print('CRANIUM faces', len(cf), 'visible', int(vis[cf].sum()), 'hidden', int((~vis[cf]).sum()))
visible = np.zeros(NF, bool); visible[nb:nb + nh] = vis
cranium = np.zeros(NF, bool); cranium[nb + cf] = True
# --- lined outer faces: the installed linings coincide with them
lined = np.zeros(NF, bool)
mi = Model(Glb(str(HERE / 'before' / 'mm9_skelwar.glb')))
for pi, off in ((0, 0), (1, nb)):
    lin = np.load(HERE / 'work' / f'lining_p{pi}.npy'); Pi, Ti = mi.primitives[pi]['positions'], mi.primitives[pi]['triangles']
    lk = {tuple(sorted(map(tuple, np.round(Pi[f] / 1e-6).astype(np.int64).tolist()))) for f in Ti[lin]}
    Pn, Tn = m.primitives[pi]['positions'], m.primitives[pi]['triangles']
    for j, f in enumerate(Tn):
        if tuple(sorted(map(tuple, np.round(Pn[f] / 1e-6).astype(np.int64).tolist()))) in lk:
            lined[off + j] = True
    print('LINED prim', pi, int(lined[off:off + len(Tn)].sum()), 'of', int(lin.sum()))
np.savez(HERE / 'work' / 'face_flags.npz', grip=grip, visible=visible, cranium=cranium, lined=lined)
