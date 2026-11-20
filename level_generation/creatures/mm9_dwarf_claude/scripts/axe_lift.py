#!/usr/bin/env python3
"""The axe off the shoulder (run 2): in Fidget the dwarf rests the axe on his right shoulder and, after arm_bump.py lifts that arm off the hip, the haft
lies 6 cm in the upper arm. One raised-cosine bump of the right wrist over the contact (ramps RAMP s, window from blade_gate.py's test), about the axis
that carries the axe's far end out along the body's normal at the deepest point; the least amplitude (steps of 2 deg, at most MAXDEG) that keeps the axe
within TOL of the skin. The fist turns with the axe, so the grip does not change. Constant axis and one window: nothing to jitter.
Args: <in glb> <out glb> <clip> ..."""
import json, os, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from pygltflib import GLTF2, Accessor, BufferView
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor')); sys.path.insert(0, str(HERE.parent / 'claude_shared'))
from glb_pose import Glb, Model
from detached_parts_audit import closest_on_triangles
src, dst, *clips = sys.argv[1:]
RAMP, MAXDEG, TOL = 0.3, float(os.environ.get('AXE_MAXDEG', 30)), 0.008


def qmul(a, b):
    x1, y1, z1, w1 = a; x2, y2, z2, w2 = b
    return np.array([w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2, w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2, w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2, w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2])
def qaxis(ax, a): return np.r_[ax * np.sin(a / 2), np.cos(a / 2)]


m = Model(Glb(src)); doc = m.glb.json
names = [n.get('name') for n in doc['nodes']]; ix = {n: i for i, n in enumerate(names)}; jn = [names[j] for j in m.joints]
P = [p for p in m.primitives if p['node'] == m.primitives[0]['node'] and p['skinned']]
tri, dom, off = [], [], 0
for p in P:
    tri.append(p['triangles'] + off); off += len(p['positions'])
    dom.append(np.array([jn[p['joints'][v][np.argmax(p['weights'][v])]] for v in range(len(p['positions']))]))
tri = np.concatenate(tri); dom = np.concatenate(dom)
item = dom == 'RHand1'
hand = np.array([any(k in d for k in (' R Hand', ' R Finger', ' R Thumb', ' R Index', ' R Middle', ' R Ring', ' R Pinky')) for d in dom])
body_f = np.where(~(item[tri].any(1) | hand[tri].any(1) | np.isin(dom, ['LHand1'])[tri].any(1)))[0]
uvs = np.concatenate([np.asarray(m.glb.accessor(pr['attributes']['TEXCOORD_0'])) for pr in doc['meshes'][doc['nodes'][m.primitives[0]['node']]['mesh']]['primitives'][:len(P)]])
ua = uvs[tri]; uvarea = np.abs((ua[:, 1, 0] - ua[:, 0, 0]) * (ua[:, 2, 1] - ua[:, 0, 1]) - (ua[:, 2, 0] - ua[:, 0, 0]) * (ua[:, 1, 1] - ua[:, 0, 1]))
body_f = body_f[uvarea[body_f] > 1e-9]                    # the dark linings (one texel) are not skin (blade_gate.py)
iv = np.where(item)[0]
X0_ = np.concatenate([p['positions'] for p in P])[iv]; ax0 = np.linalg.svd(X0_ - X0_.mean(0))[2][0]; tt = X0_ @ ax0
E0, E1 = iv[tt.argmin()], iv[tt.argmax()]                 # the haft's long faces have no inner points: a line of samples (blade_gate.py)
HD = ix['Bip01 R Hand']; FA = m.parent[HD]


def skin(loc):
    return np.concatenate([x for x, _ in m.skinned_positions(m.world(loc))[:len(P)]])


def depth(X):
    pts = np.vstack([X[iv], X[E0] + np.outer(np.linspace(0, 1, 240), X[E1] - X[E0])]); T = X[tri[body_f]]; a, b, c = T[:, 0], T[:, 1], T[:, 2]
    n = np.cross(b - a, c - a); n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    _, near = cKDTree((a + b + c) / 3).query(pts, k=16)
    q, _ = closest_on_triangles(np.repeat(pts, 16, 0), a[near.ravel()], b[near.ravel()], c[near.ravel()])
    d = np.linalg.norm(np.repeat(pts, 16, 0) - q, axis=1).reshape(near.shape); best = d.argmin(1); rows = np.arange(len(pts))
    side = np.einsum('ij,ij->i', pts - q.reshape(*near.shape, 3)[rows, best], n[near[rows, best]])
    dep = np.where((side < 0) & (d[rows, best] <= 0.06) & (np.abs(side) > 0.9 * d[rows, best]), d[rows, best], 0.0)
    i = int(dep.argmax())
    return float(dep.max()), n[near[i, best[i]]], pts[i]


g = GLTF2().load(src); blob = bytearray(g.binary_blob())
def acc(i):
    a = g.accessors[i]; bv = g.bufferViews[a.bufferView]; k = {'SCALAR': 1, 'VEC4': 4, 'VEC3': 3}[a.type]
    return np.frombuffer(bytes(blob), 'f4', a.count * k, (bv.byteOffset or 0) + (a.byteOffset or 0)).reshape(a.count, k).astype(np.float64)
def put(arr):
    global blob
    while len(blob) % 4: blob.append(0)
    o_ = len(blob); d_ = np.asarray(arr, 'f4').tobytes(); blob += d_
    g.bufferViews.append(BufferView(buffer=0, byteOffset=o_, byteLength=len(d_)))
    g.accessors.append(Accessor(bufferView=len(g.bufferViews) - 1, componentType=5126, count=len(arr), type='VEC4'))
    return len(g.accessors) - 1


rep = {}
for clip in clips:
    an = next(a for a in g.animations if a.name == clip)
    ch = next(c for c in an.channels if c.target.node == HD and c.target.path == 'rotation'); sm = an.samplers[ch.sampler]
    ts = acc(sm.input)[:, 0]; Q = acc(sm.output).copy(); dur = ts[-1]
    tf = np.arange(0, dur + 1e-6, 1 / 48); dep = np.zeros(len(tf)); worst = None
    for k, t in enumerate(tf):
        d_, n_, p_ = depth(skin(m.sample(clip, float(t)))); dep[k] = d_
        if worst is None or d_ > worst[0]: worst = (d_, k, n_, p_)
    if worst[0] < TOL:
        rep[clip] = dict(before_cm=round(worst[0] * 100, 1), amp_deg=0); print('AXE', clip, rep[clip]); continue
    on = np.where(dep > TOL)[0]; t0, t1 = tf[on[0]], tf[on[-1]]
    Rin = max(min(RAMP, t0 - 0.02), 0.1); Rout = max(min(RAMP, dur - t1 - 0.03), 0.1)
    def window(t):
        u = np.clip((t - (t0 - Rin)) / Rin, 0, 1); v = np.clip(((t1 + Rout) - t) / Rout, 0, 1)
        return (0.5 - 0.5 * np.cos(np.pi * u)) * (0.5 - 0.5 * np.cos(np.pi * v))
    w = m.world(m.sample(clip, float(tf[worst[1]])))
    W_ = w[HD][:3, 3]; ax_w = np.cross(worst[3] - W_, worst[2]); ax_w /= np.linalg.norm(ax_w)
    Fr = w[FA][:3, :3] / np.linalg.norm(w[FA][:3, :3], axis=0); ax = Fr.T @ ax_w     # constant in the forearm's frame
    span = [float(t) for t in tf if window(t) > 0]
    best = None
    for sgn in (1, -1):
        for amp in np.radians(np.arange(2, MAXDEG + 1e-6, 2)):
            wc = 0.0
            for tq in span:
                loc = m.sample(clip, tq); l2 = dict(loc); tr = l2[HD]
                l2[HD] = [tr[0], qmul(qaxis(ax, sgn * amp * window(tq)), tr[1]), tr[2]]
                wc = max(wc, depth(skin(l2))[0])
            if best is None or (round(max(wc, TOL), 4), amp) < best[0]: best = ((round(max(wc, TOL), 4), amp), sgn, amp, wc)
            if wc < TOL: break
        if best[3] < TOL: break
    _, sgn, amp, wc = best
    for k, t in enumerate(ts): Q[k] = qmul(qaxis(ax, sgn * amp * window(t)), Q[k])
    for k in range(1, len(Q)):
        if Q[k] @ Q[k - 1] < 0: Q[k] = -Q[k]
    sm.output = put(Q)
    rep[clip] = dict(before_cm=round(worst[0] * 100, 1), window=[round(float(t0), 2), round(float(t1), 2)], amp_deg=round(float(np.degrees(amp)), 1), after_cm=round(wc * 100, 1))
    print('AXE', clip, rep[clip], flush=True)
g.buffers[0].byteLength = len(blob); g.set_binary_blob(bytes(blob)); g.save(dst)
json.dump(rep, open(HERE / 'work' / 'axe_lift.json', 'w'), indent=1)
