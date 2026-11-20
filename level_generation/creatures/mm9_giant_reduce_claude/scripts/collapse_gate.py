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
REGIONS = (('knee_L', ('Bip01 L Calf', 'Bip01 L Calf_h')), ('knee_R', ('Bip01 R Calf', 'Bip01 R Calf_h')), ('hip_L', ('Bip01 L Thigh', 'Bip01 L Thigh_h')), ('hip_R', ('Bip01 R Thigh', 'Bip01 R Thigh_h')),
           ('ankle_L', ('Bip01 L Foot', 'Bip01 L Foot_h')), ('ankle_R', ('Bip01 R Foot', 'Bip01 R Foot_h')), ('toe_L', ('Bip01 L Toe0', 'Bip01 L Toe0_h')), ('toe_R', ('Bip01 R Toe0', 'Bip01 R Toe0_h')),
           ('elbow_L', ('Bip01 L Forearm', 'Bip01 L Forearm_h')), ('elbow_R', ('Bip01 R Forearm', 'Bip01 R Forearm_h')), ('shoulder_L', ('Bip01 L UpperArm', 'Bip01 L Clavicle', 'Bip01 L UpperArm_h')), ('shoulder_R', ('Bip01 R UpperArm', 'Bip01 R Clavicle', 'Bip01 R UpperArm_h')),
           ('wrist_L', ('Bip01 L Hand', 'Bip01 L Hand_h')), ('wrist_R', ('Bip01 R Hand', 'Bip01 R Hand_h')), ('groin', ('Bip01 Pelvis', 'Bip01 Spine')), ('torso', ('Bip01 Spine2', 'Bip01 Spine3')),
           ('neck', ('Bip01 Neck', 'Bip01 Neck_h', 'Bip01 Head_h')), ('head', ('Bip01 Head',)))   # giant: MM9 has a Neck bone
m = Model(Glb(sys.argv[1]))
doc = m.glb.json
names = [doc['nodes'][j]['name'] for j in doc['skins'][0]['joints']]
PR = m.primitives                              # all LOD0 primitives (up, low, head), as one surface
rest = np.vstack([np.asarray(p['positions'], float) for p in PR])     # the bind pose: node rests differ from it
OFF = np.cumsum([0] + [len(p['positions']) for p in PR])
SK = lambda world: np.vstack([x[0] for x in m.skinned_positions(world)])
T = np.vstack([np.asarray(x[1]).reshape(-1, 3) + o for x, o in zip(m.skinned_positions(m.world({})), OFF)])
J = np.vstack([p['joints'] for p in PR]); W = np.vstack([p['weights'] for p in PR])
fw = np.zeros((len(T), len(names)))
for k in range(J.shape[1]):
    for c in range(3):
        np.add.at(fw, (np.arange(len(T)), J[T[:, c], k]), W[T[:, c], k])
dom = fw.argmax(1)
label = np.array(['body'] * len(T), dtype=object)
for r, bones in REGIONS:
    label[np.isin(dom, [names.index(b) for b in bones if b in names])] = r
strip_names = tuple(n for n in names if n.startswith('Xband') or n in ('XstripRoot', 'XstripTip'))
label[np.isin(dom, [names.index(b) for b in strip_names if b in names])] = 'strip'
label[np.array(['Thumb' in names[d] or 'Index' in names[d] or 'Middle' in names[d] or 'Ring' in names[d] or 'Pinky' in names[d] for d in dom])] = 'finger'
regions = [r for r, _ in REGIONS] + ['strip', 'finger', 'body']


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
want = sys.argv[3].split(',') if len(sys.argv) > 3 else None
for clip in [a['name'] for a in doc['animations'] if not want or a['name'] in want]:
    Te = m.clip_times(clip)[-1]
    frames = np.arange(0, Te + 1e-6, 1 / 30)
    worst = {r: 0 for r in regions}
    total = 0
    worst_faces = {}
    worst_t, most = 0.0, -1
    for t in frames:
        world = m.world(m.sample(clip, float(t)))
        P = SK(world)
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
    P = SK(world)
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
