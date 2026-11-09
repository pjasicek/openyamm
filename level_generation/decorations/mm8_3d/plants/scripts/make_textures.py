#!/usr/bin/env python3
"""Tiling textures for the plants (textures/<name>_basecolor.png, _normal.png), shared by every model that uses them:
  bark   Poly Haven bark_willow_02 (CC0, source/bark_willow_02/), luminance detail graded to a neutral warm grey-brown
         (hue and darkness come from COLOR_0 per model: shrub trunks, plant10, stumps), 1024².
Usage: make_textures.py bark"""
import os, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX = os.path.join(HERE, 'textures')
SRC = os.path.join(HERE, 'source')


def lin(x):
    return np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4)


def srgb(x):
    x = np.clip(x, 0, 1)
    return np.where(x <= 0.0031308, x * 12.92, 1.055 * x ** (1 / 2.4) - 0.055)


def load(path, channels=3):
    a = np.asarray(Image.open(path)).astype(np.float32)
    a = a / (65535.0 if a.max() > 255 else 255.0)
    if a.ndim == 2:
        a = a[..., None]
    return a[..., :channels]


def bark(size=1024, target=(150, 128, 100), contrast=1.6):
    base = os.path.join(SRC, 'bark_willow_02', 'bark_willow_02_')
    diff = lin(load(base + 'diff_2k.png'))
    ao = load(base + 'ao_2k.png', 1)[..., 0]
    lum = diff @ np.array([0.2126, 0.7152, 0.0722])
    lum = lum * ao ** 1.2
    lum = (lum / lum.mean()) ** contrast
    col = lum[..., None] * lin(np.array(target) / 255.0)[None, None]
    # slight hue variation from the source (greyish lichen vs brown), kept small
    chroma = diff / np.maximum(diff.mean(-1, keepdims=True), 1e-4)
    col = col * (1 + 0.35 * (chroma - 1))
    Image.fromarray((srgb(col) * 255 + 0.5).astype(np.uint8)).resize((size, size), Image.LANCZOS).save(
        os.path.join(TEX, 'bark_basecolor.png'), optimize=True)
    Image.open(base + 'nor_gl_2k.png').convert('RGB').resize((size // 2, size // 2), Image.LANCZOS).save(
        os.path.join(TEX, 'bark_normal.png'), optimize=True)
    print('TEXTURE bark mean sRGB', (srgb(col.reshape(-1, 3).mean(0)) * 255).round())


def cactus_skin(name, flank, crest, valley, areole, spine, spine_n=5, spine_len=0.32, per_tile=4, bumps=0.0,
                seed=1, w=256, h=512):
    """One rib across u (valleys at u = 0 and 1, crest at 0.5), per_tile areoles along v on the crest, each with
    spine_n spines; tiles in u and v. Height drives the normal map (crest ridge, areole bumps)."""
    import math
    from scipy import ndimage
    rng = np.random.default_rng(seed)
    S = 2
    W, H = w * S, h * S
    y, x = np.mgrid[0:H, 0:W]
    u = (x + 0.5) / W; v = (y + 0.5) / H
    c = np.abs(u - 0.5) * 2                        # 0 crest .. 1 valley
    noise = ndimage.gaussian_filter(rng.normal(0, 1, (H, W)), 10, mode='wrap'); noise /= noise.std()
    fine = ndimage.gaussian_filter(rng.normal(0, 1, (H, W)), 1.5, mode='wrap'); fine /= fine.std()
    flank, crest, valley = [lin(np.array(q) / 255.0) for q in (flank, crest, valley)]
    t = c[..., None]
    col = np.where(t < 0.5, crest * (1 - t * 2) + flank * t * 2, flank * (2 - t * 2) + valley * (t * 2 - 1))
    col = col * (1 + 0.1 * noise[..., None] + 0.04 * fine[..., None])
    hgt = (1 - c ** 1.6) * 0.6 + 0.03 * fine
    if bumps:
        hgt += bumps * (0.5 + 0.5 * np.cos(2 * math.pi * v * per_tile * 2)) * (1 - c)
    ar, sp = lin(np.array(areole) / 255.0), lin(np.array(spine) / 255.0)
    for k in range(per_tile):
        cy = (k + 0.5) / per_tile + rng.normal(0, 0.01)
        for dy in (-1, 0, 1):                       # wrap in v
            d = np.hypot((u - 0.5) * W, (v - cy - dy) * H)
            m = d < 0.055 * W
            col[m] = ar * (1 + 0.15 * fine[m, None])
            hgt[m] += 0.25
            for j in range(spine_n):
                a = 2 * math.pi * j / spine_n + rng.normal(0, 0.3)
                L = spine_len * W * rng.uniform(0.6, 1.1)
                px, py = 0.5 * W, (cy + dy) * H
                dx, dyy = x + 0.5 - px, y + 0.5 - py
                along = dx * math.cos(a) + dyy * math.sin(a)
                across = -dx * math.sin(a) + dyy * math.cos(a)
                sm = (along > 0) & (along < L) & (np.abs(across) < 1.6 * (1 - along / L) + 0.4)
                col[sm] = sp * (1.2 - 0.5 * (along[sm] / L))[:, None]
                hgt[sm] += 0.3
    col = np.clip(col, 0, 1)
    img = Image.fromarray((srgb(col) * 255 + 0.5).astype(np.uint8)).resize((w, h), Image.LANCZOS)
    img.save(os.path.join(TEX, f'{name}_basecolor.png'), optimize=True)
    gy, gx = np.gradient(ndimage.gaussian_filter(hgt, 1.0))
    n = np.stack([-gx * 6, gy * 6, np.ones_like(gx)], -1); n /= np.linalg.norm(n, axis=-1, keepdims=True)
    Image.fromarray(((n * 0.5 + 0.5) * 255 + 0.5).astype(np.uint8)).resize((w // 2, h // 2), Image.LANCZOS).save(
        os.path.join(TEX, f'{name}_normal.png'), optimize=True)
    print('TEXTURE', name, 'mean sRGB', (srgb(col.reshape(-1, 3).mean(0)) * 255).round())


def wood(size=512, seed=7):
    """Pale splintered wood (broken stump tops): vertical fibres, cracks and darker grooves; tiles in u and v."""
    from scipy import ndimage
    rng = np.random.default_rng(seed)
    S = 2
    n = size * S
    fib = ndimage.gaussian_filter(rng.normal(0, 1, (n, n)), (40, 1.2), mode='wrap'); fib /= fib.std()
    big = ndimage.gaussian_filter(rng.normal(0, 1, (n, n)), (60, 12), mode='wrap'); big /= big.std()
    crack = ndimage.gaussian_filter(rng.normal(0, 1, (n, n)), (80, 2.5), mode='wrap'); crack /= crack.std()
    v = 0.62 + 0.12 * fib + 0.1 * big
    v -= 0.4 * np.clip((crack - 1.6) / 0.6, 0, 1)
    base = lin(np.array([226, 205, 160]) / 255.0)
    col = np.clip(v, 0.05, 1.2)[..., None] * base / 0.62 * (1 + 0.05 * big[..., None] * np.array([1, 0.6, 0.2]))
    Image.fromarray((srgb(col) * 255 + 0.5).astype(np.uint8)).resize((size, size), Image.LANCZOS).save(
        os.path.join(TEX, 'wood_basecolor.png'), optimize=True)
    hgt = 0.6 * fib - 1.5 * np.clip((crack - 1.6) / 0.6, 0, 1)
    gy, gx = np.gradient(ndimage.gaussian_filter(hgt, 1.0))
    nn = np.stack([-gx * 3, gy * 3, np.ones_like(gx)], -1); nn /= np.linalg.norm(nn, axis=-1, keepdims=True)
    Image.fromarray(((nn * 0.5 + 0.5) * 255 + 0.5).astype(np.uint8)).resize((size // 2, size // 2),
                                                                            Image.LANCZOS).save(
        os.path.join(TEX, 'wood_normal.png'), optimize=True)
    print('TEXTURE wood mean sRGB', (srgb(col.reshape(-1, 3).mean(0)) * 255).round())


def cactus():
    # plant50/51: pale blue-green segments, few long dark spines; plant52/53: deep green saguaro, brown areoles;
    # plant54: olive-yellow columns, dense pale spines
    cactus_skin('cactus_green', (150, 185, 120), (190, 215, 160), (95, 130, 70), (90, 60, 30), (50, 30, 15),
                spine_n=4, spine_len=0.42, per_tile=2, seed=51)
    cactus_skin('cactus_saguaro', (95, 125, 25), (140, 160, 45), (50, 55, 8), (120, 80, 35), (200, 180, 80),
                spine_n=6, spine_len=0.22, per_tile=5, seed=52)
    cactus_skin('cactus_yellow', (165, 150, 70), (200, 190, 110), (90, 80, 25), (220, 210, 150), (235, 225, 160),
                spine_n=9, spine_len=0.3, per_tile=6, seed=54)


if __name__ == '__main__':
    os.makedirs(TEX, exist_ok=True)
    {'bark': bark, 'cactus': cactus, 'wood': wood}[sys.argv[1]]()
