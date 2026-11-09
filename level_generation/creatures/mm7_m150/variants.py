"""Angel enhanced skirt masks and fixed native ACT palette transforms."""
import json
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]


def run():
    palettes = {p: np.frombuffer((REPO / f'assets_dev/worlds/mm7/textures/pal{p:03d}.act').read_bytes()[:768],
                                np.uint8).reshape(256, 3).astype(float) for p in [151, 152, 153]}
    base = palettes[151]
    ids = np.arange(187, 254)
    ids = ids[(base[ids, 1] > base[ids, 0]*1.08) & (base[ids, 1] > base[ids, 2]*1.04)]
    source = json.loads((HERE / 'sources.json').read_text())
    bindings = source['descriptor_bindings']
    variants = []
    for p, target in palettes.items():
        descriptors = [int(d) for d, binding in bindings.items()
                       if source['groups'][binding['standing']]['frames'][0]['palette_id'] == p]
        matrix = np.linalg.lstsq(base[ids], target[ids], rcond=None)[0]
        variants.append(dict(id=f'mm7:palette{p}', palette_id=p, default=p == 151, exact_bypass=p == 151,
                             descriptors=descriptors, rgb_matrix=matrix.tolist()))
    data = dict(variants=variants, regions=[dict(id='cloth', channel='R',
        protected='Wings, skin, steel armor, brass, leather tabs, shield, sword and helmet jewels.')],
        recolor=dict(operation='masked_rgb_matrix', color_space='encoded sRGB 0..255',
        rule='mix(base_rgb, base_rgb @ matrix, mask); alpha unchanged; exact base bypass',
        native_indices=ids.tolist(), mask_format='R8 linear',
        calibration='Fixed native green skirt ACT RGB fit, excluding warm leather and neutral armor.',
        mask_filter='Enhanced green skirt chroma with connected support and alpha-normalized Gaussian sigma 0.45.'))
    (HERE / 'variants.json').write_text(json.dumps(data, indent=2) + '\n')
    names = json.loads((HERE / 'registration.json').read_text())
    for name in names:
        a = np.array(Image.open(HERE / f'aligned_2x/{name}.png'))
        r, g, b = a[:, :, :3].astype(float).transpose(2, 0, 1)
        alpha = a[:, :, 3] / 255
        chroma = (g-r)/np.maximum(g, 1)
        weight = np.clip((chroma-.035)/.16, 0, 1) * np.clip((g-.85*b)/np.maximum(.15*g, 1), 0, 1)
        seed = (chroma > .16) & (g > b*.9) & (alpha > .5)
        labels, count = ndimage.label(seed)
        sizes = np.bincount(labels.ravel())
        keep = sizes >= 100
        keep[0] = False
        cloth = keep[labels]
        weight *= ndimage.distance_transform_edt(~cloth) <= 5
        weight = ndimage.gaussian_filter(weight * alpha, .45) / np.maximum(ndimage.gaussian_filter(alpha, .45), 1e-8)
        weight[alpha == 0] = 0
        Image.fromarray(np.round(weight * 255).astype(np.uint8)).save(HERE / f'masks_2x/{name}.png')
    settings = json.loads((HERE / 'processing_settings.json').read_text())
    settings.update(masks='R8 linear', recolor=data['recolor'])
    (HERE / 'processing_settings.json').write_text(json.dumps(settings, indent=2) + '\n')
    print('Authored', len(names), 'cloth masks; visual review pending')


if __name__ == '__main__':
    run()
