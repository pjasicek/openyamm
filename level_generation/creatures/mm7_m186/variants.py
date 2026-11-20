"""Dragonfly enhanced spine coverage and fixed native ACT recoloring."""
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]


def run():
    palettes = {p: np.frombuffer((REPO / f'assets_dev/worlds/mm7/textures/pal{p}.act').read_bytes()[:768],
                                np.uint8).reshape(256, 3).astype(float) for p in [187, 188, 189]}
    base = palettes[187]
    ids = np.arange(235, 253)
    ids = ids[(base[ids, 1] > base[ids, 0] * 1.4) & (base[ids, 1] > base[ids, 2] * 1.4)]
    variants = []
    for p, target in palettes.items():
        matrix = np.linalg.lstsq(base[ids], target[ids], rcond=None)[0]
        variants.append(dict(id=f'mm7:palette{p}', palette_id=p, default=p == 187, exact_bypass=p == 187,
                             descriptors=[226 + p - 187], rgb_matrix=matrix.tolist()))
    data = dict(variants=variants, regions=[dict(id='dorsal_spines', channel='R',
        protected='Brown-gray shell, pale wings, red-brown veins, orange eyes, jaw and gold tail.')],
        recolor=dict(operation='masked_rgb_matrix', color_space='encoded sRGB 0..255',
        rule='mix(base_rgb, base_rgb @ matrix, mask); alpha unchanged; exact base bypass',
        native_indices=ids.tolist(), mask_format='R8 linear',
        calibration='Fixed native green spine ACT RGB fit. Enhanced green coverage excludes neutral wings and warm shell.',
        mask_filter='Alpha-normalized Gaussian sigma 0.45 physical pixels.'))
    (HERE / 'variants.json').write_text(json.dumps(data, indent=2) + '\n')
    names = json.loads((HERE / 'registration.json').read_text())
    for name in names:
        a = np.array(Image.open(HERE / f'aligned_2x/{name}.png'))
        r, g, b = a[:, :, :3].astype(float).transpose(2, 0, 1)
        alpha = a[:, :, 3] / 255
        green = (g - np.maximum(r, b)) / np.maximum(g, 1)
        weight = np.clip((green - .10) / .25, 0, 1)
        weight = ndimage.gaussian_filter(weight * alpha, .45) / np.maximum(ndimage.gaussian_filter(alpha, .45), 1e-8)
        weight[alpha == 0] = 0
        Image.fromarray(np.round(weight * 255).astype(np.uint8)).save(HERE / f'masks_2x/{name}.png')
    settings = json.loads((HERE / 'processing_settings.json').read_text())
    settings.update(masks='R8 linear', recolor=data['recolor'])
    (HERE / 'processing_settings.json').write_text(json.dumps(settings, indent=2) + '\n')
    print('Authored', len(names), 'spine masks; visual review pending')


if __name__ == '__main__':
    run()
