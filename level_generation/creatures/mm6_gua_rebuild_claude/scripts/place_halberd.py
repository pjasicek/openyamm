#!/usr/bin/env python3
"""Re-seat the approved MM6 halberd attachment (mm6_gua_claude, user reviews 2159/2161; its own images and tier ramps untouched) on the
MM9 skeleton's weapon joint Xbase. Its local frame: grip at the origin, shaft along +Y toward the blade head, axe crescent on -X (the larger
side), Z through the blade. Placed by work/halberd_place.json (finish_gua.py, Blender frame): grip at G, blade head toward the spike (-U),
axe toward MM9's big blade (-W), scaled by the body's clean scale; then written in Xbase's bind frame of the runtime body GLB.
Args: <runtime body glb> <old halberd glb> <out glb>"""
import json, sys
from pathlib import Path
import numpy as np
from pygltflib import GLTF2
BODY, OLD, OUT = sys.argv[1:4]
HERE = Path(__file__).resolve().parents[1]
pl = json.load(open(HERE / 'work' / 'halberd_place.json')); S = json.load(open(HERE / 'work' / 'clean_v1.json'))['scale']
b = GLTF2().load(BODY); bb = b.binary_blob()
names = [n.name for n in b.nodes]; sk = b.skins[0]
ia = b.accessors[sk.inverseBindMatrices]; bv = b.bufferViews[ia.bufferView]
IBM = np.frombuffer(bb, np.float32, ia.count * 16, (bv.byteOffset or 0) + (ia.byteOffset or 0)).reshape(-1, 4, 4).transpose(0, 2, 1)
j = [names[k] for k in sk.joints].index('Xbase')
M = np.linalg.inv(IBM[j].astype(float))
g = lambda v: np.array([v[0], v[2], -v[1]], float)            # Blender Z-up -> glTF Y-up (directions)
xb = np.array(pl['xbase']); lift = M[1, 3] - xb[2]
print('XBASE gltf', M[:3, 3].round(4), 'blender', xb.round(4), 'lift', round(lift, 4), 'x/z check', round(M[0, 3] - xb[0], 4), round(M[2, 3] + xb[1], 4))
G = g(pl['G']) + [0, lift, 0]; U, W, D = g(pl['U']), g(pl['W']), g(pl['D'])
R = np.c_[W, -U, D]                                             # columns: where local X, Y, Z go
assert abs(np.linalg.det(R) - 1) < 1e-3, np.linalg.det(R)
A = np.eye(4); A[:3, :3] = R * S; A[:3, 3] = G                  # old local -> glTF world
L = np.linalg.inv(M) @ A                                        # -> Xbase local
h = GLTF2().load(OLD); hb = bytearray(h.binary_blob())
done = set()
for mesh in h.meshes:
    for p in mesh.primitives:
        for key, kind in ((p.attributes.POSITION, 'p'), (p.attributes.NORMAL, 'n')):
            if key is None or key in done: continue
            done.add(key); a = h.accessors[key]; v = h.bufferViews[a.bufferView]; off = (v.byteOffset or 0) + (a.byteOffset or 0)
            X = np.frombuffer(bytes(hb[off:off + a.count * 12]), np.float32).reshape(-1, 3).astype(float)
            if kind == 'p':
                Y = X @ L[:3, :3].T + L[:3, 3]; a.min = Y.min(0).tolist(); a.max = Y.max(0).tolist()
            else:
                Y = X @ (L[:3, :3] / S).T; Y /= np.linalg.norm(Y, axis=1, keepdims=True)
            hb[off:off + a.count * 12] = Y.astype(np.float32).tobytes()
h.set_binary_blob(bytes(hb)); h.save(OUT)
print('HALBERD placed', OUT, 'accessors', len(done))
