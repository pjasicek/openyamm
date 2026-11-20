"""Enhanced cleric garment coverage and native palette luminance curves."""
import numpy as np
from scipy import ndimage
from PIL import Image

REGIONS = {'mask_r': 'Blue tunic and sleeves', 'mask_g': 'Dark violet-blue trousers and boots',
           'mask_b': 'Grey shoulder mantle and cloak', 'mask_a': 'Unused; not sprite alpha'}
LUMA = np.array([.2126, .7152, .0722])


def coverage(image):
    a = np.array(image)
    rgb = a[:, :, :3].astype(float) / 255
    r, g, b = rgb.transpose(2, 0, 1)
    blue = np.clip((b - np.maximum(r, g) - .002) / .025, 0, 1)
    blue *= np.clip(((b - np.maximum(r, g)) / np.maximum(b, .01) - .03) / .10, 0, 1)
    smooth = ndimage.gaussian_filter(rgb, (3, 3, 0))
    sr, sg, sb = smooth.transpose(2, 0, 1)
    violet = np.clip(((sr - sg) / np.maximum(sb, .01) + .11) / .03, 0, 1)
    neutral = np.clip((.12 - (rgb.max(axis=2) - rgb.min(axis=2)) / np.maximum(rgb.max(axis=2), .015)) / .08, 0, 1)
    labels, _ = ndimage.label((neutral > .7) & (a[:, :, 3] > 128))
    sizes = np.bincount(labels.ravel()); keep = sizes >= 300; keep[0] = False
    neutral *= ndimage.binary_dilation(keep[labels], iterations=3)
    neutral *= 1 - blue
    weights = np.stack([blue * (1 - violet), blue * violet, neutral, np.zeros_like(blue)], axis=2)
    depth = ndimage.distance_transform_edt(a[:, :, 3] >= 250)
    core = depth > 3
    if core.any():
        distance, nearest = ndimage.distance_transform_edt(~core, return_indices=True)
        edge = (a[:, :, 3] > 0) & ~core & (distance <= 5)
        weights[edge] = weights[nearest[0], nearest[1]][edge]
    out = np.floor(np.clip(weights, 0, 1) * 255).astype(np.uint8)
    out[a[:, :, 3] == 0] = 0
    return Image.fromarray(out, 'RGBA')


def fit(config, inv, repo):
    colors = {int(p): np.fromfile(repo / f'assets_dev/worlds/mm6/textures/pal{p}.act', np.uint8)
              [:768].reshape(256, 3) / 255 for p in inv['variants']}
    counts = np.zeros(256)
    for name in inv['sources']:
        counts += np.bincount(np.array(Image.open(repo / f'assets_dev/engine/sprites/{name}.bmp'))
                              .ravel(), minlength=256)
    base = colors[675]; r, g, b = base.T
    ids = np.arange(256)
    tunic = (ids >= 39) & (ids <= 80)
    legs = (ids >= 81) & (ids <= 121)
    cloak = (base.max(axis=1) - base.min(axis=1) < .002) & ~legs & ~tunic
    y = base @ LUMA
    curves = {}
    for palette in (674, 676):
        regions = []
        for selected in (tunic, legs, cloak):
            valid = selected & (counts > 0) & (np.arange(256) > 0)
            samples = y[valid] * 255
            curve = []
            for level in range(256):
                distance = (samples - level) ** 2
                weight = counts[valid] * np.exp(-(distance - distance.min()) / 32)
                curve.append((weight @ colors[palette][valid] / weight.sum()).tolist())
            regions.append(curve)
        curves[palette] = regions + [np.zeros((256, 3)).tolist()]
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


def final_coverage(image, name):
    """Use native boot height only as a broad location guide; segment enhanced material pixels."""
    from pathlib import Path
    import json
    root = Path(__file__).resolve().parent
    sources = json.loads((root / 'sources.json').read_text())
    source = sources['sources'][name]
    indexed = np.array(Image.open(root.parents[2] / source['path']))
    palette = np.fromfile(root.parents[2] / 'assets_dev/worlds/mm6/textures/pal675.act', np.uint8)[:768].reshape(256, 3)
    ids = np.arange(256)
    native_legs = ((ids >= 81) & (ids <= 121))[indexed]
    yy, xx = np.where(native_legs)
    w = np.array(coverage(image)).astype(float) / 255
    if len(yy) < 4:
        w[:, :, 0] += w[:, :, 1]; w[:, :, 1] = 0
        return Image.fromarray(np.floor(w * 255).astype(np.uint8), 'RGBA')
    bounds = Image.fromarray((indexed != 0).astype(np.uint8)).getbbox()
    top = (source['native_offset'][1] + max(np.percentile(yy, 10), bounds[1] + (bounds[3] - bounds[1]) * .50)) * 2 - 12
    a = np.array(image)
    blue = w[:, :, 0] + w[:, :, 1]
    candidate = (w[:, :, 1] > .4) & (np.indices(blue.shape)[0] >= top)
    labels, _ = ndimage.label(candidate)
    sizes = np.bincount(labels.ravel()); keep = sizes >= 40; keep[0] = False
    core = keep[labels]
    core = ndimage.binary_fill_holes(ndimage.binary_closing(core, iterations=3))
    # Include shaded holes inside boots, leaving cloak and alpha outside the material.
    distance = ndimage.distance_transform_edt(~core)
    leg = np.clip(2 - distance, 0, 1) * np.clip(blue * 3, 0, 1)
    inside = core & (a[:, :, 3] > 0)
    leg[inside] = 1
    total = np.maximum(blue, leg)
    w[:, :, 1] = leg
    w[:, :, 0] = np.maximum(0, total - leg)
    w[:, :, 2] *= 1 - total
    w[a[:, :, 3] == 0] = 0
    return Image.fromarray(np.floor(np.clip(w, 0, 1) * 255).astype(np.uint8), 'RGBA')
