"""Apply explicitly reviewed, hash-bound palette coverage polygons to staged masks."""
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image, ImageDraw


def apply(project):
    out = Path(project).resolve() / 'redo_2x'
    policy = json.loads((out / 'review/material_mask_overrides.json').read_text())
    for name, entry in policy['frames'].items():
        image_path = out / 'aligned_2x' / (name + '.png')
        assert hashlib.sha256(image_path.read_bytes()).hexdigest() == entry['aligned_sha256']
        image = Image.open(image_path).convert('RGBA')
        mask_path = out / 'masks_2x' / (name + '.png')
        mask = Image.open(mask_path)
        assert mask.mode == 'L' and mask.size == image.size
        assert entry['reason']
        guide = Image.new('L', image.size)
        draw = ImageDraw.Draw(guide)
        for polygon in entry['polygons']:
            draw.polygon([tuple(point) for point in polygon], fill=255)
        values = np.array(mask)
        selected = (np.array(guide) > 0) & (np.array(image)[:, :, 3] > 0)
        values[selected] = 255
        Image.fromarray(values).save(mask_path)
    print('Applied reviewed material coverage to', len(policy['frames']), 'poses.')


if __name__ == '__main__':
    apply(sys.argv[1])
