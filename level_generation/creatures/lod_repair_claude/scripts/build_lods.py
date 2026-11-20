#!/usr/bin/env python3
"""Rebuild chosen colour LODs (and their shadow meshes) of an installed creature GLB from its LOD0 with MeshLab's
quadric collapse on positions, without optimal placement: every LOD vertex is an LOD0 vertex, so a LOD is a subset of
LOD0's vertex buffers (positions, normals, UVs, skin weights, burn order, all exact) plus a new index buffer.
No re-binding and no weight transfer.

Per LOD0 primitive: vertices at the same position with the same skin weights are welded for the collapse (glTF
splits them at UV and normal seams); coincident vertices with different weights are moved 2e-5 m towards their own
faces so they stay apart. Each output triangle then takes, at its three welded points, the LOD0 vertices of one UV
island (the island most of its corners share, then the best normal). A corner without a vertex in that island
(a triangle across a UV seam) gets a copy of its vertex with the UV extended from the island's nearest LOD0 triangle,
so no triangle stretches across the atlas. Materials and KHR_materials_variants mappings stay LOD0's.
The shadow mesh of each rebuilt level is the merged colour LOD (build_actor_lods.merge_shadow), tucked inside the
full-detail surface (splice_lods.tuck_shadow). Old far materials (<material>_LOD<N>) the replaced meshes used are
dropped with their images (strip_lod_materials.py). Everything else stays byte-for-byte; unused buffer data is compacted.
Run with a Python that has pymeshlab (README). Usage: build_lods.py <installed.glb> <node> <out.glb> <level:ratio,...>"""
import copy
import os
import sys
from pathlib import Path

import numpy as np
import pymeshlab
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3] / 'tools'))
sys.path.insert(0, str(HERE))
from build_actor_lods import accessor_bytes, append_accessor, merge_shadow, read_glb, write_glb  # noqa: E402
from splice_lods import compact, floats, triangles, tuck_shadow  # noqa: E402
from strip_lod_materials import strip_unused_lod_materials  # noqa: E402

SKIN = ('JOINTS_0', 'WEIGHTS_0', 'JOINTS_1', 'WEIGHTS_1')
# MeshLab's collapse crashes on a few meshes (MM6 Queen fighter); repair.py then retries with topology preserved.
PRESERVE_TOPOLOGY = os.environ.get('LOD_PRESERVE_TOPOLOGY') == '1'
# Lining fix (default since 2026-11-12, LOD_LINING_FIX=0 turns it off; also read by transfer_textures.py): cloth with a
# separate lining joined at the hem by a thin rim (mm6_pfem skirt). The collapse merges the layers there, so outward far
# triangles take lining corners whose LOD0 normals face inward: dark, streaked hems in game. Such a corner gets a copy
# of its vertex with the normal flipped (and transfer_textures.py takes colours, too, only from LOD0 faces facing the
# far triangle's way). On four robed bodies (mm7_m430, mm6_sor1, mm8_m472, mm7_m290) it removed the 5-12 % of far
# triangles with an inward corner at equal scores (lod-batch-a, lod_repair_claude/README.md).
LINING_FIX = os.environ.get('LOD_LINING_FIX', '1') != '0'
AGAINST = -0.2
# Option (LOD_CURVATURE_WEIGHT=<w>, repair.py's curvature steps use 8): thin features (bat finger bones, treant twigs,
# skeleton ribs, lich crown spikes) erode in the plain collapse. Weight MeshLab's quadric error per vertex by
# 1 + w x clip(curvature / median, 0, cap), so tubes and spikes survive and broad surfaces take the cut (lod-step1b,
# 2026-11-12). LOD_CURVATURE_LEVELS=2 weights LOD2 only (default: every rebuilt level).
CURVATURE_WEIGHT = float(os.environ.get('LOD_CURVATURE_WEIGHT', '0'))
CURVATURE_LEVELS = {int(k) for k in os.environ.get('LOD_CURVATURE_LEVELS', '').split(',') if k.strip()}
CURVATURE_CAP = float(os.environ.get('LOD_CURVATURE_CAP', '8'))


def rows(doc, binary, index):
    accessor = doc['accessors'][index]
    raw = np.frombuffer(accessor_bytes(doc, binary, index), dtype=np.uint8)
    return raw.reshape(accessor['count'], -1)


def source_faces(doc, binary, primitive):
    dtype = {5121: np.uint8, 5123: np.uint16, 5125: np.uint32}[doc['accessors'][primitive['indices']]['componentType']]
    return np.frombuffer(accessor_bytes(doc, binary, primitive['indices']), dtype=dtype).astype(np.int64).reshape(-1, 3)


def extend_uv(point, triangle_ids, faces, positions, uv):
    """UV of `point` from the nearest of the given LOD0 triangles, extended linearly over its plane."""
    a, b, c = positions[faces[triangle_ids, 0]], positions[faces[triangle_ids, 1]], positions[faces[triangle_ids, 2]]
    best = np.argmin(np.linalg.norm((a + b + c) / 3 - point, axis=1))
    a, b, c = a[best], b[best], c[best]
    e1, e2, d = b - a, c - a, point - a
    g = np.array([[e1 @ e1, e1 @ e2], [e1 @ e2, e2 @ e2]])
    v, w = np.linalg.solve(g + np.eye(2) * 1e-18, np.array([d @ e1, d @ e2]))
    corners = uv[faces[triangle_ids[best]]]
    return corners[0] + v * (corners[1] - corners[0]) + w * (corners[2] - corners[0])


def curvature_quality(vertices, face_matrix, weight):
    """Per-vertex collapse weight 1 + weight x clip(curvature / median, 0, CURVATURE_CAP). Curvature = umbrella
    Laplacian over the squared mean edge length, about 1 / radius (MeshLab's own curvature filter refuses non-manifold
    meshes)."""
    edges = np.concatenate([face_matrix[:, [0, 1]], face_matrix[:, [1, 2]], face_matrix[:, [2, 0]]])
    edges = np.unique(np.sort(edges, axis=1), axis=0)
    total, count, length2 = np.zeros_like(vertices), np.zeros(len(vertices)), np.zeros(len(vertices))
    for a, b in ((0, 1), (1, 0)):
        np.add.at(total, edges[:, a], vertices[edges[:, b]])
        np.add.at(count, edges[:, a], 1)
        np.add.at(length2, edges[:, a], ((vertices[edges[:, a]] - vertices[edges[:, b]]) ** 2).sum(1))
    count = np.maximum(count, 1)
    laplacian = np.linalg.norm(total / count[:, None] - vertices, axis=1)
    curvature = 2 * laplacian / np.maximum(length2 / count, 1e-12)
    scale = np.median(curvature[curvature > 0]) if (curvature > 0).any() else 1.0
    return 1.0 + weight * np.clip(curvature / scale, 0, CURVATURE_CAP)


def collapse(points, faces, target, curvature_weight=0.0):
    """MeshLab quadric collapse of `faces` (indices into `points`) without optimal placement, its error optionally
    weighted by curvature; returns the kept triangles as indices into `points`."""
    used, local = np.unique(faces, return_inverse=True)
    face_matrix = local.reshape(-1, 3).astype(np.int32)
    meshes = pymeshlab.MeshSet()
    if curvature_weight:
        quality = curvature_quality(points[used], face_matrix, curvature_weight)
        meshes.add_mesh(pymeshlab.Mesh(vertex_matrix=points[used], face_matrix=face_matrix, v_scalar_array=quality))
    else:
        meshes.add_mesh(pymeshlab.Mesh(vertex_matrix=points[used], face_matrix=face_matrix))
    meshes.meshing_decimation_quadric_edge_collapse(
        targetfacenum=max(int(round(target)), 12), qualitythr=.3, preserveboundary=False, optimalplacement=False,
        preservenormal=True, planarquadric=True, preservetopology=PRESERVE_TOPOLOGY,
        qualityweight=bool(curvature_weight))
    distance, nearest = cKDTree(points[used]).query(meshes.current_mesh().vertex_matrix())
    if distance.max() > 1e-9:
        raise ValueError(f'decimated vertex not found in LOD0 ({distance.max():.2e} m)')
    return used[nearest][meshes.current_mesh().face_matrix().astype(np.int64)]


def decimate_primitive(doc, binary, primitive, ratio, curvature_weight=0.0):
    """Decimated triangles of the primitive as corner references: a non-negative value is a vertex of the
    primitive, -1 - k is the k-th new vertex (a copy of vertex `source` with UV `uv`, for corners whose triangle
    crosses a UV seam). Returns (corners, [(source, uv), ...])."""
    attributes = primitive['attributes']
    positions = floats(doc, binary, attributes['POSITION'])
    normals = floats(doc, binary, attributes['NORMAL'])
    uv = floats(doc, binary, attributes['TEXCOORD_0']) if 'TEXCOORD_0' in attributes else None
    faces = source_faces(doc, binary, primitive)
    skin = np.hstack([rows(doc, binary, attributes[s]) for s in SKIN if s in attributes]) \
        if 'JOINTS_0' in attributes else np.zeros((len(positions), 0), np.uint8)
    key = np.hstack([positions.astype(np.float32).view(np.uint8).reshape(len(positions), -1), skin])
    _, welded = np.unique(key, axis=0, return_inverse=True)
    welded = welded.reshape(-1)
    count = welded.max() + 1
    points = np.zeros((count, 3))
    points[welded] = positions
    # Coincident welded points (different skin weights): move each towards its own faces.
    pairs = cKDTree(points).query_pairs(1e-6, output_type='ndarray')
    if len(pairs):
        centre = points[welded[faces]].mean(1)
        total, hits = np.zeros_like(points), np.zeros(count)
        for k in range(3):
            np.add.at(total, welded[faces[:, k]], centre)
            np.add.at(hits, welded[faces[:, k]], 1)
        for i in np.unique(pairs):
            direction = total[i] / max(hits[i], 1) - points[i]
            points[i] += 2e-5 * direction / (np.linalg.norm(direction) + 1e-12)
    # One plain quadric collapse on positions only, borders free. The texture-aware collapse broke the lizardman's
    # fragmented atlas (spikes, lost head); UVs are restored per triangle below. With protected borders the open
    # cloth and feather pieces kept their faces and the closed body skin took the whole cut (MM6 cannibal and MM7
    # harpy LOD3 lost the body); reducing each piece on its own overshot the budget and failed two of four pilots.
    # Faces whose corners weld to one point (MM9 heads: zero-area slivers) crash MeshLab's collapse; they draw nothing.
    input_faces = welded[faces]
    input_faces = input_faces[(input_faces[:, 0] != input_faces[:, 1]) & (input_faces[:, 1] != input_faces[:, 2])
                              & (input_faces[:, 0] != input_faces[:, 2])]
    corners = collapse(points, input_faces, len(faces) * ratio, curvature_weight)
    corners = corners[(corners[:, 0] != corners[:, 1]) & (corners[:, 1] != corners[:, 2])
                      & (corners[:, 0] != corners[:, 2])]
    # A small closed piece (crystal facet, tooth) can collapse to two back-to-back triangles: invisible, and flagged
    # as an inverted closed part by check_winding.py. Drop pieces of two triangles or fewer.
    graph = coo_matrix((np.ones(corners.size), (corners.reshape(-1), np.roll(corners, 1, axis=1).reshape(-1))),
                       shape=(count, count))
    _, piece = connected_components(graph, directed=False)
    sizes = np.bincount(piece[corners[:, 0]])
    corners = corners[sizes[piece[corners[:, 0]]] > 2]
    members = {}
    for vertex, point in enumerate(welded):
        members.setdefault(point, []).append(vertex)
    # UV islands: glTF splits vertices at every UV seam, so islands are the connected parts of the index graph.
    graph = coo_matrix((np.ones(faces.size), (faces.reshape(-1), np.roll(faces, 1, axis=1).reshape(-1))),
                       shape=(len(positions),) * 2)
    _, island = connected_components(graph, directed=False)
    island_faces = {}
    for f, i in enumerate(island[faces[:, 0]]):
        island_faces.setdefault(i, []).append(f)
    island_faces = {i: np.array(f) for i, f in island_faces.items()}
    face_normals = np.cross(points[corners[:, 1]] - points[corners[:, 0]], points[corners[:, 2]] - points[corners[:, 0]])
    face_normals /= np.maximum(np.linalg.norm(face_normals, axis=1, keepdims=True), 1e-12)
    result = np.zeros_like(corners)
    added = []
    flipped = {}

    def corner_vertex(vertex, f, uv_override=None):
        """Corner reference for `vertex` in triangle f: the vertex itself, or with LINING_FIX a copy with the normal
        flipped when it faces against the triangle; uv_override makes a seam copy (always added)."""
        flip = LINING_FIX and normals[vertex] @ face_normals[f] < AGAINST
        if uv_override is None and not flip:
            return vertex
        if uv_override is None:
            if vertex not in flipped:
                added.append((vertex, None, True))
                flipped[vertex] = len(added)
            return -flipped[vertex]
        added.append((vertex, uv_override, flip))
        return -len(added)

    for f, triangle in enumerate(corners):
        candidates = [np.array(members[p]) for p in triangle]
        votes = {}
        for c in candidates:
            for vertex in c:
                votes[island[vertex]] = votes.get(island[vertex], 0) + 1 + 1e-3 * (normals[vertex] @ face_normals[f])
        chosen = max(votes, key=votes.get)
        for k, c in enumerate(candidates):
            inside = c[island[c] == chosen]
            if len(inside):
                result[f, k] = corner_vertex(inside[np.argmax(normals[inside] @ face_normals[f])], f)
            else:
                best = c[np.argmax(normals[c] @ face_normals[f])]
                new_uv = extend_uv(points[triangle[k]], island_faces[chosen], faces, positions, uv) \
                    if uv is not None else uv
                if new_uv is None:
                    result[f, k] = corner_vertex(best, f)
                else:
                    result[f, k] = corner_vertex(best, f, new_uv)
    return result, added


def subset_primitive(doc, binary, primitive, corners, added):
    """New primitive with the used vertices of `primitive` plus the added vertices (source, UV or None to keep the
    source's, normal flipped), indexed by `corners`."""
    references = np.where(corners >= 0, corners, len(rows(doc, binary, primitive['attributes']['POSITION']))
                          - 1 - corners)
    used, remapped = np.unique(references, return_inverse=True)
    out = {'attributes': {}, 'material': primitive['material']}
    if 'extensions' in primitive:
        out['extensions'] = copy.deepcopy(primitive['extensions'])
    for semantic, index in primitive['attributes'].items():
        source = copy.deepcopy(doc['accessors'][index])
        original = rows(doc, binary, index)
        extra = original[[s for s, _, _ in added]].copy() if added else original[:0]
        if semantic == 'TEXCOORD_0' and added:
            uvs = original[[s for s, _, _ in added]].copy().view(np.float32).reshape(len(added), 2)
            for i, (_, u, _) in enumerate(added):
                if u is not None:
                    uvs[i] = u
            extra = uvs.astype(np.float32).view(np.uint8).reshape(len(added), -1)
        if semantic == 'NORMAL' and any(f for _, _, f in added):
            normal = extra.copy().view(np.float32).reshape(len(added), 3)
            normal[[i for i, (_, _, f) in enumerate(added) if f]] *= -1
            extra = normal.view(np.uint8).reshape(len(added), -1)
        data = np.vstack([original, extra])[used]
        source['count'] = len(used)
        if semantic == 'POSITION':
            values = data.copy().view(np.float32).reshape(len(used), 3)
            source['min'], source['max'] = values.min(0).tolist(), values.max(0).tolist()
        else:
            source.pop('min', None)
            source.pop('max', None)
        out['attributes'][semantic] = append_accessor(doc, binary, source, data.tobytes())
    index_type = 5123 if len(used) < 65536 else 5125
    packed = remapped.reshape(-1).astype(np.uint16 if index_type == 5123 else np.uint32).tobytes()
    out['indices'] = append_accessor(doc, binary, {'componentType': index_type, 'type': 'SCALAR',
                                                   'count': remapped.size}, packed)
    return out


def drop_inverted_parts(doc, binary, primitive):
    """Remove closed parts with negative volume from a far-LOD primitive, found as check_winding.py finds them
    (positions rounded to 1e-5, every edge shared twice). The collapse turns a few small closed pieces of MM9 bodies
    inside out (4-48 triangles: earrings, a weapon tip, folds); at the far switch sizes they are a pixel or two.
    Single-sided primitives only (the engine culls their back faces; check_winding.py skips double-sided ones)."""
    if doc['materials'][primitive['material']].get('doubleSided'):
        return
    positions = floats(doc, binary, primitive['attributes']['POSITION']).astype(np.float64)
    faces = source_faces(doc, binary, primitive)
    _, key = np.unique(np.round(positions, 5), axis=0, return_inverse=True)
    key = key.reshape(-1)
    welded = key[faces]
    graph = coo_matrix((np.ones(welded.size), (welded.reshape(-1), np.roll(welded, 1, axis=1).reshape(-1))),
                       shape=(key.max() + 1,) * 2)
    _, piece = connected_components(graph, directed=False)
    face_piece = piece[welded[:, 0]]
    a, b, c = positions[faces[:, 0]], positions[faces[:, 1]], positions[faces[:, 2]]
    volume = np.bincount(face_piece, np.einsum('ij,ij->i', a, np.cross(b, c)), minlength=piece.max() + 1)
    edges = np.sort(np.concatenate([welded[:, [0, 1]], welded[:, [1, 2]], welded[:, [2, 0]]]), axis=1)
    unique_edges, uses = np.unique(edges, axis=0, return_counts=True)
    open_piece = np.zeros(piece.max() + 1, bool)
    open_piece[piece[unique_edges[uses != 2, 0]]] = True
    drop = (volume < 0) & ~open_piece
    keep = ~drop[face_piece]
    if keep.all():
        return
    kept = faces[keep].astype(np.uint32).reshape(-1)
    primitive['indices'] = append_accessor(doc, binary, {'componentType': 5125, 'type': 'SCALAR', 'count': len(kept)},
                                           kept.tobytes())


def merge_body_shadow(doc, binary, mesh):
    """merge_shadow, with the merged mesh culled like its first (body) material even when another material is double
    sided (MM9 peasants' heads became double sided after their shadows were merged; the installed shadow meshes
    already draw with the body material alone)."""
    materials = [doc['materials'][p['material']] for p in mesh['primitives']]
    saved = [m.get('doubleSided') for m in materials]
    for material in materials:
        material['doubleSided'] = materials[0].get('doubleSided', False)
    try:
        return merge_shadow(doc, binary, mesh)
    finally:
        for material, value in zip(materials, saved):
            if value is None:
                material.pop('doubleSided', None)
            else:
                material['doubleSided'] = value


def main():
    installed, node_name, out = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3])
    plan = {int(k): float(v) for k, v in (item.split(':') for item in sys.argv[4].split(','))}
    doc, binary = read_glb(installed)
    binary = bytearray(binary)
    node = next(n for n in doc['nodes'] if n.get('name') == node_name and 'mesh' in n)
    lod0 = doc['meshes'][node['mesh']]
    extras = lod0['extras']
    for level, ratio in sorted(plan.items()):
        colour_index = extras['openyamm_lods'][level - 1]
        weight = CURVATURE_WEIGHT if not CURVATURE_LEVELS or level in CURVATURE_LEVELS else 0.0
        mesh = {'name': doc['meshes'][colour_index]['name'], 'primitives': [
            subset_primitive(doc, binary, p, *decimate_primitive(doc, binary, p, ratio, weight))
            for p in lod0['primitives']]}
        for primitive in mesh['primitives']:
            drop_inverted_parts(doc, binary, primitive)
        doc['meshes'][colour_index] = mesh
        if level >= len(extras.get('openyamm_shadow_lods', [])):
            continue  # no shadow mesh at this level (elementals cast none, the fish school has fewer)
        shadow_index = extras['openyamm_shadow_lods'][level]
        shadow = merge_body_shadow(doc, binary, mesh)
        shadow['name'] = doc['meshes'][shadow_index]['name']
        if 'extensions' in mesh['primitives'][0]:
            shadow['primitives'][0]['extensions'] = copy.deepcopy(mesh['primitives'][0]['extensions'])
            # A shadow LOD must be opaque in every tier (GltfModelLoader validateMeshLods): a translucent tier (the
            # Dagrell Spectre, Dagrell_C) casts with the shadow's default material, as the installed shadows did
            # (Lich Lab refused mm9_dagrell, 2026-11-07).
            for mapping in shadow['primitives'][0]['extensions'].get('KHR_materials_variants', {}).get('mappings', []):
                if doc['materials'][mapping['material']].get('alphaMode', 'OPAQUE') != 'OPAQUE':
                    mapping['material'] = shadow['primitives'][0]['material']
        tuck_shadow(doc, binary, shadow, lod0, level)
        drop_inverted_parts(doc, binary, shadow['primitives'][0])
        doc['meshes'][shadow_index] = shadow
    counts = [triangles(doc, i) for i in [node['mesh']] + extras['openyamm_lods']]
    if not all(a > b for a, b in zip(counts, counts[1:])):
        raise ValueError(f'LOD triangle counts must decrease: {counts}')
    # A rerun on an already-repaired GLB: the replaced far meshes no longer use their old <material>_LOD<N> copies,
    # which apply_bake.py would refuse; drop them and their images.
    stripped = strip_unused_lod_materials(doc)
    if stripped:
        print('STRIPPED old far materials:', ', '.join(stripped))
    packed = compact(doc, binary)
    out.parent.mkdir(parents=True, exist_ok=True)
    write_glb(out, doc, bytes(packed))
    print('BUILT', node_name, {k: v for k, v in sorted(plan.items())}, 'triangles', counts,
          f'curvature {CURVATURE_WEIGHT:g}' + (f' at {sorted(CURVATURE_LEVELS)}' if CURVATURE_LEVELS else ''),
          'lining fix' if LINING_FIX else 'no lining fix',
          f'{len(packed) / 1e6:.1f} MB')


if __name__ == '__main__':
    main()
