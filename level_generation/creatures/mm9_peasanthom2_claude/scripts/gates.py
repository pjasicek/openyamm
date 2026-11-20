#!/usr/bin/env python3
"""Numeric gates on the runtime GLB (every clip, every key at 30 fps), humanoid playbook G4-G6 / arm and hand gate.

Usage: python3 gates.py <glb> <out json> <hand joint names comma> <head joint> <foot joints comma>
- floor: lowest visible point per key (model y; 0 = floor): standing/walk/idles within +-2 cm, nothing under -2 cm
- stretch: edge length / rest length per key, p1 / p99 / max over the body and over the hand+finger edges
- wrist: hand joint rotation relative to its forearm, change from rest (degrees), max per clip
- jerk: world rotation step per 1/30 s of the head, hands and feet (degrees), max per clip, plus the largest
  second difference (sudden change of angular speed)
- seam: loops, largest joint world-rotation difference between the first and last key (degrees)
"""
import json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model

glb_path, out_path, hands, head, feet = sys.argv[1:6]
hands = hands.split(',')
feet = feet.split(',')
glb = Glb(Path(glb_path))
model = Model(glb)
names = [n.get('name') for n in glb.json['nodes']]
idx = {n: i for i, n in enumerate(names)}
prim = model.primitives[0]
tris = prim['triangles']
edges = np.unique(np.sort(np.concatenate([tris[:, [0, 1]], tris[:, [1, 2]], tris[:, [2, 0]]]), axis=1), axis=0)
joint_names = [names[j] for j in model.joints]
dom = np.array([joint_names[prim['joints'][v][np.argmax(prim['weights'][v])]] for v in range(len(prim['positions']))])
hand_v = np.isin(dom, [h for h in joint_names if any(k in h for k in hands)])
hand_e = hand_v[edges[:, 0]] & hand_v[edges[:, 1]]
rest_world = model.world({})
rest_pts = model.skinned_positions(rest_world)[0][0]
rest_len = np.linalg.norm(rest_pts[edges[:, 0]] - rest_pts[edges[:, 1]], axis=1)
ok = rest_len > 1e-5


def rot(m):
    u, _, vt = np.linalg.svd(m[:3, :3])
    return u @ vt


def angle(a, b):
    r = a.T @ b
    return np.degrees(np.arccos(np.clip((np.trace(r) - 1) / 2, -1, 1)))


track = [head] + [n for n in joint_names if n.endswith(' Hand')] + feet
hand_joints = [n for n in joint_names if n.endswith(' Hand')]
rep = {}
for clip in model.clips:
    dur = max(model.clip_times(clip))
    times = np.arange(0, dur + 1e-6, 1 / 30) if dur > 0 else [0.0]
    low, s_all, s_hand, wrist = [], [], [], []
    rots = {n: [] for n in track}
    for t in times:
        w = model.world(model.sample(clip, float(t)))
        pts = model.skinned_positions(w)[0][0]
        low.append(float(pts[:, 1].min()))
        L = np.linalg.norm(pts[edges[:, 0]] - pts[edges[:, 1]], axis=1)
        r = L[ok] / rest_len[ok]
        s_all.append(r)
        s_hand.append(L[ok & hand_e] / rest_len[ok & hand_e])
        for n in track:
            rots[n].append(rot(w[idx[n]]))
        for h in hand_joints:
            fa = names[model.parent[idx[h]]]
            rel = rot(w[idx[fa]]).T @ rot(w[idx[h]])
            rel0 = rot(rest_world[idx[fa]]).T @ rot(rest_world[idx[h]])
            wrist.append(angle(rel0, rel))
    s_all = np.concatenate(s_all)
    s_hand = np.concatenate(s_hand) if s_hand and len(s_hand[0]) else np.array([1.0])
    jerk = {}
    for n in track:
        R = rots[n]
        step = np.array([angle(R[i], R[i + 1]) for i in range(len(R) - 1)]) if len(R) > 1 else np.zeros(1)
        jerk[n] = {'max_step': round(float(step.max()), 1),
                   'max_second_diff': round(float(np.abs(np.diff(step)).max()) if len(step) > 1 else 0.0, 1)}
    entry = {'seconds': round(float(dur), 3),
             'lowest_cm': [round(min(low) * 100, 1), round(max(low) * 100, 1)],
             'stretch_body_p1_p99_max': [round(float(np.percentile(s_all, 1)), 2),
                                         round(float(np.percentile(s_all, 99)), 2), round(float(s_all.max()), 2)],
             'stretch_hand_p99_max': [round(float(np.percentile(s_hand, 99)), 2), round(float(s_hand.max()), 2)],
             'wrist_max_deg': round(float(max(wrist)) if wrist else 0.0, 1),
             'jerk': jerk}
    if clip in ('Standing', 'Walking', 'Running'):
        w0 = model.world(model.sample(clip, 0.0))
        w1 = model.world(model.sample(clip, float(dur)))
        entry['seam_deg'] = round(max(angle(rot(w0[j]), rot(w1[j])) for j in model.joints), 2)
    rep[clip] = entry
    print(f"{clip:12s} low {entry['lowest_cm']} stretch {entry['stretch_body_p1_p99_max']} hand "
          f"{entry['stretch_hand_p99_max']} wrist {entry['wrist_max_deg']} "
          f"jerk(max step) {max(v['max_step'] for v in jerk.values())} seam {entry.get('seam_deg', '-')}")
json.dump(rep, open(out_path, 'w'), indent=1)
