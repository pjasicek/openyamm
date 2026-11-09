"""Refine this reviewed blue-only master's mask; retain original RGB and AI masks."""
import json
from pathlib import Path

import numpy as np
from PIL import Image

root = Path(__file__).resolve().parents[1]
source = root / 'results/g16963_v0_s0/attempt_03'
rgb = np.asarray(Image.open(source / 'raw.png').convert('RGB'), dtype=float) / 255
mask = np.asarray(Image.open(source / 'mask.png').convert('L'), dtype=float) / 255
# The reviewed subject contains blue/cyan/navy, with no magenta material.
# Correct exact/near-exact magenta gaps and physically impossible underestimates.
matte = ((rgb[:, :, 0] > rgb[:, :, 1] + 40/255)
         & (rgb[:, :, 2] > rgb[:, :, 1] + 40/255)
         & (rgb[:, :, 0] > 60/255))
minimum = np.maximum.reduce([1-rgb[:, :, 0], rgb[:, :, 1], 1-rgb[:, :, 2]])
alpha = np.maximum(mask, minimum)
alpha[matte] = 0
destination = root / 'audit/g16963_refined_mask_v2.png'
Image.fromarray(np.rint(alpha * 255).astype('uint8')).save(destination)
destination.with_suffix('.json').write_text(json.dumps({
    'source': str(source), 'matte_pixels': int(matte.sum()),
    'method': 'reviewed blue-only material; magenta gaps zeroed; feasible-alpha floor',
    'limitation': 'Floor is not proof of correct opacity; inspect light/dark results.'
}, indent=2) + '\n')
print(destination)
