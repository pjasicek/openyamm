#!/usr/bin/env python3
"""Runtime texture sets from the Meshy returns (CLAUDE_CREATURE_TEXTURES.md; one palette, so no tier ramps):
- body (body_retexture_v1, Meshy's UVs): base colour, normal and packed metal/roughness at 1K (a separate head set
  exists). Metal is kept only where Meshy's metallic exceeds 0.5 (breastplate cups, strap studs): its skin came back
  partly metallic (90th percentile 0.32), which reads as oil. Packed channels: R specular mask (metal 0.8, else 0.12),
  G roughness, B metallic (the material sets openyamm_specular_mask).
- head (head_retexture_v1, our HeadUV): the same at 1K; red skin paint that bled onto the horns, crown spikes and fangs
  (separate head pieces; their UV triangles from dump_uv_pieces.py) is repainted ivory: the median of the pieces'
  non-red texels, keeping each texel's brightness; horns get specular 0.3, skin 0.12, no metal.
- rock (rock_multiview_v1): base colour at 2K (it fills the room's end), normal and metal/roughness at 1K, no metal.
Writes textures/qfi_*.png."""
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

P = Path(__file__).resolve().parents[1]
M = P / 'meshy'
OUT = P / 'textures'
OUT.mkdir(exist_ok=True)
LUMA = np.array([0.2126, 0.7152, 0.0722])


def load(job, name, mode='RGB'):
    return Image.open(M / job / f'texture_urls_0_{name}.png').convert(mode)


def arr(im):
    return np.asarray(im, dtype=np.float64) / 255.0


def save(a, name, size=None):
    im = Image.fromarray(np.round(np.clip(a, 0, 1) * 255).astype(np.uint8))
    if size:
        im = im.resize((size, size), Image.LANCZOS)
    im.save(OUT / name)


def packed_mr(rough, metal, spec):
    return np.stack([spec, rough, metal], axis=-1)


# ---------------------------------------------------------------- body
base = arr(load('body_retexture_v1', 'base_color'))
rough = arr(load('body_retexture_v1', 'roughness', 'L'))
metal = arr(load('body_retexture_v1', 'metallic', 'L'))
is_metal = metal > 0.5
metal = np.where(is_metal, metal, 0.0)
spec = np.where(is_metal, 0.8, 0.12)
save(base, 'qfi_basecolor_1k.png', 1024)
Image.open(M / 'body_retexture_v1' / 'texture_urls_0_normal.png').convert('RGB').resize((1024, 1024), Image.LANCZOS) \
    .save(OUT / 'qfi_normal_1k.png')
save(packed_mr(rough, metal, spec), 'qfi_metal_rough_1k.png', 1024)
report = {'body_metal_fraction': round(float(is_metal.mean()), 4)}

# ---------------------------------------------------------------- head
hb = arr(load('head_retexture_v1', 'base_color'))
H, W = hb.shape[:2]
pieces = json.loads((P / 'work' / 'uv_pieces.json').read_text())
r, g, b = hb[..., 0], hb[..., 1], hb[..., 2]
red_all = ((r - np.maximum(g, b)) > 0.04) & (g < 0.72 * r)
mask_im = Image.new('L', (W, H), 0)
draw = ImageDraw.Draw(mask_im)
for tri in pieces['head_spikes']:
    draw.polygon([(u * W, (1 - v) * H) for u, v in tri], fill=255)
# side spikes joined to the skull: any head face whose own texels are mostly (70 %) ivory is horn or spike; these
# faces get a narrow 1-texel grow only (a wide one bleached the skin round the spikes' bases)
face_im = Image.new('L', (W, H), 0)
draw_f = ImageDraw.Draw(face_im)
joined = 0
for tri in pieces['head_faces']:
    pts = [(u * W, (1 - v) * H) for u, v in tri]
    x0, y0 = int(max(0, min(p[0] for p in pts))), int(max(0, min(p[1] for p in pts)))
    x1, y1 = int(min(W - 1, max(p[0] for p in pts))) + 1, int(min(H - 1, max(p[1] for p in pts))) + 1
    if x1 <= x0 or y1 <= y0:
        continue
    face = Image.new('L', (x1 - x0, y1 - y0), 0)
    ImageDraw.Draw(face).polygon([(x - x0, y - y0) for x, y in pts], fill=255)
    inside = np.asarray(face) > 0
    if inside.sum() < 4:
        continue
    if red_all[y0:y1, x0:x1][inside].mean() < 0.3:
        draw_f.polygon(pts, fill=255); joined += 1
from PIL import ImageFilter
# grown by 6 texels: filtering at the islands' edges samples the red padding just outside the triangles
mask = (np.asarray(mask_im.filter(ImageFilter.MaxFilter(13))) > 0) | (np.asarray(face_im.filter(ImageFilter.MaxFilter(3))) > 0)
r, g, b = hb[..., 0], hb[..., 1], hb[..., 2]
red = ((r - np.maximum(g, b)) > 0.04) & (g < 0.72 * r)   # red skin (dark shadowed red too); ivory has g ~ 0.86 r
ivory_px = hb[mask & ~red]
ivory = np.median(ivory_px, axis=0) if len(ivory_px) else np.array([0.85, 0.8, 0.68])
lum = hb @ LUMA
ivory_lum = float(ivory @ LUMA)
fix = mask & red
hb[fix] = ivory[None, :] * np.clip(lum[fix] / max(ivory_lum, 1e-3), 0.65, 1.15)[:, None]
report['head_ivory_faces'] = joined; report['head_spike_texels'] = int(mask.sum()); report['head_spike_repainted'] = int(fix.sum())
report['ivory'] = [round(float(x), 3) for x in ivory]
save(hb, 'qfi_head_basecolor_1k.png', 1024)
Image.open(M / 'head_retexture_v1' / 'texture_urls_0_normal.png').convert('RGB').resize((1024, 1024), Image.LANCZOS) \
    .save(OUT / 'qfi_head_normal_1k.png')
hr = arr(load('head_retexture_v1', 'roughness', 'L'))
save(packed_mr(hr, np.zeros_like(hr), np.where(mask, 0.3, 0.12)), 'qfi_head_metal_rough_1k.png', 1024)

# ---------------------------------------------------------------- rock
load('rock_multiview_v1', 'base_color').save(OUT / 'qfi_rock_basecolor_2k.png')
Image.open(M / 'rock_multiview_v1' / 'texture_urls_0_normal.png').convert('RGB').resize((1024, 1024), Image.LANCZOS) \
    .save(OUT / 'qfi_rock_normal_1k.png')
rr = arr(load('rock_multiview_v1', 'roughness', 'L'))
save(packed_mr(rr, np.zeros_like(rr), np.full_like(rr, 0.1)), 'qfi_rock_metal_rough_1k.png', 1024)
(OUT / 'compose_report.json').write_text(json.dumps(report, indent=1))
print('COMPOSE', json.dumps(report))
