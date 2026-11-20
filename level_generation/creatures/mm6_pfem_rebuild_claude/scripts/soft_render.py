#!/usr/bin/env python3
"""Small software renderer for head diagnostics (follow-up 4): orthographic, bind pose, backface culling, z-buffer, base colour
texture (head and tier A body), simple headlight shading with the GLB's vertex normals. Also returns per-pixel (primitive, triangle).
Usage: soft_render.py <glb> <out.png> az:el[:cx,cy,cz:radius] ... (az 0 = front, 90 = her left, 270 = her right)"""
import io, sys
from pathlib import Path
import numpy as np
from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parent))
from glbio import Glb


def image(g, i):
    bv = g.j['bufferViews'][g.j['images'][i]['bufferView']]; o = bv.get('byteOffset', 0)
    return np.asarray(Image.open(io.BytesIO(bytes(g.bin[o:o + bv['byteLength']]))).convert('RGB')).astype(np.float32)


def load(g, mesh=0):
    prims = []
    for p, pr in enumerate(g.j['meshes'][mesh]['primitives']):
        d = g.prim(mesh, p); mat = g.j['materials'][pr['material']]
        tex = image(g, g.j['textures'][mat['pbrMetallicRoughness']['baseColorTexture']['index']]['source'])
        prims.append((d['POSITION'].astype(float), d['NORMAL'].astype(float), d['TEXCOORD_0'].astype(float), d['idx'], tex))
    return prims


def render(prims, az, el, cen=(0.0, 0.63, 0.03), radius=0.11, size=900, shade=True, depth=False):
    a, e = np.radians(az), np.radians(el)
    fwd = -np.array([np.sin(a) * np.cos(e), np.sin(e), np.cos(a) * np.cos(e)])
    r = np.cross(fwd, [0, 1.0, 0]); r /= np.linalg.norm(r); u = np.cross(r, fwd)
    px = 2 * radius / size; cen = np.asarray(cen)
    Z = np.full((size, size), np.inf); C = np.zeros((size, size, 3), np.float32) + [90, 94, 100]
    ID = -np.ones((size, size, 2), int)
    for pi, (co, nr, uv, tri, tex) in enumerate(prims):
        P = co - cen; X = (P @ r + radius) / px; Y = (radius - P @ u) / px; D = P @ fwd
        T = tri; fn = np.cross(co[T[:, 1]] - co[T[:, 0]], co[T[:, 2]] - co[T[:, 0]]); front = fn @ fwd < 0
        th, tw_ = tex.shape[:2]
        for f in np.nonzero(front)[0]:
            i0, i1, i2 = T[f]; xs = X[[i0, i1, i2]]; ys = Y[[i0, i1, i2]]
            x0, x1 = int(max(np.floor(xs.min()), 0)), int(min(np.ceil(xs.max()), size - 1))
            y0, y1 = int(max(np.floor(ys.min()), 0)), int(min(np.ceil(ys.max()), size - 1))
            if x1 < x0 or y1 < y0: continue
            gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
            den = (ys[1] - ys[2]) * (xs[0] - xs[2]) + (xs[2] - xs[1]) * (ys[0] - ys[2])
            if abs(den) < 1e-12: continue
            l0 = ((ys[1] - ys[2]) * (gx - xs[2]) + (xs[2] - xs[1]) * (gy - ys[2])) / den
            l1 = ((ys[2] - ys[0]) * (gx - xs[2]) + (xs[0] - xs[2]) * (gy - ys[2])) / den
            l2 = 1 - l0 - l1; ins = (l0 >= 0) & (l1 >= 0) & (l2 >= 0)
            if not ins.any(): continue
            z = l0 * D[i0] + l1 * D[i1] + l2 * D[i2]
            yy, xx = (gy[ins] - 0.5).astype(int), (gx[ins] - 0.5).astype(int); zz = z[ins]
            ok = zz < Z[yy, xx]
            if not ok.any(): continue
            yy, xx, zz = yy[ok], xx[ok], zz[ok]; L = np.c_[l0[ins][ok], l1[ins][ok], l2[ins][ok]]
            uvp = L @ uv[[i0, i1, i2]]; tx = np.clip((uvp[:, 0] * tw_).astype(int), 0, tw_ - 1); ty = np.clip((uvp[:, 1] * th).astype(int), 0, th - 1)
            col = tex[ty, tx]
            if shade:
                nn = L @ nr[[i0, i1, i2]]; nn /= np.maximum(np.linalg.norm(nn, axis=1, keepdims=True), 1e-12)
                ld = -fwd * 0.75 + u * 0.45 + r * 0.25; ld /= np.linalg.norm(ld)
                col = col * (0.35 + 0.75 * np.clip(nn @ ld, 0, 1))[:, None]
            Z[yy, xx] = zz; C[yy, xx] = col; ID[yy, xx] = [pi, f]
    if depth: return np.clip(C, 0, 255).astype(np.uint8), ID, Z
    return np.clip(C, 0, 255).astype(np.uint8), ID


if __name__ == '__main__':
    g = Glb(sys.argv[1]); prims = load(g); tiles = []
    from PIL import ImageDraw
    for v in sys.argv[3:]:
        parts = v.split(':'); az, el = float(parts[0]), float(parts[1])
        cen = tuple(map(float, parts[2].split(','))) if len(parts) > 2 else (0.0, 0.63, 0.03)
        rad = float(parts[3]) if len(parts) > 3 else 0.11
        im, _ = render(prims, az, el, cen, rad); t = Image.fromarray(im); ImageDraw.Draw(t).text((4, 4), v, fill=(255, 255, 0)); tiles.append(t)
    w, h = tiles[0].size; cols = min(3, len(tiles)); out = Image.new('RGB', (w * cols, h * ((len(tiles) + cols - 1) // cols)))
    for k, t in enumerate(tiles): out.paste(t, ((k % cols) * w, (k // cols) * h))
    out.save(sys.argv[2]); print('RENDER', sys.argv[2], out.size)
