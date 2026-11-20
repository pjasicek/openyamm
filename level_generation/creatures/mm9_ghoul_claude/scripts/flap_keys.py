#!/usr/bin/env python3
"""Flaps lie on the thighs. MM9's Bone01/Bone03 hang still on the pelvis while the thighs pass through them. Per frame, the smallest rotation about the pelvis' left-right axis that puts every thigh point under
the flap behind it (margin), on top of MM9's own keys; dilated and low-passed over the clip (cyclic on loops), so it is a smooth curve. Args: in.glb out.glb [margin]"""
import json, sys
from pathlib import Path
import numpy as np
from scipy.ndimage import gaussian_filter1d, maximum_filter1d
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
from pygltflib import GLTF2, Accessor, BufferView, AnimationSampler
IN, OUT = sys.argv[1:3]
MARGIN = float(sys.argv[3]) if len(sys.argv) > 3 else 0.012
LOOPS = ('Standing', 'Walking', 'Running', 'Backpedal', 'BackpedalRun')
m = Model(Glb(IN)); doc = m.glb.json
nodes = doc['nodes']; names = [n.get('name') for n in nodes]; ix = {n: i for i, n in enumerate(names)}
sk = doc['skins'][0]['joints']; jn = [nodes[j]['name'] for j in sk]; jx = {n: i for i, n in enumerate(jn)}
Rs = m.skinned_positions(m.world({}))
offs = np.cumsum([0] + [len(r[0]) for r in Rs])
rest = np.concatenate([r[0] for r in Rs]); T = np.concatenate([np.asarray(r[1]).reshape(-1, 3) + o for r, o in zip(Rs, offs)])
J = np.concatenate([p['joints'] for p in m.primitives]); W = np.concatenate([p['weights'] for p in m.primitives])
wt = lambda n: ((J == jx[n]) * W).sum(1) if n in jx else np.zeros(len(rest))
thigh = sum(wt(f'Bip01 {s} {b}') for s in 'LR' for b in ('Thigh', 'Thigh_h', 'Calf', 'Calf_h'))
thigh = thigh * (wt('Bip01 Pelvis') + wt('Bip01 L Thigh') + wt('Bip01 R Thigh') < 0.995)
q = np.where(thigh > 0.25)[0]
w0 = m.world({})
pel = ix['Bip01 Pelvis']
R0p = w0[pel][:3, :3]
FL = {'Bone01': 1, 'Bone03': -1}
info = {}
for b, sgn in FL.items():
    v = np.where(wt(b) > 0.3)[0]
    piv = w0[ix[b]][:3, 3]
    tip = rest[v][np.argmin(rest[v, 1])]
    u = tip - piv; L = np.linalg.norm(u); u /= L
    o = np.array([0, 0, sgn], float); o = o - u * (o @ u); o /= np.linalg.norm(o)
    # half width as a function of distance along the flap
    d = (rest[v] - piv) @ u
    bins = np.linspace(0, L, 8); wd = [max(1e-3, np.abs(rest[v][(d >= a) & (d <= c), 0]).max() if ((d >= a) & (d <= c)).any() else 0) for a, c in zip(bins[:-1], bins[1:])]
    info[b] = dict(piv=piv, u=u, o=o, L=L, bins=0.5 * (bins[:-1] + bins[1:]), wd=np.array(wd), R0=w0[ix[b]][:3, :3])
    print(b, 'L', round(L, 3), 'u', u.round(2), 'width', np.round(wd, 3))
g = GLTF2().load(IN); blob = bytearray(g.binary_blob())


def add(arr):
    global blob
    while len(blob) % 4: blob.append(0)
    o_ = len(blob); d_ = arr.astype('f4').tobytes(); blob += d_
    g.bufferViews.append(BufferView(buffer=0, byteOffset=o_, byteLength=len(d_)))
    g.accessors.append(Accessor(bufferView=len(g.bufferViews) - 1, componentType=5126, count=len(arr), type='VEC4'))
    return len(g.accessors) - 1


def qmat(R):
    from glb_pose import matrix_quaternion
    return matrix_quaternion(R)


def qmul(a, b):
    ax, ay, az, aw = a; bx, by, bz, bw = b
    return np.array([aw * bx + ax * bw + ay * bz - az * by, aw * by - ax * bz + ay * bw + az * bx, aw * bz + ax * by - ay * bx + az * bw, aw * bw - ax * bx - ay * by - az * bz])


rep = {}
for an in g.animations:
    for b, sgn in FL.items():
        fi = info[b]
        ch = next((c for c in an.channels if names[c.target.node] == b and c.target.path == 'rotation'), None)
        if ch is None:
            print('no channel', an.name, b); continue
        sam = an.samplers[ch.sampler]
        tin = sam.input
        ts = np.array(m.glb.accessor(tin)[:, 0])
        Qs = np.array(m.glb.accessor(sam.output))
        need = np.zeros(len(ts)); axes = []
        for k, t in enumerate(ts):
            world = m.world(m.sample(an.name, float(t)))
            x = np.concatenate([r[0] for r in m.skinned_positions(world)])[q]
            A = world[pel][:3, :3] @ R0p.T
            piv = world[ix[b]][:3, 3]
            Rb = world[ix[b]][:3, :3] @ fi['R0'].T
            u, o = Rb @ fi['u'], Rb @ fi['o']
            ax = np.cross(u, o); ax /= np.linalg.norm(ax)
            axes.append(ax)
            p = x - piv
            a_, b_, c_ = p @ u, p @ o, p @ ax
            r = np.hypot(a_, b_)
            wid = np.interp(r, fi['bins'], fi['wd'])
            cand = (r > ((0.15 if an.name == 'Running' else 0.2) if b == 'Bone01' else 0.12)) & (r < fi['L'] + 0.015) & (np.abs(c_) < wid + 0.004) & (a_ > -0.02)
            if cand.any():
                psi = np.arctan2(b_[cand], a_[cand]) + (0.04 if an.name == 'Running' else MARGIN) / r[cand]
                need[k] = max(0.0, psi.max())
        if an.name in LOOPS:
            e = maximum_filter1d(need, 9, mode='wrap'); e = gaussian_filter1d(e, 1.8, mode='wrap')
        else:
            e = maximum_filter1d(need, 5, mode='nearest'); e = gaussian_filter1d(e, 2.2, mode='nearest')
        e = np.minimum(e, np.radians(82))
        rep[(an.name, b)] = (round(float(np.degrees(need.max())), 1), round(float(np.degrees(e.max())), 1))
        out = Qs.copy()
        pn = next(i for i, n in enumerate(nodes) if ix[b] in n.get('children', []))
        for k, t in enumerate(ts):
            world = m.world(m.sample(an.name, float(t)))
            Rp = world[pn][:3, :3]
            ax = Rp.T @ axes[k]
            s, c = np.sin(e[k] / 2), np.cos(e[k] / 2)
            dq = np.array([ax[0] * s, ax[1] * s, ax[2] * s, c])
            out[k] = qmul(dq, Qs[k])
        out /= np.linalg.norm(out, axis=1, keepdims=True)
        for k in range(1, len(out)):
            if out[k] @ out[k - 1] < 0: out[k] *= -1
        sam.output = add(out)
g.buffers[0].byteLength = len(blob); g.set_binary_blob(bytes(blob)); g.save(OUT)
print('FLAPKEYS', {f'{k[0]}:{k[1]}': v for k, v in rep.items()})
