"""Native palette deltas on enhanced RGB for newly restored MM8 families.

The source palette comparison supplies color samples, never a resized native mask.
Project settings describe the reviewed material regions and optional color support.
"""
import numpy as np
from PIL import Image
from scipy.spatial import cKDTree
from scipy import ndimage

from prepare_detail import REPO, read
import mm8_restore_queue as queue

ROOT = None
PALETTES = []


def feature(rgb):
    r, g, b = np.moveaxis(np.asarray(rgb, dtype=float), -1, 0)
    return np.stack((r - g, b - g, .5 * (.2126 * r + .7152 * g + .0722 * b)), axis=-1)


def settings():
    source = read(ROOT / 'sources.json')
    policy = read(ROOT / 'processing.json')['materials']
    palettes = {key: np.frombuffer((REPO / value['path']).read_bytes()[:768], np.uint8)
                .reshape(256, 3).astype(float) for key, value in source['palette_sources'].items()}
    base = palettes[str(source['base_palette'])]
    changed = np.maximum.reduce([np.max(abs(value - base), axis=1) for value in palettes.values()]) >= 10
    changed[0] = False
    component = policy.get('warm_component')
    if component:
        selected = np.array(component['palette_indices'])
        base_luma = base[selected] @ np.array([.2126, .7152, .0722])
        component = dict(component, palette_rgb_per_base_luma={
            key: np.median(value[selected] / np.maximum(base_luma[:, None], 1), axis=0).tolist()
            for key, value in palettes.items()}, bright_variant_luma_power=.70, bright_variant_luma_reference=60)
    return dict(base_palette=source['base_palette'], base_exact_bypass=True,
                operation='soft_native_palette_delta_knn_v1', regions=policy['regions'],
                protected=policy['protected'], color_space='sRGB RGB8; linear coverage',
                mask_method='Enhanced RGB classified against eight native palette neighbors; no spatial mask transfer.',
                neighbors=8, distance_floor=2, base_samples=base[1:].tolist(),
                changed_samples=changed[1:].astype(int).tolist(),
                palette_deltas={key: (value - base)[1:].tolist() for key, value in palettes.items()},
                support=policy.get('support', {}), warm_component=component)


def warm_coverage(pixels, config):
    """Keep one connected warm material; protect separate fasteners and pale skin."""
    policy = config.get('warm_component')
    if not policy:
        return np.zeros(pixels.shape[:2])
    rgb = pixels[:, :, :3].astype(float)
    r, g, b = np.moveaxis(rgb, -1, 0)
    strength = np.minimum((r - policy['red_green_ratio'] * g) / policy['transition'],
                          (r - b - policy['red_blue_minimum']) / policy['transition']).clip(0, 1)
    strength *= np.clip((g - policy['green_blue_ratio'] * b) / policy['transition'], 0, 1)
    seed = (strength > .65) & (pixels[:, :, 3] > 128)
    labels, count = ndimage.label(ndimage.binary_closing(seed, iterations=1))
    if not count:
        return np.zeros(seed.shape)
    sizes = np.bincount(labels.ravel())
    sizes[0] = 0
    selected = labels == sizes.argmax()
    holes, count = ndimage.label(ndimage.binary_fill_holes(selected) & ~selected)
    hole_sizes = np.bincount(holes.ravel())
    small = (holes > 0) & (hole_sizes[holes] <= policy['maximum_hole_area'])
    strength[small] = 1
    support = ndimage.binary_dilation(selected, iterations=2)
    coverage = strength * support
    coverage = ndimage.gaussian_filter(coverage, .45)
    coverage[pixels[:, :, 3] == 0] = 0
    return coverage


def lookup(rgb, config):
    flat = np.asarray(rgb).reshape(-1, 3).astype(np.uint32)
    packed = (flat[:, 0] << 16) | (flat[:, 1] << 8) | flat[:, 2]
    _, first, inverse = np.unique(packed, return_index=True, return_inverse=True)
    distances, indices = cKDTree(feature(config['base_samples'])).query(feature(flat[first]), k=config['neighbors'])
    distances, indices = distances[inverse], indices[inverse]
    weights = 1 / np.maximum(distances, config['distance_floor']) ** 4
    weights /= weights.sum(axis=1, keepdims=True)
    selected = weights * np.asarray(config['changed_samples'])[indices]
    coverage = selected.sum(axis=1)
    return indices, selected / np.maximum(coverage[:, None], 1e-12), coverage.reshape(rgb.shape[:-1])


def masks(im, config):
    pixels = np.asarray(im)
    _, _, coverage = lookup(pixels[:, :, :3], config)
    support = config['support']
    if support.get('green_excess'):
        rgb = pixels[:, :, :3].astype(float)
        start, span = support['green_excess']
        coverage *= np.clip((rgb[:, :, 1] - np.maximum(rgb[:, :, 0], rgb[:, :, 2]) - start) / span, 0, 1)
    if support.get('opaque_body'):
        alpha_limit, radius = support['opaque_body']
        body = ndimage.binary_opening(pixels[:, :, 3] >= alpha_limit, iterations=radius)
        labels, count = ndimage.label(body)
        if count:
            sizes = np.bincount(labels.ravel())
            sizes[0] = 0
            body = ndimage.binary_fill_holes(labels == sizes.argmax())
            body = ndimage.binary_dilation(body, iterations=1)
        coverage *= body
    coverage = np.maximum(coverage, warm_coverage(pixels, config))
    coverage[pixels[:, :, 3] == 0] = 0
    return np.round(coverage * 255).astype(np.uint8)


def recolor(im, mask, palette, config):
    if int(palette) == int(config['base_palette']):
        return im.copy()
    pixels = np.array(im)
    rgb = pixels[:, :, :3].astype(float)
    indices, weights, _ = lookup(rgb, config)
    delta = (np.asarray(config['palette_deltas'][str(palette)])[indices] * weights[:, :, None]).sum(axis=1)
    coverage = np.asarray(mask)[:, :, None] / 255
    warm = warm_coverage(pixels, config)[:, :, None]
    coverage = np.maximum(coverage - warm, 0)
    result = rgb + delta.reshape(rgb.shape) * coverage
    if config.get('warm_component'):
        luma = rgb @ np.array([.2126, .7152, .0722])
        component = config['warm_component']
        colors = np.asarray(component['palette_rgb_per_base_luma'][str(palette)])
        if colors @ np.array([.2126, .7152, .0722]) > 1:
            reference = component['bright_variant_luma_reference']
            luma = reference * (luma / reference) ** component['bright_variant_luma_power']
        target = luma[:, :, None] * colors
        result = result * (1 - warm) + target * warm
    pixels[:, :, :3] = np.round(result).clip(0, 255)
    return Image.fromarray(pixels)
