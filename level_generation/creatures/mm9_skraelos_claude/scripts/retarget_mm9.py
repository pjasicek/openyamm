"""Retarget MM9 clips between two MM9 skeletons by WORLD rotation copy (playbook rule: a local copy differs where the
rest frames differ; Sigmund's FHP biped and the PeasantMale biped differ 0-13 deg per joint and in hierarchy).

Usage: retarget_mm9.py <target glb> <source glb> <out glb> <map json>
map json: {"clips": {"<out name>": "<source clip>", ...},
           "bones": {"<target joint>": "<source joint>", ...},   # world-rotation delta copied
           "root": ["<target root>", "<source root>"],            # translation follows the source root, scaled
           "fps": 30}
For a mapped target joint t with source s:  W_t(f) = W_s(f) W_s(rest)^-1 W_t(rest)   (rotations only);
unmapped target joints keep their rest LOCAL rotation (they follow their parent). Local = W_parent^-1 W_t.
Root translation (target root's parent frame = the source root's parent frame, both under 'Scene Root'):
T_t(f) = T_t(rest) + (T_s(f) - T_s(rest)) * k,  k = target root height / source root height at rest.
The out GLB is the target GLB with ONLY the retargeted animations (rotation + root translation channels, LINEAR, fps).
"""
import json, sys
import numpy as np
from pygltflib import GLTF2, Animation, AnimationChannel, AnimationChannelTarget, AnimationSampler, Accessor, BufferView


def qmul(a, b):
    x1, y1, z1, w1 = np.moveaxis(a, -1, 0)
    x2, y2, z2, w2 = np.moveaxis(b, -1, 0)
    return np.stack([w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2, w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
                     w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2, w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2], -1)


def qinv(q):
    return q * np.array([-1, -1, -1, 1.0])


def qrot(q, v):
    p = np.concatenate([v, np.zeros(v.shape[:-1] + (1,))], -1)
    return qmul(qmul(q, p), qinv(q))[..., :3]


def slerp(q0, q1, t):
    d = np.sum(q0 * q1, -1, keepdims=True)
    q1 = np.where(d < 0, -q1, q1); d = np.abs(d)
    lin = d > 0.9995
    th = np.arccos(np.clip(d, -1, 1)); s = np.sin(th)
    with np.errstate(invalid='ignore', divide='ignore'):
        a = np.where(lin, 1 - t, np.sin((1 - t) * th) / s); b = np.where(lin, t, np.sin(t * th) / s)
    q = a * q0 + b * q1
    return q / np.linalg.norm(q, axis=-1, keepdims=True)


def read(g, i):
    acc = g.accessors[i]; bv = g.bufferViews[acc.bufferView]
    n = {'SCALAR': 1, 'VEC3': 3, 'VEC4': 4}[acc.type]
    off = (bv.byteOffset or 0) + (acc.byteOffset or 0)
    return np.frombuffer(g.binary_blob(), dtype=np.float32, count=acc.count * n, offset=off).reshape(acc.count, n).astype(float)


def sample(g, anim, node_idx, path, times):
    for ch in anim.channels:
        if ch.target.node == node_idx and ch.target.path == path:
            s = anim.samplers[ch.sampler]
            t = read(g, s.input)[:, 0]; v = read(g, s.output)
            tq = np.clip(times, t[0], t[-1])
            k = np.clip(np.searchsorted(t, tq, side='right') - 1, 0, max(len(t) - 2, 0))
            if len(t) == 1:
                return np.repeat(v[:1], len(times), 0)
            u = ((tq - t[k]) / np.maximum(t[k + 1] - t[k], 1e-9))[:, None]
            return slerp(v[k], v[k + 1], u) if path == 'rotation' else v[k] * (1 - u) + v[k + 1] * u
    return None


def rest(n, path):
    if path == 'rotation':
        return np.array(n.rotation if n.rotation else [0, 0, 0, 1.0])
    return np.array(n.translation if n.translation else [0, 0, 0.0])


def parents(g):
    p = {}
    for i, n in enumerate(g.nodes):
        for c in n.children or []:
            p[c] = i
    return p


def world_rot(g, par, local):
    """local: {node: (F,4)} -> world (F,4) per node, from the scene roots down."""
    W = {}
    def w(i):
        if i in W:
            return W[i]
        W[i] = local[i] if i not in par else qmul(w(par[i]), local[i])
        return W[i]
    for i in local:
        w(i)
    return W


def main():
    tgt_p, src_p, out_p, map_p = sys.argv[1:5]
    cfg = json.load(open(map_p)); fps = cfg.get('fps', 30)
    T = GLTF2().load(tgt_p); S = GLTF2().load(src_p)
    tn = {n.name: i for i, n in enumerate(T.nodes)}; sn = {n.name: i for i, n in enumerate(S.nodes)}
    tpar, spar = parents(T), parents(S)
    tjoints = [i for i, n in enumerate(T.nodes) if n.mesh is None]
    sjoints = [i for i, n in enumerate(S.nodes) if n.mesh is None]
    trest = {i: rest(T.nodes[i], 'rotation')[None] for i in tjoints}
    srest = {i: rest(S.nodes[i], 'rotation')[None] for i in sjoints}
    Wt0 = world_rot(T, tpar, trest); Ws0 = world_rot(S, spar, srest)
    troot, sroot = tn[cfg['root'][0]], sn[cfg['root'][1]]
    def height(g, par, i, r):
        # world position of joint i at rest
        pos = np.zeros(3); j = i
        chain = []
        while True:
            chain.append(j)
            if j not in par: break
            j = par[j]
        p = np.zeros(3); q = np.array([0, 0, 0, 1.0])
        for j in reversed(chain):
            p = p + qrot(q[None], rest(g.nodes[j], 'translation')[None])[0]
            q = qmul(q[None], rest(g.nodes[j], 'rotation')[None])[0]
        return p
    ht = height(T, tpar, troot, None); hs = height(S, spar, sroot, None)
    k = cfg.get('root_scale') or abs(ht[1]) / max(abs(hs[1]), 1e-6)
    print('RETARGET root heights', np.round(ht, 3), np.round(hs, 3), 'k', round(k, 3))
    blob = bytearray(T.binary_blob() or b'')
    T.animations = []
    def add(arr, typ, mn=False):
        arr = np.ascontiguousarray(arr, np.float32)
        while len(blob) % 4: blob.append(0)
        bv = BufferView(buffer=0, byteOffset=len(blob), byteLength=arr.nbytes); blob.extend(arr.tobytes())
        T.bufferViews.append(bv)
        acc = Accessor(bufferView=len(T.bufferViews) - 1, componentType=5126, count=len(arr), type=typ)
        if mn:
            acc.min = [float(arr.min())]; acc.max = [float(arr.max())]
        T.accessors.append(acc)
        return len(T.accessors) - 1
    smap = {tn[a]: sn[b] for a, b in cfg['bones'].items()}
    for out_name, clip in cfg['clips'].items():
        sa = next(a for a in S.animations if a.name == clip)
        dur = max(read(S, s.input)[-1, 0] for s in sa.samplers)
        F = max(2, int(round(dur * fps)) + 1); times = np.linspace(0, dur, F)
        sloc = {}
        for i in sjoints:
            q = sample(S, sa, i, 'rotation', times)
            sloc[i] = q if q is not None else np.repeat(srest[i], F, 0)
        Ws = world_rot(S, spar, sloc)
        Wt = {}
        def wt(i):
            if i in Wt:
                return Wt[i]
            if i in smap:
                s = smap[i]
                Wt[i] = qmul(qmul(Ws[s], qinv(Ws0[s])), Wt0[i])
            else:
                Wt[i] = qmul(wt(tpar[i]), np.repeat(trest[i], F, 0)) if i in tpar else np.repeat(trest[i], F, 0)
            return Wt[i]
        chans, samps = [], []
        tacc = add(times[:, None], 'SCALAR', True)
        for i in tjoints:
            wq = wt(i)
            lq = qmul(qinv(wt(tpar[i])), wq) if i in tpar else wq
            for f in range(1, F):
                if np.dot(lq[f], lq[f - 1]) < 0:
                    lq[f] = -lq[f]
            lq /= np.linalg.norm(lq, axis=1, keepdims=True)
            samps.append(AnimationSampler(input=tacc, output=add(lq, 'VEC4'), interpolation='LINEAR'))
            chans.append(AnimationChannel(sampler=len(samps) - 1, target=AnimationChannelTarget(node=i, path='rotation')))
        st = sample(S, sa, sroot, 'translation', times)
        st = st if st is not None else np.repeat(rest(S.nodes[sroot], 'translation')[None], F, 0)
        tt = rest(T.nodes[troot], 'translation')[None] + (st - rest(S.nodes[sroot], 'translation')[None]) * k
        samps.append(AnimationSampler(input=tacc, output=add(tt, 'VEC3'), interpolation='LINEAR'))
        chans.append(AnimationChannel(sampler=len(samps) - 1, target=AnimationChannelTarget(node=troot, path='translation')))
        T.animations.append(Animation(name=out_name, channels=chans, samplers=samps))
        print('RETARGET', out_name, '<-', clip, F, 'frames', round(dur, 3), 's')
    T.buffers[0].byteLength = len(blob)
    T.set_binary_blob(bytes(blob))
    T.save(out_p)


if __name__ == '__main__':
    main()
