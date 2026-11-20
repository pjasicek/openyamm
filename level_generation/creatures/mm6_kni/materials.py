"""Enhanced blue-violet accent coverage and native neutral/accent palette curves."""
import numpy as np
from PIL import Image

REGIONS = {'mask_r': 'Blue-violet armor accents', 'mask_g': 'Neutral armor, blade and mane tonal variants',
           'mask_b': 'Unused', 'mask_a': 'Unused; not sprite alpha'}
LUMA = np.array([.2126, .7152, .0722])


def coverage(image):
    a = np.array(image)
    rgb = a[:, :, :3].astype(float) / 255
    red, green, blue = rgb.transpose(2, 0, 1)
    violet = np.clip((blue - green - .008) / .025, 0, 1)
    violet *= np.clip(((blue - green) / np.maximum(blue, .01) - .045) / .13, 0, 1)
    # Warm brown grip and small gold fittings remain unchanged.
    warm = np.clip(((red - blue) / np.maximum(red, .01) - .20) / .20, 0, 1)
    neutral = (1 - violet) * (1 - warm)
    out = np.zeros((*red.shape, 4), np.uint8)
    out[:, :, 0] = np.floor(violet * 255)
    out[:, :, 1] = np.floor(neutral * 255)
    out[a[:, :, 3] == 0] = 0
    return Image.fromarray(out, 'RGBA')


def fit(config, inv, repo):
    colors = {int(p): np.fromfile(repo / f'assets_dev/worlds/mm6/textures/pal{p}.act', np.uint8)
              [:768].reshape(256, 3) / 255 for p in inv['variants']}
    counts = np.zeros(256)
    for name in inv['sources']:
        counts += np.bincount(np.array(Image.open(repo / f'assets_dev/engine/sprites/{name}.bmp'))
                              .ravel(), minlength=256)
    ids = np.arange(256)
    accent = (ids >= 87) & (ids <= 198)
    neutral = (ids > 0) & ((ids <= 75) | (ids >= 199))
    y = colors[760] @ LUMA
    curves = {}
    for palette in (761, 762):
        regions = []
        for selected in (accent, neutral):
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
    a = np.array(image)
    rgb = a[:, :, :3].astype(float) / 255
    weights = np.array(mask).astype(float) / 255
    level = np.clip(np.round((rgb @ LUMA) * 255), 0, 255).astype(int)
    output = rgb * (1 - weights.sum(axis=2, keepdims=True))
    for region in range(4):
        output += weights[:, :, region, None] * np.array(vectors[palette][region])[level]
    a[:, :, :3] = np.round(np.clip(output, 0, 1) * 255).astype(np.uint8)
    return Image.fromarray(a)
