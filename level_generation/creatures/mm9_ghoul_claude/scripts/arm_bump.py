#!/usr/bin/env python3
"""Fingertips off the thigh by one smooth bump per arm contact (second pass, replaces hand_rest.py here: its per-key path filter left the upper arm 6.6 deg/f over MM9).
For a clip and side: the frames where the hand is inside the body; the deepest point's outward direction d at the worst key; one rotation axis for the upper arm (in its parent's frame) and one for the wrist (in the forearm's frame), both carrying the fingertips along d;
amplitude = a raised-cosine window over the contact with ramps of RAMP seconds, the same curve for both joints, solved for the least amplitude that clears the contact to under 0.8 cm. A window plus two constant axes cannot jitter; the added speed is amplitude/ramp.
The upper arm's half-rotation helper is rewritten with it. Args: <in glb> <out glb> <clip:side[:ramp]> ..."""
import json, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from pygltflib import GLTF2, Accessor, BufferView
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor')); sys.path.insert(0, str(HERE.parent / 'claude_shared')); sys.path.insert(0, str(HERE / 'scripts'))
from glb_pose import Glb, Model
from detached_parts_audit import closest_on_triangles
from outer_surface import outer_faces
src, dst, *jobs = sys.argv[1:]


def qmat(q):
    x, y, z, w = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)], [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)], [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
def qmul(a, b):
    x1, y1, z1, w1 = a; x2, y2, z2, w2 = b
    return np.array([w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2, w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2, w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2, w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2])
def qaxis(ax, a):
    return np.r_[ax * np.sin(a / 2), np.cos(a / 2)]
def qpow(q, k):
    q = q if q[3] >= 0 else -q
    ang = 2 * np.arccos(np.clip(q[3], -1, 1)); s = np.sin(ang / 2)
    ax = q[:3] / s if s > 1e-8 else np.zeros(3)
    return np.r_[ax * np.sin(ang * k / 2), np.cos(ang * k / 2)]


model = Model(Glb(src)); doc = model.glb.json
names = [n.get('name') for n in doc['nodes']]; idx = {n: i for i, n in enumerate(names)}
jn = [names[j] for j in model.joints]
P = model.primitives; USE = [k for k, pr in enumerate(P) if pr['node'] == P[0]['node'] and pr['skinned']]
tris, dom, off = [], [], 0
for k in USE:
    pr = P[k]; tris.append(pr['triangles'] + off); off += len(pr['positions'])
    dom.append(np.array([jn[pr['joints'][v][np.argmax(pr['weights'][v])]] for v in range(len(pr['positions']))]))
tris = np.concatenate(tris); dom = np.concatenate(dom)
ARM = ('Clavicle', 'UpperArm', 'Forearm', 'Hand', 'Finger', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky')
HAND = ('Hand', 'Finger', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky')
isarm = np.array([any(k in d for k in ARM) for d in dom])
rest = np.concatenate([model.skinned_positions(model.world({}))[k][0] for k in USE])
body = np.where(~isarm[tris].any(1))[0]; body = body[outer_faces(rest, tris, body)]


def skin(w):
    sp = model.skinned_positions(w); return np.concatenate([sp[k][0] for k in USE])


def depth(pts, X):
    T = X[tris[body]]; a, b, c = T[:, 0], T[:, 1], T[:, 2]
    n = np.cross(b - a, c - a); n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    _, near = cKDTree((a + b + c) / 3).query(pts, k=30)
    rp = np.repeat(pts, near.shape[1], 0)
    q, _ = closest_on_triangles(rp, a[near.ravel()], b[near.ravel()], c[near.ravel()])
    d = np.linalg.norm(rp - q, axis=1).reshape(near.shape); best = d.argmin(1); rows = np.arange(len(pts))
    cp = q.reshape(*near.shape, 3)[rows, best]; nn = n[near[rows, best]]
    side = np.einsum('ij,ij->i', pts - cp, nn)
    return np.where((side < 0) & (d[rows, best] <= 0.12), -side, 0.0), nn


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
def tracks(clip):
    an = next(a for a in g.animations if a.name == clip); tr = {}
    for ch in an.channels:
        if ch.target.path == 'rotation':
            tr[ch.target.node] = an.samplers[ch.sampler]
    return tr


report = {}
for job in jobs:
    spec = job.split(':'); clip, side = spec[0], spec[1]; RAMP = float(spec[2]) if len(spec) > 2 else 0.42
    tok = f' {side} '
    ua, fa, hd = idx[f'Bip01 {side} UpperArm'], idx[f'Bip01 {side} Forearm'], idx[f'Bip01 {side} Hand']
    uh = idx[f'Bip01 {side} UpperArm_h']
    hv = np.where(np.array([tok in d and any(k in d for k in HAND) for d in dom]))[0]
    tr = tracks(clip); ts = acc(tr[ua].input)[:, 0]
    Qua, Qh, Quh = acc(tr[ua].output).copy(), acc(tr[hd].output).copy(), acc(tr[uh].output).copy()
    pa = model.parent[ua]
    rest_q = np.array(doc['nodes'][ua].get('rotation', [0, 0, 0, 1]), float)
    dur = ts[-1]; tf = np.arange(0, dur + 1e-6, 1 / 96)      # the hand sweeps past the knee between 30 fps keys
    dep = np.zeros(len(tf)); dirs = np.zeros((len(tf), 3)); tips = np.zeros((len(tf), 3))
    for k, t in enumerate(tf):
        w = model.world(model.sample(clip, float(t))); X = skin(w)
        d_, nn = depth(X[hv], X); i = int(d_.argmax()); dep[k] = d_[i]; dirs[k] = nn[i]; tips[k] = X[hv[i]]
    cont = dep > 0.012
    print('DEPTH', clip, side, 'series cm', [round(float(x) * 100, 1) for x in dep[::6]], flush=True)
    if not cont.any():
        print('BUMP', clip, side, 'no contact'); continue
    k0, k1 = np.where(cont)[0][[0, -1]]; kw = int(dep.argmax())
    w = model.world(model.sample(clip, float(tf[kw])))
    S, W = w[ua][:3, 3], w[hd][:3, 3]; tip = tips[kw]
    # always straight out to the side of the hips: the contact normals of a long pass disagree and one key's normal drove the hand into the next contact
    lat = w[idx['Bip01 L Thigh']][:3, 3] - w[idx['Bip01 R Thigh']][:3, 3]; lat /= np.linalg.norm(lat)
    d = lat if side == 'L' else -lat
    def frame(n):
        r = w[n][:3, :3]; return r / np.linalg.norm(r, axis=0)
    t0, t1 = tf[k0], tf[k1]
    Rin = max(min(RAMP, t0 - 0.02), 0.1); Rout = max(min(RAMP, dur - t1 - 0.03), 0.1)      # back on MM9's pose before the clip's last key
    def window(t):
        u = np.clip((t - (t0 - Rin)) / Rin, 0, 1); v = np.clip(((t1 + Rout) - t) / Rout, 0, 1)
        return (0.5 - 0.5 * np.cos(np.pi * u)) * (0.5 - 0.5 * np.cos(np.pi * v))
    def frame(n):
        r = w[n][:3, :3]; return r / np.linalg.norm(r, axis=0)
    span = [float(t) for t in tf[::2] if window(t) > 0]
    best = None
    for sgn in (1, -1):
        dd = d * sgn
        a1 = np.cross(tip - S, dd); a1 /= max(np.linalg.norm(a1), 1e-9)
        a2 = np.cross(tip - W, dd); a2 /= max(np.linalg.norm(a2), 1e-9)
        axu = frame(pa).T @ a1; axh = frame(fa).T @ a2       # constant in the parents' frames
        for amp in np.radians(np.arange(3, 30, 3)):
            worst = 0.0
            for tq in span:
                loc = model.sample(clip, tq)
                b = window(tq) * amp
                q1 = qmul(qaxis(axu, b * 0.6), loc[ua][1]); q2 = qmul(qaxis(axh, b), loc[hd][1])
                l2 = dict(loc); l2[ua] = (loc[ua][0], q1) + tuple(loc[ua][2:]); l2[hd] = (loc[hd][0], q2) + tuple(loc[hd][2:])
                r_ = rest_q * np.array([-1, -1, -1, 1]); l2[uh] = (loc[uh][0], qmul(rest_q, qpow(qmul(r_, q1), 0.5))) + tuple(loc[uh][2:])
                X = skin(model.world(l2)); worst = max(worst, depth(X[hv], X)[0].max())
            score = (round(max(worst, 0.006), 4), amp)         # the least amplitude among equal results
            if best is None or score < best[0]:
                best = (score, sgn, float(np.degrees(amp)), float(worst), axu, axh)
            if worst < 0.006: break
    _, sgn, ampd, wc, ax_ua, ax_hd = best
    best = (ampd, wc)
    amp = np.radians(ampd)
    for k, t in enumerate(ts):
        b = window(t) * amp
        Qua[k] = qmul(qaxis(ax_ua, b * 0.6), Qua[k]); Qh[k] = qmul(qaxis(ax_hd, b), Qh[k])
        r_ = rest_q * np.array([-1, -1, -1, 1]); Quh[k] = qmul(rest_q, qpow(qmul(r_, Qua[k]), 0.5))
    tr[ua].output = put(Qua); tr[hd].output = put(Qh); tr[uh].output = put(Quh)
    report[f'{clip}:{side}'] = dict(before_cm=round(float(dep.max()) * 100, 1), window=[round(float(t0), 2), round(float(t1), 2)], amp_deg=best[0], after_cm=round(best[1] * 100, 1), sign=sgn)
    print('BUMP', clip, side, report[f'{clip}:{side}'], flush=True)
    # following jobs read the corrected clip: write through
    g.buffers[0].byteLength = len(blob); g.set_binary_blob(bytes(blob)); g.save(dst)
    model = Model(Glb(dst)); doc = model.glb.json
# neighbouring keys of q and -q make a linear sampler swing the long way between them: a one-frame spike between clean keys (the thumb into the thigh at 0.8125 s)
fixed = 0
for an in g.animations:
    for ch in an.channels:
        if ch.target.path != 'rotation': continue
        sm = an.samplers[ch.sampler]; Q = acc(sm.output)
        flip = (Q[1:] * Q[:-1]).sum(1) < 0
        if flip.any():
            Q = Q.copy()
            for i in range(1, len(Q)):
                if (Q[i] * Q[i - 1]).sum() < 0: Q[i] = -Q[i]
            sm.output = put(Q); fixed += 1
print('SIGNS fixed', fixed)
g.buffers[0].byteLength = len(blob); g.set_binary_blob(bytes(blob)); g.save(dst)
json.dump(report, open(HERE / 'work' / 'arm_bump.json', 'w'), indent=1)
