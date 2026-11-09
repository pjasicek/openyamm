"""Enhanced barbarian armor/leather masks with native palette ramps."""
import numpy as np
from scipy import ndimage
from PIL import Image

REGIONS = {'mask_r': 'Blue breastplate, scale panel, shoulder and knee armor', 'mask_g': 'Reddish leather gloves and boots',
           'mask_b': 'Unused', 'mask_a': 'Unused; not sprite alpha'}
LUMA = np.array([.2126, .7152, .0722])


def coverage(image):
    a = np.array(image); rgb = a[:, :, :3].astype(float) / 255
    r, g, b = rgb.transpose(2, 0, 1)
    armor = np.clip((b - r - .018) / .05, 0, 1) * np.clip((b - g - .008) / .035, 0, 1)
    leather = np.clip((r - g - .008) / .025, 0, 1) * np.clip((b / np.maximum(g, .01) - .83) / .12, 0, 1)
    leather *= np.clip((r / np.maximum(b, .01) - 1.05) / .25, 0, 1)
    weights = np.stack([armor, leather, armor * 0, armor * 0], axis=2)
    for ch in range(2):
        labels, _ = ndimage.label((weights[:, :, ch] > .5) & (a[:, :, 3] > 128))
        sizes = np.bincount(labels.ravel()); keep = sizes >= 60; keep[0] = False
        weights[:, :, ch] *= ndimage.binary_dilation(keep[labels], iterations=3)
    total = np.maximum(1, weights.sum(axis=2, keepdims=True)); weights /= total
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
    base = colors[664]; r, g, b = base.T
    ids = np.arange(256)
    cape = (ids >= 23) & (ids <= 82)
    tabard = (ids >= 90) & (ids <= 142)
    y = base @ LUMA
    curves = {}
    for palette in (663, 665):
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


def final_coverage(image, name):
    """Protect the reviewed enhanced blade footprint, never native pixel-mask scaling."""
    import json
    from pathlib import Path
    root = Path(__file__).resolve().parent
    axes = json.loads((root / 'blade_axes_reviewed.json').read_text())['axes']
    weights = np.array(coverage(image))
    line = np.array(axes[name], dtype=float).reshape(2, 2)
    start, end = line; direction = end - start; length = np.linalg.norm(direction)
    direction /= length
    yy, xx = np.indices((image.height, image.width))
    delta = np.stack([xx - start[0], yy - start[1]], axis=2)
    along = delta @ direction
    distance = np.abs(delta[:, :, 0] * direction[1] - delta[:, :, 1] * direction[0])
    nearby = (along >= -5) & (along <= length + 5) & (distance <= 6)
    rgb = np.array(image)[:, :, :3].astype(float)
    # Include dark blue blade reflections inside the explicitly reviewed footprint.
    metal = (rgb[:, :, 2] > rgb[:, :, 0]) & (rgb[:, :, 1] > rgb[:, :, 0])
    weights[nearby & metal, 0] = 0
    if name == 'bar1ded0':
        # Reviewed raised glove is almost black; color seeds alone missed it.
        glove = (xx >= 368) & (xx <= 410) & (yy >= 327) & (yy <= 364)
        leather = (rgb[:, :, 0] > rgb[:, :, 1] * 1.5) & (rgb[:, :, 1] < 35)
        weights[glove & leather, 1] = 255
        weights[np.array(image)[:, :, 3] == 0] = 0
    return Image.fromarray(weights, 'RGBA')
