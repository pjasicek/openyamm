#!/usr/bin/env python3
"""Build the Dragon Pharaoh's open book as a static attachment on B_L_Hand (built mesh, 256 px atlas: lapis leather
cover with a gold border, cream pages with ruled lines of text, page edges).

    build_book.py <book_local.json> <out_attachment.glb> [<out_book_space.glb>]"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gltf_write import Writer  # noqa: E402


def atlas():
    s = 256
    img = Image.new('RGB', (s, s), (30, 50, 140))
    d = ImageDraw.Draw(img)
    # cover (u 0..0.5): lapis leather, gold border and a gold ankh-like boss
    rng = np.random.default_rng(3)
    cov = (np.array([30, 52, 140]) * (1 + 0.08 * rng.normal(0, 1, (s, s // 2)))[..., None]).clip(0, 255).astype(np.uint8)
    img.paste(Image.fromarray(cov), (0, 0))
    d.rectangle([5, 5, 122, 250], outline=(214, 170, 64), width=5)
    d.ellipse([46, 100, 82, 136], outline=(214, 170, 64), width=4)
    d.line([64, 136, 64, 190], fill=(214, 170, 64), width=5)
    d.line([44, 152, 84, 152], fill=(214, 170, 64), width=5)
    # pages (u 0.5..1, v 0..0.5): cream with text rows and a red rubric
    d.rectangle([128, 0, 255, 127], fill=(236, 224, 192))
    for k, y in enumerate(range(12, 120, 7)):
        x1 = 245 if k % 6 != 5 else 200
        col = (150, 40, 30) if k == 0 else (70, 56, 40)
        d.line([138, y, x1, y], fill=col, width=2)
    # page edges (u 0.5..1, v 0.5..1): striated cream
    for y in range(128, 256):
        c = 215 + int(18 * np.sin(y * 1.9))
        d.line([128, y, 255, y], fill=(c, c - 12, c - 40))
    return img.filter(ImageFilter.GaussianBlur(0.4))


def box(lo, hi, uvrect_top, uvrect_side, uvrect_bottom):
    """Axis-aligned box: 6 faces, 24 vertices; top (+Y) face takes uvrect_top, bottom uvrect_bottom, sides side."""
    x0, y0, z0 = lo; x1, y1, z1 = hi
    faces = {
        '+y': [(x0, y1, z1), (x1, y1, z1), (x1, y1, z0), (x0, y1, z0)],
        '-y': [(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)],
        '+x': [(x1, y0, z1), (x1, y0, z0), (x1, y1, z0), (x1, y1, z1)],
        '-x': [(x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (x0, y1, z0)],
        '+z': [(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)],
        '-z': [(x1, y0, z0), (x0, y0, z0), (x0, y1, z0), (x1, y1, z0)],
    }
    V, U, F, N = [], [], [], []
    for key, quad in faces.items():
        r = uvrect_top if key == '+y' else uvrect_bottom if key == '-y' else uvrect_side
        base = len(V)
        V += quad
        u0, v0, u1, v1 = r
        U += [(u0, v1), (u1, v1), (u1, v0), (u0, v0)]
        n = {'+y': (0, 1, 0), '-y': (0, -1, 0), '+x': (1, 0, 0), '-x': (-1, 0, 0), '+z': (0, 0, 1), '-z': (0, 0, -1)}[key]
        N += [n] * 4
        F += [(base, base + 1, base + 2), (base, base + 2, base + 3)]
    return np.array(V, float), np.array(N, float), np.array(U, float), np.array(F)


def rot_z(deg):
    a = np.radians(deg)
    return np.array([[np.cos(a), -np.sin(a), 0], [np.sin(a), np.cos(a), 0], [0, 0, 1]])


def book_mesh(b):
    w, h = b['width'], b['height']
    pt, ct = b['page_thickness'], b['cover_thickness']
    COVER = (0.0, 0.0, 0.5, 1.0); PAGE = (0.5, 0.0, 1.0, 0.5); EDGE = (0.5, 0.5, 1.0, 1.0)
    parts = []
    for side in (-1, 1):
        R = rot_z(side * b['valley_deg'])
        half = w / 2
        lo_c, hi_c = (0.0, 0.0, -h / 2), (half, ct, h / 2)
        lo_p, hi_p = (0.004, ct, -h / 2 + 0.006), (half - 0.007, ct + pt, h / 2 - 0.006)
        for lo, hi, top, sidee, bottom in ((lo_c, hi_c, COVER, COVER, COVER), (lo_p, hi_p, PAGE, EDGE, EDGE)):
            v, n, u, f = box(lo, hi, top, sidee, bottom)
            if side < 0:
                v[:, 0] = -v[:, 0]; n[:, 0] = -n[:, 0]; f = f[:, ::-1]
            parts.append(((R @ v.T).T, (R @ n.T).T, u, f))
    # spine: a thin rounded strip under the valley
    v, n, u, f = box((-0.008, -0.006, -h / 2), (0.008, 0.002, h / 2), COVER, COVER, COVER)
    parts.append((v, n, u, f))
    V, N, U, F = [], [], [], []
    off = 0
    for v, n, u, f in parts:
        V.append(v); N.append(n); U.append(u); F.append(f + off); off += len(v)
    return np.vstack(V), np.vstack(N), np.vstack(U), np.vstack(F)


def main():
    cfg = json.load(open(sys.argv[1]))
    out = sys.argv[2]
    B = np.array(cfg['book_in_B_L_Hand'])
    v, n, u, f = book_mesh(cfg['book'])
    tex = atlas()
    for path, M in ((out, B), (sys.argv[3] if len(sys.argv) > 3 else None, np.eye(4))):
        if path is None:
            continue
        w = Writer()
        t = w.image(tex, 'book_basecolor')
        mat = w.material('Book', t, roughness=0.75, double=False)
        vt = (np.c_[v, np.ones(len(v))] @ M.T)[:, :3]
        nt = n @ M[:3, :3].T
        mesh = w.mesh('Book', [(vt, nt, u, f, mat)])
        w.node('Book', mesh)
        w.write(path)
    print('WROTE', out, 'triangles', len(f))


if __name__ == '__main__':
    main()
