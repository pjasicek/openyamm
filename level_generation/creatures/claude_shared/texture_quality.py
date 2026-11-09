#!/usr/bin/env python3
"""Texture-quality measurements of creature GLBs (TEXTURE_QUALITY_PASS.md): how much of the base-colour atlas the UVs
use, how evenly texels are spread over the surface, how fragmented and stretched the UV islands are.

Usage: texture_quality.py <glb> [<glb> ...] [--json out.json] [--heatmap out_prefix] [--by-bone]

Per material with a base-colour texture (LOD0 only: the first mesh that uses it), area-weighted over triangles:
- atlas: union of the UV triangles rasterised at 2048 by texel centre (overlaps and mirrored halves count once), in %;
  uv_sum: the plain sum of UV triangle areas (counts overlaps twice; equal to atlas when nothing overlaps);
- density: texels per creature size (sqrt(texel area / surface area) x the largest bounding-box extent), p10/p50/p90,
  and spread = p90 / p10 (1.0 is perfectly even; the head is meant to be denser, so 1.5-2 is normal);
- equivalent: the size of a square texture that, fully used at the median density, would give the same detail
  (sqrt(atlas use) x texture size) - the number to compare between models;
- islands: UV-connected pieces (an edge joins two triangles only when both ends share UV coordinates), and the share
  of the surface on islands of fewer than 8 triangles (fragments: Meshy paints each one as a separate blotch);
- stretch: ratio of the UV map's singular values per triangle (1 = no shear or stretch), p90; above 2 is visibly
  smeared in one direction.
--by-bone adds the median density per dominant joint (skinned meshes), lowest first.
--heatmap writes <prefix>_density.png (UV space, log2 of density over the median or --reference: blue -1 or less, green
0, red +1 or more) and <prefix>_stretch.png (white 1, red 3 or more); render them on the model with render_glb_views.py
`<image substring>=<heatmap png>`.
"""
import argparse
import io
import json
import struct
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

COMPONENTS = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}
TYPES = {5126: np.float32, 5125: np.uint32, 5123: np.uint16, 5121: np.uint8}


def read_glb(path):
    raw = Path(path).read_bytes()
    n = struct.unpack_from('<I', raw, 12)[0]
    return json.loads(raw[20:20 + n]), raw[28 + n:]


def accessor(doc, binary, index):
    a = doc['accessors'][index]
    view = doc['bufferViews'][a['bufferView']]
    count, width = a['count'], COMPONENTS[a['type']]
    dtype = np.dtype(TYPES[a['componentType']])
    offset = view.get('byteOffset', 0) + a.get('byteOffset', 0)
    stride = view.get('byteStride', 0) or dtype.itemsize * width
    rows = np.frombuffer(binary, np.uint8, count=stride * (count - 1) + dtype.itemsize * width, offset=offset)
    out = np.lib.stride_tricks.as_strided(rows, (count, dtype.itemsize * width), (stride, 1))
    values = np.frombuffer(out.copy().tobytes(), dtype).reshape(count, width).astype(np.float64)
    if a.get('normalized'):
        values /= np.iinfo(dtype).max
    return values


def image_size(doc, binary, texture):
    image = doc['images'][doc['textures'][texture]['source']]
    view = doc['bufferViews'][image['bufferView']]
    start = view.get('byteOffset', 0)
    return Image.open(io.BytesIO(binary[start:start + view['byteLength']])).size


def islands(tri_uv, tri_pos):
    """Union-find over triangles sharing an edge with identical positions and UVs on both ends."""
    n = len(tri_uv)
    parent = np.arange(n)

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    keys = np.concatenate([np.round(tri_pos, 5), np.round(tri_uv, 6)], -1)
    edges = {}
    for t in range(n):
        for k in range(3):
            a, b = tuple(keys[t, k]), tuple(keys[t, (k + 1) % 3])
            edge = (a, b) if a < b else (b, a)
            other = edges.setdefault(edge, t)
            if other != t:
                ra, rb = find(t), find(other)
                if ra != rb:
                    parent[ra] = rb
    return np.array([find(i) for i in range(n)])


def weighted_percentile(values, weights, q):
    order = np.argsort(values)
    cumulative = np.cumsum(weights[order])
    return float(np.interp(np.asarray(q) / 100 * cumulative[-1], cumulative, values[order]))


def raster_union(tri_uv, size=2048):
    """Texels whose centre lies inside any UV triangle (overlapping and mirrored halves count once)."""
    covered = np.zeros((size, size), bool)
    p = tri_uv * size
    for t in p:
        x0, y0 = np.maximum(np.floor(t.min(0)).astype(int), 0)
        x1, y1 = np.minimum(np.ceil(t.max(0)).astype(int), size)
        if x1 <= x0 or y1 <= y0:
            continue
        gy, gx = np.mgrid[y0:y1, x0:x1] + 0.5
        a, b, c = t
        w0 = (b[0] - a[0]) * (gy - a[1]) - (b[1] - a[1]) * (gx - a[0])
        w1 = (c[0] - b[0]) * (gy - b[1]) - (c[1] - b[1]) * (gx - b[0])
        w2 = (a[0] - c[0]) * (gy - c[1]) - (a[1] - c[1]) * (gx - c[0])
        covered[y0:y1, x0:x1] |= ((w0 >= 0) & (w1 >= 0) & (w2 >= 0)) | ((w0 <= 0) & (w1 <= 0) & (w2 <= 0))
    return covered


def heat(values, lo, hi, colours):
    x = np.clip((values - lo) / (hi - lo), 0, 1) * (len(colours) - 1)
    i = np.minimum(x.astype(int), len(colours) - 2)
    f = (x - i)[:, None]
    c = np.asarray(colours, np.float64)
    return c[i] * (1 - f) + c[i + 1] * f


def paint(tri_uv, colours, path, size=1024):
    image = Image.new('RGB', (size, size), (40, 40, 40))
    draw = ImageDraw.Draw(image)
    for t, c in zip(tri_uv, colours):
        draw.polygon([(float(u) * size, float(v) * size) for u, v in t], fill=tuple(int(x) for x in c))
    image.save(path)


def measure(path, heatmap=None, by_bone=False, reference=None):
    doc, binary = read_glb(path)
    result = {'glb': str(path), 'materials': []}
    joint_names = None
    if by_bone and doc.get('skins'):
        joint_names = [doc['nodes'][j].get('name', str(j)) for j in doc['skins'][0]['joints']]
    gathered = {}
    for mesh in doc['meshes']:
        for prim in mesh['primitives']:
            if 'material' not in prim or 'TEXCOORD_0' not in prim['attributes']:
                continue
            material = doc['materials'][prim['material']]
            texture = material.get('pbrMetallicRoughness', {}).get('baseColorTexture')
            if texture is None:
                continue
            image = doc['textures'][texture['index']]['source']
            if image in gathered and gathered[image]['mesh'] != mesh.get('name'):
                continue                              # a lower LOD sharing the texture
            entry = gathered.setdefault(image, {'mesh': mesh.get('name'), 'name': material.get('name', '?'),
                                                'size': image_size(doc, binary, texture['index']),
                                                'pos': [], 'uv': [], 'bone': []})
            pos = accessor(doc, binary, prim['attributes']['POSITION'])
            uv = accessor(doc, binary, prim['attributes']['TEXCOORD_0'])
            idx = accessor(doc, binary, prim['indices']).astype(np.int64).reshape(-1, 3)
            entry['pos'].append(pos[idx])
            entry['uv'].append(uv[idx])
            if joint_names and 'JOINTS_0' in prim['attributes']:
                joints = accessor(doc, binary, prim['attributes']['JOINTS_0']).astype(int)
                weights = accessor(doc, binary, prim['attributes']['WEIGHTS_0'])
                dominant = joints[np.arange(len(joints)), weights.argmax(1)]
                entry['bone'].append(np.array([np.bincount(d, minlength=1).argmax() for d in dominant[idx]]))
    for image, entry in gathered.items():
        tri_pos, tri_uv = np.concatenate(entry['pos']), np.concatenate(entry['uv'])
        width, height = entry['size']
        extent = float(np.ptp(tri_pos.reshape(-1, 3), 0).max())
        e1, e2 = tri_pos[:, 1] - tri_pos[:, 0], tri_pos[:, 2] - tri_pos[:, 0]
        area3 = 0.5 * np.linalg.norm(np.cross(e1, e2), axis=1)
        px = tri_uv * [width, height]
        d1, d2 = px[:, 1] - px[:, 0], px[:, 2] - px[:, 0]
        area2 = 0.5 * np.abs(d1[:, 0] * d2[:, 1] - d1[:, 1] * d2[:, 0])
        ok = area3 > 1e-12
        density = np.sqrt(area2[ok] / area3[ok]) * extent
        w = area3[ok]
        # stretch: local 2D frame on the 3D triangle, Jacobian of 3D -> texel map, singular value ratio
        x_axis = e1 / np.maximum(np.linalg.norm(e1, axis=1, keepdims=True), 1e-12)
        normal = np.cross(e1, e2)
        y_axis = np.cross(normal, x_axis)
        y_axis /= np.maximum(np.linalg.norm(y_axis, axis=1, keepdims=True), 1e-12)
        p1 = np.stack([np.einsum('ij,ij->i', e1, x_axis), np.einsum('ij,ij->i', e1, y_axis)], 1)
        p2 = np.stack([np.einsum('ij,ij->i', e2, x_axis), np.einsum('ij,ij->i', e2, y_axis)], 1)
        P = np.stack([p1, p2], 2)[ok]
        T = np.stack([d1, d2], 2)[ok]
        J = T @ np.linalg.pinv(P)
        sv = np.linalg.svd(J, compute_uv=False)
        stretch = sv[:, 0] / np.maximum(sv[:, 1], 1e-9)
        union = raster_union(tri_uv)
        isl = islands(tri_uv, tri_pos)
        _, inverse, counts = np.unique(isl, return_inverse=True, return_counts=True)
        fragment = counts[inverse] < 8
        p10, p50, p90 = (weighted_percentile(density, w, q) for q in (10, 50, 90))
        record = {'material': entry['name'], 'texture': width, 'triangles': int(len(tri_uv)),
                  'atlas_pct': round(100 * float(union.mean()), 1),
                  'uv_sum_pct': round(100 * float(area2.sum() / (width * height)), 1),
                  'density_p10': round(p10), 'density_p50': round(p50), 'density_p90': round(p90),
                  'spread': round(p90 / max(p10, 1e-9), 2),
                  'equivalent_px': round(width * float(np.sqrt(union.mean()))),
                  'islands': int(len(counts)),
                  'fragment_surface_pct': round(100 * float(area3[fragment].sum() / area3.sum()), 1),
                  'stretch_p90': round(weighted_percentile(stretch, w, 90), 2)}
        if entry['bone']:
            bones = np.concatenate(entry['bone'])[ok]
            per = {}
            for b in np.unique(bones):
                m = bones == b
                if w[m].sum() / w.sum() > 0.003:
                    per[joint_names[b]] = {'density_p50': round(weighted_percentile(density[m], w[m], 50)),
                                           'stretch_p90': round(weighted_percentile(stretch[m], w[m], 90), 2),
                                           'surface_pct': round(100 * float(w[m].sum() / w.sum()), 1)}
            record['by_bone'] = dict(sorted(per.items(), key=lambda kv: kv[1]['density_p50']))
        result['materials'].append(record)
        if heatmap:
            rel = np.full(len(tri_uv), 0.0)
            rel[ok] = np.log2(np.maximum(density, 1e-6) / (reference or p50))
            uvs = tri_uv.copy()
            paint(uvs, heat(rel, -1, 1, [(40, 60, 255), (40, 220, 80), (255, 40, 40)]), f'{heatmap}_density.png')
            st = np.ones(len(tri_uv))
            st[ok] = stretch
            paint(uvs, heat(st, 1, 3, [(255, 255, 255), (255, 200, 60), (255, 30, 30)]), f'{heatmap}_stretch.png')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('glbs', nargs='+')
    parser.add_argument('--json')
    parser.add_argument('--heatmap')
    parser.add_argument('--by-bone', action='store_true')
    parser.add_argument('--reference', type=float, help='heatmap density shown green (default: each model\'s median); '
                        'pass the before median to compare two versions on one scale')
    args = parser.parse_args()
    results = [measure(p, args.heatmap, args.by_bone, args.reference) for p in args.glbs]
    for r in results:
        for m in r['materials']:
            print(f"{Path(r['glb']).name} {m['material']} {m['texture']}px: atlas {m['atlas_pct']}% "
                  f"(uv sum {m['uv_sum_pct']}%) "
                  f"(equivalent {m['equivalent_px']}px), density p10/p50/p90 {m['density_p10']}/{m['density_p50']}/"
                  f"{m['density_p90']} spread {m['spread']}, islands {m['islands']} "
                  f"(fragments {m['fragment_surface_pct']}% of surface), stretch p90 {m['stretch_p90']}")
            for bone, v in list(m.get('by_bone', {}).items())[:6]:
                print(f'    {bone}: density {v["density_p50"]}, stretch p90 {v["stretch_p90"]}, '
                      f'{v["surface_pct"]}% of surface')
    if args.json:
        Path(args.json).write_text(json.dumps(results, indent=1))


if __name__ == '__main__':
    main()
