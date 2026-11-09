#!/usr/bin/env python3
"""Dragon King head set (2026-10-30 rework; CLAUDE_CREATURE_TEXTURES.md "Head detail"; after
mm9_yrsa_claude/v2/scripts/compose_headhand.py).

Inputs: meshy/head_retexture_v1 maps (laid out on HeadUV 0..1 before head_split_dk.py scaled it), work/head_uv_v1.npz
(dump_head_uv.py: head UV triangles with tags 0 skin, 1 palate, 2 floor, 3 tooth, 4 eye, and the neck seam pairs),
references_head/04_mouth_palate.png and 05_mouth_floor.png (Codex swatches: across the mouth horizontally, front at
the top, throat at the bottom), textures/dragonking_head_ao_2k.png (bake_ao_head.py), the graded body base colour.

- Head: the retexture resampled into the lower-left HEAD_SCALE square (exact: head_split_dk.py scaled the islands by
  the same factor), graded like the body (claude_shared/grade_basecolor.py settings, head AO), then a skin-only gain
  so the head's skin luminance matches the body's across the neck seam (median ratio over the seam pairs).
- Mouth strip (top strip, v 0.806..0.994): per UV column the covered v range of the palate (u 0.01..0.49) and of the
  floor (u 0.51..0.99) takes the swatch remapped across it (gums at both lip edges, palate or tongue between) and
  along the strip (front -> throat; the swatch's own darkening toward the throat). Normal from the swatch luminance
  (ridges, papillae), roughness wet.
- Maps: base colour 2K (head material), normal and metal-rough 1K (R 1, G roughness, B 0; material_classes_to_orm.py
  rewrites R/G/B from the classes), classes 1K: 1 skin, 3 membrane (dark frill membrane), 4 claw/horn, 5 tooth,
  6 eye, 7 mouth (tags from the geometry; only ivory horn texels by colour).
Writes textures/dragonking_head_basecolor.png, _normal_1k.png, _metal_rough_1k.png, _material_classes.png and
review/head_set_preview.png."""
import json, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage

HERE = Path(__file__).resolve().parents[2]
T, J = HERE / 'textures', HERE / 'meshy' / 'head_retexture_v1'
N, S, HEAD_SCALE = 2048, 1024, 0.8
GRADE = HERE.parent / 'claude_shared' / 'grade_basecolor.py'


def raster(uv, size):
    tri = np.full((size, size), -1, np.int32)
    P = uv * size
    for t in range(len(P)):
        p = P[t]
        x0, x1 = max(int(np.floor(p[:, 0].min())), 0), min(int(np.ceil(p[:, 0].max())), size - 1)
        y0, y1 = max(int(np.floor(p[:, 1].min())), 0), min(int(np.ceil(p[:, 1].max())), size - 1)
        if x1 < x0 or y1 < y0:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        a, b, c = p
        den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(den) < 1e-12:
            continue
        l1 = ((b[1] - c[1]) * (gx - c[0]) + (c[0] - b[0]) * (gy - c[1])) / den
        l2 = ((c[1] - a[1]) * (gx - c[0]) + (a[0] - c[0]) * (gy - c[1])) / den
        inside = (l1 >= -1e-3) & (l2 >= -1e-3) & (1 - l1 - l2 >= -1e-3)
        iy, ix = np.nonzero(inside)
        tri[size - 1 - (iy + y0), ix + x0] = t
    return tri


def pad(img, covered):
    _, (iy, ix) = ndimage.distance_transform_edt(~covered, return_indices=True)
    return img[iy, ix]


def scaled(img, fill):
    out = Image.new(img.mode, (N, N), fill)
    k = int(round(N * HEAD_SCALE))
    out.paste(img.resize((k, k), Image.LANCZOS), (0, N - k))
    return np.asarray(out).astype(np.float32)


def lum(a):
    return a[..., :3] @ np.array([0.2126, 0.7152, 0.0722], np.float32)


def hsv(rgb):
    mx, mn = rgb.max(-1), rgb.min(-1)
    d = mx - mn + 1e-9
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    h = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60
    return h, (mx - mn) / (mx + 1e-9), mx


D = np.load(HERE / 'work' / 'head_uv_v1.npz')
uv, tag = D['uv'], D['tag']
tri = raster(uv, N)
cov = tri >= 0
tagmap = np.where(cov, tag[np.maximum(tri, 0)], -1)

# ---------------------------------------------------------------- head (retexture) + grade
base = scaled(Image.open(J / 'texture_urls_0_base_color.png').convert('RGB'), (0, 0, 0))
headcov = cov & (tagmap != 1) & (tagmap != 2)
tmp = T / 'dragonking_head_basecolor_ungraded.png'
Image.fromarray(np.uint8(np.clip(pad(base, headcov), 0, 255))).save(tmp)
subprocess.run([sys.executable, str(GRADE), '--ao', str(T / 'dragonking_head_ao_2k.png'), str(tmp)], check=True)
graded = np.asarray(Image.open(T / 'dragonking_head_basecolor_ungraded_graded.png').convert('RGB')).astype(np.float32)

# seam gain (skin only): body graded base colour at the body side, head graded at the head side
body = np.asarray(Image.open(T / 'dragonking_basecolor_graded.png').convert('RGB')).astype(np.float32)
BH = body.shape[0]


def sample(img, u, v):
    h = img.shape[0]
    x = np.clip((u * h).astype(int), 0, h - 1); y = np.clip(((1 - v) * h).astype(int), 0, h - 1)
    return ndimage.uniform_filter(img, (7, 7, 1))[y, x]


# band match: head skin texels just above the neck cut against body skin texels just below it (triangle interiors,
# not the seam vertices, which sit on padded island borders)
xyz = D['xyz']
hb = (tag == 0) & (xyz[:, 2] > 14.45) & (xyz[:, 2] < 14.9) & (xyz[:, 1] > -3.6)
hmask = np.isin(tri, np.nonzero(hb)[0])
BD = np.load(HERE / 'work' / 'uv3d_body_v3.npz')
bc = BD['xyz'].mean(1)
bsel = (bc[:, 2] > 13.9) & (bc[:, 2] < 14.45) & (bc[:, 1] > -3.2) & (bc[:, 1] < -0.6) & (BD['head'].mean(1) < 0.5)
btri = raster(BD['uv'], body.shape[0])
bmask = np.isin(btri, np.nonzero(bsel)[0])
hpx, bpx = graded[hmask], body[bmask]
hmed, bmed = np.median(hpx, 0), np.median(bpx, 0)
gain = float(np.clip(lum(bmed[None])[0] / max(lum(hmed[None])[0], 1), 0.6, 1.4))
tint = np.clip((bmed / np.maximum(hmed, 1)) / gain, 0.85, 1.15) ** 0.5      # half of the remaining per-channel cast
ok = np.ones(int(hmask.sum()), bool)
skin = headcov & (tagmap == 0)
h_, s_, v_ = hsv(graded / 255)
skinish = skin & (s_ > 0.25)          # green scales; horns, teeth and eyes keep their own brightness
head_rgb = graded.copy()
head_rgb[skinish] = np.clip(head_rgb[skinish] * gain * tint, 0, 255)

# ---------------------------------------------------------------- mouth strip from the Codex swatches
def sheet(tag_id, swatch_file, u0, u1):
    sw = np.asarray(Image.open(HERE / 'references_head' / swatch_file).convert('RGB')).astype(np.float32)
    H, W = sw.shape[:2]
    m = tagmap == tag_id
    cols = np.nonzero(m.any(0))[0]
    cols = cols[(cols >= int(u0 * N)) & (cols <= int(u1 * N))]
    if not len(cols):
        return None, None
    c_front, c_back = cols.min(), cols.max()
    out = np.zeros((N, N, 3), np.float32); hgt = np.zeros((N, N), np.float32)
    swl = lum(sw)
    for c in cols:
        rows = np.nonzero(m[:, c])[0]
        r_top, r_bot = rows.min(), rows.max()               # image rows: top = high v
        along = (c - c_front) / max(c_back - c_front, 1)
        sr = int(np.clip(along * (H - 1), 0, H - 1))
        rr = np.arange(r_top, r_bot + 1)
        across = (rr - r_top) / max(r_bot - r_top, 1)        # 0..1 across the covered sheet (both lip edges = gums)
        sc = np.clip((across * (W - 1)).astype(int), 0, W - 1)
        out[rr, c] = sw[sr, sc]; hgt[rr, c] = swl[sr, sc]
    return out, hgt


pal, ph = sheet(1, '04_mouth_palate.png', 0.0, 0.5)
flo, fh = sheet(2, '05_mouth_floor.png', 0.5, 1.0)
mouthcov = (tagmap == 1) | (tagmap == 2)
mouth_rgb = np.where((tagmap == 1)[..., None], pal, flo)
height = np.where(tagmap == 1, ph, fh)
final = np.where(mouthcov[..., None], mouth_rgb, head_rgb)
final = pad(final, cov)
Image.fromarray(np.uint8(np.clip(np.round(final), 0, 255))).save(T / 'dragonking_head_basecolor.png')

# ---------------------------------------------------------------- normal, metal-rough
nrm = scaled(Image.open(J / 'texture_urls_0_normal.png').convert('RGB'), (128, 128, 255))
hs = ndimage.gaussian_filter(height / 255.0, 1.2)
gy, gx = np.gradient(hs)
k = 6.0
mn = np.stack([-gx * k, gy * k, np.ones_like(hs)], -1); mn /= np.linalg.norm(mn, axis=-1, keepdims=True)
nrm = np.where(mouthcov[..., None], (mn * 0.5 + 0.5) * 255, nrm)
nrm = pad(nrm, cov)
Image.fromarray(np.uint8(np.round(nrm))).resize((S, S), Image.LANCZOS).save(T / 'dragonking_head_normal_1k.png')
rough = scaled(Image.open(J / 'texture_urls_0_roughness.png').convert('L'), 200)
rough = np.clip(rough, 0.45 * 255, 0.9 * 255)
rough[mouthcov] = 0.35 * 255
orm = pad(np.stack([np.full((N, N), 255.0), rough, np.zeros((N, N))], -1), cov)
Image.fromarray(np.uint8(np.round(orm))).resize((S, S), Image.LANCZOS).save(T / 'dragonking_head_metal_rough_1k.png')

# ---------------------------------------------------------------- material classes (1K)
tm = np.asarray(Image.fromarray((tagmap + 1).astype(np.uint8)).resize((S, S), Image.NEAREST)).astype(int) - 1
fs = np.asarray(Image.fromarray(np.uint8(np.clip(final, 0, 255))).resize((S, S), Image.LANCZOS), np.float32) / 255
h, s, v = hsv(ndimage.uniform_filter(fs, (3, 3, 1)))
classes = np.zeros((S, S), np.uint8)
classes[tm == 0] = 1
classes[(tm == 0) & (s < 0.18) & (v > 0.45)] = 4                     # ivory horn tips / crest (Meshy paints most horns green)
# no colour-based membrane or eye classes on the head: the mottled graded skin has dark and yellow texels everywhere
classes[tm == 3] = 5
classes[tm == 4] = 6
classes[(tm == 1) | (tm == 2)] = 7
Image.fromarray(classes).save(T / 'dragonking_head_material_classes.png')
names = {0: 'empty', 1: 'skin', 3: 'membrane', 4: 'claw_horn', 5: 'tooth', 6: 'eye', 7: 'mouth'}
rep = {'seam_gain': round(gain, 3), 'seam_tint': tint.round(3).tolist(), 'head_band_median': hmed.round(1).tolist(), 'body_band_median': bmed.round(1).tolist(), 'band_texels': [int(hmask.sum()), int(bmask.sum())], 'head_coverage': round(float(headcov.mean()), 3),
       'mouth_coverage': round(float(mouthcov.mean()), 3),
       'class_share': {names[k]: round(float((classes == k).mean()), 4) for k in names}}
json.dump(rep, open(T / 'dragonking_head_compose.json', 'w'), indent=1)
pv = Image.fromarray(np.uint8(np.clip(final, 0, 255))).resize((1024, 1024), Image.LANCZOS)
pal_c = {0: (0, 0, 0), 1: (110, 160, 70), 3: (200, 120, 200), 4: (240, 240, 120), 5: (255, 255, 230), 6: (60, 200, 255), 7: (200, 40, 60)}
cp = np.zeros((S, S, 3), np.uint8)
for kk, cc in pal_c.items():
    cp[classes == kk] = cc
sheet_img = Image.new('RGB', (2048, 1024)); sheet_img.paste(pv, (0, 0)); sheet_img.paste(Image.fromarray(cp), (1024, 0))
(HERE / 'review').mkdir(exist_ok=True)
sheet_img.save(HERE / 'review' / 'head_set_preview.png')
print('HEADSET', json.dumps(rep))
