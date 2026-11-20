#!/usr/bin/env python3
"""Rat A/B/C texture sets from the Meshy retexture: skin (head, lower legs/paws, tail) and fur recoloured to the
native tier medians (palettes 807/808/809) with Meshy's shading kept, eyes tinted per tier, roughness classes."""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'mm6_gob_claude' / 'scripts'))
import compose_textures_v2 as C
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'meshy/retexture_v2/texture_urls_0'          # textured from the Codex HD masters
OUT = ROOT / 'textures'; OUT.mkdir(exist_ok=True)
BRIGHT = 1.45                                     # albedo vs native sprite (sprites carry baked shading)
TIERS = {'a': ((0.267, 0.188, 0.235), (0.251, 0.220, 0.235), (0.95, 0.80, 0.20)),
         'b': ((0.192, 0.224, 0.157), (0.176, 0.176, 0.169), (0.95, 0.55, 0.12)),
         'c': ((0.239, 0.149, 0.149), (0.220, 0.184, 0.184), (0.95, 0.12, 0.08))}
data = np.load(ROOT / 'work/uv3d.npz')
part_map, xyz = C.rasterise(data)
strict, _ = C.rasterise(data, tol=0.0)
interior = ndimage.binary_erosion(strict >= 0, iterations=2)
_, (iy, ix) = ndimage.distance_transform_edt(~interior, return_indices=True)
def pad(a):
    o = a[iy, ix]; o[interior] = a[interior]; return o
base = pad(C.load(str(SRC) + '_base_color.png'))
rough = pad(C.load(str(SRC) + '_roughness.png', 'L'))
metal = pad(C.load(str(SRC) + '_metallic.png', 'L'))
normal = pad(C.load(str(SRC) + '_normal.png'))
x, y, z = xyz[..., 0], xyz[..., 1], xyz[..., 2]
valid = part_map >= 0
h, s, v = C.hsv(base)
lum = base @ np.array([0.2126, 0.7152, 0.0722])
collar = valid & (y > -0.34) & (y < -0.27) & (z > 0.06)
stud = collar & (v > 0.45) & (s < 0.25)
eye_tex = valid & (y < -0.32) & (h > 15) & (h < 50) & (s > 0.5) & (v > 0.35)
# Eyes painted as whole eyeballs: centre from the orange texels of the cleaner (left) eye, refined per side within
# 2 cm of the mirrored guess; sphere centre sits inside the head, pupil faces outward/forward.
pl = xyz[eye_tex & (x > 0)]; guess = np.median(pl, 0)
EYE_R = 0.0135
eye = np.zeros_like(valid); pupil = np.zeros_like(valid); rim_w = np.zeros(valid.shape, np.float32)
iris_t = np.zeros(valid.shape, np.float32)
for sx in (1.0, -1.0):
    g = guess * np.array([sx, 1, 1])
    near = xyz[eye_tex & (np.sign(x) == sx) & (np.linalg.norm(xyz - g, axis=-1) < 0.02)]
    c = np.median(near, 0) if len(near) > 50 else g
    axis = np.array([sx * 0.85, -0.45, 0.28]); axis /= np.linalg.norm(axis)
    core = c - axis * EYE_R * 0.55
    d = xyz - core; dist = np.linalg.norm(d, axis=-1)
    ang = np.degrees(np.arccos(np.clip((d @ axis) / np.maximum(dist, 1e-6), -1, 1)))
    inside = valid & (dist < EYE_R * 1.35) & (ang < 72) & (np.abs(y + 0.40) < 0.04)
    eye |= inside
    pupil |= inside & (ang < 20)
    iris_t = np.where(inside, np.clip(ang / 72, 0, 1), iris_t)
    rim_w = np.where(inside, np.clip((ang - 52) / 20, 0, 1), rim_w)
skin_geo = valid & ((y > 0.13) | ((z < 0.07) & (np.abs(x) > 0.05)) | ((y < -0.30) & ~collar))
skin_tex = valid & (s > 0.18) & (h > 60) & (h < 140)
skin = (skin_geo | skin_tex) & ~stud & ~eye
fur = valid & ~skin & ~stud & ~eye
skin_w = ndimage.gaussian_filter(skin.astype(np.float32), 3)
for tier, (skin_c, fur_c, eye_c) in TIERS.items():
    out = base.copy()
    for mask_w, col in ((skin_w, skin_c), (1 - skin_w, fur_c)):
        col = np.array(col) * BRIGHT
        lref = np.median(lum[(mask_w > 0.5) & valid]) if ((mask_w > 0.5) & valid).any() else 0.2
        shade = np.clip(lum / max(lref, 1e-3), 0.35, 1.8)[..., None]
        tinted = np.clip(col[None, None] * shade, 0, 1)
        m = (mask_w * valid)[..., None]
        out = out * (1 - m) + tinted * m
    out[stud] = base[stud]
    iris = np.array(eye_c)[None] * (1.05 - 0.45 * iris_t[eye, None])          # brighter centre, darker edge
    iris = iris * (1 - 0.65 * rim_w[eye, None])                               # dark limbal ring at the socket
    out[eye] = np.clip(iris, 0, 1)
    out[pupil] = (0.03, 0.025, 0.02)
    Image.fromarray(np.clip(pad(out) * 255 + 0.5, 0, 255).astype(np.uint8)).save(OUT / f'rat_{tier}_basecolor.png', optimize=True)
r = np.full(rough.shape, 0.78, np.float32); r[skin] = 0.62; r[stud] = 0.35; r[eye] = 0.18
m = np.zeros_like(r); m[stud] = 0.8
mr = np.stack([np.ones_like(r), r, m], -1)
Image.fromarray(np.clip(mr * 255 + 0.5, 0, 255).astype(np.uint8)).resize((1024, 1024), Image.LANCZOS).save(OUT / 'rat_metal_rough_1k.png')
Image.fromarray(np.clip(normal * 255 + 0.5, 0, 255).astype(np.uint8)).resize((1024, 1024), Image.LANCZOS).save(OUT / 'rat_normal_1k.png')
# Region weights for the shared-skin tiers (claude_shared/fit_tier_regions.py): channel order skin, fur, eyes.
clear = (valid & ~stud & ~eye).astype(np.float32)
np.savez_compressed(OUT / 'rat_region_weights.npz', names=np.array(['skin', 'fur', 'eyes']),
                    skin=pad(skin_w * clear), fur=pad((1 - skin_w) * clear), eyes=pad((eye & ~pupil).astype(np.float32)))
print('COMPOSED', {'skin': int(skin.sum()), 'fur': int(fur.sum()), 'eye': int(eye.sum()), 'stud': int(stud.sum())})
