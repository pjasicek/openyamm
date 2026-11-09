#!/usr/bin/env python3
"""Face collapse gate: per clip, at 30 fps, the faces whose area collapses or whose normal flips against the rest pose, by joint
region. Rest is carried along by each face's own blended skin rotation, so a limb that simply swings does not count:
  collapse - posed area below AREA of the rest area
  flip     - posed normal against the rest normal turned by the face's blended rotation (dot below 0)
Prints the worst single frame per clip and region, the face-frames per clip, and how many of the worst frame's faces any
camera can see (exposed). Usage: collapse_gate.py <glb> [json]"""
import json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model

AREA = 0.2
REGIONS = (('knee_L', ('Xbleg', 'Xblegmid', 'Xbleg_h', 'Xblegmid_h')), ('knee_R', ('Xbleg01', 'Xblegmid01', 'Xbleg01_h', 'Xblegmid01_h')),
           ('hip_L', ('Xblegpiv', 'Xblegpiv_h')), ('hip_R', ('Xblegpiv01', 'Xblegpiv01_h')),
           ('ankle_L', ('Xbankle', 'Xbfoot', 'Xbankle_h')), ('ankle_R', ('Xbankle01', 'Xbfoot01', 'Xbankle01_h')),
           ('fore_L', ('Xflegpiv', 'Xfankle', 'Xffoot')), ('fore_R', ('Xflegpiv01', 'Xfankle01', 'Xffoot01')))
m = Model(Glb(sys.argv[1]))
doc = m.glb.json
names = [doc['nodes'][j]['name'] for j in doc['skins'][0]['joints']]
pr = m.primitives[0]
rest = m.skinned_positions(m.world({}))[0][0]
T = np.asarray(m.skinned_positions(m.world({}))[0][1]).reshape(-1, 3)
J, W = pr['joints'], pr['weights']
fw = np.zeros((len(T), len(names)))
for k in range(J.shape[1]):
    for c in range(3):
        np.add.at(fw, (np.arange(len(T)), J[T[:, c], k]), W[T[:, c], k])
dom = fw.argmax(1)
label = np.array(['body'] * len(T), dtype=object)
for r, bones in REGIONS:
    label[np.isin(dom, [names.index(b) for b in bones if b in names])] = r
regions = [r for r, _ in REGIONS] + ['body']


def tri(P):
    n = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]])
    return n, np.linalg.norm(n, axis=1) / 2


def exposed(P, faces, normals):
    """Which of the faces can be seen: a ray from just off the face, in any of 42 directions, leaves the mesh unblocked. A face
    inside a crease or under a pressed thigh cannot be seen from any camera."""
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
pal0 = None
report = {}
for clip in [a['name'] for a in doc['animations']]:
    Te = m.clip_times(clip)[-1]
    frames = np.arange(0, Te + 1e-6, 1 / 30)
    worst = {r: 0 for r in regions}
    total = 0
    worst_faces = {}
    worst_t, most = 0.0, -1
    for t in frames:
        world = m.world(m.sample(clip, float(t)))
        P = m.skinned_positions(world)[0][0]
        pal = world[m.joints] @ m.inverse_binds
        blend = np.einsum('fb,bij->fij', fw / 3, pal[:, :3, :3])
        n, a = tri(P)
        nr = np.einsum('fij,fj->fi', blend, n0)
        d = (n * nr).sum(1) / np.maximum(np.linalg.norm(n, axis=1) * np.linalg.norm(nr, axis=1), 1e-12)
        bad = ok & ((a < AREA * a0) | (d < 0))
        total += int(bad.sum())
        if int(bad.sum()) > most:
            most, worst_t = int(bad.sum()), float(t)
        for r in regions:
            c = int((bad & (label == r)).sum())
            if c > worst[r]:
                worst[r] = c
                worst_faces[r] = float(t)
    world = m.world(m.sample(clip, float(worst_t)))
    P = m.skinned_positions(world)[0][0]
    n, a = tri(P)
    pal = world[m.joints] @ m.inverse_binds
    nr = np.einsum('fij,fj->fi', np.einsum('fb,bij->fij', fw / 3, pal[:, :3, :3]), n0)
    d = (n * nr).sum(1) / np.maximum(np.linalg.norm(n, axis=1) * np.linalg.norm(nr, axis=1), 1e-12)
    bad = ok & ((a < AREA * a0) | (d < 0))
    seen = exposed(P, np.nonzero(bad)[0], nr)
    shown = {r: int((seen & (label == r)).sum()) for r in regions}
    report[clip] = {'worst': {r: v for r, v in worst.items() if v}, 'face_frames': total, 'frames': len(frames),
                    'exposed_at_worst_frame': {r: v for r, v in shown.items() if v}, 'worst_time': float(worst_t)}
    print(f'{clip:12} face-frames {total:6}  worst frame ' + ' '.join(f'{r}={v}' for r, v in worst.items() if v)
          + '  | exposed ' + (' '.join(f'{r}={v}' for r, v in shown.items() if v) or '0'))
if len(sys.argv) > 2:
    json.dump(report, open(sys.argv[2], 'w'), indent=1)
