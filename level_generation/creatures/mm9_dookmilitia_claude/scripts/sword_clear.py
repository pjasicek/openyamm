#!/usr/bin/env python3
"""The held sword and its hand off the head and body by one smooth bump of the arm (run 2: Cower's hilt went 5.6 cm into
the head, the right hand 2.5 cm into it).

For a clip and side: the frames where the sword (blade_gate.py's points: its faces' corners and centres plus a line along
the blade) or the hand is inside the skin; one rotation axis for the upper arm (in its parent's frame) and one for the
wrist (in the forearm's frame), both carrying the deepest point along d, d either straight away from the head's centre
or along the contact normal. Amplitude = a raised-cosine window over the contact with ramps of RAMP seconds, the same
curve for both joints (upper arm 0.6 of it), solved for the least amplitude that leaves under 0.5 cm. A window and two
constant axes cannot jitter. The upper arm's half-rotation helper is rewritten with it, as arm_bump.py does.
Args: <in glb> <out glb> <clip:side[:ramp]> ..."""
import json, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from pygltflib import GLTF2, Accessor, BufferView
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor')); sys.path.insert(0, str(HERE.parent / 'claude_shared'))
from glb_pose import Glb, Model
from detached_parts_audit import closest_on_triangles
sys.path.insert(0, str(HERE / 'scripts'))
from outer_surface import outer_faces
src, dst, *jobs = sys.argv[1:]
ITEM = 'Ybasesword'
HAND = ('Hand', 'Finger', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky')
ARM = ('Clavicle', 'UpperArm', 'Forearm') + HAND
BARY = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1], [1 / 3, 1 / 3, 1 / 3]])


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


class Scene:
    def __init__(self, path, side):
        self.m = m = Model(Glb(path)); doc = m.glb.json
        self.names = [n.get('name') for n in doc['nodes']]; jn = [self.names[j] for j in m.joints]
        P = m.primitives; self.USE = [k for k, pr in enumerate(P) if pr['node'] == P[0]['node'] and pr['skinned']]
        tri, dom, uvs, off = [], [], [], 0
        for k in self.USE:
            pr = P[k]; tri.append(pr['triangles'] + off); off += len(pr['positions'])
            dom.append(np.array([jn[pr['joints'][v][np.argmax(pr['weights'][v])]] for v in range(len(pr['positions']))]))
        self.tri = tri = np.concatenate(tri); self.dom = dom = np.concatenate(dom)
        for pr in doc['meshes'][0]['primitives'][:len(self.USE)]:
            uvs.append(np.asarray(m.glb.accessor(pr['attributes']['TEXCOORD_0'])))
        ua = np.concatenate(uvs)[tri]
        uvarea = np.abs((ua[:, 1, 0] - ua[:, 0, 0]) * (ua[:, 2, 1] - ua[:, 0, 1]) - (ua[:, 2, 0] - ua[:, 0, 0]) * (ua[:, 1, 1] - ua[:, 0, 1]))
        tok = f' {side} '
        item = dom == ITEM; other = np.isin(dom, ['Ybasesword', 'Ybasedagger'])
        hand = np.array([tok in d and any(k in d for k in HAND) for d in dom])
        self.body_s = np.where(~(item[tri].any(1) | hand[tri].any(1) | other[tri].any(1)) & (uvarea > 1e-9))[0]      # as blade_gate.py
        ARMG = ARM + ('Twist',); arm = np.array([tok in d and any(k in d for k in ARMG) for d in dom])
        wv_ = np.char.startswith(dom.astype(str), 'Ybase')
        bh = np.where(~(arm[tri].any(1) | wv_[tri].any(1)))[0]     # as arm_hand_gate.py --outer-only --exact
        self.itf = np.where(item[tri].all(1))[0]
        self.hv = np.where(hand | np.array([tok in d and 'Forearm' in d for d in dom]))[0]
        rest = np.concatenate([p['positions'] for p in (P[k] for k in self.USE)])
        self.body_h = bh[outer_faces(rest, tri, bh)]
        iv = np.where(item)[0]; ax = np.linalg.svd(rest[iv] - rest[iv].mean(0))[2][0]; tt = rest[iv] @ ax
        self.ends = iv[[tt.argmin(), tt.argmax()]]
        self.head = self.names.index('Bip01 Head')

    def skin(self, w):
        sp = self.m.skinned_positions(w); return np.concatenate([sp[k][0] for k in self.USE])

    @staticmethod
    def inside(pts, X, faces, tri, reach, cone=True):
        T = X[tri[faces]]; a, b, c = T[:, 0], T[:, 1], T[:, 2]
        n = np.cross(b - a, c - a); n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
        K = 16 if cone else 40
        _, near = cKDTree((a + b + c) / 3).query(pts, k=K)
        rp = np.repeat(pts, K, 0)
        q, _ = closest_on_triangles(rp, a[near.ravel()], b[near.ravel()], c[near.ravel()])
        d = np.linalg.norm(rp - q, axis=1).reshape(near.shape); best = d.argmin(1); rows = np.arange(len(pts))
        nn = n[near[rows, best]]; side = np.einsum('ij,ij->i', pts - q.reshape(*near.shape, 3)[rows, best], nn)
        db = d[rows, best]
        if not cone:
            return np.where((side < 0) & (db <= reach), -side, 0.0), nn
        return np.where((side < 0) & (db <= reach) & (np.abs(side) > 0.9 * db), db, 0.0), nn

    def depth(self, w):
        """deepest point of sword or hand inside the skin: (depth, point, contact normal)"""
        X = self.skin(w)
        pts = np.einsum('kb,fbc->fkc', BARY, X[self.tri[self.itf]]).reshape(-1, 3)
        e = X[self.ends]; pts = np.vstack([pts, e[0] + np.outer(np.linspace(0, 1, 240), e[1] - e[0])])
        ds, ns = self.inside(pts, X, self.body_s, self.tri, 0.06)
        dh, nh = self.inside(X[self.hv], X, self.body_h, self.tri, 0.06, cone=False)
        if ds.max() >= dh.max():
            i = int(ds.argmax()); return float(ds[i]), pts[i], ns[i]
        i = int(dh.argmax()); return float(dh[i]), X[self.hv][i], nh[i]


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
    an = next(a for a in g.animations if a.name == clip); return {ch.target.node: an.samplers[ch.sampler] for ch in an.channels if ch.target.path == 'rotation'}


report = {}
cur = src
for job in jobs:
    spec = job.split(':'); clip, side = spec[0], spec[1]; RAMP = float(spec[2]) if len(spec) > 2 else 0.35
    S_ = Scene(cur, side); m = S_.m; doc = m.glb.json; idx = {n: i for i, n in enumerate(S_.names)}
    ua, fa, hd, uh = (idx[f'Bip01 {side} {k}'] for k in ('UpperArm', 'Forearm', 'Hand', 'UpperArm_h'))
    pa = m.parent[ua]; rest_q = np.array(doc['nodes'][ua].get('rotation', [0, 0, 0, 1]), float)
    dur = max(m.clip_times(clip)); tf = np.arange(0, dur + 1e-6, 1 / 48)
    dep = np.zeros(len(tf)); tips = np.zeros((len(tf), 3)); nrm = np.zeros((len(tf), 3))
    for k, t in enumerate(tf):
        dep[k], tips[k], nrm[k] = S_.depth(m.world(m.sample(clip, float(t))))
    print('DEPTH', clip, side, 'cm', [round(float(x) * 100, 1) for x in dep[::6]], flush=True)
    cont = dep > 0.008
    if not cont.any():
        print('CLEAR', clip, side, 'no contact'); continue
    k0, k1 = np.where(cont)[0][[0, -1]]; kw = int(dep.argmax())
    w = m.world(m.sample(clip, float(tf[kw])))
    S, Wp, H = w[ua][:3, 3], w[hd][:3, 3], w[S_.head][:3, 3]; tip = tips[kw]
    t0, t1 = tf[k0], tf[k1]
    Rin = max(min(RAMP, t0 - 0.02), 0.1); Rout = max(min(RAMP, dur - t1 - 0.03), 0.1)
    def window(t):
        u = np.clip((t - (t0 - Rin)) / Rin, 0, 1); v = np.clip(((t1 + Rout) - t) / Rout, 0, 1)
        return (0.5 - 0.5 * np.cos(np.pi * u)) * (0.5 - 0.5 * np.cos(np.pi * v))
    def frame(n):
        r = w[n][:3, :3]; return r / np.linalg.norm(r, axis=0)
    span = [float(t) for t in tf[::2] if window(t) > 0]
    radial = (tip - H) / np.linalg.norm(tip - H)
    def posed(tq, axu, axh, amp):
        loc = m.sample(clip, tq); b = window(tq) * amp
        q1 = qmul(qaxis(axu, b * 0.6), loc[ua][1]); q2 = qmul(qaxis(axh, b), loc[hd][1])
        l2 = dict(loc); l2[ua] = (loc[ua][0], q1) + tuple(loc[ua][2:]); l2[hd] = (loc[hd][0], q2) + tuple(loc[hd][2:])
        r_ = rest_q * np.array([-1, -1, -1, 1]); l2[uh] = (loc[uh][0], qmul(rest_q, qpow(qmul(r_, q1), 0.5))) + tuple(loc[uh][2:])
        return m.world(l2)
    best = None
    for dname, d in (('radial', radial), ('normal', nrm[kw])):
        a1 = np.cross(tip - S, d); a1 /= max(np.linalg.norm(a1), 1e-9)
        a2 = np.cross(tip - Wp, d); a2 /= max(np.linalg.norm(a2), 1e-9)
        axu = frame(pa).T @ a1; axh = frame(fa).T @ a2      # constant in the parents' frames
        for amp in np.radians(np.arange(2, 32, 2)):
            worst = max(S_.depth(posed(tq, axu, axh, amp))[0] for tq in span)
            score = (round(max(worst, 0.004), 4), amp)
            if best is None or score < best[0]:
                best = (score, dname, float(np.degrees(amp)), float(worst), axu, axh)
            if worst < 0.004: break
    _, dname, ampd, wc, ax_ua, ax_hd = best; amp = np.radians(ampd)
    tr = tracks(clip)
    for node, ax, f_ in ((ua, ax_ua, 0.6), (hd, ax_hd, 1.0)):
        ts = acc(tr[node].input)[:, 0]; Q = acc(tr[node].output).copy()
        for k, t in enumerate(ts):
            Q[k] = qmul(qaxis(ax, window(t) * amp * f_), Q[k])
        tr[node].output = put(Q)
        if node == ua:
            Qua_t, Qua = ts, Q
    tsh = acc(tr[uh].input)[:, 0]; Quh = acc(tr[uh].output).copy(); r_ = rest_q * np.array([-1, -1, -1, 1])
    for k, t in enumerate(tsh):
        qa = np.array([np.interp(t, Qua_t, Qua[:, c]) for c in range(4)]); qa /= np.linalg.norm(qa)
        Quh[k] = qmul(rest_q, qpow(qmul(r_, qa), 0.5))
    tr[uh].output = put(Quh)
    report[f'{clip}:{side}'] = dict(before_cm=round(float(dep.max()) * 100, 1), window=[round(float(t0), 2), round(float(t1), 2)], dir=dname, amp_deg=ampd, after_cm=round(wc * 100, 1))
    print('CLEAR', clip, side, report[f'{clip}:{side}'], flush=True)
    g.buffers[0].byteLength = len(blob); g.set_binary_blob(bytes(blob)); g.save(dst); cur = dst
g.buffers[0].byteLength = len(blob); g.set_binary_blob(bytes(blob)); g.save(dst)
json.dump(report, open(HERE / 'work' / 'sword_clear.json', 'w'), indent=1)
