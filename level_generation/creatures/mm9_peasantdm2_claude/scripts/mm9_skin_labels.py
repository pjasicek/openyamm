#!/usr/bin/env python3
"""Label the MM9 PeasantDM2 skin (256 px) by body part from the MM9 mesh itself: every triangle of the raw conversion
(source/mm9/pdm2a.glb) is rasterised into its skin UVs with its dominant joint and rest height. Writes
work/mm9_skin_labels.npz (label per texel: 0 none, 1 head, 2 tunic incl. sleeves and skirt, 3 hands, 4 legs above the boot,
5 boots) and review/mm9_skin_labels.png (labels over both skins) for tiers_pdm2.py."""
import numpy as np
from PIL import Image
from pygltflib import GLTF2
g = GLTF2().load('source/mm9/pdm2a.glb'); blob = g.binary_blob()


def acc(i):
    a = g.accessors[i]; bv = g.bufferViews[a.bufferView]
    n = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}[a.type]
    dt = {5126: np.float32, 5123: np.uint16, 5125: np.uint32, 5121: np.uint8}[a.componentType]
    return np.frombuffer(blob, dt, a.count * n, (bv.byteOffset or 0) + (a.byteOffset or 0)).reshape(a.count, n)


names = [g.nodes[j].name for j in g.skins[0].joints]
N = 256
lab = np.zeros((N, N), int); zz = np.full((N, N), np.nan)
for m in g.meshes:
    for p in m.primitives:
        if p.attributes.JOINTS_0 is None:
            continue
        P = acc(p.attributes.POSITION); UV = acc(p.attributes.TEXCOORD_0); J = acc(p.attributes.JOINTS_0).astype(int)
        Wt = acc(p.attributes.WEIGHTS_0); T = acc(p.indices).reshape(-1, 3)
        dom = J[np.arange(len(J)), Wt.argmax(1)]
        for t in T:
            jn = names[np.bincount(dom[t]).argmax()]
            z = P[t, 1].mean()                       # glTF Y up
            if 'Head' in jn or 'Neck' in jn or 'Ponytail' in jn or 'Bone03' == jn:
                L = 1
            elif 'Hand' in jn or 'Finger' in jn:
                L = 3
            elif 'Calf' in jn or 'Foot' in jn or 'Toe' in jn:
                L = 5
            elif 'Thigh' in jn:
                L = 4
            else:
                L = 2
            uv = UV[t] * N
            x0, y0 = np.floor(uv.min(0)).astype(int); x1, y1 = np.ceil(uv.max(0)).astype(int)
            xs, ys = np.meshgrid(np.arange(max(x0, 0), min(x1, N - 1) + 1) + 0.5, np.arange(max(y0, 0), min(y1, N - 1) + 1) + 0.5)
            a, b, c = uv
            den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
            if abs(den) < 1e-9:
                continue
            l0 = ((b[1] - c[1]) * (xs - c[0]) + (c[0] - b[0]) * (ys - c[1])) / den
            l1 = ((c[1] - a[1]) * (xs - c[0]) + (a[0] - c[0]) * (ys - c[1])) / den
            ins = (l0 >= -0.02) & (l1 >= -0.02) & (1 - l0 - l1 >= -0.02)
            yy, xx = (ys[ins] - 0.5).astype(int), (xs[ins] - 0.5).astype(int)
            lab[yy, xx] = L; zz[yy, xx] = z
np.savez('work/mm9_skin_labels.npz', lab=lab, z=zz)
cols = np.array([[0, 0, 0], [255, 0, 0], [0, 0, 255], [255, 255, 0], [0, 255, 0], [255, 0, 255]], float)
out = []
for t in 'ab':
    a = np.asarray(Image.open(f'source/mm9/skins/pdm2{t}.png').convert('RGB'), float)
    out.append(a * 0.55 + cols[lab] * 0.45 * (lab > 0)[..., None])
Image.fromarray(np.uint8(np.concatenate(out, 1))).resize((1024, 512), Image.NEAREST).save('review/mm9_skin_labels.png')
print('LABELS', {k: int((lab == k).sum()) for k in range(6)})
