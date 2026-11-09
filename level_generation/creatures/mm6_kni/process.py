"""Purple-safe knight extraction, neutral steel grade and enhanced material masks."""
import json
from pathlib import Path
import sys
import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / 'mm6_peasants'))
import process_family
from materials import coverage


def main():
    purple = process_family.module('purple_matte', ROOT.parent / 'mm6_sor1/process.py')
    process_family.matte.extract = purple.extract
    process_family.fix_contour = purple.contour
    process_family.run('kni')
    for folder in ('cleaned', 'aligned_2x'):
        for path in (ROOT / folder).glob('*.png'):
            image = Image.open(path).convert('RGBA')
            mask = coverage(image)
            pixels = np.array(image)
            rgb = pixels[:, :, :3].astype(float)
            neutral = np.array(mask)[:, :, 1:2] / 255
            grey = (rgb @ np.array([.2126, .7152, .0722]))[:, :, None]
            rgb = rgb * (1 - neutral) + grey * neutral
            pixels[:, :, :3] = np.round(np.clip(rgb * .90, 0, 255)).astype(np.uint8)
            pixels = np.array(purple.contour(Image.fromarray(pixels), 'magenta'))
            rgb = pixels[:, :, :3].astype(float)
            edge = ndimage.distance_transform_edt(pixels[:, :, 3] >= 250) <= 4
            warm_pink = rgb[:, :, 0] >= rgb[:, :, 2] * .92
            excess = np.maximum(0, np.minimum(rgb[:, :, 0], rgb[:, :, 2]) - rgb[:, :, 1] - 6)
            excess *= edge & warm_pink
            rgb[:, :, 0] -= excess
            rgb[:, :, 2] -= excess
            rgb[:, :, 1] -= np.maximum(0, rgb[:, :, 1] - np.maximum(rgb[:, :, 0], rgb[:, :, 2]) - 2) * edge
            pixels[:, :, :3] = np.round(np.clip(rgb, 0, 255)).astype(np.uint8)
            Image.fromarray(pixels).save(path)
            if folder == 'aligned_2x':
                mask.save(ROOT / 'masks_2x' / path.name)
    (ROOT / 'tone.json').write_text(json.dumps({
        'rgb_gain': .90, 'neutral_material': 'desaturate generated warm steel using enhanced material G coverage',
        'alpha': 'unchanged after extraction', 'matte': 'purple-safe local projection; shared sorcerer implementation',
        'comparisons': 'Extraction comparison sheets precede final grade'
    }, indent=2) + '\n')


if __name__ == '__main__':
    main()
