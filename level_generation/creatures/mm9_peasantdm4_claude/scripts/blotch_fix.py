#!/usr/bin/env python3
"""Lift Meshy's dark stains on the ochre cloth (PeasantDM4, 2026-11-02: dark blotches 1-4 cm across on the puffed
sleeves and the skirt; the master and MM9 have none). On the graded body colour: ochre cloth texels (hue 25-60 deg,
saturation > 0.5) whose small-scale luminance (Gaussian SIGMA_S px, inside the cloth mask) falls below RATIO x the
broad luminance (SIGMA_B px) are lifted by the gain broad/small (capped), feathered; the knit's fine detail (the image
over its small blur) stays. Reads textures/pdm4_tp_basecolor_graded_preblotch.png (first-run backup), writes
textures/pdm4_tp_basecolor_graded.png and review/blotch_mask.png. Usage (project folder): blotch_fix.py [ratio 0.72]"""
import shutil, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

RATIO = float(sys.argv[1]) if len(sys.argv) > 1 else 0.72
SIGMA_S, SIGMA_B = 6.0, 28.0
f = Path('textures/pdm4_tp_basecolor_graded.png'); bk = f.with_name(f.stem + '_preblotch.png')
if not bk.exists():
    shutil.copyfile(f, bk)
img = np.asarray(Image.open(bk).convert('RGB')).astype(float)
mx = img.max(2); mn = img.min(2); sat = (mx - mn) / np.maximum(mx, 1)
r, g, b = img[..., 0], img[..., 1], img[..., 2]
hue = np.degrees(np.arctan2(np.sqrt(3) * (g - b), 2 * r - g - b)) % 360
cloth = (hue > 25) & (hue < 60) & (sat > 0.5) & (mx > 20)
cloth = ndi.binary_opening(cloth, iterations=2)
L = img @ [0.2126, 0.7152, 0.0722]
cm = cloth.astype(float)


def mblur(x, s):
    return ndi.gaussian_filter(x * cm, s) / np.maximum(ndi.gaussian_filter(cm, s), 1e-3)


Ls = mblur(L, SIGMA_S); Lb = mblur(L, SIGMA_B)
blot = cloth & (Ls < RATIO * Lb)
blot = ndi.binary_opening(blot, iterations=1)
lab, n = ndi.label(blot)
size = ndi.sum(blot, lab, range(1, n + 1))
keep = np.isin(lab, np.nonzero((size >= 30) & (size <= 6000))[0] + 1)
w = ndi.gaussian_filter(ndi.binary_dilation(keep, iterations=3).astype(float), 3.0) * cloth
gain = np.clip(Lb / np.maximum(Ls, 1), 1.0, 2.2)
out = img * (1 + (gain[..., None] - 1) * w[..., None])
Image.fromarray(np.uint8(np.clip(out, 0, 255))).save(f)
Image.fromarray(np.uint8(np.clip(w, 0, 1) * 255)).save('review/blotch_mask.png')
print('BLOTCH_FIX blobs', int(len(np.unique(lab[keep])) - (0 in lab[keep])), 'texels', int(keep.sum()), 'ratio', RATIO)
