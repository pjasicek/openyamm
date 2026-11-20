"""Extract native cleric poses, apply fixed grade and build enhanced material masks."""
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
    process_family.run('cle')
    for folder in ('cleaned', 'aligned_2x'):
        for path in (ROOT / folder).glob('*.png'):
            a = np.array(Image.open(path).convert('RGBA'))
            rgb = a[:, :, :3].astype(float)
            edge = ndimage.distance_transform_edt(a[:, :, 3] >= 250) <= 3
            rgb[:, :, 1] -= np.maximum(0, rgb[:, :, 1] - np.maximum(rgb[:, :, 0], rgb[:, :, 2]) - 2) * edge
            a[:, :, :3] = np.round(np.clip(rgb * .92, 0, 255)).astype(np.uint8)
            image = Image.fromarray(a); image.save(path)
            if folder == 'aligned_2x':
                mask = final_coverage(image, path.stem)
                weights = np.array(mask)[:, :, 1].astype(float) / 255
                pixels = np.array(image)
                pixels[:, :, :3] = np.round(pixels[:, :, :3] * (1 - .35 * weights[:, :, None])).astype(np.uint8)
                Image.fromarray(pixels).save(path)
                mask.save(ROOT / 'masks_2x' / path.name)
    (ROOT / 'tone.json').write_text(json.dumps({'rgb_gain': .92, 'scope': 'fixed family-wide',
        'reason': 'Match native muted blue, grey and gold tonal weight', 'alpha': 'unchanged', 'boots_rgb_gain': .65, 'boot_mask': 'enhanced coherent blue coverage, native height guide only'}, indent=2) + '\n')


if __name__ == '__main__':
    main()
