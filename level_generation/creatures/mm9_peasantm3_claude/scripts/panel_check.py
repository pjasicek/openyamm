"""Fraction of the moved panel faces' UV corners that land on tunic-coloured (red, covered) body texels.
Args: <body basecolor png> <export glb>"""
import sys, numpy as np
from PIL import Image
from pygltflib import GLTF2
img = np.asarray(Image.open(sys.argv[1]).convert('RGB'), float); N = img.shape[0]
g = GLTF2().load(sys.argv[2]); b = g.binary_blob()
def acc(i, n, dt=np.float32):
    a = g.accessors[i]; bv = g.bufferViews[a.bufferView]
    return np.frombuffer(b, dt, a.count * n, (bv.byteOffset or 0) + (a.byteOffset or 0)).reshape(-1, n)
p = next(p for m in g.meshes for p in m.primitives if g.materials[p.material].name == 'PeasantM3')
P = acc(p.attributes.POSITION, 3); UV = acc(p.attributes.TEXCOORD_0, 2)
sel = (P[:, 1] > 1.47) & (P[:, 1] < 1.53) & (np.abs(P[:, 0]) < 0.06) & (P[:, 2] > 0.04)
uv = UV[sel]; px = np.clip((uv * N).astype(int), 0, N - 1); c = img[px[:, 1], px[:, 0]]
red = (c[:, 0] > c[:, 1] * 1.6) & (c[:, 0] > 60)
print('PANELCHECK corners', int(sel.sum()), 'on tunic red %.2f' % red.mean())
