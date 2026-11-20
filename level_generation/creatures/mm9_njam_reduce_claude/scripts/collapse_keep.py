#!/usr/bin/env python3
"""Exact faces where a candidate's new (cut) faces collapse in pose (b50: the collapse gate's worst-frame knee counts 0 -> 2-3,
torso 4 -> 6, SpellAttack elbow/shoulder R +1). The collapse gate's own test (../mm9_njam_claude/scripts/collapse_gate.py: posed
area below 20 % of rest or the normal flipped against the face's blended skin rotation, every clip at 30 fps) on the candidate's
LOD0; every bad face that is not an installed face (a face made by a collapse) in the REGIONS given marks the installed faces
whose rest centroid lies within PAD m of it (closest point on the bad face). Writes work/collapse_keep.npy (per installed LOD0
face, glb_parts order). Usage: [REGIONS=knee_L,... PAD=0.004] collapse_keep.py <candidate.glb>"""
import os
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor')); sys.path.insert(0, str(HERE.parent / 'claude_shared'))
from glb_pose import Glb, Model  # noqa: E402
from detached_parts_audit import closest_on_triangles  # noqa: E402
WANT = os.environ.get('REGIONS', 'knee_L,knee_R,hip_L,hip_R,groin,torso,elbow_L,elbow_R,shoulder_L,shoulder_R').split(',')
PAD = float(os.environ.get('PAD', '0.004'))
REGIONS = (('knee_L', ('Bip01 L Calf', 'Bip01 L Calf_h')), ('knee_R', ('Bip01 R Calf', 'Bip01 R Calf_h')),
           ('hip_L', ('Bip01 L Thigh', 'Bip01 L Thigh_h')), ('hip_R', ('Bip01 R Thigh', 'Bip01 R Thigh_h')),
           ('elbow_L', ('Bip01 L Forearm', 'Bip01 L Forearm_h')), ('elbow_R', ('Bip01 R Forearm', 'Bip01 R Forearm_h')),
           ('shoulder_L', ('Bip01 L UpperArm', 'Bip01 L Clavicle', 'Bip01 L UpperArm_h')),
           ('shoulder_R', ('Bip01 R UpperArm', 'Bip01 R Clavicle', 'Bip01 R UpperArm_h')),
           ('groin', ('Bip01 Pelvis', 'Bip01 Spine')), ('torso', ('Bip01 Spine1', 'Bip01 Spine2', 'Bip01 Spine3')))


def load(path):
    m = Model(Glb(str(path))); names = [m.glb.json['nodes'][j]['name'] for j in m.glb.json['skins'][0]['joints']]
    PR = m.primitives[:3]; OFF = np.cumsum([0] + [len(p['positions']) for p in PR])
    T = np.vstack([np.asarray(p['triangles']).reshape(-1, 3) + o for p, o in zip(PR, OFF)])
    rest = np.vstack([np.asarray(p['positions'], float) for p in PR])
    J = np.vstack([p['joints'] for p in PR]); W = np.vstack([p['weights'] for p in PR])
    return m, names, PR, T, rest, J, W


m, names, PR, T, rest, J, W = load(sys.argv[1])
_, _, PI, TI, restI, _, _ = load(HERE / 'before' / 'mm9_njam.glb')
fw = np.zeros((len(T), len(names)))
for k in range(J.shape[1]):
    for c in range(3):
        np.add.at(fw, (np.arange(len(T)), J[T[:, c], k]), W[T[:, c], k])
dom = fw.argmax(1); label = np.array(['body'] * len(T), dtype=object)
for r, bones in REGIONS:
    label[np.isin(dom, [names.index(b) for b in bones if b in names])] = r
inreg = np.isin(label, WANT)
# installed faces by exact corner positions
key = lambda P, Tr: {tuple(sorted(map(tuple, np.round(P[t], 7).tolist()))) for t in Tr}
inst = key(restI, TI)
new = np.array([tuple(sorted(map(tuple, np.round(rest[t], 7).tolist()))) not in inst for t in T])
print('candidate faces', len(T), 'new', int(new.sum()), 'new in regions', int((new & inreg).sum()))
n0 = np.cross(rest[T[:, 1]] - rest[T[:, 0]], rest[T[:, 2]] - rest[T[:, 0]]); a0 = np.linalg.norm(n0, axis=1) / 2; ok = a0 > 1e-9
SK = lambda world: np.vstack([x[0] for x in m.skinned_positions(world)[:3]])
badany = np.zeros(len(T), bool)
for clip in m.clips:
    for t in np.arange(0, m.clip_times(clip)[-1] + 1e-6, 1 / 30):
        world = m.world(m.sample(clip, float(t))); P = SK(world)
        pal = world[m.joints] @ m.inverse_binds
        n = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]]); a = np.linalg.norm(n, axis=1) / 2
        nr = np.einsum('fij,fj->fi', np.einsum('fb,bij->fij', fw / 3, pal[:, :3, :3]), n0)
        d = (n * nr).sum(1) / np.maximum(np.linalg.norm(n, axis=1) * np.linalg.norm(nr, axis=1), 1e-12)
        badany |= ok & ((a < 0.2 * a0) | (d < 0))
sel = np.flatnonzero(badany & new & inreg)
print('bad new faces in regions', len(sel), {r: int((label[sel] == r).sum()) for r in WANT})
ci = restI[TI].mean(1); tree = cKDTree(ci); hit = np.zeros(len(TI), bool)
for f in sel:
    tri = rest[T[f]]; c = tri.mean(0); R = np.linalg.norm(tri - c, axis=1).max() + PAD
    idx = tree.query_ball_point(c, R)
    if not idx:
        continue
    idx = np.array(idx); q, _ = closest_on_triangles(ci[idx], *[np.repeat(tri[k][None], len(idx), 0) for k in range(3)])
    hit[idx[np.linalg.norm(q - ci[idx], axis=1) < PAD]] = True
np.save(HERE / 'work' / 'collapse_keep.npy', hit); print('KEEP installed faces', int(hit.sum()))
