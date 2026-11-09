"""Goblin enhanced vest and trousers/bracer masks and deterministic native ACT variants."""
import json
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]


def run():
    sources = json.loads((HERE / 'sources.json').read_text())
    palettes = {int(p): np.frombuffer((REPO / data['path']).read_bytes()[:768], np.uint8)
                .reshape(256, 3).astype(float) for p, data in sources['palette_sources'].items()}
    base = palettes[248]
    histogram = np.zeros(256)
    for item in sources["sources"].values():
        histogram += np.bincount(np.array(Image.open(REPO/item["path"])).ravel(), minlength=256)
    variants = []
    for palette, target in palettes.items():
        regions = []
        for channel, bounds in enumerate([(156, 181), (181, 255)]):
            ids = np.arange(*bounds)
            luma_weights = np.array([.2126,.7152,.0722])
            luminance = base[ids] @ luma_weights
            weights = histogram[ids] / np.maximum(luminance, 8)**2
            gain = ((luminance*weights) @ target[ids]) / ((luminance*weights) @ luminance)
            matrix = np.outer(luma_weights, gain)
            regions.append(dict(channel=channel, native_indices=ids.tolist(), rgb_matrix=matrix.tolist(),
                                mean_fit_error=float(abs(base[ids] @ matrix-target[ids]).mean())))
        descriptors = [int(d) for d, binding in sources['descriptor_bindings'].items()
                       if sources['groups'][binding['standing']]['frames'][0]['palette_id'] == palette]
        variants.append(dict(id=f'mm7:palette{palette}', palette_id=palette, default=palette == 248,
                             exact_bypass=palette == 248, descriptors=descriptors, regions=regions))
    names = json.loads((HERE / 'registration.json').read_text())
    for name in names:
        rgba = np.array(Image.open(HERE / f'aligned_2x/{name}.png'))
        r, g, b = rgba[:, :, :3].astype(float).transpose(2, 0, 1)
        alpha = rgba[:, :, 3]/255
        blue = (b-r)/np.maximum(b,1)
        coverage = np.clip((blue-.045)/.16,0,1)
        seed = (blue > .20) & (alpha > .5)
        labels, _ = ndimage.label(seed)
        keep = np.bincount(labels.ravel()) >= 60
        keep[0] = False
        coverage *= ndimage.distance_transform_edt(~keep[labels]) <= 5
        vest = np.clip((g/np.maximum(b,1)-.79)/.08,0,1) * np.clip((blue-.23)/.13,0,1)
        weights = np.dstack((coverage*vest,coverage*(1-vest),np.zeros_like(g)))
        denominator = ndimage.gaussian_filter(alpha, .45)
        for channel in range(2):
            weights[:, :, channel] = ndimage.gaussian_filter(weights[:, :, channel]*alpha, .45) / np.maximum(denominator, 1e-8)
        weights[alpha == 0] = 0
        weights /= np.maximum(weights.sum(axis=2), 1)[:, :, None]
        Image.fromarray(np.round(weights*255).astype(np.uint8)).save(HERE / f'masks_2x/{name}.png')
    data = dict(variants=variants, regions=[dict(id='vest', channel='R'), dict(id='trousers_bracers', channel='G')],
                recolor=dict(operation='independent_masked_rgb_matrices', color_space='encoded sRGB 0..255',
                rule='base + sum(mask[channel] * (base @ region_matrix - base)); exact base bypass; alpha unchanged',
                mask_format='RGB8 linear; R teal vest, G navy trousers and bracers, B reserved zero',
                calibration='Separate fixed native pixel-frequency-weighted relative-error ACT luminance-to-RGB fits: vest 156..180, trousers/bracers 181..254.',
                mask_filter='Enhanced blue cloth support, connected components, teal/navy G-to-B and blue-chroma split; alpha-normalized Gaussian sigma 0.45.',
                protected='Green skin, reddish brown hair, brass armor and trim, sword metal and brown boots.'))
    (HERE / 'variants.json').write_text(json.dumps(data, indent=2)+'\n')
    settings = json.loads((HERE / 'processing_settings.json').read_text())
    settings.update(masks=data['recolor']['mask_format'], mask_regions=data['regions'], recolor=data['recolor'])
    (HERE / 'processing_settings.json').write_text(json.dumps(settings, indent=2)+'\n')
    print('Authored', len(names), 'vest/trousers masks; visual review pending')


if __name__ == '__main__':
    run()
