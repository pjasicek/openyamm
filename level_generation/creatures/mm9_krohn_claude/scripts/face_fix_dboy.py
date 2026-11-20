#!/usr/bin/env python3
"""Face paint fixes on a dwarf-boy head set (positions from head_texel_pos.py: glTF rest, floor 0, +Z front).
Starts from work/<prefix>_head_basecolor_composed.png (compose_headhand.py's output, kept as the backup) and writes
textures/<prefix>_head_basecolor.png.
1. Closed mouth: in the mouth box (|x| < MX, |y - LIP| < 9 mm, front) light low-saturation texels between the lips
   (Meshy painted teeth) take a soft lip shadow (the lips' median x 0.62), feathered 1 px;
   the skin-tone gap between the two lip bands (boy b: read as parted lips) becomes lip (median x 0.9).
2. Lips without lipstick: lip texels (redness r/g above the cheek's by > 0.12) move DESAT of the way to the cheek
   skin's own hue at their own luminance (b's Meshy lips were saturated red), the fine detail stays.
3. Writes work/hand_ref_<prefix>.txt (the cheek skin median) for hand_clean.py.
Usage (project folder): face_fix_dboy.py <prefix> [desat 0.35] [lip y 0.81]"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage
P = sys.argv[1]
DESAT = float(sys.argv[2]) if len(sys.argv) > 2 else 0.35
LIP = float(sys.argv[3]) if len(sys.argv) > 3 else 0.81
MX = float(__import__("os").environ.get("MX", 0.024))
pos = np.load('work/head_texel_pos.npz')['pos']
ok = np.isfinite(pos[..., 0])
X, Y, Z = [np.nan_to_num(pos[..., i]) for i in range(3)]
img = np.asarray(Image.open(f'work/{P}_head_basecolor_composed.png').convert('RGB')).astype(np.float64)
out = img.copy()
front = ok & (Z > 0.055)
cheek = front & (np.abs(X) > 0.025) & (np.abs(X) < 0.045) & (np.abs(Y - (LIP + 0.03)) < 0.008)
ck = np.median(img[cheek], 0)
lumf = lambda c: c @ np.array([0.2126, 0.7152, 0.0722])
rg_cheek = ck[0] / max(ck[1], 1)
box = front & (np.abs(X) < MX) & (np.abs(Y - LIP) < 0.009)
r, g, b = img[..., 0], img[..., 1], img[..., 2]
redness = r / np.maximum(g, 1)
lips = box & (redness > rg_cheek + 0.12)
lipmed = np.median(img[lips], 0) if lips.any() else ck
mx, mn = img.max(-1), img.min(-1)
sat = (mx - mn) / np.maximum(mx, 1)
teeth = box & (sat < 0.33) & (lumf(img) > lumf(lipmed) * 1.15) & (np.abs(X) < MX * 0.8) & (np.abs(Y - LIP) < 0.006)
# the pale gap between the two lips (b: a skin-tone band 3 mm high between the lip bands): texels of the box that are
# not lip but have lip texels within GAP above AND below at the same x (1 mm bins in x and y) join the shadow
GAP = 0.0035
bx = np.round(X / 0.001).astype(int); byy = np.round(Y / 0.0005).astype(int)
occ = {}
for xi, yi in zip(bx[lips], byy[lips]):
    occ.setdefault(xi, set()).add(yi)
gap = np.zeros_like(box)
for yy_, xx_ in zip(*np.nonzero(box & ~lips)):
    col = occ.get(bx[yy_, xx_], ())
    y0 = byy[yy_, xx_]
    if any(y0 < t <= y0 + GAP / 0.0005 for t in col) and any(y0 - GAP / 0.0005 <= t < y0 for t in col):
        gap[yy_, xx_] = True
tw = np.clip(ndimage.gaussian_filter(teeth.astype(float), 1.0) * 1.6, 0, 1) * box
shadow = lipmed * 0.62
out = out * (1 - tw[..., None]) + shadow * tw[..., None]
# the gap becomes lip (one closed mouth with full lips, not a parted one), a touch darker where the lips meet
gw = np.clip(ndimage.gaussian_filter(gap.astype(float), 0.8) * 1.4, 0, 1) * box
out = out * (1 - gw[..., None]) + (lipmed * 0.9) * gw[..., None]
lips = lips | gap
teeth = teeth | gap
# lips toward the cheek hue at their own luminance
lw = np.clip(ndimage.gaussian_filter(lips.astype(float), 1.2) * 1.3, 0, 1) * box
l_own = lumf(out)
target = ck[None, None, :] * (l_own / max(lumf(ck), 1))[..., None]
out = out * (1 - DESAT * lw[..., None]) + target * (DESAT * lw[..., None])
Image.fromarray(np.uint8(np.clip(out, 0, 255))).save(f'textures/{P}_head_basecolor.png')
open(f'work/hand_ref_{P}.txt', 'w').write(','.join(str(int(x)) for x in ck))
print('FACEFIX', P, {'gap_texels': int(gap.sum()), 'cheek': ck.round(0).tolist(), 'lip_median': np.round(lipmed, 0).tolist(), 'lip_texels': int(lips.sum()),
                     'teeth_texels': int(teeth.sum()), 'desat': DESAT})
