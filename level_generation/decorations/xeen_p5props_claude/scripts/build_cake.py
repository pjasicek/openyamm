#!/usr/bin/env python3
"""The wedding cake on MM9's round table as one decoration model (no Blender): a built three-tier cake (white icing,
gold piping rings, a gold stand plate and a small gold topper) appended as a second-material primitive set to a copy of
assets_source/worlds/mm9/models/mm9_deco_roundtable.glb. Table metres: the table is 2.02 across and 1.13 tall.

    build_cake.py <out.glb> [--preview out.png]"""
import io
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / 'level_generation/creatures/claude_shared/floor'))
from glb_pose import Glb  # noqa: E402

TABLE = ROOT / 'assets_source/worlds/mm9/models/mm9_deco_roundtable.glb'
SEG = 24


def atlas():
    """512 x 256: u 0..0.5 icing (white with faint swags and dots), u 0.5..1 gold."""
    w, h = 512, 256
    img = Image.new('RGB', (w, h), (244, 240, 230))
    d = ImageDraw.Draw(img)
    for k in range(8):                      # swags (garlands) round the tiers
        x0 = k * 32
        d.arc([x0, 60, x0 + 32, 140], 0, 180, fill=(226, 214, 190), width=3)
        d.ellipse([x0 + 14, 98, x0 + 18, 102], fill=(214, 196, 150))
    rng = np.random.default_rng(5)
    a = np.asarray(img, float)
    a[:, :256] *= (1 + 0.025 * rng.normal(0, 1, (h, 256)))[..., None]
    gold = np.array([212, 168, 70.0])
    y = np.linspace(0, 1, h)[:, None]
    shade = 0.85 + 0.3 * np.abs(np.sin(y * 18))
    a[:, 256:] = gold * shade[..., None]
    img = Image.fromarray(a.clip(0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.6))
    return img


def cylinder(r, y0, y1, u0, u1, top=True):
    V, U, F = [], [], []
    for j in range(SEG + 1):
        th = 2 * math.pi * j / SEG
        for y, v in ((y0, 0.75), (y1, 0.25)):
            V.append((r * math.cos(th), y, r * math.sin(th))); U.append((u0 + (u1 - u0) * j / SEG, v))
    for j in range(SEG):
        a, b, c, d = 2 * j, 2 * j + 2, 2 * j + 3, 2 * j + 1
        F += [(a, c, b), (a, d, c)]
    if top:
        base = len(V)
        V.append((0, y1, 0)); U.append(((u0 + u1) / 2, 0.08))
        for j in range(SEG + 1):
            th = 2 * math.pi * j / SEG
            V.append((r * math.cos(th), y1, r * math.sin(th))); U.append(((u0 + u1) / 2 + 0.02 * math.cos(th), 0.08 + 0.05 * math.sin(th)))
        for j in range(SEG):
            F.append((base, base + 2 + j, base + 1 + j))
    return np.array(V, float), np.array(U, float), np.array(F)


def torus(R, r, y, u0, u1, seg_small=4):
    V, U, F = [], [], []
    for j in range(SEG + 1):
        th = 2 * math.pi * j / SEG
        for k in range(seg_small + 1):
            ph = 2 * math.pi * k / seg_small
            rr = R + r * math.cos(ph)
            V.append((rr * math.cos(th), y + r * math.sin(ph), rr * math.sin(th)))
            U.append((u0 + (u1 - u0) * j / SEG, k / seg_small))
    n = seg_small + 1
    for j in range(SEG):
        for k in range(seg_small):
            a, b, c, d = j * n + k, (j + 1) * n + k, (j + 1) * n + k + 1, j * n + k + 1
            F += [(a, c, b), (a, d, c)]
    return np.array(V, float), np.array(U, float), np.array(F)


def cake(top):
    parts = []
    ICING, GOLD = (0.02, 0.48), (0.52, 0.98)
    y = top
    # stand: a gold plate on a short foot
    parts.append(cylinder(0.075, y, y + 0.05, *GOLD))
    parts.append(cylinder(0.40, y + 0.05, y + 0.075, *GOLD))
    y += 0.075
    tiers = [(0.33, 0.22), (0.245, 0.20), (0.16, 0.18)]
    for r, h in tiers:
        parts.append(cylinder(r, y, y + h, *ICING))
        parts.append(torus(r, 0.018, y + 0.012, *GOLD))
        parts.append(torus(r - 0.01, 0.014, y + h, *ICING))
        y += h
    # topper: a small gold double ring (the two faces of Xeen joined) on a stem
    parts.append(cylinder(0.012, y, y + 0.07, *GOLD))
    for dx in (-0.035, 0.035):
        v, u, f = torus(0.045, 0.009, 0.0, *GOLD)
        v = v[:, [0, 2, 1]]                    # stand the ring up (in the x-y plane)
        v[:, 0] += dx; v[:, 1] += y + 0.12
        f = f[:, ::-1]
        parts.append((v, u, f))
    V, U, F, off = [], [], [], 0
    for v, u, f in parts:
        V.append(v); U.append(u); F.append(f + off); off += len(v)
    return np.vstack(V), np.vstack(U), np.vstack(F), y + 0.17


def normals(v, f):
    n = np.zeros_like(v)
    fn = np.cross(v[f[:, 1]] - v[f[:, 0]], v[f[:, 2]] - v[f[:, 0]])
    for k in range(3):
        np.add.at(n, f[:, k], fn)
    return n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)


def main():
    out = sys.argv[1]
    g = Glb(TABLE)
    j = g.json
    prims = j['meshes'][0]['primitives']
    tv = np.vstack([g.accessor(p['attributes']['POSITION']) for p in prims])
    centre = np.abs(tv[:, 0]) ** 2 + np.abs(tv[:, 2]) ** 2 < 0.5 ** 2
    top = float(tv[centre, 1].max())
    v, u, f, cake_top = cake(top)
    n = normals(v, f)
    img = atlas()
    buf = io.BytesIO(); img.save(buf, 'PNG'); data = buf.getvalue()
    g.bin += b'\0' * (-len(g.bin) % 4)
    j['bufferViews'].append({'buffer': 0, 'byteOffset': len(g.bin), 'byteLength': len(data)})
    g.bin += data
    j['buffers'][0]['byteLength'] = len(g.bin)
    j['images'].append({'bufferView': len(j['bufferViews']) - 1, 'mimeType': 'image/png', 'name': 'xeen_cake_basecolor'})
    j['textures'].append({'sampler': 0, 'source': len(j['images']) - 1})
    j['materials'].append({'name': 'xeen_cake', 'doubleSided': False,
                           'pbrMetallicRoughness': {'baseColorTexture': {'index': len(j['textures']) - 1},
                                                    'metallicFactor': 0, 'roughnessFactor': 0.6}})
    prims.append({'attributes': {'POSITION': g.append_accessor(v, 'VEC3'), 'NORMAL': g.append_accessor(n, 'VEC3'),
                                 'TEXCOORD_0': g.append_accessor(u, 'VEC2')},
                  'indices': None, 'material': len(j['materials']) - 1})
    idx = np.ascontiguousarray(f.astype(np.uint32).reshape(-1))
    g.bin += b'\0' * (-len(g.bin) % 4)
    j['bufferViews'].append({'buffer': 0, 'byteOffset': len(g.bin), 'byteLength': idx.nbytes, 'target': 34963})
    g.bin += idx.tobytes()
    j['accessors'].append({'bufferView': len(j['bufferViews']) - 1, 'componentType': 5125, 'count': len(idx),
                           'type': 'SCALAR'})
    prims[-1]['indices'] = len(j['accessors']) - 1
    j['buffers'][0]['byteLength'] = len(g.bin)
    j['nodes'][0]['name'] = 'xeen_deco_cake'
    j['meshes'][0]['name'] = 'xeen_deco_cake'
    j.setdefault('asset', {})['generator'] = 'OpenYAMM xeen_p5props_claude build_cake.py (MM9 roundtable + built cake)'
    g.write(out)
    print(json.dumps({'table_top': top, 'cake_top': cake_top, 'cake_triangles': int(len(f)),
                      'table_triangles': int(sum(g.accessor(p['indices']).shape[0] for p in prims[:-1]) // 3)}))


if __name__ == '__main__':
    main()
