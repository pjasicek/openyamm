#!/usr/bin/env python3
"""Death and Dead keep the approved body exactly: the floor pass saw the now rigid plates reach lower and lifted the corpse 5 cm, so the
approved root keys come back, and each plate that would sink turns about its hinge, smoothly, by the least angle that keeps it on the floor.
Args: <in glb> <approved glb> <out glb>"""
import json, sys
from pathlib import Path
import numpy as np
from scipy.ndimage import gaussian_filter1d
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
IN, OLD, OUT = sys.argv[1:4]
g, o = Glb(IN), Glb(OLD)
AX = json.load(open(HERE / 'work' / 'skirt_axes.json'))
nm = [n.get('name') for n in g.json['nodes']]; no = [n.get('name') for n in o.json['nodes']]
an = {a['name']: a for a in g.json['animations']}; ao = {a['name']: a for a in o.json['animations']}
for c in ('Death', 'Dead'):
    for ch in an[c]['channels']:
        if ch['target']['path'] != 'translation': continue
        n = nm[ch['target']['node']]
        if n.startswith('Skirt_'): continue
        co = next(x for x in ao[c]['channels'] if no[x['target']['node']] == n and x['target']['path'] == 'translation')
        v = o.accessor(ao[c]['samplers'][co['sampler']]['output'])
        an[c]['samplers'][ch['sampler']]['output'] = g.append_accessor(v, 'VEC3')
g.write(OUT)
g = Glb(OUT); m = Model(g); nm = [n.get('name') for n in g.json['nodes']]
an = {a['name']: a for a in g.json['animations']}
pr = m.primitives[0]; jn = [nm[j] for j in m.joints]
dom = np.array([jn[pr['joints'][v][np.argmax(pr['weights'][v])]] for v in range(len(pr['positions']))])
groups = {x: np.where(dom == 'Skirt_' + x)[0] for x in AX}
def qmat(q):
    x, y, z, w = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)], [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)], [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
def qaxis(a, t):
    a = np.asarray(a) / np.linalg.norm(a); return np.r_[a * np.sin(t / 2), np.cos(t / 2)]
def qmul(a, b):
    x1, y1, z1, w1 = a; x2, y2, z2, w2 = b
    return np.array([w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2, w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2, w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2, w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2])
T = np.array(sorted(m.clip_times('Death'))); dt = (T[-1] - T[0]) / (len(T) - 1)
SPI = nm.index('Bip01 Spine')
turn = {}
for x, v in groups.items():
    bi = nm.index('Skirt_' + x); ang = []
    q0 = np.array(g.json['nodes'][bi].get('rotation', [0, 0, 0, 1]), float); aL = qmat(q0).T @ np.array(AX[x])
    for t in T:
        w = m.world(m.sample('Death', float(t))); pos = m.skinned_positions(w)[0][0][v]
        P = w[bi][:3, 3]; a = w[bi][:3, :3] @ aL; best = 0.0
        if pos[:, 1].min() < -0.003:
            K = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]])
            for d in sorted(np.radians(np.arange(-70, 71, 3.0)), key=abs):
                R = np.eye(3) + np.sin(d) * K + (1 - np.cos(d)) * K @ K
                if ((pos - P) @ R.T + P)[:, 1].min() >= -0.003: best = d; break
        ang.append(best)
    ang = np.array(ang); e = np.sign(ang) * np.maximum.accumulate(np.abs(ang))        # once on the floor it stays laid down
    e = gaussian_filter1d(e, 0.05 / dt, mode='nearest'); e[-1] = e[-3]; turn[x] = (e, aL)
    print('FLOORPLATE', x, 'max deg', round(float(np.degrees(np.abs(e).max())), 1))
for c in ('Death', 'Dead'):
    for ch in an[c]['channels']:
        n = nm[ch['target']['node']]
        if not n.startswith('Skirt_') or ch['target']['path'] != 'rotation': continue
        x = n[6:]; sm = an[c]['samplers'][ch['sampler']]; v = g.accessor(sm['output']).astype(np.float64); tk = g.accessor(sm['input']).ravel()
        e, aL = turn[x]
        new = np.array([qmul(q, qaxis(aL, np.interp(t, T, e) if c == 'Death' else e[-1])) for q, t in zip(v, tk)])
        sm['output'] = g.append_accessor(new.astype(np.float32), 'VEC4')
g.write(OUT); print('SKIRTFLOOR written')
