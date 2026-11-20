#!/usr/bin/env python3
"""Break the mirror symmetry of the leaf hood (mm9_greenman r3): the body was symmetrised before the head retexture, so
Meshy painted mirror twins on both halves and the back of the hood read as a Rorschach mask. Every green leaf part of
the head set (loose parts under 200 triangles whose median texel is green: not the face shell, hands, branches or the
staff) is scaled in brightness by a random factor in [1-J, 1+J] and nudged in hue (green/yellow balance +-H), seeded
per part, so twin leaves differ. Usage (project folder): leaf_jitter.py <export glb> <head png> [J 0.12] [H 0.06]"""
import sys
import numpy as np
from PIL import Image
sys.path.insert(0, 'scripts')
from leafparts import part_labels
glb, png = sys.argv[1:3]
J = float(sys.argv[3]) if len(sys.argv) > 3 else 0.12
Hh = float(sys.argv[4]) if len(sys.argv) > 4 else 0.06
img = np.asarray(Image.open(png).convert('RGB')).astype(np.float32)
lab, sizes, big = part_labels(glb, 'GreenManHead', img.shape[0])
rng = np.random.default_rng(266)
fb = rng.uniform(1 - J, 1 + J, len(sizes)); fh = rng.uniform(-Hh, Hh, len(sizes))
n = 0
for k in range(len(sizes)):
    if k == big or sizes[k] >= 200:
        continue
    m = lab == k
    if m.sum() < 20:
        continue
    med = np.median(img[m], 0)
    if not (med[1] > med[0] * 1.05 and med[1] > med[2] * 1.5):
        continue
    px = img[m] * fb[k]
    px[:, 0] *= 1 + fh[k]; px[:, 2] *= 1 - fh[k]
    img[m] = px; n += 1
Image.fromarray(np.uint8(np.clip(np.round(img), 0, 255))).save(png)
print('LEAFJITTER parts', n)
