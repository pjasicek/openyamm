"""Moon cleric enhanced robe/panel masks and deterministic native ACT variants."""
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
    base = palettes[37]
    variants = []
    for palette, target in palettes.items():
        regions = []
        for channel, bounds in enumerate([(165, 229), (135, 165)]):
            ids = np.arange(*bounds)
            if channel == 0:
                ids = ids[(base[ids, 1] > base[ids, 0]*1.35) & (base[ids, 1] > base[ids, 2]*2)]
            else:
                ids = ids[(base[ids, 1] > base[ids, 0]*.7) & (base[ids, 1] > base[ids, 2]*2)]
            matrix = np.linalg.lstsq(base[ids], target[ids], rcond=None)[0]
            regions.append(dict(channel=channel, native_indices=ids.tolist(), rgb_matrix=matrix.tolist(),
                                mean_fit_error=float(abs(base[ids] @ matrix-target[ids]).mean())))
        descriptors = [int(d) for d, binding in sources['descriptor_bindings'].items()
                       if sources['groups'][binding['standing']]['frames'][0]['palette_id'] == palette]
        variants.append(dict(id=f'mm7:palette{palette}', palette_id=palette, default=palette == 37,
                             exact_bypass=palette == 37, descriptors=descriptors, regions=regions))
    names = json.loads((HERE / 'registration.json').read_text())
    for name in names:
        rgba = np.array(Image.open(HERE / f'aligned_2x/{name}.png'))
        r, g, b = rgba[:, :, :3].astype(float).transpose(2, 0, 1)
        alpha = rgba[:, :, 3]/255
        green = np.clip(((g-b)/np.maximum(g, 1)-.35)/.25, 0, 1)
        green *= np.clip((1.28-r/np.maximum(g, 1))/.15, 0, 1)
        seed = (green > .7) & (alpha > .5)
        labels, count = ndimage.label(seed)
        sizes = np.bincount(labels.ravel())
        keep = sizes >= 100
        keep[0] = False
        green *= ndimage.distance_transform_edt(~keep[labels]) <= 4
        # Bright warm spell flecks overlap the robe. Preserve their color rather than
        # treating them as the similarly hued, much darker hanging-panel material.
        if name.startswith('m170a'):
            flecks = np.clip((r/np.maximum(g, 1)-.73)/.10, 0, 1) * np.clip((g-50)/25, 0, 1)
            green *= 1-flecks
        panels = np.clip((r/np.maximum(g, 1)-.69)/.18, 0, 1)
        weights = np.dstack((green*(1-panels), green*panels, np.zeros_like(g)))
        denominator = ndimage.gaussian_filter(alpha, .45)
        for channel in range(2):
            weights[:, :, channel] = ndimage.gaussian_filter(weights[:, :, channel]*alpha, .45) / np.maximum(denominator, 1e-8)
        weights[alpha == 0] = 0
        weights /= np.maximum(weights.sum(axis=2), 1)[:, :, None]
        Image.fromarray(np.round(weights*255).astype(np.uint8)).save(HERE / f'masks_2x/{name}.png')
    data = dict(variants=variants, regions=[dict(id='robe', channel='R'), dict(id='hanging_panels', channel='G')],
                recolor=dict(operation='independent_masked_rgb_matrices', color_space='encoded sRGB 0..255',
                rule='base + sum(mask[channel] * (base @ region_matrix - base)); exact base bypass; alpha unchanged',
                mask_format='RGB8 linear; R robe, G hanging panels, B reserved zero',
                calibration='Separate fixed native ACT fits: green robe 165..228, dark olive panels 135..164.',
                mask_filter='Enhanced cloth hue support, connected components, green/olive chroma split; bright warm casting flecks excluded; alpha-normalized Gaussian sigma 0.45.',
                protected='Gray face/hands, black hair, gold ornament, turquoise tassels and golden spell flecks.'))
    (HERE / 'variants.json').write_text(json.dumps(data, indent=2)+'\n')
    settings = json.loads((HERE / 'processing_settings.json').read_text())
    settings.update(masks=data['recolor']['mask_format'], mask_regions=data['regions'], recolor=data['recolor'])
    (HERE / 'processing_settings.json').write_text(json.dumps(settings, indent=2)+'\n')
    print('Authored', len(names), 'robe/panel masks; visual review pending')


if __name__ == '__main__':
    run()
