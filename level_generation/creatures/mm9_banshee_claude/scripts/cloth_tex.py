#!/usr/bin/env python3
"""Cloak and hair textures from the Codex swatches. Cloak: u centre->wrist, v root->rim, mirrored on both sides, alpha fades A_ROOT -> A_RIM and the rim is torn (tears.py). Normal from the cloth's brightness, roughness flat, no metal.
Hair: strands, alpha falling to the tips; recoloured by ramps. Writes textures/banshee_cloth_rgba.png, banshee_cloth_normal.png, banshee_cloth_mr.png, banshee_hair_rgba.png. Run from the project folder."""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, 'scripts')
import tears
A_ROOT, A_RIM = 0.66, 0.34
A_HAIR, A_TIP = 0.96, 0.72
T = Path('textures')
c = Image.open('references_swatch/cloth.png').convert('RGB').resize((1024, 1024), Image.LANCZOS)
rgb = np.asarray(c, np.float32) / 255
lum = rgb @ np.array([0.3, 0.59, 0.11])
S_ = 1024
E = tears.tear_field(S_, S_, 5, depth=0.075, periodic=False, holes=7)
cut = np.clip((E + 2) / 4, 0, 1)
v = (np.arange(S_) + 0.5) / S_
k = np.clip(v / 0.9, 0, 1); k = k * k * (3 - 2 * k)
a = (A_ROOT * (1 - k) + A_RIM * k)[:, None] * cut * (0.6 + 0.4 * np.clip(E / 60, 0, 1))
# the torn edge is scorched
edge = np.clip(1 - E / 26, 0, 1)[..., None] * 0.75
rgb2 = rgb * (1 - edge) + rgb * 0.25 * edge
Image.fromarray(np.dstack([(rgb2 * 255 + 0.5).astype(np.uint8), (a * 255 + 0.5).astype(np.uint8)]), 'RGBA').save(T / 'banshee_cloth_rgba.png')
h = ndimage.gaussian_filter(lum, 1.2)
gx = ndimage.sobel(h, axis=1) * 2.2; gy = ndimage.sobel(h, axis=0) * 2.2
n = np.dstack([-gx, gy, np.ones_like(h)]); n /= np.linalg.norm(n, axis=2, keepdims=True)
Image.fromarray(((n * 0.5 + 0.5) * 255 + 0.5).astype(np.uint8)).resize((512, 512), Image.LANCZOS).save(T / 'banshee_cloth_normal.png')
Image.merge('RGB', [Image.new('L', (64, 64), 255), Image.new('L', (64, 64), 235), Image.new('L', (64, 64), 0)]).save(T / 'banshee_cloth_mr.png')
hair = Image.open('references_swatch/hair.png').convert('RGB').resize((512, 512), Image.LANCZOS)
hrgb = np.asarray(hair, np.uint8)
yy = (np.arange(512) + 0.5) / 512
ah = A_TIP + (A_HAIR - A_TIP) * np.clip(yy / 0.45, 0, 1)
Image.fromarray(np.dstack([hrgb, np.repeat((ah[:, None] * 255).astype(np.uint8), 512, 1)]), 'RGBA').save(T / 'banshee_hair_rgba.png')
print('CLOTH alpha mean', float(a.mean()))
