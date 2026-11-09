"""Devil enhanced hide/ventral-plate masks and deterministic native ACT variants."""
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
    base = palettes[44]
    variants = []
    for palette, target in palettes.items():
        regions = []
        for channel, bounds in enumerate([(140, 216), (60, 88)]):
            ids = np.arange(*bounds)
            if channel == 0:
                ids = ids[(base[ids, 0] > base[ids, 1]*1.1) & (base[ids, 1] > base[ids, 2]*1.4)]
            else:
                ids = ids[(base[ids, 2] > base[ids, 0]*1.02) & (base[ids, 0] > 20)]
            matrix = np.linalg.lstsq(base[ids], target[ids], rcond=None)[0]
            regions.append(dict(channel=channel, native_indices=ids.tolist(), rgb_matrix=matrix.tolist(),
                                mean_fit_error=float(abs(base[ids] @ matrix-target[ids]).mean())))
        descriptors = [int(d) for d, binding in sources['descriptor_bindings'].items()
                       if sources['groups'][binding['standing']]['frames'][0]['palette_id'] == palette]
        variants.append(dict(id=f'mm7:palette{palette}', palette_id=palette, default=palette == 44,
                             exact_bypass=palette == 44, descriptors=descriptors, regions=regions))
    names = json.loads((HERE / 'registration.json').read_text())
    eye_regions = json.loads((HERE / 'eye_regions.json').read_text())['circles']
    for name in names:
        rgba = np.array(Image.open(HERE / f'aligned_2x/{name}.png'))
        r, g, b = rgba[:, :, :3].astype(float).transpose(2, 0, 1)
        alpha = rgba[:, :, 3]/255
        hide = np.clip(((r-b)/np.maximum(r, 1)-.20)/.22, 0, 1)
        hide *= np.clip((r/np.maximum(g, 1)-1.05)/.18, 0, 1)
        # Yellow eye lights are close to neutral in R/G and stay protected.
        plates = np.clip(((b-r)/np.maximum(b, 1)-.015)/.12, 0, 1)
        for weight, minimum in [(hide, 70), (plates, 45)]:
            seed = (weight > .7) & (alpha > .5)
            labels, count = ndimage.label(seed)
            sizes = np.bincount(labels.ravel())
            keep = sizes >= minimum
            keep[0] = False
            weight *= ndimage.distance_transform_edt(~keep[labels]) <= 4
        if 'detail' in names[name]['batch']:
            # New masters render the chest plates nearer neutral gray. Require a
            # broad connected gray surface so thin ivory spikes stay protected.
            neutral = np.clip((b / np.maximum(r, 1) - .85) / .09, 0, 1)
            neutral *= np.clip((b / np.maximum(g, 1) - .93) / .08, 0, 1)
            seeds = ndimage.binary_closing((neutral > .7) & (alpha > .6), iterations=2)
            labels, count = ndimage.label(seeds)
            support = np.zeros_like(seeds)
            for label, slices in enumerate(ndimage.find_objects(labels), 1):
                if slices is None:
                    continue
                h, w = [v.stop-v.start for v in slices]
                region = labels == label
                if region.sum() >= 300 and min(h, w) >= 12 and max(h, w)/min(h, w) < 3.0:
                    support |= region
            neutral *= ndimage.distance_transform_edt(~support) <= 3
            plates = np.maximum(plates, neutral)
        eye_seed = (g > r*.90) & (b < r*.55) & (r > 150) & (alpha > .6)
        eye_labels, count = ndimage.label(eye_seed)
        eye_sizes = np.bincount(eye_labels.ravel())
        eye_keep = (eye_sizes >= 3) & (eye_sizes <= 180)
        eye_keep[0] = False
        eyes = ndimage.distance_transform_edt(~eye_keep[eye_labels]) <= 3
        if name in eye_regions:
            x, y, radius = eye_regions[name]
            yy, xx = np.indices(alpha.shape)
            eyes |= (xx-x)**2 + (yy-y)**2 <= radius**2
        hide[eyes] = 0
        plates[eyes] = 0
        weights = np.dstack((hide, plates*(1-hide), np.zeros_like(g)))
        denominator = ndimage.gaussian_filter(alpha, .45)
        for channel in range(2):
            weights[:, :, channel] = ndimage.gaussian_filter(weights[:, :, channel]*alpha, .45) / np.maximum(denominator, 1e-8)
        weights[alpha == 0] = 0
        weights /= np.maximum(weights.sum(axis=2), 1)[:, :, None]
        Image.fromarray(np.round(weights*255).astype(np.uint8)).save(HERE / f'masks_2x/{name}.png')
    data = dict(variants=variants, regions=[dict(id='hide', channel='R'), dict(id='ventral_plates', channel='G')],
                recolor=dict(operation='independent_masked_rgb_matrices', color_space='encoded sRGB 0..255',
                rule='base + sum(mask[channel] * (base @ region_matrix - base)); exact base bypass; alpha unchanged',
                mask_format='RGB8 linear; R ochre hide, G slate chest and feet, B reserved zero',
                calibration='Separate fixed native ACT fits: brown hide 140..215, slate ventral plates within 60..87.',
                mask_filter='Enhanced warm hide and blue-gray plate chroma with connected support; small bright yellow eye components excluded with a three-pixel margin; alpha-normalized Gaussian sigma 0.45.',
                protected='Ivory spikes, claws and teeth; yellow eyes. Slate chest and feet retain their separate native palette transform.'))
    (HERE / 'variants.json').write_text(json.dumps(data, indent=2)+'\n')
    settings = json.loads((HERE / 'processing_settings.json').read_text())
    settings.update(masks=data['recolor']['mask_format'], mask_regions=data['regions'], recolor=data['recolor'])
    (HERE / 'processing_settings.json').write_text(json.dumps(settings, indent=2)+'\n')
    print('Authored', len(names), 'hide/plate masks; visual review pending')


if __name__ == '__main__':
    run()
