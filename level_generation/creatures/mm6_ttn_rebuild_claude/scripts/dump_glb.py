"""Dump the installed GLB's images and LOD0 arrays (positions, uv, joints, weights, indices) for inspection."""
import sys, io, json, os
import numpy as np
from pygltflib import GLTF2
from PIL import Image
g = GLTF2().load(sys.argv[1]); out = sys.argv[2]; os.makedirs(out, exist_ok=True)
blob = g.binary_blob()
def acc(i):
    a = g.accessors[i]; bv = g.bufferViews[a.bufferView]
    dt = {5126: np.float32, 5123: np.uint16, 5125: np.uint32, 5121: np.uint8}[a.componentType]
    n = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}[a.type]
    stride = bv.byteStride or np.dtype(dt).itemsize * n
    raw = np.frombuffer(blob, np.uint8, count=stride * (a.count - 1) + np.dtype(dt).itemsize * n, offset=(bv.byteOffset or 0) + (a.byteOffset or 0))
    arr = np.lib.stride_tricks.as_strided(raw.view(dt) if stride % np.dtype(dt).itemsize == 0 else raw, shape=(a.count, n), strides=(stride, np.dtype(dt).itemsize)).copy()
    if a.normalized and dt == np.uint8: arr = arr / 255.0
    if a.normalized and dt == np.uint16 and a.type != 'SCALAR': arr = arr / 65535.0
    return arr
for im in g.images:
    bv = g.bufferViews[im.bufferView]
    img = Image.open(io.BytesIO(blob[(bv.byteOffset or 0):(bv.byteOffset or 0) + bv.byteLength]))
    img.save(os.path.join(out, im.name + '.png')); print(im.name, img.size, img.mode)
p = g.meshes[0].primitives[0]; a = p.attributes
np.savez(os.path.join(out, 'lod0.npz'), pos=acc(a.POSITION), uv=acc(a.TEXCOORD_0), j=acc(a.JOINTS_0), w=acc(a.WEIGHTS_0), idx=acc(p.indices).ravel(),
         names=np.array([g.nodes[j].name for j in g.skins[0].joints]))
