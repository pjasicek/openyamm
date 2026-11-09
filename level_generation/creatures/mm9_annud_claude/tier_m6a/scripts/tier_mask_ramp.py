#!/usr/bin/env python3
"""Region masks and the colour ramp of tier pm6_a (MM9 row 47, PeasantM6a: Annud's body with a mustard tunic where
PeasantM6b, Annud's own skin, is red). CLAUDE_CREATURE_TEXTURES.md: one shared texture set, region mask + ramp; the
approved Annud images are only read.

Mask (one region, the tunic cloth): per texel of the installed GLB's base colour (body 2K, head 2K, area-averaged to
the 1K mask) the woven red tunic is saturation >= ~0.7 at hue 4-28 deg and value below ~0.8; trousers (saturation
~0.56), shoes (below the tunic hem: rest-pose height from uv_positions.py), skin, hair, the cream rope belt and the
gold trim (hue >= 30) fall outside. Texels inside the gold trim bands (gold density in a 9x9 window >= 0.2) stay out,
so the trim's dark ground keeps Annud's colour as MM9's M6a keeps its trim. Padded into the gutters from the nearest
island texel, then a 1-texel feather.

Ramp: the native tunic texels (where M6b is red and M6a mustard) of PEASANTM6A.dtx sorted by luminance into 16 stops,
in linear RGB, times a brightness factor (--brightness, default 1.0 = MM9's own M6a luminance). Annud's albedo ratio
to PeasantM6b (k, our graded tunic's mean linear luminance over M6b's native tunic, 0.82) is reported: scaling M6a by it
turned the mustard olive-brown on the model (review/sheet_pm6a_torso_k082.png), so the tier keeps M6a's own luminance.
Range = the 2nd-98th luminance percentiles of the masked body texels.

Usage (tier_m6a/): tier_mask_ramp.py <installed glb> <m6a.png> <m6b.png> [--brightness F]"""
import io
import json
import struct
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hsv import rgb_to_hsv  # noqa: E402

LUMA = np.array([0.2126, 0.7152, 0.0722])
SIZE = 1024


def lin(srgb):
    return np.where(srgb <= 0.04045, srgb / 12.92, ((srgb + 0.055) / 1.055) ** 2.4)


def smooth(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def glb_image(path, name):
    b = open(path, 'rb').read()
    jl = struct.unpack('<I', b[12:16])[0]
    doc = json.loads(b[20:20 + jl])
    binary = b[20 + jl + 8:]
    image = next(im for im in doc['images'] if im['name'] == name)
    bv = doc['bufferViews'][image['bufferView']]
    o = bv.get('byteOffset', 0)
    return Image.open(io.BytesIO(binary[o:o + bv['byteLength']])).convert('RGB')


def tunic_weight(rgb, pos, covered, min_height, max_height):
    hsv = rgb_to_hsv(rgb)
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    hue = smooth(h, 2, 6) * (1 - smooth(h, 26, 31))
    w = hue * smooth(s, 0.64, 0.76) * (1 - smooth(v, 0.72, 0.85))
    y = pos[..., 1]
    w *= smooth(y, min_height - 0.03, min_height + 0.03) * (1 - smooth(y, max_height - 0.03, max_height + 0.03))
    gold = ((h >= 30) & (h <= 62) & (v >= 0.42) & (s >= 0.35)).astype(float)
    density = ndimage.uniform_filter(gold, 9)
    w *= density < 0.2
    w[~covered] = 0
    # Pad like the colour: every gutter texel takes its nearest island texel's weight, then feather one texel.
    _, (iy, ix) = ndimage.distance_transform_edt(~covered, return_indices=True)
    w = w[iy, ix]
    return ndimage.gaussian_filter(w, 0.7)


def main():
    glb, m6a_path, m6b_path = sys.argv[1:4]
    brightness = float(sys.argv[sys.argv.index('--brightness') + 1]) if '--brightness' in sys.argv else 1.0
    out = Path('textures')
    body = np.asarray(glb_image(glb, 'annud_tp_basecolor_graded').resize((SIZE, SIZE), Image.BOX)) / 255.0
    head = np.asarray(glb_image(glb, 'annud_tp_head_basecolor_export').resize((SIZE, SIZE), Image.BOX)) / 255.0
    pb, ph = np.load('work/uv_positions.npz'), np.load('work/uv_positions_head.npz')
    # Tunic hem at ~0.65 m (rest pose, GLB metres); the head set's tunic is the collar under the neck (below 1.55).
    wb = tunic_weight(body, pb['pos'], pb['covered'], 0.65, 9.0)
    wh = tunic_weight(head, ph['pos'], ph['covered'], 1.20, 1.55)

    a = np.asarray(Image.open(m6a_path).convert('RGB')) / 255.0
    b = np.asarray(Image.open(m6b_path).convert('RGB')) / 255.0
    ha, hb = rgb_to_hsv(a), rgb_to_hsv(b)
    native = (hb[..., 0] < 25) & (hb[..., 1] > 0.45) & (ha[..., 0] > 30) & (ha[..., 0] < 60) & (ha[..., 1] > 0.45)
    la, lb = lin(a[native]), lin(b[native])
    full = (wb > 0.9) & pb['covered']
    ours = lin(body[full])
    our_lum = ours @ LUMA
    k = our_lum.mean() / (lb @ LUMA).mean()
    order = np.argsort(la @ LUMA)
    stops = np.array_split(la[order], 16)
    colors = np.clip(np.array([s.mean(0) for s in stops]) * brightness, 0, 1)
    lo, hi = np.percentile(our_lum, [2, 98])
    ramp = {'range': [round(float(lo), 5), round(float(hi), 5)],
            'colors': [[round(float(c), 5) for c in row] for row in colors]}

    for name, w in (('annud_m6a_region_mask', wb), ('annud_m6a_head_region_mask', wh)):
        zero = np.zeros_like(w)
        Image.merge('RGBA', [Image.fromarray(np.clip(x * 255 + 0.5, 0, 255).astype(np.uint8), 'L')
                             for x in (w, zero, zero, zero)]).save(out / f'{name}.png', optimize=True)
    report = {
        'variant': 'pm6_a', 'mm9_row': 47, 'native_skin': 'PEASANTM6A.dtx', 'approved_skin': 'PEASANTM6B.dtx',
        'native_tunic_texels': int(native.sum()), 'albedo_ratio_k': round(float(k), 4), 'brightness': brightness,
        'native_m6a_tunic_mean_srgb': [round(float(x) * 255) for x in a[native].mean(0)],
        'native_m6b_tunic_mean_srgb': [round(float(x) * 255) for x in b[native].mean(0)],
        'our_tunic_mean_srgb': [round(float(x) * 255) for x in body[full].mean(0)],
        'body_mask_coverage': round(float((wb > 0.5).mean()), 4),
        'head_mask_coverage': round(float((wh > 0.5).mean()), 4),
        'ramp': ramp,
    }
    (out / 'annud_m6a_ramps.json').write_text(json.dumps(report, indent=1))
    print('TIER_MASK_RAMP', json.dumps({k_: v for k_, v in report.items() if k_ != 'ramp'}), 'range', ramp['range'])


if __name__ == '__main__':
    main()
