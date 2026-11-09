#!/usr/bin/env python3
"""Texture-quality pass on the installed GLB (2026-10-31): change only UVs and images, everything else byte-for-byte.

--corners <npz>  new LOD0 UVs per triangle (texpass_uv.py; Blender Z-up positions check the triangle order): the LOD0
                 colour primitive is re-indexed, vertices split where the new UVs differ; positions, normals, joints
                 and weights are copied from the vertex each corner had. The shadow meshes keep their own accessors.
--lod1 <glb>     colour LOD1 primitive from tools/build_actor_lods.py run on the re-UV'd LOD0 (the old LOD1 was
                 collapsed along the old seams and cannot take the new layout); material and variant mapping kept,
                 the LOD1 shadow mesh is not touched.
--image name=png replaces the embedded image of that name (same name, PNG).
--lod0-only      writes only the LOD0 colour mesh (no LOD or shadow meshes): the source tools/build_actor_lods.py takes.
Unreferenced buffer data is compacted (lod_repair_claude/scripts/splice_lods.py).
Usage: patch_glb.py <in.glb> <out.glb> [--corners npz] [--lod1 glb] [--image name=png ...] [--lod0-only]
"""
import argparse
import struct
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[4] / 'tools'))
sys.path.insert(0, str(HERE.parents[2] / 'lod_repair_claude/scripts'))
from build_actor_lods import accessor_bytes, append_accessor, read_glb, write_glb  # noqa: E402
from splice_lods import compact  # noqa: E402

NODE = 'BoneDragon'
DTYPES = {5121: np.uint8, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
WIDTH = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}


def array(doc, binary, index):
    a = doc['accessors'][index]
    return np.frombuffer(accessor_bytes(doc, binary, index), DTYPES[a['componentType']]).reshape(a['count'],
                                                                                                WIDTH[a['type']])


def put(doc, binary, source_index, values):
    source = dict(doc['accessors'][source_index])
    source['count'] = len(values)
    if source['type'] != 'SCALAR' and source['componentType'] == 5126:
        source['min'] = values.min(0).astype(float).tolist()
        source['max'] = values.max(0).astype(float).tolist()
    else:
        source.pop('min', None), source.pop('max', None)
    return append_accessor(doc, binary, source, np.ascontiguousarray(values).tobytes())


def reuv_lod0(doc, binary, corners):
    data = np.load(corners)
    primitive = doc['meshes'][next(n for n in doc['nodes'] if n.get('name') == NODE)['mesh']]['primitives'][0]
    attributes = primitive['attributes']
    faces = array(doc, binary, primitive['indices']).reshape(-1, 3).astype(np.int64)
    positions = array(doc, binary, attributes['POSITION']).astype(np.float64)
    xyz = data['xyz'].astype(np.float64)
    gltf = np.stack([xyz[..., 0], xyz[..., 2], -xyz[..., 1]], -1)
    error = np.abs(gltf - positions[faces]).max()
    if len(gltf) != len(faces) or error > 1e-5:
        raise ValueError(f'triangle order differs from the import (max corner error {error})')
    uv = data['uv'].astype(np.float64).copy()
    uv[..., 1] = 1.0 - uv[..., 1]
    keys = {}
    source, new_uv = [], []
    new_faces = np.zeros_like(faces)
    for f in range(len(faces)):
        for k in range(3):
            key = (int(faces[f, k]), round(float(uv[f, k, 0]), 7), round(float(uv[f, k, 1]), 7))
            index = keys.get(key)
            if index is None:
                index = keys[key] = len(source)
                source.append(key[0])
                new_uv.append(uv[f, k])
            new_faces[f, k] = index
    source = np.array(source)
    out = {}
    for semantic, index in attributes.items():
        values = np.array(new_uv, np.float32) if semantic == 'TEXCOORD_0' else array(doc, binary, index)[source]
        out[semantic] = put(doc, binary, index, values)
    index_type = np.uint16 if len(source) < 65536 else np.uint32
    indices = dict(doc['accessors'][primitive['indices']])
    indices['componentType'] = 5123 if index_type is np.uint16 else 5125
    indices.pop('min', None), indices.pop('max', None)
    indices['count'] = new_faces.size
    primitive['indices'] = append_accessor(doc, binary, indices, new_faces.astype(index_type).tobytes())
    primitive['attributes'] = out
    print(f'LOD0 re-UV: {len(positions)} -> {len(source)} vertices, {len(faces)} triangles')


def replace_lod1(doc, binary, path):
    lods, payload = read_glb(Path(path))
    node = next(n for n in doc['nodes'] if n.get('name') == NODE)
    target = doc['meshes'][doc['meshes'][node['mesh']]['extras']['openyamm_lods'][0]]
    lnode = next(n for n in lods['nodes'] if n.get('name') == NODE)
    joints = [doc['nodes'][j]['name'] for j in doc['skins'][node['skin']]['joints']]
    ljoints = [lods['nodes'][j]['name'] for j in lods['skins'][lnode['skin']]['joints']]
    if joints != ljoints:
        raise ValueError('LOD GLB has another joint order')
    source = lods['meshes'][lods['meshes'][lnode['mesh']]['extras']['openyamm_lods'][0]]
    if len(source['primitives']) != 1 or len(target['primitives']) != 1:
        raise ValueError('expected one LOD1 primitive')
    src, dst = source['primitives'][0], target['primitives'][0]
    dst['attributes'] = {s: append_accessor(doc, binary, lods['accessors'][i], accessor_bytes(lods, payload, i))
                         for s, i in src['attributes'].items()}
    dst['indices'] = append_accessor(doc, binary, lods['accessors'][src['indices']],
                                     accessor_bytes(lods, payload, src['indices']))
    print(f"LOD1 replaced: {lods['accessors'][src['indices']]['count'] // 3} triangles")


def replace_image(doc, binary, name, path):
    image = next(i for i in doc['images'] if i.get('name') == name)
    data = Path(path).read_bytes()
    if data[:8] != b'\x89PNG\r\n\x1a\n':
        raise ValueError(f'{path} is not a PNG')
    binary.extend(b'\0' * (-len(binary) % 4))
    doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(data)})
    binary.extend(data)
    image['bufferView'] = len(doc['bufferViews']) - 1
    image['mimeType'] = 'image/png'
    width, height = struct.unpack('>II', data[16:24])
    print(f'image {name} <- {path} ({width}x{height})')


def lod0_only(doc):
    node = next(n for n in doc['nodes'] if n.get('name') == NODE)
    keep = node['mesh']
    doc['meshes'][keep].pop('extras', None)
    doc['meshes'] = [doc['meshes'][keep]]
    node['mesh'] = 0
    print('LOD0 only')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('src'), parser.add_argument('out')
    parser.add_argument('--corners'), parser.add_argument('--lod1')
    parser.add_argument('--image', action='append', default=[])
    parser.add_argument('--lod0-only', action='store_true')
    args = parser.parse_args()
    doc, binary = read_glb(Path(args.src))
    binary = bytearray(binary)
    if args.corners:
        reuv_lod0(doc, binary, args.corners)
    if args.lod1:
        replace_lod1(doc, binary, args.lod1)
    for spec in args.image:
        name, path = spec.split('=', 1)
        replace_image(doc, binary, name, path)
    if args.lod0_only:
        lod0_only(doc)
    write_glb(Path(args.out), doc, compact(doc, binary))


if __name__ == '__main__':
    main()
