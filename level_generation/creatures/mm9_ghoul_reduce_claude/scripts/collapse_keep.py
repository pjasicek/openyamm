#!/usr/bin/env python3
"""Installed body faces around the faces that collapse or flip in a candidate (the Ghoul's collapse_gate.py rule: posed area below 20 %
of rest, or the normal against the rest normal carried by the face's blended rotation; its joint regions), for the listed
clip:region pairs, every frame at 30 fps. Keeps every installed Ghoul_A face within R m (rest centroids) of those faces, mirrored
in x, as work/keep_extra_<name>.npy. Usage: collapse_keep.py <candidate glb> <name> <clip:region> ...   (env R, default 0.025)"""
import os, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model  # noqa: E402
R = float(os.environ.get('R', '0.025')); AREA = 0.2
JR = {'knee_L': ('L Calf', 0.10), 'knee_R': ('R Calf', 0.10), 'groin_L': ('L Thigh', 0.15), 'groin_R': ('R Thigh', 0.15),
      'elbow_L': ('L Forearm', 0.085), 'elbow_R': ('R Forearm', 0.085), 'armpit_L': ('L UpperArm', 0.12),
      'armpit_R': ('R UpperArm', 0.12), 'ankle_L': ('L Foot', 0.09), 'ankle_R': ('R Foot', 0.09), 'wrist_L': ('L Hand', 0.05),
      'wrist_R': ('R Hand', 0.05)}
glb, name = sys.argv[1:3]; pairs = [a.split(':') for a in sys.argv[3:]]
m = Model(Glb(glb)); doc = m.glb.json; names = [doc['nodes'][j]['name'] for j in doc['skins'][0]['joints']]
Rs = m.skinned_positions(m.world({})); rest = np.concatenate([r[0] for r in Rs]); offs = np.cumsum([0] + [len(r[0]) for r in Rs])
T = np.concatenate([np.asarray(r[1]).reshape(-1, 3) + o for r, o in zip(Rs, offs)])
J = np.concatenate([p['joints'] for p in m.primitives]); W = np.concatenate([p['weights'] for p in m.primitives])
fw = np.zeros((len(T), len(names)))
for k in range(J.shape[1]):
    for c in range(3):
        np.add.at(fw, (np.arange(len(T)), J[T[:, c], k]), W[T[:, c], k])
w0 = m.world({}); jp = {n: w0[doc['skins'][0]['joints'][i]][:3, 3] for i, n in enumerate(names)}
cen = rest[T].mean(1); label = np.array(['body'] * len(T), dtype=object)
for r, (b, rad) in sorted(JR.items(), key=lambda kv: -kv[1][1]):
    label[np.linalg.norm(cen - jp['Bip01 ' + b], axis=1) < rad] = r
hb = [i for i, n in enumerate(names) if n.endswith((' Head', ' Neck', ' Head_h', ' Neck_h'))]
label[(fw[:, hb].sum(1) > 2.0) & (label == 'body')] = 'neck_head'
def tri(P):
    n = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]]); return n, np.linalg.norm(n, axis=1) / 2
n0, a0 = tri(rest); ok = a0 > 1e-9
hit = np.zeros(len(T), bool)
for clip, reg in pairs:
    for t in np.arange(0, m.clip_times(clip)[-1] + 1e-6, 1 / 30):
        world = m.world(m.sample(clip, float(t))); P = np.concatenate([r[0] for r in m.skinned_positions(world)])
        pal = world[m.joints] @ m.inverse_binds; n, a = tri(P)
        nr = np.einsum('fij,fj->fi', np.einsum('fb,bij->fij', fw / 3, pal[:, :3, :3]), n0)
        d = (n * nr).sum(1) / np.maximum(np.linalg.norm(n, axis=1) * np.linalg.norm(nr, axis=1), 1e-12)
        hit |= ok & ((a < AREA * a0) | (d < 0)) & (label == reg)
print('collapsing faces', int(hit.sum()), [(c, r) for c, r in pairs])
src = Model(Glb(str(HERE / 'before' / 'mm9_ghoul.glb'))); sr = src.skinned_positions(src.world({}))[0]
sc = sr[0][np.asarray(sr[1]).reshape(-1, 3)].mean(1)
pts = cen[hit]; pts = np.vstack([pts, pts * [-1, 1, 1]])
keep = np.zeros(len(sc), bool)
for i in cKDTree(sc).query_ball_point(pts, R):
    keep[i] = True
lab = np.load(HERE / 'work' / 'labels.npz')['body']; keep &= lab == 0
np.save(HERE / 'work' / f'keep_extra_{name}.npy', keep); print('COLLAPSE KEEP', name, R, int(keep.sum()))
