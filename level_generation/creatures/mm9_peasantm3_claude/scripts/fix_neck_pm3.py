#!/usr/bin/env python3
"""Neck skin under the jaw (PeasantM1/DM1/DM2 collar-paint lesson). The head turnarounds show the tunic's brocade neckline
round the neck, so both head retextures painted the neck as gold brocade (tier A also wine-red velvet) above the real
collar. Every head-set texel below the jaw line (face_rigid_pm3.py's boundary minus MARGIN: the neck, not the chin or
the beard) takes the tier's own skin: the median of its upper-cheek skin, darkened slightly toward the collar, with a
share of the paint's fine luminance detail, feathered over a few texels; gutters refilled by pad_head.py afterwards.
Rewrites textures/<prefix>_head_basecolor.png (backup <prefix>_head_basecolor_preneck.png on the first run) and flattens
the head normal map there (<prefix>_head_normal_1k.png, backup _preneck).
Usage (project folder): fix_neck_pm3.py <export glb> <prefix> [...]"""
import os, shutil, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, str(Path(__file__).resolve().parent))
from headpos import texel_positions
Z0, Y0, SLOPE, CURVE, YB, BACK, ZMAX = 0.676, -0.035, 0.45, 1.2, 0.0, 0.4, 0.725   # face_rigid_pm3.py (Blender rest)
MARGIN, FLOOR, DETAIL = 0.006, 0.855, 0.06
glb, prefixes = sys.argv[1], sys.argv[2:]
N = 2048
pos, cov = texel_positions(glb, 'PeasantM3Head', N)
# export GLB (glTF): x, y up above the floor, z forward -> Blender rest x, -z, y - floor
bx = np.nan_to_num(pos[..., 0]); by = -np.nan_to_num(pos[..., 2]); bz = np.nan_to_num(pos[..., 1]) - FLOOR
zb = np.minimum(Z0 + SLOPE * (by - Y0) + CURVE * bx ** 2 + BACK * np.clip(by - YB, 0, None), ZMAX)
ang = np.degrees(np.arctan2(bx, -by))
# collar: the head set's lowest faces in front of and beside the neck flare out from the neck base into the V gap of the
# body's brocade yoke (bind rest: neck column r ~3.5 cm above z 0.645, flare r 5-9 cm below); they continue the yoke
COLLAR_Z = 0.668
bpos, bcov = texel_positions(glb, 'PeasantM3', N)
bbx = np.nan_to_num(bpos[..., 0]); bby = -np.nan_to_num(bpos[..., 2]); bbz = np.nan_to_num(bpos[..., 1]) - FLOOR
# r2 (orchestrator review: "a lighter neck band with a jagged lower edge at the collar"): the head/body seam runs along the
# head split's triangles. One smooth collar line all round the neck, 4 mm above the body set's top at each angle (10-degree
# bins, circular smoothing), so the jagged seam lies inside the gold band; at the front at least COLLAR_Z (the V gap)
bang = np.degrees(np.arctan2(bbx, -bby))
neckb = bcov & (bbz > 0.58) & (np.hypot(bbx, bby) < 0.13)
bins = np.arange(-180, 181, 10)
top = np.array([bbz[neckb & (bang >= a) & (bang < a + 10)].max() if (neckb & (bang >= a) & (bang < a + 10)).any() else np.nan
                for a in bins[:-1]])
top = np.where(np.isnan(top), np.nanmin(top), top)
top = np.convolve(np.r_[top[-2:], top, top[:2]], np.ones(5) / 5, 'valid')
zc = np.interp(ang, bins[:-1] + 5, top, period=360) + 0.004
zc = np.where(np.abs(ang) < 35, np.maximum(zc, COLLAR_Z), zc)
collar = cov & (bz < zc) & (bz > 0.4)
if os.environ.get('NECKLINE') == '1':
    # r7: the collar is everything below neck_line.py's smooth curve (collar top per 10 deg, smoothed 7 bins, >= 0.668 m)
    topn = np.array([bbz[neckb & (bang >= b) & (bang < b + 10)].max() if (neckb & (bang >= b) & (bang < b + 10)).any() else np.nan
                     for b in bins[:-1]])
    topn = np.maximum(np.where(np.isnan(topn), np.nanmin(topn), topn), 0.668)
    topn = np.maximum(np.convolve(np.r_[topn[-3:], topn, topn[:3]], np.ones(7) / 7, 'valid'), 0.668)
    zc = np.interp(ang, bins[:-1] + 5, topn, period=360)
    collar = cov & (bz < zc - 0.0004) & (bz > 0.4)
# beard -> neck: a 3D gradient from FEATHER_UP above the jaw line minus MARGIN to FEATHER below it (not a 2-texel edge)
FEATHER, FEATHER_UP = 0.014, {'pm3_tp': 0.006, 'pm3b_tp': 0.002}
below = cov & (bz < zb - MARGIN) & (bz > 0.4) & ~collar
csoft = ndimage.gaussian_filter(collar.astype(float), 1.5) / np.maximum(ndimage.gaussian_filter(cov.astype(float), 1.5), 1e-3) * cov   # r6b: coverage-normalised (island borders kept old paint as seam lines)
print('FIXNECK collar line z by angle', dict(zip(range(-180, 180, 45), np.interp(np.arange(-180, 180, 45), bins[:-1] + 5, top).round(3) + 0.004)))
# body yoke brocade beside the gap (same height band, gold texels) gives the collar colour
body_img = np.asarray(Image.open('textures/pm3_tp_basecolor_graded.png').convert('RGB'), float)
bmx, bmn = body_img.max(-1), body_img.min(-1)
bsat = (bmx - bmn) / np.maximum(bmx, 1)
yoke = bcov & (bbz > 0.58) & (bbz < 0.66) & (np.abs(bbx) < 0.14) & (bby < 0.02) & (bsat > 0.6) & (body_img[..., 0] > 110)
yoke_ref = np.median(body_img[yoke], 0)
from scipy.spatial import cKDTree
ywide = bcov & (bbz > 0.56) & (np.hypot(bbx, bby) < 0.16) & (bsat > 0.45) & (body_img[..., 0] > 90) & (body_img[..., 2] < 0.25 * body_img[..., 0])   # r7: gold only (skin b/r ~0.42)
yk = np.nonzero(ywide)
ytree = cKDTree(np.column_stack([bbx[ywide], bby[ywide], bbz[ywide]]))
YS = 4 if os.environ.get('NECKLINE') == '1' else 5   # r7: keep the brocade weave
yoke_soft = np.stack([ndimage.gaussian_filter(np.where(ywide, body_img[..., c], 0), YS) for c in range(3)], -1) / \
    np.maximum(ndimage.gaussian_filter(ywide.astype(float), YS), 1e-3)[..., None]
yoke_mu, yoke_sd = body_img[yoke].mean(0), body_img[yoke].std(0)
print('FIXNECK collar texels', int(collar.sum()), 'yoke texels', int(yoke.sum()), 'yoke ref', yoke_ref.round())
cheek = cov & (bz > 0.765) & (bz < 0.79) & (np.abs(bx) > 0.028) & (np.abs(bx) < 0.06) & (by < -0.05)
print('FIXNECK zone texels', int(below.sum()), 'cheek texels', int(cheek.sum()))
for p in prefixes:
    f = Path(f'textures/{p}_head_basecolor.png'); bk = Path(f'textures/{p}_head_basecolor_preneck.png')
    if not bk.exists():
        shutil.copyfile(f, bk)
    img = np.asarray(Image.open(bk).convert('RGB'), float)
    # the hand squares share the image: only head texels are touched (cov is the head primitive's own coverage)
    ref = np.median(img[cheek], 0)
    lum = img @ [0.299, 0.587, 0.114]
    fine = lum - ndimage.gaussian_filter(lum, 3.0)
    # darker toward the collar (the neck lies in the jaw's shadow): x0.97 at the jaw line, x0.88 at the collar
    t = np.clip((zb - bz) / 0.08, 0, 1)
    # r2: x0.90 at the jaw line, x0.82 at the collar (the r1 neck at x0.97 read as a lighter band under the beard)
    skin = ref[None, None, :] * (0.90 - 0.08 * t)[..., None] + DETAIL * fine[..., None]
    fu = FEATHER_UP.get(p, 0.002)
    soft = ((1 - np.clip((bz - (zb - MARGIN - FEATHER + fu)) / (FEATHER + fu), 0, 1)) ** 1.5) * cov * (bz > 0.4) * ~collar
    soft = ndimage.gaussian_filter(soft, 1.0)
    out = img * (1 - soft[..., None]) + skin * soft[..., None]
    # under the chin the turnaround's collar edge was projected as a saturated gold bead line (just above the jaw
    # boundary): saturated gold there -> skin (the beards are less saturated: A's ginger ~0.6, B's dark brown)
    mx_, mn_ = img.max(-1), img.min(-1)
    sat = (mx_ - mn_) / np.maximum(mx_, 1)
    bead = cov & (bz < zb + 0.015) & (by > -0.065) & (sat > 0.85) & (img[..., 0] > 120) & ~collar   # r2: truly saturated gold only
    bsoft = ndimage.gaussian_filter(ndimage.binary_dilation(bead, iterations=2).astype(float), 1.0) * cov
    out = out * (1 - bsoft[..., None]) + skin * bsoft[..., None]
    # collar: the yoke's gold with the original paint's light/dark detail (normalised over the collar)
    # (colour transfer: per channel, the original paint's collar texels moved to the yoke brocade's mean and spread, so
    # the painted band keeps its weave and pattern in the body yoke's gold)
    # the band: the original paint's brocade ring at the neck base (z 0.648-0.668, gold texels); each collar texel takes
    # the band texel at its angle, its height rescaled from the collar's 0.615..COLLAR_Z onto the band
    band = cov & (bz > 0.648) & (bz < 0.668) & (np.abs(ang) < 100) & (sat > 0.6) & (img[..., 0] > 90)
    from scipy.spatial import cKDTree
    arc = lambda a: np.radians(a) * 0.045
    tree = cKDTree(np.column_stack([arc(ang[band]), bz[band]]))
    cy, cx = np.nonzero(collar)
    zmap = 0.650 + np.clip((bz[collar] - 0.615) / (COLLAR_Z - 0.615), 0, 1) * 0.016
    _, k = tree.query(np.column_stack([arc(ang[collar]), zmap]))
    src = img[band][k]
    # r2: the colour of the nearest body-yoke texel in 3D (the yoke softened, so the wedges continue the yoke beside them;
    # the band-only transfer went flat orange at the sides where there is no band to sample) x the band's weave as detail
    sl = src @ [0.299, 0.587, 0.114]
    det = np.clip(sl / max(sl.mean(), 1.0), 0.6, 1.5) ** 0.25   # r2d: little pattern (the band remap read as scales)
    near = ytree.query(np.column_stack([bx[collar], by[collar], bz[collar]]))[1]
    gold = img.copy()
    gold[cy, cx] = np.clip(yoke_soft[yk[0][near], yk[1][near]] * det[:, None], 0, 255)
    if os.environ.get('NECKLINE') == '1' and os.environ.get('COLLAR_SKIN') != '1':
        # gold of the nearest body-collar texel (softened) with the head paint's weave as faint detail
        near = ytree.query(np.column_stack([bx[collar], by[collar], bz[collar]]))[1]
        gold2 = img.copy()
        lc = lum[collar]; det2 = np.clip(lc / max(lc.mean(), 1.0), 0.6, 1.4) ** 0.5
        gold2[cy, cx] = np.clip(yoke_soft[yk[0][near], yk[1][near]] * det2[:, None], 0, 255)
        cs = ndimage.gaussian_filter(collar.astype(float), 0.8) / np.maximum(ndimage.gaussian_filter(cov.astype(float), 0.8), 1e-3) * cov
        out = out * (1 - cs[..., None]) + gold2 * cs[..., None]
    elif os.environ.get('COLLAR_SKIN') == '1':
        # r6 (user note "some artifacts here?"): the head set's faces below the collar line are the throat in the body
        # collar's V opening (and, at the sides, tucked under the collar by neck_tuck.py): one neck skin tone, not a gold
        # remap of the collar band (it read as torn gold shards next to the body's real collar)
        # r7: exactly the neck's own skin function of height (one continuous tone across the throat, no seams)
        cskin = skin
        out = out * (1 - csoft[..., None]) + cskin * csoft[..., None]
    else:
        out = out * (1 - csoft[..., None]) + gold * csoft[..., None]
    print('FIXNECK', p, 'bead texels', int(bead.sum()))
    Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(f)
    nf = Path(f'textures/{p}_head_normal_1k.png'); nbk = Path(f'textures/{p}_head_normal_1k_preneck.png')
    soft = np.maximum(np.maximum(soft, bsoft), csoft)   # r2: the collar band's normal flattened too (old paint's folds)
    # r7: the whole head set below the jaw line flattened evenly (coverage-normalised, no per-island edges: partly
    # flattened island borders read as lighter rectangles across the throat)
    fl = (cov & (bz < zb - MARGIN + 0.002) & (bz > 0.4)).astype(float)
    fl = ndimage.gaussian_filter(fl, 3.0) / np.maximum(ndimage.gaussian_filter(cov.astype(float), 3.0), 1e-3) * cov
    soft = np.maximum(soft, np.clip(fl, 0, 1))
    if nf.exists():
        if not nbk.exists():
            shutil.copyfile(nf, nbk)
        nm = np.asarray(Image.open(nbk).convert('RGB'), float)
        # r7: gutters take the flatten weight of their nearest island texel (unflattened gutter normals mixed into the
        # island borders under bilinear sampling: thin pale outlines round every throat island)
        _, (gy, gx) = ndimage.distance_transform_edt(~cov, return_indices=True)
        soft = np.where(cov, soft, soft[gy, gx])
        s1 = np.asarray(Image.fromarray((np.clip(soft, 0, 1) * 255).astype(np.uint8)).resize(nm.shape[1::-1], Image.BILINEAR), float) / 255
        flat = np.array([128.0, 128.0, 255.0])
        Image.fromarray(np.clip(nm * (1 - s1[..., None]) + flat * s1[..., None], 0, 255).astype(np.uint8)).save(nf)
    print('FIXNECK', p, 'skin ref', ref.round(), 'texels', int((soft > 0.5).sum()))
