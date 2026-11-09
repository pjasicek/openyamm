"""Hydra palette displacement: preserve five distinct native head colors and shared body.

One enhanced-art coverage mask protects neutral highlights. A smooth RGB lookup stores
the native palette displacement, rather than collapsing different hues to one luminance ramp.
"""
import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.spatial import cKDTree

GRID = 33


def coverage(image):
    a = np.array(image)
    c = a[:, :, :3].astype(float) / 255
    chroma = c.max(2) - c.min(2)
    neutral_highlight = np.clip((c.min(2)-.55)/.25, 0, 1) * np.clip((.12-chroma)/.08, 0, 1)
    weight = 1-neutral_highlight
    weight[a[:, :, 3] == 0] = 0
    return Image.fromarray(np.round(weight*255).astype(np.uint8), 'L')


def fit(config, inv, repo):
    colors = {int(p): np.fromfile(repo/path, np.uint8)[:768].reshape(256, 3)/255
              for p, path in inv['palette_paths'].items()}
    counts = np.zeros(256)
    for src in inv['sources'].values():
        counts += np.bincount(np.array(Image.open(repo/src['path'])).ravel(), minlength=256)
    counts[0] = 0
    used = counts > 0
    base = colors[754][used]
    points = np.stack(np.meshgrid(*([np.linspace(0, 1, GRID)]*3), indexing='ij'), -1).reshape(-1, 3)
    distance, indices = cKDTree(base).query(points, k=8)
    weights = np.exp(-(distance**2-distance[:, :1]**2)/.0015)
    weights /= weights.sum(1, keepdims=True)
    luma = np.array([.2126, .7152, .0722])
    base_mean = (base[indices]*weights[:, :, None]).sum(1)
    brightness = (points@luma)/np.maximum(base_mean@luma, .01)
    result = {}
    for palette in [755, 756]:
        target = (colors[palette][used][indices]*weights[:, :, None]).sum(1)
        target *= brightness[:, None]
        lut = (target-points).reshape(GRID, GRID, GRID, 3)
        result[palette] = np.round(lut, 6).tolist()
    return result


def recolor(image, mask, palette, config, vectors):
    if palette == 754:
        return image.copy()
    a = np.array(image)
    c = a[:, :, :3].astype(float)/255
    coordinates = np.moveaxis(c*(GRID-1), -1, 0)
    lut = np.array(vectors[palette])
    delta = np.stack([ndimage.map_coordinates(lut[:, :, :, k], coordinates, order=1, mode='nearest')
                      for k in range(3)], -1)
    weight = np.array(mask).astype(float)/255
    a[:, :, :3] = np.round(np.clip(c+delta*weight[:, :, None], 0, 1)*255).astype(np.uint8)
    return Image.fromarray(a)
