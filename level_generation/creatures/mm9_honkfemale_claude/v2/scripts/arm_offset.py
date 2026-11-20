#!/usr/bin/env python3
"""One constant shoulder offset on every clip (Honk female: MM9's arms hang close to a slim dress, the HD dress is wider). A constant
rotation cannot add jitter, unlike a per-clip push. The upper arm's local rotation q becomes d * q, d = the rotation about the actor's
forward axis expressed in the parent's rest frame, so each arm swings out by `deg` in every frame of every clip.
Usage: arm_offset.py in.glb out.glb <deg> [--names "Bip01 L UpperArm" "Bip01 R UpperArm"]   (L is on -x before mirror_glb.py)"""
import json, struct, sys
import numpy as np
src, dst, deg = sys.argv[1], sys.argv[2], float(sys.argv[3])
raw = open(src, 'rb').read()
n = struct.unpack_from('<I', raw, 12)[0]
doc = json.loads(raw[20:20 + n])
blob = bytearray(raw[20 + n + 8:])
def qmul(a, b):
    ax, ay, az, aw = a; bx, by, bz, bw = b
    return np.array([aw*bx + ax*bw + ay*bz - az*by, aw*by - ax*bz + ay*bw + az*bx, aw*bz + ax*by - ay*bx + az*bw, aw*bw - ax*bx - ay*by - az*bz])
def qconj(q): return q * np.array([-1, -1, -1, 1.0])
par = {}
for i, nd in enumerate(doc['nodes']):
    for c in nd.get('children', []): par[c] = i
def world_q(i):
    q = np.array(doc['nodes'][i].get('rotation', [0, 0, 0, 1.0]))
    while i in par:
        i = par[i]; q = qmul(np.array(doc['nodes'][i].get('rotation', [0, 0, 0, 1.0])), q)
    return q
names = {nd.get('name'): i for i, nd in enumerate(doc['nodes'])}
ds = {}
for name, sgn in (('Bip01 L UpperArm', -1), ('Bip01 R UpperArm', 1)):
    i = names[name]; Rp = world_q(par[i])
    a = np.radians(deg) * sgn / 2
    D = np.array([0, 0, np.sin(a), np.cos(a)])       # glTF +z is the actor's forward axis here
    ds[i] = qmul(qmul(qconj(Rp), D), Rp)
done = set(); count = 0
for an in doc['animations']:
    for ch in an['channels']:
        i = ch['target'].get('node')
        if i in ds and ch['target']['path'] == 'rotation':
            ac = an['samplers'][ch['sampler']]['output']
            if ac in done: continue
            done.add(ac)
            a = doc['accessors'][ac]; bv = doc['bufferViews'][a['bufferView']]
            off = bv.get('byteOffset', 0) + a.get('byteOffset', 0)
            q = np.frombuffer(blob, np.float32, a['count'] * 4, off).reshape(-1, 4).astype(np.float64)
            out = np.array([qmul(ds[i], x) for x in q]); out /= np.linalg.norm(out, axis=1, keepdims=True)
            blob[off:off + a['count'] * 16] = out.astype(np.float32).tobytes(); count += 1
enc = json.dumps(doc, separators=(',', ':')).encode(); enc += b' ' * (-len(enc) % 4)
blob += b'\0' * (-len(blob) % 4)
open(dst, 'wb').write(struct.pack('<III', 0x46546c67, 2, 28 + len(enc) + len(blob)) + struct.pack('<II', len(enc), 0x4e4f534a) + enc + struct.pack('<II', len(blob), 0x004e4942) + bytes(blob))
print('ARMOFFSET', deg, 'deg on', count, 'clip channels')
