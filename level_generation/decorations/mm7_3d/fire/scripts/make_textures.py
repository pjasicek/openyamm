#!/usr/bin/env python3
"""Texture sets of this batch into textures/<name>_{basecolor,normal,mr}.png (mr: G roughness, B metal) and their
linear means into textures/means.json (COLOR_0 tints: linear(native) / linear(texture mean)).

Scan-derived sets use the MM6 fire batch's derivation (../../../mm6_dungeons_3d/fire/scripts/pbr.py, imported read
only) on this batch's CC0 Poly Haven downloads (source/polyhaven/, fetch_textures.py):

| set | Poly Haven source | use |
|---|---|---|
| stone | rock_face_03 | beacon bowl and pedestal (dec60, dec62, dec63) |
| gold | european_walnut_veneer_05 (its fine linear streaks as brushed metal) | golden brazier, magic pedestal, buoy bell and cage |
| copper | european_walnut_veneer_05 | the buoy's dome |
| staves | wood_planks (turned 90 degrees: seams along v) | the buoy's barrel |
| bandiron | rusty_metal_04 | the buoy's dark corroded bands |
| rust | rusty_metal_05 | torch02 lantern |
| bark | bark_brown_02 | dec24x logs |
| ember_<colour> | rock_face_03 through a fire ramp (cracks glow) | beacon fire beds |

Procedural (this script, own work): endgrain (log ends), orb (magic orb swirls), grid (lantern cage, alpha cut-out),
halo (additive glow cards).
Usage: make_textures.py"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parents[1] / 'mm6_dungeons_3d' / 'fire' / 'scripts'))
import pbr  # noqa: E402

pbr.SOURCE = HERE / 'source' / 'polyhaven'
OUT = HERE / 'textures'

EMBER = {
    'orange': [(0.0, (60, 12, 4)), (0.35, (160, 50, 12)), (0.65, (225, 105, 28)), (0.9, (250, 170, 60)),
               (1.0, (255, 215, 120))],
    'blue': [(0.0, (4, 14, 40)), (0.35, (10, 60, 140)), (0.65, (30, 130, 215)), (0.9, (110, 190, 250)),
             (1.0, (190, 230, 255))],
    'white': [(0.0, (30, 30, 36)), (0.35, (110, 110, 120)), (0.65, (190, 190, 200)), (0.9, (235, 235, 245)),
              (1.0, (255, 255, 255))],
}

SETS = {
    # Pitted grey-brown stone, high contrast like the native bowl (dark pits, pale flakes).
    'stone': dict(asset='rock_face_03', saturation=0.25, hue=(96, 86, 80), mean=0.085, contrast=1.7,
                  rough=(0.5, 0.45), rough_range=(0.6, 0.95), metal=0.0, normal_strength=1.6, size=512),
    # Brushed gold (streaks along u: rings round a lathe).
    'gold': dict(asset='european_walnut_veneer_05', saturation=0.0, hue=(205, 152, 82), mean=0.30, contrast=2.2,
                 rough=(0.4, 0.2), rough_range=(0.25, 0.5), metal=0.55, normal_strength=1.0, size=512),
    'copper': dict(asset='european_walnut_veneer_05', saturation=0.0, hue=(215, 140, 110), mean=0.42, contrast=1.6,
                   rough=(0.3, 0.12), rough_range=(0.15, 0.35), metal=0.6, normal_strength=0.6, size=256),
    'staves': dict(asset='wood_planks', saturation=0.1, hue=(186, 116, 56), mean=0.24, contrast=1.3,
                   rough=(0.6, 0.3), rough_range=(0.45, 0.85), metal=0.0, normal_strength=1.4, size=512),
    'bandiron': dict(asset='rusty_metal_04', saturation=0.3, hue=(80, 52, 34), mean=0.035, contrast=2.0,
                     rough=(0.6, 0.3), rough_range=(0.4, 0.9), metal=0.3, normal_strength=2.5, size=256),
    'rust': dict(asset='rusty_metal_05', saturation=0.6, hue=(160, 62, 14), mean=0.10, contrast=1.6,
                 rough=(0.7, 0.2), rough_range=(0.4, 0.9), metal=0.2, normal_strength=2.0, size=512),
    'bark': dict(asset='bark_brown_02', saturation=0.08, hue=(100, 74, 52), mean=0.08, contrast=1.5,
                 rough=(0.4, 0.55), rough_range=(0.6, 0.98), metal=0.0, normal_strength=1.5, size=512),
}
for colour, ramp in EMBER.items():
    SETS[f'ember_{colour}'] = dict(asset='rock_face_03', ramp=ramp, invert=True, rough=(0.3, 0.6),
                                   rough_range=(0.6, 0.95), metal=0.0, normal_strength=1.4, size=256)


def derive(name, asset, size=512, saturation=0.0, hue=None, mean=0.2, contrast=1.0, ramp=None, invert=False,
           normal_strength=1.0, rough=(1.0, 0.0), rough_range=(0.25, 1.0), metal=0.0, mr_size=256):
    """pbr.derive with a hue-preserving grade: the scan's luminance (contrast as a power about its mean) times the
    target colour's linear chroma, plus a little of the scan's own chroma (saturation); mean = the set's linear
    luminance. Ramps (embers) go through pbr.base_colour unchanged."""
    if ramp is not None:
        colour = pbr.base_colour(asset, size, 0.0, None, mean, 1.0, ramp, invert)
    else:
        lin = pbr.linear(pbr.load(asset, 'diff', size))
        lum = lin @ pbr.LUMA
        m = float(lum.mean())
        detail = (np.maximum(lum, 1e-6) / m) ** contrast
        target = pbr.linear(hue)
        target = target / float(target @ pbr.LUMA)
        chroma = (lin - lum[..., None]) / m * saturation
        colour = np.clip((target[None, None] * detail[..., None] + chroma) * mean, 0, 1)
    normal = pbr.normal_map(asset, size, normal_strength)
    r = pbr.roughness(asset, size, rough[0], rough[1], *rough_range)
    pbr.save_set(OUT, name, colour, normal, r, metal, mr_size)
    return [round(float(v), 5) for v in colour.reshape(-1, 3).mean(0)]


def rotate_set(name):
    """Turn a saved set 90 degrees (wood_planks' horizontal seams to vertical staves); the normal map's x and y turn
    with the image."""
    for kind in ('basecolor', 'normal', 'mr'):
        path = OUT / f'{name}_{kind}.png'
        a = np.asarray(Image.open(path)).copy()
        a = np.rot90(a, 1)
        if kind == 'normal':
            n = a.astype(np.float64) / 255 * 2 - 1
            n = np.dstack([-n[..., 1], n[..., 0], n[..., 2]])
            a = ((n * 0.5 + 0.5) * 255 + 0.5).astype(np.uint8)
        Image.fromarray(np.ascontiguousarray(a)).save(path, optimize=True)


def noise(size, scale, seed):
    """Tileable smooth noise (FFT-filtered), normalised to 0..1."""
    rng = np.random.default_rng(seed)
    f = np.fft.fft2(rng.normal(size=(size, size)))
    k = np.fft.fftfreq(size)[:, None] ** 2 + np.fft.fftfreq(size)[None, :] ** 2
    f *= np.exp(-k * (size / scale) ** 2)
    n = np.real(np.fft.ifft2(f))
    return (n - n.min()) / (n.max() - n.min())


def save(name, colour_srgb, normal=None, rough=0.5, metal=0.0, alpha=None):
    size = colour_srgb.shape[0]
    rgba = np.clip(colour_srgb, 0, 255).astype(np.uint8)
    if alpha is not None:
        rgba = np.dstack([rgba, (np.clip(alpha, 0, 1) * 255).astype(np.uint8)])
    Image.fromarray(rgba).save(OUT / f'{name}_basecolor.png', optimize=True)
    if normal is None:
        normal = np.dstack([np.full((size, size), 0.5), np.full((size, size), 0.5), np.ones((size, size))])
    Image.fromarray((normal * 255 + 0.5).astype(np.uint8)).save(OUT / f'{name}_normal.png', optimize=True)
    r = rough if np.ndim(rough) else np.full((size, size), rough)
    mr = np.dstack([np.zeros((size, size)), r, np.full((size, size), metal)])
    Image.fromarray((mr * 255 + 0.5).astype(np.uint8)).save(OUT / f'{name}_mr.png', optimize=True)
    lin = pbr.linear(colour_srgb[..., :3])
    return [round(float(v), 5) for v in lin.reshape(-1, 3).mean(0)]


def height_normal(h, strength):
    gy, gx = np.gradient(h)
    n = np.dstack([-gx * strength, gy * strength, np.ones_like(h)])
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    return n * 0.5 + 0.5


def endgrain(size=256):
    """Log end: growth rings round an off-centre pith, radial cracks, a dark charred bark rim (u, v 0..1 over the
    disc; the builder maps the cap to the unit square)."""
    y, x = (np.mgrid[0:size, 0:size] + 0.5) / size
    wob = noise(size, 18, 3) - 0.5
    r = np.hypot(x - 0.52, y - 0.48) * 2 + wob * 0.08
    a = np.arctan2(y - 0.48, x - 0.52)
    rings = 0.5 + 0.5 * np.sin(r * 2 * np.pi * 9)
    crack = np.clip(1 - np.abs(np.sin(a * 3 + wob * 6)) * 12, 0, 1) * (r > 0.2) * (r < 0.85)
    base = np.array([168, 78, 44.0])
    dark = np.array([96, 40, 22.0])
    t = 0.55 + 0.25 * rings + 0.2 * (noise(size, 40, 4) - 0.5)
    col = dark + (base - dark) * t[..., None]
    col *= (1 - 0.6 * crack)[..., None]
    rim = np.clip((r - 0.86) / 0.06, 0, 1)
    col = col * (1 - rim[..., None]) + np.array([40, 26, 18.0]) * rim[..., None]
    h = rings * 0.3 - crack + noise(size, 30, 5) * 0.5
    return save('endgrain', col, height_normal(h, 6.0), rough=0.85, metal=0.0)


def orb(size=512):
    """Magic orb: pale clouded glass with curling darker swirls (domain-warped noise bands), tileable in u and v;
    the orb's colour comes from each variant's baseColorFactor. Glossy dielectric."""
    n1, n2 = noise(size, 12, 11), noise(size, 8, 12)
    y, x = np.mgrid[0:size, 0:size] / size
    warp = noise(size, 5, 13) * 6.0 + (n1 - 0.5) * 1.5
    bands = np.abs(np.sin(2 * np.pi * (x * 1 + y * 1 + warp * 0.5)))
    lines = np.clip(1 - bands * 5, 0, 1) * np.clip(n2 * 1.6 - 0.2, 0, 1)
    cloud = noise(size, 60, 14)
    lum = 0.88 + 0.12 * cloud - 0.6 * lines
    col = np.clip(lum, 0, 1)[..., None] * np.array([255.0, 255, 255])
    h = lines * 0.5 + cloud * 0.2
    return save('orb', col, height_normal(h, 3.0), rough=0.1, metal=0.0)


def grid(size=256):
    """Lantern cage: rusty iron bars (8 across, 5 rings over the texture) cut out of an alpha mask; the colour is the
    rust scan's (rusty_metal_05) graded like `rust`."""
    rust = np.asarray(Image.open(OUT / 'rust_basecolor.png').convert('RGB').resize((size, size))).astype(float)
    y, x = (np.mgrid[0:size, 0:size] + 0.5) / size
    def bars(t, count, width):
        f = (t * count) % 1.0
        return np.minimum(f, 1 - f) * 2 < width
    alpha = (bars(x, 8, 0.26) | bars(y, 5, 0.2) | (y < 0.03) | (y > 0.97)).astype(float)
    shade = 0.75 + 0.25 * noise(size, 20, 21)
    col = rust * shade[..., None]
    return save('grid', col, None, rough=0.7, metal=0.2, alpha=alpha)


def halo(size=128):
    """Soft glow for additive halo cards: white, alpha a smooth radial falloff (peak 1 at the centre, 0 at the
    edge); the card's colour and strength come from COLOR_0 or the material factor."""
    y, x = (np.mgrid[0:size, 0:size] + 0.5) / size * 2 - 1
    r = np.clip(np.hypot(x, y), 0, 1)
    alpha = np.exp(-4.0 * r * r) * (1 - r * r) ** 2
    return save('halo', np.full((size, size, 3), 255.0), None, rough=1.0, metal=0.0, alpha=alpha)


def main():
    OUT.mkdir(exist_ok=True)
    means = {}
    for name, spec in SETS.items():
        means[name] = derive(name, **spec)
        if name == 'staves':
            rotate_set(name)
        print('PBR', name, 'sRGB mean', [round(float(v) * 255) for v in pbr.srgb(np.array(means[name]))])
    means['endgrain'] = endgrain()
    means['orb'] = orb()
    means['grid'] = grid()
    means['halo'] = halo()
    (OUT / 'means.json').write_text(json.dumps(means, indent=1) + '\n')


if __name__ == '__main__':
    main()
