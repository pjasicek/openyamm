#!/usr/bin/env python3
"""UV chart escape audit of a reduced GLB against its source (the Mummy's uv_escape.py, generalised; 2026-11-04).

A collapse that slides a seam vertex can leave a new face whose UV triangle reaches off the painted charts, into the
gutter or into another island: the smeared chevron on the reduced Mummy's forearm (204 faces). For every mesh node of
<reduced.glb> and every LOD (LOD0 = the node's mesh, LOD1-3 = mesh extras `openyamm_lods`), each primitive's UV triangles
are sampled (91 barycentric samples) against the charts of the *source LOD0*: the union of the source primitives that
use the same base-colour image (matched by image bytes, so renamed or split primitives still find their charts).

Per face it reports
  off    fraction of samples outside the source coverage (rasterised at the texture size, dilated by DIL texels);
  cross  fraction of samples on the coverage but not on the face's own chart (another island, e.g. abutting charts);
         the face's chart comes from its corners' UVs (source vertices), else the most common chart under it, and is
         tested exactly against that chart's own raster (overlapping and mirrored islands are not false positives);
  dist   furthest off-chart sample from the undilated coverage, in texels;
  colour mean |RGB| (0-255) between the off-chart samples and the nearest charted texel, worst over the tier base
         colour images (KHR_materials_variants): the gutters of the MM9 paints are not padded, so most escapes > 8.
UV triangles are rasterised with their edges, so zero-area UV slivers count as chart.
A face escapes when off > FRAC or cross > FRAC (Mummy defaults: DIL 2, FRAC 0.02). The same test runs on the source's
own LODs as a baseline, so LOD1-3 counts show what the reduction added (Blender's decimate escapes a little on its own).
A primitive whose image is not in the source (rebuilt and rebaked part) is checked against its own LOD0 charts instead
and flagged `own`.

Usage: reduction_uv_audit.py <reduced.glb> <source.glb> [--json out.json] [--res N] [--dil N] [--frac F]
       [--self-test]   (source against itself: the false-positive floor, expected 0)
Prints one line per node/LOD/primitive: faces, escaping (off / cross), worst, max dist, baseline escaping in the source.
The JSON keeps every escaping face (index, material, off, cross, dist, centroid and normal in the GLB's mesh space,
3D area) for close-up renders (reduction_uv_closeups.py)."""
import argparse
import hashlib
import json
import struct
import sys
from io import BytesIO
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

K = 12  # barycentric sample grid: (K + 1)(K + 2) / 2 = 91 samples per face


def read_glb(path):
    raw = Path(path).read_bytes()
    magic, version, length = struct.unpack_from('<III', raw)
    if magic != 0x46546c67 or version != 2:
        raise ValueError(f'{path}: not a GLB 2 file')
    size, _ = struct.unpack_from('<II', raw, 12)
    doc = json.loads(raw[20:20 + size])
    return doc, raw[28 + size:]


def view_bytes(doc, binary, view_index):
    v = doc['bufferViews'][view_index]
    o = v.get('byteOffset', 0)
    return binary[o:o + v['byteLength']]


def accessor(doc, binary, index):
    a = doc['accessors'][index]
    n = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}[a['type']]
    dt = np.dtype({5126: '<f4', 5125: '<u4', 5123: '<u2', 5121: 'u1', 5122: '<i2', 5120: 'i1'}[a['componentType']])
    v = doc['bufferViews'][a['bufferView']]
    off = v.get('byteOffset', 0) + a.get('byteOffset', 0)
    stride = v.get('byteStride', dt.itemsize * n)
    buf = np.frombuffer(binary, np.uint8, count=stride * (a['count'] - 1) + dt.itemsize * n, offset=off)
    rows = np.lib.stride_tricks.as_strided(buf, (a['count'], dt.itemsize * n), (stride, 1))
    x = np.ascontiguousarray(rows).view(dt).reshape(a['count'], n)
    return x if n > 1 else x[:, 0]


def base_image(doc, binary, material_index):
    """(key, width, height) of the material's base colour image; key = sha1 of the image bytes."""
    if material_index is None:
        return None, 0, 0
    m = doc['materials'][material_index]
    t = m.get('pbrMetallicRoughness', {}).get('baseColorTexture')
    if t is None:
        return 'mat:' + m.get('name', str(material_index)), 1024, 1024
    img = doc['images'][doc['textures'][t['index']]['source']]
    data = view_bytes(doc, binary, img['bufferView'])
    w, h = Image.open(BytesIO(data)).size
    key = hashlib.sha1(data).hexdigest()[:16]
    PIXELS.setdefault(key, data)
    return key, w, h


PIXELS = {}  # image key -> PNG bytes
DECODED = {}  # (image key, size) -> float RGB


def rgb(key, size):
    """Base colour of an image key as float RGB resized to (w, h); None for untextured materials."""
    if key not in PIXELS:
        return None
    if (key, size) not in DECODED:
        im = Image.open(BytesIO(PIXELS[key])).convert('RGB')
        DECODED[(key, size)] = np.asarray(im if im.size == size else im.resize(size, Image.BILINEAR)).astype(np.float32)
    return DECODED[(key, size)]


def mesh_prims(doc, binary, mesh_index, images):
    out = []
    for pi, p in enumerate(doc['meshes'][mesh_index]['primitives']):
        a = p['attributes']
        if 'TEXCOORD_0' not in a or p.get('mode', 4) != 4:
            continue
        mat = p.get('material')
        if mat not in images:
            images[mat] = base_image(doc, binary, mat)
        key, w, h = images[mat]
        tiers = [key]  # base colour images of the tier variants (KHR_materials_variants), default first
        for mp in p.get('extensions', {}).get('KHR_materials_variants', {}).get('mappings', []):
            if mp['material'] not in images:
                images[mp['material']] = base_image(doc, binary, mp['material'])
            if images[mp['material']][0] not in tiers:
                tiers.append(images[mp['material']][0])
        T = accessor(doc, binary, p['indices']).astype(np.int64).reshape(-1, 3) if 'indices' in p else \
            np.arange(doc['accessors'][a['POSITION']]['count']).reshape(-1, 3)
        out.append(dict(index=pi, material=doc['materials'][mat]['name'] if mat is not None else '-', key=key, tiers=tiers,
                        size=(w, h), P=accessor(doc, binary, a['POSITION']).astype(float),
                        UV=accessor(doc, binary, a['TEXCOORD_0']).astype(float), T=T))
    return out


def model(path):
    """{node name: [LOD0 prims, LOD1 prims, ...]} for every mesh node that is not itself an LOD/shadow mesh."""
    doc, binary = read_glb(path)
    lod_meshes = set()
    for m in doc['meshes']:
        ex = m.get('extras', {})
        lod_meshes.update(ex.get('openyamm_lods', []))
        lod_meshes.update(ex.get('openyamm_shadow_lods', []))
    images, nodes = {}, {}
    for n in doc['nodes']:
        if 'mesh' not in n or n['mesh'] in lod_meshes:
            continue
        chain = [n['mesh']] + doc['meshes'][n['mesh']].get('extras', {}).get('openyamm_lods', [])
        nodes[n.get('name', f"node{n['mesh']}")] = [mesh_prims(doc, binary, mi, images) for mi in chain]
    return nodes


def chart_labels(uv, T):
    """Chart id per triangle: triangles connected through shared UV coordinates (quantised)."""
    q = np.round(uv * 2 ** 20).astype(np.int64)
    _, vid = np.unique(q, axis=0, return_inverse=True)
    vid = vid.reshape(-1)
    tri = T.shape[0]
    nv = int(vid.max()) + 1 if len(vid) else 0
    # union-find over (triangle, uv vertex) incidence via a sparse graph
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components
    rows = np.repeat(np.arange(tri), 3)
    cols = tri + vid[T].reshape(-1)
    g = coo_matrix((np.ones(len(rows)), (rows, cols)), shape=(tri + nv, tri + nv))
    _, lab = connected_components(g, directed=False)
    return lab[:tri]


class Charts:
    """Rasterised source charts of one texture: dilated coverage, distance to coverage, two chart-id layers."""

    def __init__(self, polys, size, dil):
        # polys: list of (uv (n, 2), T (m, 3)) of the source LOD0 primitives using this texture
        self.w, self.h = size
        uv = np.concatenate([p[0][p[1]].reshape(-1, 2) for p in polys])
        T = np.arange(len(uv)).reshape(-1, 3)
        lab = chart_labels(uv, T)
        self.nlab = int(lab.max()) + 1
        cov = Image.new('L', (self.w, self.h))
        la = Image.new('I', (self.w, self.h))
        lb = Image.new('I', (self.w, self.h))
        dc, da, db = ImageDraw.Draw(cov), ImageDraw.Draw(la), ImageDraw.Draw(lb)
        px = uv[T] * np.array([self.w, self.h])
        order = np.argsort(lab, kind='stable')
        for t in order:
            pts = [tuple(p) for p in px[t]]
            dc.polygon(pts, fill=255)
            dc.line(pts + pts[:1], fill=255)  # edges too: zero-area UV slivers (PIL skips them in polygon)
            da.polygon(pts, fill=int(lab[t]) + 1)
            da.line(pts + pts[:1], fill=int(lab[t]) + 1)
        for t in order[::-1]:
            pts = [tuple(p) for p in px[t]]
            db.polygon(pts, fill=int(lab[t]) + 1)
            db.line(pts + pts[:1], fill=int(lab[t]) + 1)
        base = np.asarray(cov) > 0
        self.cov = ndimage.binary_dilation(base, iterations=dil) if dil else base
        self.dist = ndimage.distance_transform_edt(~base)
        # chart ids spread into the dilation ring from the nearest covered texel
        A, B = np.asarray(la).astype(np.int32), np.asarray(lb).astype(np.int32)
        _, (iy, ix) = ndimage.distance_transform_edt(~base, return_indices=True)
        self.A, self.B = A[iy, ix], B[iy, ix]
        self.iy, self.ix = iy, ix  # nearest covered texel, for the colour an off-chart sample should have had
        # exact chart lookups: UV corner -> chart ids, and per-chart masks (cropped, built on demand)
        self.uv_charts = {}
        for key, c in zip(map(tuple, np.round(uv * 2 ** 20).astype(np.int64)), np.repeat(lab, 3)):
            self.uv_charts.setdefault(key, set()).add(int(c) + 1)
        self.px, self.lab, self.dil, self.masks = px, lab, dil, {}

    def chart_mask(self, c):
        if c not in self.masks:
            tris = self.px[self.lab == c - 1]
            x0, y0 = np.floor(tris.reshape(-1, 2).min(0)).astype(int) - self.dil - 1
            x1, y1 = np.ceil(tris.reshape(-1, 2).max(0)).astype(int) + self.dil + 2
            im = Image.new('L', (x1 - x0, y1 - y0)); d = ImageDraw.Draw(im)
            for t in tris:
                pts = [(p[0] - x0, p[1] - y0) for p in t]
                d.polygon(pts, fill=255)
                d.line(pts + pts[:1], fill=255)
            m = np.asarray(im) > 0
            if self.dil:
                m = ndimage.binary_dilation(m, iterations=self.dil)
            self.masks[c] = (x0, y0, m)
        return self.masks[c]

    def in_charts(self, cands, x, y):
        ok = np.zeros(len(x), bool)
        for c in cands:
            x0, y0, m = self.chart_mask(c)
            lx, ly = x - x0, y - y0
            v = (lx >= 0) & (ly >= 0) & (lx < m.shape[1]) & (ly < m.shape[0])
            ok[v] |= m[ly[v], lx[v]]
        return ok

    def test(self, uv, T, frac):
        i, j = np.meshgrid(np.arange(K + 1), np.arange(K + 1))
        m = i + j <= K
        w = np.stack([i[m], j[m], K - i[m] - j[m]], 1) / K
        s = np.einsum('sk,fkc->fsc', w, uv[T])
        x = np.clip((s[..., 0] * self.w).astype(int), 0, self.w - 1)
        y = np.clip((s[..., 1] * self.h).astype(int), 0, self.h - 1)
        on = self.cov[y, x]
        off = (~on).mean(1)
        dist = np.where(on, 0.0, self.dist[y, x]).max(1)
        a, b = self.A[y, x], self.B[y, x]
        q = np.round(uv * 2 ** 20).astype(np.int64)
        cross = np.zeros(len(T))
        for f in range(len(T)):
            sets = [self.uv_charts.get(tuple(q[v])) for v in T[f]]
            sets = [c for c in sets if c]
            cands = set.intersection(*sets) if sets else set()
            if not cands and sets:
                cands = set.union(*sets)
            if not cands:  # corners not on source vertices (decimated LODs): the most common chart under the samples
                v = np.concatenate([a[f][on[f]], b[f][on[f]]])
                v = v[v > 0]
                if not len(v):
                    continue
                cands = {int(np.bincount(v).argmax())}
            sus = on[f] & ~np.isin(a[f], list(cands)) & ~np.isin(b[f], list(cands))
            if sus.any():  # the raster layers do not show the face's chart there: test the chart masks exactly
                sus[sus] = ~self.in_charts(cands, x[f][sus], y[f][sus])
                cross[f] = sus.mean()
        bad = (off > frac) | (cross > frac)
        self.last = (x, y, on)
        return bad, off, cross, dist

    def colour_error(self, fl, keys):
        """Per listed face: mean |RGB| difference (0-255) between its off-chart samples and the nearest charted texel,
        worst over the tier images (low = the gutter is padded with the chart's colour, the escape cannot show)."""
        x, y, on = self.last
        worst = np.zeros(len(fl))
        for k in keys:
            img = rgb(k, (self.w, self.h))
            if img is None:
                continue
            for n, f in enumerate(fl):
                o = ~on[f]
                if o.any():
                    xs, ys = x[f][o], y[f][o]
                    d = np.abs(img[ys, xs] - img[self.iy[ys, xs], self.ix[ys, xs]]).mean()
                    worst[n] = max(worst[n], d)
        return worst


def tri_area(P, T):
    return 0.5 * np.linalg.norm(np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]]), axis=1)


def audit(reduced, source, res=None, dil=2, frac=0.02):
    R, S = model(reduced), model(source)
    report = {'reduced': str(reduced), 'source': str(source), 'dil': dil, 'frac': frac, 'nodes': {}}
    cache = {}

    def charts_for(key, size, polys, tag):
        ck = (tag, key)
        if ck not in cache:
            sz = (res, res) if res else size
            cache[ck] = Charts(polys, sz, dil)
        return cache[ck]

    for node, chain in R.items():
        src = S.get(node)
        src0 = {}
        for p in (src[0] if src else []):
            src0.setdefault(p['key'], []).append(p)
        own0 = {}
        for p in chain[0]:
            own0.setdefault(p['key'], []).append(p)
        lods = []
        for lod, prims in enumerate(chain):
            rows = []
            base = src[lod] if src and lod < len(src) else []
            for p in prims:
                if p['key'] in src0:
                    ch, mode = charts_for(p['key'], p['size'], [(q['UV'], q['T']) for q in src0[p['key']]], 'src'), 'src'
                else:
                    ch, mode = charts_for(p['key'], p['size'], [(q['UV'], q['T']) for q in own0[p['key']]], 'own'), 'own'
                bad, off, cross, dist = ch.test(p['UV'], p['T'], frac)
                cerr = ch.colour_error(np.flatnonzero(bad), p['tiers'])
                bl = [q for q in base if q['key'] == p['key'] and q['material'] == p['material']] or \
                     [q for q in base if q['key'] == p['key']]
                bbad = None
                if bl and mode == 'src':
                    bbad = int(sum(int(ch.test(q['UV'], q['T'], frac)[0].sum()) for q in bl))
                A = tri_area(p['P'], p['T'])
                n = np.cross(p['P'][p['T'][:, 1]] - p['P'][p['T'][:, 0]], p['P'][p['T'][:, 2]] - p['P'][p['T'][:, 0]])
                n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-20)
                fl = np.flatnonzero(bad)
                rows.append(dict(
                    primitive=p['index'], material=p['material'], mode=mode, faces=int(len(p['T'])),
                    escaping=int(bad.sum()), off=int((off > frac).sum()), cross=int((cross > frac).sum()),
                    worst_off=round(float(off.max()) if len(off) else 0, 3),
                    worst_cross=round(float(cross.max()) if len(cross) else 0, 3),
                    max_dist=round(float(dist[fl].max()) if len(fl) else 0, 1),
                    area_mm2=round(float(A[fl].sum()) * 1e6, 1), baseline=bbad, tiers=len(p['tiers']),
                    colour_err_max=round(float(cerr.max()) if len(fl) else 0, 1),
                    colour_err_over8=int((cerr > 8).sum()),
                    faces_list=[dict(face=int(f), off=round(float(off[f]), 3), cross=round(float(cross[f]), 3),
                                     dist=round(float(dist[f]), 1), colour_err=round(float(cerr[i]), 1), area_mm2=round(float(A[f]) * 1e6, 2),
                                     centroid=p['P'][p['T'][f]].mean(0).round(4).tolist(),
                                     normal=n[f].round(3).tolist(),
                                     tri=p['P'][p['T'][f]].round(5).tolist(),
                                     uv=p['UV'][p['T'][f]].mean(0).round(4).tolist()) for i, f in enumerate(fl)]))
            lods.append(rows)
        report['nodes'][node] = lods
    return report


def print_report(rep, out=sys.stdout):
    for node, lods in rep['nodes'].items():
        for lod, rows in enumerate(lods):
            for r in rows:
                bl = '-' if r['baseline'] is None else r['baseline']
                print(f"{node} LOD{lod} {r['material']:<22} {r['mode']} faces {r['faces']:>5} escaping {r['escaping']:>4} "
                      f"(off {r['off']}, cross {r['cross']}) worst off {r['worst_off']:.3f} cross {r['worst_cross']:.3f} "
                      f"max dist {r['max_dist']} tx colour err max {r['colour_err_max']} (>8: {r['colour_err_over8']}, "
                      f"{r['tiers']} tier images) area {r['area_mm2']} mm2 | source LOD{lod} {bl}", file=out)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('reduced')
    ap.add_argument('source')
    ap.add_argument('--json')
    ap.add_argument('--res', type=int)
    ap.add_argument('--dil', type=int, default=2)
    ap.add_argument('--frac', type=float, default=0.02)
    ap.add_argument('--self-test', action='store_true')
    a = ap.parse_args()
    rep = audit(a.source if a.self_test else a.reduced, a.source, a.res, a.dil, a.frac)
    print_report(rep)
    if a.json:
        Path(a.json).parent.mkdir(parents=True, exist_ok=True)
        Path(a.json).write_text(json.dumps(rep, indent=1))


if __name__ == '__main__':
    main()
