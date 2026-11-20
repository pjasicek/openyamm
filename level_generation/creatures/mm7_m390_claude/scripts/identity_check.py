"""Compare the MM7 Roc sprite family (m390) with the MM8 Thunderbird family (m552) it shares art with.

Reads the original indexed bitmaps, the palettes and the sprite frame tables; writes review/identity_check.json.
"""
import hashlib
import json
import os
import sys

import numpy as np
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..'))
MM7 = os.path.join(ROOT, 'assets_dev/worlds/mm7/sprites')
MM8 = os.path.join(ROOT, 'assets_legacy/sprites_mm8_monsters_20261019/assets_dev/engine/sprites')
OUT = os.path.join(os.path.dirname(__file__), '../review/identity_check.json')


def load(directory, name):
    for entry in os.listdir(directory):
        if entry.lower() == name.lower() + '.bmp':
            image = Image.open(os.path.join(directory, entry))
            return np.array(image), image.getpalette()
    return None, None


def main():
    names = sorted(entry[:-4].lower() for entry in os.listdir(MM7) if entry.lower().startswith('m390'))
    frames = []
    for name in names:
        a, pa = load(MM7, name)
        b, pb = load(MM8, name.replace('m390', 'm552'))
        if b is None:
            frames.append({'frame': name, 'mm8': None})
            continue
        same_shape = a.shape == b.shape
        index_equal = float((a == b).mean()) if same_shape else 0.0
        mask_a = a != 0
        mask_b = b != 0
        iou = float((mask_a & mask_b).sum() / max(1, (mask_a | mask_b).sum())) if same_shape else 0.0
        frames.append({'frame': name, 'index_equal_fraction': round(index_equal, 4), 'alpha_iou': round(iou, 4)})
    palettes = {}
    for pid in (553, 554, 555):
        path = os.path.join(ROOT, f'assets_dev/worlds/mm8/textures/pal{pid}.act')
        palettes[pid] = hashlib.sha256(open(path, 'rb').read()).hexdigest()
    scales = {}
    for group in ('m391', 'm392', 'm393', 'm553', 'm554', 'm555'):
        text = open(os.path.join(ROOT, f'assets_dev/engine/rendering/sprite_frames/monsters/{group}.yml')).read()
        values = sorted({line.split(':')[1].strip() for line in text.splitlines() if line.strip().startswith('scale:')})
        pals = sorted({line.split(':')[1].strip() for line in text.splitlines()
                       if line.strip().startswith('palette_id:')})
        scales[group] = {'scales': values, 'palettes': pals}
    compared = [f for f in frames if f.get('mm8') is not False and 'index_equal_fraction' in f]
    summary = {
        'mm7_frames': len(names),
        'matched_mm8_frames': len(compared),
        'min_index_equal_fraction': min(f['index_equal_fraction'] for f in compared),
        'mean_index_equal_fraction': round(sum(f['index_equal_fraction'] for f in compared) / len(compared), 4),
        'min_alpha_iou': min(f['alpha_iou'] for f in compared),
    }
    json.dump({'summary': summary, 'palette_sha256': palettes, 'frame_tables': scales, 'frames': frames},
              open(OUT, 'w'), indent=1)
    print(json.dumps(summary), json.dumps(scales))


if __name__ == '__main__':
    sys.exit(main())
