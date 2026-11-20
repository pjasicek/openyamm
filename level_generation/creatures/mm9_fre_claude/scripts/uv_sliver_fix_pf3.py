#!/usr/bin/env python3
"""UV slivers on the head (pass 5, viewer close-up): tweak_pf1.py closes the mouth slit and Meshy's small holes by collapsing rims, which
leaves triangles a fraction of a millimetre across in 3D whose corners sit in different UV islands; across one triangle the texture then runs
over the gutters between islands (a pale glint along the lip line). Every head triangle with an edge stretched more than 4x the head's median
UV density gets its own rows, all three on the corner whose texel (tier A paint) has the median luminance of the three.
Args: <npz in> <npz out> <tier A head png>   (project folder)"""
import sys
import numpy as np
from PIL import Image
D = dict(np.load(sys.argv[1])); tri, uv, co, mat, comp = D['tri'], D['uv'], D['co'], D['mat'], D['comp']
names = [str(x) for x in D['names']]; kh = names.index('head')
im = np.asarray(Image.open(sys.argv[3]).convert('RGB'), np.float32) @ np.array([0.2126, 0.7152, 0.0722]); S = im.shape[0]
H = np.where((mat == 1) & (comp[tri[:, 0]] == kh))[0]
E3 = np.linalg.norm(co[tri[H]][:, [1, 2, 0]] - co[tri[H]], axis=2); E2 = np.linalg.norm(uv[tri[H]][:, [1, 2, 0]] - uv[tri[H]], axis=2)
dens = np.median(E2[E3 > 1e-4] / E3[E3 > 1e-4])
bad = H[((E2 / np.maximum(E3, 1e-9)) > 4 * dens).any(1) & (E2 > 2.0 / S).any(1)]
new = []
for f in bad:
    t = tri[f].copy(); px = np.clip(((1 - uv[t, 1]) * S).astype(int), 0, S - 1), np.clip((uv[t, 0] * S).astype(int), 0, S - 1)
    k = int(np.argsort(im[px])[1])
    for j in range(3):
        new.append((t[j], t[k])); tri[f, j] = len(co) + len(new) - 1
if new:
    src = np.array([a for a, _ in new]); uvs = np.array([b for _, b in new])
    for key in ('co', 'orig', 'comp'): D[key] = np.concatenate([D[key], D[key][src]])
    D['uv'] = np.vstack([D['uv'], D['uv'][uvs]]); D['tri'] = tri
np.savez(sys.argv[2], **D)
print('UV SLIVERS', len(bad), 'triangles on single texels, rows added', len(new))
