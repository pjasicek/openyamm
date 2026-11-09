"""Record source-specific round tine cores and individual wood thorns after clay inspection."""
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import median_filter

from prepare_weapons import simplify

P = Path(__file__).resolve().parents[1]
ROOT = P.parents[2]
designs = json.loads((P / 'designs.json').read_text())
for icon in ['7item039', '7item040', '7item227', 'item051', 'item053', 'item055', 'trident1', 'trident2']:
    design = designs['pole_' + icon]
    w, h = design['image_size']
    mask = np.asarray(Image.open(ROOT / 'assets_dev/engine/icons_x2' / (icon + '.png')))[:, :, 3] > 127
    parts = []
    for side in (-1, 1):
        profile = []
        for y in range(round(h * .3) if icon == 'item053' else design['head_end']):
            xs = np.flatnonzero(mask[y] & ((np.arange(w) - w / 2) * side > w * .07))
            runs = [r for r in np.split(xs, np.flatnonzero(np.diff(xs) > 1) + 1) if len(r)]
            if not runs:
                continue
            run = max(runs, key=len)
            # A branch joined to the central stem is its socket, not another tine cross-section.
            if (run.min() - w / 2) * side < w * .08 and (run.max() - w / 2) * side < w * .08:
                continue
            if len(run) > w * .3:
                break
            profile.append([float(y), float((run.min() + run.max()) / 2), float(max(.45, len(run) / 2 * .8))])
        a = np.array(profile)
        assert len(a) > 15, icon
        a[:, 1:] = median_filter(a[:, 1:], size=(5, 1), mode='nearest')
        indexes = {0, len(a) - 1}
        for axis in (1, 2):
            indexes.update(int(np.argmin(abs(a[:, 0] - pt[0]))) for pt in simplify(a[:, [0, axis]], .65))
        profile = [[float(x), float(y), float(r)] for y, x, r in a[sorted(indexes)]]
        parts.append({'material': 'gold' if icon in ['7item227', 'item055', 'trident1', 'trident2'] else 'steel',
                      'profile': profile})
    design['swept_parts'] = parts

design = designs['pole_item041']
design['shaft_profile'] = [[y, 34, r] for y, r in
                           [(0, .5), (8, 1.5), (35, 5), (65, 9), (88, 12), (110, 13),
                            (145, 12), (165, 12), (220, 11), (290, 11), (400, 11),
                            (480, 11), (500, 14), (530, 13), (547, 10)]]
parts = []
for n, y in enumerate([98, 147, 191, 212, 252, 299]):
    for side in (-1, 1):
        base = [34 + side * 9, y + 4, 5 if n else 7]
        tip = [34 + side * (27 if n % 2 else 31), y - (10 if n % 2 else 0), .45]
        parts.append({'material': 'wood', 'profile': [base, tip]})
design['swept_parts'] = parts

design = designs['pole_7item031']
design['shaft_profile'] = [[y, 16.5, min(r, 9)] if y < 208 else [y, x, r]
                           for y, x, r in design['shaft_profile']]
design['swept_parts'] = [{'material': 'rope', 'profile': [[16, 136, 1.5], [12, 157, 1.5],
                                                        [4, 180, 1.2], [2, 195, .45]]}]

# Tiny studs belong in the painted normal detail; the core stays a continuous round timber.
for icon in ['item042', 'item079']:
    design = designs['pole_' + icon]
    a = np.array(design['shaft_profile'])
    ys = np.arange(a[0, 0], a[-1, 0] + 1)
    radius = median_filter(np.interp(ys, a[:, 0], a[:, 2]), size=23, mode='nearest')
    centre = median_filter(np.interp(ys, a[:, 0], a[:, 1]), size=23, mode='nearest')
    points = np.column_stack([ys, centre, radius])
    indexes = {0, len(points) - 1}
    for axis in (1, 2):
        indexes.update(int(np.argmin(abs(ys - pt[0]))) for pt in simplify(points[:, [0, axis]], .65))
    design['shaft_profile'] = points[sorted(indexes)].tolist()

assert all(len(p['profile']) >= 2 and min(r[2] for r in p['profile']) > 0
           for d in designs.values() for p in d.get('swept_parts', []))
(P / 'designs.json').write_text(json.dumps(designs, indent=2) + '\n')
