#!/usr/bin/env python3
"""Move a joint's pivot (the joint and its half helper <joint>_h) by a world offset at rest, on a GLB with or without clips:
node translations, every translation key of the joint (in its parent's frame), its children's translations and keys
(back by the same offset in the joint's frame, so they stay put at rest) and the inverse bind matrices; the mesh and its
weights stay. Run half_keys.py afterwards when the GLB has clips. Mirror x for the left/right pair yourself.
Args: <in glb> <out glb> <dx> <dy> <dz> [joint, default 'Bip01 Head'] (metres, glTF axes)"""
import sys
from pathlib import Path
import numpy as np
from pygltflib import GLTF2, Accessor, BufferView
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
IN, OUT = sys.argv[1:3]; d = np.array([float(x) for x in sys.argv[3:6]]); JN = sys.argv[6] if len(sys.argv) > 6 else 'Bip01 Head'
m = Model(Glb(Path(IN))); names = [n.get('name') for n in m.glb.json['nodes']]
w0 = m.world({}); ji = names.index(JN); s3 = m.parent[ji]
Rp = w0[s3][:3, :3]; dl = np.linalg.solve(Rp, d)          # the offset in the parent's frame (with its scale)
dc = np.linalg.solve(w0[ji][:3, :3], d)                   # and in the joint's own frame, for its children
g = GLTF2().load(IN); blob = bytearray(g.binary_blob())
def put(arr, typ):
    global blob
    while len(blob) % 4: blob.append(0)
    o = len(blob); b = np.asarray(arr, 'f4').tobytes(); blob += b
    g.bufferViews.append(BufferView(buffer=0, byteOffset=o, byteLength=len(b)))
    g.accessors.append(Accessor(bufferView=len(g.bufferViews) - 1, componentType=5126, count=len(arr), type=typ))
    return len(g.accessors) - 1
def acc(i, n):
    a = g.accessors[i]; bv = g.bufferViews[a.bufferView]
    return np.frombuffer(bytes(blob), 'f4', a.count * n, (bv.byteOffset or 0) + (a.byteOffset or 0)).reshape(a.count, n).astype(float)
targets = [ji, names.index(JN + '_h')]
kids = list(g.nodes[ji].children or [])
for c in kids:
    g.nodes[c].translation = [float(x) for x in np.array(g.nodes[c].translation or [0, 0, 0]) - dc]
for i in targets:
    g.nodes[i].translation = [float(x) for x in np.array(g.nodes[i].translation or [0, 0, 0]) + dl]
sk = g.skins[0]; IB = acc(sk.inverseBindMatrices, 16).reshape(-1, 4, 4).transpose(0, 2, 1)      # column-major
Tm = np.eye(4); Tm[:3, 3] = -d
for k, j in enumerate(sk.joints):
    if j in targets: IB[k] = IB[k] @ Tm
sk.inverseBindMatrices = put(IB.transpose(0, 2, 1).reshape(-1, 16), 'MAT4')
n = 0
for an in g.animations:
    for ch in an.channels:
        if ch.target.node == targets[0] and ch.target.path == 'translation':
            sm = an.samplers[ch.sampler]; sm.output = put(acc(sm.output, 3) + dl, 'VEC3'); n += 1
        elif ch.target.node in kids and ch.target.path == 'translation':
            sm = an.samplers[ch.sampler]; sm.output = put(acc(sm.output, 3) - dc, 'VEC3')
g.buffers[0].byteLength = len(blob); g.set_binary_blob(bytes(blob)); g.save(OUT)
print('PIVOT', JN, 'moved', d, 'keys', n, 'children', [g.nodes[c].name for c in kids])
