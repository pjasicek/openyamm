#!/usr/bin/env python3
"""Re-seat the approved MM6 merchant club attachment (mm6_mer1_club.glb: grip centre at the origin, handle along +Y to the head; its images,
LODs and shadow primitives untouched) on the body's `Club` joint (child of Bip01 Spine; place_halberd.py of the Guard rebuild adapted).
Placed by work/club_place.json (finish_mer.py, Blender frame) `belt`: grip at G, head along U (down the right hip), local X along A, scaled
with the body; written in Club's bind frame of the runtime body GLB. club_keys.py moves the joint into the fist in the attack.
Args: <runtime body glb> <old club glb> <out glb>"""
import json, sys
from pathlib import Path
import numpy as np
from pygltflib import GLTF2
BODY, OLD, OUT = sys.argv[1:4]
HERE = Path(__file__).resolve().parents[1]
pl = json.load(open(HERE / 'work' / 'club_place.json')); S = pl['scale']
b = GLTF2().load(BODY); bb = b.binary_blob()
names = [n.name for n in b.nodes]; sk = b.skins[0]
ia = b.accessors[sk.inverseBindMatrices]; bv = b.bufferViews[ia.bufferView]
IBM = np.frombuffer(bb, np.float32, ia.count * 16, (bv.byteOffset or 0) + (ia.byteOffset or 0)).reshape(-1, 4, 4).transpose(0, 2, 1)
j = [names[k] for k in sk.joints].index('Club')
M = np.linalg.inv(IBM[j].astype(float))
g = lambda v: np.array([v[0], v[2], -v[1]], float)            # Blender Z-up -> glTF Y-up
yb = np.array(pl['belt']['G']); lift = M[1, 3] - yb[2]
print('CLUB joint gltf', M[:3, 3].round(4), 'blender', yb.round(4), 'lift', round(lift, 4), 'x/z check', round(M[0, 3] - yb[0], 4), round(M[2, 3] + yb[1], 4))
U, A = g(pl['belt']['U']), g(pl['belt']['A']); A = A - U * (A @ U); A /= np.linalg.norm(A); Z = np.cross(A, U)
R = np.c_[A, U, Z]
assert abs(np.linalg.det(R) - 1) < 1e-3, np.linalg.det(R)
G = g(pl['belt']['G']) + [0, lift, 0]
T = np.eye(4); T[:3, :3] = R * S; T[:3, 3] = G - U * pl['tc']          # club local (0, tc/S, 0) -> G
L = np.linalg.inv(M) @ T
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
print('CLUB placed', OUT, 'accessors', len(done))
