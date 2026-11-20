"""Separate enhanced staff/hair coverage and deterministic native Cleric palettes."""
import json
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
from scipy.spatial import cKDTree
from process import ROOT, queue

PALETTES = [461, 462, 463]


def settings():
    source = json.loads((ROOT / 'sources.json').read_text())
    palettes = {k: np.frombuffer((queue.REPO / v['path']).read_bytes()[:768], np.uint8)
                   .reshape(256, 3).astype(float) for k, v in source['palette_sources'].items()}
    base = palettes['461']
    return {'base_palette': 461, 'base_exact_bypass': True,
        'operation': 'cleric_staff_palette_delta_and_hair_ramp_v1',
        'regions': ['green staff and finial inset', 'black hair'],
        'mask_channels': {'R': 'staff coverage', 'G': 'hair coverage', 'B': 'unused zero'},
        'mask_format': 'RGB8', 'color_space': 'sRGB RGB8; linear coverage',
        'protected': 'Tan skin, russet robe/vest, red front panel and gold/ivory fittings are protected.',
        'mask_method': 'Enhanced green chroma for staff. Neutral dark enhanced components within a broad native hair bounding region; reviewed per-pose component extensions prevent clipped hair coverage. No resized native silhouette mask.',
        'hair_component_extensions': json.loads((ROOT / 'hair_component_extensions.json').read_text()),
        'hair_luma_knots': [0, 12, 40], 'hair_native_ramp_indices': [68, 60, 69],
        'hair_ramps': {k: v[[68, 60, 69]].tolist() for k, v in palettes.items()},
        'staff_base_samples': base[25:59].tolist(),
        'staff_deltas': {k: (v - base)[25:59].tolist() for k, v in palettes.items()},
        'palette_deltas': {k: (v - base)[1:].tolist() for k, v in palettes.items()},
        'ignored_native_differences': 'One-code-value incidental palette rounding on protected materials; index zero is transparent.'}


def masks(image, config, name):
    a = np.asarray(image); rgb = a[:, :, :3].astype(float)
    r, g, b = np.moveaxis(rgb, -1, 0)
    staff = np.clip((g - np.maximum(r, b) - 2) / 20, 0, 1)
    source = json.loads((ROOT / 'sources.json').read_text())['sources'][name]
    ix = np.asarray(Image.open(queue.REPO / source['path']))
    ys, xs = np.where((ix >= 60) & (ix <= 81))
    roi = np.zeros(a.shape[:2], dtype=bool)
    if len(xs):
        box = [max(0, 32 + int(xs.min()) * 2 - 20), max(0, 32 + int(ys.min()) * 2 - 20),
               min(image.width, 32 + int(xs.max() + 1) * 2 + 20),
               min(image.height, 32 + int(ys.max() + 1) * 2 + 20)]
        roi[box[1]:box[3], box[0]:box[2]] = True
    chroma = np.max(rgb, axis=2) - np.min(rgb, axis=2)
    neutral = np.clip((18 - chroma) / 8, 0, 1)
    dark = np.clip((75 - np.max(rgb, axis=2)) / 20, 0, 1)
    candidate = (neutral * dark > .1) & (a[:, :, 3] > 0)
    extension = config['hair_component_extensions'].get(name)
    if extension:
        assert queue.sha(ROOT / 'toned_2x' / (name + '.png')) == extension['master_sha256']
        if 'hair_seed_box' in extension:
            x0, y0, x1, y1 = extension['hair_seed_box']
            roi[:] = False
            roi[y0:y1, x0:x1] = True
        if 'enhanced_hair_boundary' in extension:
            boundary = Image.new('L', image.size)
            ImageDraw.Draw(boundary).polygon([tuple(p) for p in extension['enhanced_hair_boundary']], fill=255)
            candidate &= np.asarray(boundary) > 0
    else:
        candidate &= roi
    labels, _ = ndi.label(candidate)
    sizes = np.bincount(labels.ravel()); sizes[0] = 0
    seeded = np.zeros(len(sizes), dtype=bool)
    seeded[np.unique(labels[roi])] = True
    seeded[0] = False
    hair = neutral * dark * (sizes[labels] >= 12) * seeded[labels]
    hair *= 1 - staff
    result = np.rint(np.stack([staff, hair, np.zeros_like(staff)], axis=2) * 255).astype(np.uint8)
    result[a[:, :, 3] == 0] = 0
    return result


def recolor(image, mask, palette, config):
    if int(palette) == config['base_palette']:
        return image.copy()
    a = np.array(image); rgb = a[:, :, :3].astype(float)
    coverage = np.asarray(mask, dtype=float) / 255
    points = np.asarray(config['staff_base_samples'])
    distance, indices = cKDTree(points).query(rgb.reshape(-1, 3), k=4)
    weights = 1 / np.maximum(distance, 2) ** 4
    weights /= weights.sum(axis=1, keepdims=True)
    deltas = np.asarray(config['staff_deltas'][str(palette)])
    staff_delta = (deltas[indices] * weights[:, :, None]).sum(axis=1).reshape(rgb.shape)
    luma = rgb @ np.array([.2126, .7152, .0722])
    ramp = np.asarray(config['hair_ramps'][str(palette)])
    hair_rgb = np.stack([np.interp(luma, config['hair_luma_knots'], ramp[:, k]) for k in range(3)], axis=2)
    hair_rgb += np.maximum(luma - config['hair_luma_knots'][-1], 0)[:, :, None] * .5
    rgb += staff_delta * coverage[:, :, 0, None] + (hair_rgb - rgb) * coverage[:, :, 1, None]
    a[:, :, :3] = np.rint(rgb).clip(0, 255).astype(np.uint8)
    return Image.fromarray(a)
