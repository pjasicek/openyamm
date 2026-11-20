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

FEATURES = {
    '6crown1': [('left leaf foot', [0, .4, .3, 1], 'bottom'),
                ('right leaf foot', [.7, .4, 1, 1], 'bottom'),
                ('dangling ornament foot', [.4, .25, .65, .7], 'bottom')],
    '6crown2': [('left band extent', [0, 0, .3, 1], 'left'),
                ('right band extent', [.7, 0, 1, 1], 'right'),
                ('blue gem center', [.2, .3, .65, 1], 'blue')],
    '6crown3': [('left back prong', [.15, 0, .35, .35], 'top'),
                ('central back prong', [.4, 0, .6, .35], 'top'),
                ('right back prong', [.65, 0, .85, .35], 'top')],
    '6hat1': [('cap apex', [.2, 0, .75, .5], 'top'),
              ('left brim', [0, .4, .3, 1], 'left'),
              ('right feather extent', [.7, 0, 1, .7], 'right')],
    '7item089': [('central spike', [.25, 0, .5, .4], 'top'),
                 ('left outer horn', [0, 0, .25, .6], 'top'),
                 ('right outer horn', [.75, 0, 1, .65], 'top')],
    '7item095': [('top knob', [.4, 0, .7, .4], 'top'),
                 ('left folded brim', [0, .3, .3, 1], 'left'),
                 ('right cap extent', [.7, 0, 1, 1], 'right')],
    '7item096': [('left cap extent', [0, 0, .3, 1], 'left'),
                 ('right cap extent', [.7, 0, 1, 1], 'right'),
                 ('green fastener center', [.1, 0, .5, .5], 'green')],
    '7item097': [('left crown extent', [0, 0, .3, 1], 'left'),
                 ('right crown extent', [.7, 0, 1, 1], 'right'),
                 ('orange gem center', [.2, .3, .6, .85], 'orange')],
}


def point(im, box, mode):
    a = np.array(im)
    mask = a[:, :, 3] >= 128
    r, g, b = [a[:, :, i].astype(float) for i in range(3)]
    if mode == 'blue':
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
    proof = Image.new('RGB', (1500, 900), '#555555')
    for i, row in enumerate(json.loads((OUT / 'manifest.json').read_text())['rows']):
        m = row['member']
        name = Path(m['source_path']).stem
        comparison = Image.open(OUT / 'registration' / (m['id'] + '-item.png'))
        proof.paste(comparison, (i % 3 * 500, i // 3 * 300))
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
