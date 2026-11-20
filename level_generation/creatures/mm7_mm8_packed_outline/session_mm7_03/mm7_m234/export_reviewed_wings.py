"""Export this session's reviewed wing masks through the unchanged shared tools."""
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / 'mm7_m214'))
import export_session

original_masks = export_session.masks


def reviewed_masks(family, out, sources, records, config):
    original_masks(family, out, sources, records, config)
    exclusions = json.loads((out / 'wing_stone_exclusions.json').read_text())
    for name, entry in exclusions.items():
        aligned = out / f'aligned_2x/{name}.png'
        assert hashlib.sha256(aligned.read_bytes()).hexdigest() == entry['aligned_sha256']
        path = out / f'masks_2x/{name}.png'
        mask = np.array(Image.open(path))
        cut = Image.new('L', (mask.shape[1], mask.shape[0]))
        for polygon in entry['polygons']:
            ImageDraw.Draw(cut).polygon([tuple(point) for point in polygon], fill=255)
        mask[np.array(cut) != 0] = 0
        Image.fromarray(mask).save(path)
    path = out / 'variants.json'
    variants = json.loads(path.read_text())
    variants['recolor']['mask_filter'] += (
        ' SHA-bound, visually reviewed stone-hand polygons protect reflected green on '
        'the two front flight poses after membrane filtering.'
    )
    path.write_text(json.dumps(variants, indent=2) + '\n')


if __name__ == '__main__':
    export_session.masks = reviewed_masks
    export_session.export('mm7_m234')
