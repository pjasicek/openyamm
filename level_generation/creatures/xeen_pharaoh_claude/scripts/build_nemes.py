#!/usr/bin/env python3
"""Build the Dragon Pharaoh's nemes (striped headcloth) as a static attachment on B_Head.

    build_nemes.py <body.glb> <spec nemes.json> <out_model_space.glb> <out_attachment.glb> [--report report.json]

The hood is a bicubic surface through rows of control points (front edge, side, back midline, mirrored), closed at the
top by a pole fan; lappets hang from its front corners and a short drape behind the neck. Texture: horizontal gold and
lapis bands (v), a gold band along every edge, a small gold uraeus on the brow. The model-space copy is for review
(load it with the body in rest pose); the attachment is the same mesh in B_Head's space (inverse bind matrix)."""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy.interpolate import CubicSpline
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pglb import load, lod0_body  # noqa: E402
from gltf_write import Writer, smooth_normals  # noqa: E402


def hexrgb(h):
    return np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], float)


def hood_grid(spec):
    mx = spec['midline_x']
    rows = spec['rows']
    ctrl = []
    for r in rows:
        F, S, B = np.array(r['F'], float), np.array(r['S'], float), np.array(r['B'], float)
        B[0] = mx
        mirror = lambda p: np.array([2 * mx - p[0], p[1], p[2]])
        ctrl.append([F, S, B, mirror(S), mirror(F)])
    ctrl = np.array(ctrl)                      # rows x 5 x 3
    uk = np.array([0.0, 0.25, 0.5, 0.75, 1.0])
    cols = spec['cols']
    us = np.linspace(0, 1, cols + 1)
    across = np.array([CubicSpline(uk, ctrl[i], axis=0)(us) for i in range(len(ctrl))])  # rows x cols x 3
    nr = (len(ctrl) - 1) * spec['rows_per_span'] + 1
    vk = np.linspace(0, 1, len(ctrl))
    vs = np.linspace(0, 1, nr)
    grid = CubicSpline(vk, across, axis=0)(vs)  # nr x cols x 3
    return grid, us, vs


def build(spec, head_centre):
    grid, us, vs = hood_grid(spec)
    nr, nc = grid.shape[0], grid.shape[1]
    verts, uvs, faces = [], [], []
    vstep = 1.0 / (nr - 1)
    total_rows = nr - 1 + spec['lappet']['rows'] + 2   # texture v spans hood + lappet
    def v_of(row):
        return row / total_rows
    index = {}
    for i in range(nr):
        for j in range(nc):
            index[(i, j)] = len(verts)
            verts.append(grid[i, j]); uvs.append((us[j], v_of(i)))
    for i in range(nr - 1):
        for j in range(nc - 1):
            a, b, c, d = index[(i, j)], index[(i, j + 1)], index[(i + 1, j + 1)], index[(i + 1, j)]
            faces += [(a, b, c), (a, c, d)]
    # top pole fan
    pole = len(verts); verts.append(np.array(spec['pole'], float)); uvs.append((0.5, 0.0))
    for j in range(nc - 1):
        faces.append((pole, index[(0, j + 1)], index[(0, j)]))
    # close the top front gap: the first row's two front ends meet over the brow (fan already covers it)
    # lappets (left: u in range; right: mirrored range) hanging from the last row
    lp = spec['lappet']
    last = nr - 1
    def hang(js, bottom_y, dz, dx_in, nrows, narrow=1.0, side=1):
        top = np.array([grid[last, j] for j in js])
        centre_x = top[:, 0].mean()
        ids_prev = [index[(last, j)] for j in js]
        for k in range(1, nrows + 1):
            t = k / nrows
            row = top.copy()
            row[:, 1] = top[:, 1] + (bottom_y - top[:, 1]) * t
            row[:, 2] = top[:, 2] + dz * t
            row[:, 0] = centre_x + (top[:, 0] - centre_x) * (1 + (narrow - 1) * t) + dx_in * t * side
            ids = []
            for q, p in enumerate(row):
                ids.append(len(verts)); verts.append(p); uvs.append((us[js[q]], v_of(last + k * (spec['lappet']['rows'] + 2) / (nrows + 2) if False else last + k)))
            for q in range(len(js) - 1):
                a, b, c, d = ids_prev[q], ids_prev[q + 1], ids[q + 1], ids[q]
                faces.extend([(a, b, c), (a, c, d)])
            ids_prev = ids
    jl = [j for j in range(nc) if lp['u'][0] <= us[j] <= lp['u'][1]]
    jr = [j for j in range(nc) if 1 - lp['u'][1] <= us[j] <= 1 - lp['u'][0]]
    hang(jl, lp['bottom_y'], lp['dz_bottom'], lp['dx_bottom'], lp['rows'], side=1)
    hang(jr, lp['bottom_y'], lp['dz_bottom'], -lp['dx_bottom'], lp['rows'], side=1)
    dp = spec['drape']
    jd = [j for j in range(nc) if dp['u'][0] <= us[j] <= dp['u'][1]]
    hang(jd, dp['bottom_y'], dp['dz_bottom'], 0.0, dp['rows'], narrow=dp['narrow'])
    v = np.array(verts); uv = np.array(uvs, float); f = np.array(faces, np.int64)
    # orient faces outward (away from the head centre)
    fc = v[f].mean(1); fn = np.cross(v[f[:, 1]] - v[f[:, 0]], v[f[:, 2]] - v[f[:, 0]])
    flip = (fn * (fc - head_centre)).sum(1) < 0
    f[flip] = f[flip][:, ::-1]
    return v, uv, f


def uraeus(spec):
    """A small rearing cobra on the brow: a tapered body (8-gon) and a hood disc, gold, in model space."""
    rows = spec['rows']
    mx = spec['midline_x']
    F = np.array(rows[1]['F']); base = np.array([mx, F[1] + 0.004, F[2] + 0.004])
    path = [base + np.array([0, 0.000, 0.000]), base + np.array([0, 0.014, 0.010]), base + np.array([0, 0.030, 0.012]),
            base + np.array([0, 0.040, 0.020])]
    radii = [0.009, 0.007, 0.006, 0.004]
    verts, faces, uvs = [], [], []
    n = 8
    for k, (c, r) in enumerate(zip(path, radii)):
        for a in range(n):
            th = 2 * np.pi * a / n
            verts.append(c + np.array([np.cos(th) * r * (1.6 if k == 2 else 1.0), 0, np.sin(th) * r]))
            uvs.append((0.02, 0.5))
    for k in range(len(path) - 1):
        for a in range(n):
            i0, i1 = k * n + a, k * n + (a + 1) % n
            j0, j1 = i0 + n, i1 + n
            faces += [(i0, i1, j1), (i0, j1, j0)]
    tip = len(verts); verts.append(path[-1] + np.array([0, 0.008, 0.006])); uvs.append((0.02, 0.5))
    for a in range(n):
        faces.append(((len(path) - 1) * n + a, (len(path) - 1) * n + (a + 1) % n, tip))
    bottom = len(verts); verts.append(path[0] - np.array([0, 0.004, 0])); uvs.append((0.02, 0.5))
    for a in range(n):
        faces.append((a + 0, bottom, (a + 1) % n))
    return np.array(verts), np.array(uvs, float), np.array(faces)


def texture(spec, size=512):
    gold, blue = hexrgb(spec['gold']), hexrgb(spec['blue'])
    n = spec['stripes']
    yy, xx = np.mgrid[0:size, 0:size] / size
    # v stripes: alternating gold / blue, the blue a little wider; thin dark seams between
    phase = (yy * n * 2) % 2.0
    is_gold = phase < 0.85
    img = np.where(is_gold[..., None], gold, blue)
    seam = (np.abs(((yy * n * 2) % 1.0) - 0.0) < 0.03) | (np.abs(phase - 0.85) < 0.03)
    img = np.where(seam[..., None], img * 0.55, img)
    band = spec['band']
    edge = (xx < band) | (xx > 1 - band) | (yy > 0.985)
    img = np.where(edge[..., None], gold * 1.08, img)
    rng = np.random.default_rng(7)
    noise = rng.normal(0, 1, (size, size))
    noise = np.asarray(Image.fromarray(((noise * 20 + 128).clip(0, 255)).astype(np.uint8)).filter(
        ImageFilter.GaussianBlur(1.2)), float) / 128 - 1
    weave = 1 + 0.06 * np.sin(xx * size * 1.7) * np.sin(yy * size * 1.3) + 0.05 * noise
    img = (img * weave[..., None]).clip(0, 255).astype(np.uint8)
    mr = np.zeros((size, size, 3), np.uint8)
    gold_px = np.all(np.abs(img.astype(int) - gold) < 60, axis=2) | edge
    mr[..., 1] = np.where(gold_px, 110, 200)      # roughness: gold smoother
    mr[..., 2] = np.where(gold_px, 200, 0)        # metallic: gold threads
    return Image.fromarray(img), Image.fromarray(mr)


def main():
    body, spec_path, out_model, out_att = sys.argv[1:5]
    report = sys.argv[sys.argv.index('--report') + 1] if '--report' in sys.argv else None
    spec = json.load(open(spec_path))
    g, m, names = load(body)
    W = m.world({})
    head = names['B_Head']
    centre = np.array([spec['midline_x'], 1.705, -0.07])
    v, uv, f = build(spec, centre)
    uv_v, uv_uv, uv_f = uraeus(spec)
    # clearance: LOD0 body vertices (rest) that lie outside the hood near it, not counting crest (head/neck) vertices
    prim, dom = lod0_body(m)
    P = prim['positions']
    n = smooth_normals(v, f)
    tree = cKDTree(v)
    d, k = tree.query(P)
    out = ((P - v[k]) * n[k]).sum(1)
    near = d < 0.06
    headneck = np.isin(dom, [names['B_Head'], names['B_Neck']])
    poke_other = near & (out > 0.003) & ~headneck
    poke_head = near & (out > 0.0) & headneck
    rep = {'hood_vertices': int(len(v)), 'hood_triangles': int(len(f)), 'uraeus_triangles': int(len(uv_f)),
           'body_pokes_non_head': int(poke_other.sum()),
           'body_pokes_non_head_max_mm': float(out[poke_other].max() * 1000) if poke_other.any() else 0.0,
           'head_neck_vertices_outside': int(poke_head.sum())}
    print(json.dumps(rep))
    if report:
        json.dump(rep, open(report, 'w'), indent=1)
    tex, mr = texture(spec)
    Path(out_model).parent.mkdir(parents=True, exist_ok=True)
    tex.save(str(Path(out_model).with_suffix('.basecolor.png')))
    ibm = m.inverse_binds[m.joints.index(head)]
    levels = []
    for cols, rps, lrows, drows in ((spec['cols'], spec['rows_per_span'], spec['lappet']['rows'], spec['drape']['rows']),
                                    (20, 2, 3, 2), (12, 1, 2, 1)):
        s2 = json.loads(json.dumps(spec))
        s2['cols'], s2['rows_per_span'] = cols, rps
        s2['lappet']['rows'], s2['drape']['rows'] = lrows, drows
        lv, luv, lf = build(s2, centre)
        if not levels:
            vv = np.vstack([lv, uv_v]); ff = np.vstack([lf, uv_f + len(lv)]); uu = np.vstack([luv, uv_uv])
        else:
            vv, ff, uu = lv, lf, luv
        levels.append((vv, uu, ff))
    for path, M in ((out_model, np.eye(4)), (out_att, ibm)):
        w = Writer()
        bt = w.image(tex, 'nemes_basecolor')
        mt = w.image(mr, 'nemes_mr')
        mat = w.material('Nemes', bt, mt, roughness=1.0, metallic=1.0)
        meshes = []
        for li, (vv, uu, ff) in enumerate(levels):
            vt = (np.c_[vv, np.ones(len(vv))] @ M.T)[:, :3]
            nt = smooth_normals(vt, ff)
            meshes.append(w.mesh('Nemes' if li == 0 else f'Nemes_LOD{li}', [(vt, nt, uu, ff, mat)]))
        w.doc['meshes'][meshes[0]]['extras'] = {'openyamm_lods': meshes[1:]}
        w.node('Nemes', meshes[0])
        w.write(path)
    print('LOD triangles', [len(l[2]) for l in levels])
    print('WROTE', out_model, out_att, 'triangles', len(f) + len(uv_f))


if __name__ == '__main__':
    main()
