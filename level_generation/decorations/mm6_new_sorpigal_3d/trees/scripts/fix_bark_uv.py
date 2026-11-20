#!/usr/bin/env python3
"""Fix the swapped bark UV axes of an installed tree GLB in place (2026-10-16), without rebuilding it.

Bug: build_tree.py's branch_mesh() scaled Blender's curve UVs as if u ran around the bevel and v along the curve. Blender's
curve UVs run the other way (u along, v around), so each Sapling tube had u = t_along x `around` and v = t_around x
`along`: the bark tiled `along` times around the branch and only `around` times along it, which stretched the furrows
along every trunk and limb. The intended mapping is u = t_around x `around` (an integer, so the seam tiles) and
v = t_along x `along` (`along` = branch length / bark tile).

For each Bark primitive of every level in the LOD chain (LOD0 to LOD2; the impostor has no bark), the triangles are
split into connected parts. Positions are welded, so a tube's UV seam does not split it. Each part is classified:
 - a Sapling tube with the swapped mapping: its u gradient runs along the part's main axis. The fix is
   u' = v x around / along, where along = the part's v span (exact: rings are whole) and around = the build's rule
   from the widest circumference (2 pi r_max = along / |grad v|): max(1, round(2 pi r_max x 0.8 / tile)), a whole
   number so the seam tiles. And v' = u / (median |grad u| x tile), so the bark runs one tile per `tile` metres
   along the branch, the build's density.
 - a root spur or prop root (add_roots / add_aerial_roots: already u around, v along): its v gradient runs along the
   axis. It is left unchanged.
Only the TEXCOORD_0 floats of the fixed parts change, written in place, so the file layout, geometry, normals,
COLOR_0, other primitives and bounds stay byte-identical. The texel density along the branch is the build's
(1 tile per `tile` m).
Usage: fix_bark_uv.py <in.glb> <out.glb> [--tile 0.8] [--material Bark]"""
import argparse
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[5] / 'tools'))
import link_static_model_lods as link  # noqa: E402

DTYPE = {5126: np.float32, 5125: np.uint32, 5123: np.uint16, 5121: np.uint8}
WIDTH = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}


def view_of(doc, index):
    a = doc['accessors'][index]; v = doc['bufferViews'][a['bufferView']]
    dt = np.dtype(DTYPE[a['componentType']]); w = WIDTH[a['type']]
    stride = v.get('byteStride', dt.itemsize * w)
    return a, v.get('byteOffset', 0) + a.get('byteOffset', 0), stride, dt, w


def read(doc, binary, index):
    a, start, stride, dt, w = view_of(doc, index)
    raw = np.frombuffer(binary, np.uint8, a['count'] * stride, start).reshape(a['count'], stride)  # noqa: F841
    return raw[:, :dt.itemsize * w].copy().view(dt).reshape(a['count'], w)


def write(doc, binary, index, values):
    a, start, stride, dt, w = view_of(doc, index)
    values = np.ascontiguousarray(values.astype(dt)).reshape(a['count'], w)
    raw = values.view(np.uint8).reshape(a['count'], dt.itemsize * w)
    for row in range(a['count']):
        o = start + row * stride
        binary[o:o + dt.itemsize * w] = raw[row].tobytes()


def parts(tris, pos):
    """Connected parts of a triangle list, vertices welded by exact position."""
    key = {}
    weld = np.array([key.setdefault(tuple(p), len(key)) for p in np.round(pos, 6)])
    parent = list(range(len(key)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x
    for t in weld[tris]:
        for a, b in ((t[0], t[1]), (t[1], t[2])):
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[ra] = rb
    groups = defaultdict(list)
    for i, t in enumerate(weld[tris]):
        groups[find(t[0])].append(i)
    return [np.array(g) for g in groups.values()]


def gradients(p, uv):
    """Per triangle 3D gradients of u and v (in the triangle plane)."""
    e1, e2 = p[:, 1] - p[:, 0], p[:, 2] - p[:, 0]
    d1, d2 = uv[:, 1] - uv[:, 0], uv[:, 2] - uv[:, 0]
    g11, g12, g22 = (e1 * e1).sum(1), (e1 * e2).sum(1), (e2 * e2).sum(1)
    det = g11 * g22 - g12 * g12
    ok = det > 1e-14
    det = np.where(ok, det, 1.0)
    out = []
    for c in (0, 1):
        a = (g22 * d1[:, c] - g12 * d2[:, c]) / det
        b = (g11 * d2[:, c] - g12 * d1[:, c]) / det
        out.append(a[:, None] * e1 + b[:, None] * e2)
    return out[0], out[1], ok


def fix_primitive(doc, binary, prim, tile, report):
    pos = read(doc, binary, prim['attributes']['POSITION']).astype(np.float64)
    uv = read(doc, binary, prim['attributes']['TEXCOORD_0']).astype(np.float64)
    tris = read(doc, binary, prim['indices']).reshape(-1, 3).astype(np.int64)
    new = uv.copy()
    done = set()
    for part in parts(tris, pos):
        t = tris[part]; verts = np.unique(t)
        p, q = pos[t], uv[t]
        gu, gv, ok = gradients(p, q)
        if ok.sum() < 3:
            report.append(('skip-degenerate', len(part))); continue
        centred = pos[verts] - pos[verts].mean(0)
        axis = np.linalg.svd(centred, full_matrices=False)[2][0]
        nu, nv = np.linalg.norm(gu[ok], axis=1), np.linalg.norm(gv[ok], axis=1)
        cu = np.abs(gu[ok] @ axis) / np.maximum(nu, 1e-12)
        cv = np.abs(gv[ok] @ axis) / np.maximum(nv, 1e-12)
        if np.median(cu) <= np.median(cv):
            report.append(('root', len(part))); continue        # already u around, v along
        along = float(np.ptp(uv[verts, 1]))
        if along < 1e-6:
            report.append(('skip-flat', len(part))); continue
        density = float(np.median(nu))                  # old u per metre along the branch
        r_max = float(np.percentile(along / np.maximum(nv, 1e-12), 95)) / (2 * np.pi)
        x = 2 * np.pi * r_max * 0.8 / tile
        # tiles around: the build's rule, a whole number (so the seam tiles), at least 1; a twig thinner than one tile
        # round gets one tile around (texels squeezed around it, as build_tree.py does)
        around_new = max(1, round(x))
        report.append(('tube', len(part), round(density * along * tile, 2), round(x, 2), around_new, round(along, 2)))
        new[verts, 0] = uv[verts, 1] * around_new / along          # v spanned the ring: 0..along
        new[verts, 1] = uv[verts, 0] / (density * tile)            # along: one tile per `tile` metres
        done.update(verts.tolist())
    write(doc, binary, prim['attributes']['TEXCOORD_0'], new.astype(np.float32))
    return len(done)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('src', type=Path); ap.add_argument('out', type=Path)
    ap.add_argument('--tile', type=float, default=0.8); ap.add_argument('--material', default='Bark')
    args = ap.parse_args()
    # patch the file's own bytes (the BIN chunk in place), so everything but the fixed floats stays byte-identical
    raw = bytearray(args.src.read_bytes())
    doc, _ = link.read_glb(args.src)
    json_size = int.from_bytes(raw[12:16], 'little')
    binary = memoryview(raw)[28 + json_size:]
    node = next(n for n in doc['nodes'] if 'mesh' in n)
    chain = [node['mesh']] + doc['meshes'][node['mesh']].get('extras', {}).get('openyamm_lods', [])
    seen = set()
    for level, mi in enumerate(chain):
        for prim in doc['meshes'][mi]['primitives']:
            if doc['materials'][prim['material']]['name'] != args.material:
                continue
            uv_index = prim['attributes']['TEXCOORD_0']
            assert uv_index not in seen, 'TEXCOORD_0 accessor shared between bark primitives'
            seen.add(uv_index)
            report = []
            fixed = fix_primitive(doc, binary, prim, args.tile, report)
            tubes = [r for r in report if r[0] == 'tube']
            # r[2]: the build's integer `around` recovered from |grad u| (a check: near-integer when the old mapping
            # was linear); r[3]: tiles around from the circumference; r[4]: tiles around after the fix
            odd = [r for r in tubes if abs(r[2] - round(r[2])) > 0.3 and r[5] > 0.31]
            print(f'LOD{level} {doc["meshes"][mi]["name"]}: parts {len(report)}, tubes fixed {len(tubes)} '
                  f'({fixed} vertices), roots kept {sum(r[0] == "root" for r in report)}, '
                  f'skipped {sum(r[0].startswith("skip") for r in report)}, old around off-integer {len(odd)}')
            for r in odd[:4]:
                print('   ODD', r)
    binary.release()
    args.out.write_bytes(raw)
    print('FIXED', args.src.name, '->', args.out)


if __name__ == '__main__':
    main()
