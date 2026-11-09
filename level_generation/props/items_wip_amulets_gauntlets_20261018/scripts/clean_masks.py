"""Quantize semantic masks and replace unwanted thin outline strokes with neighbouring declared classes."""
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt

P = Path(__file__).resolve().parents[1]
PALETTE = np.array([(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (0, 0, 0)])
designs = json.loads((P / 'designs.json').read_text())
for name in sys.argv[1:]:
    path = P / 'codex_tex' / name / 'mask_atlas.png'
    raw = path.with_name('mask_raw.png')
    if not raw.exists():
        raw.write_bytes(path.read_bytes())
    rgba = np.array(Image.open(raw).convert('RGBA'))
    classes = np.sum((rgba[..., None, :3].astype(float) - PALETTE) ** 2, axis=-1).argmin(-1)
    opaque = rgba[..., 3] > 127
    black = (classes == 4) & opaque
    notes = designs[name].get('mask_notes', '')
    allowed = [0, 1]
    if 'CLOTH BLUE' in notes:
        allowed.append(2)
    if 'HORN YELLOW' in notes:
        allowed.append(3)
    if 'GEM BLACK' in notes:
        allowed.append(4)
    distances = np.sum((rgba[..., None, :3].astype(float) - PALETTE[allowed]) ** 2, axis=-1)
    declared = np.array(allowed)[distances.argmin(-1)]
    reclassified = opaque & ~black & (classes != declared)
    classes[~black] = declared[~black]
    keep_black = black & (distance_transform_edt(black) >= 3) if 'GEM BLACK' in notes else np.zeros_like(black)
    invalid = black & ~keep_black
    valid = opaque & ~black
    assert valid.any(), name
    indices = distance_transform_edt(~valid, return_distances=False, return_indices=True)
    classes[invalid] = classes[tuple(indices[:, invalid])]
    rgba[..., :3] = PALETTE[classes]
    Image.fromarray(rgba).save(path)
    print(name, 'removed outline pixels', int(invalid.sum()), 'retained gem pixels', int(keep_black.sum()),
          'undeclared class corrections', int(reclassified.sum()))
