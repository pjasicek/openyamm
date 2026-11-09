"""Tone check of the texture pass: the engine's tier colour (base colour, region mask and ramps as fs_model.sc applies
them) of the approved and the new maps at the same surface points (texels of the new layout; approved values
sampled through the installed UVs), per tier and region: median sRGB, luminance spread around the median
(p10/p90 of lum / median) and the 4-16 px band at the approved texel density.
Usage: texpass_tone.py <before.glb> <after.glb>
"""
import json
import sys
from pathlib import Path

import numpy as np
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).resolve().parent))
from texpass_glb import PROJECT, TP, read_glb  # noqa: E402
from transfer_textures import image, sample  # noqa: E402

sys.path.insert(0, str(PROJECT.parent / 'claude_shared'))
import region_variants as R  # noqa: E402

W = np.array([0.2126, 0.7152, 0.0722])


def srgb(c):
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.clip(c, 0, None) ** (1 / 2.4) - 0.055)


def tiers(path, uv):
    doc, binary = read_glb(Path(path))
    m0 = doc['materials'][0]
    base = sample(image(doc, binary, m0['pbrMetallicRoughness']['baseColorTexture']['index']) / 255, uv)
    mask = sample(image(doc, binary, m0['extras']['openyamm_region_mask']['index'], 'RGBA') / 255, uv)
    lin = R.srgb_to_linear(np.clip(base, 0, 1))
    lum = lin @ W
    out = {}
    for m in doc['materials'][:3]:
        colour = lin.copy()
        for c, region in enumerate(m['extras']['openyamm_region_ramps']):
            lo, hi = region['range']
            stops = np.array(region['colors'])
            x = np.clip((lum - lo) / (hi - lo), 0, 1) * 15
            i = np.minimum(x.astype(int), 14)
            f = (x - i)[:, None]
            colour = colour * (1 - mask[:, c:c + 1]) + (stops[i] * (1 - f) + stops[i + 1] * f) * mask[:, c:c + 1]
        out[m['name'][-1]] = srgb(colour)
    return out, mask


r = np.load(TP / 'raster_1024.npz')
cov = r['triangle'] >= 0
new_uv = np.stack(np.meshgrid((np.arange(1024) + .5) / 1024, (np.arange(1024) + .5) / 1024), -1)[cov]
before, mask_b = tiers(sys.argv[1], r['old_uv'][cov])
after, mask_a = tiers(sys.argv[2], new_uv)
report = {}
for tier in before:
    for c, name in enumerate(('scales', 'ventral', 'fins')):
        sel = (mask_b[:, c] > .9) & (mask_a[:, c] > .9)
        row = {}
        for label, data in (('before', before[tier]), ('after', after[tier])):
            lum = data[sel] @ W
            med = np.median(lum)
            image_lum = np.zeros((1024, 1024))
            image_lum[cov] = data @ W
            band = ndimage.gaussian_filter(image_lum, 2) - ndimage.gaussian_filter(image_lum, 8)
            row[label] = {'median_srgb': np.round(np.median(data[sel], 0) * 255).astype(int).tolist(),
                          'spread_p10_p90': [round(float(np.percentile(lum, 10) / med), 3),
                                             round(float(np.percentile(lum, 90) / med), 3)],
                          'band_rms': round(float(np.sqrt((band[cov][sel] ** 2).mean()) * 255), 2)}
        report[f'{tier}_{name}'] = dict(row, texels=int(sel.sum()))
(TP / 'tone_report.json').write_text(json.dumps(report, indent=1) + '\n')
for key, row in report.items():
    print(key, row['texels'], 'before', row['before'], '\n   after ', row['after'])
