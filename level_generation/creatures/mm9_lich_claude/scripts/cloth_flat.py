#!/usr/bin/env python3
"""The corpse's cloth lies on the floor. On her back MM9's arms and pelvis rest near the floor, and the sleeves' drape bones
(Box01-04) and the rear robe (XRobe1-3) hang straight through it, which would lift the whole corpse by 21 cm. In the last
pose each of these joints is turned by the smallest search angle that brings its vertices above the floor, joints in chain
order; Death ramps the turn in smoothly over its last part, Dead holds it. No other clip changes.
Usage: cloth_flat.py <in.glb> <out.glb>"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, '../claude_shared/floor')
import glb_pose, floor_fix as FF

src, dst = sys.argv[1:3]
JOINTS = ['XRobe1', 'Box04', 'Box02', 'Box03', 'Box01']
ANGLES = np.radians([6, 10, 14, 18, 22, 26, 30, 36, 42])
FLOOR = 0.012


def qmul(a, b):
    x1, y1, z1, w1 = a; x2, y2, z2, w2 = b
    return np.array([w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2, w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
                     w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2, w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2])


def slerp(a, b, w):
    if a @ b < 0:
        b = -b
    d = np.clip(a @ b, -1, 1); th = np.arccos(d)
    if th < 1e-6:
        return a
    return (np.sin((1 - w) * th) * a + np.sin(w * th) * b) / np.sin(th)


glb = glb_pose.Glb(src); model = glb_pose.Model(glb)
names = [n.get('name') for n in glb.json['nodes']]
idx = {n: i for i, n in enumerate(names)}
P = model.primitives
USE = [k for k, p in enumerate(P) if p['node'] == P[0]['node'] and p['skinned']]
jn = [names[j] for j in model.joints]
dom = np.concatenate([np.array([jn[P[k]['joints'][v][np.argmax(P[k]['weights'][v])]] for v in range(len(P[k]['positions']))]) for k in USE])
t_end = max(model.clip_times('Dead'))
local = model.sample('Dead', float(max(model.clip_times('Dead'))))


def lowest(loc, mask=None, top=False):
    w = model.world(loc); sp = model.skinned_positions(w)
    X = np.concatenate([sp[k][0] for k in USE])
    if top:
        return X[mask, 1].max()
    return X[:, 1].min() if mask is None else X[mask, 1].min()


print('Dead lowest before', round(float(lowest(local)), 3))
deltas = {}
for name in JOINTS:
    j = idx[name]
    mask = np.isin(dom, ('XRobe3',)) if name == 'XRobe1' else dom == name       # the robe by its hem: it turns from the waist
    if j not in local or not mask.any():
        continue
    q0 = local[j][1].copy()
    base = lowest(local, mask)
    if base >= FLOOR:
        continue
    ceiling = max(lowest(local, mask, True), 0.2)      # the cloth lies down: it may not rise above where it starts or the body
    best = (base, None)
    for ang in ANGLES:
        done = False
        for ax in np.eye(3):
            for sgn in (1, -1):
                dq = np.r_[ax * np.sin(sgn * ang / 2), np.cos(ang / 2)]
                trs = list(local[j]); trs[1] = qmul(q0, dq); old = local[j]; local[j] = tuple(trs)
                lo = lowest(local, mask)
                high = lowest(local, mask, True)
                local[j] = old
                if high > ceiling:
                    continue
                if lo > best[0] + 0.004:
                    best = (lo, dq)
                if lo >= FLOOR:
                    done = True
        if done:
            break
    if best[1] is not None:
        trs = list(local[j]); trs[1] = qmul(q0, best[1]); local[j] = tuple(trs)
        deltas[name] = best[1]
        print(name, 'turn deg', round(float(2 * np.degrees(np.arccos(np.clip(best[1][3], -1, 1)))), 1), 'lowest', round(float(best[0]), 3))
print('Dead lowest after', round(float(lowest(local)), 3))
death_dur = max(model.clip_times('Death'))
for clip in ('Death', 'Dead'):
    for name, dq in deltas.items():
        j = idx[name]
        sampler = FF.channel(model, clip, j, 'rotation')
        times = model.clip_times(clip)
        inputs, outputs = FF.keys_covering(model, sampler, times, 'rotation')
        outputs = np.array(outputs)
        for i, t in enumerate(inputs):
            w = 1.0 if clip == 'Dead' else np.clip((t - 0.45 * death_dur) / (0.45 * death_dur), 0, 1)
            w = w * w * (3 - 2 * w)
            full = qmul(outputs[i], dq)
            outputs[i] = slerp(outputs[i] / np.linalg.norm(outputs[i]), full / np.linalg.norm(full), w)
        sampler['output'] = glb.append_accessor(outputs, 'VEC4')
glb.write(dst)
print('written', dst)
