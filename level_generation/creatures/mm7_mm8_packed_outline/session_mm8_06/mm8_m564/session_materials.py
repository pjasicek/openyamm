"""MM8 session adapter for the existing enhanced-RGB native-palette lookup.

Used by all eight staged families. Coverage is provisional until pose/mask review;
it is computed on generated pixels, never transferred from a native silhouette.
"""
import importlib.util
import json
import os
from pathlib import Path
import sys

import numpy as np
from PIL import Image

REPO = Path.cwd().resolve()
STAGE = Path(__file__).resolve().parent.parent
ROOT = STAGE / os.environ['MM8_RESTORE_FAMILY']
assert ROOT.parent == STAGE and ROOT.is_dir()
sys.path.insert(0, str(REPO / 'level_generation/creatures/mm8_m584'))
spec = importlib.util.spec_from_file_location(
    'session_native_palette_lookup', REPO / 'level_generation/creatures/mm8_m584/materials.py')
lookup_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lookup_module)


def settings():
    source = json.loads((ROOT / 'sources.json').read_text())
    palettes = {key: np.frombuffer((REPO / value['path']).read_bytes()[:768], np.uint8)
                .reshape(256, 3).astype(float) for key, value in source['palette_sources'].items()}
    base = palettes[str(source['base_palette'])]
    changed = np.max([np.max(abs(value - base), axis=1) for value in palettes.values()], axis=0) > 0
    changed[0] = False
    return dict(base_palette=source['base_palette'], base_exact_bypass=True,
                operation='soft_native_palette_delta_knn_v1', color_space='sRGB RGB8; linear R8 coverage',
                regions=['native palette-changing materials; semantic review pending'],
                mask_method='Existing Raven Man unique-RGB palette lookup; no native spatial mask transfer.',
                feature='(R-G, B-G, 0.5*luma709), RGB8', neighbors=8, distance_floor=2,
                base_samples=base[1:].tolist(), changed_samples=changed[1:].astype(int).tolist(),
                palette_deltas={key: (value - base)[1:].tolist() for key, value in palettes.items()},
                review_status='provisional_pending_all_palette_and_material_poses')


CONFIG = settings()
REGIONS = CONFIG['regions']


def coverage(image):
    if not any(CONFIG['changed_samples']):
        return Image.new('L', image.size)
    pixels = np.asarray(image)
    _, _, weights = lookup_module.lookup(pixels[:, :, :3], CONFIG)
    weights[pixels[:, :, 3] == 0] = 0
    return Image.fromarray(np.round(weights * 255).astype(np.uint8), 'L')


def recolor(image, mask, palette, *legacy_review_arguments):
    if int(palette) == CONFIG['base_palette']:
        return image.copy()
    pixels = np.array(image)
    rgb = pixels[:, :, :3].astype(float)
    ids, weights, _ = lookup_module.lookup(rgb, CONFIG)
    delta = (np.asarray(CONFIG['palette_deltas'][str(palette)])[ids] * weights[:, :, None])
    delta = delta.sum(axis=1).reshape(rgb.shape)
    pixels[:, :, :3] = np.round(rgb + delta * np.asarray(mask)[:, :, None] / 255).clip(0, 255)
    return Image.fromarray(pixels)
