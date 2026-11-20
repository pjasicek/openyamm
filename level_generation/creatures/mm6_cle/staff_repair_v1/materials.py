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
    # Hue-relative coverage retains dark cloth folds instead of punching holes in them.
    blue = np.clip(((b - np.maximum(r, g)) / np.maximum(b, .001) - .015) / .045, 0, 1)
    smooth = ndimage.gaussian_filter(rgb, (3, 3, 0))
    sr, sg, sb = smooth.transpose(2, 0, 1)
    violet = np.clip(((sr - sg) / np.maximum(sb, .01) + .11) / .03, 0, 1)
    neutral = np.clip((.12 - (rgb.max(axis=2) - rgb.min(axis=2)) / np.maximum(rgb.max(axis=2), .015)) / .08, 0, 1)
    labels, _ = ndimage.label((neutral > .7) & (a[:, :, 3] > 128))
    sizes = np.bincount(labels.ravel()); keep = sizes >= 300; keep[0] = False
    neutral *= ndimage.binary_dilation(keep[labels], iterations=3)
    neutral *= 1 - blue
    weights = np.stack([blue * (1 - violet), blue * violet, neutral, np.zeros_like(blue)], axis=2)
    # Enclosed dark creases belong to the surrounding leg material, not protected holes.
    leg_core = (weights[:, :, 1] > .8) & (a[:, :, 3] > 128)
    leg_fill = ndimage.binary_fill_holes(ndimage.binary_closing(leg_core, iterations=3))
    protected_warm = (r > g * 1.15) & (g > b * 1.1)
    fill = leg_fill & ~leg_core & ~protected_warm & (a[:, :, 3] > 128)
    weights[fill] = [0, 1, 0, 0]
    # Narrow dark blue-grey cloak piping is trim, not trousers. Keep its native dark edge.
    blue_depth = ndimage.distance_transform_edt(blue > .5)
    near_cloak = ndimage.distance_transform_edt(neutral < .8) <= 6
    piping = (blue > .2) & (blue_depth <= 3) & near_cloak & (rgb.max(axis=2) < .25)
    weights[piping] = 0
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
        # Smooth sparse native color samples; continuous enhanced shading must not become color bands.
        curve = ndimage.gaussian_filter1d(np.array(vectors[palette][region]), 8, axis=0, mode='nearest')
        output += weights[:, :, region, None] * curve[level]
    a[:, :, :3] = np.round(np.clip(output, 0, 1) * 255).astype(np.uint8)
    return Image.fromarray(a)

