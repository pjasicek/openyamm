"""Enhanced bone/blade/eye masks and native nonlinear palette curves."""
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

REGIONS = {'mask_r': 'Ivory bones', 'mask_g': 'Rusty blade and hilt',
           'mask_b': 'Red eye points', 'mask_a': 'Unused; not sprite alpha'}
LUMA = np.array([.2126, .7152, .0722])


def coverage(image, name=None, guides=None):
    a = np.array(image)
    rgb = a[:, :, :3].astype(float) / 255
    red, green, blue = rgb.transpose(2, 0, 1)
    warm = (red - green) / np.maximum(red, .01)
    eyes = np.clip((warm - .65) / .12, 0, 1)
    blade = np.clip((warm - .18) / .13, 0, 1) * (1 - eyes)
    if name and guides is None:
        guides = json.loads((Path(__file__).parent / 'material_guides.json').read_text())[name]
    if guides is not None:
        if 'blade_minimum_warm' in guides:
            blade = np.clip((warm - guides['blade_minimum_warm']) / .10, 0, 1) * (1 - eyes)
        for key, weight in [('blade', blade), ('eyes', eyes)]:
            region = np.zeros(red.shape, bool)
            for x0, y0, x1, y1 in guides[key]:
                region[max(0, y0):y1, max(0, x0):x1] = True
            if key == 'blade' and 'blade_polygon' in guides:
                polygon = Image.new('L', image.size)
                ImageDraw.Draw(polygon).polygon([tuple(p) for p in guides['blade_polygon']], fill=255)
                region = np.array(polygon) > 0
            elif key == 'blade' and 'blade_axis' in guides:
                axis = guides['blade_axis']
                start, end = np.array(axis['points'], dtype=float)
                vector = end-start
                yy, xx = np.indices(red.shape)
                along = np.clip(((xx-start[0])*vector[0]+(yy-start[1])*vector[1]) /
                                max(float(vector @ vector), 1), 0, 1)
                distance = np.hypot(xx-start[0]-along*vector[0], yy-start[1]-along*vector[1])
                region &= distance <= axis['radius']
            weight *= region
    bone = np.clip(1 - blade - eyes, 0, 1)
    out = np.zeros((*red.shape, 4), np.uint8)
    out[:, :, 0] = np.floor(bone * 255)
    out[:, :, 1] = np.floor(blade * 255)
    out[:, :, 2] = np.floor(eyes * 255)
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
    bone = (ids > 0) & ((ids <= 142) | (ids >= 210))
    blade = (ids >= 143) & (ids <= 198)
    eyes = (ids >= 199) & (ids <= 209)
    y = colors[816] @ LUMA
    curves = {}
    for palette in (817, 818):
        regions = []
        for selected in (bone, blade, eyes):
            valid = selected & (counts > 0)
            # Native highlights clamp and dark red bones crush to black: preserve
            # that nonlinear response instead of fitting a single RGB slope.
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
