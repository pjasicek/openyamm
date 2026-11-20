#!/usr/bin/env python3
"""Runtime maps for the retextured bat (meshy/bat_texture_r1) on the fixed 40 % mesh: base colour (AO-graded),
tangent normal, metal/roughness, membrane/body region mask. Regions come from Meshy's colours (blue membrane,
grey fur; an old-mask transfer by nearest face was blocky along the wing bones), and each region's luminance is quantile-matched
to the installed texture's, so the accepted tier ramps keep their look. Painted by part: fangs ivory, claws from the
toe colour to ivory at the tip (`tip` face attribute); eyes, inner ears and mouth keep Meshy's colours.
Out: textures/bat_{basecolor_2k,normal_1k,metal_rough_1k,region_mask}.png, work/compose_report.json."""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.spatial import cKDTree

P = Path(__file__).resolve().parents[1]; T = P / 'textures'; T.mkdir(exist_ok=True); N = 2048
sys.path.insert(0, str(P.parent / 'claude_shared')); import region_variants as R  # noqa: E402
sys.path.insert(0, str(P.parents[2] / 'tools')); from normal_map_convention import measure  # noqa: E402
W = np.array([.2126, .7152, .0722]); lin = R.srgb_to_linear
enc = lambda c: np.where(c <= .0031308, c * 12.92, 1.055 * np.maximum(c, 0) ** (1 / 2.4) - .055)
PART = {'body': 0, 'claw': 1, 'teeth': 3, 'eyes': 4, 'tongue': 5, 'membrane': 8}
IVORY = np.array([.93, .90, .80])


def load(p, mode='RGB', size=N):
    return np.array(Image.open(p).convert(mode).resize((size, size), Image.Resampling.LANCZOS), float) / 255


def save(c, p, size=None):
    im = Image.fromarray(np.uint8(np.clip(c, 0, 1) * 255 + .5))
    (im.resize((size, size), Image.Resampling.LANCZOS) if size else im).save(p)


def pad(c, cov):
    return c[tuple(ndimage.distance_transform_edt(~cov, return_distances=False, return_indices=True))]


def quantile_match(lum, sel, target):
    q = np.linspace(0, 100, 201)
    sq = np.maximum.accumulate(np.percentile(lum[sel], q) + np.arange(201) * 1e-9)
    return np.interp(lum, sq, np.percentile(target, q))


d = np.load(P / 'work/uvraster_bat.npz'); part = d['piece']; cov = part >= 0; pos = d['pos']; nrm = d['normal']; tip = d['tip']
old_base = np.asarray(Image.open(P / 'work/old_base.png').convert('RGB'), np.float32) / 255
old_mask = np.stack([np.asarray(ch.resize((N, N), Image.Resampling.BILINEAR), np.float32)   # per channel: an RGBA resize
                     for ch in Image.open(P / 'work/old_mask.png').convert('RGBA').split()], -1) / 255  # premultiplies by the empty alpha
# installed per-region luminance distributions (on the installed layout)
olum = lin(old_base) @ W
target = {k: olum[old_mask[..., k] > .8] for k in range(2)}

src = P / 'meshy/bat_texture_r1'
rgb = load(src / 'texture_urls_0_base_color.png')
# regions from Meshy's own colours (as mm6_bat_claude/scripts/compose_bat.py): blue membrane, grey fur; the red and
# pink parts (eyes, inner ears, mouth) keep Meshy's colours and take no ramp
h, sat, val = np.moveaxis(np.array(Image.fromarray(np.uint8(np.clip(rgb, 0, 1) * 255)).convert('HSV'), np.float32) / 255, -1, 0)
hd = h * 360
membrane = cov & (hd > 170) & (hd < 260) & (sat > .22)
pink = cov & ((hd < 25) | (hd > 315)) & (sat > .28) & ~membrane
fixed = np.isin(part, [PART['teeth'], PART['claw']]) & cov
body = cov & ~membrane & ~pink & ~fixed
mask = np.stack([ndimage.gaussian_filter(pad(m_.astype(np.float32), cov), .7) for m_ in (membrane, body)], -1)
ao = ndimage.gaussian_filter(load(T / 'bat_ao_1k.png', 'L'), 1.5); rgb *= .82 + .18 * ao[..., None]
lum = lin(rgb) @ W; out = lin(rgb); wsum = np.zeros((N, N))
gain = np.zeros((N, N))
for k in range(2):
    sel = cov & (mask[..., k] > .8)
    ratio = np.where(lum > 1e-5, quantile_match(lum, sel, target[k]) / np.maximum(lum, 1e-5), 1.0)
    gain += (ratio - 1) * mask[..., k]; wsum += mask[..., k]
gain = np.where(wsum > 1, gain / np.maximum(wsum, 1e-6), gain)
out *= (1 + gain)[..., None]
rgb = np.clip(enc(np.clip(out, 0, 1)), 0, 1)
teeth = cov & (part == PART['teeth']); claws = cov & (part == PART['claw']); eyes = cov & (part == PART['eyes'])
l2 = rgb @ W
rgb[teeth] = np.clip(IVORY * (.85 + .15 * l2[teeth, None]), 0, 1)
w = np.clip((tip - .03) / .25, 0, 1)[..., None]; w = w * w * (3 - 2 * w)   # ivory from just above the toe
rgb[claws] = (rgb * (1 - w) + IVORY * (.9 + .1 * l2[..., None]) * w)[claws]
for sel in (teeth, claws):                              # neither takes the tier ramps
    mask[sel] = 0
normal = load(src / 'texture_urls_0_normal.png'); corr = measure(np.uint8(normal * 255 + .5))
if corr < 0:
    normal[..., 1] = 1 - normal[..., 1]
flat = teeth | (claws & (w[..., 0] > .5))
normal[flat] = normal[flat] * .3 + np.array([.5, .5, 1.]) * .7
membrane = mask[..., 0] > .5
rough = np.full((N, N), .72); rough[membrane] = .6; rough[teeth | (claws & (w[..., 0] > .5))] = .35
save(pad(rgb, cov), T / 'bat_basecolor_2k.png')
save(pad(normal, cov), T / 'bat_normal_1k.png', 1024)
save(np.stack([np.ones((N, N)), pad(rough, cov), np.zeros((N, N))], -1), T / 'bat_metal_rough_1k.png', 1024)
R.write_mask([pad(mask[..., 0], cov), pad(mask[..., 1], cov)], T / 'bat_region_mask.png', size=1024)
after = lin(rgb) @ W
rep = {'covered': int(cov.sum()), 'teeth': int(teeth.sum()), 'claws': int(claws.sum()), 'membrane': int(membrane.sum()), 'pink': int(pink.sum()),
       'normal_correlation': corr,
       'membrane_lum_new_old_p50': [round(float(np.median(after[cov & (mask[..., 0] > .8)])), 3), round(float(np.median(target[0])), 3)],
       'body_lum_new_old_p50': [round(float(np.median(after[cov & (mask[..., 1] > .8)])), 3), round(float(np.median(target[1])), 3)]}
(P / 'work/compose_report.json').write_text(json.dumps(rep, indent=1) + '\n'); print('COMPOSE', rep)
