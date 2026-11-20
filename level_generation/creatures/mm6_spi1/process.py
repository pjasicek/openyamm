"""Extract spider sheets and keep one native blue-black material grade across views."""
import json
from pathlib import Path
import sys
import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / 'mm6_peasants'))
import process_family
from prepare_family import REPO, load


def main():
    process_family.run('spi1')
    _, config, inv = load('spi1')
    counts = np.zeros(256)
    for name in inv['sources']:
        counts += np.bincount(np.array(Image.open(REPO / inv['sources'][name]['path'])).ravel(), minlength=256)
    colors = {int(p): np.frombuffer((REPO / f'assets_dev/worlds/mm6/textures/pal{p}.act').read_bytes()[:768],
              np.uint8).reshape(256, 3) / 255 for p in inv['variants']}
    base = colors[823]
    selected = (base[:, 2] > base[:, 0] + .02) & (base[:, 2] > base[:, 1] + .02) & (counts > 0)
    y = base[selected] @ np.array([.2126, .7152, .0722])
    weights = counts[selected]
    vectors = {p: (np.sum(y[:, None] * c[selected] * weights[:, None], axis=0) /
                  np.sum(y * y * weights)) for p, c in colors.items()}
    reg = json.loads((ROOT / 'registration.json').read_text())
    for name in reg:
        for folder in ['cleaned', 'aligned_2x']:
            path = ROOT / folder / (name + '.png')
            im = Image.open(path)
            a = np.array(im)
            c = a[:, :, :3].astype(float) / 255
            # A few generated rear views expose red eye flecks despite native occlusion.
            if name.endswith('4'):
                red = (c[:, :, 0] > c[:, :, 1] + .03) & (c[:, :, 0] > c[:, :, 2] + .03)
                valid = (a[:, :, 3] > 128) & ~red & (c[:, :, 2] > c[:, :, 0] + .01)
                if red.any() and valid.any():
                    _, ix = ndimage.distance_transform_edt(~valid, return_indices=True)
                    c[red] = c[ix[0], ix[1]][red] * .5
                    a[:, :, :3] = np.round(c * 255).astype(np.uint8)
                    im = Image.fromarray(a)
            coverage = process_family.mask(im, config)
            w = np.array(coverage).astype(float) / 255
            lum = c @ np.array([.2126, .7152, .0722])
            target = lum[:, :, None] * vectors[823] * .70
            c = c * .85 * (1 - w[:, :, None]) + target * w[:, :, None]
            a[:, :, :3] = np.round(np.clip(c, 0, 1) * 255).astype(np.uint8)
            process_family.fix_contour(Image.fromarray(a), config['matte']).save(path)
            if folder == 'aligned_2x':
                coverage.save(ROOT / 'masks_2x' / (name + '.png'))
    (ROOT / 'recolor_vectors.json').write_text(json.dumps(
        {p: (v * .80).tolist() for p, v in vectors.items() if p != 823}, indent=2) + '\n')
    (ROOT / 'tone.json').write_text(json.dumps(dict(chitin_gain=.70, protected_gain=.85, variant_gain=.80,
        blue_vector=vectors[823].tolist(), scope='fixed material hue and gain across all frames',
        fit='native-used blue chitin palette indices weighted by all native source pixels',
        reason='Reduce brighter generated chitin and align blue/cyan sheet drift to native blue-black',
        alpha='unchanged', rear_cleanup='Only generated red flecks in native rear view 4 removed',
        comparisons='Extraction contacts precede grade; packaged contacts/viewer use final grade'), indent=2) + '\n')


if __name__ == '__main__':
    main()
