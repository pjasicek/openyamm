#!/usr/bin/env python3
"""Lift Meshy's dark stains on the ochre cloth, measured on the surface (PeasantDM4, 2026-11-02: dark blotches 2-5 cm
across on the puffed sleeves and the skirt; the HD masters and MM9 have none). blotch_fix.py's image-space test missed
blotches at UV island edges, so here every body texel's rest position (static export, 512 grid) is a point: ochre
cloth texels (hue 25-60 deg, saturation > 0.5) compare the mean luminance of their K_S nearest cloth points (about 1 cm)
with that of their K_B nearest (about 6 cm); where the small mean is below RATIO x the broad one, the colour is lifted by
broad/small (cap 2.2), feathered, upsampled to 2K. The knit's fine detail stays (a gain, not a repaint).
Reads textures/pdm4_tp_basecolor_graded_preblotch.png (first-run backup of the graded paint), writes
textures/pdm4_tp_basecolor_graded.png and review/blotch3d_mask.png.
Usage (project folder): blotch_fix3d.py [ratio 0.78] [export glb work/pdm4_body_tex.glb] [K_S 40] [K_B 1500] (about 2 and 10 cm: a
4 cm painted patch filled a 260-point broad window by itself)"""
import shutil, sys
sys.path.insert(0, 'scripts')
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from scipy.spatial import cKDTree
from headpos import texel_positions

RATIO = float(sys.argv[1]) if len(sys.argv) > 1 else 0.78
glb = sys.argv[2] if len(sys.argv) > 2 else 'work/pdm4_body_tex.glb'
K_S, K_B, N = int(sys.argv[3]) if len(sys.argv) > 3 else 40, int(sys.argv[4]) if len(sys.argv) > 4 else 1500, 512
f = Path('textures/pdm4_tp_basecolor_graded.png'); bk = f.with_name(f.stem + '_preblotch.png')
if not bk.exists():
    shutil.copyfile(f, bk)
full = Image.open(bk).convert('RGB'); W = full.size[0]
img = np.asarray(full.resize((N, N), Image.BOX)).astype(float)
pos, cov = texel_positions(glb, 'PeasantDM4', N)
mx = img.max(2); mn = img.min(2); sat = (mx - mn) / np.maximum(mx, 1)
r, g, b = img[..., 0], img[..., 1], img[..., 2]
hue = np.degrees(np.arctan2(np.sqrt(3) * (g - b), 2 * r - g - b)) % 360
cloth = cov & (hue > 25) & (hue < 60) & (sat > 0.5) & (mx > 20)
iy, ix = np.nonzero(cloth)
P = pos[iy, ix]; L = (img @ [0.2126, 0.7152, 0.0722])[iy, ix]
tree = cKDTree(P)
gain = np.ones(len(P)); hit = np.zeros(len(P), bool)
for a in range(0, len(P), 4000):                        # chunks: bounded memory
    _, nb = tree.query(P[a:a + 4000], k=K_B)
    Lb = L[nb].mean(1); Ls = L[nb[:, :K_S]].mean(1)
    h = Ls < RATIO * Lb
    hit[a:a + 4000] = h
    gain[a:a + 4000] = np.where(h, np.clip(Lb / np.maximum(Ls, 1), 1, 2.2), 1)
G = np.ones((N, N)); M = np.zeros((N, N))
G[iy, ix] = gain; M[iy, ix] = hit
M = ndi.binary_opening(M > 0, iterations=1)
M = ndi.gaussian_filter(ndi.binary_dilation(M, iterations=1).astype(float), 1.0) * cloth
G = ndi.gaussian_filter(np.where(cloth, G, 1.0), 1.0)
Gf = np.asarray(Image.fromarray(np.float32(1 + (G - 1) * M)).resize((W, W), Image.BILINEAR))
cl = np.asarray(Image.fromarray(np.uint8(cloth) * 255).resize((W, W), Image.NEAREST)) > 0
cl = ndi.binary_dilation(cl, iterations=4)
src = np.asarray(full).astype(float)
out = src * np.where(cl, Gf, 1.0)[..., None]
Image.fromarray(np.uint8(np.clip(out, 0, 255))).save(f)
Image.fromarray(np.uint8(np.clip(M, 0, 1) * 255)).save('review/blotch3d_mask.png')
print('BLOTCH3D cloth points', len(P), 'blotch points', int(hit.sum()), 'ratio', RATIO, 'max gain', round(float(gain.max()), 2))
