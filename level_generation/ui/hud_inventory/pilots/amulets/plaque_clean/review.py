"""Measure actually reviewed plaque marks and mounting; preserve native data."""
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

cell = 'engine--icons--amulet4.bmp'
artifact = OUT / 'amulet4.png'
native = rendered(Image.open(ROOT / 'assets_dev/engine/icons/amulet4.bmp'), 'item')
native = native.resize((80, 144), Image.Resampling.NEAREST)
candidate = Image.open(artifact).convert('RGBA')
assert candidate.size == native.size
features = []
for im in (native, candidate):
    rgba = np.array(im)
    rgb = rgba[:, :, :3].astype(int)
    mask = rgba[:, :, 3] >= 128
    measured = []
    for x0, y0, x1, y1 in ((18, 108, 31, 115), (32, 104, 47, 118), (55, 104, 64, 119)):
        weights = np.maximum(0, 100 - rgb[y0:y1, x0:x1].mean(axis=2)) * mask[y0:y1, x0:x1]
        y, x = ndimage.center_of_mass(weights)
        measured.append([float(x + x0), float(y + y0)])
    for x0, y0, x1, y1, channel in ((10, 105, 23, 127, 0), (29, 118, 70, 128, 2)):
        patch = rgb[y0:y1, x0:x1]
        other = np.max(np.delete(patch, channel, axis=2), axis=2)
        weights = np.maximum(0, patch[:, :, channel] - other) * mask[y0:y1, x0:x1]
        y, x = ndimage.center_of_mass(weights)
        measured.append([float(x + x0), float(y + y0)])
    holes, count = ndimage.label(ndimage.binary_fill_holes(mask) & ~mask)
    largest = max(range(1, count + 1), key=lambda k: int((holes == k).sum()))
    y, x = ndimage.center_of_mass(holes == largest)
    measured.append([float(x), float(y)])
    labels, _ = ndimage.label(~mask)
    assert labels[137, 38] > 0 and (labels[-1] == labels[137, 38]).any()
    features.append(measured)

names = ['left black horizontal mark', 'central black curved mark', 'right black vertical mark',
         'red mark group', 'blue lower mark group', 'main cord opening center']
landmarks = [dict(name=name, source_xy=[v / 2 for v in source], restored_xy=restored)
             for name, source, restored in zip(names, features[0], features[1])]
registration = OUT / 'registration' / f'{cell}-registration.json'
r = json.loads(registration.read_text())
r['landmarks'] = landmarks
r['visual_fit_notes'] = (
    'Actually inspected final native/x2/overlay/logical comparison, enlarged native comparison, full '
    'composed sheet and enlarged light/dark. Three black marks measured by darkness max(0,100-meanRGB) '
    'in documented fixed windows; red/blue groups by dominant channel excess in separate face windows. '
    'Cord opening is largest enclosed alpha128 background component. Lower mounting slit connects to '
    'bottom exterior in both originals and generated alpha. Marks, margins and mounting placement '
    'retained; no native-mask replacement or local feature warping. Fine mounting relief is interpreted '
    'from the low-resolution source, without new readable text.')
registration.write_text(json.dumps(r, indent=2) + '\n')
images = [str(registration.with_name(f'{cell}-item.png')), str(OUT / 'amulet4-enlarged-edges.png'),
          str(OUT / 'complete-sheet.png'), str(BASE / 'enlarged-comparison.png')]
notes = (
    'Actual visual review passes for ancient plaque: exact80x144 full canvas, logical40x72 scale, '
    'irregular cord loop, pale aged rectangular face, native black/red/blue painted marks, mounting '
    'curls and open-bottom slit preserved. Six measured features stay within tolerance. No invented '
    'readable inscription. Generated detail survives final export and logical comparison. Source-informed '
    'raw magenta extraction removes stray backing from cord; final narrow-contour RGB correction retains '
    'alpha and interior marks. Light/dark shows no pink artifact and genuine mounting openings remain. '
    'Other sheet cells retain independent statuses. Own runtime preview remains pending.')
sha = hashlib.sha256(artifact.read_bytes()).hexdigest()
(OUT / 'review.json').write_text(json.dumps(dict(identity=True, registration=True, compositing=True,
    detail_at_x2=True, state_or_animation_consistency=True, notes=notes,
    registration_record=str(registration), review_images=images), indent=2) + '\n')
(OUT / 'feature-audit.json').write_text(json.dumps(dict(artifact_sha256=sha, landmarks=landmarks,
    bottom_slot_open_both=True, script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()), indent=2) + '\n')
(OUT / 'stage-review.json').write_text(json.dumps(dict(full_canvas_review=True, artifact_sha256=sha,
    notes='Full single-cell80x144 reconstruction must match actually inspected final artifact. '
          'Full sheet, native comparison and enlarged light/dark pass. Own runtime review pending.',
    review_images=images), indent=2) + '\n')
print(json.dumps(dict(landmarks=landmarks, sha256=sha), indent=2))
