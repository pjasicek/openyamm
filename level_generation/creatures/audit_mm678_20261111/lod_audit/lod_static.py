#!/usr/bin/env python3
"""Static LOD checks of an installed creature GLB (read-only), one JSON line per model.

Body = the skinned node with LODs and the most LOD0 triangles (as lod_repair_claude/scripts/repair.py picks it).
Per colour level: triangles and ratio to LOD0; whether the level has its own `<material>_LOD<N>` maps (a lod_repair far
LOD) or samples LOD0's atlas; far map size and UV share (texels inside the level's UV triangles); region-mask channels
and the LOD0 material's ramp count; ramps of the far copies equal to LOD0's; variant far copies that point at the
default tier's far maps although the variant has its own LOD0 paint; vertex colour agreement (far vertices are LOD0
vertices: the far map at the far UV against LOD0's map at LOD0's UV, both box-filtered to about the far texel size);
and, for levels on LOD0's atlas, the share of surface whose texel density is far from LOD0's (triangles across charts).
Shadow meshes: signed distance of each shadow level's surface samples to each colour level's surface (outside > 0).
Usage: lod_static.py <glb> [<glb>...]  -> JSON lines on stdout"""
import io
import os
import json
import struct
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'lod_repair_claude' / 'scripts'))
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
import types  # noqa: E402
sys.modules.setdefault("pymeshlab", types.ModuleType("pymeshlab"))
from transfer_textures import closest_on_triangles  # noqa: E402

TYPES = {5121: np.uint8, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
WIDTH = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}


def read_glb(path):
    raw = Path(path).read_bytes()
    n = struct.unpack_from('<I', raw, 12)[0]
    return json.loads(raw[20:20 + n]), raw[28 + n:]


def array(doc, binary, index):
    a = doc['accessors'][index]
    v = doc['bufferViews'][a['bufferView']]
    dtype = np.dtype(TYPES[a['componentType']])
    width = WIDTH[a['type']]
    start = v.get('byteOffset', 0) + a.get('byteOffset', 0)
    stride = v.get('byteStride', dtype.itemsize * width)
    raw = np.frombuffer(binary, np.uint8, a['count'] * stride - (stride - dtype.itemsize * width), start)
    raw = np.lib.stride_tricks.as_strided(raw, (a['count'], dtype.itemsize * width), (stride, 1)).copy()
    out = raw.view(dtype).reshape(a['count'], width)
    if a.get('normalized') and dtype != np.float32:
        out = out.astype(np.float64) / np.iinfo(dtype).max
    return out


class Model:
    def __init__(self, path):
        self.doc, self.bin = read_glb(path)
        self.images = {}

    def image_bytes(self, image_index):
        image = self.doc['images'][image_index]
        v = self.doc['bufferViews'][image['bufferView']]
        start = v.get('byteOffset', 0)
        return self.bin[start:start + v['byteLength']]

    def picture(self, texture_index):
        source = self.doc['textures'][texture_index]['source']
        if source not in self.images:
            self.images[source] = Image.open(io.BytesIO(self.image_bytes(source)))
            self.images[source].load()
        return self.images[source], source

    def prim(self, p):
        a = p['attributes']
        pos = array(self.doc, self.bin, a['POSITION']).astype(np.float64)
        faces = array(self.doc, self.bin, p['indices']).reshape(-1, 3).astype(np.int64)
        uv = array(self.doc, self.bin, a['TEXCOORD_0']).astype(np.float64) if 'TEXCOORD_0' in a else None
        nrm = array(self.doc, self.bin, a['NORMAL']).astype(np.float64) if 'NORMAL' in a else None
        return pos, faces, uv, nrm


def maps_of(material):
    pbr = material.get('pbrMetallicRoughness', {})
    found = {'basecolor': pbr.get('baseColorTexture'), 'mr': pbr.get('metallicRoughnessTexture'),
             'mask': (material.get('extras') or {}).get('openyamm_region_mask'), 'normal': material.get('normalTexture')}
    return {k: v['index'] for k, v in found.items() if v is not None}


def uv_share(uv, faces, size):
    """Fraction of a size x size texture inside the UV triangles (rasterized at up to 1024 px)."""
    res = min(size, 1024)
    canvas = Image.new('L', (res, res), 0)
    draw = ImageDraw.Draw(canvas)
    pts = np.mod(uv, 1.0) * res if np.all((uv >= -0.01) & (uv <= 1.01)) else np.clip(uv, 0, 1) * res
    for tri in faces:
        draw.polygon([tuple(pts[i]) for i in tri], fill=255)
    return float((np.asarray(canvas) > 0).mean())


def boxed(picture, size):
    """RGB float array of the picture box-filtered to size x size."""
    return np.asarray(picture.convert('RGB').resize((size, size), Image.BOX), np.float64)


def sample(arr, uv):
    h, w = arr.shape[:2]
    x = np.clip((np.mod(uv[:, 0], 1.0) * w).astype(int), 0, w - 1)
    y = np.clip((np.mod(uv[:, 1], 1.0) * h).astype(int), 0, h - 1)
    return arr[y, x]


def densities(pos, faces, uv):
    e1, e2 = pos[faces[:, 1]] - pos[faces[:, 0]], pos[faces[:, 2]] - pos[faces[:, 0]]
    area = np.linalg.norm(np.cross(e1, e2), axis=1) / 2
    u1, u2 = uv[faces[:, 1]] - uv[faces[:, 0]], uv[faces[:, 2]] - uv[faces[:, 0]]
    uarea = np.abs(u1[:, 0] * u2[:, 1] - u1[:, 1] * u2[:, 0]) / 2
    ok = area > 1e-12
    return np.where(ok, np.sqrt(uarea / np.maximum(area, 1e-12)), np.nan), area


def surface_samples(pos, faces, count, rng):
    a, b, c = pos[faces[:, 0]], pos[faces[:, 1]], pos[faces[:, 2]]
    area = np.linalg.norm(np.cross(b - a, c - a), axis=1) / 2
    if area.sum() <= 0:
        return np.zeros((0, 3))
    pick = rng.choice(len(faces), count, p=area / area.sum())
    r1, r2 = rng.random(count), rng.random(count)
    s = np.sqrt(r1)
    return (1 - s)[:, None] * a[pick] + (s * (1 - r2))[:, None] * b[pick] + (s * r2)[:, None] * c[pick]


def closest(points, a, b, c):
    """Closest point distances to candidate triangles (points[:, None] vs a/b/c[:, k]) via Ericson's test."""
    return closest_on_triangles(points, a, b, c)


def signed_outside(points, pos, faces):
    """Signed distance of points to the surface (pos, faces): positive outside (along the closest face's normal)."""
    a, b, c = pos[faces[:, 0]], pos[faces[:, 1]], pos[faces[:, 2]]
    normal = np.cross(b - a, c - a)
    normal /= np.maximum(np.linalg.norm(normal, axis=1, keepdims=True), 1e-15)
    tree = cKDTree((a + b + c) / 3)
    out = np.empty(len(points))
    for start in range(0, len(points), 4000):
        chunk = points[start:start + 4000]
        _, cand = tree.query(chunk, k=min(24, len(faces)))
        dist, bary = closest(chunk, a[cand], b[cand], c[cand])
        best = np.argmin(dist, axis=1)
        rows = np.arange(len(chunk))
        f = cand[rows, best]
        w = bary[rows, best]
        q = w[:, :1] * a[f] + w[:, 1:2] * b[f] + w[:, 2:] * c[f]
        out[start:start + 4000] = np.einsum('ij,ij->i', chunk - q, normal[f])
    return out


def analyse(path):
    m = Model(path)
    doc = m.doc
    report = {'glb': str(path), 'stem': Path(path).stem}
    nodes = [n for n in doc.get('nodes', []) if 'mesh' in n and 'skin' in n
             and (doc['meshes'][n['mesh']].get('extras') or {}).get('openyamm_lods')]
    if not nodes:
        report['error'] = 'no skinned node with LODs'
        return report
    tri = lambda mi: sum(doc['accessors'][p['indices']]['count'] // 3 for p in doc['meshes'][mi]['primitives'])
    node = max(nodes, key=lambda n: tri(n['mesh']))
    report['node'] = node.get('name')
    report['bodies_with_lods'] = len(nodes)
    lod0 = doc['meshes'][node['mesh']]
    chain = [node['mesh']] + lod0['extras']['openyamm_lods']
    shadows = lod0['extras'].get('openyamm_shadow_lods', [])
    report['tris'] = [tri(mi) for mi in chain]
    report['ratios'] = [round(t / report['tris'][0], 3) for t in report['tris']]
    report['shadow_tris'] = [tri(mi) for mi in shadows]
    mats = doc['materials']
    names = {mat['name']: i for i, mat in enumerate(mats)}
    # LOD0 geometry per primitive.
    p0 = [m.prim(p) for p in lod0['primitives']]
    ramps = []
    for p in lod0['primitives']:
        ramps.append(len((mats[p['material']].get('extras') or {}).get('openyamm_region_ramps', [])))
    report['ramps'] = ramps
    levels = {}
    for level, mi in enumerate(chain[1:], start=1):
        mesh = doc['meshes'][mi]
        info = {'prims': []}
        for j, p in enumerate(mesh['primitives']):
            mat = mats[p['material']]
            own = mat['name'].endswith(f'_LOD{level}')
            pi = {'material': mat['name'], 'own_maps': own}
            kinds = maps_of(mat)
            pos, faces, uv, nrm = m.prim(p)
            if 'basecolor' not in kinds or uv is None:
                info['prims'].append(pi)
                continue
            pic, src = m.picture(kinds['basecolor'])
            pi['size'] = list(pic.size)
            pi['uv_share'] = round(uv_share(uv, faces, max(pic.size)), 3)
            if 'mask' in kinds:
                mpic, _ = m.picture(kinds['mask'])
                pi['mask_mode'] = mpic.mode
                if mpic.mode == 'RGBA':
                    alpha = np.asarray(mpic)[..., 3]
                    pi['mask_alpha_255'] = round(float((alpha == 255).mean()), 3)
            # ramps equal to the LOD0 material's
            base_name = mat['name'][:-len(f'_LOD{level}')] if own else mat['name']
            if own and base_name in names:
                base = mats[names[base_name]]
                pi['ramps_match'] = (base.get('extras') or {}).get('openyamm_region_ramps') == \
                    (mat.get('extras') or {}).get('openyamm_region_ramps')
            # vertex colour agreement with LOD0 (j-th LOD0 primitive)
            if j < len(p0) and p0[j][2] is not None:
                q_pos, q_faces, q_uv, q_nrm = p0[j]
                q_mat = mats[lod0['primitives'][j]['material']]
                q_kinds = maps_of(q_mat)
                if 'basecolor' in q_kinds:
                    q_pic, q_src = m.picture(q_kinds['basecolor'])
                    used = np.unique(faces)
                    tree = cKDTree(q_pos)
                    dist, near = tree.query(pos[used], k=8, distance_upper_bound=1e-6)
                    valid = np.isfinite(dist[:, 0])
                    pi['vertices_on_lod0'] = round(float(valid.mean()), 3)
                    if valid.any() and nrm is not None and q_nrm is not None:
                        cand = np.where(np.isfinite(dist), near, near[:, :1])[valid]
                        cand = np.minimum(cand, len(q_pos) - 1)
                        dots = np.einsum('ikj,ij->ik', q_nrm[cand], nrm[used][valid])
                        pick = cand[np.arange(len(cand)), np.argmax(dots, axis=1)]
                        far_size = max(pic.size)
                        size0 = max(q_pic.size)
                        share0 = uv_share(q_uv, q_faces, 1024)
                        if src == q_src:
                            own_size, far_arr = size0, None
                        else:
                            # LOD0 box-filtered to the far map's texel density (size x sqrt(UV share) per map).
                            ratio = far_size * np.sqrt(max(pi['uv_share'], 1e-3)) / (size0 * np.sqrt(max(share0, 1e-3)))
                            own_size = int(max(32, min(size0, size0 * ratio)))
                            far_arr = boxed(pic, far_size)
                        lod0_arr = boxed(q_pic, own_size)
                        a0 = sample(lod0_arr, q_uv[pick])
                        a1 = sample(far_arr if far_arr is not None else lod0_arr, uv[used][valid])
                        diff = np.abs(a0 - a1).mean(axis=1)
                        pi['vertex_colour_median'] = round(float(np.median(diff)), 1)
                        pi['vertex_colour_p90'] = round(float(np.percentile(diff, 90)), 1)
                    # texel density against LOD0's (levels on LOD0's atlas: triangles across charts smear it)
                    if src == q_src:
                        d0, a0w = densities(q_pos, q_faces, q_uv)
                        # each triangle against the LOD0 triangles nearest its centre (heads and hands are denser)
                        d1, a1w = densities(pos, faces, uv)
                        _, near0 = cKDTree(q_pos[q_faces].mean(1)).query(pos[faces].mean(1), k=8)
                        ref = np.nanmedian(d0[near0], axis=1)
                        bad = (d1 > 4 * ref) | (d1 < ref / 4)
                        pi['smear_share'] = round(float(a1w[bad & np.isfinite(d1)].sum() / max(a1w.sum(), 1e-12)), 3)
            # variants: far copy pointing at the default's far map although the LOD0 variant has its own paint
            mappings = p.get('extensions', {}).get('KHR_materials_variants', {}).get('mappings', [])
            lod0_p = lod0['primitives'][j] if j < len(lod0['primitives']) else None
            if own and mappings and lod0_p is not None:
                lod0_default = maps_of(mats[lod0_p['material']])
                far_default = kinds
                stale = []
                for mp in mappings:
                    copy = mats[mp['material']]
                    if not copy['name'].endswith(f'_LOD{level}'):
                        continue
                    vname = copy['name'][:-len(f'_LOD{level}')]
                    if vname not in names:
                        continue
                    vmaps = maps_of(mats[names[vname]])
                    own_lod0 = {k for k, t in vmaps.items()
                                if k not in lod0_default or m.picture(t)[1] != m.picture(lod0_default[k])[1]}
                    far_copy = maps_of(copy)
                    same = {k for k in own_lod0 if far_copy.get(k) is not None and far_default.get(k) is not None
                            and m.picture(far_copy[k])[1] == m.picture(far_default[k])[1]}
                    missing = {k for k in own_lod0 if k not in far_copy}
                    if same or missing:
                        stale.append(f'{copy["name"]}:{"+".join(sorted(same | missing))}')
                    rm = (mats[names[vname]].get('extras') or {}).get('openyamm_region_ramps') == \
                        (copy.get('extras') or {}).get('openyamm_region_ramps')
                    if not rm:
                        stale.append(f'{copy["name"]}:ramps')
                if stale:
                    pi['variant_issues'] = stale
            info['prims'].append(pi)
        levels[level] = info
    report['levels'] = levels
    # shadow meshes against colour levels
    rng = np.random.default_rng(1)
    colour = []
    for mi in chain:
        ps = [m.prim(p) for p in doc['meshes'][mi]['primitives']]
        offs = np.cumsum([0] + [len(x[0]) for x in ps])
        colour.append((np.concatenate([x[0] for x in ps]),
                       np.concatenate([x[1] + o for x, o in zip(ps, offs)])))
    sh = {}
    for s, mi in enumerate(shadows if not os.environ.get('LOD_STATIC_NO_SHADOW') else []):
        ps = [m.prim(p) for p in doc['meshes'][mi]['primitives']]
        offs = np.cumsum([0] + [len(x[0]) for x in ps])
        spos = np.concatenate([x[0] for x in ps])
        sfaces = np.concatenate([x[1] + o for x, o in zip(ps, offs)])
        pts = surface_samples(spos, sfaces, 6000, rng)
        extent = float(np.ptp(colour[0][0], axis=0).max())
        row = {}
        for c, (cpos, cfaces) in enumerate(colour):
            d = signed_outside(pts, cpos, cfaces)
            row[c] = {'out2mm': round(float((d > 0.002).mean()), 4), 'out10mm': round(float((d > 0.010).mean()), 4),
                      'p99_mm': round(float(np.percentile(d, 99)) * 1000, 1)}
        sh[s] = row
    report['shadow'] = sh
    report['extent_m'] = round(float(np.ptp(colour[0][0], axis=0).max()), 3)
    return report


if __name__ == '__main__':
    for path in sys.argv[1:]:
        try:
            print(json.dumps(analyse(path)), flush=True)
        except Exception as error:  # report and go on
            print(json.dumps({'glb': path, 'stem': Path(path).stem, 'error': repr(error)}), flush=True)
