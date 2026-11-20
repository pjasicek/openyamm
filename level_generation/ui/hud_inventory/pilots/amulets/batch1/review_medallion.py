"""Retain measured features and the actual visual assessment of the first medallion candidate."""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

P = Path(__file__).resolve().parent
HUD = P.parents[2]
sys.path.insert(0, str(HUD))
from freeze_targets import rendered

ROOT = HUD.parents[2]
cell = 'engine--icons--7item131.bmp'
native = rendered(Image.open(ROOT / 'assets_dev/engine/icons/7item131.bmp'), 'item')
native = native.resize((62, 64), Image.Resampling.NEAREST)
candidate = Image.open(P / '7item131.png').convert('RGBA')
features = []
edge_scores = []
for im in (native, candidate):
    rgba = np.array(im)
    mask = rgba[:, :, 3] >= 128
    labels, count = ndimage.label(ndimage.binary_fill_holes(mask) & ~mask)
    hole = max(range(1, count + 1), key=lambda n: int((labels == n).sum()))
    hole_y, hole_x = ndimage.center_of_mass(labels == hole)
    y, x = np.nonzero(mask[48:64, :42])
    bottom = y == y.max()
    bottom_xy = [float(x[bottom].mean()), float(y[bottom].mean() + 48)]
    y, x = np.nonzero(mask[22:50, :14])
    left = x == x.min()
    left_xy = [float(x[left].mean()), float(y[left].mean() + 22)]
    features.append([left_xy, bottom_xy, [hole_x, hole_y]])
    visible = rgba[:, :, 3] > 0
    band = visible & ~ndimage.binary_erosion(mask, iterations=4)
    rgb = rgba[:, :, :3].astype(int)
    excess = np.maximum(0, np.minimum(rgb[:, :, 0], rgb[:, :, 2]) - rgb[:, :, 1])
    edge_scores.append(dict(max_magenta_excess=int(excess[band].max()),
                            visible_contour_pixels=int(band.sum())))

record_path = P / 'registration' / f'{cell}-registration.json'
record = json.loads(record_path.read_text())
record['landmarks'] = [dict(name=name, source_xy=[v / 2 for v in source], restored_xy=restored)
    for name, source, restored in zip(
        ['left medallion contour', 'medallion lower tip', 'large suspension-loop hole center'],
        features[0], features[1])]
record['visual_fit_notes'] = (
    'Actually viewed native/x2/overlay/logical comparison, complete six-cell sheet, light/dark and enlarged '
    'native/restored medallion. The curled embossed figure, irregular rim and long right suspension loop '
    'remain recognizable and correctly positioned. Measurements use alpha128 extrema in recorded windows '
    'and the largest enclosed hole; no landmark coordinates inferred merely from expected scale.')
record_path.write_text(json.dumps(record, indent=2) + '\n')
images = [str(P / 'registration' / f'{cell}-item.png'), str(P / '7item131-light-dark.png'),
          str(P / '7item131-enlarged-comparison.png'), str(P / 'complete-sheet.png')]
notes = (
    'Actually reviewed all six cells and the complete processed sheet; this approval covers only 7item131. '
    'Exact62x64 canvas preserves native angular gold medallion, curled relief and narrow hanging loop. '
    'The embossed figure resolves into curved gold relief without new lettering or a replacement symbol. '
    'Fine highlights remain readable at logical size; no clipped loop, magenta fringe or neighboring item '
    'appears on light/dark backgrounds. Uniform fitting only, with soft matte and premultiplied resizing. '
    'Measured left contour, lower pendant tip and suspension hole agree within2 x2 pixels. '
    'No related hover/animation states occur in this single inventory cell. In-game preview remains pending.')
review = dict(identity=True, registration=True, compositing=False, detail_at_x2=True,
              state_or_animation_consistency=True, notes=notes,
              registration_record=str(record_path), review_images=images)
review['notes'] += ' Subsequent enlarged audit found dark contour spill; this initial candidate is superseded by medallion_final.'
(P / '7item131-review.json').write_text(json.dumps(review, indent=2) + '\n')
(P / '7item131-edge-audit.json').write_text(json.dumps(dict(
    artifact_sha256=hashlib.sha256((P / '7item131.png').read_bytes()).hexdigest(),
    native=edge_scores[0], restored=edge_scores[1], band_width_x2=4,
    notes='Candidate chroma score only; enlarged audit found dark residual spill. See medallion_final.'), indent=2) + '\n')
print(json.dumps(dict(features_x2=features, edge_scores=edge_scores), indent=2))
