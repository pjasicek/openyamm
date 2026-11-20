"""Un-mirror an MM9 ABC conversion (Evil Sorcerer; from mm9_highwayman_claude/scripts/mirror_source.py, no weapons, 2026-10-31).

LithTech is left-handed and convert_abc_model.py keeps its axes in right-handed glTF, so every converted MM9 model is the
mirror image of the game: `Bip01 R *` sits at +X on a figure facing +Z, the anatomical LEFT, and the Skeleton Warrior holds
its scimitar in its left hand and throws with its right. This writes a source GLB with the true handedness:
- every clip is mirrored about the rig's mid-plane: world bone motion D_n(t) = W_n(t) W_n(rest)^-1 becomes S D_n(t) S on the
  partner bone (L <-> R), and the local TRS are rebuilt, so the rest pose, rest frames and bone lengths do not change;
- the L and R node names are swapped, so `Bip01 R Hand` is the anatomical right hand (now at -X);
- both weapon bones change hands and their meshes are mirrored with them;
- the body mesh is mirrored too (x, winding, joints to the partner bones): the skins are asymmetric (eye patch, braid, lacing). Sockets in the model.yml keep their
ABC names; RangeAttack is LHand1 = the anatomical left hand, the node now named LHand1.
Args: <in glb> <out glb>"""
import sys
import numpy as np
from pygltflib import GLTF2, Accessor, BufferView, AnimationChannel, AnimationChannelTarget, AnimationSampler, Animation

IN, OUT = sys.argv[1:3]
g = GLTF2().load(IN)
blob = bytearray(g.binary_blob())


def acc(i):
    a = g.accessors[i]; bv = g.bufferViews[a.bufferView]
    n = {'SCALAR': 1, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}[a.type]
    ct = {5126: 'f4', 5123: 'u2', 5125: 'u4', 5121: 'u1'}[a.componentType]
    return np.frombuffer(bytes(blob), ct, a.count * n, (bv.byteOffset or 0) + (a.byteOffset or 0)).reshape(a.count, n).copy()


def add(arr, ty, ct=5126, target=None, minmax=False):
    global blob
    while len(blob) % 4: blob.append(0)
    off = len(blob); data = arr.astype({5126: 'f4', 5123: 'u2', 5125: 'u4', 5121: 'u1'}[ct]).tobytes(); blob += data
    g.bufferViews.append(BufferView(buffer=0, byteOffset=off, byteLength=len(data), target=target))
    ac = Accessor(bufferView=len(g.bufferViews) - 1, componentType=ct, count=len(arr), type=ty)
    if minmax:
        ac.min = [float(x) for x in np.atleast_1d(arr.min(0))]; ac.max = [float(x) for x in np.atleast_1d(arr.max(0))]
    g.accessors.append(ac)
    return len(g.accessors) - 1


def qmat(q):
    x, y, z, w = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def matq(m):
    t = np.trace(m)
    if t > 0:
        s = np.sqrt(t + 1) * 2; q = [(m[2, 1] - m[1, 2]) / s, (m[0, 2] - m[2, 0]) / s, (m[1, 0] - m[0, 1]) / s, s / 4]
    else:
        i = int(np.argmax(np.diag(m))); j, k = (i + 1) % 3, (i + 2) % 3
        s = np.sqrt(1 + m[i, i] - m[j, j] - m[k, k]) * 2
        q = [0, 0, 0, 0]; q[i] = s / 4; q[j] = (m[j, i] + m[i, j]) / s; q[k] = (m[k, i] + m[i, k]) / s
        q[3] = (m[k, j] - m[j, k]) / s
    q = np.array(q); return q / np.linalg.norm(q)


def trs(t, q):
    m = np.eye(4); m[:3, :3] = qmat(q); m[:3, 3] = t; return m


nodes = g.nodes
parent = {c: i for i, n in enumerate(nodes) for c in (n.children or [])}
rest_t = [np.array(n.translation or [0, 0, 0], float) for n in nodes]
rest_q = [np.array(n.rotation or [0, 0, 0, 1], float) for n in nodes]
for n in nodes:
    assert n.scale in (None, [1, 1, 1], [1.0, 1.0, 1.0]) or np.allclose(n.scale, 1), n.name
name = {i: n.name for i, n in enumerate(nodes)}
idx = {n.name: i for i, n in enumerate(nodes)}


def partner(nm):
    for a, b in ((' L ', ' R '), (' R ', ' L ')):
        if a in nm: return nm.replace(a, b)
    return nm


swap = {i: idx.get(partner(name[i]), i) for i in name}
WEAP = []
skel = [i for i in name if nodes[i].mesh is None and i not in WEAP]
assert all(swap[swap[i]] == i for i in skel)


def order():
    seen, out = set(), []
    def visit(i):
        if i in seen: return
        if i in parent: visit(parent[i])
        seen.add(i); out.append(i)
    for i in name: visit(i)
    return out


ORDER = order()


def worlds(T, Q):
    W = {}
    for i in ORDER:
        L = trs(T[i], Q[i])
        W[i] = W[parent[i]] @ L if i in parent else L
    return W


W0 = worlds(rest_t, rest_q)
x0 = (W0[idx['Bip01 L UpperArm']][0, 3] + W0[idx['Bip01 R UpperArm']][0, 3]) / 2
print('mid-plane x', x0)
S = np.eye(4); S[0, 0] = -1; S[0, 3] = 2 * x0


def sample(times, ts, vs, path):
    i = np.clip(np.searchsorted(ts, times, 'right') - 1, 0, len(ts) - 1); j = np.minimum(i + 1, len(ts) - 1)
    u = np.where(ts[j] > ts[i], (times - ts[i]) / np.maximum(ts[j] - ts[i], 1e-9), 0.0)[:, None]
    if path == 'translation': return vs[i] * (1 - u) + vs[j] * u
    a, b = vs[i], vs[j].copy()
    b[(a * b).sum(1) < 0] *= -1
    q = a * (1 - u) + b * u
    return q / np.linalg.norm(q, axis=1, keepdims=True)


W0n = {}
new_parent = {w: swap[parent[w]] for w in WEAP}
for i in WEAP:
    nb = S @ W0[i]
    nb[:3, 0] *= -1                                 # a proper frame again: the mirrored bone's X flips back
    W0n[i] = nb

for an in g.animations:
    tracks = {}
    tset = set()
    for ch in an.channels:
        sm = an.samplers[ch.sampler]
        ts = acc(sm.input)[:, 0]; tset.update(np.round(ts, 6).tolist())
        tracks[(ch.target.node, ch.target.path)] = (ts, acc(sm.output))
    times = np.array(sorted(tset), float)
    T = {i: np.tile(rest_t[i], (len(times), 1)) for i in name}
    Q = {i: np.tile(rest_q[i], (len(times), 1)) for i in name}
    for (n, path), (ts, vs) in tracks.items():
        if path == 'translation': T[n] = sample(times, ts, vs, path)
        elif path == 'rotation': Q[n] = sample(times, ts, vs, path)
    allb = skel + WEAP
    outT = {i: np.zeros((len(times), 3)) for i in allb}; outQ = {i: np.zeros((len(times), 4)) for i in allb}
    for k in range(len(times)):
        W = worlds({i: T[i][k] for i in name}, {i: Q[i][k] for i in name})
        NW = {}
        for i in skel:
            src = swap[i]
            D = W[src] @ np.linalg.inv(W0[src])
            NW[i] = S @ D @ S @ W0[i]
        for i in WEAP:
            NW[i] = S @ (W[i] @ np.linalg.inv(W0[i])) @ S @ W0n[i]
        for i in allb:
            pi = new_parent.get(i, parent.get(i))
            L = np.linalg.inv(NW[pi]) @ NW[i] if pi is not None else NW[i]
            outT[i][k] = L[:3, 3]; outQ[i][k] = matq(L[:3, :3])
    for i in allb:
        q = outQ[i]
        for k in range(1, len(q)):
            if q[k] @ q[k - 1] < 0: q[k] *= -1
    inp = add(times, 'SCALAR', minmax=True)
    samplers, channels = [], []
    for i in allb:
        moved_t = i in WEAP or np.abs(outT[i] - rest_t[i]).max() > 1e-6
        moved_q = i in WEAP or np.abs(outQ[i] * np.sign((outQ[i] * rest_q[i]).sum(1, keepdims=True)) - rest_q[i]).max() > 1e-6
        if moved_t:
            samplers.append(AnimationSampler(input=inp, output=add(outT[i], 'VEC3'), interpolation='LINEAR'))
            channels.append(AnimationChannel(sampler=len(samplers) - 1, target=AnimationChannelTarget(node=i, path='translation')))
        if moved_q:
            samplers.append(AnimationSampler(input=inp, output=add(outQ[i], 'VEC4'), interpolation='LINEAR'))
            channels.append(AnimationChannel(sampler=len(samplers) - 1, target=AnimationChannelTarget(node=i, path='rotation')))
    an.samplers, an.channels = samplers, channels

# both weapons: to the other hand, mirrored
skin = g.skins[0]
ibm = acc(skin.inverseBindMatrices).reshape(-1, 4, 4).copy()
for i in WEAP:
    old_hand = parent[i]; new_hand = swap[old_hand]
    nodes[old_hand].children.remove(i); nodes[new_hand].children.append(i)
    L = np.linalg.inv(W0[new_hand]) @ W0n[i]
    nodes[i].translation = L[:3, 3].tolist(); nodes[i].rotation = matq(L[:3, :3]).tolist()
    ibm[skin.joints.index(i)] = np.linalg.inv(W0n[i]).T
skin.inverseBindMatrices = add(ibm.reshape(-1, 16), 'MAT4')
pos_in_skin = {n: k for k, n in enumerate(skin.joints)}
for bn in [n for n in nodes if n.mesh is not None]:      # the body pieces too: the skins are asymmetric, so the figure must be the game's
    for prim in g.meshes[bn.mesh].primitives:
        pos = acc(prim.attributes.POSITION).copy()
        prim.attributes.POSITION = add(pos * [-1, 1, 1] + [2 * x0, 0, 0], 'VEC3', minmax=True, target=34962)
        if prim.attributes.NORMAL is not None:
            prim.attributes.NORMAL = add(acc(prim.attributes.NORMAL) * [-1, 1, 1], 'VEC3', target=34962)
        ix = acc(prim.indices).reshape(-1, 3)[:, ::-1]
        prim.indices = add(ix.ravel(), 'SCALAR', ct=g.accessors[prim.indices].componentType, target=34963)
        jt = g.accessors[prim.attributes.JOINTS_0]
        J = acc(prim.attributes.JOINTS_0)
        Jn = J.copy()
        for k, n in enumerate(skin.joints):
            Jn[J == k] = pos_in_skin[swap[n]]
        prim.attributes.JOINTS_0 = add(Jn, 'VEC4', ct=jt.componentType, target=34962)
for i in skel:
    nodes[i].name = name[swap[i]]
g.buffers[0].byteLength = len(blob)
g.set_binary_blob(bytes(blob))
g.save(OUT)
print('mirrored', OUT, len(g.animations), 'clips')
