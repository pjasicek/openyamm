#!/usr/bin/env python3
"""Flying Feet texture set on the v2 layout (the single right foot without its inner shell; the left foot is its mirrored
copy and shares every texel). The maps come from transfer_paint.py (the 4K Meshy paint meshy/foot_retexture_v1
resampled once onto v2): 2K colour, 1K normal, 1K ORM (R baked AO,
G roughness, B 0), 1K region mask (R = skin: the foot, ankle bumps, toes and nails; G = the feathered wings; from the
geometry: UV triangles rasterised per part from work/uv_v2.npz, padded into the gutters, feathered 1 texel) and the
1K material classes (1 skin, 4 nails by colour, 2 feathers; README). Grading and the gutter fill follow in
build_runtime.sh."""
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'textures'; OUT.mkdir(exist_ok=True)
base = Image.open(OUT / 'v2_basecolor.png').convert('RGB')
base.save(OUT / 'feet_basecolor.png')
Image.open(OUT / 'v2_normal_1k.png').convert('RGB').save(OUT / 'feet_normal_1k.png')
rough = np.asarray(Image.open(OUT / 'v2_roughness_1k.png').convert('L')) / 255.0
ao = np.asarray(Image.open(OUT / 'feet_ao_2k.png').convert('L').resize((1024, 1024), Image.LANCZOS)) / 255.0
orm = np.stack([ao, np.clip(rough, 0.5, 0.95), np.zeros_like(ao)], -1)
Image.fromarray((orm * 255 + 0.5).astype(np.uint8)).save(OUT / 'feet_mr_1k.png')

d = np.load(ROOT / 'work/uv_v2.npz'); uv = d['new']; part = d['part']
N = 1024
lab = Image.new('L', (N, N), 0); dr = ImageDraw.Draw(lab)
for t, p in zip(uv, part):
    pts = [(float(u) * N - 0.5, (1 - float(v)) * N - 0.5) for u, v in t]
    dr.polygon(pts, fill=1 if p == 0 else 2)
lab = np.asarray(lab)
inside = lab > 0
# pad: every gutter texel takes the label of the nearest island texel
_, (iy, ix) = ndimage.distance_transform_edt(~inside, return_indices=True)
padded = lab[iy, ix]
skin = ndimage.gaussian_filter((padded == 1).astype(np.float32), 0.8)
wing = ndimage.gaussian_filter((padded == 2).astype(np.float32), 0.8)
z = np.zeros((N, N), np.uint8)
to8 = lambda x: (np.clip(x, 0, 1) * 255 + 0.5).astype(np.uint8)
Image.merge('RGBA', [Image.fromarray(to8(skin)), Image.fromarray(to8(wing)), Image.fromarray(z), Image.fromarray(z)]) \
    .save(OUT / 'feet_region_mask.png')
# material classes: nails are the pale pink, low-saturation texels inside the skin
rgb = np.asarray(base.resize((N, N), Image.LANCZOS), np.float64) / 255
mx = rgb.max(-1); sat = np.where(mx > 0, (mx - rgb.min(-1)) / np.maximum(mx, 1e-6), 0)
nail = (lab == 1) & (sat < 0.33) & (mx > 0.78)
nail = ndimage.binary_opening(nail, iterations=1)
cls = np.where(lab == 2, 2, np.where(nail, 4, np.where(lab == 1, 1, 0))).astype(np.uint8)
Image.fromarray(cls, 'L').save(OUT / 'feet_material_classes.png')
print('COMPOSED skin', round(float((lab == 1).mean()), 3), 'wing', round(float((lab == 2).mean()), 3),
      'nails', round(float(nail.mean()), 4))
