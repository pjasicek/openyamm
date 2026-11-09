"""Measure visually identified extremities independently in native and generated art; never move pixels."""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(OUT.parents[1]))
from freeze_targets import rendered
from finalize_classification import ROOT

# Normalized search windows identify the observed feature, not its expected coordinate.
FEATURES = {
    '6helm3': [('left wing tip', [0, 0, .3, .5], 'top'),
               ('central spike', [.35, 0, .65, .4], 'top'), ('right wing tip', [.7, 0, 1, .5], 'top')],
    '6helm4': [('left horn tip', [0, 0, .3, .5], 'top'),
               ('right horn tip', [.7, 0, 1, .5], 'top'), ('left cheek foot', [.1, .75, .4, 1], 'bottom')],
    '6helm5': [('central ridge tip', [.35, 0, .65, .4], 'top'),
               ('left swept tip', [0, 0, .3, .5], 'top'), ('right swept tip', [.7, 0, 1, .5], 'top')],
    '7item090': [('apex spike', [.3, 0, .7, .4], 'top'),
                 ('left rim extent', [0, .6, .4, 1], 'left'), ('right rim extent', [.6, .6, 1, 1], 'right')],
    '7item091': [('dome apex', [.2, 0, .8, .3], 'top'),
                 ('left mail foot', [0, .65, .4, 1], 'bottom'), ('right mail foot', [.7, .65, 1, 1], 'bottom')],
    '7item092': [('left horn tip', [0, 0, .25, .5], 'left'),
                 ('left cheek foot', [0, .7, .4, 1], 'bottom'), ('right cheek foot', [.5, .7, 1, 1], 'bottom')],
    '7item093': [('gold apex', [.3, 0, .6, .4], 'top'),
                 ('left horn tip', [0, 0, .25, .65], 'top'), ('right horn tip', [.75, 0, 1, .65], 'top')],
    '7item094': [('feather tip', [.65, 0, 1, .4], 'top'),
                 ('left brim extent', [0, .4, .3, 1], 'left'), ('lower brim', [.1, .7, .7, 1], 'bottom')],
}


def point(im, window, mode):
    a = np.array(im.getchannel('A')) >= 128
    x0, y0, x1, y1 = [round(v * (im.width if i % 2 == 0 else im.height)) for i, v in enumerate(window)]
    yy, xx = np.nonzero(a[y0:y1, x0:x1])
    xx, yy = xx + x0, yy + y0
    values = yy if mode in ('top', 'bottom') else xx
    edge = values.min() if mode in ('top', 'left') else values.max()
    selected = values == edge
    return [float(xx[selected].mean()), float(yy[selected].mean())]


records = {}
for row in json.loads((OUT / 'manifest.json').read_text())['rows']:
    m = row['member']
    name = Path(m['source_path']).stem
    if name not in FEATURES:
        continue
    with Image.open(ROOT / m['source_path']) as im:
        native = rendered(im, 'item').resize(tuple(m['export_region'][2:]), Image.Resampling.NEAREST)
    restored = Image.open(OUT / (name + '.png')).convert('RGBA')
    landmarks = []
    for feature, region, mode in FEATURES[name]:
        source, dest = point(native, region, mode), point(restored, region, mode)
        landmarks.append(dict(name=feature, source_xy=[v / 2 for v in source], restored_xy=dest,
                              window=region, measurement=mode + ' opaque extremity',
                              max_error_x2=max(abs(a-b) for a, b in zip(source, dest))))
    records[name] = landmarks
(OUT / 'measured-landmarks.json').write_text(json.dumps(records, indent=2) + '\n')
print(json.dumps({n: [(p['name'], p['max_error_x2']) for p in ps] for n, ps in records.items()}, indent=2))
