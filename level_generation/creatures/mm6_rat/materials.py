"""Enhanced rat fur/skin and iris coverage, with fixed native palette ramps."""
import numpy as np
from scipy import ndimage
from PIL import Image

REGIONS = {'mask_r': 'Native fur and bare skin/tail', 'mask_g': 'Amber eye iris',
           'mask_b': 'Unused', 'mask_a': 'Unused; not sprite alpha'}
LUMA = np.array([.2126, .7152, .0722])


def coverage(image):
    a = np.array(image); rgb = a[:, :, :3].astype(float) / 255
    r, g, b = rgb.transpose(2, 0, 1)
    hsv = np.array(image.convert('RGB').convert('HSV')).astype(float)
    hue = hsv[:, :, 0] * 360 / 255; sat = hsv[:, :, 1] / 255
    eye = np.clip((sat - .55) / .15, 0, 1) * np.clip((hue - 10) / 8, 0, 1) * np.clip((52 - hue) / 12, 0, 1)
    eye *= np.clip((r - .12) / .08, 0, 1)
    # Fur/skin occupy coherent dark masses; neutral bright teeth, metal and eye rims do not.
    bright = np.clip((np.max(rgb, axis=2) - .28) / .12, 0, 1)
    neutral = np.clip((.58 - sat) / .15, 0, 1)
    protected = bright * neutral
    body = (1 - protected) * (1 - eye)
    weights = np.stack([body, eye, body * 0, body * 0], axis=2)
    weights[a[:, :, 3] == 0] = 0
    return Image.fromarray(np.floor(weights * 255).astype(np.uint8), 'RGBA')


def fit(config, inv, repo):
    colors = {int(p): np.fromfile(repo / f'assets_dev/worlds/mm6/textures/pal{p}.act', np.uint8)
              [:768].reshape(256, 3) / 255 for p in inv['variants']}
    counts = np.zeros(256)
    for name, source in inv['sources'].items():
        if source['referenced']:
            counts += np.bincount(np.array(Image.open(repo / f'assets_dev/engine/sprites/{name}.bmp'))
                                  .ravel(), minlength=256)
    base = colors[808]; r, g, b = base.T
    ids = np.arange(256)
    cape = (ids >= 55)
    tabard = (ids > 0) & (ids < 55) & (r > g * 1.25) & (g > b * 1.2)
    y = base @ LUMA
    curves = {}
    for palette in (807, 809):
        regions = []
        for selected in (cape, tabard):
            valid = selected & (counts > 0)
            samples = y[valid] * 255
            curve = []
            for level in range(256):
                distance = (samples - level) ** 2
                weight = counts[valid] * np.exp(-(distance - distance.min()) / 32)
                curve.append((weight @ colors[palette][valid] / weight.sum()).tolist())
            regions.append(curve)
        curves[palette] = regions + [np.zeros((256, 3)).tolist()] * 2
    return curves


def recolor(image, mask, palette, config, vectors):
    if palette == config['base_palette']:
        return image.copy()
    a = np.array(image); rgb = a[:, :, :3].astype(float) / 255
    w = np.array(mask).astype(float) / 255
    level = np.clip(np.round((rgb @ LUMA) * 255), 0, 255).astype(int)
    output = rgb * (1 - w.sum(axis=2, keepdims=True))
    for region in range(4):
        output += w[:, :, region, None] * np.array(vectors[palette][region])[level]
    a[:, :, :3] = np.round(np.clip(output, 0, 1) * 255).astype(np.uint8)
    return Image.fromarray(a)
