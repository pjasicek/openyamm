#!/usr/bin/env python3
"""Keep the approved look on the sharper 4K paint (texture pass 2026-10-30). The fresh paint drifted: a grey fibred iris and
veined sclera where the approved eye has a black disc and a ribbed cream ring (same size and place), the hide 7 % and the
red mouth flesh 26 % darker. Run once after grade_basecolor.py (keeps the graded input as ..._graded_meshy.png).

- Non-eye regions: new + blur(approved - new), a mask-normalised Gaussian of SIGMA texels inside each region
  (../mm9_annud_claude/v2/scripts/match_skin.py): the tone follows the approved paint, the detail stays the new one's.
  The hide then takes the approved luminance distribution by quantile matching, the Winged Mutant's wing-tone fix
  (luminance sd 45.6 -> 38.1, the approved value).
- Eyes (the eyeball pieces, class 2): approved low frequencies times the new paint's fine luminance ratio, so the
  approved design and colour stay, black stays black, and the new paint adds fibres and veins. Tiers B/C still go fiery
  through the eye ramps, which read this luminance.

Usage: match_approved.py [sigma 20] [eye sigma 5]"""
import shutil, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage

HERE = Path(__file__).resolve().parent.parent
T = HERE / 'textures'
SIGMA = float(sys.argv[1]) if len(sys.argv) > 1 else 20.0
EYE_SIGMA = float(sys.argv[2]) if len(sys.argv) > 2 else 5.0
RAW = T / 'eye_basecolor_graded_meshy.png'
if not RAW.exists():
    shutil.copy2(T / 'eye_basecolor_graded.png', RAW)
new = np.asarray(Image.open(RAW).convert('RGB'), np.float32)
app = np.asarray(Image.open(HERE / 'work/approved_graded_on_new.png').convert('RGB'), np.float32)
cover = np.asarray(Image.open(HERE / 'work/approved_cover_on_new.png')) > 0
# compose.py writes class * 80 into uint8: 1 hide 80, 2 eyes 160, 3 mouth 240, 4 teeth 64 (wrapped)
cl = np.asarray(Image.open(T / 'eye_material_classes.png').resize((2048, 2048), Image.NEAREST))
L = np.array([0.2126, 0.7152, 0.0722], np.float32)


def nblur(img, m, sigma):
    den = ndimage.gaussian_filter(m, sigma)
    if img.ndim == 2:
        return ndimage.gaussian_filter(img * m, sigma) / np.maximum(den, 1e-4)
    return np.stack([ndimage.gaussian_filter(img[..., c] * m, sigma) for c in range(3)], -1) / np.maximum(den, 1e-4)[..., None]


out = new.copy()
report = {}
for value, name in ((80, 'hide'), (240, 'mouth'), (64, 'teeth')):
    mask = (cl == value) & cover
    m = mask.astype(np.float32)
    broad = nblur((app - new) * m[..., None], m, SIGMA)
    den_fix = 1.0                                   # (app - new) is masked once; nblur's m only weighs the Gaussian
    out[mask] = np.clip(new[mask] + broad[mask] * den_fix, 0, 255)
    if name == 'hide':
        la, lo = app[mask] @ L, out[mask] @ L
        q = np.linspace(0, 1, 513)
        mapped = np.interp(lo, np.quantile(lo, q), np.quantile(la, q))
        out[mask] = np.clip(out[mask] * (mapped / np.maximum(lo, 1.0))[:, None], 0, 255)
        report['hide_luminance_sd'] = [round(float(la.std()), 1), round(float(lo.std()), 1),
                                       round(float((out[mask] @ L).std()), 1)]
    report[name] = {'approved': app[mask].mean(0).round(1).tolist(), 'new': new[mask].mean(0).round(1).tolist(),
                    'matched': out[mask].mean(0).round(1).tolist()}
mask = (cl == 160) & cover
m = mask.astype(np.float32)
lum = new @ L
ratio = (lum + 6) / (nblur(lum, m, EYE_SIGMA) + 6)
low = nblur(app, m, 1.2)                             # the approved design at its own resolution
out[mask] = np.clip(low[mask] * (np.clip(ratio[mask], 0.65, 1.45) ** 0.75)[:, None], 0, 255)   # softened: the new iris rim ticks
report['eyes'] = {'approved': app[mask].mean(0).round(1).tolist(), 'new': new[mask].mean(0).round(1).tolist(),
                  'matched': out[mask].mean(0).round(1).tolist(),
                  'luminance_sd': [round(float((a[mask] @ L).std()), 1) for a in (app, new, out)]}
Image.fromarray(out.astype(np.uint8)).save(T / 'eye_basecolor_graded.png')
print('MATCHED', report)
