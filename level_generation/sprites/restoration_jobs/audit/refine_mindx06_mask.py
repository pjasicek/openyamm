"""Local reviewed mask repair for violet-rimmed lights; keeps RGB immutable."""
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

root = Path(__file__).resolve().parents[1]
source = root / 'results/g17110_v0_s0/attempt_02'
rgb = np.asarray(Image.open(source / 'raw.png').convert('RGB'), dtype=float) / 255
mask = np.asarray(Image.open(source / 'mask.png').convert('L'), dtype=float) / 255
distance = np.maximum.reduce([1-rgb[:, :, 0], rgb[:, :, 1], 1-rgb[:, :, 2]])
# This specific master contains yellow/white lights and dark violet rims, but no
# bright magenta material. Preserve full violet extents rather than AI core masks.
background = distance < .035
material = distance > .30
alpha = np.maximum(mask, distance)
alpha[material] = 1
alpha[background] = 0
destination = root / 'audit/g17110_refined_mask.png'
Image.fromarray(np.rint(alpha * 255).astype('uint8')).save(destination)
destination.with_suffix('.json').write_text(json.dumps({
    'source': str(source),
    'raw_sha256': hashlib.sha256((source / 'raw.png').read_bytes()).hexdigest(),
    'method': 'Reviewed violet/white/yellow material mask repair, feasible edge alpha, near-magenta background zeroed',
    'background_distance': .035, 'opaque_material_distance': .30,
    'limitation': 'Local estimate, requires light/dark review; not a generic FX mask.'
}, indent=2) + '\n')
print(destination)
