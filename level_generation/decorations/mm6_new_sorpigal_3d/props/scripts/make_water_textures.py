#!/usr/bin/env python3
"""Fountain water texture (props/textures_water/stream_*), sta1a revision 4 (2026-10-09). Tileable; maps:
stream_basecolor.png (sRGB RGBA, alpha = coverage of the blended water), stream_normal.png (OpenGL tangent space),
stream_mr.png (glTF metallic-roughness: G = roughness, B = metal).
Falling, aerated water from FFT-filtered noise, rows = v along the stream (which the engine scrolls), columns = u
around it (the flattened tube's edges at u = 0 and 0.5):
 - colour: the native strands' blue body (fount1-3 stream pixels, sRGB 25-75 %: 58/79/119 to 102/127/190, median
   79/101/154) with near-white aerated streaks and stretched bubbles (the strands' highlights, 149/182/239 and up);
   revision 3's transparent dark teal read as glass in game;
 - alpha: 0.86-1.0 over the stream, about 10 % thinner at the edges (u = 0, 0.5);
 - normal: the streaks' relief mixed with OpenMW's water_nm.png (assets_dev/engine/rendering/water/, GPL-3.0 like
   this repository, see its source.yml), tiled 2 around and once along, so the shimmer is stretched by the fall;
 - roughness 0.3: a moderate wet sheen, neither glass nor plastic.
Usage: make_water_textures.py"""
import os
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
OUT = os.path.join(HERE, 'textures_water')
WATER_NM = os.path.join(REPO, 'assets_dev', 'engine', 'rendering', 'water', 'water_nm.png')
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(6612)


def lin(srgb):
    srgb = np.asarray(srgb, np.float64)
    return np.where(srgb <= 0.04045, srgb / 12.92, ((srgb + 0.055) / 1.055) ** 2.4)


def srgb(linear):
    linear = np.clip(linear, 0, 1)
    return np.where(linear <= 0.0031308, linear * 12.92, 1.055 * linear ** (1 / 2.4) - 0.055)


def noise(shape, beta, scale=(1.0, 1.0)):
    """Periodic fractal noise in [0, 1]; scale stretches the frequencies per axis (rows, columns)."""
    field = rng.normal(size=shape)
    fy, fx = np.meshgrid(np.fft.fftfreq(shape[0]) * scale[0], np.fft.fftfreq(shape[1]) * scale[1], indexing='ij')
    radius = np.sqrt(fy * fy + fx * fx); radius[0, 0] = 1.0
    spectrum = np.fft.fft2(field) / radius ** beta; spectrum[0, 0] = 0.0
    values = np.real(np.fft.ifft2(spectrum))
    return (values - values.min()) / (values.max() - values.min())


def normal_map(height, strength):
    dx = (np.roll(height, -1, 1) - np.roll(height, 1, 1)) * 0.5 * strength
    dy = (np.roll(height, -1, 0) - np.roll(height, 1, 0)) * 0.5 * strength
    n = np.stack([-dx, dy, np.ones_like(height)], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    return n * 0.5 + 0.5


def save(name, colour_linear, alpha, normal, roughness):
    rgba = np.dstack([srgb(colour_linear), np.clip(alpha, 0, 1)])
    Image.fromarray((rgba * 255 + 0.5).astype(np.uint8), 'RGBA').save(os.path.join(OUT, f'{name}_basecolor.png'))
    Image.fromarray((np.clip(normal, 0, 1) * 255 + 0.5).astype(np.uint8), 'RGB').save(
        os.path.join(OUT, f'{name}_normal.png'))
    shape = colour_linear.shape[:2]
    mr = np.dstack([np.zeros(shape), np.full(shape, roughness), np.zeros(shape)])
    Image.fromarray((mr * 255 + 0.5).astype(np.uint8), 'RGB').save(os.path.join(OUT, f'{name}_mr.png'))
    mean = (srgb(colour_linear).reshape(-1, 3).mean(0) * 255).round(1)
    print('TEXTURE', name, shape, 'mean sRGB', mean, 'mean alpha', round(float(np.mean(alpha)), 3))


# ---------------------------------------------------------------- stream (rows = v along the stream, columns = u around)
S = 512
# rows are v: streaks along v need little energy at row frequencies, so those are scaled up (weakened)
streak = noise((S, S), 1.25, (8.0, 1.0)) ** 1.2
fine = noise((S, S), 1.0, (4.0, 1.0))
core = np.clip((noise((S, S), 1.05, (10.0, 1.0)) - 0.6) * 5.0, 0, 1)             # narrow aerated white streaks
flecks = np.clip((noise((S, S), 0.9, (3.0, 1.0)) - 0.8) * 6.0, 0, 1)              # bubbles, stretched by the fall
body = 0.7 * streak + 0.3 * fine
low, high = np.percentile(body, [2, 98])
body = np.clip((body - low) / (high - low), 0, 1)
white = np.clip(core + 0.7 * flecks, 0, 1)
dark, blue, light, foam = (lin(np.array(c) / 255) for c in ([46, 64, 104], [78, 101, 158], [140, 172, 230],
                                                             [222, 234, 250]))
b3 = body[..., None]
colour = np.where(b3 < 0.6, dark + (blue - dark) * (b3 / 0.6), blue + (light - blue) * ((b3 - 0.6) / 0.4))
colour = colour + (foam - colour) * white[..., None]
edge = np.abs(np.sin(2 * np.pi * np.arange(S) / S))[None, :]          # 0 at the tube's two edges
alpha = np.clip((0.86 + 0.08 * body + 0.1 * white) * (0.9 + 0.1 * edge), 0, 1)
nm = np.asarray(Image.open(WATER_NM).convert('RGB')) / 255.0 * 2 - 1
nm = np.tile(nm, (1, 2, 1))                                      # 128 x 256: two ripple cells around, one along
nm = np.stack([np.asarray(Image.fromarray(nm[..., c].astype(np.float32), 'F').resize((S, S), Image.BILINEAR))
               for c in range(3)], -1)
streak_n = normal_map(0.7 * streak + 0.3 * fine + 0.4 * white, 14.0) * 2 - 1
mixed = streak_n + nm * np.array([1.0, 1.0, 0.0])
mixed /= np.linalg.norm(mixed, axis=-1, keepdims=True)
save('stream', colour, alpha, mixed * 0.5 + 0.5, 0.3)
