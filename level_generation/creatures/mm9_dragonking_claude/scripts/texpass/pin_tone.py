#!/usr/bin/env python3
"""Keep the approved look of a fresh paint (brief step 3; after mm9_annud_claude/v2/scripts/match_skin.py and
mm9_wingedmutant_claude/scripts/wing_grain.py). The approved graded colour is resampled onto the new layout at the same
surface points (tp.resample). Per material class:
1. grain: the log-luminance detail finer than GRAIN_SIGMA texels is scaled so that it is `factor` times the approved
   amplitude in that band (only ever scaled down; hue and edges stay), for the classes named in --grain;
2. tone: the new colour takes the broad difference to the approved one, new + blur(approved - new), a blur of SIGMA
   texels normalised inside the class, so each class follows the approved paint region by region while the detail
   stays the new paint's.
Gutters are padded from the result. --strip V --strip-image P copies the rows above v = V from P byte for byte.

Usage: pin_tone.py <new graded png> <approved graded png> <pairs npz> <classes png> <out png>
         [--sigma 24] [--grain 3=1.3 ...] [--report json] [--strip V --strip-image P]"""
import argparse, json, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, str(Path(__file__).resolve().parent))
import tp

GRAIN_SIGMA = 12.0
ap = argparse.ArgumentParser()
ap.add_argument('new'); ap.add_argument('approved'); ap.add_argument('pairs'); ap.add_argument('classes'); ap.add_argument('out')
ap.add_argument('--sigma', type=float, default=24.0)
ap.add_argument('--grain', nargs='*', default=[])
ap.add_argument('--report')
ap.add_argument('--strip', type=float)
ap.add_argument('--strip-image')
a = ap.parse_args()
new, old = tp.load(a.new), tp.load(a.approved)
N = new.shape[0]
remap, cover = tp.resample(old, np.load(a.pairs), N)
cls = np.asarray(Image.open(a.classes).convert('L').resize((N, N), Image.NEAREST)).copy()
cls[~cover] = 0
present = [int(k) for k in np.unique(cls) if k and (cls == k).sum() > 200]
rep = {'sigma': a.sigma, 'grain_sigma': GRAIN_SIGMA}
out = new.copy()


def lp(img, mask, sigma):
    den = ndimage.gaussian_filter(mask.astype(np.float32), sigma)
    return ndimage.gaussian_filter(img * mask, sigma) / np.maximum(den, 1e-4)


for spec in a.grain:
    k, factor = spec.split('='); k, factor = int(k), float(factor)
    m = cls == k
    ln, lo = np.log(np.maximum(tp.lum(out), 1.0)), np.log(np.maximum(tp.lum(remap), 1.0))
    dn, do = ln - lp(ln, m, GRAIN_SIGMA), lo - lp(lo, m, GRAIN_SIGMA)
    sn, so = float(dn[m].std()), float(do[m].std())
    scale = min(1.0, factor * so / max(sn, 1e-6))
    gain = np.exp(dn * (scale - 1.0))[..., None]
    soft = ndimage.gaussian_filter(m.astype(np.float32), 1.5)[..., None]
    out = out * (1 + (gain - 1) * soft)
    rep[f'grain_{k}'] = {'detail_sd_new': round(sn, 3), 'detail_sd_approved': round(so, 3), 'scale': round(scale, 3)}
base = out.copy()
for k in present:
    m = cls == k
    shift = tp.broad_shift(base, remap, m, a.sigma)
    soft = ndimage.gaussian_filter(m.astype(np.float32), 1.5)[..., None]
    out = out + shift * soft
out = np.clip(out, 0, 255)
for k in present:
    m = cls == k
    rep[f'class_{k}'] = {'texels': int(m.sum()), 'approved': remap[m].mean(0).round(1).tolist(),
                         'new': new[m].mean(0).round(1).tolist(), 'out': out[m].mean(0).round(1).tolist(),
                         'lum_sd_approved': round(float(tp.lum(remap[m]).std()), 1),
                         'lum_sd_new': round(float(tp.lum(new[m]).std()), 1),
                         'lum_sd_out': round(float(tp.lum(out[m]).std()), 1)}
out = tp.pad(out, cover)
if a.strip is not None:
    rows = int(round((1 - a.strip) * N))
    out[:rows] = tp.load(a.strip_image)[:rows]
tp.save(out, a.out)
print('PIN', json.dumps(rep))
if a.report:
    json.dump(rep, open(a.report, 'w'), indent=1)
