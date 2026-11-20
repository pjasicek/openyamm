#!/usr/bin/env python3
"""Clean neckline in the body paint (orchestrator review of r6: the skin-to-collar edge a blocky stepped line). After
neck_line.py the head set ends on a smooth curve z_n(angle) (the body collar's top per 10 degrees, smoothed, never below
0.668 m at the front); below it the visible surface is the BODY set, whose 4K paint had skin wedges in the collar's V opening
with a rectangular outline. Body texels below the curve within 3.5 cm and 13 cm of the neck axis, front 200 degrees, that are
skin-coloured take the colour of the nearest gold collar texel in 3D (blurred 2 texels, the collar's own weave as detail),
feathered: the collar band reaches the curve everywhere and the skin/gold boundary is the curve.
Order: breeches_tone.py -> body_neckline_paint.py -> tier_pm3.py (its classes come from this paint).
Reads/writes textures/pm3_tp_basecolor_graded.png (backup work/pm3_tp_basecolor_graded_preneckline.png on the first run).
Usage (project folder): body_neckline_paint.py work/pm3_body_tex_unlined.glb"""
import shutil, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.spatial import cKDTree
sys.path.insert(0, str(Path(__file__).resolve().parent))
from headpos import texel_positions
glb = sys.argv[1]
src = Path('work/pm3_tp_basecolor_graded_preneckline.png'); out = Path('textures/pm3_tp_basecolor_graded.png')
if not src.exists():
    shutil.copyfile(out, src)
img = np.asarray(Image.open(src).convert('RGB'), float)
N = img.shape[0]
pos, cov = texel_positions(glb, 'PeasantM3', N)
bx = np.nan_to_num(pos[..., 0]); by = -np.nan_to_num(pos[..., 2]); bz = np.nan_to_num(pos[..., 1]) - 0.855
C = np.array([0.0004, -0.0021])
r = np.hypot(bx - C[0], by - C[1]); ang = np.degrees(np.arctan2(bx - C[0], -(by - C[1])))
# neck_line.py's curve, recomputed from this body: top of the body collar per 10-degree bin, smoothed (7), >= 0.668
neckb = cov & (bz > 0.55) & (r < 0.13)
bins = np.arange(-180, 181, 10)
top = np.array([bz[neckb & (ang >= b) & (ang < b + 10)].max() if (neckb & (ang >= b) & (ang < b + 10)).any() else np.nan
                for b in bins[:-1]])
top = np.maximum(np.where(np.isnan(top), np.nanmin(top), top), 0.668)
top = np.maximum(np.convolve(np.r_[top[-3:], top, top[:3]], np.ones(7) / 7, 'valid'), 0.668)
zn = np.interp(ang, bins[:-1] + 5, top, period=360)
mx, mn = img.max(-1), img.min(-1); sat = (mx - mn) / np.maximum(mx, 1)
hue_r = img[..., 0] / np.maximum(img[..., 1], 1)
skin = cov & (sat > 0.15) & (sat < 0.62) & (mx > 120) & (hue_r < 1.9)
zone = cov & (r < 0.13) & (np.abs(ang) < 100) & (bz < zn) & (bz > zn - 0.035)
gold = cov & (sat > 0.62) & (img[..., 0] > 110) & (bz > 0.56) & (r < 0.17) & (np.abs(ang) < 120)
# r7b: after neck_line.py TRIM=1 the head no longer covers the collar's V: the body's own V surface (tunic cloth, an olive edge)
# shows between the neckline curve and the brooch; all non-gold texels there take the collar gold (MM9 A: the gold neckline
# band with the brooch on it). V = front 70 degrees, 4.5 cm below the curve, inside 11 cm of the axis.
import importlib.util
spec = importlib.util.spec_from_file_location('tier_pm3', str(Path(__file__).resolve().parent / 'tier_pm3.py'))
tp = importlib.util.module_from_spec(spec); spec.loader.exec_module(tp)
rp = tp.raster_positions(glb)
pid = np.asarray(Image.fromarray(rp['PeasantM3#piece'].astype(np.int32)).resize((N, N), Image.NEAREST)) if rp['PeasantM3#piece'].shape[0] != N else rp['PeasantM3#piece']
shell = np.isin(pid, rp['PeasantM3#main'])          # torso+sleeve shell and skirt piece: not the brooch or belt pieces
vzone = cov & shell & (r < 0.15) & (np.abs(ang) < 75) & (bz < zn) & (bz > zn - 0.065)
tgt = ((zone & skin) | (vzone & ~gold)) & shell
gy, gx = np.nonzero(gold)
tree = cKDTree(np.column_stack([bx[gold], by[gold], bz[gold]]))
ty, tx = np.nonzero(tgt)
_, k = tree.query(np.column_stack([bx[tgt], by[tgt], bz[tgt]]))
blur = np.stack([ndimage.gaussian_filter(np.where(gold, img[..., c], 0), 2) for c in range(3)], -1) / \
    np.maximum(ndimage.gaussian_filter(gold.astype(float), 2), 1e-3)[..., None]
res = img.copy()
res[ty, tx] = blur[gy[k], gx[k]]
w = ndimage.gaussian_filter(tgt.astype(float), 1.2) * cov
res = img * (1 - w[..., None]) + res * w[..., None]
Image.fromarray(np.clip(res, 0, 255).astype(np.uint8)).save(out)
print('BODYNECKLINE skin texels repainted', int(tgt.sum()), 'zone', int(zone.sum()), 'gold refs', int(gold.sum()))
