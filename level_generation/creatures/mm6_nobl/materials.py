"""Independent enhanced cape/tabard masks, with native fixed palette ramps."""
import numpy as np
from scipy import ndimage
from PIL import Image

REGIONS = {'mask_r': 'Blue cape and shoulder mantle', 'mask_g': 'Violet-blue tabard',
           'mask_b': 'Unused', 'mask_a': 'Unused; not sprite alpha'}
LUMA = np.array([.2126, .7152, .0722])


def coverage(image):
    a = np.array(image); rgb = a[:, :, :3].astype(float) / 255
    r, g, b = rgb.transpose(2, 0, 1)
    blue = np.clip((b - np.maximum(r, g) - .002) / .020, 0, 1)
    blue *= np.clip(((b - np.maximum(r, g)) / np.maximum(b, .01) - .03) / .12, 0, 1)
    smooth = ndimage.gaussian_filter(rgb, (2, 2, 0))
    sr, sg, sb = smooth.transpose(2, 0, 1)
    tabard = np.clip(((sr - sg) / np.maximum(sb, .01) + .20) / .10, 0, 1)
    weights = np.stack([blue * (1 - tabard), blue * tabard, blue * 0, blue * 0], axis=2)
    for channel in range(2):
        labels, _ = ndimage.label((weights[:, :, channel] > .6) & (a[:, :, 3] > 128))
        sizes = np.bincount(labels.ravel()); keep = sizes >= 160; keep[0] = False
        weights[:, :, channel] *= ndimage.binary_dilation(keep[labels], iterations=4)
    depth = ndimage.distance_transform_edt(a[:, :, 3] >= 250); core = depth > 3
    if core.any():
        distance, nearest = ndimage.distance_transform_edt(~core, return_indices=True)
        edge = (a[:, :, 3] > 0) & ~core & (distance <= 5)
        weights[edge] = weights[nearest[0], nearest[1]][edge]
    out = np.floor(np.clip(weights, 0, 1) * 255).astype(np.uint8); out[a[:, :, 3] == 0] = 0
    return Image.fromarray(out, 'RGBA')


def fit(config, inv, repo):
    colors = {int(p): np.fromfile(repo / f'assets_dev/worlds/mm6/textures/pal{p}.act', np.uint8)
              [:768].reshape(256, 3) / 255 for p in inv['variants']}
    counts = np.zeros(256)
    for name, source in inv['sources'].items():
        if source['referenced']:
            counts += np.bincount(np.array(Image.open(repo / f'assets_dev/engine/sprites/{name}.bmp'))
                                  .ravel(), minlength=256)
    base = colors[778]; r, g, b = base.T
    ids = np.arange(256)
    cape = (ids >= 126) & (ids <= 185) & (b > g) & (g > r)
    tabard = ids >= 220
    y = base @ LUMA
    curves = {}
    for palette in (777, 779):
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
