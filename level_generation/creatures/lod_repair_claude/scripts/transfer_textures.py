#!/usr/bin/env python3
"""Fill the textures of rebuilt LODs from LOD0, per texel, in bind space (no ray casting).

For every texel of a LOD triangle in its new UVs (unwrap_lods.py): the nearest point of LOD0 on the same connected
piece as the triangle and facing the same way (a coat over the body, a cape over the back or a thin sheet's far side
cannot be picked up), then LOD0's base colour, metal/roughness (bilinear) and region mask (nearest) at that point.

The normal map is converted in the engine's own frame: fs_model.sc builds the tangent frame per pixel from position
and UV derivatives (no stored tangents), which over a triangle is the frame of its edges and UVs. LOD0's shaded normal
(interpolated normal plus its normal map at the material's scale) is rebuilt in LOD0's frame and stored in the LOD
triangle's frame against the LOD's interpolated normal, so the engine shades the LOD with LOD0's normals. A bake that
encodes against other tangents (Cycles, MikkTSpace) shaded the coarse LOD3s dark and blotchy in game.
Empty texels take their nearest filled texel (mip and filtering margins).
Usage: transfer_textures.py <built.glb> <node> <unwrap dir> [level,...]  -> <unwrap dir>/lod<N>_p<primitive>_<map>.png"""
import io
import os
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3] / 'tools'))
sys.path.insert(0, str(HERE))
from build_actor_lods import read_glb  # noqa: E402
from build_lods import source_faces  # noqa: E402
from splice_lods import floats  # noqa: E402

CANDIDATES = 32
CHUNK = 20000
# Samples per texel along each axis. One point sample of the 2K LOD0 maps per far texel aliased fine fabric detail
# into grain (MM9 townswomen 2026-11-07: speckled skirts, mottled collars at the LOD1 -> LOD2 switch); the maps are
# filled at SUPERSAMPLE x the size and box-filtered down (the region mask keeps its centre sample).
SUPERSAMPLE = 4
# UV-correspondence lookup (transfer's param_uv): face-id raster size and accepted distance (fraction of the
# primitive's bounding diagonal) between the UV-found LOD0 point and the texel's point.
PARAM_RESOLUTION = 2048
PARAM_TOLERANCE = float(os.environ.get('LOD_PARAM_TOLERANCE', '0.02'))
# With build_lods.py's LINING_FIX (default on, LOD_LINING_FIX=0 off): colours, too, only from UV faces facing the far
# triangle's way.
LINING_FIX = os.environ.get('LOD_LINING_FIX', '1') != '0'


def image(doc, binary, texture_index, mode='RGB'):
    source = doc['images'][doc['textures'][texture_index]['source']]
    view = doc['bufferViews'][source['bufferView']]
    start = view.get('byteOffset', 0)
    return np.asarray(Image.open(io.BytesIO(binary[start:start + view['byteLength']])).convert(mode), np.float32)


def sample(texture, uv, nearest=False):
    height, width = texture.shape[:2]
    x = np.mod(uv[:, 0], 1.0) * width - 0.5
    y = np.mod(uv[:, 1], 1.0) * height - 0.5
    if nearest:
        return texture[np.clip(np.round(y).astype(int), 0, height - 1), np.clip(np.round(x).astype(int), 0, width - 1)]
    x0, y0 = np.floor(x).astype(int), np.floor(y).astype(int)
    fx, fy = (x - x0)[:, None], (y - y0)[:, None]
    x0, x1 = np.mod(x0, width), np.mod(x0 + 1, width)
    y0, y1 = np.clip(y0, 0, height - 1), np.clip(y0 + 1, 0, height - 1)
    return (texture[y0, x0] * (1 - fx) * (1 - fy) + texture[y0, x1] * fx * (1 - fy)
            + texture[y1, x0] * (1 - fx) * fy + texture[y1, x1] * fx * fy)


def normalize(v):
    return v / np.maximum(np.linalg.norm(v, axis=-1, keepdims=True), 1e-12)


def frame(edge1, edge2, duv1, duv2, normal):
    """fs_model.sc's tangent and bitangent, scaled by its inverseLength, from two edges of a triangle."""
    p1 = np.cross(normal, edge1)
    p2 = np.cross(edge2, normal)
    tangent = p2 * duv1[..., :1] + p1 * duv2[..., :1]
    bitangent = p2 * duv1[..., 1:] + p1 * duv2[..., 1:]
    length = np.maximum(np.maximum((tangent ** 2).sum(-1), (bitangent ** 2).sum(-1)), 1e-6)
    scale = (1.0 / np.sqrt(length)) * np.where((edge1 * p2).sum(-1) < 0, -1.0, 1.0)
    return tangent * scale[..., None], bitangent * scale[..., None]


def closest_on_triangles(points, a, b, c):
    """Closest points of points[:, None] on triangles (a, b, c)[:, k]; returns (distance, barycentric)."""
    ab, ac, ap = b - a, c - a, points[:, None] - a
    d1, d2 = (ab * ap).sum(-1), (ac * ap).sum(-1)
    bp, cp = points[:, None] - b, points[:, None] - c
    d3, d4 = (ab * bp).sum(-1), (ac * bp).sum(-1)
    d5, d6 = (ab * cp).sum(-1), (ac * cp).sum(-1)
    va, vb, vc = d3 * d6 - d5 * d4, d5 * d2 - d1 * d6, d1 * d4 - d3 * d2
    denominator = np.where(np.abs(va + vb + vc) < 1e-30, 1e-30, va + vb + vc)
    v, w = vb / denominator, vc / denominator
    bary = np.stack([1 - v - w, v, w], -1)
    # Regions outside the face (Ericson, Real-Time Collision Detection 5.1.5), in order of precedence reversed.
    t_ab = np.clip(d1 / np.where(d1 - d3 == 0, 1e-30, d1 - d3), 0, 1)
    t_ac = np.clip(d2 / np.where(d2 - d6 == 0, 1e-30, d2 - d6), 0, 1)
    t_bc = np.clip((d4 - d3) / np.where((d4 - d3) + (d5 - d6) == 0, 1e-30, (d4 - d3) + (d5 - d6)), 0, 1)
    outside = [
        ((va <= 0) & (d4 - d3 >= 0) & (d5 - d6 >= 0), np.stack([np.zeros_like(t_bc), 1 - t_bc, t_bc], -1)),
        ((vb <= 0) & (d2 >= 0) & (d6 <= 0), np.stack([1 - t_ac, np.zeros_like(t_ac), t_ac], -1)),
        ((vc <= 0) & (d1 >= 0) & (d3 <= 0), np.stack([1 - t_ab, t_ab, np.zeros_like(t_ab)], -1)),
        ((d6 >= 0) & (d5 <= d6), np.broadcast_to([0.0, 0.0, 1.0], bary.shape)),
        ((d3 >= 0) & (d4 <= d3), np.broadcast_to([0.0, 1.0, 0.0], bary.shape)),
        ((d1 <= 0) & (d2 <= 0), np.broadcast_to([1.0, 0.0, 0.0], bary.shape)),
    ]
    for mask, value in outside:
        bary = np.where(mask[..., None], value, bary)
    closest = bary[..., :1] * a + bary[..., 1:2] * b + bary[..., 2:] * c
    return np.linalg.norm(points[:, None] - closest, axis=-1), bary


def rasterize(uv, size):
    """Texels whose centre lies in each triangle: (triangle index, texel x, y, barycentric)."""
    pixel = uv * size
    triangles, xs, ys, barys = [], [], [], []
    for t, (a, b, c) in enumerate(pixel):
        low = np.floor(np.minimum(np.minimum(a, b), c) - 0.5).astype(int)
        high = np.ceil(np.maximum(np.maximum(a, b), c) + 0.5).astype(int)
        low, high = np.clip(low, 0, size - 1), np.clip(high, 0, size - 1)
        gx, gy = np.meshgrid(np.arange(low[0], high[0] + 1), np.arange(low[1], high[1] + 1))
        centre = np.stack([gx.ravel() + 0.5, gy.ravel() + 0.5], -1)
        area = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
        if abs(area) < 1e-12:
            continue
        w1 = ((centre[:, 0] - a[0]) * (c[1] - a[1]) - (centre[:, 1] - a[1]) * (c[0] - a[0])) / area
        w2 = ((b[0] - a[0]) * (centre[:, 1] - a[1]) - (b[1] - a[1]) * (centre[:, 0] - a[0])) / area
        inside = (w1 >= -1e-4) & (w2 >= -1e-4) & (w1 + w2 <= 1 + 1e-4)
        if inside.any():
            triangles.append(np.full(inside.sum(), t))
            xs.append(gx.ravel()[inside])
            ys.append(gy.ravel()[inside])
            barys.append(np.stack([1 - w1[inside] - w2[inside], w1[inside], w2[inside]], -1))
    return np.concatenate(triangles), np.concatenate(xs), np.concatenate(ys), np.concatenate(barys)


def pieces(positions, faces):
    """Connected piece of each triangle, vertices joined by position."""
    _, point = np.unique(positions.astype(np.float32), axis=0, return_inverse=True)
    point = point.reshape(-1)
    welded = point[faces]
    count = point.max() + 1
    graph = coo_matrix((np.ones(welded.size), (welded.reshape(-1), np.roll(welded, 1, axis=1).reshape(-1))),
                       shape=(count, count))
    _, label = connected_components(graph, directed=False)
    return label[welded[:, 0]], label[point]


MAPS = ('basecolor', 'mr', 'mask', 'normal')


def material_maps(material):
    """Texture index of each map a material has (colour tiers need the region mask; effect parts lack some maps)."""
    pbr = material.get('pbrMetallicRoughness', {})
    found = {'basecolor': pbr.get('baseColorTexture'), 'mr': pbr.get('metallicRoughnessTexture'),
             'mask': material.get('extras', {}).get('openyamm_region_mask'), 'normal': material.get('normalTexture')}
    return {kind: texture['index'] for kind, texture in found.items() if texture is not None}


def own_map_variants(doc, primitive):
    """Variant materials of the primitive whose maps differ from its default material's."""
    default = material_maps(doc['materials'][primitive['material']])
    mappings = primitive.get('extensions', {}).get('KHR_materials_variants', {}).get('mappings', [])
    return sorted({m['material'] for m in mappings
                   if material_maps(doc['materials'][m['material']]) not in ({}, default)})


def unwrapped_uvs(doc, binary, primitive, index, data):
    """The primitive's triangles and their new UVs per corner (unwrap_lods.py, same triangle order)."""
    faces = source_faces(doc, binary, primitive)
    corner_uv = data[f'p{index}_uv']
    if len(corner_uv) != len(faces):
        raise ValueError(f'primitive {index}: {len(corner_uv)} unwrapped triangles for {len(faces)}')
    return faces, corner_uv


def face_id_map(uv0, f0, resolution):
    """LOD0 face index under each texel of LOD0's UV layout (-1 in gutters; overlapping charts keep the last face)."""
    ids = np.full((resolution, resolution), -1, np.int64)
    triangle, x, y, _ = rasterize(uv0[f0], resolution)
    ids[y, x] = triangle
    return ids


def uv_barycentric(point, a, b, c):
    """Barycentric weights of 2D points in 2D triangles (clamped to the triangle)."""
    v0, v1, v2 = b - a, c - a, point - a
    d00, d01, d11 = (v0 * v0).sum(-1), (v0 * v1).sum(-1), (v1 * v1).sum(-1)
    d20, d21 = (v2 * v0).sum(-1), (v2 * v1).sum(-1)
    denominator = np.where(np.abs(d00 * d11 - d01 * d01) < 1e-20, 1e-20, d00 * d11 - d01 * d01)
    v = (d11 * d20 - d01 * d21) / denominator
    w = (d00 * d21 - d01 * d20) / denominator
    weights = np.clip(np.stack([1 - v - w, v, w], -1), 0.0, None)
    return weights / np.maximum(weights.sum(-1, keepdims=True), 1e-12)


def transfer(doc, binary, lod0_primitive, lod_primitive, corners, corner_uv, size, material_index=None,
             param_uv=None):
    """Textures of one LOD primitive (triangles `corners` with UVs `corner_uv`) from its LOD0 primitive, read from the
    primitive's material or from `material_index` (a variant with its own maps).

    `param_uv` (per triangle corner, the LOD0 UVs build_lods.py gave the triangle) is tried first: the LOD0 face under
    that UV is used when its surface point lies within PARAM_TOLERANCE of the texel's point. Nearest-point matching
    alone scrambles corrugated surfaces (a coarse skirt cuts through LOD0's pleats and its nearest points jump between
    fold faces: grain, MM9 townswomen 2026-11-07); the UV correspondence keeps pleats and weave, and the nearest point
    still covers triangles whose LOD0 UVs cross charts."""
    material = doc['materials'][lod0_primitive['material'] if material_index is None else material_index]
    indices = material_maps(material)
    # The region mask keeps all four channels: a fourth region (hair) lives in alpha, and an RGB copy (alpha 255 when
    # loaded) put every far-LOD texel into it (Hesper villagers 2026-10-22: LOD2/3 one hair-coloured figure).
    maps = {kind: image(doc, binary, index, 'RGBA' if kind == 'mask' else 'RGB') for kind, index in indices.items()
            if kind != 'normal'}
    normal_map = image(doc, binary, indices['normal']) if 'normal' in indices else None
    normal_scale = material.get('normalTexture', {}).get('scale', 1.0)
    lod_positions = floats(doc, binary, lod_primitive['attributes']['POSITION'])
    lod_normals = normalize(floats(doc, binary, lod_primitive['attributes']['NORMAL']))
    attributes = lod0_primitive['attributes']
    p0 = floats(doc, binary, attributes['POSITION'])
    n0 = normalize(floats(doc, binary, attributes['NORMAL']))
    uv0 = floats(doc, binary, attributes['TEXCOORD_0'])
    f0 = source_faces(doc, binary, lod0_primitive)
    piece_of_face, piece_of_point = pieces(p0, f0)
    # LOD vertices are LOD0 vertices: their piece by position.
    _, unique_index = np.unique(p0.astype(np.float32), axis=0, return_index=True)
    point_tree = cKDTree(p0[unique_index])
    _, nearest = point_tree.query(lod_positions[corners[:, 0]])
    lod_piece = piece_of_point[unique_index[nearest]]
    face_normal0 = normalize(np.cross(p0[f0[:, 1]] - p0[f0[:, 0]], p0[f0[:, 2]] - p0[f0[:, 0]]))
    centroid_tree = cKDTree(p0[f0].mean(1))
    param_ids = None
    param_hits = 0
    if param_uv is not None:
        param_ids = face_id_map(uv0, f0, PARAM_RESOLUTION)
        param_tolerance = PARAM_TOLERANCE * np.linalg.norm(p0.max(0) - p0.min(0))
    final_size, size = size, size * SUPERSAMPLE
    triangle, tx, ty, bary = rasterize(corner_uv, size)
    out = {kind: np.zeros((size, size, 4 if kind == 'mask' else 3), np.float32) for kind in indices}
    filled = np.zeros((size, size), bool)
    for start in range(0, len(triangle), CHUNK):
        t, x, y, b = triangle[start:start + CHUNK], tx[start:start + CHUNK], ty[start:start + CHUNK], \
            bary[start:start + CHUNK]
        tri_positions = lod_positions[corners[t]]
        tri_normals = lod_normals[corners[t]]
        point = (b[:, :, None] * tri_positions).sum(1)
        normal = normalize((b[:, :, None] * tri_normals).sum(1))
        _, candidates = centroid_tree.query(point, k=min(CANDIDATES, len(f0)))
        a_, b_, c_ = p0[f0[candidates, 0]], p0[f0[candidates, 1]], p0[f0[candidates, 2]]
        distance, candidate_bary = closest_on_triangles(point, a_, b_, c_)
        cost = distance + np.where(piece_of_face[candidates] != lod_piece[t][:, None], 1e6, 0.0) \
            + np.where((face_normal0[candidates] * normal[:, None]).sum(-1) < -0.2, 1e3, 0.0)
        best = np.argmin(cost, axis=1)
        rows = np.arange(len(t))
        face = candidates[rows, best]
        w = candidate_bary[rows, best]
        normal_face, normal_w = face, w
        if param_ids is not None:
            uvp = (b[:, :, None] * param_uv[t]).sum(1)
            px = np.clip((np.mod(uvp, 1.0) * param_ids.shape[0]).astype(int), 0, param_ids.shape[0] - 1)
            found = param_ids[px[:, 1], px[:, 0]]
            ok = found >= 0
            safe = np.where(ok, found, 0)
            wp = uv_barycentric(np.mod(uvp, 1.0), uv0[f0[safe, 0]], uv0[f0[safe, 1]], uv0[f0[safe, 2]])
            pp = (wp[:, :, None] * p0[f0[safe]]).sum(1)
            ok &= np.linalg.norm(pp - point, axis=1) < param_tolerance
            colour_ok = ok & ((face_normal0[safe] * normal).sum(-1) >= -0.2) if LINING_FIX else ok
            face = np.where(colour_ok, found, face)
            w = np.where(colour_ok[:, None], wp, w)
            param_hits += int(colour_ok.sum())
            # Thin cloth (skirts, aprons, sleeves) has a lining with the outer layer's UVs, so the UV raster often
            # holds the lining's face: the same colours, but a normal facing away, which the clamp below turned into
            # near-horizontal far normals and shiny blotches (MM9 dwarf townswomen, 2026-11-07). The normal takes the
            # UV face only when it faces the LOD's way (the nearest-point rule); otherwise the nearest outer face.
            facing = ok & ((face_normal0[safe] * normal).sum(-1) >= -0.2)
            normal_face = np.where(facing, found, normal_face)
            normal_w = np.where(facing[:, None], wp, normal_w)
        corner = f0[face]
        uv = (w[:, :, None] * uv0[corner]).sum(1)
        for kind, texture in maps.items():
            out[kind][y, x] = sample(texture, uv, nearest=kind == 'mask')
        filled[y, x] = True
        if 'normal' not in out:
            continue
        # LOD0's shaded normal in its own fs_model.sc frame.
        corner = f0[normal_face]
        shading0 = normalize((normal_w[:, :, None] * n0[corner]).sum(1))
        e1, e2 = p0[corner[:, 1]] - p0[corner[:, 0]], p0[corner[:, 2]] - p0[corner[:, 0]]
        t0, b0 = frame(e1, e2, uv0[corner[:, 1]] - uv0[corner[:, 0]], uv0[corner[:, 2]] - uv0[corner[:, 0]], shading0)
        xy = sample(normal_map, (normal_w[:, :, None] * uv0[corner]).sum(1))[:, :2] / 127.5 - 1.0
        z = np.sqrt(np.maximum(1.0 - (xy ** 2).sum(-1), 0.0))
        target = normalize(t0 * (xy[:, :1] * normal_scale) - b0 * (xy[:, 1:] * normal_scale) + shading0 * z[:, None])
        # The same normal in the LOD triangle's frame, against the LOD's interpolated normal (normal scale 1).
        lod_uv = corner_uv[t]
        t1, b1 = frame(tri_positions[:, 1] - tri_positions[:, 0], tri_positions[:, 2] - tri_positions[:, 0],
                       lod_uv[:, 1] - lod_uv[:, 0], lod_uv[:, 2] - lod_uv[:, 0], normal)
        basis = np.stack([t1, -b1, normal], -1)
        coefficients = np.linalg.solve(basis + np.eye(3) * 1e-9, target[:, :, None])[:, :, 0]
        coefficients[:, 2] = np.maximum(coefficients[:, 2], 0.05)
        mapped = normalize(coefficients)
        out['normal'][y, x] = np.stack([mapped[:, 0], mapped[:, 1], mapped[:, 2]], -1) * 127.5 + 127.5
    _, (iy, ix) = distance_transform_edt(~filled, return_indices=True)
    pictures = {}
    for kind, data in out.items():
        data = data[iy, ix]
        if kind == 'mask':
            data = data[SUPERSAMPLE // 2::SUPERSAMPLE, SUPERSAMPLE // 2::SUPERSAMPLE]
        else:
            data = data.reshape(final_size, SUPERSAMPLE, final_size, SUPERSAMPLE, -1).mean((1, 3))
            if kind == 'normal':
                data = normalize(data / 127.5 - 1.0) * 127.5 + 127.5
        pictures[kind] = Image.fromarray(np.clip(np.round(data), 0, 255).astype(np.uint8))
    transfer.param_share = param_hits / max(len(triangle), 1)
    return pictures, filled.mean()


def main():
    built, node_name, unwrap_dir = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3])
    doc, binary = read_glb(built)
    node = next(n for n in doc['nodes'] if n.get('name') == node_name and 'mesh' in n)
    lod0 = doc['meshes'][node['mesh']]
    levels = [int(x) for x in sys.argv[4].split(',')] if len(sys.argv) > 4 else \
        sorted(int(p.stem[3:]) for p in unwrap_dir.glob('lod?.npz'))
    for level in levels:
        data = np.load(unwrap_dir / f'lod{level}.npz')
        lod_mesh = doc['meshes'][lod0['extras']['openyamm_lods'][level - 1]]
        # build_lods.py writes one LOD primitive per LOD0 primitive, in order.
        for index, (primitive, lod_primitive) in enumerate(zip(lod0['primitives'], lod_mesh['primitives'])):
            if not material_maps(doc['materials'][primitive['material']]):
                continue
            corners, corner_uv = unwrapped_uvs(doc, binary, lod_primitive, index, data)
            size = int(data[f'p{index}_size'])
            # The built LOD's own UVs (build_lods.py: LOD0 UVs per triangle) are the UV correspondence.
            param_uv = floats(doc, binary, lod_primitive['attributes']['TEXCOORD_0'])[corners] \
                if 'TEXCOORD_0' in lod_primitive['attributes'] else None
            maps, coverage = transfer(doc, binary, primitive, lod_primitive, corners, corner_uv, size,
                                      param_uv=param_uv)
            for kind, picture in maps.items():
                picture.save(unwrap_dir / f'lod{level}_p{index}_{kind}.png')
            print(f'TRANSFERRED lod{level} primitive {index} {size}px, {coverage:.0%} of texels covered, '
                  f'{transfer.param_share:.0%} by UV correspondence', flush=True)
            # A variant with maps of its own (an MM9 tier with its own paint rather than ramps) gets its own far maps.
            for variant in own_map_variants(doc, primitive):
                maps, _ = transfer(doc, binary, primitive, lod_primitive, corners, corner_uv, size, variant, param_uv)
                for kind, picture in maps.items():
                    picture.save(unwrap_dir / f'lod{level}_p{index}_m{variant}_{kind}.png')
                print(f'TRANSFERRED lod{level} primitive {index} variant material {variant}', flush=True)


if __name__ == '__main__':
    main()
