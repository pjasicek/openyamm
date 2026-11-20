#!/usr/bin/env python3
"""Procedural textures for the leftover corpses (textures/), in the outdoor props' format (basecolor sRGB, OpenGL
normal, metallic-roughness): `rope` (three twisted strands running diagonally across u, so a tube with u around and
v along reads as laid rope; tileable). The noise helpers are reimplemented here (outdoor make_textures.py is read
only). Usage: make_textures.py"""
import os

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, 'textures')
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(4242)


def noise(shape, beta=2.0, scale=(1.0, 1.0)):
    field = rng.normal(size=shape)
    freqs = np.meshgrid(*[np.fft.fftfreq(n) * s for n, s in zip(shape, scale)], indexing='ij')
    radius = np.sqrt(sum(f * f for f in freqs)); radius[0, 0] = 1.0
    spectrum = np.fft.fftn(field) / radius ** beta; spectrum[0, 0] = 0.0
    values = np.real(np.fft.ifftn(spectrum))
    return (values - values.min()) / (values.max() - values.min())


def srgb(linear):
    linear = np.clip(linear, 0, 1)
    return np.where(linear <= 0.0031308, linear * 12.92, 1.055 * linear ** (1 / 2.4) - 0.055)


def save(name, colour_linear, height, strength, roughness, metal):
    Image.fromarray((srgb(colour_linear) * 255 + 0.5).astype(np.uint8)).save(os.path.join(OUT, f'{name}_basecolor.png'))
    dx = (np.roll(height, -1, 1) - np.roll(height, 1, 1)) * 0.5 * strength
    dy = (np.roll(height, -1, 0) - np.roll(height, 1, 0)) * 0.5 * strength
    n = np.stack([-dx, dy, np.ones_like(height)], -1); n /= np.linalg.norm(n, axis=-1, keepdims=True)
    Image.fromarray(((n * 0.5 + 0.5) * 255 + 0.5).astype(np.uint8)).save(os.path.join(OUT, f'{name}_normal.png'))
    mr = np.dstack([np.zeros(height.shape), np.full(height.shape, roughness), np.full(height.shape, metal)])
    Image.fromarray((mr * 255 + 0.5).astype(np.uint8)).save(os.path.join(OUT, f'{name}_mr.png'))
    print('TEXTURE', name, 'mean sRGB', (srgb(colour_linear).reshape(-1, 3).mean(0) * 255).round(1))


S = 256
y, x = np.mgrid[0:S, 0:S] / S                       # rows = v (along the rope), columns = u (around)
phase = (x * 3 + y * 3) % 1.0                        # three strands per turn, one turn per texture repeat
strand = np.sin(np.pi * phase) ** 0.6                # rounded strand profile, dark grooves between strands
fibre = noise((S, S), 1.4, (0.3, 6.0))               # fine fibres along each strand
rough = noise((S, S), 2.2)
height = 0.8 * strand + 0.15 * fibre + 0.05 * rough
dark, light = np.array([0.05, 0.028, 0.012]), np.array([0.30, 0.19, 0.085])
value = np.clip(0.15 + 0.85 * strand * (0.75 + 0.25 * fibre) * (0.85 + 0.3 * rough), 0, 1)[..., None]
save('rope', dark * (1 - value) + light * value, height, 8.0, 0.9, 0.0)
