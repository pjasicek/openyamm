#!/usr/bin/env python3
"""Ears of both head tiers (orchestrator ear sweep 2026-11-02, rows 17-18: tier B's copper bow-shaped braid ties painted
onto both ears, tier A's white braid beads at the ears with brown smudges below them; DM1 had the same fault, see
../mm9_peasantdm1_claude/README.md "Ears and beard edge").

Cause: both head turnarounds wear braid ties at ear height; the mesh has no tie, so Meshy's head retextures projected
them onto the ears (each ear is its own loose part of the head primitive, about 80 triangles) and onto the head shell
just below and behind them. Neither tier has a clean ear to copy (DM1 used its tier B ears), so the ear skin is
synthesised:
1. Ears (the two small loose parts at |x| 0.06-0.11 m, y 1.0-1.1 m): every texel takes the tier's temple skin (median of
   the skin-coloured shell texels within TEMPLE m of the ear, behind the cheek) times a crease term from the geometry
   (texels within CREASE m of the head shell darken to CREASE_DARK, so the ear reads where it meets the head) and a
   faint luminance grain from the temple skin. The engine shades the ear's shape from its mesh normals: the head
   normal map (each tier's) is flat on the ears, and the shared ORM takes the temple skin's median.
2. Around the ears (below the ears' top + 2.5 cm): on the head shell within ZONE m of the ear surface, texels darker than
   DARK x the local light paint and not skin-coloured (the brown smudges, the copper ties' shaded parts); there and on
   the hair bob within ZONE_HAIR m (tier B's ties reach onto it; the grey strands are kept), saturated orange-brown
   texels darker than 0.78 x the skin (the ties); on the shell below the ear centre (painted as grey sideburn and beard
   hair), every texel that is not light grey hair (saturation < 0.3, luminance > 110). They take the mean of the clean paint around them (normalised
   Gaussian at 3 / 6 / 12 / 24 px where enough of it is near, else the light-hair median), feathered.
Backups: <prefix>_head_basecolor_preear.png, <prefix>_head_normal_1k_preear.png and pdm2_tp_head_metal_rough_1k_preear.png
(first run); every run reads them, so a rerun repeats the result (reset_head_backups.py moves them away and restores the
ORM). Order (head_paint.sh): ... -> hand_clean -> fix_ear -> pad_head.
Usage (project folder): fix_ear_pdm2.py <export glb> [prefixes pdm2_tp,pdm2b_tp] [--debug <out dir>]"""
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from headpos import texel_positions
from ear_islands import _load, _components, _raster

TEMPLE, CREASE, CREASE_DARK, ZONE, ZONE_HAIR, DARK = 0.06, 0.006, 0.78, 0.025, 0.04, 0.72
MAT = 'PeasantDM2Head'
T = Path('textures')
args = sys.argv[1:]
DEBUG = None
if '--debug' in args:
    i = args.index('--debug'); DEBUG = Path(args[i + 1]); del args[i:i + 2]; DEBUG.mkdir(parents=True, exist_ok=True)
glb = args[0]
PREFIXES = (args[1] if len(args) > 1 else 'pdm2_tp,pdm2b_tp').split(',')


def backup(name):
    f, bk = T / f'{name}.png', T / f'{name}_preear.png'
    if not bk.exists() and DEBUG is None:
        shutil.copyfile(f, bk)
    return f, np.asarray(Image.open(bk if bk.exists() else f).convert('RGB'), float)


N = 2048
pos, cov = texel_positions(glb, MAT, N)
P, UV, tri = _load(glb)
part = _components(P, tri)
sizes = np.bincount(part)
cen = np.array([P[tri[part == k]].reshape(-1, 3).mean(0) for k in range(len(sizes))])
ears = [k for k in range(len(sizes)) if sizes[k] < 200 and 0.06 < abs(cen[k, 0]) < 0.11 and 1.0 < cen[k, 1] < 1.1]
shell = int(np.argmax([sizes[k] if 0.85 < cen[k, 1] < 1.25 and abs(cen[k, 0]) < 0.05 else 0 for k in range(len(sizes))]))
tp = _raster(UV, tri, part, N)
X = np.nan_to_num(pos, nan=9.0)
earm = np.isin(tp, ears) & cov
shellm = (tp == shell) & cov
hair = [k for k in range(len(sizes)) if k != shell and sizes[k] > 500 and cen[k, 1] > 1.0]     # the hair bob
hairm = np.isin(tp, hair) & cov
# crease: distance from each ear texel to the shell surface (shell texel positions, subsampled)
sp = X[shellm][::3]
d_shell = np.full((N, N), 1.0)
d_shell[earm] = cKDTree(sp).query(X[earm])[0]
crease = CREASE_DARK + (1 - CREASE_DARK) * np.clip(d_shell / CREASE, 0, 1)
crease = ndimage.gaussian_filter(crease, 1.5)


def hsl(img):
    mx, mn = img.max(-1), img.min(-1)
    sat = (mx - mn) / np.maximum(mx, 1)
    lum = img @ [0.299, 0.587, 0.114]
    r, g, b = img[..., 0], img[..., 1], img[..., 2]
    hue = np.degrees(np.arctan2(np.sqrt(3) * (g - b), 2 * r - g - b)) % 360
    return hue, sat, lum


def local_mean(img, valid, sigma):
    wv = ndimage.gaussian_filter(valid.astype(float), sigma)
    return np.stack([ndimage.gaussian_filter(img[..., i] * valid, sigma) for i in range(3)], -1) / \
        np.maximum(wv, 1e-6)[..., None], wv


def refill_gutter(out, changed, covm, it=8):
    near = ndimage.binary_dilation(changed, iterations=it) & ~covm
    _, (iy, ix) = ndimage.distance_transform_edt(~covm, return_indices=True)
    out[near] = out[iy[near], ix[near]]


report = {'ear_parts': [int(k) for k in ears], 'ear_triangles': [int(sizes[k]) for k in ears], 'shell': shell,
          'hair': [int(k) for k in hair]}
ear_cen = [cen[k] for k in ears]
temple = np.zeros((N, N), bool)
for c in ear_cen:
    temple |= shellm & (np.linalg.norm(X - c, axis=-1) < TEMPLE) & (X[..., 2] < c[2] + 0.04)
# distance of every shell / hair texel to the nearest ear texel (3D)
d_ear = np.full((N, N), 1.0)
near = (shellm | hairm) & (np.min([np.linalg.norm(X - c, axis=-1) for c in ear_cen], 0) < 0.08)
d_ear[near] = cKDTree(X[earm][::2]).query(X[near])[0]
top = max(c[1] for c in ear_cen) + 0.025
ear_y = np.zeros((N, N))
for c in ear_cen:                     # the centre height of the ear on the texel's side
    ear_y[np.sign(X[..., 0]) == np.sign(c[0])] = c[1]
zone = shellm & (d_ear < ZONE) & (X[..., 1] < top)              # shell: dark smudges and ties
hzone = hairm & (d_ear < ZONE_HAIR) & (X[..., 1] < top)          # hair bob: tie colours only (keeps the strands)
orm_ref = None
for pre in PREFIXES:
    fa, img = backup(f'{pre}_head_basecolor')
    hue, sat, lum = hsl(img)
    skinlike = (hue > 8) & (hue < 40) & (sat > 0.28) & (sat < 0.8) & (lum > 90)
    tsk = temple & skinlike
    skin = np.median(img[tsk], 0)
    out = img.copy()
    # 1. ears: temple skin x crease x a faint grain of the temple skin's own luminance texture
    grain_src = lum[tsk] / max(np.median(lum[tsk]), 1)
    rng = np.random.default_rng(7)
    grain = np.ones((N, N))
    grain[earm] = np.clip(rng.choice(grain_src, earm.sum()), 0.9, 1.1)
    grain = ndimage.gaussian_filter(grain, 0.8)
    out[earm] = np.clip(skin[None] * (crease[earm] * grain[earm])[:, None], 0, 255)
    # 2. foreign paint on the shell around the ears
    light = zone & (lum > np.percentile(lum[zone], 50))
    lm, _ = local_mean(img, light, 10.0)
    llum = lm @ [0.299, 0.587, 0.114]
    skin_l = skin @ [0.299, 0.587, 0.114]
    dark = zone & (lum < DARK * llum) & ~(skinlike & (lum > 0.8 * skin_l))
    tie = (zone | hzone) & (hue > 5) & (hue < 45) & (sat > 0.4) & (lum < 0.78 * skin_l)
    zz = zone | hzone
    # below the ear centres the shell is painted as grey sideburn / beard hair: anything else there is a tie or smudge
    low = zone & (X[..., 1] < ear_y + 0.005)
    hairlike = (sat < 0.3) & (lum > 110)
    bad = ndimage.binary_dilation(dark | tie | (low & ~hairlike), iterations=2) & zz
    clean = zz & ~bad
    # fill: the zone's light-hair median, refined by the clean paint around at 24 / 12 / 6 / 3 px where there is enough
    fill = np.broadcast_to(np.median(img[zz & hairlike], 0), img.shape).copy()
    for sg in (24.0, 12.0, 6.0, 3.0):
        f2, w2 = local_mean(img, clean, sg)
        fill = np.where((w2 > 0.15)[..., None], f2, fill)
    w = np.clip(ndimage.gaussian_filter(bad.astype(float), 1.0) * 1.5, 0, 1) * zz
    out = out * (1 - w[..., None]) + fill * w[..., None]
    refill_gutter(out, earm | (w > 0.02), cov)
    report[pre] = {'skin': skin.round(1).tolist(), 'temple_texels': int(tsk.sum()), 'ear_texels': int(earm.sum()),
                   'zone_texels': int(zone.sum()), 'replaced_texels': int((w > 0.5).sum())}
    if DEBUG is not None:
        dbg = img.copy(); dbg[earm] = (255, 0, 255); dbg[bad] = (0, 255, 0); dbg[tsk] = (255, 255, 0)
        Image.fromarray(np.uint8(dbg)).save(DEBUG / f'{pre}_debug.png')
        Image.fromarray(np.uint8(np.clip(np.round(out), 0, 255))).save(DEBUG / f'{pre}_head_basecolor.png')
    else:
        Image.fromarray(np.uint8(np.clip(np.round(out), 0, 255))).save(fa)
    # normal map: flat on the ears (1K)
    ear1k = np.asarray(Image.fromarray(np.uint8(earm) * 255).resize((1024, 1024), Image.BILINEAR)) > 0
    cov1k = np.asarray(Image.fromarray(np.uint8(cov) * 255).resize((1024, 1024), Image.BILINEAR)) > 0
    fn, nm = backup(f'{pre}_head_normal_1k')
    nm = nm.copy(); nm[ear1k] = (128, 128, 255)
    refill_gutter(nm, ear1k, cov1k)
    if DEBUG is None:
        Image.fromarray(np.uint8(nm)).save(fn)
    if pre == PREFIXES[0]:
        fo, orm = backup(f'{pre}_head_metal_rough_1k')
        t1k = np.asarray(Image.fromarray(np.uint8(tsk) * 255).resize((1024, 1024), Image.NEAREST)) > 0
        orm = orm.copy(); orm_ref = np.median(orm[t1k], 0); orm[ear1k] = orm_ref
        refill_gutter(orm, ear1k, cov1k)
        report['orm_ear'] = orm_ref.round(1).tolist()
        if DEBUG is None:
            Image.fromarray(np.uint8(orm)).save(fo)
print('FIXEAR', report)
