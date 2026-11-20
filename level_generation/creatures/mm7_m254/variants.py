"""Golem enhanced dark/light cloth stripe masks and deterministic native ACT variants."""
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
    base = palettes[255]
    histogram = np.zeros(256)
    for item in sources["sources"].values():
        histogram += np.bincount(np.array(Image.open(REPO/item["path"])).ravel(), minlength=256)
    variants = []
    for palette, target in palettes.items():
        regions = []
        for channel, bounds in enumerate([(151, 199), (202, 256)]):
            ids = np.arange(*bounds)
            ids = ids[(base[ids,1] > base[ids,0]*1.1) & (base[ids,1] > base[ids,2]*1.04)]
            luma_weights = np.array([.2126,.7152,.0722])
            luminance = base[ids] @ luma_weights
            weights = histogram[ids] / np.maximum(luminance, 8)**2
            gain = ((luminance*weights) @ target[ids]) / ((luminance*weights) @ luminance)
            # Frozen identity-sheet native/enhanced median luminances, shared by every frame.
            normalization = [47.3264/31.3986, 79.3906/91.5008][channel]
            matrix = np.outer(luma_weights, gain) * normalization
            regions.append(dict(channel=channel, native_indices=ids.tolist(), rgb_matrix=matrix.tolist(),
                                mean_fit_error=float(abs(base[ids] @ matrix-target[ids]).mean())))
        descriptors = [int(d) for d, binding in sources['descriptor_bindings'].items()
                       if sources['groups'][binding['standing']]['frames'][0]['palette_id'] == palette]
        variants.append(dict(id=f'mm7:palette{palette}', palette_id=palette, default=palette == 255,
                             exact_bypass=palette == 255, descriptors=descriptors, regions=regions))
    names = json.loads((HERE / 'registration.json').read_text())
    for name in names:
        rgba = np.array(Image.open(HERE / f'aligned_2x/{name}.png'))
        r, g, b = rgba[:, :, :3].astype(float).transpose(2, 0, 1)
        alpha = rgba[:, :, 3]/255
        green = (g-r)/np.maximum(g,1)
        coverage = np.clip((green-.06)/.20,0,1) * np.clip((g-b)/np.maximum(g*.12,1),0,1)
        seed = (green > .24) & (g > b*1.08) & (alpha > .5)
        labels, _ = ndimage.label(seed)
        keep = np.bincount(labels.ravel()) >= 25
        keep[0] = False
        coverage *= ndimage.distance_transform_edt(~keep[labels]) <= 4
        # The enhanced cloth alternates deep green and pale teal; classify its own painted pixels.
        support = coverage * alpha
        smooth = ndimage.gaussian_filter(g * support, 10) / np.maximum(ndimage.gaussian_filter(support, 10), 1e-8)
        ratio = ndimage.median_filter(g / np.maximum(smooth, 1), size=3)
        light = np.clip((ratio-.90)/.20,0,1)
        weights = np.dstack((coverage*(1-light),coverage*light,np.zeros_like(g)))
        denominator = ndimage.gaussian_filter(alpha, .45)
        for channel in range(2):
            weights[:, :, channel] = ndimage.gaussian_filter(weights[:, :, channel]*alpha, .45) / np.maximum(denominator, 1e-8)
        weights[alpha == 0] = 0
        weights /= np.maximum(weights.sum(axis=2), 1)[:, :, None]
        Image.fromarray(np.round(weights*255).astype(np.uint8)).save(HERE / f'masks_2x/{name}.png')
    data = dict(variants=variants, regions=[dict(id='dark_green_stripe', channel='R'), dict(id='light_green_stripe', channel='G')],
                recolor=dict(operation='independent_masked_rgb_matrices', color_space='encoded sRGB 0..255',
                rule='base + sum(mask[channel] * (base @ region_matrix - base)); exact base bypass; alpha unchanged',
                mask_format='RGB8 linear; R dark green stripe, G light green stripe, B reserved zero',
                calibration='Separate fixed native pixel-frequency-weighted relative-error ACT luminance-to-RGB fits: dark stripe 151..198, light stripe 202..255; only genuinely green ACT entries, excluding dark blue underwear/shadows. Frozen native/enhanced standing median shade normalization: R 47.3264/31.3986, G 79.3906/91.5008.',
                mask_filter='Enhanced green cloth support, connected components >=25, 3x3 median enhanced green/local cloth brightness split 0.90..1.10; cloth-weighted Gaussian sigma 10; alpha-normalized Gaussian sigma 0.45.',
                protected='Gold body and belt trim, ivory horns, black collar and wrist/ankle cuffs.'))
    (HERE / 'variants.json').write_text(json.dumps(data, indent=2)+'\n')
    settings = json.loads((HERE / 'processing_settings.json').read_text())
    settings.update(masks=data['recolor']['mask_format'], mask_regions=data['regions'], recolor=data['recolor'])
    (HERE / 'processing_settings.json').write_text(json.dumps(settings, indent=2)+'\n')
    print('Authored', len(names), 'cloth stripe masks; visual review pending')


if __name__ == '__main__':
    run()
