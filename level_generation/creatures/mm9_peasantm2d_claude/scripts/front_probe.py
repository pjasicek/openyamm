"""Which faces are frontmost (glTF +Z, the figure's front) in a region at a clip pose; their material, texel luminance, normal z.
Args: <glb> <clip> <time> <x0> <x1> <y0> <y1>"""
import sys, io
import numpy as np
from PIL import Image
sys.path.insert(0, '../claude_shared/floor')
from glb_pose import Glb, Model
g, clip, t = sys.argv[1], sys.argv[2], float(sys.argv[3]); x0, x1, y0, y1 = map(float, sys.argv[4:8])
G = Glb(g); m = Model(G); doc = G.json
posed = m.skinned_positions(m.world(m.sample(clip, t)))
mesh_prims = [(n, p) for n in m.order if 'mesh' in doc['nodes'][n] for p in doc['meshes'][doc['nodes'][n]['mesh']]['primitives']]
best = {}
k = 0
for (node, prim), (pts, tri) in zip([x for x in mesh_prims if 'LOD' not in (doc['meshes'][doc['nodes'][x[0]]['mesh']].get('name') or '') or 'LOD0' in (doc['meshes'][doc['nodes'][x[0]]['mesh']].get('name') or '')], posed):
    c = pts[tri].mean(1)
    a, b, cc = (pts[tri[:, i]] for i in range(3)); n = np.cross(b - a, cc - a); n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
    sel = np.where((np.abs(c[:, 0]) > x0) & (np.abs(c[:, 0]) < x1) & (c[:, 1] > y0) & (c[:, 1] < y1))[0]
    for i in sel:
        key = (int(c[i, 0] / 0.02), int(c[i, 1] / 0.02))
        if key not in best or c[i, 2] > best[key][0]: best[key] = (c[i, 2], k, i, n[i, 2], prim)
    k += 1
mats = doc['materials']
uvcache = {}
from collections import Counter
cnt = Counter(); dark = []
for key, (z, k, i, nz, prim) in best.items():
    mn = mats[prim['material']]['name']
    if k not in uvcache:
        uvcache[k] = G.accessor(prim['attributes']['TEXCOORD_0']); idx = G.accessor(prim['indices']).astype(int).reshape(-1, 3)
        tex = doc['textures'][mats[prim['material']]['pbrMetallicRoughness']['baseColorTexture']['index']]['source']
        bv = doc['bufferViews'][doc['images'][tex]['bufferView']]
        im = np.asarray(Image.open(io.BytesIO(G.bin[bv.get('byteOffset', 0):bv.get('byteOffset', 0) + bv['byteLength']])).convert('RGB'), float)
        uvcache[k] = (uvcache[k], idx, im)
    uv, idx, im = uvcache[k]; u = uv[idx[i]].mean(0); S = im.shape[0]
    lum = im[int(np.clip(u[1] * S, 0, S - 1)), int(np.clip(u[0] * S, 0, S - 1))].mean()
    cnt[(mn, lum < 30, nz < 0)] += 1
    if nz < 0: dark.append((round(key[0] * 0.02, 2), round(key[1] * 0.02, 2), mn, int(i), round(float(nz), 2), round(float(lum), 1), np.round(u, 3).tolist()))
print('PROBE', dict(cnt)); [print('DARK', d) for d in dark[:30]]
