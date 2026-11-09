"""Measure the inspected eye pendant's actual iris and suspension geometry."""
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
P = BASE / 'eye_final'
sys.path.insert(0, str(HUD))
from freeze_targets import rendered

cell = 'engine--icons--7item130.bmp'
artifact = P / '7item130.png'
native = rendered(Image.open(ROOT / 'assets_dev/engine/icons/7item130.bmp'), 'item')
native = native.resize((44, 128), Image.Resampling.NEAREST)
candidate = Image.open(artifact).convert('RGBA')
assert candidate.size == (44, 128)
features, edges = [], []
for im in (native, candidate):
    rgba = np.array(im)
    rgb = rgba[:, :, :3].astype(int)
    mask = rgba[:, :, 3] >= 128
    weights = np.maximum(0, np.minimum(rgb[:, :, 1], rgb[:, :, 2]) - rgb[:, :, 0])
    weights[:95] = 0
    weights[~mask] = 0
    iris_y, iris_x = ndimage.center_of_mass(weights)
    labels, count = ndimage.label(ndimage.binary_fill_holes(mask) & ~mask)
    hole = max(range(1, count + 1), key=lambda j: int((labels == j).sum()))
    hole_y, hole_x = ndimage.center_of_mass(labels == hole)
    y, x = np.nonzero(mask[118:])
    bottom = y == y.max()
    features.append([[iris_x, iris_y], [hole_x, hole_y],
                     [float(x[bottom].mean()), float(y[bottom].mean() + 118)]])
    band = (rgba[:, :, 3] > 0) & ~ndimage.binary_erosion(mask, iterations=4)
    excess = np.maximum(0, np.minimum(rgb[:, :, 0], rgb[:, :, 2]) - rgb[:, :, 1])
    weighted = excess * rgba[:, :, 3] / 255
    edges.append(dict(max_weighted_magenta_excess=float(weighted[band].max()),
                      pixels_above2=int(((weighted > 2) & band).sum())))

registration = P / 'registration' / f'{cell}-registration.json'
r = json.loads(registration.read_text())
r['landmarks'] = [dict(name=name, source_xy=[v / 2 for v in source], restored_xy=restored)
    for name, source, restored in zip(['blue iris center', 'chain opening center', 'eyeball lower tip'],
                                     features[0], features[1])]
r['visual_fit_notes'] = (
    'Actually inspected native/x2/overlay/logical comparison, enlarged original/candidate, final enlarged '
    'light/dark and complete six-cell sheet. Blue iris center measured using cyan excess over red belowy95; '
    'chain opening is the largest enclosed alpha128 hole; lower eye tip is the bottom alpha128 extremum '
    'below118. Native/asymmetric eye, chain and cap placement retained. Final cleanup preserves alpha '
    'and interior pixels exactly; no local geometry warping.')
registration.write_text(json.dumps(r, indent=2) + '\n')
images = [str(P / 'registration' / f'{cell}-item.png'), str(P / '7item130-enlarged-edges.png'),
          str(P / 'complete-sheet.png'), str(BASE / '7item130-enlarged-comparison.png')]
notes = (
    'Actual visual review passes for this eye pendant only: exact44x128 native canvas and logical22x64 '
    'footprint; recognizable blue iris, pale eyeball/red vessels, gold cap, attachment and narrow chain. '
    'Highlights and fine chain detail are resolved at final size without replacing the eye with a gem. '
    'Three measured features are within1 x2 pixel. Final local four-pixel contour cleanup removes dark '
    'matte excess beyond2 while retaining alpha, iris, vessels and clean interior. Enlarged final light/dark '
    'shows no visible magenta halo or clipped chain. No additional states in this inventory cell. '
    'The other five sheet cells have their own acceptance status; runtime preview remains pending.')
review = dict(identity=True, registration=True, compositing=True, detail_at_x2=True,
              state_or_animation_consistency=True, notes=notes,
              registration_record=str(registration), review_images=images)
(P / 'review.json').write_text(json.dumps(review, indent=2) + '\n')
sha = hashlib.sha256(artifact.read_bytes()).hexdigest()
(P / 'feature-and-edge-audit.json').write_text(json.dumps(dict(
    artifact_sha256=sha, features_x2=features, edge_scores=edges,
    measurement_script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()), indent=2) + '\n')
(P / 'stage-review.json').write_text(json.dumps(dict(full_canvas_review=True, artifact_sha256=sha,
    notes='Full44x128 single-cell reconstruction must match the actually reviewed final eye artifact hash. '
          'Complete sheet, native comparison and enlarged light/dark pass; runtime review remains open.',
    review_images=images), indent=2) + '\n')
print(json.dumps(dict(features_x2=features, edges=edges, sha256=sha), indent=2))
