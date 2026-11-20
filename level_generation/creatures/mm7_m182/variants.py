"""Dragon enhanced material masks and deterministic native ACT variants."""
import json
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.optimize import nnls

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]


def run():
    sources = json.loads((HERE / 'sources.json').read_text())
    palettes = {int(p): np.frombuffer((REPO / data['path']).read_bytes()[:768], np.uint8)
                .reshape(256, 3).astype(float) for p, data in sources['palette_sources'].items()}
    base = palettes[183]
    variants = []
    for palette, target in palettes.items():
        regions = []
        for channel, ids in enumerate([np.r_[1:36,216:256], np.r_[36:62,104:216], np.r_[62:88]]):
            matrix = np.linalg.lstsq(base[ids], target[ids], rcond=None)[0]
            if palette == 185 and channel == 1:
                # Avoid negative-coefficient extrapolation turning warm tail accents green.
                matrix = np.column_stack([nnls(base[ids], target[ids,c])[0] for c in range(3)])
            regions.append(dict(channel=channel, native_indices=ids.tolist(), rgb_matrix=matrix.tolist(),
                                fit='nonnegative least squares' if palette == 185 and channel == 1 else 'least squares',
                                mean_fit_error=float(abs(base[ids] @ matrix-target[ids]).mean())))
        descriptors = [int(d) for d, binding in sources['descriptor_bindings'].items()
                       if sources['groups'][binding['standing']]['frames'][0]['palette_id'] == palette]
        variants.append(dict(id=f'mm7:palette{palette}', palette_id=palette, default=palette == 183,
                             exact_bypass=palette == 183, descriptors=descriptors, regions=regions))
    corrections = json.loads((HERE / 'spine_mask_corrections.json').read_text())
    names = json.loads((HERE / 'registration.json').read_text())
    for name in names:
        rgba = np.array(Image.open(HERE / f'aligned_2x/{name}.png'))
        r, g, b = rgba[:, :, :3].astype(float).transpose(2, 0, 1)
        alpha = rgba[:, :, 3]/255
        # Enhanced scales are distinctly greener than the membrane; native masks are never resized.
        body = np.clip(((g-r)/np.maximum(g, 1)-.10)/.16, 0, 1)
        body *= np.clip(((g-b)/np.maximum(g, 1)-.08)/.15, 0, 1)
        # The continuous gold ventral strip differs from small gold membrane flecks and dorsal spines.
        gold_seed = (r > g*1.02) & (b < r*.60) & (r > 35) & (alpha > .5)
        labels, count = ndimage.label(gold_seed)
        sizes = np.bincount(labels.ravel())
        keep = sizes >= 180
        keep[0] = False
        support = ndimage.distance_transform_edt(~keep[labels]) <= 2
        gold = np.clip(((r-b)/np.maximum(r, 1)-.25)/.25, 0, 1)
        gold *= np.clip((r/np.maximum(g, 1)-.92)/.12, 0, 1)*support
        # Neutral pale horns, teeth and claw highlights bypass material recoloring.
        saturation = (np.maximum.reduce([r,g,b])-np.minimum.reduce([r,g,b]))/np.maximum.reduce([r,g,b,np.ones_like(r)])
        neutral = np.clip((.22-saturation)/.12,0,1)*np.clip((np.maximum.reduce([r,g,b])-45)/40,0,1)
        for x0,y0,x1,y1 in corrections.get(name,[]):
            gold[y0:y1,x0:x1] = 0
        body *= 1-gold
        membrane = (1-body)*(1-gold)
        weights = np.dstack((body, membrane, gold))*(1-neutral)[:,:,None]
        denominator = ndimage.gaussian_filter(alpha, .45)
        for channel in range(3):
            weights[:, :, channel] = ndimage.gaussian_filter(weights[:, :, channel]*alpha, .45) / np.maximum(denominator, 1e-8)
        weights[alpha == 0] = 0
        weights /= np.maximum(weights.sum(axis=2), 1)[:, :, None]
        Image.fromarray(np.round(weights*255).astype(np.uint8)).save(HERE / f'masks_2x/{name}.png')
    data = dict(variants=variants, regions=[dict(id='scales',channel='R'),dict(id='membranes_and_spines',channel='G'),dict(id='ventral_gold',channel='B')],
                recolor=dict(operation='independent_masked_rgb_matrices',color_space='encoded sRGB 0..255',
                rule='base + sum(mask[channel] * (base @ region_matrix - base)); exact base bypass; alpha unchanged',
                mask_format='RGB8 linear; R green scales, G wing membranes and dorsal accents, B continuous gold ventral plates',
                calibration='Fixed native ACT RGB fits: scales 1..35 and 216..255; membranes 36..61 and 104..215; ventral gold 62..87. Red membrane fit uses nonnegative coefficients to prevent green extrapolation on warm dorsal/tail accents.',
                mask_filter='Enhanced chroma and connected gold regions; six authored profile-recoil dorsal exclusions; neutral horn/claw protection; alpha-normalized Gaussian sigma 0.45.',
                protected='Pale horns, teeth and claws; gold ventral plates retain a separate native transform.'))
    (HERE / 'variants.json').write_text(json.dumps(data, indent=2)+'\n')
    settings = json.loads((HERE / 'processing_settings.json').read_text())
    settings.update(masks=data['recolor']['mask_format'], mask_regions=data['regions'], recolor=data['recolor'])
    (HERE / 'processing_settings.json').write_text(json.dumps(settings, indent=2)+'\n')
    print('Authored', len(names), 'dragon material masks; visual review pending')


if __name__ == '__main__':
    run()
