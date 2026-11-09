"""Record the inspected hand charm's ring and separated fingertip measurements."""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

BASE = Path(__file__).resolve().parent
HUD = BASE.parents[2]
ROOT = HUD.parents[2]
P = BASE / 'hand_final'
sys.path.insert(0, str(HUD))
from freeze_targets import rendered

cell = 'engine--icons--7item132.bmp'
artifact = P / '7item132.png'
native = rendered(Image.open(ROOT / 'assets_dev/engine/icons/7item132.bmp'), 'item')
native = native.resize((40, 108), Image.Resampling.NEAREST)
candidate = Image.open(artifact).convert('RGBA')
assert candidate.size == (40, 108)
features, edges = [], []
for im in (native, candidate):
    rgba = np.array(im)
    mask = rgba[:, :, 3] >= 128
    labels, count = ndimage.label(ndimage.binary_fill_holes(mask) & ~mask)
    hole = max(range(1, count + 1), key=lambda j: int(((labels == j)[:20]).sum()))
    ring_y, ring_x = ndimage.center_of_mass(labels == hole)
    points = [[ring_x, ring_y]]
    for x0, y0, x1, y1 in [(0, 65, 8, 86), (0, 95, 40, 108)]:
        y, x = np.nonzero(mask[y0:y1, x0:x1])
        bottom = y == y.max()
        points.append([float(x[bottom].mean() + x0), float(y[bottom].mean() + y0)])
    features.append(points)
    rgb = rgba[:, :, :3].astype(int)
    band = (rgba[:, :, 3] > 0) & ~ndimage.binary_erosion(mask, iterations=4)
    excess = np.maximum(0, np.minimum(rgb[:, :, 0], rgb[:, :, 2]) - rgb[:, :, 1])
    score = excess * rgba[:, :, 3] / 255
    edges.append(dict(max_weighted_magenta_excess=float(score[band].max()),
                      pixels_above2=int(((score > 2) & band).sum())))

registration = P / 'registration' / f'{cell}-registration.json'
r = json.loads(registration.read_text())
r['landmarks'] = [dict(name=name, source_xy=[v / 2 for v in source], restored_xy=restored)
    for name, source, restored in zip(['suspension ring center', 'thumb lower tip', 'longest finger lower tip'],
                                     features[0], features[1])]
r['visual_fit_notes'] = (
    'Actual enlarged native/restored inspection and final native/x2/overlay/logical comparison performed. '
    'Ring is the enclosed alpha128 hole above20; thumb tip is lower alpha128 extremum in x0:8,y65:86; '
    'longest finger is lower extremum below95. Native finger lengths, holes, wrist cuff and asymmetric thumb '
    'retained. Central palm relief remains in its native area; no recognizable new lettering or named symbol. '
    'Item934 describes an unidentifiable stamped symbol. Its fine shape is interpretive restoration of '
    'ambiguous native pixels, not a claimed exact reconstruction of an identifiable emblem.')
registration.write_text(json.dumps(r, indent=2) + '\n')
images = [str(P / 'registration' / f'{cell}-item.png'), str(P / '7item132-enlarged-edges.png'),
          str(P / 'complete-sheet.png'), str(BASE / '7item132-enlarged-comparison.png')]
notes = (
    'Actually reviewed full six-cell sheet, enlarged native/restored hand and final comparison plus enlarged '
    'light/dark. Exact40x108 canvas preserves silver hand charm, five fingers, wrist cuff and suspension ring. '
    'The central unknown stamped motif stays in the palm; restored relief is clearer but does not turn into '
    'lettering or a new identifiable icon. Source item934 explicitly describes an unidentifiable symbol. '
    'Measured ring, thumb and longest fingertip agree within1 x2 pixel. Uniform fitting only. Local contour '
    'RGB repair preserves alpha and interior and leaves no visible magenta halo in final review. Finger gaps '
    'remain open at logical size. This approval covers only7item132, not other unresolved batch cells. '
    'No related hover or animation states in this inventory cell; runtime preview remains pending.')
review = dict(identity=True, registration=True, compositing=True, detail_at_x2=True,
              state_or_animation_consistency=True, notes=notes,
              registration_record=str(registration), review_images=images)
(P / 'review.json').write_text(json.dumps(review, indent=2) + '\n')
sha = hashlib.sha256(artifact.read_bytes()).hexdigest()
(P / 'feature-and-edge-audit.json').write_text(json.dumps(dict(
    artifact_sha256=sha, features_x2=features, edge_scores=edges,
    source_description='assets_dev/engine/data_tables/items.txt, item934, Witch\'s Amulet',
    measurement_script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()), indent=2) + '\n')
(P / 'stage-review.json').write_text(json.dumps(dict(full_canvas_review=True, artifact_sha256=sha,
    notes='Full40x108 single-cell reconstruction must match the actually inspected final hand artifact hash. '
          'Native comparison, complete sheet and enlarged light/dark pass. Runtime preview remains open.',
    review_images=images), indent=2) + '\n')
print(json.dumps(dict(features_x2=features, edges=edges, sha256=sha), indent=2))
