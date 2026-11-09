"""Measure identified landmarks on both artworks independently; produce one full-resolution proof."""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(OUT.parents[1]))
from freeze_targets import rendered
from finalize_classification import ROOT

FEATURES = {'6cape1': [('left cloth tip', [0, 0, 0.2, 1], 'left'), ('upper fold crest', [0, 0, 1, 0.4], 'top'), ('right folded edge', [0.8, 0, 1, 1], 'right'), ('lower cloth hem', [0, 0.6, 1, 1], 'bottom')], '6cape2': [('left cloth tip', [0, 0, 0.2, 1], 'left'), ('upper fold crest', [0, 0, 1, 0.4], 'top'), ('right folded edge', [0.8, 0, 1, 1], 'right'), ('lower cloth hem', [0, 0.6, 1, 1], 'bottom')], '6cape3': [('left cloth tip', [0, 0, 0.2, 1], 'left'), ('upper fold crest', [0, 0, 1, 0.4], 'top'), ('right folded edge', [0.8, 0, 1, 1], 'right'), ('lower cloth hem', [0, 0.6, 1, 1], 'bottom')], '6cape4': [('left cloth tip', [0, 0, 0.2, 1], 'left'), ('upper fold crest', [0, 0, 1, 0.4], 'top'), ('right folded edge', [0.8, 0, 1, 1], 'right'), ('lower cloth hem', [0, 0.6, 1, 1], 'bottom')], '6cape5': [('left cloth tip', [0, 0, 0.2, 1], 'left'), ('upper fold crest', [0, 0, 1, 0.4], 'top'), ('right folded edge', [0.8, 0, 1, 1], 'right'), ('lower cloth hem', [0, 0.6, 1, 1], 'bottom')], '6nwcape': [('left cloth tip', [0, 0, 0.2, 1], 'left'), ('upper fold crest', [0, 0, 1, 0.4], 'top'), ('right folded edge', [0.8, 0, 1, 1], 'right'), ('lower cloth hem', [0, 0.6, 1, 1], 'bottom')], '7item109': [('left cloth tip', [0, 0, 0.2, 1], 'left'), ('upper fold crest', [0, 0, 1, 0.4], 'top'), ('right folded edge', [0.8, 0, 1, 1], 'right'), ('lower cloth hem', [0, 0.6, 1, 1], 'bottom')], '7item325': [('left cloth tip', [0, 0, 0.2, 1], 'left'), ('upper fold crest', [0, 0, 1, 0.4], 'top'), ('right folded edge', [0.8, 0, 1, 1], 'right'), ('lower cloth hem', [0, 0.6, 1, 1], 'bottom')], '7item330': [('left cloth tip', [0, 0, 0.2, 1], 'left'), ('upper fold crest', [0, 0, 1, 0.4], 'top'), ('right folded edge', [0.8, 0, 1, 1], 'right'), ('lower cloth hem', [0, 0.6, 1, 1], 'bottom')]}

def point(im, box, mode):
    a = np.array(im)
    mask = a[:, :, 3] >= 128
    r, g, b = [a[:, :, i].astype(float) for i in range(3)]
    if mode == 'purple':
        mask &= (b > g + 20) & (r > g + 20)
    elif mode == 'bright':
        mask &= (r > 155) & (g > 155) & (b > 135)
    elif mode == 'blue':
        mask &= (b > r + 20) & (b > g + 20)
    elif mode == 'green':
        mask &= (g > r + 5) & (g > b)
    elif mode == 'orange':
        mask &= (r > g * 1.4) & (r > b * 2) & (r > 80)
    x0, y0, x1, y1 = [round(v * (im.width if i % 2 == 0 else im.height)) for i, v in enumerate(box)]
    yy, xx = np.nonzero(mask[y0:y1, x0:x1])
    assert len(xx), 'No measured feature'
    xx, yy = xx + x0, yy + y0
    if mode in ('top', 'bottom', 'left', 'right'):
        values = yy if mode in ('top', 'bottom') else xx
        edge = values.min() if mode in ('top', 'left') else values.max()
        selected = values == edge
        xx, yy = xx[selected], yy[selected]
    return [float(xx.mean()), float(yy.mean())]


if __name__ == '__main__':
    records = {}
    proof = Image.new('RGB', (1950, 1200), '#555555')
    for i, row in enumerate(json.loads((OUT / 'manifest.json').read_text())['rows']):
        m = row['member']
        name = Path(m['source_path']).stem
        comparison = Image.open(OUT / 'registration' / (m['id'] + '-item.png'))
        proof.paste(comparison, (i % 3 * 650, i // 3 * 400))
        with Image.open(ROOT / m['source_path']) as im:
            native = rendered(im, 'item').resize(tuple(m['export_region'][2:]), Image.Resampling.NEAREST)
        restored = Image.open(OUT / (name + '.png')).convert('RGBA')
        landmarks = []
        for feature, region, mode in FEATURES[name]:
            a, b = point(native, region, mode), point(restored, region, mode)
            landmarks.append(dict(name=feature, source_xy=[v / 2 for v in a], restored_xy=b,
                window=region, measurement=mode, max_error_x2=max(abs(x-y) for x, y in zip(a, b))))
        records[name] = landmarks
    proof.save(OUT / 'registration-all.png')
    (OUT / 'measured-landmarks.json').write_text(json.dumps(records, indent=2) + '\n')
    print(json.dumps({n: [(p['name'], p['max_error_x2']) for p in ps] for n, ps in records.items()}, indent=2))
