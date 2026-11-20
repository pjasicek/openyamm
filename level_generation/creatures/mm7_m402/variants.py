"""Spider enhanced abdomen coverage and fixed native ACT recoloring."""
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]


def run():
    palettes = {p: np.frombuffer((REPO / f'assets_dev/worlds/mm7/textures/pal{p:03d}.act').read_bytes()[:768],
                                np.uint8).reshape(256, 3).astype(float) for p in [66, 67, 68]}
    base = palettes[66]
    ids = np.arange(93, 214)
    variants = []
    for p, target in palettes.items():
        matrix = np.linalg.lstsq(base[ids], target[ids], rcond=None)[0]
        variants.append(dict(id=f'mm7:palette{p}', palette_id=p, default=p == 66, exact_bypass=p == 66,
                             descriptors=[400 + p - 66], rgb_matrix=matrix.tolist()))
    data = dict(variants=variants, regions=[dict(id='abdomen', channel='R',
        protected='Near-black legs, red serrated segments, ivory tips, mouth and yellow eyes.')],
        recolor=dict(operation='masked_rgb_matrix', color_space='encoded sRGB 0..255',
        rule='mix(base_rgb, base_rgb @ matrix, mask); alpha unchanged; exact base bypass',
        native_indices=ids.tolist(), mask_format='R8 linear',
        calibration='Fixed native abdomen ACT RGB fit including teal shadows and neutral highlights. Enhanced green/teal coverage excludes warm leg segments and eyes.',
        mask_filter='Green/teal components >=100 physical pixels, 2-pixel transition support; alpha-normalized Gaussian sigma 0.45.'))
    (HERE / 'variants.json').write_text(json.dumps(data, indent=2) + '\n')
    names = json.loads((HERE / 'registration.json').read_text())
    for name in names:
        a = np.array(Image.open(HERE / f'aligned_2x/{name}.png'))
        r, g, b = a[:, :, :3].astype(float).transpose(2, 0, 1)
        alpha = a[:, :, 3] / 255
        green = (g - r) / np.maximum(g, 1)
        weight = np.clip((green - .25) / .20, 0, 1) * np.clip((g - b * .85) / np.maximum(g * .15, 1), 0, 1)
        # Saturated green/teal abdomen regions exclude reflected green on neutral leg highlights.
        seed = (green > .31) & (g > b * .90) & (alpha > .5)
        labels, count = ndimage.label(seed)
        sizes = np.bincount(labels.ravel())
        keep = sizes >= 100
        keep[0] = False
        abdomen = keep[labels]
        weight *= ndimage.distance_transform_edt(~abdomen) <= 2
        weight = ndimage.gaussian_filter(weight * alpha, .45) / np.maximum(ndimage.gaussian_filter(alpha, .45), 1e-8)
        weight[alpha == 0] = 0
        Image.fromarray(np.round(weight * 255).astype(np.uint8)).save(HERE / f'masks_2x/{name}.png')
    settings = json.loads((HERE / 'processing_settings.json').read_text())
    settings.update(masks='R8 linear', recolor=data['recolor'])
    (HERE / 'processing_settings.json').write_text(json.dumps(settings, indent=2) + '\n')
    print('Authored', len(names), 'abdomen masks; visual review pending')


if __name__ == '__main__':
    run()
