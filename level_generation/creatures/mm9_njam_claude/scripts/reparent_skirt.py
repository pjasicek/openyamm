"""NJAM.abc hangs its six coat-skirt hinges (Bone06/22/14/10/02/18, each with a second segment) from `root_bone`, a second root
that follows `Bip01 Spine` loosely (yaw up to 8 deg apart in walk3). Our belt and coat top ride on the Spine, so a hinge on
root_bone would twist the skirt's top ring off the belt. This re-parents the six hinges under `Bip01 Spine` and keeps MM9's
world motion exactly: new local = Spine_local^-1 * root_bone_local * hinge_local at the union of the three nodes' key times
(both roots are children of the static Scene Root). Rest likewise. root_bone stays as an unused node.
Args: in.glb out.glb"""
import sys
import numpy as np
from pygltflib import GLTF2, Accessor, BufferView, AnimationSampler, AnimationChannel, AnimationChannelTarget

IN, OUT = sys.argv[1:3]
g = GLTF2().load(IN)
names = [n.name for n in g.nodes]
I = {n: i for i, n in enumerate(names)}
SP, RB = I['Bip01 Spine'], I['root_bone']
HINGES = [I[n] for n in ('Bone06', 'Bone22', 'Bone14', 'Bone10', 'Bone02', 'Bone18')]
blob = bytearray(g.binary_blob())


def read(ai):
    a = g.accessors[ai]
    bv = g.bufferViews[a.bufferView]
    n = {'SCALAR': 1, 'VEC3': 3, 'VEC4': 4}[a.type]
    off = (bv.byteOffset or 0) + (a.byteOffset or 0)
    return np.frombuffer(bytes(blob[off:off + a.count * n * 4]), np.float32).reshape(a.count, n).astype(float)


def add(arr, typ, mm=False):
    global blob
    arr = np.ascontiguousarray(arr, np.float32)
    while len(blob) % 4:
        blob.append(0)
    off = len(blob)
    blob += arr.tobytes()
    g.bufferViews.append(BufferView(buffer=0, byteOffset=off, byteLength=arr.nbytes))
    acc = Accessor(bufferView=len(g.bufferViews) - 1, componentType=5126, count=len(arr), type=typ)
    if mm:
        acc.min = [float(arr.min())]
        acc.max = [float(arr.max())]
    g.accessors.append(acc)
    return len(g.accessors) - 1


def qmat(q):
    x, y, z, w = q / np.linalg.norm(q)
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def mat2q(R):
    t = np.trace(R)
    if t > 0:
        s = np.sqrt(t + 1) * 2
        return np.array([(R[2, 1] - R[1, 2]) / s, (R[0, 2] - R[2, 0]) / s, (R[1, 0] - R[0, 1]) / s, s / 4])
    i = int(np.argmax(np.diag(R)))
    if i == 0:
        s = np.sqrt(1 + R[0, 0] - R[1, 1] - R[2, 2]) * 2
        return np.array([s / 4, (R[0, 1] + R[1, 0]) / s, (R[0, 2] + R[2, 0]) / s, (R[2, 1] - R[1, 2]) / s])
    if i == 1:
        s = np.sqrt(1 + R[1, 1] - R[0, 0] - R[2, 2]) * 2
        return np.array([(R[0, 1] + R[1, 0]) / s, s / 4, (R[1, 2] + R[2, 1]) / s, (R[0, 2] - R[2, 0]) / s])
    s = np.sqrt(1 + R[2, 2] - R[0, 0] - R[1, 1]) * 2
    return np.array([(R[0, 2] + R[2, 0]) / s, (R[1, 2] + R[2, 1]) / s, s / 4, (R[1, 0] - R[0, 1]) / s])


def M(t, q):
    m = np.eye(4)
    m[:3, :3] = qmat(q)
    m[:3, 3] = t
    return m


def rest(i):
    n = g.nodes[i]
    return np.array(n.translation or [0, 0, 0], float), np.array(n.rotation or [0, 0, 0, 1], float)


def qcont(v):
    v = v.copy()
    for k in range(1, len(v)):
        if v[k] @ v[k - 1] < 0:
            v[k] = -v[k]
    return v


def sample(ch, node, path, times, default):
    if (node, path) not in ch:
        return np.repeat(default[None], len(times), 0)
    t, v = ch[(node, path)]
    out = np.stack([np.interp(times, t, v[:, k]) for k in range(v.shape[1])], 1)
    return out


def convert(Ts, Qs, Tr, Qr, Th, Qh):
    T, Q = [], []
    for k in range(len(Ts)):
        m = np.linalg.inv(M(Ts[k], Qs[k])) @ M(Tr[k], Qr[k]) @ M(Th[k], Qh[k])
        T.append(m[:3, 3])
        Q.append(mat2q(m[:3, :3]))
    return np.array(T), qcont(np.array(Q))


RS, RR = rest(SP), rest(RB)
HREST = {h: rest(h) for h in HINGES}
for h in HINGES:
    T, Q = convert([RS[0]], [RS[1]], [RR[0]], [RR[1]], [HREST[h][0]], [HREST[h][1]])
    g.nodes[h].translation = T[0].tolist()
    g.nodes[h].rotation = Q[0].tolist()
g.nodes[RB].children = [c for c in (g.nodes[RB].children or []) if c not in HINGES]
g.nodes[SP].children = list(g.nodes[SP].children or []) + HINGES
worst = 0.0
for an in g.animations:
    ch = {}
    for c in an.channels:
        s = an.samplers[c.sampler]
        v = read(s.output)
        if c.target.path == 'rotation':
            v = qcont(v)
        ch[(c.target.node, c.target.path)] = (read(s.input)[:, 0], v)
    keep = [c for c in an.channels if c.target.node not in HINGES]
    for h in HINGES:
        keys = [ch[k][0] for k in ch if k[0] in (SP, RB, h)]
        times = np.unique(np.concatenate(keys)) if keys else np.array([0.0])
        Ts = sample(ch, SP, 'translation', times, RS[0])
        Qs = sample(ch, SP, 'rotation', times, RS[1])
        Tr = sample(ch, RB, 'translation', times, RR[0])
        Qr = sample(ch, RB, 'rotation', times, RR[1])
        Th = sample(ch, h, 'translation', times, HREST[h][0])
        Qh = sample(ch, h, 'rotation', times, HREST[h][1])
        T, Q = convert(Ts, Qs, Tr, Qr, Th, Qh)
        worst = max(worst, float(np.linalg.norm(T - g.nodes[h].translation, axis=1).max()))
        # MM9's pivot slides on the spine by 2-22 cm (root_bone's own path; 2.4 cm already in stand1). Ours stays on the Spine at its
        # rest offset, so the coat's top ring cannot leave the belt; the world rotation is kept
        T = np.repeat(np.array(g.nodes[h].translation)[None], len(T), 0)
        ti = add(times[:, None], 'SCALAR', True)
        for path, val, typ in (('translation', T, 'VEC3'), ('rotation', Q, 'VEC4')):
            an.samplers.append(AnimationSampler(input=ti, output=add(val, typ), interpolation='LINEAR'))
            keep.append(AnimationChannel(sampler=len(an.samplers) - 1, target=AnimationChannelTarget(node=h, path=path)))
    an.channels = keep
g.buffers[0].byteLength = len(blob)
g.set_binary_blob(bytes(blob))
g.save(OUT)
print('REPARENT', OUT, 'MM9 hinge pivot drift on the Spine, dropped (max over clips, m):', round(worst, 4))
