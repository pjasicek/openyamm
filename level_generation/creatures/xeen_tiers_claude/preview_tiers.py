#!/usr/bin/env python3
"""Offline preview of a region-ramp model's skins (lane S, Xeen colour tiers): rasterises the LOD0 body in its bind
pose from four sides with each variant's material (base colour through the region ramps, the shader's maths from
claude_shared/tier_textures.py), plus a mask view (regions 0..3 = red, green, blue, yellow) to learn which region is
which body part. Not a runtime check: look at the tiers in game as well.

    preview_tiers.py <model.glb> <out.png> [variant ...] [--size 300] [--views front,left,back,right] [--mask]

Without variants, every variant of the model is drawn, one row each."""
import argparse
import io
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'claude_shared'))
from xeen_tiers import read  # noqa: E402
from tier_textures import srgb_to_linear, linear_to_srgb  # noqa: E402

TYPES = {5126: np.float32, 5125: np.uint32, 5123: np.uint16, 5121: np.uint8}
SIZES = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}
LUMA = np.array([0.2126, 0.7152, 0.0722])
MASK_COLOURS = np.array([[1, 0.1, 0.1], [0.1, 1, 0.1], [0.2, 0.3, 1], [1, 1, 0.1]])


def accessor(doc, binary, index):
    acc = doc['accessors'][index]
    view = doc['bufferViews'][acc['bufferView']]
    dtype = TYPES[acc['componentType']]
    n = SIZES[acc['type']]
    start = view.get('byteOffset', 0) + acc.get('byteOffset', 0)
    stride = view.get('byteStride', 0)
    item = np.dtype(dtype).itemsize * n
    if stride and stride != item:
        raw = np.frombuffer(binary, np.uint8, count=stride * acc['count'], offset=start).reshape(-1, stride)[:, :item]
        return np.frombuffer(raw.tobytes(), dtype).reshape(acc['count'], n)
    return np.frombuffer(binary, dtype, count=acc['count'] * n, offset=start).reshape(acc['count'], n)


def image(doc, binary, texture, cache):
    src = doc['textures'][texture]['source']
    if src not in cache:
        view = doc['bufferViews'][doc['images'][src]['bufferView']]
        data = binary[view.get('byteOffset', 0):view.get('byteOffset', 0) + view['byteLength']]
        cache[src] = Image.open(io.BytesIO(data))
    return cache[src]


def material_texels(doc, binary, mat, cache, mask_view):
    """Linear RGB texture of a material as the shader colours it (region ramps applied), or its mask view."""
    pbr = mat.get('pbrMetallicRoughness', {})
    factor = np.array(pbr.get('baseColorFactor', [1, 1, 1, 1])[:3])
    if 'baseColorTexture' in pbr:
        base = np.asarray(image(doc, binary, pbr['baseColorTexture']['index'], cache).convert('RGB'), np.float64)
        lin = srgb_to_linear(base / 255) * factor
    else:
        lin = np.ones((4, 4, 3)) * factor
    ex = mat.get('extras', {})
    if 'openyamm_region_mask' in ex and 'openyamm_region_ramps' in ex:
        bands = image(doc, binary, ex['openyamm_region_mask']['index'], cache).convert('RGBA').split()
        size = (lin.shape[1], lin.shape[0])
        mask = np.stack([np.asarray(b if b.size == size else b.resize(size, Image.BILINEAR), np.float64) / 255
                         for b in bands], -1)
        if mask_view:
            grey = np.repeat((lin @ LUMA)[..., None], 3, -1) ** 0.5 * 0.6
            out = grey
            for c in range(4):
                w = mask[..., c:c + 1]
                out = out * (1 - w) + MASK_COLOURS[c] * w
            return srgb_to_linear(out)
        lum = lin @ LUMA
        for channel, ramp in enumerate(ex['openyamm_region_ramps']):
            lo, hi = ramp['range']
            t = np.clip((lum - lo) / max(hi - lo, 1e-4), 0, 1) * 15
            i0 = np.floor(t).astype(int)
            i1 = np.minimum(i0 + 1, 15)
            f = (t - i0)[..., None]
            colours = np.asarray(ramp['colors'])
            w = mask[..., channel][..., None]
            lin = lin * (1 - w) + (colours[i0] * (1 - f) + colours[i1] * f) * w
    return lin


def variant_material(doc, prim, vindex):
    for m in prim.get('extensions', {}).get('KHR_materials_variants', {}).get('mappings', []):
        if vindex in m['variants']:
            return m['material']
    return prim.get('material', 0)


def render(tris, uvs, normals, texids, textures, view, size):
    """Orthographic z-buffer raster. tris: T x 3 x 3 positions; returns size x size RGB (linear) + coverage."""
    rot = {'front': 0, 'left': 90, 'back': 180, 'right': 270}[view]
    a = np.radians(rot)
    r = np.array([[np.cos(a), 0, np.sin(a)], [0, 1, 0], [-np.sin(a), 0, np.cos(a)]])
    p = tris @ r.T
    n = normals @ r.T
    lo = p.reshape(-1, 3).min(0)
    hi = p.reshape(-1, 3).max(0)
    scale = (size - 8) / max(hi[0] - lo[0], hi[1] - lo[1])
    cx = (lo[0] + hi[0]) / 2
    cy = (lo[1] + hi[1]) / 2
    sx = (p[..., 0] - cx) * scale + size / 2
    sy = size / 2 - (p[..., 1] - cy) * scale
    sz = p[..., 2]
    zbuf = np.full((size, size), -np.inf)
    out = np.zeros((size, size, 3))
    light = np.array([0.4, 0.6, 0.7])
    light /= np.linalg.norm(light)
    for t in range(len(tris)):
        x0, x1, x2 = sx[t]
        y0, y1, y2 = sy[t]
        minx = max(int(np.floor(min(x0, x1, x2))), 0)
        maxx = min(int(np.ceil(max(x0, x1, x2))), size - 1)
        miny = max(int(np.floor(min(y0, y1, y2))), 0)
        maxy = min(int(np.ceil(max(y0, y1, y2))), size - 1)
        if minx > maxx or miny > maxy:
            continue
        den = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
        if abs(den) < 1e-9:
            continue
        xs, ys = np.meshgrid(np.arange(minx, maxx + 1) + 0.5, np.arange(miny, maxy + 1) + 0.5)
        w0 = ((y1 - y2) * (xs - x2) + (x2 - x1) * (ys - y2)) / den
        w1 = ((y2 - y0) * (xs - x2) + (x0 - x2) * (ys - y2)) / den
        w2 = 1 - w0 - w1
        inside = (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
        if not inside.any():
            continue
        z = w0 * sz[t, 0] + w1 * sz[t, 1] + w2 * sz[t, 2]
        yi = (ys - 0.5).astype(int)
        xi = (xs - 0.5).astype(int)
        sel = inside & (z > zbuf[yi, xi])
        if not sel.any():
            continue
        uv = (w0[sel, None] * uvs[t, 0] + w1[sel, None] * uvs[t, 1] + w2[sel, None] * uvs[t, 2])
        tex = textures[texids[t]]
        h, w = tex.shape[:2]
        u = np.clip((uv[:, 0] % 1.0) * w, 0, w - 1).astype(int)
        v = np.clip((uv[:, 1] % 1.0) * h, 0, h - 1).astype(int)
        nn = (w0[sel, None] * n[t, 0] + w1[sel, None] * n[t, 1] + w2[sel, None] * n[t, 2])
        nn /= np.maximum(np.linalg.norm(nn, axis=1, keepdims=True), 1e-6)
        shade = 0.45 + 0.75 * np.abs(nn @ light)
        zbuf[yi[sel], xi[sel]] = z[sel]
        out[yi[sel], xi[sel]] = tex[v, u] * shade[:, None]
    return out, np.isfinite(zbuf)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('glb')
    ap.add_argument('out')
    ap.add_argument('variants', nargs='*')
    ap.add_argument('--size', type=int, default=300)
    ap.add_argument('--views', default='front,left,back,right')
    ap.add_argument('--mask', action='store_true', help='add a row with the region mask view')
    ap.add_argument('--mesh', type=int, default=0)
    args = ap.parse_args()
    doc, binary = read(args.glb)
    names = [v['name'] for v in doc.get('extensions', {}).get('KHR_materials_variants', {}).get('variants', [])]
    rows = args.variants or names
    mesh = doc['meshes'][args.mesh]
    prims = []
    for prim in mesh['primitives']:
        pos = accessor(doc, binary, prim['attributes']['POSITION']).astype(np.float64)
        nor = accessor(doc, binary, prim['attributes']['NORMAL']).astype(np.float64)
        uv = accessor(doc, binary, prim['attributes']['TEXCOORD_0']).astype(np.float64)
        idx = accessor(doc, binary, prim['indices']).reshape(-1, 3).astype(np.int64)
        prims.append((prim, pos[idx], nor[idx], uv[idx]))
    cache = {}
    views = args.views.split(',')
    lines = [(r, False) for r in rows] + ([(rows[0], True)] if args.mask else [])
    s = args.size
    sheet = Image.new('RGB', (s * len(views), (s + 14) * len(lines)), (96, 96, 96))
    draw = ImageDraw.Draw(sheet)
    for li, (variant, mask_view) in enumerate(lines):
        vindex = names.index(variant) if variant in names else -1
        textures, tris, uvs, nors, texids = [], [], [], [], []
        for pi, (prim, t, n, uv) in enumerate(prims):
            mat = doc['materials'][variant_material(doc, prim, vindex)]
            textures.append(material_texels(doc, binary, mat, cache, mask_view))
            tris.append(t); nors.append(n); uvs.append(uv); texids.append(np.full(len(t), pi))
        tris = np.concatenate(tris); nors = np.concatenate(nors); uvs = np.concatenate(uvs)
        texids = np.concatenate(texids)
        for vi, view in enumerate(views):
            rgb, cov = render(tris, uvs, nors, texids, textures, view, s)
            srgb = (np.clip(linear_to_srgb(rgb), 0, 1) * 255).astype(np.uint8)
            img = Image.fromarray(srgb)
            sheet.paste(img, (vi * s, li * (s + 14) + 14), Image.fromarray((cov * 255).astype(np.uint8)))
        draw.text((4, li * (s + 14) + 1), ('MASK ' if mask_view else '') + variant, fill=(255, 255, 255))
    sheet.save(args.out)
    print('WROTE', args.out)


if __name__ == '__main__':
    main()
