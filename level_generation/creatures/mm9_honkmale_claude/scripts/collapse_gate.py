#!/usr/bin/env python3
"""Face collapse gate for the Honk bodies, adapted from mm9_cat_claude/scripts/collapse_gate.py: per clip, at 30 fps, the faces
whose area collapses or whose normal flips against the rest pose, by joint region, over both materials. Rest is carried along
by each face's own blended skin rotation, so a limb that simply swings does not count:
  collapse - posed area below AREA of the rest area
  flip     - posed normal against the rest normal turned by the face's blended rotation (dot below 0)
Prints the worst single frame per clip and region, the face-frames per clip, and how many of the worst frame's faces any camera
can see (exposed). Usage: collapse_gate.py <glb> [json]"""
import json, re, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model

AREA = 0.2


def region(name):
    side = '_L' if ' L ' in name else '_R' if ' R ' in name else ''
    if re.search(r'Forearm', name): return 'elbow' + side
    if re.search(r'Clavicle|UpperArm', name): return 'armpit' + side
    if re.search(r'Hand|Finger|Thumb|Index|Middle|Ring|Pinky', name): return 'hand' + side
    if re.search(r'Calf|Foot|Toe', name): return 'leg' + side
    if name.startswith('X'): return 'robe'
    if re.search(r'Ponytail|^Y', name): return 'hair'
    if 'Head' in name: return 'head'
    if 'Neck' in name: return 'neck'
    return 'waist'


m = Model(Glb(sys.argv[1]))
doc = m.glb.json
names = [doc['nodes'][j]['name'] for j in doc['skins'][0]['joints']]
prims = [p for p in m.primitives if p['skinned']]
assert len(prims) == 2


def merged(posed):
    return np.vstack([posed[i][0] for i, p in enumerate(m.primitives) if p['skinned']])


offs = np.cumsum([0] + [len(p['positions']) for p in prims])
T = np.vstack([np.asarray(p['triangles']).reshape(-1, 3) + offs[i] for i, p in enumerate(prims)])
J = np.vstack([p['joints'] for p in prims])
W = np.vstack([p['weights'] for p in prims])
rest = merged(m.skinned_positions(m.world({})))
fw = np.zeros((len(T), len(names)))
for k in range(J.shape[1]):
    for c in range(3):
        np.add.at(fw, (np.arange(len(T)), J[T[:, c], k]), W[T[:, c], k])
dom = fw.argmax(1)
bone_region = np.array([region(n) for n in names], dtype=object)
label = bone_region[dom].copy()
# a face of the robe tube, not only its X chains: everything below the belt that is not boot
y = rest[T].mean(1)[:, 1]
top = float(rest[:, 1].max())
belt = 0.59 * top
lowerbody = np.isin(label.astype(str), ('waist', 'robe'))
label[(y < belt) & lowerbody] = 'robe'
label[(label == 'robe') & (y > 0.72 * belt)] = 'groin'  # the robe's lap: what bends when the legs swing
regions = sorted(set(label.tolist()))


def tri(P):
    n = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]])
    return n, np.linalg.norm(n, axis=1) / 2


def exposed(P, faces, normals):
    """Which of the faces can be seen: a ray from just off the face, in any of 42 directions, leaves the mesh unblocked."""
    A, B, C = P[T[:, 0]], P[T[:, 1]], P[T[:, 2]]
    e1, e2 = B - A, C - A
    g = np.pi * (3 - 5 ** 0.5)
    k = np.arange(42) + 0.5
    zz = 1 - 2 * k / 42
    rr = np.sqrt(1 - zz ** 2)
    dirs = np.c_[rr * np.cos(g * k), zz, rr * np.sin(g * k)]
    out = np.zeros(len(T), bool)
    for f in faces:
        o = P[T[f]].mean(0)
        o = o + normals[f] / max(np.linalg.norm(normals[f]), 1e-12) * 2e-4
        for w in dirs:
            h = np.cross(w, e2)
            det = (e1 * h).sum(1)
            s = o - A
            with np.errstate(divide='ignore', invalid='ignore'):
                u = (s * h).sum(1) / det
                q = np.cross(s, e1)
                v = (q * w).sum(1) / det
                tt = (e2 * q).sum(1) / det
            hit = (np.abs(det) > 1e-14) & (u >= 0) & (v >= 0) & (u + v <= 1) & (tt > 1e-4)
            hit[f] = False
            if not hit.any():
                out[f] = True
                break
    return out


n0, a0 = tri(rest)
ok = a0 > 1e-9


def bad_faces(t, clip):
    world = m.world(m.sample(clip, float(t)))
    P = merged(m.skinned_positions(world))
    pal = world[m.joints] @ m.inverse_binds
    blend = np.einsum('fb,bij->fij', fw / 3, pal[:, :3, :3])
    n, a = tri(P)
    nr = np.einsum('fij,fj->fi', blend, n0)
    d = (n * nr).sum(1) / np.maximum(np.linalg.norm(n, axis=1) * np.linalg.norm(nr, axis=1), 1e-12)
    return P, nr, ok & ((a < AREA * a0) | (d < 0))


report = {}
print('faces by region:', {r: int((label == r).sum()) for r in regions})
import os
ONLY = os.environ.get('CLIPS')
for clip in [a['name'] for a in doc['animations'] if not ONLY or a['name'] in ONLY.split(',')]:
    Te = m.clip_times(clip)[-1]
    frames = np.arange(0, Te + 1e-6, 1 / 30)
    worst = {r: 0 for r in regions}
    wt = {}
    total = 0
    worst_t, most = 0.0, -1
    for t in frames:
        _, _, bad = bad_faces(t, clip)
        total += int(bad.sum())
        if int(bad.sum()) > most:
            most, worst_t = int(bad.sum()), float(t)
        for r in regions:
            c = int((bad & (label == r)).sum())
            if c > worst[r]:
                worst[r] = c
                wt[r] = round(float(t), 3)
    P, nr, bad = bad_faces(worst_t, clip)
    seen = exposed(P, np.nonzero(bad)[0], nr)
    shown = {r: int((seen & (label == r)).sum()) for r in regions}
    report[clip] = {'worst': {r: v for r, v in worst.items() if v}, 'worst_times': wt, 'face_frames': total, 'frames': len(frames),
                    'exposed_at_worst_frame': {r: v for r, v in shown.items() if v}, 'worst_time': float(worst_t)}
    print(f'{clip:12} face-frames {total:6}/{len(frames)}  worst ' + ' '.join(f'{r}={v}@{wt[r]}' for r, v in worst.items() if v)
          + '  | exposed ' + (' '.join(f'{r}={v}' for r, v in shown.items() if v) or '0'), flush=True)
if len(sys.argv) > 2:
    json.dump(report, open(sys.argv[2], 'w'), indent=1)
