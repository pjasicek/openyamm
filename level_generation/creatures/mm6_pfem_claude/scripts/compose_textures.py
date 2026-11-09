#!/usr/bin/env python3
"""Compose the final A/B/C texture sets from the Meshy retexture, the Meshy-detail bake and procedural fixes.

- A base colour: retexture + green hem bands painted by rest-pose height (Meshy omitted them) + painted knife.
- Normal: retexture normal; cloth parts (skirt, sleeves, belt, green bodice) take the detail-bake fold normals.
- Metallic/roughness packed for glTF (G = roughness, B = metallic); knife steel/iron/wood and glossy eyes.
- B/C: green garment texels mapped through affine fits of the original palettes 786 -> 787 / 788.
"""
import colorsys
import json
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
STAGE1 = ROOT.parent / 'new_sorpigal_3d_stage1_20261006/pfem/source/palettes'
OUT = ROOT / 'textures'
SIZE = 2048
BANDS = [(0.19, 0.264), (0.313, 0.385)]  # green hem bands (m, rest pose), measured on the reference-derived model


def load(path, mode='RGB'):
    return np.asarray(Image.open(path).convert(mode), dtype=np.float32) / 255.0


def rasterise(data):
    uv, xyz, part = data['uv'], data['xyz'], data['part']
    part_map = np.full((SIZE, SIZE), -1, dtype=np.int32)
    xyz_map = np.zeros((SIZE, SIZE, 3), dtype=np.float32)
    for t in range(len(uv)):
        p = uv[t] * SIZE
        p[:, 1] = SIZE - p[:, 1]
        x0, y0 = np.floor(p.min(0)).astype(int); x1, y1 = np.ceil(p.max(0)).astype(int)
        x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, SIZE - 1), min(y1, SIZE - 1)
        if x1 < x0 or y1 < y0:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        a, b, c = p
        d = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(d) < 1e-12:
            continue
        w0 = ((b[1] - c[1]) * (gx - c[0]) + (c[0] - b[0]) * (gy - c[1])) / d
        w1 = ((c[1] - a[1]) * (gx - c[0]) + (a[0] - c[0]) * (gy - c[1])) / d
        w2 = 1 - w0 - w1
        inside = (w0 >= -0.02) & (w1 >= -0.02) & (w2 >= -0.02)
        ys, xs = np.nonzero(inside)
        part_map[y0 + ys, x0 + xs] = part[t]
        xyz_map[y0 + ys, x0 + xs] = (w0[inside, None] * xyz[t][0] + w1[inside, None] * xyz[t][1]
                                     + w2[inside, None] * xyz[t][2])
    # Grow islands so mip/bilinear sampling at seams reads the right part.
    for _ in range(6):
        empty = part_map < 0
        for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            src = np.roll(np.roll(part_map, dy, 0), dx, 1)
            srcx = np.roll(np.roll(xyz_map, dy, 0), dx, 1)
            take = empty & (src >= 0) & (part_map < 0)
            part_map[take] = src[take]; xyz_map[take] = srcx[take]
    return part_map, xyz_map


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def hsv(rgb):
    mx = rgb.max(-1); mn = rgb.min(-1); delta = mx - mn
    sat = np.where(mx > 1e-4, delta / np.maximum(mx, 1e-4), 0)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    h = np.zeros_like(mx)
    m = delta > 1e-5
    rc = np.where(m & (mx == r), ((g - b) / np.maximum(delta, 1e-5)) % 6, 0)
    gc = np.where(m & (mx == g), (b - r) / np.maximum(delta, 1e-5) + 2, 0)
    bc = np.where(m & (mx == b), (r - g) / np.maximum(delta, 1e-5) + 4, 0)
    h = np.where(m & (mx == r), rc, np.where(m & (mx == g), gc, np.where(m, bc, 0))) * 60
    return h, sat, mx


def palette(pid):
    raw = (STAGE1 / f'pal{pid}.act').read_bytes()
    return np.array([tuple(raw[i * 3:i * 3 + 3]) for i in range(256)], dtype=np.float32) / 255.0


def fit_palette(target):
    src = palette(786); dst = palette(target)
    differ = np.abs(src - dst).sum(1) > 0.02
    A = np.c_[src[differ], np.ones(differ.sum())]
    M, *_ = np.linalg.lstsq(A, dst[differ], rcond=None)
    return M, int(differ.sum())


def main():
    OUT.mkdir(exist_ok=True)
    data = np.load(ROOT / 'work/uv3d.npz')
    parts = [str(p) for p in data['parts']]
    P = {name: i for i, name in enumerate(parts)}
    part_map, xyz = rasterise(data)
    retex = ROOT / 'meshy/retexture_a_v1/texture_urls_0'
    base = load(str(retex) + '_base_color.png')
    normal = load(str(retex) + '_normal.png')
    rough = load(str(retex) + '_roughness.png', 'L')
    metal = load(str(retex) + '_metallic.png', 'L')
    bake_c = load(ROOT / 'texturing/bake_diffuse.png')
    bake_n = load(ROOT / 'texturing/bake_normal.png')
    z = xyz[..., 2]
    h, s, v = hsv(base)
    green = (h > 65) & (h < 175) & (s > 0.12) & (v > 0.05)
    body = part_map == P['Body']
    bodice_green = body & green & (z > 1.02) & (z < 1.25)
    band_rgb = np.median(base[bodice_green], axis=0)
    skirt = part_map == P['Skirt']
    white_lum = np.median(base[skirt & (z > 0.5)].mean(-1))
    band_w = np.zeros(z.shape, dtype=np.float32)
    for lo, hi in BANDS:
        band_w = np.maximum(band_w, smoothstep(lo - 0.003, lo + 0.003, z) * (1 - smoothstep(hi - 0.003, hi + 0.003, z)))
    band_w *= skirt
    lum = base.mean(-1, keepdims=True)
    painted = np.clip(band_rgb * np.clip(lum / white_lum, 0.45, 1.2), 0, 1)
    base_a = base * (1 - band_w[..., None]) + painted * band_w[..., None]
    # Pale linen toward the native sprite's cream-grey (Meshy's white read too bright beside sprites in-game).
    linen = (skirt | (part_map == P['SleeveLeft']) | (part_map == P['SleeveRight'])) & (base.mean(-1) > 0.55)
    tone = np.array([0.90, 0.885, 0.835], dtype=np.float32)
    linen_w = (linen * (1 - band_w))[..., None]
    base_a = base_a * (1 - linen_w) + base_a * tone * linen_w
    rough_out = rough.copy(); metal_out = metal.copy()
    # Knife: wood grip, iron guard, steel blade along the blade axis from the grip centre.
    knife = part_map == P['Knife']
    along = ((xyz - data['grip']) * data['blade']).sum(-1)
    for mask, rgb, r, m in ((knife & (along < 0.049), (0.28, 0.17, 0.10), 0.75, 0.0),
                            (knife & (along >= 0.049) & (along < 0.061), (0.30, 0.30, 0.32), 0.45, 0.85),
                            (knife & (along >= 0.061), (0.70, 0.71, 0.73), 0.28, 1.0)):
        base_a[mask] = rgb; rough_out[mask] = r; metal_out[mask] = m
        normal[mask] = (0.5, 0.5, 1.0)
    eyes = part_map == P['Eyes']
    rough_out[eyes] = 0.22; metal_out[eyes] = 0.0
    metal_out[(part_map == P['Body']) | skirt | (part_map == P['HairCap']) | (part_map == P['Braid'])] = 0.0
    # Cloth fold normals from the detail bake where its rays hit.
    hit = bake_c.sum(-1) > 0.02
    cloth = (skirt | (part_map == P['SleeveLeft']) | (part_map == P['SleeveRight']) | (part_map == P['Belt'])
             | (body & green & (z > 0.98) & (z < 1.34)))
    use = cloth & hit
    n0 = normal * 2 - 1; n1 = bake_n * 2 - 1
    blended = n0 * 0.2 + n1 * 0.8
    blended /= np.maximum(np.linalg.norm(blended, axis=-1, keepdims=True), 1e-6)
    normal_out = np.where(use[..., None], blended * 0.5 + 0.5, normal)

    def save(arr, name, mode='RGB'):
        Image.fromarray(np.clip(arr * 255 + 0.5, 0, 255).astype(np.uint8), mode).save(OUT / name, optimize=True)

    save(base_a, 'pfem_a_basecolor.png')
    save(normal_out, 'pfem_normal.png')
    mr = np.stack([np.ones_like(rough_out), rough_out, metal_out], -1)
    save(mr, 'pfem_metal_rough.png')
    report = {'band_rgb_srgb': (band_rgb * 255).round().tolist(), 'white_luminance': float(white_lum),
              'bands_m': BANDS, 'cloth_normal_texels': int(use.sum()), 'skin_fits': {}}
    # Palette skins: green garment texels (bodice + painted bands) through the 786 -> 787/788 fits.
    garment = (body | skirt) & green
    garment_w = np.where(garment, smoothstep(0.10, 0.22, hsv(base_a)[1]), 0.0)
    garment_w = np.maximum(garment_w, band_w)
    for skin, pid in (('b', 787), ('c', 788)):
        M, count = fit_palette(pid)
        mapped = np.clip(np.c_[base_a.reshape(-1, 3), np.ones(SIZE * SIZE)] @ M, 0, 1).reshape(SIZE, SIZE, 3)
        out = base_a * (1 - garment_w[..., None]) + mapped * garment_w[..., None]
        save(out, f'pfem_{skin}_basecolor.png')
        report['skin_fits'][skin] = {'palette': pid, 'entries': count, 'matrix': M.round(4).tolist()}
    (OUT / 'compose_report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'skin_fits'}))


if __name__ == '__main__':
    main()
