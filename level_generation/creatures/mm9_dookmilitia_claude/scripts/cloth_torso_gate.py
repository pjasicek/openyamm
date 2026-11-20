#!/usr/bin/env python3
"""Skirt through the torso, per clip at 48 fps (run 2; skirt_gate.py covers the thighs through the skirt). A skirt vertex
(Skirt_* weight share over 0.5: the free cloth, not the band under the belt) is inside when it lies behind the nearest
outer face of the torso (faces whose vertices all follow Pelvis, Spine*, Neck: no limb, no cloth, no held weapon) within
6 cm, by that face's normal. Depth in cm; the bind pose is printed first as the baseline.
Args: <glb> <out json> [clips]"""
import json, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor')); sys.path.insert(0, str(HERE.parent / 'claude_shared')); sys.path.insert(0, str(HERE / 'scripts'))
from glb_pose import Glb, Model
from detached_parts_audit import closest_on_triangles
from outer_surface import outer_faces
glb, out = sys.argv[1:3]
want = sys.argv[3].split(',') if len(sys.argv) > 3 else None
m = Model(Glb(glb)); names = [n.get('name') for n in m.glb.json['nodes']]; jn = [names[j] for j in m.joints]
P = m.primitives; USE = [k for k, pr in enumerate(P) if pr['node'] == P[0]['node'] and pr['skinned']]
tri, dom, sk, off = [], [], [], 0
skirt_j = np.array([n.startswith('Skirt_') for n in jn])
for k in USE:
    pr = P[k]; tri.append(pr['triangles'] + off); off += len(pr['positions'])
    dom.append(np.array([jn[pr['joints'][v][np.argmax(pr['weights'][v])]] for v in range(len(pr['positions']))]))
    sk.append((pr['weights'] * skirt_j[pr['joints']]).sum(1))
tri = np.concatenate(tri); dom = np.concatenate(dom); sk = np.concatenate(sk)
TORSO = ('Bip01 Pelvis', 'Bip01 Spine', 'Bip01 Spine1', 'Bip01 Spine2', 'Bip01 Spine3', 'Bip01 Neck')
tv = np.isin(dom, TORSO) & (sk < 0.05)
cloth = np.where(sk > 0.5)[0]


def skin(w):
    sp = m.skinned_positions(w); return np.concatenate([sp[k][0] for k in USE])


rest = skin(m.world({}))
tf = np.where(tv[tri].all(1))[0]; tf = tf[outer_faces(rest, tri, tf)]


def depth(X):
    T = X[tri[tf]]; a, b, c = T[:, 0], T[:, 1], T[:, 2]
    n = np.cross(b - a, c - a); n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    pts = X[cloth]; _, near = cKDTree((a + b + c) / 3).query(pts, k=24)
    rp = np.repeat(pts, 24, 0)
    q, _ = closest_on_triangles(rp, a[near.ravel()], b[near.ravel()], c[near.ravel()])
    d = np.linalg.norm(rp - q, axis=1).reshape(near.shape); best = d.argmin(1); rows = np.arange(len(pts))
    side = np.einsum('ij,ij->i', pts - q.reshape(*near.shape, 3)[rows, best], n[near[rows, best]])
    db = d[rows, best]
    return np.where((side < 0) & (db <= 0.06) & (np.abs(side) > 0.9 * db), db, 0.0)


print('skirt verts', len(cloth), 'torso outer faces', len(tf), 'bind depth cm', round(float(depth(rest).max()) * 100, 2))
rep = {}
for clip in m.clips:
    if want and clip not in want: continue
    dur = max(m.clip_times(clip)); worst = (0.0, 0); bad = 0
    for k, t in enumerate(np.arange(0, dur + 1e-6, 1 / 48)):
        dd = depth(skin(m.world(m.sample(clip, float(t))))).max()
        if dd > worst[0]: worst = (float(dd), k)
        bad += int(dd > 0.01)
    rep[clip] = {'worst_cm': round(worst[0] * 100, 1), 'frame48': worst[1], 'frames_over_1cm': bad}
    print(f'{clip:13s} skirt in torso max {rep[clip]["worst_cm"]:5.1f} cm @{worst[1]}  frames >1cm {bad}', flush=True)
json.dump(rep, open(out, 'w'), indent=1)
