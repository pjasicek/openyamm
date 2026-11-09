#!/usr/bin/env python3
"""Texture sets of the dungeon wall torches from the CC0 Poly Haven maps in source/ (fetch.py). Each set is written
as textures/<set>_{basecolor,normal,mr}.png at SIZE (base colour sRGB, OpenGL normal, glTF metallic-roughness: G
roughness, B metal), tileable, and shared by every torch model that uses it (the engine shares GPU textures between
models whose embedded PNG bytes are equal, and the glTF exporter embeds these files unchanged).

- torchwood (rough_wood): a weathered stick, graded to a neutral warm brown above every native wood tone so the
  per-model COLOR_0 tint (a normalised vertex colour, at most one) only darkens it (6torch01, torchnf, torch01 stick and holder).
- torchrag (hessian_380 with procedural tar blotches): a burlap rag wound round the torch head in four slanted
  layers, soaked with glossy tar (6torch01 and torchnf heads, the torch01 wrap).
- rustiron (rust_coarse_01, bare forged-iron patches from rusty_metal_04): the 6torch01 ring clamp, arm and plate.
- darkiron (rusty_metal_04): dark blue-grey forged iron, glossy, with the native sprite's copper-brown streaks
  where the source is rusted (trchb00 / nwtrchnf).
Usage: python3 -I make_textures.py"""
import os

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = os.path.join(HERE, 'source')
OUT = os.path.join(HERE, 'textures')
SIZE = 512


def load(asset, kind):
    """A 1k source map as float32 0..1 (RGB, or one channel for the grey maps)."""
    image = Image.open(os.path.join(SOURCE, asset, f'{asset}_{kind}_1k.png'))
    a = np.asarray(image).astype(np.float32)
    a /= 65535.0 if image.mode.startswith('I') else 255.0
    if a.ndim == 3:
        return a[..., :3] if kind in ('diff', 'nor_gl') else a[..., 0]
    return a


def to_linear(c):
    c = np.clip(c, 0.0, None)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def to_srgb(c):
    c = np.clip(c, 0.0, 1.0)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


def lin(rgb):
    return to_linear(np.asarray(rgb, np.float32) / 255.0)


def luminance(rgb_linear):
    return rgb_linear @ np.array([0.2126, 0.7152, 0.0722], np.float32)


def blur(a, radius):
    """Wrapping (FFT) gaussian blur of a tileable one-channel map; radius is the sigma in pixels."""
    fy = np.fft.fftfreq(a.shape[0])[:, None]
    fx = np.fft.fftfreq(a.shape[1])[None, :]
    kernel = np.exp(-2 * (np.pi * radius) ** 2 * (fx * fx + fy * fy))
    return np.real(np.fft.ifft2(np.fft.fft2(a) * kernel)).astype(np.float32)


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def resize(a, size):
    """Wrapping resize of a tileable map (float, any channels) so its edges still meet."""
    n = a.shape[0]
    channels = [a] if a.ndim == 2 else [a[..., k] for k in range(a.shape[2])]
    out = []
    for c in channels:
        tiled = Image.fromarray(np.tile(c, (3, 3)).astype(np.float32), 'F')
        big = np.asarray(tiled.resize((3 * size, 3 * size), Image.LANCZOS))
        out.append(big[size:2 * size, size:2 * size])
    return out[0] if a.ndim == 2 else np.stack(out, -1)


def normal_from_height(h, strength):
    """OpenGL tangent-space normal (0..1 encoded) of a tileable height map (pixel units times strength)."""
    dx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * 0.5 * strength
    dy = (np.roll(h, 1, 0) - np.roll(h, -1, 0)) * 0.5 * strength        # image rows run down, +y is up
    n = np.stack([-dx, -dy, np.ones_like(h)], -1)
    return n / np.linalg.norm(n, axis=-1, keepdims=True)


def decode_normal(encoded):
    n = encoded * 2 - 1
    return n / np.linalg.norm(n, axis=-1, keepdims=True)


def combine_normals(a, b):
    """Whiteout blend of two decoded tangent-space normals."""
    n = np.stack([a[..., 0] + b[..., 0], a[..., 1] + b[..., 1], a[..., 2] * b[..., 2]], -1)
    return n / np.linalg.norm(n, axis=-1, keepdims=True)


def save(name, base_linear, normal, rough, metal):
    os.makedirs(OUT, exist_ok=True)
    base = resize(to_srgb(base_linear), SIZE)
    Image.fromarray((np.clip(base, 0, 1) * 255 + 0.5).astype(np.uint8), 'RGB').save(
        os.path.join(OUT, f'{name}_basecolor.png'), optimize=True)
    n = resize(normal, SIZE)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    Image.fromarray((np.clip(n * 0.5 + 0.5, 0, 1) * 255 + 0.5).astype(np.uint8), 'RGB').save(
        os.path.join(OUT, f'{name}_normal.png'), optimize=True)
    mr = np.stack([np.zeros_like(rough), rough, metal], -1)
    mr = resize(mr, SIZE)
    Image.fromarray((np.clip(mr, 0, 1) * 255 + 0.5).astype(np.uint8), 'RGB').save(
        os.path.join(OUT, f'{name}_mr.png'), optimize=True)
    mean = to_srgb(luminance(to_linear(base)).mean()) * 255
    print('TEXTURE', name, 'mean sRGB', tuple(int(v) for v in (to_srgb(to_linear(base).reshape(-1, 3).mean(0)) * 255)),
          'grey', int(mean), 'roughness', round(float(rough.mean()), 2), 'metal', round(float(metal.mean()), 2))


def torchwood():
    diff = to_linear(load('rough_wood', 'diff'))
    ao = load('rough_wood', 'ao')
    rel = luminance(diff) * (0.55 + 0.45 * ao)
    rel = rel / rel.mean()
    base = lin((150, 100, 64))[None, None, :] * (rel ** 1.25)[..., None]
    # Keep a little of the source's own colour variation (grey weathering, darker cracks).
    chroma = diff / np.maximum(luminance(diff)[..., None], 1e-4)
    base *= 0.85 + 0.15 * chroma
    rough = np.clip(load('rough_wood', 'rough') * 0.45 + 0.55, 0, 1)            # dry, weathered: no sheen
    save('torchwood', base, decode_normal(load('rough_wood', 'nor_gl')), rough, np.zeros_like(rough))


def torchrag():
    n = 1024
    diff = to_linear(load('hessian_380', 'diff'))
    weave = luminance(diff) / luminance(diff).mean()
    # Four rag layers wound slantwise (integer frequencies keep the tile seamless): each layer's lower edge laps
    # over the next one, so the height is a sawtooth with a dark, shadowed seam under each overlap.
    y, x = np.mgrid[0:n, 0:n].astype(np.float32) / n
    phase = (4 * (1 - y) + 1 * x) % 1.0
    wobble = blur(np.random.default_rng(3).normal(size=(n, n)).astype(np.float32), 18) * 9
    phase = (phase + wobble * 0.05) % 1.0
    layer = np.sqrt(phase)                                     # height rises from the seam to the next lap
    seam = smoothstep(0.0, 0.08, phase) * (0.4 + 0.6 * smoothstep(0.0, 0.25, phase))
    # Tar: blotches of tileable fractal noise over about two thirds of the rag; each layer a little different.
    rng = np.random.default_rng(11)
    tar = sum(weight * blur(rng.normal(size=(n, n)).astype(np.float32), sigma) / blur(
        rng.normal(size=(n, n)).astype(np.float32), sigma).std() for weight, sigma in ((1.0, 16), (0.7, 7), (0.4, 3)))
    lap = np.floor(4 * (1 - y) + x + wobble * 0.05).astype(int) % 4
    tar += np.array([0.3, -0.2, 0.1, -0.1], np.float32)[lap]
    tar = smoothstep(np.percentile(tar, 5), np.percentile(tar, 40), tar)
    tar = np.clip(tar + 0.35 * smoothstep(0.85, 1.0, phase), 0, 1)          # tar collects at the laps
    cloth = lin((150, 115, 82))[None, None, :] * weave[..., None]
    pitch = lin((96, 72, 50))[None, None, :] * (0.8 + 0.2 * weave[..., None])
    base = (cloth * (1 - tar[..., None]) + pitch * tar[..., None]) * (0.25 + 0.75 * seam)[..., None]
    height = blur(layer * 6.0, 2.5) + weave * 0.6 - tar * 0.4
    normal = combine_normals(decode_normal(load('hessian_380', 'nor_gl')), normal_from_height(height, 1.2))
    rough = np.clip(0.92 - 0.5 * tar, 0, 1)
    save('torchrag', base, normal, rough, np.zeros_like(rough))


def rustiron():
    rust = to_linear(load('rust_coarse_01', 'diff'))
    ao = load('rust_coarse_01', 'ao')
    bare = smoothstep(0.35, 0.75, blur(load('rusty_metal_04', 'metal'), 2.5))
    grey = luminance(to_linear(load('rusty_metal_04', 'diff')))
    iron = lin((64, 56, 52))[None, None, :] * (grey / grey[bare > 0.5].mean())[..., None] ** 0.4
    base = (rust * (1 - bare[..., None]) + iron * bare[..., None]) * (0.6 + 0.4 * ao)[..., None]
    base *= 1.5                                                 # headroom: COLOR_0 (at most one) only darkens
    normal = combine_normals(decode_normal(load('rust_coarse_01', 'nor_gl')),
                             decode_normal(load('rusty_metal_04', 'nor_gl')))
    rough = np.clip(load('rust_coarse_01', 'rough') * (1 - bare) + 0.42 * bare, 0.05, 1)
    save('rustiron', base, normal, rough, 0.55 * bare)


def darkiron():
    diff = to_linear(load('rusty_metal_04', 'diff'))
    bare = smoothstep(0.3, 0.7, blur(load('rusty_metal_04', 'metal'), 1.5))
    rel = np.clip(luminance(diff) / luminance(diff).mean(), 0.15, 4.0)
    # The native iron (trchb00): smooth blue-grey at (56, 55, 68) median with soft copper-brown streaks along the
    # shaft; its white highlights come from the glossy surface, not from paint. So the source's bare/rust contrast is
    # flattened to a gentle mottle and the rust becomes a warm stain over the same dark iron.
    stain = (1 - bare) * smoothstep(0.2, 0.9, blur(1 - bare, 3))
    iron = lin((84, 84, 106))[None, None, :] * (rel ** 0.45)[..., None]
    copper = lin((104, 80, 70))[None, None, :] * (rel ** 0.45)[..., None]
    base = iron * (1 - 0.45 * stain[..., None]) + copper * 0.45 * stain[..., None]
    base *= 1.5                                                 # headroom: COLOR_0 (at most one) only darkens
    # Glossy: a low, dielectric-like roughness gives the sprite's white highlights without darkening the diffuse
    # colour the way a high metallic value would (the engine scales diffuse by one minus metallic).
    rough = np.clip(0.3 * bare + (0.36 + 0.2 * load('rusty_metal_04', 'rough')) * (1 - bare), 0.05, 1)
    save('darkiron', base, decode_normal(load('rusty_metal_04', 'nor_gl')), rough, 0.3 * bare + 0.15 * (1 - bare))


if __name__ == '__main__':
    torchwood()
    torchrag()
    rustiron()
    darkiron()
