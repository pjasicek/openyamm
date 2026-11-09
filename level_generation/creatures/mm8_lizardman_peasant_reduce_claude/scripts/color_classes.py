#!/usr/bin/env python3
"""Per-face base-colour class of the rest mesh (9 samples per face in the merged atlas): ivory (bright, unsaturated:
neck/calf fringes, arm bands, claws), gold (trim), red (apron checks), green (tunic), brown (belt, collar), teal
(skin), other -> work/color_class.npy (str per face); prints counts and, with work/verr_<cand>.npy, error per class."""
import sys
import colorsys
import numpy as np
from PIL import Image
d = np.load('work/mesh_in.npz'); f = d['faces']; uv = d['wuv'].reshape(-1, 3, 2)
img = np.asarray(Image.open('work/basecolor.png').convert('RGB'), np.float32) / 255; H, W = img.shape[:2]
B = np.random.default_rng(1).dirichlet((1, 1, 1), 9)
u = np.einsum('sk,fkc->fsc', B, uv)
x = np.clip((u[..., 0] % 1) * W, 0, W - 1).astype(int); y = np.clip((1 - u[..., 1] % 1) * H, 0, H - 1).astype(int)
col = img[y, x].reshape(-1, 3)
hsv = np.array([colorsys.rgb_to_hsv(*c) for c in col]).reshape(len(f), 9, 3)
h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
cls = np.full(h.shape, 'other', object)
cls[(h > .4) & (h < .6) & (s > .3)] = 'teal'
cls[(h > .22) & (h < .42) & (s > .35)] = 'green'
cls[((h < .04) | (h > .95)) & (s > .45)] = 'red'
cls[(h >= .04) & (h < .10) & (s > .45) & (v < .6)] = 'brown'
cls[(h >= .08) & (h < .17) & (s > .45) & (v >= .5)] = 'gold'
cls[(s < .28) & (v > .62)] = 'ivory'
face = np.array([max(set(r), key=list(r).count) for r in cls])
np.save('work/color_class.npy', face.astype(str))
for k in np.unique(face):
    print('CLASS', k, int((face == k).sum()))
if len(sys.argv) > 1:
    e = np.load(sys.argv[1])[f].max(1) * 1000
    for k in np.unique(face):
        m = face == k; print(f'ERR {k:6s} faces {m.sum():5d} p99 {np.percentile(e[m], 99):6.2f} max {e[m].max():6.2f} >5.1mm {(e[m] > 5.1).sum()}')
