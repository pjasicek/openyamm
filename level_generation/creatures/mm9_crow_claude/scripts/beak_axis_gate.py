#!/usr/bin/env python3
"""Beak axis of the grafted head (gape corner -> beak tip, rigid on Xhead; its gape sits on MM9's Xbeak joint in the
bind pose and its tip is Socket_Mouth) against MM9's beak axis (Xbeak joint -> the MM9 beak tip vertex), in the Xbody
frame, every clip at 48 fps (head rework 2026-10-30). Usage: beak_axis_gate.py <mm9 glb> <our glb>"""
import sys
import numpy as np
sys.path.insert(0, __import__('os').path.join(__import__('os').path.dirname(__import__('os').path.abspath(__file__)),
                                              '..', '..', 'claude_shared', 'floor'))
from glb_pose import Glb, Model

ROLE = {'Standing': ['fly'], 'Running': ['fly'], 'Fidget': ['fidgetAir1'], 'AttackMelee': ['HattackAir1'],
        'Hit': ['winceair1'], 'Death': ['dieair1', 'fall1', 'falldown1']}
RATE = {'Running': 4 / 3}
src, ours = Model(Glb(sys.argv[1])), Model(Glb(sys.argv[2]))
ns, no = src.glb.json['nodes'], ours.glb.json['nodes']
i9 = {n['name']: i for i, n in enumerate(ns) if 'name' in n}
io = {n['name']: i for i, n in enumerate(no) if 'name' in n}
# MM9 beak tip vertex (bind)
pr = src.primitives[0]
jn = [ns[j]['name'] for j in src.joints]
dom = np.array([jn[pr['joints'][k][pr['weights'][k].argmax()]] for k in range(len(pr['positions']))])
W0 = src.world({})
P0 = src.skinned_positions(W0)[0][0]
bk = np.nonzero(np.isin(dom, ['Xbeak', 'Xjawpiv']))[0]
tip_i = bk[np.argmax(np.linalg.norm(P0[bk] - W0[i9['Xbeak']][:3, 3], axis=1))]
Wo0 = ours.world({})
gape_bind = W0[i9['Xbeak']][:3, 3]      # our gape corner sits on MM9's Xbeak joint in the bind pose (graft_head.py)


def body(W, idx):
    B = W[idx['Xbody']][:3, :3]
    return B / np.linalg.norm(B[:, 0])


def axes(t9clip, t9, role, t):
    W = src.world(src.sample(t9clip, t9)); P = src.skinned_positions(W)[0][0]
    a9 = body(W, i9).T @ (P[tip_i] - W[i9['Xbeak']][:3, 3])
    Wo = ours.world(ours.sample(role, t))
    M = Wo[io['Xhead']] @ np.linalg.inv(Wo0[io['Xhead']])
    gape = (M @ np.append(gape_bind, 1))[:3]
    ao = body(Wo, io).T @ (Wo[io['Socket_Mouth']][:3, 3] - gape)
    return a9 / np.linalg.norm(a9), ao / np.linalg.norm(ao)


for role, names in ROLE.items():
    dur = [src.clip_times(n)[-1] - src.clip_times(n)[0] for n in names]
    T = ours.clip_times(role)[-1]
    out = []
    for k in range(int(round(T * 48)) + 1):
        t = min(k / 48, T); ts = t * RATE.get(role, 1.0); ci = 0
        while ci < len(names) - 1 and ts > dur[ci] + 1e-9:
            ts -= dur[ci]; ci += 1
        a9, ao = axes(names[ci], src.clip_times(names[ci])[0] + ts, role, t)
        out.append((float(np.degrees(np.arccos(np.clip(a9 @ ao, -1, 1)))), t))
    w = max(out)
    print(f'{role:12s} beak axis vs MM9: max {w[0]:5.1f} deg at {w[1]:.2f} s, mean {np.mean([o[0] for o in out]):5.1f}')
