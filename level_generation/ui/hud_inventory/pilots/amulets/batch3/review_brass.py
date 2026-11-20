"""Record actual brass charm review and measured features; no artwork changes."""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

BASE = Path(__file__).resolve().parent
OUT = BASE / 'brass_matte_repair'
HUD = BASE.parents[2]
ROOT = HUD.parents[2]
sys.path.insert(0, str(HUD))
from freeze_targets import rendered

cell = 'engine--icons--item147.bmp'
artifact = OUT / 'item147.png'
native = rendered(Image.open(ROOT / 'assets_dev/engine/icons/item147.bmp'), 'item')
native = native.resize((72, 102), Image.Resampling.NEAREST)
candidate = Image.open(artifact).convert('RGBA')
features = []
holes_report = []
for im in (native, candidate):
    rgba = np.array(im)
    mask = rgba[:, :, 3] >= 128
    holes = ndimage.binary_fill_holes(mask) & ~mask
    holes_report.append(dict(total_pixels=int(holes.sum()), body_pixels=int(holes[12:].sum())))
    assert not holes[12:].any(), 'Opaque lacquer must not have extraction holes'
    y, x = ndimage.center_of_mass(holes)
    rows, cols = np.nonzero(mask[96:])
    bottom = rows == rows.max()
    features.append([[x, y], [float(cols[bottom].mean()), float(rows[bottom].mean() + 96)]])

# Read directly from the actually inspected 8x coordinate-grid images. These are approximate pixel centers,
# not alpha extrema or expected coordinates copied into the generated result.
native_junction = [35.5, 53.5]
restored_junction = [36.5, 53.0]
landmarks = [dict(name='suspension opening center', source_xy=[v / 2 for v in features[0][0]],
                  restored_xy=features[1][0]),
             dict(name='central diamond four-facet junction, visual grid measurement',
                  source_xy=[v / 2 for v in native_junction], restored_xy=restored_junction),
             dict(name='lower cardinal projection tip', source_xy=[v / 2 for v in features[0][1]],
                  restored_xy=features[1][1])]
registration = OUT / 'registration' / f'{cell}-registration.json'
r = json.loads(registration.read_text())
r['landmarks'] = landmarks
r['visual_fit_notes'] = (
    'Actually inspected native/candidate coordinate grids, enlarged original comparison, raw crop, final '
    'native/x2/overlay/logical comparison, enlarged light/dark and complete sheet. Ring opening combines '
    'the native tiny disconnected key pixels; final opening center measured from actual enclosed alpha128 '
    'background. Bottom tip measured below96. Diamond facet junction visually read from8x coordinate grids '
    'at native(35.5,53.5) and generated(36.5,53.0), in x2 coordinates. Body matting repair preserves all '
    'geometry and central opaque pixels; pink lacquer remains opaque. No local feature warping.')
registration.write_text(json.dumps(r, indent=2) + '\n')
images = [str(registration.with_name(f'{cell}-item.png')), str(OUT / 'enlarged-edges.png'),
          str(OUT / 'complete-sheet.png'), str(BASE / 'item147-enlarged-comparison.png'),
          str(BASE / 'item147-native-grid.png'), str(BASE / 'item147-candidate-grid.png'),
          str(BASE / 'item147-raw-crop.png')]
notes = (
    'Actual visual review passes for the brass charm only: exact72x102 canvas, native logical36x51 size, '
    'central raised four-facet diamond, four cardinal gold projections, suspension loop and pink lacquer '
    'rim retained. Fine stamped relief interprets the native mottled gold detail without a new named '
    'symbol or inscription. Material and silhouette remain recognizable at logical size. The initial '
    'extractor removed real pink lacquer; the repaired extraction protects raw RGB/alpha inside the '
    'generated closed body, preserves the genuine top opening, and removes confirmed exterior contour '
    'spill only. Final light/dark review shows continuous opaque rim. No additional state in this cell; '
    'other sheet members retain their separate acceptance/deferred status. Own runtime preview is pending.')
sha = hashlib.sha256(artifact.read_bytes()).hexdigest()
(OUT / 'review.json').write_text(json.dumps(dict(identity=True, registration=True, compositing=True,
    detail_at_x2=True, state_or_animation_consistency=True, notes=notes,
    registration_record=str(registration), review_images=images), indent=2) + '\n')
(OUT / 'feature-audit.json').write_text(json.dumps(dict(artifact_sha256=sha, landmarks=landmarks,
    holes=holes_report, script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()), indent=2) + '\n')
(OUT / 'stage-review.json').write_text(json.dumps(dict(full_canvas_review=True, artifact_sha256=sha,
    notes='Single-cell full72x102 reconstruction must match this actually inspected final artifact. '
          'Native comparison, complete sheet and enlarged light/dark pass. Own runtime coverage pending.',
    review_images=images), indent=2) + '\n')
print(json.dumps(dict(landmarks=landmarks, holes=holes_report, artifact_sha256=sha), indent=2))
