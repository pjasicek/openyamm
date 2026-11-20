#!/usr/bin/env python3
"""Acid Crawler texture set from the Meshy retexture (meshy/retexture_v2 on the xatlas UVs, painted from the four Codex HD masters).

Writes into textures/:
  hcr_basecolor.png         2K base colour (Meshy, islands padded into the gutters; the eye pieces repainted as
                            glossy dark-olive domes with a highlight, since Meshy painted them beige)
  hcr_normal_1k.png         Meshy normal map (+y down; tools/prepare_actor_glb.py converts it)
  hcr_mr_1k.png             metal/roughness (R 1 until bake_ao.sh writes the AO, G roughness by class, B 0)
  hcr_region_weights.npz    soft region weights, one per mask channel:
                              carapace  (R) dorsal plates, head shield, mandibles, the pale armour of the thighs
                              acid      (G) the yellow-green soft body: belly lobes, joints, throat sac
                              limbs     (B) ankle rings, clawed feet and the olive-brown soft parts between
                              eyes      (A) the two eye pieces
  hcr_glow_mask.png         1K, acid region x brightness: where an emissive texture would glow (engine need)
  hcr_material_classes.png  1K labels (CLAUDE_CREATURE_TEXTURES.md): 4 carapace/claws, 1 soft body, 6 eyes,
                            7 mouth interior
Classes per texel come from the piece (work/uv3d.npz part labels + work/rig_info.json part names) and, on the body
piece, the Meshy colour (pale low-saturation = armour, hue >= 48 deg saturated = acid, the rest = limbs/soft)."""
import json, sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / 'mm6_gob_claude' / 'scripts'))
import compose_textures_v2 as C

SRC = ROOT / 'meshy/retexture_v2/texture_urls_0'
OUT = ROOT / 'textures'; OUT.mkdir(exist_ok=True)
data = np.load(ROOT / 'work/uv3d.npz')
parts = {int(k): v for k, v in json.load(open(ROOT / 'work/rig_info.json'))['parts'].items()}
info = json.load(open(ROOT / 'work/rig_info.json'))
part_map, xyz = C.rasterise(data)
strict, _ = C.rasterise(data, tol=0.0)
valid = part_map >= 0
interior = ndimage.binary_erosion(strict >= 0, iterations=2)
_, (iy, ix) = ndimage.distance_transform_edt(~interior, return_indices=True)


def pad(a):
    o = a[iy, ix]; o[interior] = a[interior]; return o


def save(array, path, size=None, mode=None):
    image = Image.fromarray(np.clip(array * 255 + 0.5, 0, 255).astype(np.uint8), mode)
    if size:
        image = image.resize((size, size), Image.LANCZOS)
    image.save(path, optimize=True)


def ssm(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)


def kind_mask(prefix):
    ks = [k for k, p in parts.items() if p.startswith(prefix)]
    return np.isin(part_map, ks)


base = C.load(str(SRC) + '_base_color.png')
normal = C.load(str(SRC) + '_normal.png')
rough = C.load(str(SRC) + '_roughness.png', 'L')
h, s, v = C.hsv(base)
body = kind_mask('body'); plate = kind_mask('plate'); mand = kind_mask('mandible'); eye = kind_mask('eye')
legp = kind_mask('ring') | kind_mask('foot')

# ---- eyes: glossy dark-olive domes, a soft highlight toward the upper front, a faint lime rim
for k in [k for k, p in parts.items() if p == 'eye']:
    m = part_map == k
    tri = data['xyz'][data['part'] == k].reshape(-1, 3)
    c = tri.mean(0)
    n = xyz[m] - c; n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-6)
    light = np.array([0.35 * np.sign(c[0]), -0.6, 0.72]); light /= np.linalg.norm(light)
    d = n @ light
    col = np.array([0.10, 0.13, 0.06])[None] + np.array([0.10, 0.16, 0.04])[None] * np.clip(1 - np.abs(d), 0, 1)[:, None] ** 3
    col = col + np.array([0.75, 0.80, 0.62])[None] * ssm(d, 0.86, 0.97)[:, None]
    base[m] = np.clip(col, 0, 1)

# ---- soft class weights
acid_c = ssm(h, 44, 52) * ssm(s, 0.36, 0.46)
pale_c = (1 - acid_c) * ssm(v, 0.40, 0.48) * (1 - ssm(s, 0.42, 0.52))
w_acid = np.where(body, acid_c, 0.0)
w_car = np.where(body, pale_c, 0.0) + (plate | mand)
w_eye = eye.astype(float)
w_limb = np.where(body, np.clip(1 - acid_c - pale_c, 0, 1), 0.0) + legp
mouth = body & (xyz[..., 1] < info['mouth'][1] + 0.045) & (np.abs(xyz[..., 0]) < 0.05) & \
    (np.abs(xyz[..., 2] - info['mouth'][2]) < 0.035) & (v < 0.38)
weights = {}
for name, w in (('carapace', w_car), ('acid', w_acid), ('limbs', w_limb), ('eyes', w_eye)):
    w = ndimage.gaussian_filter(np.clip(w, 0, 1).astype(np.float32), 1.0) * valid
    weights[name] = pad(w)
total = sum(weights.values())
for name in weights:                                   # partition of unity inside the islands
    weights[name] = np.where(total > 1e-3, weights[name] / np.maximum(total, 1e-3), 0)

# ---- classes, roughness, glow
classes = np.zeros(part_map.shape, np.uint8)
classes[valid] = 1
classes[valid & ((w_car > 0.5) | legp) & ~eye] = 4
classes[eye] = 6
classes[mouth] = 7
r = np.clip(rough * 0.3 + 0.55, 0.45, 0.85)
r = np.where(weights['acid'] > 0.5, 0.38, r); r[eye] = 0.15; r = np.where(classes == 4, np.minimum(r, 0.6), r)
lum = base @ np.array([0.2126, 0.7152, 0.0722])
glow = weights['acid'] * ssm(lum, 0.18, 0.45)

base = pad(base)
save(base, OUT / 'hcr_basecolor.png')
save(pad(normal), OUT / 'hcr_normal_1k.png', 1024)
save(np.stack([np.ones_like(r), pad(r), np.zeros_like(r)], -1), OUT / 'hcr_mr_1k.png', 1024)
np.savez_compressed(OUT / 'hcr_region_weights.npz', names=np.array(list(weights)), **weights)
save(pad(glow), OUT / 'hcr_glow_mask.png', 1024, 'L')
lab = Image.fromarray(pad(classes)).resize((1024, 1024), Image.NEAREST); lab.save(OUT / 'hcr_material_classes.png')
print('COMPOSED', {k: int((w > 0.5).sum()) for k, w in weights.items()}, 'mouth', int(mouth.sum()))
