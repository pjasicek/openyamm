#!/usr/bin/env python3
"""Grade a Meshy statue texture to its native sprite (native shading transfer on a static prop): every covered texel
keeps its rank in the Meshy base colour's luminance (carved detail, painted shade) and takes the sprite's colour at
that rank from the sprite's own luminance-sorted ramp (gold pixels excluded), with the contrast eased (the engine
lights the model on top). Texels in a plinth band (below `plinth` of the height) use the sprite's plinth rows; on
7dec54, saturated yellow Meshy texels take the sprite's gold ramp. Normal map kept; metallic-roughness: metal 0,
roughness at least 0.6. Writes textures/hd_<name>_{basecolor,normal,mr}.png and work/hd_<name>_texture.json (mean
of the covered base colour, for hd_build.py's COLOR_0 tint).
Usage: hd_grade.py <name> <base colour png> <normal png> <mr png>"""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import statue_compose as sc  # noqa: E402

HERE = sc.HERE
SPECS = {
    '7dec55': {'sprites': [f'7dec55a{k}_p3.png' for k in range(4)], 'gold': False, 'plinth': None},
    '7dec54': {'sprites': [f'7dec54a{k}_p3.png' for k in range(5)], 'gold': True, 'plinth': None},
    'dec94': {'sprites': ['dec94_p2.png'], 'gold': False, 'plinth': (0.24, 0.76)},
    'dec95': {'sprites': ['dec95_p2.png'], 'gold': False, 'plinth': (0.21, 0.79), 'soften': 1.0, 'size': 1024},
}
HEADROOM = 1.3
X2 = os.path.join(HERE, '..', '..', '..', '..', 'assets_legacy', 'decorations_x2_20261016')


def sprite_rows(names, lo, hi, gold):
    pix = []
    for n in names:
        im = sc.load(os.path.join(X2, n), mode='RGBA')
        h = im.shape[0]
        rows = np.nonzero(im[..., 3].max(1) > 0.5)[0]
        top, bottom = rows.min(), rows.max() + 1
        a, b = int(top + (bottom - top) * lo), int(top + (bottom - top) * hi)
        p = im[a:b][im[a:b, ..., 3] > 0.5][:, :3]
        g = sc.gold_mask(p)
        pix.append(p[g] if gold else p[~g])
    p = np.concatenate(pix)
    return p[np.argsort(p @ sc.LUMA)]


def main():
    name, base, normal, mr = sys.argv[1:5]
    spec = SPECS[name]
    img = sc.load(base)
    h, w = img.shape[:2]
    tris = np.load(os.path.join(HERE, 'statues_hd', name, 'meshy', 'uv_tris.npy'))
    cover = Image.new('L', (w, h)); height = Image.new('L', (w, h))
    dc, dh = ImageDraw.Draw(cover), ImageDraw.Draw(height)
    for t in tris:
        poly = [(u * w, (1 - v) * h) for u, v, _ in t]
        dc.polygon(poly, fill=255)
        dh.polygon(poly, fill=int(np.clip(t[:, 2].mean(), 0, 1) * 255))
    covered = np.asarray(cover) > 0
    zt = np.asarray(height) / 255.0
    from scipy.ndimage import gaussian_filter
    # the Meshy stone grain is high-contrast speckle; the sprites' stone is smoother: rank a softened luminance
    lum = gaussian_filter(img @ sc.LUMA, spec.get('soften', 1.4))
    out = img.copy()
    groups = []
    if spec['plinth']:
        cut = spec['plinth'][0]
        groups.append((covered & (zt < cut), sprite_rows(spec['sprites'], spec['plinth'][1], 1.0, False)))
        groups.append((covered & (zt >= cut), sprite_rows(spec['sprites'], 0.0, spec['plinth'][1], False)))
    else:
        rest = covered.copy()
        if spec['gold']:
            gold = covered & sc.atlas_gold_mask(img)
            groups.append((gold, sprite_rows(spec['sprites'], 0, 1, True)))
            rest &= ~gold
            print('GOLD texels', int(gold.sum()))
        groups.append((rest, sprite_rows(spec['sprites'], 0, 1, False)))
    for mask, ramp in groups:
        r = sc.rank(lum[mask])
        colour = sc.ramp(r, ramp)
        mean = colour.mean(0)
        out[mask] = mean + (colour - mean) * spec.get('contrast', 0.8)
    out = sc.dilate_fill(out, covered)
    albedo = (out[covered].mean(0) * 255).round(1).tolist()
    # headroom: COLOR_0 (occlusion x tint) only darkens, so the texture is stored brighter (linear x HEADROOM) and the
    # tint brings the albedo back to the graded mean
    lin = np.where(out <= 0.04045, out / 12.92, ((out + 0.055) / 1.055) ** 2.4) * HEADROOM
    out = np.where(lin <= 0.0031308, lin * 12.92, 1.055 * np.clip(lin, 0, 1) ** (1 / 2.4) - 0.055)
    mean = (out[covered].mean(0) * 255).round(1).tolist()
    json.dump({'mean': mean, 'albedo': albedo}, open(os.path.join(HERE, 'work', f'hd_{name}_texture.json'), 'w'))
    print('MEAN', name, mean)
    size = spec.get('size', 1536)            # dec95 is a 60-unit statue: 1024 is plenty
    sc.save(os.path.join(sc.TEX, f'hd_{name}_basecolor.png'), out, (size, size))
    sc.save(os.path.join(sc.TEX, f'hd_{name}_normal.png'), sc.load(normal), (min(1024, size), min(1024, size)))
    m = sc.load(mr)
    m[..., 2] = 0.0
    m[..., 1] = np.maximum(m[..., 1], 0.6)
    sc.save(os.path.join(sc.TEX, f'hd_{name}_mr.png'), m, (256, 256))


if __name__ == '__main__':
    main()
