#!/usr/bin/env python3
"""Label each MM9 boy skin (128 px) by body part from its own MM9 mesh (the three models map their skins differently:
PEASANTBOY1E puts the green tunic block on its sleeves). Every triangle of source/mm9/<id>.glb is rasterised into its
skin UVs with its dominant joint and height (glTF Y, MM9 floor at -0.4824). Labels: 0 none, 1 head, 2 vest (torso
below the neck, above the hem), 3 hands, 4 trousers, 5 boots (below BOOT_TOP), 6 sleeves (arm joints), 7 belt (torso
in the belt band). Writes work/mm9_skin_labels_<id>.npz and review/mm9_skin_labels.png. Project folder."""
import numpy as np
from PIL import Image
from pygltflib import GLTF2
FLOOR = -0.4824
BOOT_TOP, HEM, BELT = FLOOR + 0.35, FLOOR + 0.58, (FLOOR + 0.735, FLOOR + 0.81)
N = 128
cols = np.array([[0, 0, 0], [255, 0, 0], [0, 0, 255], [255, 255, 0], [0, 255, 0], [255, 0, 255], [0, 255, 255],
                 [255, 255, 255]], float)
out = []
for mid in ('pboy1', 'pboy2', 'pboy1e'):
    g = GLTF2().load(f'source/mm9/{mid}.glb'); blob = g.binary_blob()

    def acc(i):
        a = g.accessors[i]; bv = g.bufferViews[a.bufferView]
        n = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}[a.type]
        dt = {5126: np.float32, 5123: np.uint16, 5125: np.uint32, 5121: np.uint8}[a.componentType]
        return np.frombuffer(blob, dt, a.count * n, (bv.byteOffset or 0) + (a.byteOffset or 0)).reshape(a.count, n)
    names = [g.nodes[j].name for j in g.skins[0].joints]
    lab = np.zeros((N, N), int)
    for m in g.meshes:
        for p in m.primitives:
            if p.attributes.JOINTS_0 is None:
                continue
            P = acc(p.attributes.POSITION); UV = acc(p.attributes.TEXCOORD_0); J = acc(p.attributes.JOINTS_0).astype(int)
            Wt = acc(p.attributes.WEIGHTS_0); T = acc(p.indices).reshape(-1, 3)
            if len(T) < 5:
                continue
            dom = J[np.arange(len(J)), Wt.argmax(1)]
            for t in T:
                jn = names[np.bincount(dom[t]).argmax()]
                z = P[t, 1].mean()
                if 'Head' in jn or 'Neck' in jn:
                    L = 1
                elif 'Hand' in jn or 'Finger' in jn:
                    L = 3
                elif 'Arm' in jn or 'Forearm' in jn:
                    L = 6
                elif z < BOOT_TOP:
                    L = 5
                elif 'Thigh' in jn or 'Calf' in jn or z < HEM - 0.02:
                    L = 4
                elif BELT[0] < z < BELT[1]:
                    L = 7
                else:
                    L = 2
                uv = UV[t] * N
                x0, y0 = np.floor(uv.min(0)).astype(int); x1, y1 = np.ceil(uv.max(0)).astype(int)
                xs, ys = np.meshgrid(np.arange(max(x0, 0), min(x1, N - 1) + 1) + 0.5,
                                     np.arange(max(y0, 0), min(y1, N - 1) + 1) + 0.5)
                a, b, c = uv
                den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
                if abs(den) < 1e-9:
                    continue
                l0 = ((b[1] - c[1]) * (xs - c[0]) + (c[0] - b[0]) * (ys - c[1])) / den
                l1 = ((c[1] - a[1]) * (xs - c[0]) + (a[0] - c[0]) * (ys - c[1])) / den
                ins = (l0 >= -0.02) & (l1 >= -0.02) & (1 - l0 - l1 >= -0.02)
                yy, xx = (ys[ins] - 0.5).astype(int), (xs[ins] - 0.5).astype(int)
                lab[yy % N, xx % N] = L
    np.savez(f'work/mm9_skin_labels_{mid}.npz', lab=lab)
    a = np.asarray(Image.open(f'source/mm9/skins/{mid}.png').convert('RGB'), float)
    out.append(a * 0.5 + cols[lab] * 0.5 * (lab > 0)[..., None])
    print('LABELS', mid, {k: int((lab == k).sum()) for k in range(8)})
Image.fromarray(np.uint8(np.concatenate(out, 1))).resize((1536, 512), Image.NEAREST).save('review/mm9_skin_labels.png')
