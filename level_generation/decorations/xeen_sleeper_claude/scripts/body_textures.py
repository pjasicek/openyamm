#!/usr/bin/env python3
"""Stage 2a: the sleeper's body textures. For each of the titan's three texture sets (LOD0/1 2080 x 1024, LOD2 512,
LOD3 256) bake the chosen skin's region ramps into the base colour (claude_shared/tier_textures.py, the shader's
maths: a static decoration has no tiers) and close the eyes: the white of the eyes (inside the eye polygons'
UV triangles from build_body.py) is filled from the surrounding skin and a dark lid line drawn along each eye.
Writes work/tex/body<set>_basecolor.png (+ _normal, _mr copied) and work/tex/eyes<set>_crop.png for review.
Usage: body_textures.py [skin]   (skin: Titan_A | Titan_B | Titan_C, default sleeper.json's)"""
import io
import json
import struct
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent
REPO = HERE.parents[3]
sys.path.insert(0, str(REPO / 'level_generation' / 'creatures' / 'claude_shared'))
from gutter_fill import coverage  # noqa: E402
from tier_textures import apply  # noqa: E402

cfg = json.loads((HERE / 'sleeper.json').read_text())
skin = sys.argv[1] if len(sys.argv) > 1 else cfg['skin']
out = PROJECT / 'work' / 'tex'
out.mkdir(parents=True, exist_ok=True)
raw = (REPO / cfg['source']).read_bytes()
size = struct.unpack_from('<I', raw, 12)[0]
doc = json.loads(raw[20:20 + size])
binary = raw[28 + size:]


def image(index):
    tex = doc['textures'][index]
    view = doc['bufferViews'][doc['images'][tex['source']]['bufferView']]
    data = binary[view.get('byteOffset', 0):view.get('byteOffset', 0) + view['byteLength']]
    return Image.open(io.BytesIO(data))


materials = {m['name']: m for m in doc['materials']}
# texture set -> (material name, LODs using it)
SETS = {'0': (skin, (0, 1)), '2': (skin + '_LOD2', (2,)), '3': (skin + '_LOD3', (3,))}
for key, (mat_name, lods) in SETS.items():
    mat = materials[mat_name]
    pbr = mat['pbrMetallicRoughness']
    base = np.asarray(image(pbr['baseColorTexture']['index']).convert('RGB')).astype(np.float64) / 255
    mask = np.asarray(image(mat['extras']['openyamm_region_mask']['index']).convert('RGBA')).astype(np.float64) / 255
    colour = apply(base, mask, mat['extras']['openyamm_region_ramps'])
    h, w = colour.shape[:2]
    # eyes: white texels inside the eye polygons of every LOD using this set
    eye_area = np.zeros((h, w), bool)
    for lod in lods:
        tri = np.load(PROJECT / 'work' / f'eyes_lod{lod}.npz')['uv'].astype(np.float64)
        if len(tri):
            eye_area |= coverage(tri, h, w)
    eye_area = ndimage.binary_dilation(eye_area, iterations=max(1, round(w / 400)))
    lum = base @ [0.2126, 0.7152, 0.0722]
    sat = base.max(-1) - base.min(-1)
    white = eye_area & (lum > 0.55) & (sat < 0.12)
    white = ndimage.binary_closing(white, iterations=1)
    labels, n = ndimage.label(white)
    sizes = ndimage.sum(white, labels, range(1, n + 1))
    keep = [i + 1 for i, s in enumerate(sizes) if s >= max(3, 0.15 * sizes.max())] if n else []
    eyes = np.isin(labels, keep)
    rim = ndimage.binary_dilation(eyes, iterations=3) & eye_area & (lum > 0.40) & (sat < 0.15)
    eyes = eyes | rim
    grown = ndimage.binary_dilation(eyes, iterations=max(1, round(w / 520))) & eye_area
    # fill from the skin around (grey, unsaturated texels of the eye area only: other charts' gutters are not skin):
    # repeated masked blur, a simple diffusion inpaint; anything left takes the skin's median
    skin_src = eye_area & ~grown & (sat < 0.08) & (lum > 0.2) & (lum < 0.6)
    skin_med = np.median(colour[skin_src], 0) if skin_src.any() else colour[eye_area].mean(0)
    known = skin_src.copy()
    acc = np.where(known[..., None], colour, 0)
    for _ in range(80):
        a = ndimage.uniform_filter(acc, size=(3, 3, 1))
        b = ndimage.uniform_filter(known.astype(np.float64), size=3)
        newly = grown & ~known & (b > 0.05)   # at least one known neighbour (the filter leaves float residue)
        if not newly.any():
            break
        acc[newly] = a[newly] / b[newly, None]
        known = known | newly
    acc[grown & ~known] = skin_med
    lid = acc * 0.88   # the lid a touch darker than the cheek
    colour = np.where(grown[..., None], lid, colour)
    # lid line: along each eye's long axis through its centre, dark grey, tapering at the ends
    img = Image.fromarray((np.clip(colour, 0, 1) * 255 + 0.5).astype(np.uint8), 'RGB')
    draw = ImageDraw.Draw(img)
    labels, n = ndimage.label(eyes)
    for i in range(1, n + 1):
        ys, xs = np.nonzero(labels == i)
        if len(xs) < 3:
            continue
        pts = np.stack([xs, ys], 1).astype(np.float64)
        c = pts.mean(0)
        u, s, vt = np.linalg.svd(pts - c, full_matrices=False)
        axis = vt[0]
        t = (pts - c) @ axis
        lo_t, hi_t = t.min(), t.max()
        width = max(1, int(round(w / 600)))
        steps = 12
        for k in range(steps):
            a = lo_t + (hi_t - lo_t) * k / steps
            b = lo_t + (hi_t - lo_t) * (k + 1) / steps
            mid = (a + b) / 2 / max(abs(lo_t), abs(hi_t), 1e-6)
            wk = max(1, int(round(width * (1.0 - 0.6 * mid * mid))))
            p0 = c + axis * a
            p1 = c + axis * b
            draw.line([tuple(p0), tuple(p1)], fill=(38, 36, 36), width=wk)
        print(f'SET {key} eye {i}: {len(xs)} texels, length {hi_t - lo_t:.1f} px')
    img.save(out / f'body{key}_basecolor.png', optimize=True)
    image(mat['normalTexture']['index']).convert('RGB').save(out / f'body{key}_normal.png', optimize=True)
    image(pbr['metallicRoughnessTexture']['index']).convert('RGB').save(out / f'body{key}_mr.png', optimize=True)
    if eyes.any():
        ys, xs = np.nonzero(grown)
        box = (max(0, xs.min() - 40), max(0, ys.min() - 40), min(w, xs.max() + 40), min(h, ys.max() + 40))
        before = Image.fromarray((np.clip(apply(base, mask, mat['extras']['openyamm_region_ramps']), 0, 1) * 255)
                                 .astype(np.uint8)).crop(box)
        after = img.crop(box)
        sheet = Image.new('RGB', (before.width * 2 + 4, before.height))
        sheet.paste(before, (0, 0)); sheet.paste(after, (before.width + 4, 0))
        sheet.save(out / f'eyes{key}_crop.png')
    print(f'SET {key} {mat_name} {w}x{h} eye texels {int(eyes.sum())}')
