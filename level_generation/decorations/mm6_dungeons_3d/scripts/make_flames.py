#!/usr/bin/env python3
"""Flame flipbook textures for every fire decoration, from the CC0 Unity Labs flipbooks in source/unity_labs_vfx/ (16 x
4 frames, seamless 64-frame loops). Each flame is recoloured toward the MM torch flame: its brightness picks a colour
from a ramp measured on the native torch frames (torch01-torch10, darkest to brightest), so the core stays near
white-yellow and the tongues turn orange. The faint smoke above the flame fades out with it, and the flame body's
alpha is strengthened (ALPHA_GAIN) so a blended card does not read as smoke. Writes textures/<name>_basecolor.png and
prints each sheet's flame extents per frame, as fractions of the frame (left, right, top, base), for placing the
cards.
Usage: make_flames.py"""
import json
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parents[1]
REPO = HERE.parents[2]
X2 = REPO / 'assets_dev/engine/decorations_x2'
SOURCE = HERE / 'source/unity_labs_vfx'
COLUMNS, ROWS = 16, 4
ALPHA_GAIN = 1.8
# name: (source sheet, brightness below which the flame fades out (smoke), brightness of full opacity)
FLAMES = {
    'flame02': ('flame02_16x4.png', 0.18, 0.42),
    'flame03': ('flame03_16x4.png', 0.18, 0.42),
}


def luminance(rgb):
    return rgb @ np.array([0.299, 0.587, 0.114]) / 255.0


def native_ramp(bins=32):
    """Mean native torch flame colour per brightness bin (sRGB 0..255), the empty bins filled from their neighbours."""
    files = {binding['name'].lower(): binding['file']
             for binding in json.loads((X2 / 'manifest.json').read_text())['bindings']}
    samples = []
    for index in range(1, 11):
        pixels = np.asarray(Image.open(X2 / files[f'torch{index:02d}']).convert('RGBA'), dtype=np.float64)
        flame = pixels[:104]                        # above the torch head
        rgba = flame.reshape(-1, 4)
        rgba = rgba[(rgba[:, 3] > 200) & (rgba[:, 0] > 120)]
        samples.append(rgba[:, :3])
    rgb = np.concatenate(samples)
    level = luminance(rgb)
    edges = np.linspace(level.min(), level.max(), bins + 1)
    ramp = np.zeros((bins, 3))
    filled = np.zeros(bins, dtype=bool)
    for k in range(bins):
        inside = (level >= edges[k]) & (level <= edges[k + 1])
        if inside.sum() >= 20:
            ramp[k] = rgb[inside].mean(axis=0)
            filled[k] = True
    known = np.nonzero(filled)[0]
    for channel in range(3):
        ramp[:, channel] = np.interp(np.arange(bins), known, ramp[known, channel])
    return ramp


def recolour(sheet, ramp, fade_low, fade_high):
    pixels = np.asarray(sheet.convert('RGBA'), dtype=np.float64)
    rgb, alpha = pixels[..., :3], pixels[..., 3] / 255.0
    level = luminance(rgb)
    # Brightness relative to the sheet's brightest flame picks the ramp colour; dim smoke fades out.
    relative = np.clip(level / max(np.percentile(level[alpha > 0.5], 99.5), 1e-3), 0.0, 1.0)
    index = np.clip((relative * (len(ramp) - 1)).round().astype(int), 0, len(ramp) - 1)
    keep = np.clip((relative - fade_low) / (fade_high - fade_low), 0.0, 1.0)
    out = np.zeros_like(pixels)
    out[..., :3] = ramp[index]
    # The renders' soft alpha reads as brown smoke over dark walls; a blended card needs a denser flame body.
    out[..., 3] = np.clip(alpha * ALPHA_GAIN, 0.0, 1.0) * keep * keep * (3.0 - 2.0 * keep) * 255.0
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), 'RGBA')


def extents(sheet):
    alpha = np.asarray(sheet)[..., 3]
    height, width = alpha.shape[0] // ROWS, alpha.shape[1] // COLUMNS
    boxes = []
    for frame in range(COLUMNS * ROWS):
        cell = alpha[(frame // COLUMNS) * height:(frame // COLUMNS + 1) * height,
                     (frame % COLUMNS) * width:(frame % COLUMNS + 1) * width] > 32
        ys, xs = np.nonzero(cell)
        boxes.append((xs.min() / width, (xs.max() + 1) / width, ys.min() / height, (ys.max() + 1) / height))
    return np.array(boxes)


def main():
    ramp = native_ramp()
    for name, (source, fade_low, fade_high) in FLAMES.items():
        sheet = recolour(Image.open(SOURCE / source), ramp, fade_low, fade_high)
        out = HERE / 'textures' / f'{name}_basecolor.png'
        sheet.save(out, optimize=True)
        boxes = extents(sheet)
        low, high = np.percentile(boxes, 10, axis=0), np.percentile(boxes, 90, axis=0)
        print(f'FLAME {name} {sheet.size} left {low[0]:.2f}-{high[0]:.2f} right {low[1]:.2f}-{high[1]:.2f} '
              f'top {low[2]:.2f}-{high[2]:.2f} base {low[3]:.2f}-{high[3]:.2f} -> {out.relative_to(REPO)}')


if __name__ == '__main__':
    main()
