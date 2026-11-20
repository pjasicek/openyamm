"""Jackalman native tonal grade and coherent blue cloth coverage."""
from pathlib import Path
import json
import sys
import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / 'mm6_peasants'))
import process_family


def cloth_mask(image, config):
    weights = np.array(process_family.mask(image, config))
    # Headcloth/skirt are broad connected cloth regions; native cyan staff bands
    # are a different protected material despite also containing blue.
    labels, _ = ndimage.label(weights > 160)
    sizes = np.bincount(labels.ravel())
    keep = sizes >= 400
    keep[0] = False
    region = ndimage.binary_dilation(keep[labels], iterations=4)
    weights[~region] = 0
    return Image.fromarray(weights, 'L')


def main():
    process_family.run('jak1')
    config = json.loads((ROOT / 'config.json').read_text())
    for folder in ('cleaned', 'aligned_2x'):
        for path in (ROOT / folder).glob('*.png'):
            pixels = np.array(Image.open(path).convert('RGBA'))
            rgb = pixels[:, :, :3].astype(float)
            edge = ndimage.distance_transform_edt(pixels[:, :, 3] >= 250) <= 3
            rgb[:, :, 1] -= np.maximum(0, rgb[:, :, 1] - np.maximum(rgb[:, :, 0], rgb[:, :, 2]) - 2) * edge
            pixels[:, :, :3] = np.round(np.clip(rgb * .86, 0, 255)).astype(np.uint8)
            image = Image.fromarray(pixels)
            image.save(path)
            if folder == 'aligned_2x':
                cloth_mask(image, config).save(ROOT / 'masks_2x' / path.name)
    (ROOT / 'tone.json').write_text(json.dumps({
        'rgb_gain': .86, 'reason': 'Generated blue cloth, gold and chest highlights brighter than native',
        'alpha': 'unchanged', 'mask': 'enhanced blue cloth components >=400 pixels, four-pixel fringe; cyan staff bands protected',
        'comparisons': 'Extraction comparison sheets precede grade'
    }, indent=2) + '\n')


if __name__ == '__main__':
    main()
