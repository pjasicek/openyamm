#!/usr/bin/env python3
"""Cutlass tip off the floor and the blade off the thigh (run 2). MM9's Hattack1 ends its swing with the tip 9 cm under the floor and the blade
5 cm into the right thigh (0.4 s). Per job: the frames (96 fps) where the tip is under FLOOR or the blade is inside the body; one constant
axis in the forearm's frame that turns the blade up at the worst frame; a raised-cosine window over those frames with RAMP s ramps; the
least amplitude (1 deg steps) that clears both. One window and one axis cannot jitter. The wrist only: the swing of the arm stays MM9's.
Args: <in glb> <out glb> <clip:side[:ramp]> ..."""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from pygltflib import GLTF2, Accessor, BufferView
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor')); sys.path.insert(0, str(HERE.parent / 'claude_shared'))
from glb_pose import Glb, Model
from detached_parts_audit import closest_on_triangles
src, dst, *jobs = sys.argv[1:]
FLOOR = 0.01
def qmul(a, b):
    x1, y1, z1, w1 = a; x2, y2, z2, w2 = b
    return np.array([w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2, w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2, w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2, w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2])
def qaxis(ax, a): return np.r_[ax * np.sin(a / 2), np.cos(a / 2)]
g = GLTF2().load(src); blob = bytearray(g.binary_blob())
def acc(i):
    a = g.accessors[i]; bv = g.bufferViews[a.bufferView]; n = {'SCALAR': 1, 'VEC4': 4, 'VEC3': 3}[a.type]
    return np.frombuffer(bytes(blob), 'f4', a.count * n, (bv.byteOffset or 0) + (a.byteOffset or 0)).reshape(a.count, n).astype(np.float64)
def put(arr):
    global blob
    while len(blob) % 4: blob.append(0)
    o_ = len(blob); d = np.asarray(arr, 'f4').tobytes(); blob += d
    g.bufferViews.append(BufferView(buffer=0, byteOffset=o_, byteLength=len(d)))
    g.accessors.append(Accessor(bufferView=len(g.bufferViews) - 1, componentType=5126, count=len(arr), type='VEC4'))
    return len(g.accessors) - 1
for job in jobs:
    m = Model(Glb(dst if Path(dst).exists() and job != jobs[0] else src)); doc = m.glb.json
    names = [n.get('name') for n in doc['nodes']]; ix = {n: i for i, n in enumerate(names)}; jn = [names[j] for j in m.joints]
    P = [p for p in m.primitives if p['node'] == m.primitives[0]['node'] and p['skinned']]
    tri = np.vstack([p['triangles'] + o for p, o in zip(P, np.cumsum([0] + [len(p['positions']) for p in P]))])
    dom = np.concatenate([np.array([jn[p['joints'][v][np.argmax(p['weights'][v])]] for v in range(len(p['positions']))]) for p in P])
    spec = job.split(':'); clip, side = spec[0], spec[1]; RAMP = float(spec[2]) if len(spec) > 2 else 0.15
    tok = f' {side} '
    item = dom == 'Bone07'; hand = np.array([tok in d and any(k in d for k in ('Hand', 'Finger', 'Forearm')) for d in dom])
    body_f = np.where(~(item[tri].any(1) | hand[tri].any(1)))[0]; iv = np.where(item)[0]
    def skin(w):
        sp = m.skinned_positions(w); return np.concatenate([s[0] for s in sp[:len(P)]])
    def measure(X):
        low = float(X[iv, 1].min())
        T = X[tri[body_f]]; a, b, c = T[:, 0], T[:, 1], T[:, 2]; n = np.cross(b - a, c - a); n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
        pts = X[iv]; _, near = cKDTree((a + b + c) / 3).query(pts, k=16); rp = np.repeat(pts, 16, 0)
        q, _ = closest_on_triangles(rp, a[near.ravel()], b[near.ravel()], c[near.ravel()]); d = np.linalg.norm(rp - q, axis=1).reshape(near.shape)
        best = d.argmin(1); r = np.arange(len(pts)); s_ = np.einsum('ij,ij->i', pts - q.reshape(*near.shape, 3)[r, best], n[near[r, best]])
        dep = np.where((s_ < 0) & (d[r, best] <= .06) & (np.abs(s_) > .9 * d[r, best]), d[r, best], 0.)
        return max(FLOOR - low, 0.), float(dep.max())
    hd, fa = ix[f'Bip01 {side} Hand'], ix[f'Bip01 {side} Forearm']
    an = next(a for a in g.animations if a.name == clip); tr = {c.target.node: an.samplers[c.sampler] for c in an.channels if c.target.path == 'rotation'}
    ts = acc(tr[hd].input)[:, 0]; Qh = acc(tr[hd].output).copy(); dur = ts[-1]
    tf = np.arange(0, dur + 1e-6, 1 / 96); bad = np.zeros(len(tf))
    for k, t in enumerate(tf):
        fl, bl = measure(skin(m.world(m.sample(clip, float(t))))); bad[k] = max(fl, bl)
    cont = bad > .004
    if not cont.any(): print('TIP', clip, side, 'clear'); continue
    k0, k1 = np.where(cont)[0][[0, -1]]; kw = int(bad.argmax())
    w = m.world(m.sample(clip, float(tf[kw]))); X = skin(w)
    tipv = iv[np.argmax(np.linalg.norm(X[iv] - w[hd][:3, 3], axis=1))]; blade = X[tipv] - w[hd][:3, 3]; blade /= np.linalg.norm(blade)
    up = np.array([0, 1., 0]); ax = np.cross(blade, up); ax /= np.linalg.norm(ax)     # turns the tip toward +y
    rf = w[fa][:3, :3]; rf = rf / np.linalg.norm(rf, axis=0); axl = rf.T @ ax
    t0, t1 = tf[k0], tf[k1]; Rin = max(min(RAMP, t0), .06); Rout = max(min(RAMP, dur - t1 - .02), .06)
    def window(t):
        u = np.clip((t - (t0 - Rin)) / Rin, 0, 1); v = np.clip(((t1 + Rout) - t) / Rout, 0, 1); return (.5 - .5 * np.cos(np.pi * u)) * (.5 - .5 * np.cos(np.pi * v))
    span = [float(t) for t in tf if window(t) > 0]
    best = None
    for amp in np.radians(np.arange(1, 31)):
        worst = 0.
        for tq in span[::2]:
            loc = m.sample(clip, tq); l2 = dict(loc); r = loc[hd]
            l2[hd] = [r[0], qmul(qaxis(axl, window(tq) * amp), r[1]), r[2]]   # rotation in the hand's parent (forearm) frame
            worst = max(worst, *measure(skin(m.world(l2))))
        if best is None or worst < best[1] - 1e-4: best = (amp, worst)
        if worst < .004: break
    amp = best[0]
    for k, t in enumerate(ts): Qh[k] = qmul(qaxis(axl, window(t) * amp), Qh[k])
    tr[hd].output = put(Qh)
    print('TIP', clip, side, {'before_cm': round(float(bad.max()) * 100, 1), 'window': [round(float(t0), 3), round(float(t1), 3)], 'amp_deg': round(float(np.degrees(amp)), 1), 'after_cm': round(best[1] * 100, 1)}, flush=True)
    g.buffers[0].byteLength = len(blob); g.set_binary_blob(bytes(blob)); g.save(dst)
g.buffers[0].byteLength = len(blob); g.set_binary_blob(bytes(blob)); g.save(dst)
