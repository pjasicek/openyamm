#!/usr/bin/env python3
"""Keys of XFlap, solved against the legs (run 2; replaces flap_keys.py's heuristic alone, which left the flap 3.3 cm in a thigh in Running and
6.1 cm in AttackMelee). Per Spine key: start from flap_keys.py's swing (forward A off the leading thigh, sideways B), and if a flap point that
the hinge carries lies inside a leg (plate_gate.py's test), search more forward swing and sideways swing for the smallest change that clears it.
The needed angles are then held over +-HOLD keys (running maximum of the extra swing) and low-passed (sigma SIG keys), wrapped on loops, so the
flap follows smooth curves. Args: <in glb> <out glb>"""
import sys, os
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from scipy.ndimage import gaussian_filter1d, maximum_filter1d
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor')); sys.path.insert(0, str(HERE.parent / 'claude_shared'))
from glb_pose import Glb, Model, trs_matrix
from detached_parts_audit import closest_on_triangles
from pygltflib import GLTF2, Accessor, BufferView, AnimationSampler, AnimationChannel, AnimationChannelTarget
IN, OUT = sys.argv[1:3]
HOLD, SIG = int(os.environ.get('HOLD', 2)), float(os.environ.get('SIG', 1.2))
LOOPS = {'Standing', 'Walking', 'Running', 'Backpedal', 'BackpedalRun'}
m = Model(Glb(IN)); doc = m.glb.json; names = [n.get('name') for n in doc['nodes']]; ix = {n: i for i, n in enumerate(names)}
g = GLTF2().load(IN); blob = bytearray(g.binary_blob())
def add(arr, typ):
    global blob
    while len(blob) % 4: blob.append(0)
    o = len(blob); d = arr.astype('f4').tobytes(); blob += d
    g.bufferViews.append(BufferView(buffer=0, byteOffset=o, byteLength=len(d)))
    g.accessors.append(Accessor(bufferView=len(g.bufferViews) - 1, componentType=5126, count=len(arr), type=typ))
    return len(g.accessors) - 1
jn = [names[j] for j in m.joints]; ibm = {n: m.inverse_binds[i] for i, n in enumerate(jn)}
Bs = np.linalg.inv(ibm['Bip01 Spine'])
def ang(v): return np.arctan2(v[2], -v[1])
bind = {s: np.linalg.inv(ibm[f'Bip01 {s} Calf'])[:3, 3] - np.linalg.inv(ibm[f'Bip01 {s} Thigh'])[:3, 3] for s in 'LR'}
r0 = {s: ang(bind[s]) for s in 'LR'}
axis_local = Bs[:3, :3].T @ np.array([1., 0, 0]); axis_local /= np.linalg.norm(axis_local)
fwd_local = Bs[:3, :3].T @ np.array([0, 0, 1.]); fwd_local /= np.linalg.norm(fwd_local)
XF = ix['XFlap']; T0 = np.array(doc['nodes'][XF]['translation'], float); S0 = np.array(doc['nodes'][XF].get('scale', [1, 1, 1.]), float)
def qa(ax, a): return np.r_[ax * np.sin(a / 2), np.cos(a / 2)]
def qm(p, q):
    x1, y1, z1, w1 = p; x2, y2, z2, w2 = q
    return np.array([w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2, w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2, w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2, w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2])
def Q(A, B): return qm(qa(fwd_local, B), qa(axis_local, -A))
# mesh: legs and flap points as in plate_gate.py
PR = [p for p in m.primitives if p['skinned'] and p['node'] == m.primitives[0]['node']]
J, W = np.vstack([p['joints'] for p in PR]), np.vstack([p['weights'] for p in PR])
offs = np.cumsum([0] + [len(p['positions']) for p in PR]); tri = np.vstack([np.asarray(p['triangles']).reshape(-1, 3) + o for p, o in zip(PR, offs)])
restp = np.vstack([p['positions'] for p in PR]); SH = np.load(HERE / 'work/shell_pos.npy'); sw = cKDTree(SH).query(restp)[0] < 1e-4
legb = [i for i, n in enumerate(jn) if ('Thigh' in n or 'Calf' in n)]; lw = (np.isin(J, legb) * W).sum(1)
legf = np.where((lw[tri] > .4).all(1) & ~sw[tri].any(1))[0]
xfj = jn.index('XFlap'); xw = (W * (J == xfj)).sum(1)
fl = np.where(sw & (xw > .3))[0]; print('flap points carried by the hinge', len(fl))
H1 = np.c_[restp[fl], np.ones(len(fl))]
def skin_all(world):
    pal = world[m.joints] @ m.inverse_binds; H = np.c_[restp, np.ones(len(restp))]
    return np.einsum('vij,vj->vi', np.einsum('vk,vkij->vij', W, pal[J]), H)[:, :3]
def depth(q, ft, tree, n_):
    _, near = tree.query(q, k=16); pts = np.repeat(q, near.shape[1], 0)
    qq, _ = closest_on_triangles(pts, ft[near.ravel(), 0], ft[near.ravel(), 1], ft[near.ravel(), 2])
    dd = np.linalg.norm(pts - qq, axis=1).reshape(near.shape); b = dd.argmin(1); r = np.arange(len(q)); fid = near[r, b]; cp = qq.reshape(*near.shape, 3)[r, b]
    s_ = -np.einsum('ij,ij->i', q - cp, n_[fid]); dist = dd[r, b]; ins = (s_ > .003) & (s_ > .7 * dist) & (dist < .07)
    return float(s_[ins].max()) if ins.any() else 0.
CAND = sorted([(da, db) for da in np.radians(np.arange(0, 61, 4)) for db in np.radians(np.arange(-32, 33, 8))], key=lambda c: c[0] + .5 * abs(c[1]))
tops = {}
for an in g.animations:
    an.channels = [c for c in an.channels if c.target.node != XF]
    ch0 = next(c for c in an.channels if names[c.target.node] == 'Bip01 Spine'); tin = an.samplers[ch0.sampler].input
    a = g.accessors[tin]; bv = g.bufferViews[a.bufferView]; ts = np.frombuffer(bytes(blob[(bv.byteOffset or 0) + (a.byteOffset or 0):(bv.byteOffset or 0) + (a.byteOffset or 0) + 4 * a.count]), 'f4').copy()
    A0 = np.zeros(len(ts)); B0 = np.zeros(len(ts)); dA = np.zeros(len(ts)); dB = np.zeros(len(ts)); left = []
    loc = [m.sample(an.name, float(t)) for t in ts]
    for k, t in enumerate(ts):
        Wd = m.world(loc[k]); Rs = (Wd[ix['Bip01 Spine']] @ ibm['Bip01 Spine'])[:3, :3]; vals = []
        for s in 'LR':
            v = Rs.T @ (Wd[ix[f'Bip01 {s} Calf']][:3, 3] - Wd[ix[f'Bip01 {s} Thigh']][:3, 3]); vals.append(ang(v) - r0[s])
        A0[k] = max(max(vals), 0); B0[k] = vals[0] - vals[1]
    A0 = np.clip(gaussian_filter1d(A0, 1.2, mode='wrap' if an.name in LOOPS else 'nearest'), 0, np.radians(100))
    B0 = np.clip(gaussian_filter1d(B0, 1.2, mode='wrap' if an.name in LOOPS else 'nearest') * -1.0, -np.radians(30), np.radians(30))
    for k, t in enumerate(ts):
        Wd = m.world(loc[k]); x = skin_all(Wd); ft = x[tri[legf]]; n_ = np.cross(ft[:, 1] - ft[:, 0], ft[:, 2] - ft[:, 0]); n_ /= np.maximum(np.linalg.norm(n_, axis=1, keepdims=True), 1e-12)
        tree = cKDTree(ft.mean(1)); par = Wd[m.parent[XF]]; best = (9., 0., 0.)
        for da, db in CAND:
            A, B = min(A0[k] + da, np.radians(110)), np.clip(B0[k] + db, -np.radians(35), np.radians(35))
            Wd[XF] = par @ trs_matrix(T0, Q(A, B), S0); pal = Wd[m.joints] @ m.inverse_binds
            q = np.einsum('vij,vj->vi', np.einsum('vk,vkij->vij', W[fl], pal[J[fl]]), H1)[:, :3]
            dp = depth(q, ft, tree, n_)
            if dp < best[0]: best = (dp, A - A0[k], B - B0[k])
            if dp < .004: break
        dA[k], dB[k] = best[1], best[2]
        if best[0] >= .004: left.append((round(float(t), 3), round(best[0] * 100, 1)))
    mode = 'wrap' if an.name in LOOPS else 'nearest'
    dA = gaussian_filter1d(maximum_filter1d(dA, 2 * HOLD + 1, mode=mode), SIG, mode=mode)
    db_hold = np.where(np.abs(maximum_filter1d(dB, 2 * HOLD + 1, mode=mode)) >= np.abs(-maximum_filter1d(-dB, 2 * HOLD + 1, mode=mode)), maximum_filter1d(dB, 2 * HOLD + 1, mode=mode), -maximum_filter1d(-dB, 2 * HOLD + 1, mode=mode))
    dB = gaussian_filter1d(db_hold, SIG, mode=mode)
    A = np.clip(A0 + dA, 0, np.radians(110)); B = np.clip(B0 + dB, -np.radians(35), np.radians(35))
    Qs = np.array([Q(a_, b_) for a_, b_ in zip(A, B)])
    s2 = len(an.samplers); an.samplers.append(AnimationSampler(input=tin, output=add(Qs, 'VEC4'), interpolation='LINEAR'))
    s1 = len(an.samplers); an.samplers.append(AnimationSampler(input=tin, output=add(np.tile(T0, (len(ts), 1)), 'VEC3'), interpolation='LINEAR'))
    an.channels.append(AnimationChannel(sampler=s2, target=AnimationChannelTarget(node=XF, path='rotation')))
    an.channels.append(AnimationChannel(sampler=s1, target=AnimationChannelTarget(node=XF, path='translation')))
    tops[an.name] = (round(float(np.degrees(A.max())), 1), round(float(np.degrees(dA.max())), 1), round(float(np.degrees(np.abs(dB).max())), 1), left[:3])
    print(an.name, 'max swing, extra forward, extra side, keys not cleared', tops[an.name], flush=True)
g.buffers[0].byteLength = len(blob); g.set_binary_blob(bytes(blob)); g.save(OUT)
print('FLAP solved', len(tops), 'clips')
