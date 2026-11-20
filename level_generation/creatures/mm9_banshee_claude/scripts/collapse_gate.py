#!/usr/bin/env python3
"""Face collapse gate of the Banshee (after mm9_cat_claude/scripts/collapse_gate.py): per clip at 30 fps, the faces whose area
collapses or whose normal flips against the rest pose, by joint region, over ALL LOD0 primitives (the Banshee is split by
blend order). Rest is carried along by each face's own blended skin rotation, so a swinging limb does not count:
  collapse - posed area below AREA of the rest area
  flip     - posed normal against the rest normal turned by the face's blended rotation (dot below 0)
On a see-through body no fold is hidden, so "exposed" is not reported: every count here can be seen.
Death and Dead are scaled to nothing on purpose (the Ghost dissolves): their area test is relative to the pose's uniform scale.
Usage: collapse_gate.py <glb> [json]"""
import json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model

AREA = 0.2


def region(name):
    side = 'R' if name.endswith('01') else 'L'
    if name.startswith('Zfing'):
        return 'fingers_' + ('R' if name[-2:] in ('04', '05', '06', '07') else 'L')
    if name.startswith('Zhand'):
        return 'wrist_' + side
    if name.startswith('Zarmbase'):
        return 'shoulder_' + side
    if name.startswith('Zarmpiv'):
        return 'upperarm_' + side
    if name.startswith('Zarm'):
        return 'elbow_fore_' + side
    if name.startswith('Xspine'):
        return 'torso'
    if name in ('XCENTER', 'Ydress'):
        return 'waist'
    if name.startswith(('Xneck', 'Xheadpiv')):
        return 'neck'
    if name.startswith(('Xjaw', 'Xchin')):
        return 'jaw'
    if name.startswith(('Xhair', 'Xhm', 'Xht', 'Xhb')):
        return 'hair'
    if name.startswith('Xhead') or name == 'Xface':
        return 'head'
    if name.startswith(('XcB', 'XcC', 'XcD')):
        return 'wing_' + side
    if name.startswith(('Xcm', 'Xce', 'Xct', 'XcA')):
        return 'cape'
    if name.startswith('Y'):
        return 'dress_' + {'f': 'front', 'b': 'back', 'l': 'left', 'r': 'right'}.get(name[1], 'front')
    return 'other'


m = Model(Glb(sys.argv[1]))
doc = m.glb.json
names = [doc['nodes'][j]['name'] for j in doc['skins'][0]['joints']]
labels_of_bone = [region(n) for n in names]
regions = sorted(set(labels_of_bone))
posed0 = m.skinned_positions(m.world({}))
prims = []
for pr, (rest, T) in zip(m.primitives, posed0):
    T = np.asarray(T).reshape(-1, 3)
    J, W = pr['joints'], pr['weights']
    fw = np.zeros((len(T), len(names)))
    for k in range(J.shape[1]):
        for c in range(3):
            np.add.at(fw, (np.arange(len(T)), J[T[:, c], k]), W[T[:, c], k])
    lab = np.array([labels_of_bone[i] for i in fw.argmax(1)], dtype=object)
    n0 = np.cross(rest[T[:, 1]] - rest[T[:, 0]], rest[T[:, 2]] - rest[T[:, 0]])
    prims.append((T, fw, lab, n0, np.linalg.norm(n0, axis=1) / 2))
report = {}
for clip in [a['name'] for a in doc['animations']]:
    Te = m.clip_times(clip)[-1]
    frames = np.arange(0, Te + 1e-6, 1 / 30)
    worst = {r: 0 for r in regions}
    wt = {}
    total = 0
    for t in frames:
        world = m.world(m.sample(clip, float(t)))
        pal = world[m.joints] @ m.inverse_binds
        counts = {r: 0 for r in regions}
        for (P, _), (T, fw, lab, n0, a0) in zip(m.skinned_positions(world), prims):
            n = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]])
            a = np.linalg.norm(n, axis=1) / 2
            blend = np.einsum('fb,bij->fij', fw / 3, pal[:, :3, :3])
            scale2 = np.abs(np.linalg.det(blend)) ** (2 / 3)
            nr = np.einsum('fij,fj->fi', blend, n0)
            d = (n * nr).sum(1) / np.maximum(np.linalg.norm(n, axis=1) * np.linalg.norm(nr, axis=1), 1e-16)
            bad = (a0 > 1e-9) & ((a < AREA * a0 * scale2) | (d < 0))
            total += int(bad.sum())
            for r, c in zip(*np.unique(lab[bad], return_counts=True)):
                counts[r] += int(c)
        for r in regions:
            if counts[r] > worst[r]:
                worst[r] = counts[r]
                wt[r] = round(float(t), 3)
    report[clip] = {'worst': {r: v for r, v in worst.items() if v}, 'worst_time': {r: wt[r] for r in wt}, 'face_frames': total,
                    'frames': len(frames)}
    print(f'{clip:13} face-frames {total:6} of {len(frames)} frames; worst frame '
          + (' '.join(f'{r}={v}@{wt[r]}' for r, v in worst.items() if v) or 'none'))
print('TOTAL faces', sum(len(p[0]) for p in prims))
if len(sys.argv) > 2:
    json.dump(report, open(sys.argv[2], 'w'), indent=1)
