"""Ghost enhanced brown robe masks and fixed native ACT palette transforms."""
import json
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]


def run():
    palettes = {p: np.frombuffer((REPO / f'assets_dev/worlds/mm7/textures/pal{p:03d}.act').read_bytes()[:768],
                                np.uint8).reshape(256, 3).astype(float) for p in [243, 244, 245]}
    base = palettes[244]
    ids = np.arange(84, 251)
    source = json.loads((HERE / 'sources.json').read_text())
    bindings = source['descriptor_bindings']
    histogram = np.zeros(256)
    for item in source['sources'].values():
        indices = np.array(Image.open(REPO / item['path']))
        histogram += np.bincount(indices.ravel(), minlength=256)
    weights = histogram[ids]
    variants = []
    for p, target in palettes.items():
        descriptors = [int(d) for d, binding in bindings.items()
                       if source['groups'][binding['standing']]['frames'][0]['palette_id'] == p]
        luma_weights = np.array([.2126, .7152, .0722])
        luminance = base[ids] @ luma_weights
        gain = ((luminance * weights) @ target[ids]) / ((luminance * weights) @ luminance)
        matrix = np.outer(luma_weights, gain)
        variants.append(dict(id=f'mm7:palette{p}', palette_id=p, default=p == 244, exact_bypass=p == 244,
                             descriptors=descriptors, rgb_matrix=matrix.tolist()))
    data = dict(variants=variants, regions=[dict(id='cloth', channel='R',
        protected='Yellowed ivory skull, ribs, arms and fingers; black eye and nasal sockets.')],
        recolor=dict(operation='masked_rgb_matrix', color_space='encoded sRGB 0..255',
        rule='mix(base_rgb, base_rgb @ matrix, mask); alpha unchanged; exact base bypass',
        native_indices=ids.tolist(), mask_format='R8 linear',
        calibration='Fixed native pixel-frequency-weighted rank-one cloth luminance-to-RGB fit over changed indices 84..250 avoids unstable chroma extrapolation.',
        mask_filter='Enhanced brown robe chroma with yellow-green bone exclusion and four authored enhanced hand exclusion regions with connected support and alpha-normalized Gaussian sigma 0.45.'))
    (HERE / 'variants.json').write_text(json.dumps(data, indent=2) + '\n')
    names = json.loads((HERE / 'registration.json').read_text())
    bone_exclusions = json.loads((HERE / 'bone_exclusions.json').read_text())
    for name in names:
        a = np.array(Image.open(HERE / f'aligned_2x/{name}.png'))
        r, g, b = a[:, :, :3].astype(float).transpose(2, 0, 1)
        alpha = a[:, :, 3] / 255
        chroma = (r-g)/np.maximum(r, 1)
        weight = np.clip((chroma-.07)/.11, 0, 1)
        # Bone is yellow-green: its G-B gap greatly exceeds its R-G gap.
        weight *= np.clip(((r-g)-.65*(g-b))/np.maximum(.08*r,1),0,1)
        seed = (chroma > .18) & (alpha > .5)
        labels, count = ndimage.label(seed)
        sizes = np.bincount(labels.ravel())
        keep = sizes >= 80
        keep[0] = False
        cloth = keep[labels]
        weight *= ndimage.distance_transform_edt(~cloth) <= 5
        for x0,y0,x1,y1 in bone_exclusions.get(name,[]):
            weight[y0:y1,x0:x1] = 0
        weight = ndimage.gaussian_filter(weight * alpha, .45) / np.maximum(ndimage.gaussian_filter(alpha, .45), 1e-8)
        weight[alpha == 0] = 0
        Image.fromarray(np.round(weight * 255).astype(np.uint8)).save(HERE / f'masks_2x/{name}.png')
    settings = json.loads((HERE / 'processing_settings.json').read_text())
    settings.update(masks='R8 linear', recolor=data['recolor'])
    (HERE / 'processing_settings.json').write_text(json.dumps(settings, indent=2) + '\n')
    print('Authored', len(names), 'cloth masks; visual review pending')


if __name__ == '__main__':
    run()
