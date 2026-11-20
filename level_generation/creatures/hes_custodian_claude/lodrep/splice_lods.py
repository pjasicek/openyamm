#!/usr/bin/env python3
"""Replace chosen colour LODs (and their shadow meshes) of an installed creature GLB with those of a rebuilt GLB
(rebuild_lods.py). Everything else stays byte-for-byte: LOD0, the kept levels, materials, images, clips.
Each new primitive takes the material of the LOD0 primitive with the same material name and its
KHR_materials_variants mapping (the LOD builder drops it). New shadow meshes are tucked inside the full-detail
surface (MARGIN), as shrink_shadow_lods.py does in the reduction projects. Unreferenced buffer data is compacted.
Usage: splice_lods.py <installed.glb> <rebuilt.glb> <out.glb> <node> [levels, default 2,3]"""
import copy
import sys
from pathlib import Path

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import accessor_bytes, append_accessor, read_glb, write_glb  # noqa: E402

MARGIN = {1: 0.002, 2: 0.004, 3: 0.007}  # metres inside the full-detail surface, per shadow level


def triangles(doc, mesh_index):
    return sum(doc['accessors'][p['indices']]['count'] // 3 for p in doc['meshes'][mesh_index]['primitives'])


def floats(doc, binary, index):
    accessor = doc['accessors'][index]
    width = {'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[accessor['type']]
    return np.frombuffer(accessor_bytes(doc, binary, index), dtype=np.float32).reshape(-1, width).astype(np.float64)


def copy_mesh(doc, binary, rebuilt, rebuilt_binary, mesh, lod0):
    """Copy a rebuilt mesh into doc; materials and variant mappings follow LOD0's primitive of the same name."""
    by_name = {doc['materials'][p['material']]['name']: p for p in lod0['primitives']}
    primitives = []
    for primitive in mesh['primitives']:
        out = {'attributes': {s: append_accessor(doc, binary, rebuilt['accessors'][i],
                                                 accessor_bytes(rebuilt, rebuilt_binary, i))
                              for s, i in primitive['attributes'].items()},
               'indices': append_accessor(doc, binary, rebuilt['accessors'][primitive['indices']],
                                          accessor_bytes(rebuilt, rebuilt_binary, primitive['indices']))}
        source = by_name[rebuilt['materials'][primitive['material']]['name']]
        out['material'] = source['material']
        if 'extensions' in source:
            out['extensions'] = copy.deepcopy(source['extensions'])
        primitives.append(out)
    return {**{k: v for k, v in mesh.items() if k != 'primitives'}, 'primitives': primitives}


def tuck_shadow(doc, binary, mesh, lod0, level):
    reference = np.concatenate([floats(doc, binary, p['attributes']['POSITION']) for p in lod0['primitives']])
    normals = np.concatenate([floats(doc, binary, p['attributes']['NORMAL']) for p in lod0['primitives']])
    normals /= np.maximum(np.linalg.norm(normals, axis=1, keepdims=True), 1e-9)
    tree = cKDTree(reference)
    for primitive in mesh['primitives']:
        index = primitive['attributes']['POSITION']
        positions = floats(doc, binary, index)
        _, nearest = tree.query(positions)
        signed = np.einsum('ij,ij->i', positions - reference[nearest], normals[nearest])
        push = np.clip(signed + MARGIN[level], 0.0, 0.015)
        original = positions.copy()
        positions -= normals[nearest] * push[:, None]
        # A closed piece thinner than the margin (MM8 wasp eyes) turns inside out: keep such pieces where they were.
        faces = np.frombuffer(accessor_bytes(doc, binary, primitive['indices']), dtype={
            5121: np.uint8, 5123: np.uint16, 5125: np.uint32}[doc['accessors'][primitive['indices']]['componentType']])
        faces = faces.astype(np.int64).reshape(-1, 3)
        _, point = np.unique(original.astype(np.float32), axis=0, return_inverse=True)
        point = point.reshape(-1)
        welded = point[faces]
        graph = coo_matrix((np.ones(welded.size), (welded.reshape(-1), np.roll(welded, 1, axis=1).reshape(-1))),
                           shape=(point.max() + 1,) * 2)
        _, piece = connected_components(graph, directed=False)
        face_piece = piece[welded[:, 0]]
        volume = lambda p: np.einsum('ij,ij->i', p[faces[:, 0]], np.cross(p[faces[:, 1]], p[faces[:, 2]]))
        before = np.bincount(face_piece, volume(original), minlength=piece.max() + 1)
        after = np.bincount(face_piece, volume(positions), minlength=piece.max() + 1)
        flipped = np.flatnonzero(np.sign(before) != np.sign(after))
        restore = np.isin(piece[point], flipped)
        positions[restore] = original[restore]
        accessor = copy.deepcopy(doc['accessors'][index])
        accessor['min'], accessor['max'] = positions.min(0).tolist(), positions.max(0).tolist()
        primitive['attributes']['POSITION'] = append_accessor(doc, binary, accessor,
                                                              positions.astype(np.float32).tobytes())


def compact(doc, binary):
    used = set()
    for mesh in doc['meshes']:
        for primitive in mesh['primitives']:
            used |= set(primitive['attributes'].values()) | {primitive['indices']}
            for target in primitive.get('targets', []):
                used |= set(target.values())
    for skin in doc.get('skins', []):
        if 'inverseBindMatrices' in skin:
            used.add(skin['inverseBindMatrices'])
    for animation in doc.get('animations', []):
        for sampler in animation['samplers']:
            used |= {sampler['input'], sampler['output']}
    accessor_map = {old: new for new, old in enumerate(sorted(used))}
    views = sorted({doc['accessors'][i]['bufferView'] for i in used}
                   | {image['bufferView'] for image in doc.get('images', []) if 'bufferView' in image})
    view_map, packed, new_views = {}, bytearray(), []
    for new, old in enumerate(views):
        view = copy.deepcopy(doc['bufferViews'][old])
        start = view.get('byteOffset', 0)
        packed.extend(b'\0' * (-len(packed) % 4))
        view['byteOffset'] = len(packed)
        packed.extend(binary[start:start + view['byteLength']])
        new_views.append(view)
        view_map[old] = new
    doc['accessors'] = [dict(doc['accessors'][old], bufferView=view_map[doc['accessors'][old]['bufferView']])
                        for old in sorted(used)]
    doc['bufferViews'] = new_views
    for image in doc.get('images', []):
        if 'bufferView' in image:
            image['bufferView'] = view_map[image['bufferView']]
    for mesh in doc['meshes']:
        for primitive in mesh['primitives']:
            primitive['attributes'] = {k: accessor_map[v] for k, v in primitive['attributes'].items()}
            primitive['indices'] = accessor_map[primitive['indices']]
            for target in primitive.get('targets', []):
                for key in target:
                    target[key] = accessor_map[target[key]]
    for skin in doc.get('skins', []):
        if 'inverseBindMatrices' in skin:
            skin['inverseBindMatrices'] = accessor_map[skin['inverseBindMatrices']]
    for animation in doc.get('animations', []):
        for sampler in animation['samplers']:
            sampler['input'], sampler['output'] = accessor_map[sampler['input']], accessor_map[sampler['output']]
    return packed


def main():
    installed, rebuilt_path, out = (Path(a) for a in sys.argv[1:4])
    node_name = sys.argv[4]
    levels = [int(x) for x in (sys.argv[5] if len(sys.argv) > 5 else '2,3').split(',')]
    doc, binary = read_glb(installed)
    binary = bytearray(binary)
    rebuilt, rebuilt_binary = read_glb(rebuilt_path)
    node = next(n for n in doc['nodes'] if n.get('name') == node_name and 'mesh' in n)
    rebuilt_node = next(n for n in rebuilt['nodes'] if n.get('name') == node_name and 'mesh' in n)
    joints = [doc['nodes'][i]['name'] for i in doc['skins'][node['skin']]['joints']]
    if joints != [rebuilt['nodes'][i]['name'] for i in rebuilt['skins'][rebuilt_node['skin']]['joints']]:
        raise ValueError('joint order differs')
    lod0 = doc['meshes'][node['mesh']]
    extras, rebuilt_extras = lod0['extras'], rebuilt['meshes'][rebuilt_node['mesh']]['extras']
    for level in levels:
        colour = rebuilt['meshes'][rebuilt_extras['openyamm_lods'][level - 1]]
        doc['meshes'][extras['openyamm_lods'][level - 1]] = copy_mesh(doc, binary, rebuilt, rebuilt_binary, colour,
                                                                      lod0)
        shadow = copy_mesh(doc, binary, rebuilt, rebuilt_binary,
                           rebuilt['meshes'][rebuilt_extras['openyamm_shadow_lods'][level]], lod0)
        tuck_shadow(doc, binary, shadow, lod0, level)
        doc['meshes'][extras['openyamm_shadow_lods'][level]] = shadow
    counts = [triangles(doc, i) for i in [node['mesh']] + extras['openyamm_lods']]
    if not all(a > b for a, b in zip(counts, counts[1:])):
        raise ValueError(f'LOD triangle counts must decrease: {counts}')
    packed = compact(doc, binary)
    out.parent.mkdir(parents=True, exist_ok=True)
    write_glb(out, doc, bytes(packed))
    print('SPLICED', node_name, 'levels', levels, 'triangles', counts, f'{len(packed) / 1e6:.1f} MB')


if __name__ == '__main__':
    main()
