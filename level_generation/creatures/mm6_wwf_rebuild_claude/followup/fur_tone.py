#!/usr/bin/env python3
"""Fur tone (follow-up 2026-11-11): the rebuild's fur painted light grey with a fine crosshatch that read as chainmail,
where the native MM6 werewolf sprites are dark grey-black. Three steps on the fur texels (class 'fur' of
compose_wwf.py, no region weight), per UV chart (normalised Gaussians over the chart's fur texels, so charts never bleed):
1. crosshatch: detail = luminance minus a sigma-SIG blur; where its local RMS is high (the net of bright strands), the
   detail is scaled down to KMIN (torso, where the net read as chainmail: KMIN_TORSO; limbs KMIN_LIMBS; head none);
   elsewhere kept (fine fur and the face stay sharp);
2. large-scale tone: L = sigma-BIG blur; per height band (tone_stats.BANDS, feet 0 .. head top 1, rest pose) the band
   median of L is moved onto the native sprite fur median (palette 831, walk and fight frames) x GAIN, and the
   chart-to-chart spread around it compressed to (L/median)^ALPHA (the paint's pale chest charts were 2-3x the band);
   the head keeps its spread (ALPHA 1) and may only darken (face as painted);
3. the fine detail rides on top as the ratio r = luminance/L, highlights eased off the head (r > 1: 1 + KNEE tanh((r-1)/KNEE)),
   so no strand paints pale. Bands blend linearly between centres.
Colour keeps its chroma ratio (one luminance scale per texel); the gutter follows its nearest chart texel. Shorts, gem,
gold, ivory and eyes keep their texels, so the tier ramps stay valid.
The pale strands of the chest/shoulder/back ruff were classed 'ivory' by compose_wwf.py (low saturation, bright) and
so carried the claws' specular 0.9 in game: texels in the torso (rest height 0.3-0.95, |x| < 0.4 m, z < 0.17 m, i.e.
not the muzzle's teeth, not the hand or toe claws) with saturation < 0.3 are fur here, and their specular mask (metal/
rough red) drops to the fur's 0.35; the class map is rewritten to match.
Usage: fur_tone.py <in basecolor> <out basecolor> [<in metal_rough> <out metal_rough> <in classes> <out classes>]
(run once after compose_wwf.py, on its outputs: compose_wwf.py's wwf_basecolor.png, wwf_metal_rough.png and
wwf_classes.png; the follow-up kept those in work/before_followup/*_rebuild.png and wrote the results to textures/)"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, str(Path(__file__).resolve().parent))
import tone_stats as TS
HERE = Path(__file__).resolve().parents[1]
W = np.array([0.2126, 0.7152, 0.0722])
SIG, RMS0, RMS1, BIG = 4.0, 0.02, 0.06, 20.0
KMIN_TORSO, KMIN_LIMBS = 0.2, 0.45                 # head: 1 (face detail kept)
KNEE = 0.45                                       # highlight ratio above L: 1 + KNEE * tanh((r - 1) / KNEE)
GAIN = 1.1
ALPHA = [0.5, 0.5, 0.5, 0.4, 0.35, 1.0]          # per band, TS.BANDS order
src, dst = sys.argv[1], sys.argv[2]

R = np.load(HERE / 'work/raster_v1.npz'); cov = R['cov']; pos = R['pos']
cls = np.asarray(Image.open(sys.argv[5] if len(sys.argv) > 6 else HERE / 'textures/wwf_classes.png').convert('RGB').resize((2048, 2048), Image.NEAREST))
rw = np.load(HERE / 'work/region_weights.npy').astype(np.float64).max(0)
base = np.asarray(Image.open(src).convert('RGB')).astype(np.float64) / 255
lum0 = base @ W
y = pos[..., 1]; h = (y - y[cov].min()) / (y[cov].max() - y[cov].min())
torso = lambda P, H: (H > 0.3) & (H < 0.95) & (np.abs(P[..., 0]) < 0.4) & (P[..., 2] < 0.17)
mx, mn = base.max(-1), base.min(-1); sat = (mx - mn) / np.maximum(mx, 1e-6)
ruff = cov & (rw < 0.02) & torso(pos, h) & (cls[..., 0] == 245) & (sat < 0.3)
fur = cov & (rw < 0.02) & (((cls[..., 0] == 60) & (cls[..., 1] == 60)) | ruff)

sstep = lambda x: np.clip(x, 0, 1) ** 2 * (3 - 2 * np.clip(x, 0, 1))
w_head = sstep((h - 0.84) / 0.04)
w_torso = sstep((h - 0.45) / 0.08) * sstep((0.34 - np.abs(pos[..., 0])) / 0.06)
KMIN = (KMIN_LIMBS + (KMIN_TORSO - KMIN_LIMBS) * w_torso) * (1 - w_head) + w_head
lab, _ = ndimage.label(cov); lum1 = lum0.copy(); big = lum0.copy()
for k, sl in enumerate(ndimage.find_objects(lab), 1):
    sl = tuple(slice(max(s.start - 40, 0), s.stop + 40) for s in sl)
    m = (lab[sl] == k) & fur[sl]
    if m.sum() < 30:
        continue
    l = lum0[sl]; mf = m.astype(float)
    nb = lambda x, s: ndimage.gaussian_filter(x * mf, s) / np.maximum(ndimage.gaussian_filter(mf, s), 1e-6)
    low = nb(l, SIG); d = (l - low) * mf
    rms = np.sqrt(nb(d * d, 2 * SIG))
    kk = 1 - (1 - KMIN[sl]) * np.clip((rms - RMS0) / (RMS1 - RMS0), 0, 1)
    l1 = low + d * kk
    lum1[sl][m] = l1[m]; big[sl][m] = nb(l1, BIG)[m]

nh, nl = TS.native_fur()
cen = np.array([(a + min(b, 1)) / 2 for a, b, _ in TS.BANDS])
ref = np.array([np.median(big[fur & (h >= a) & (h < b)]) for a, b, _ in TS.BANDS])
tgt = np.array([np.median(nl[(nh >= a) & (nh < b)]) * GAIN for a, b, _ in TS.BANDS])
hf = np.clip(h[fur], cen[0], cen[-1])
REF, TGT, ALP = (np.interp(hf, cen, v) for v in (ref, tgt, np.array(ALPHA)))
HEAD = np.interp(hf, cen, (np.arange(len(cen)) == len(cen) - 1).astype(float))
bf, l1f, l0f = np.maximum(big[fur], 1e-4), lum1[fur], lum0[fur]
newL = TGT * (bf / REF) ** ALP
newL = np.where(HEAD > 0, np.minimum(newL, bf) * HEAD + newL * (1 - HEAD), newL)
r = l1f / bf; wh = w_head[fur]; r = np.where(r > 1, (1 + KNEE * np.tanh((r - 1) / KNEE)) * (1 - wh) + r * wh, r)
new = np.clip(newL * r, 0, 1)
ratio = np.ones(base.shape[:2]); ratio[fur] = new / np.maximum(l0f, 1e-4)
idx = ndimage.distance_transform_edt(~cov, return_distances=False, return_indices=True)
ratio = np.where(cov, ratio, ratio[idx[0], idx[1]])
out = np.clip(base * ratio[..., None], 0, 1)
Image.fromarray(np.uint8(out * 255 + 0.5)).save(dst)
print('FURTONE', dst, 'fur texels', int(fur.sum()), 'of them ruff strands once ivory', int(ruff.sum()))
if len(sys.argv) > 6:
    c1 = np.array(Image.open(sys.argv[5]).convert('RGB')); n1 = c1.shape[0]
    P1 = pos[::2048 // n1, ::2048 // n1]; H1 = h[::2048 // n1, ::2048 // n1]
    fix = (c1[..., 0] == 245) & (c1[..., 1] == 245) & torso(P1, H1)
    c1[fix] = (60, 60, 60); Image.fromarray(c1).save(sys.argv[6])
    mr = np.array(Image.open(sys.argv[3]).convert('RGB')); assert mr.shape[:2] == fix.shape
    mr[..., 0][fix] = np.uint8(0.35 * 255 + 0.5); Image.fromarray(mr).save(sys.argv[4])
    print('RECLASS', int(fix.sum()), 'class/specular texels ivory -> fur at', n1)
hh = h[fur]
for (a, b, name), r, t in zip(TS.BANDS, ref, tgt):
    s = (hh >= a) & (hh < b)
    print(f'  {name:15s} L median {r*255:5.1f} -> target {t*255:5.1f} | texels p50/p90/p99 before '
          f'{np.percentile(l0f[s],50)*255:5.1f}/{np.percentile(l0f[s],90)*255:5.1f}/{np.percentile(l0f[s],99)*255:5.1f}'
          f' after {np.percentile(new[s],50)*255:5.1f}/{np.percentile(new[s],90)*255:5.1f}/{np.percentile(new[s],99)*255:5.1f}')
