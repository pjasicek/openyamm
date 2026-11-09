#!/usr/bin/env python3
"""Arm proportions and alignment of a Honk GLB, per clip, against the MM9 source. Prints at bind: face length (chin to hairline), hand length and width, forearm radius along
the forearm, wrist position; per clip: the wrist bend (forearm line against hand line) ours and MM9, how far the forearm's end sits from the sleeve cuff's centre.
Args: <glb> <mm9 source glb> <role map json: clip -> mm9 clip> [--unmirrored-source]"""
import json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
glb, src, rolej = sys.argv[1:4]
m = Model(Glb(glb)); d = m.glb.json; nd = [n.get('name', '') for n in d['nodes']]
names = [d['nodes'][j]['name'] for j in d['skins'][0]['joints']]
ps = [p for p in m.primitives if p['skinned']]
off = np.cumsum([0] + [len(p['positions']) for p in ps])
J = np.vstack([p['joints'] for p in ps]); W = np.vstack([p['weights'] for p in ps]); P = np.vstack([p['positions'] for p in ps])
T = np.vstack([p['triangles'] + off[i] for i, p in enumerate(ps)])
dom = J[np.arange(len(J)), W.argmax(1)]
mat = np.concatenate([np.full(len(p['positions']), i) for i, p in enumerate(ps)])


def skin(w):
    pal = w[m.joints] @ m.inverse_binds
    b = np.einsum('vk,vkij->vij', W, pal[J])
    return np.einsum('vij,vj->vi', b, np.c_[P, np.ones(len(P))])[:, :3]


w0 = m.world({})
pos = lambda w, n: w[nd.index(n)][:3, 3]
print('--- bind')
head = np.isin(dom, [names.index(n) for n in names if n == 'Bip01 Head']) & (mat == 1)
print('head verts height', P[head, 1].min().round(3), P[head, 1].max().round(3))
for s in 'LR':
    e, wr, mid, tip = (pos(w0, f'Bip01 {s} {b}') for b in ('Forearm', 'Hand', 'Middle1', 'Middle3'))
    ids = [names.index(n) for n in names if f' {s} ' in n and any(k in n for k in ('Hand', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky'))]
    hv = np.isin(dom, ids) & (mat == 1)
    axis = (mid - wr) / np.linalg.norm(mid - wr)
    al = (P[hv] - wr) @ axis
    perp = (P[hv] - wr) - np.outer(al, axis)
    fa = (wr - e); L = np.linalg.norm(fa); fa /= L
    print(s, 'upper', round(float(np.linalg.norm(e - pos(w0, f'Bip01 {s} UpperArm'))), 3), 'forearm len', round(float(L), 3), 'hand length (wrist to farthest along)', round(float(al.max()), 3), 'width', round(float(2 * np.percentile(np.abs(perp @ np.cross(axis, fa) / max(np.linalg.norm(np.cross(axis, fa)), 1e-6)), 97)), 3), 'bind wrist bend deg', round(float(np.degrees(np.arccos(np.clip(axis @ fa, -1, 1)))), 1))
    # forearm skin: hand-material verts on the forearm side of the wrist
    fid = names.index(f'Bip01 {s} Forearm')
    fs = np.where((mat == 1) & (((P - wr) @ fa) < 0.01) & (((P - e) @ fa) > -0.02) & (np.linalg.norm(np.cross(P - wr, fa), axis=1) < 0.08))[0]
    if len(fs):
        at = (P[fs] - e) @ fa / L
        rr = np.linalg.norm(np.cross(P[fs] - wr, fa), axis=1)
        print('   forearm skin radius cm by t(0 elbow..1 wrist):', [(round(float(a), 1), round(float(rr[(at > a - .1) & (at <= a + .1)].mean()) * 100, 1)) for a in (.3, .5, .7, .9, 1.0) if ((at > a - .1) & (at <= a + .1)).any()], 'axis offset cm', round(float(np.linalg.norm((P[fs] - (e + np.outer((P[fs] - e) @ fa, fa))).mean(0))) * 100, 1))
ms = Model(Glb(src)); nds = [n.get('name', '') for n in ms.glb.json['nodes']]
role = json.load(open(rolej))
print('--- clips: wrist bend deg ours/MM9 L, R; hand dir error to the MM9 bend; cuff centre to forearm line cm L, R')
# cuff ring: sleeve body-material verts on the Forearm side with the largest projection along the forearm
for clip, srcclip in role.items():
    if clip not in m.clips or srcclip not in ms.clips:
        continue
    dur = m.clip_times(clip)[-1]
    row = {'L': [], 'R': []}
    for t in np.linspace(0, dur, 7):
        w = m.world(m.sample(clip, float(t)))
        st = float(t) / dur * ms.clip_times(srcclip)[-1]
        ws = ms.world(ms.sample(srcclip, st))
        for s in 'LR':
            e, wr, mid = (w[nd.index(f'Bip01 {s} {b}')][:3, 3] for b in ('Forearm', 'Hand', 'Middle1'))
            f, h = wr - e, mid - wr
            a = np.degrees(np.arccos(np.clip(f @ h / np.linalg.norm(f) / np.linalg.norm(h), -1, 1)))
            e2, wr2, mid2 = (ws[nds.index(f'Bip01 {s} {b}')][:3, 3] for b in ('Forearm', 'Hand', 'Finger1'))
            f2, h2 = wr2 - e2, mid2 - wr2
            a2 = np.degrees(np.arccos(np.clip(f2 @ h2 / np.linalg.norm(f2) / np.linalg.norm(h2), -1, 1)))
            row[s].append((a, a2))
    print(f"{clip:13} L ours {np.mean([x[0] for x in row['L']]):5.1f} max {np.max([x[0] for x in row['L']]):5.1f} MM9 {np.mean([x[1] for x in row['L']]):5.1f} | R ours {np.mean([x[0] for x in row['R']]):5.1f} max {np.max([x[0] for x in row['R']]):5.1f} MM9 {np.mean([x[1] for x in row['R']]):5.1f}")
# cuff in Standing
w = m.world(m.sample('Standing', 0.5)); X = skin(w)
for s in 'LR':
    e, wr = w[nd.index(f'Bip01 {s} Forearm')][:3, 3], w[nd.index(f'Bip01 {s} Hand')][:3, 3]
    fa = (wr - e) / np.linalg.norm(wr - e)
    ids = [names.index(f'Bip01 {s} Forearm'), names.index(f'Bip01 {s} Hand')]
    v = np.isin(dom, ids) & (mat == 0)
    al = (X - wr) @ fa
    far = v & (al > np.percentile(al[v], 85))
    c = X[far].mean(0)
    r = np.linalg.norm((X[far] - c), axis=1)
    off_ = (c - wr) - fa * ((c - wr) @ fa)
    print(s, 'Standing cuff centre', c.round(3).tolist(), 'radius', round(float(np.median(r)), 3), 'wrist', wr.round(3).tolist(), 'centre off the forearm line cm', round(float(np.linalg.norm(off_)) * 100, 1), 'cuff past wrist cm', round(float((c - wr) @ fa) * 100, 1))
