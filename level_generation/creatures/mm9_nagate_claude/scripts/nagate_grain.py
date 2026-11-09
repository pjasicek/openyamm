#!/usr/bin/env python3
"""Texture pass (2026-10-30): the 4K repaint reads grainier than the approved Nagate (pale stipple on head, legs and wing
cases). Run once after grade_basecolor.py, before the last compose_nagate.py; rewrites textures/nagate_basecolor_graded.png
(a new grade restores the input). Wing-grain method of mm9_wingedmutant_claude: per region, the log-luminance detail finer
than SIGMA texels is scaled so its amplitude on the surface is KEEP x the approved one at the same surface scale (hue and
edges stay). The eyes (no ramp, they keep the base colour) take the approved mean colour by a per-channel gain.
Inputs: work/before_texpass/textures (approved), textures, work/uv3d_nagate.npz, work/uv3d_nagate_v2.npz."""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import region_variants as RV

SIGMA = 6.0          # new texels (2K)
KEEP = 1.25          # detail kept above the approved amplitude (a sharper paint carries a little more, Wmut 1.25)
DENSITY = 989 / 1250  # approved / new median density at 2K, so one surface scale in both
REGIONS = {'wings': 0, 'chitin': 1, 'bands': 3}
W = np.array([0.2126, 0.7152, 0.0722])
B, T = HERE / 'work' / 'before_texpass' / 'textures', HERE / 'textures'


def encode(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


def detail(linear, sigma):
    log = np.log(np.maximum(linear @ W, 1e-4))
    return log - ndimage.gaussian_filter(log, sigma)


def sample(img, uv):
    h, w = img.shape[:2]
    return img[np.clip(((1 - uv[:, 1]) * h).astype(int), 0, h - 1), np.clip((uv[:, 0] * w).astype(int), 0, w - 1)]


new_lin = RV.srgb_to_linear(RV.load_srgb(T / 'nagate_basecolor_graded.png'))
old_lin = RV.srgb_to_linear(RV.load_srgb(B / 'nagate_basecolor_graded.png'))
mask = np.stack([np.asarray(c.resize((2048, 2048), Image.BILINEAR), np.float64) / 255
                 for c in Image.open(T / 'nagate_region_mask.png').convert('RGBA').split()], -1)
old, new = np.load(HERE / 'work' / 'uv3d_nagate.npz'), np.load(HERE / 'work' / 'uv3d_nagate_v2.npz')
xyz = new['xyz']
area = np.linalg.norm(np.cross(xyz[:, 1] - xyz[:, 0], xyz[:, 2] - xyz[:, 0]), axis=1) / 2
rng = np.random.default_rng(5)
n = 500000
face = rng.choice(len(area), n, p=area / area.sum())
bary = rng.dirichlet((1, 1, 1), n)[..., None]
p0, p1 = (old['uv'][face] * bary).sum(1), (new['uv'][face] * bary).sum(1)
d0, d1 = detail(old_lin, SIGMA * DENSITY), detail(new_lin, SIGMA)
s0, s1, region = sample(d0, p0), sample(d1, p1), sample(mask, p1)
scale = np.ones((2048, 2048))
for name, ch in REGIONS.items():
    core = region[:, ch] > 0.5
    a0, a1 = float(s0[core].std()), float(s1[core].std())
    k = min(1.0, KEEP * a0 / a1)
    print(f'{name}: detail approved {a0:.3f} new {a1:.3f} -> k {k:.2f}')
    scale -= mask[..., ch] * (1 - k)
gain = np.exp(d1 * (scale - 1))[..., None]
out = new_lin * gain
classes = np.asarray(Image.open(T / 'nagate_material_classes.png').resize((2048, 2048), Image.NEAREST))
eye = classes == 250
base1k = Image.open(B / 'nagate_material_classes.png')
eye_old = np.asarray(base1k.resize((2048, 2048), Image.NEAREST)) == 250
target, current = old_lin[eye_old].mean(0), out[eye].mean(0)
print('eyes approved', target.round(3), 'new', current.round(3))
out[eye] *= target / current
Image.fromarray((encode(out) * 255 + 0.5).astype(np.uint8)).save(T / 'nagate_basecolor_graded.png')
print('GRAIN done')
