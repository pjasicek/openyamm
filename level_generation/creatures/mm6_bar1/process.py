"""Barbarian extraction, fixed tone and enhanced armor/leather coverage."""
from pathlib import Path
import json
import sys
import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / 'mm6_peasants'))
import process_family
from materials import final_coverage


def main():
    process_family.run('bar1')
    config = json.loads((ROOT / 'config.json').read_text())
    for folder in ('cleaned', 'aligned_2x'):
        for path in (ROOT / folder).glob('*.png'):
            pixels = np.array(Image.open(path).convert('RGBA'))
            rgb = pixels[:, :, :3].astype(float)
            edge = ndimage.distance_transform_edt(pixels[:, :, 3] >= 250) <= 3
            rgb[:, :, 1] -= np.maximum(0, rgb[:, :, 1] - np.maximum(rgb[:, :, 0], rgb[:, :, 2]) - 2) * edge
            pixels[:, :, :3] = np.round(np.clip(rgb * .88, 0, 255)).astype(np.uint8)
            image = Image.fromarray(pixels)
            image.save(path)
            if folder == 'aligned_2x':
                final_coverage(image, path.stem).save(ROOT / 'masks_2x' / path.name)
    (ROOT / 'tone.json').write_text(json.dumps({
        'rgb_gain': .88, 'reason': 'Generated cloth and gold brighter than native',
        'alpha': 'unchanged', 'mask': 'enhanced blue armor and reddish leather; gold, silver, hair and skin protected',
        'comparisons': 'Extraction comparison sheets precede grade'
    }, indent=2) + '\n')


if __name__ == '__main__':
    main()
