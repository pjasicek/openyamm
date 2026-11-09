#!/usr/bin/env python3
"""Runtime maps for the body and head sets from the Meshy returns (meshy/{body,head}_texture_r1), with the project's
material contract: base colour (AO-graded), tangent normal, specular/roughness, hide/belly region mask; ivory parts
(rebuilt horns and spikes, teeth, claws and spurs) painted clean ivory; the eyes painted by position (gold iris, dark
rim, vertical slit pupil).
Head and body hide and belly luminance are both quantile-matched to the installed body's distributions, so the
region ramps give both sets the same colour (user: "make sure somehow the scaling/color matches the body").
Ramps: the installed (accepted v7) ramps with more chroma, from the restored x2 comparison (user: "a bit more
saturated color ... check the original restored x2"): see SATURATION below; tier A's gold also turns towards the
x2's orange gold. Out: textures/cdr1r_{body,head}_{basecolor_2k,normal_2k,metal_rough_2k,region_mask}.png,
textures/cdr1r_ramps.json (per material name: region ramps), work/compose_report.json."""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

P = Path(__file__).resolve().parents[1]; T = P / 'textures'; N = 2048
sys.path.insert(0, str(P.parent / 'claude_shared')); import region_variants as R  # noqa: E402
sys.path.insert(0, str(P.parents[2] / 'tools')); from normal_map_convention import measure  # noqa: E402
sys.path.insert(0, str(P / 'scripts')); import glb_raster as G  # noqa: E402
W = np.array([.2126, .7152, .0722]); lin = R.srgb_to_linear
enc = lambda c: np.where(c <= .0031308, c * 12.92, 1.055 * np.maximum(c, 0) ** (1 / 2.4) - .055)
SATURATION = {'hide': 1.30, 'belly': 1.45}          # linear chroma gain about luminance (x2: red C 55 vs 39-45,
GOLD_TINT_A = np.array([1.0, .86, .62])             # gold C 57 vs 37, gold hue 62 vs 73 degrees)
PART = {'skin': 0, 'horn': 1, 'crest': 2, 'teeth': 3, 'eyes': 4, 'tongue': 5, 'ivory': 6, 'spines': 7}


def load(p, mode='RGB'):
    return np.array(Image.open(p).convert(mode).resize((N, N), Image.Resampling.LANCZOS), float) / 255


def save(c, p):
    Image.fromarray(np.uint8(np.clip(c, 0, 1) * 255 + .5)).save(p)


def pad(c, cov):
    return c[tuple(ndimage.distance_transform_edt(~cov, return_distances=False, return_indices=True))]


def quantile_match(lum, sel, target):
    q = np.linspace(0, 100, 201)
    sq = np.maximum.accumulate(np.percentile(lum[sel], q) + np.arange(201) * 1e-9)
    return np.interp(lum, sq, np.percentile(target, q))


# installed body distributions and accepted ramps
doc, binary = G.read_glb(P / 'export/mm6_cdr1_unified.glb')
mats = {m['name']: m for m in doc['materials']}
prims = G.lod0_primitives(doc, binary, 'Body')
m = mats['DragonBody_A']
obase = np.asarray(G.image(doc, binary, m['pbrMetallicRoughness']['baseColorTexture']['index']).convert('RGB'), np.float32) / 255
omask = np.asarray(G.image(doc, binary, m['extras']['openyamm_region_mask']['index']).convert('RGBA')
                   .resize(obase.shape[1::-1]), np.float32) / 255
_, ocov = G.raster(prims['DragonBody_A']['pos'], prims['DragonBody_A']['uv'], prims['DragonBody_A']['idx'], obase.shape[0])
olum = lin(obase) @ W
target = {'hide': olum[ocov & (omask[..., 0] > .8)], 'belly': olum[ocov & (omask[..., 1] > .8)]}

report = {}
for label in ['body', 'head']:
    d = np.load(P / 'work' / f'uvraster_{label}.npz'); part = d['piece']; cov = part >= 0; pos = d['pos']; nrm = d['normal']
    src = P / 'meshy' / f'{label}_texture_r1'
    rgb = load(src / 'texture_urls_0_base_color.png')
    ao = ndimage.gaussian_filter(load(T / f'cdr1_{label}_ao_1k.png', 'L'), 1.5)
    rgb *= .80 + .20 * ao[..., None]
    h, s, v = np.moveaxis(np.array(Image.fromarray(np.uint8(np.clip(rgb, 0, 1) * 255)).convert('HSV')) / 255, -1, 0)
    ivory = cov & np.isin(part, [PART['horn'], PART['teeth'], PART['ivory']])
    eyes = cov & (part == PART['eyes'])
    gold = cov & ((np.isin(part, [PART['crest'], PART['spines']])) |
                  ((part == PART['skin']) & (h > 32 / 360) & (h < 85 / 360) & (s > .32))) | eyes
    hide = cov & ~gold & ~ivory
    # luminance: both sets onto the installed body's hide / belly distributions (hue and detail kept)
    lum = lin(rgb) @ W; out = lin(rgb)
    for name, sel in (('hide', hide), ('belly', gold & ~eyes)):
        matched = quantile_match(lum, sel, target[name])
        ratio = np.where(lum > 1e-5, matched / np.maximum(lum, 1e-5), 1.0)
        out[sel] *= ratio[sel, None]
    rgb = np.clip(enc(np.clip(out, 0, 1)), 0, 1)
    # ivory: clean enamel with a little of the source variation
    l2 = rgb @ W
    rgb[ivory] = np.clip((.76 + .20 * l2[ivory, None]) * np.array([1., .98, .87]), 0, 1)
    # eyes: per eye (side of x), iris by angle from the eye's outward axis; slit pupil along the eye's vertical
    if eyes.any():
        for side in (-1, 1):
            sel = eyes & (np.sign(pos[..., 0]) == side)
            if not sel.any():
                continue
            c = pos[sel].mean(0); a = nrm[sel].mean(0); a /= np.linalg.norm(a)
            up = np.array([0, 0, 1.]) - a * a[2]; up /= np.linalg.norm(up); across = np.cross(a, up)
            dvec = pos[sel] - c; facing = dvec @ a
            q = dvec - np.outer(facing, a); R_ = np.percentile(np.linalg.norm(q, axis=1), 98)
            r = np.linalg.norm(q, axis=1) / max(R_, 1e-6); qa = (q @ across) / R_; qu = (q @ up) / R_
            col = np.where(r[:, None] < .78, np.array([1.0, .80, .22]) * (1.05 - .45 * r[:, None]),
                           np.array([.35, .18, .05]))                      # iris (bright centre), dark rim
            slit = (np.abs(qa) < .11 * np.sqrt(np.clip(1 - (qu / .8) ** 2, 0, 1))) & (r < .8)
            col[slit] = [.03, .02, .01]
            col[facing < -.25 * R_] = [.05, .03, .02]                       # back of the eyeball
            rgb[sel] = col
    masks = [ndimage.gaussian_filter(pad(mk.astype(float), cov), .65) for mk in (hide, gold)]
    normal = load(src / 'texture_urls_0_normal.png'); corr = measure(np.uint8(normal * 255 + .5))
    if corr < 0:
        normal[..., 1] = 1 - normal[..., 1]
    flat = ivory | eyes
    normal[flat] = normal[flat] * .35 + np.array([.5, .5, 1.]) * .65        # smooth enamel, keep a little grain
    rough = np.full((N, N), .82); rough[ivory] = .45; rough[eyes] = .25
    spec = np.full((N, N), .14); spec[ivory] = .35; spec[eyes] = .5; spec *= .35 + .65 * ao
    save(pad(rgb, cov), T / f'cdr1r_{label}_basecolor_2k.png')
    save(pad(normal, cov), T / f'cdr1r_{label}_normal_2k.png')
    save(np.stack([pad(spec, cov), pad(rough, cov), np.zeros_like(spec)], -1), T / f'cdr1r_{label}_metal_rough_2k.png')
    R.write_mask(masks, T / f'cdr1r_{label}_region_mask.png', size=N)
    after = lin(rgb) @ W
    report[label] = {'covered': int(cov.sum()), 'hide': int(hide.sum()), 'gold': int(gold.sum()), 'ivory': int(ivory.sum()),
                     'eyes': int(eyes.sum()), 'normal_correlation': corr,
                     'hide_lum_p10_50_90': np.percentile(after[hide], [10, 50, 90]).round(3).tolist(),
                     'belly_lum_p10_50_90': np.percentile(after[gold & ~eyes], [10, 50, 90]).round(3).tolist()}

# ramps: accepted ramps with more chroma about each colour's luminance (linear), tier A gold towards orange
ramps = {}
for name, mat in mats.items():
    rr = []
    for k, reg in enumerate(mat['extras']['openyamm_region_ramps']):
        cols = np.array(reg['colors'])
        if k == 1 and name.endswith('_A'):
            y = cols @ W; cols = cols * GOLD_TINT_A; cols *= (y / np.maximum(cols @ W, 1e-9))[:, None]
        y = (cols @ W)[:, None]; g = SATURATION['hide' if k == 0 else 'belly']
        cols = np.clip(y + (cols - y) * g, 0, 1)
        rr.append({'range': reg['range'], 'colors': cols.tolist()})
    ramps[name] = rr
(T / 'cdr1r_ramps.json').write_text(json.dumps(ramps, indent=1) + '\n')
(P / 'work' / 'compose_report.json').write_text(json.dumps(report, indent=1) + '\n')
print('COMPOSE', json.dumps(report))
