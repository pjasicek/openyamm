"""MM9 NOBLEMAN clips onto the HIGHWAYMAN/FIGHTERBASE joint layout. The Bip01 core names match (Pelvis, Spine..Spine3, Neck, Head, Clavicle,
UpperArm, Forearm, Hand, Thigh, Calf, Foot, Toe0) and every bone's axis is the biped convention (-X along the bone), so local rotations carry
over unchanged, with one exception: NOBLEMAN hangs the thighs from Bip01 Spine, FIGHTERBASE from Bip01 Pelvis. Here each thigh's rest and keys
become Spine_local(t) * Thigh_local(t) (translation Spine_T + R_spine Thigh_T) on the union of the two key time sets (keys linear: exact).
Finger channels (different finger names and frames) are dropped; our MPFB fingers are keyed by finger_keys. Args: <nobleman glb> <out glb>"""
import sys
import numpy as np
from pygltflib import GLTF2, BufferView, Accessor
IN, OUT = sys.argv[1:3]
g = GLTF2().load(IN)
names = [n.name for n in g.nodes]; ix = {n: i for i, n in enumerate(names)}


def read(acc_index):
    acc = g.accessors[acc_index]; bv = g.bufferViews[acc.bufferView]; data = g.binary_blob()
    n = {'SCALAR': 1, 'VEC3': 3, 'VEC4': 4}[acc.type]
    off = (bv.byteOffset or 0) + (acc.byteOffset or 0); stride = bv.byteStride or 4 * n
    raw = np.frombuffer(data, dtype=np.uint8, count=stride * (acc.count - 1) + 4 * n, offset=off)
    out = np.lib.stride_tricks.as_strided(raw.view(np.float32), shape=(acc.count, n), strides=(stride, 4)) if stride != 4 * n \
        else raw.view(np.float32).reshape(acc.count, n)
    return np.array(out, np.float64)


blob = bytearray(g.binary_blob())


def add(arr, typ, minmax=False):
    global blob
    arr = np.ascontiguousarray(arr, np.float32)
    while len(blob) % 4: blob.append(0)
    off = len(blob); blob += arr.tobytes()
    g.bufferViews.append(BufferView(buffer=0, byteOffset=off, byteLength=arr.nbytes))
    acc = Accessor(bufferView=len(g.bufferViews) - 1, componentType=5126, count=len(arr), type=typ)
    if minmax: acc.min = [float(arr.min())]; acc.max = [float(arr.max())]
    g.accessors.append(acc); return len(g.accessors) - 1


def qmul(a, b):
    x1, y1, z1, w1 = a.T; x2, y2, z2, w2 = b.T
    return np.stack([w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2, w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
                     w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2, w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2], -1)


def qrot(q, v):
    u = q[:, :3]; w = q[:, 3:4]
    return v + 2 * np.cross(u, np.cross(u, v) + w * v)


def slerp_at(t, q, tq):
    q = q.copy()
    for k in range(1, len(q)):
        if q[k] @ q[k - 1] < 0: q[k] = -q[k]
    out = np.zeros((len(tq), 4))
    for c in range(4): out[:, c] = np.interp(tq, t, q[:, c])
    return out / np.linalg.norm(out, axis=1, keepdims=True)


def lerp_at(t, v, tq):
    return np.stack([np.interp(tq, t, v[:, c]) for c in range(3)], -1)


orig = {n.name: (np.array(n.translation or [0, 0, 0], float), np.array(n.rotation or [0, 0, 0, 1], float)) for n in g.nodes}
sp = g.nodes[ix['Bip01 Spine']]; pe = ix['Bip01 Pelvis']
spT = np.array(sp.translation or [0, 0, 0], float)[None]; spR = np.array(sp.rotation or [0, 0, 0, 1], float)[None]
for S in 'LR':
    th = g.nodes[ix[f'Bip01 {S} Thigh']]
    tT = np.array(th.translation or [0, 0, 0], float)[None]; tR = np.array(th.rotation or [0, 0, 0, 1], float)[None]
    th.translation = (spT + qrot(spR, tT))[0].tolist(); th.rotation = qmul(spR, tR)[0].tolist()
    sp.children.remove(ix[f'Bip01 {S} Thigh']); g.nodes[pe].children.append(ix[f'Bip01 {S} Thigh'])
rest = {n.name: (np.array(n.translation or [0, 0, 0], float), np.array(n.rotation or [0, 0, 0, 1], float)) for n in g.nodes}
for a in g.animations:
    ch = {}
    for c in a.channels:
        s = a.samplers[c.sampler]; ch[(names[c.target.node], c.target.path)] = (read(s.input)[:, 0], read(s.output), c)
    dur = max(v[0][-1] for v in ch.values())

    def get(n, p, tq):
        if (n, p) in ch:
            t, v, _ = ch[(n, p)]
            return slerp_at(t, v, tq) if p == 'rotation' else lerp_at(t, v, tq)
        # glTF: an unanimated path keeps the node's own (original) value
        return np.repeat(orig[n][1 if p == 'rotation' else 0][None], len(tq), 0)
    keep = []
    for c in a.channels:
        n = names[c.target.node]
        if 'Finger' in n: continue
        keep.append(c)
    a.channels = keep
    for S in 'LR':
        tn = f'Bip01 {S} Thigh'
        times = set()
        for key in (('Bip01 Spine', 'rotation'), ('Bip01 Spine', 'translation'), (tn, 'rotation'), (tn, 'translation')):
            if key in ch: times |= set(ch[key][0].tolist())
        tq = np.array(sorted(times)) if times else np.array([0.0])
        sR = get('Bip01 Spine', 'rotation', tq); sT = get('Bip01 Spine', 'translation', tq)
        tRk = get(tn, 'rotation', tq)
        tTk = get(tn, 'translation', tq)
        nR = qmul(sR, tRk); nT = sT + qrot(sR, tTk)
        ti = add(tq[:, None], 'SCALAR', True)
        for path, val in (('rotation', nR), ('translation', nT)):
            vi = add(val, 'VEC4' if path == 'rotation' else 'VEC3')
            if (tn, path) in ch:
                c = ch[(tn, path)][2]; s = a.samplers[c.sampler]; s.input = ti; s.output = vi; s.interpolation = 'LINEAR'
            else:
                from pygltflib import AnimationSampler, AnimationChannel, AnimationChannelTarget
                a.samplers.append(AnimationSampler(input=ti, output=vi, interpolation='LINEAR'))
                a.channels.append(AnimationChannel(sampler=len(a.samplers) - 1, target=AnimationChannelTarget(node=ix[tn], path=path)))
# joints a clip leaves unkeyed hold NOBLEMAN's rest (clips_mm9.py would otherwise put our own rest there: Bip01 Spine rests 13 deg tilted)
from pygltflib import AnimationSampler, AnimationChannel, AnimationChannelTarget
added = 0
for a in g.animations:
    have = {(c.target.node, c.target.path) for c in a.channels}
    t1 = max(float(g.accessors[s.input].max[0]) for s in a.samplers)
    for i, n in enumerate(g.nodes):
        if not (n.name or '').startswith('Bip01') or 'Finger' in n.name or (i, 'rotation') in have: continue
        ti = add(np.array([[0.0], [t1]]), 'SCALAR', True); vi = add(np.repeat(np.array(n.rotation or [0, 0, 0, 1.0])[None], 2, 0), 'VEC4')
        a.samplers.append(AnimationSampler(input=ti, output=vi, interpolation='LINEAR'))
        a.channels.append(AnimationChannel(sampler=len(a.samplers) - 1, target=AnimationChannelTarget(node=i, path='rotation'))); added += 1
print('CONSTANT channels', added)
g.buffers[0].byteLength = len(blob)
g.set_binary_blob(bytes(blob))
g.save(OUT)
print('CONVERTED', OUT, [a.name for a in g.animations])
