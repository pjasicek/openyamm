#!/usr/bin/env python3
"""Look pass on the graded maps, no repaint (Zombie's soft_detail route): the 1.2-9 px pebble band cut on skin ('lizard' hide), normal maps flattened; rope toned from Meshy's yellow to MM9's tan.
Writes textures/thrall_torso_{a,b,c}_soft.png, thrall_limbs_{a,b,c}_soft.png, normals in place of the *_normal files from *_normal_raw copies."""
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
T = Path('textures')
TONE = {'a': 0.90, 'b': 0.95, 'c': 1.0}
def gauss(a, s): return np.stack([ndimage.gaussian_filter(a[..., c], s) for c in range(3)], -1)
def hsv(a):
    mx, mn = a.max(2), a.min(2); s = (mx - mn) / np.maximum(mx, 1e-6); r, g, b = a[..., 0], a[..., 1], a[..., 2]
    return np.degrees(np.arctan2(np.sqrt(3) * (g - b), 2 * r - g - b)) % 360, s, mx
def proc(p, out, tone=1.0):
    a = np.asarray(Image.open(p).convert('RGB'), np.float32) / 255
    h, s, v = hsv(a)
    skin = (h > 12) & (h < 33) & (s > 0.3) & (v > 0.3)
    skin = ndimage.gaussian_filter(ndimage.binary_opening(ndimage.binary_closing(skin, iterations=3), iterations=2).astype(np.float32), 2.0)[..., None]
    lo = gauss(a, 9); mid = gauss(a, 1.2)
    soft = lo + (mid - lo) * 0.6 + (a - mid) * 0.8
    a = a * (1 - skin * 0.85) + soft * skin * 0.85
    h, s, v = hsv(a)
    rope = ndimage.gaussian_filter(((h > 33) & (h < 52) & (s > 0.35) & (v > 0.5)).astype(np.float32), 1.0)[..., None]
    g = a.mean(2, keepdims=True); roped = (g + (a - g) * 0.8) * 0.8
    a = a * (1 - rope) + roped * rope
    a = a * (1 - skin * (1 - tone))
    Image.fromarray((np.clip(a, 0, 1) * 255 + .5).astype('u1')).save(out)
for t in 'abc':
    proc(T / f'thrall_torso_{t}_raw_graded.png', T / f'thrall_torso_{t}_final.png', TONE[t])
    proc(T / f'thrall_limbs_{t}_raw_graded.png', T / f'thrall_limbs_{t}_soft.png', TONE[t])
def flatten(p, k):
    q = Path(str(p).replace('_normal', '_normal_raw'))
    if not q.exists(): q.write_bytes(p.read_bytes())
    a = np.asarray(Image.open(q).convert('RGB'), np.float32) / 127.5 - 1
    a[..., :2] *= k; a /= np.maximum(np.linalg.norm(a, axis=2, keepdims=True), 1e-6)
    Image.fromarray(((a + 1) * 127.5 + .5).astype('u1')).save(p)
for t in 'abc': flatten(T / f'thrall_torso_{t}_normal.png', 0.55)
flatten(T / 'thrall_limbs_normal.png', 0.45)
print('SOFT done')
