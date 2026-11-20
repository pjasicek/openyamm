#!/usr/bin/env python3
"""New body half of the djinn atlas from the Meshy body retexture (meshy/body_texture_r1), the head half kept as
installed. The upload's body square (u, v in [0, 0.92]) is resampled to the atlas's left 1024 px. Regions from Meshy's
own colours (blue skin, gold metal, saturated gems on the gold accessories, grey vortex); skin and gem luminance are
quantile-matched to the installed body half so the shared tier ramps keep their look. PBR as the original
(mm6_djn_claude/scripts/compose_genie.py): matte skin, gold metal, glossy gems. The 32 px gutter takes the body's
edge. Out: textures/djn_{basecolor,metal_rough,normal,region_mask}_atlas.png, work/compose_report.json."""
import io
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

P = Path(__file__).resolve().parents[1]; T = P / 'textures'; T.mkdir(exist_ok=True); N = 1024; UP = .92
sys.path.insert(0, str(P.parent / 'claude_shared')); import region_variants as R  # noqa: E402
sys.path.insert(0, str(P.parents[2] / 'tools')); from normal_map_convention import measure  # noqa: E402
sys.path.insert(0, str(P / 'scripts')); import glb_raster as G  # noqa: E402
W = np.array([.2126, .7152, .0722]); lin = R.srgb_to_linear
enc = lambda c: np.where(c <= .0031308, c * 12.92, 1.055 * np.maximum(c, 0) ** (1 / 2.4) - .055)


def pad(a, cov):
    return a[tuple(ndimage.distance_transform_edt(~cov, return_distances=False, return_indices=True))]


def hsv(a):
    return np.moveaxis(np.asarray(Image.fromarray(np.uint8(np.clip(a, 0, 1) * 255)).convert('HSV'), float) / 255, -1, 0)


def quantile_match(lum, sel, target):
    q = np.linspace(0, 100, 201)
    sq = np.maximum.accumulate(np.percentile(lum[sel], q) + np.arange(201) * 1e-9)
    return np.interp(lum, sq, np.percentile(target, q))


def from_upload(name):
    """Meshy map -> body square at N (square uv = upload uv / 0.92)"""
    src = np.asarray(Image.open(P / 'meshy/body_texture_r1' / f'texture_urls_0_{name}.png').convert('RGB'), float) / 255
    S = src.shape[0]; yy, xx = np.mgrid[:N, :N]
    u = (xx + .5) / N * UP; v = (1 - (yy + .5) / N) * UP
    coords = np.array([(1 - v) * S - .5, u * S - .5])
    return np.stack([ndimage.map_coordinates(src[..., i], coords, order=1, mode='nearest') for i in range(3)], -1)


# installed atlas (head half kept) and its body-half distributions
doc, b = G.read_glb(P.parents[2] / 'assets_source/worlds/mm6/models/mm6_djn.glb')
mat = next(m for m in doc['materials'] if m['name'] == 'Genie_A')
idx = {'base': mat['pbrMetallicRoughness']['baseColorTexture']['index'], 'mr': mat['pbrMetallicRoughness']['metallicRoughnessTexture']['index'],
       'normal': mat['normalTexture']['index'], 'mask': mat['extras']['openyamm_region_mask']['index']}
old = {k: np.asarray(G.image(doc, b, i).convert('RGBA' if k == 'mask' else 'RGB'), float) / 255 for k, i in idx.items()}
ob, om = old['base'][:, :N], old['mask'][:, :N]
olum = R.luminance(ob)
target = {'skin': olum[om[..., 0] > .8], 'gems': olum[om[..., 1] > .8]}

r = np.load(P / 'work/body_raster.npz'); bone = r['bone']; names = list(r['bone_names']); cov = bone >= 0
bname = np.array(names + ['-'])[bone]
accessory = cov & np.char.startswith(bname.astype(str), 'Gold')
vortex = cov & np.char.startswith(bname.astype(str), 'Vortex')
body = from_upload('base_color')
h, s, v = hsv(body)
gold = cov & (h > .07) & (h < .20) & (s > .3) & (v > .28)
skin = cov & (h > .48) & (h < .73) & (s > .18) & ~accessory & ~vortex
# gems: the non-gold texels on the gold pieces. Meshy painted them dark navy; the reference has green studs on the
# armlet and bracer, a red centre gem on the bracer and red gems on the wrist bracelet. Clustered in 3D: the bracer's
# largest gem and the bracelet's gems are painted red (no ramp), the rest are the tier-ramped gem region (dark studs).
stones = accessory & ~gold & ((v < .75) | (s > .35))          # dark stones and Meshy's bright green paint
mred = accessory & ((h < .05) | (h > .93)) & (s > .45) & (v > .3)   # Meshy's own red gems (bracer centre)
gy, gx = np.nonzero(stones | mred); piece = bname[gy, gx]
red = mred[gy, gx] | (piece == 'GoldBracelet')
shade = np.clip(R.luminance(body[gy, gx]) / max(np.percentile(R.luminance(body[gy, gx]), 90), 1e-3), .25, 1.2)[:, None]
keep = mred[gy, gx]                                      # Meshy's red stays as painted
paint = red & ~keep
body[gy[paint], gx[paint]] = np.clip(np.array([.92, .10, .08]) * (.72 + .38 * shade[paint]), 0, 1)
# studs: the installed gem ramp is near-black navy in every tier (the accepted look: dark studs, red centre gems),
# so the stud base is that navy too; a green base bled through the soft mask edge as green rims
body[gy[~red], gx[~red]] = np.clip(np.array([.05, .08, .17]) * (.8 + .4 * shade[~red]), 0, 1)
nc = 0
gems = np.zeros_like(stones); gems[gy[~red], gx[~red]] = True
reds = np.zeros_like(stones); reds[gy[red], gx[red]] = True
h, s, v = hsv(body)
# vortex: Meshy's silver is right for the reference, brought to the installed (accepted) brightness
ovortex = (om[..., 0] < .2) & (om[..., 1] < .2) & (R.luminance(ob) < .6)
osat = (ob.max(-1) - ob.min(-1)) / np.maximum(ob.max(-1), 1e-3); ovortex &= osat < .15
target['vortex'] = olum[ovortex]
# luminance onto the installed distributions (skin, gems); hue and detail kept
lum = R.luminance(body); out = lin(body)
for sel, name in ((skin, 'skin'), (vortex & ~gold, 'vortex')):
    if sel.sum() > 500 and len(target[name]) > 500:
        ratio = np.where(lum > 1e-5, quantile_match(lum, sel, target[name]) / np.maximum(lum, 1e-5), 1.0)
        out[sel] *= ratio[sel, None]
body = np.clip(enc(np.clip(out, 0, 1)), 0, 1)
rough_src = from_upload('roughness')[..., 0]
normal = from_upload('normal'); score = measure(np.uint8(normal * 255 + .5))
if score < 0:
    normal[..., 1] = 1 - normal[..., 1]
spec = np.full((N, N), .20); rg = np.clip(.8 + .2 * (rough_src - .5), .68, .94); metal = np.zeros((N, N))
spec[gold] = .8; rg[gold] = np.clip(.40 + .2 * (rough_src[gold] - .5), .29, .52); metal[gold] = .55
spec[gems | reds] = .6; rg[gems | reds] = .26
masks = [ndimage.gaussian_filter(pad(m.astype(float), cov), .55) for m in (skin, gems)]
new = {'base': pad(body, cov), 'mr': np.stack([pad(spec, cov), pad(rg, cov), pad(metal, cov)], -1),
       'normal': pad(normal, cov), 'mask': np.stack(masks + [np.zeros((N, N)), np.zeros((N, N))], -1)}
names_out = {'base': 'djn_basecolor_atlas', 'mr': 'djn_metal_rough_atlas', 'normal': 'djn_normal_atlas', 'mask': 'djn_region_mask_atlas'}
for k, img in new.items():
    atlas = old[k].copy()
    atlas[:, :N, :img.shape[-1]] = img
    atlas[:, N:N + 32, :img.shape[-1]] = img[:, -1:, :]                 # gutter takes the body edge
    if k == 'mask':
        atlas[:, :N, 3] = old['mask'][:, :N, 3]
    Image.fromarray(np.uint8(np.clip(atlas, 0, 1) * 255 + .5), 'RGBA' if k == 'mask' else 'RGB').save(T / f'{names_out[k]}.png')
after = R.luminance(body)
rep = {'covered': int(cov.sum()), 'skin': int(skin.sum()), 'gold': int(gold.sum()), 'gems': int(gems.sum()), 'red_gems': int(reds.sum()), 'gem_clusters': int(nc),
       'vortex': int(vortex.sum()), 'normal_score': score,
       'skin_lum_new_old_p50': [round(float(np.median(after[skin])), 3), round(float(np.median(target['skin'])), 3)],
       'gems_lum_new_old_p50': [round(float(np.median(after[gems])), 3) if gems.any() else None, round(float(np.median(target['gems'])), 3)]}
(P / 'work/compose_report.json').write_text(json.dumps(rep, indent=1) + '\n'); print('COMPOSE', rep)
