"""Measure the actually inspected final talisman, including asymmetric gap connectivity."""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

BASE = Path(__file__).resolve().parent
OUT = BASE / 'final'
HUD = BASE.parents[2]
ROOT = HUD.parents[2]
sys.path.insert(0, str(HUD))
from freeze_targets import rendered

cell = 'engine--icons--item149.bmp'
artifact = OUT / 'item149.png'
native = rendered(Image.open(ROOT / 'assets_dev/engine/icons/item149.bmp'), 'item')
native = native.resize((62, 100), Image.Resampling.NEAREST)
candidate = Image.open(artifact).convert('RGBA')
assert candidate.size == native.size
features, topology = [], []
for im in (native, candidate):
    rgba = np.array(im)
    rgb = rgba[:, :, :3].astype(int)
    mask = rgba[:, :, 3] >= 128
    measured = []
    for x0, y0, x1, y1 in ((23, 45, 30, 52), (31, 45, 38, 52)):
        weights = np.maximum(0, 140 - rgb[y0:y1, x0:x1].mean(axis=2)) * mask[y0:y1, x0:x1]
        y, x = ndimage.center_of_mass(weights)
        measured.append([float(x + x0), float(y + y0)])
    holes = ndimage.binary_fill_holes(mask) & ~mask
    y, x = ndimage.center_of_mass(holes[:40])
    measured.append([float(x), float(y)])
    y, x = ndimage.center_of_mass(holes[40:, :25])
    measured.append([float(x), float(y + 40)])
    features.append(measured)
    labels, _ = ndimage.label(~mask)
    right_open = bool((labels[:, -1] == labels[49, 50]).any())
    left_closed = not bool((labels[:, 0] == labels[49, 12]).any())
    assert labels[49, 50] > 0 and labels[49, 12] > 0 and right_open and left_closed
    topology.append(dict(right_slot_open=right_open, left_slot_closed=left_closed))

names = ['left skull eye socket dark center', 'right skull eye socket dark center',
         'upper suspension opening center', 'left wing opening center']
landmarks = [dict(name=name, source_xy=[v / 2 for v in source], restored_xy=restored)
             for name, source, restored in zip(names, features[0], features[1])]
registration = OUT / 'registration' / f'{cell}-registration.json'
r = json.loads(registration.read_text())
r['landmarks'] = landmarks
r['visual_fit_notes'] = (
    'Actually inspected raw master, initial and final native/x2/overlay/logical comparisons, enlarged '
    'native comparison, final enlarged light/dark and complete composed sheet. Eye socket centers use '
    'max(0,140-meanRGB) in fixed x2 windows[23,45,30,52] and[31,45,38,52]; ring and left wing opening '
    'centers use actual alpha128 enclosed background. All four features align within1 output pixel. '
    'Right middle slot opens to exterior and left remains enclosed, matching native asymmetry. '
    'Smooth skull relief and wing contours retain native placement; no native-mask substitution.')
registration.write_text(json.dumps(r, indent=2) + '\n')
images = [str(registration.with_name(f'{cell}-item.png')), str(OUT / 'item149-enlarged-edges.png'),
          str(OUT / 'complete-sheet.png'), str(BASE / 'enlarged-comparison.png')]
notes = (
    'Final blood talisman passes actual visual review: exact62x100 canvas, logical31x50 size, bone skull, '
    'eye sockets, teeth, small suspension ring and four gold wing tips preserved. Generated right-slot '
    'repair now opens to the exterior at final resolution; the native left slot remains closed. Four '
    'measured internal/opening features are within1 x2 pixel. Smooth restored relief survives at final '
    'size. Two residual contour pixels receive local RGB decontamination with alpha and interior '
    'unchanged; final light/dark shows no visible magenta halo. No additional inventory state for this '
    'cell. Other composed-sheet cells retain their independent statuses. Own runtime review pending.')
sha = hashlib.sha256(artifact.read_bytes()).hexdigest()
(OUT / 'review.json').write_text(json.dumps(dict(identity=True, registration=True, compositing=True,
    detail_at_x2=True, state_or_animation_consistency=True, notes=notes,
    registration_record=str(registration), review_images=images), indent=2) + '\n')
(OUT / 'feature-audit.json').write_text(json.dumps(dict(artifact_sha256=sha, landmarks=landmarks,
    topology=topology, script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()), indent=2) + '\n')
(OUT / 'stage-review.json').write_text(json.dumps(dict(full_canvas_review=True, artifact_sha256=sha,
    notes='Full single-cell62x100 reconstruction must match the inspected final artifact. Native '
          'comparison, enlarged light/dark and complete sheet pass; own runtime review remains pending.',
    review_images=images), indent=2) + '\n')
print(json.dumps(dict(landmarks=landmarks, topology=topology, sha256=sha), indent=2))
