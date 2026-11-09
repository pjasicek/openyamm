#!/usr/bin/env python3
"""Link the turret's authored LODs into the runtime actor, as tools/build_actor_lods.py does for decimated ones:
the meshes <Mesh>_LOD1..3 of export/<name>_authored_lods.glb (the same rig, built by build_turret_actor.py) are
appended to the prepared LOD0 GLB as the base mesh's `openyamm_lods`, with one merged shadow mesh per level
(`openyamm_shadow_lods`); the LOD0 bytes, rig, clips and images stay as they are. Joints map by name, materials by
name. Writes <out> and lods.json beside it.
Usage: link_lods.py <runtime lod0.glb> <authored lods.glb> <out.glb> <mesh node>"""
import json
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import accessor_bytes, append_accessor, merge_shadow, read_glb, write_glb  # noqa: E402


def main():
    source, authored, destination, node_name = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]), sys.argv[4]
    document, original = read_glb(source)
    binary = bytearray(original)
    lods, payload = read_glb(authored)
    node = next(n for n in document['nodes'] if n.get('name') == node_name)
    mesh_index = node['mesh']
    if document['meshes'][mesh_index].get('extras', {}).get('openyamm_lods'):
        raise ValueError('Link into the level-zero runtime export')
    joint_names = [document['nodes'][i]['name'] for i in document['skins'][node['skin']]['joints']]
    bind = list(struct.iter_unpack('<16f', accessor_bytes(document, original,
                                                          document['skins'][node['skin']]['inverseBindMatrices'])))
    materials = {m['name']: i for i, m in enumerate(document['materials'])}
    lod_indices = []
    for level in range(1, 4):
        lower = next(n for n in lods['nodes'] if n.get('name') == f'{node_name}_LOD{level}')
        for key, default in [('translation', [0, 0, 0]), ('rotation', [0, 0, 0, 1]), ('scale', [1, 1, 1])]:
            if any(abs(a - b) > 1e-4 for a, b in zip(node.get(key, default), lower.get(key, default))):
                raise ValueError('An authored LOD has another mesh transform')
        skin = lods['skins'][lower['skin']]
        remap = [joint_names.index(lods['nodes'][i]['name']) for i in skin['joints']]
        matrices = list(struct.iter_unpack('<16f', accessor_bytes(lods, payload, skin['inverseBindMatrices'])))
        if any(abs(a - b) > 1e-4 for index, matrix in zip(remap, matrices) for a, b in zip(bind[index], matrix)):
            raise ValueError('An authored LOD has another bind space')
        mesh = {'name': f'{node_name}_LOD{level}', 'primitives': []}
        for primitive in lods['meshes'][lower['mesh']]['primitives']:
            attributes = {}
            for semantic, index in primitive['attributes'].items():
                accessor = lods['accessors'][index]
                packed = accessor_bytes(lods, payload, index)
                if semantic.startswith('JOINTS_'):
                    code = {5121: 'B', 5123: 'H'}[accessor['componentType']]
                    values = [remap[v[0]] for v in struct.iter_unpack('<' + code, packed)]
                    packed = struct.pack('<' + code * len(values), *values)
                attributes[semantic] = append_accessor(document, binary, accessor, packed)
            mesh['primitives'].append({'attributes': attributes,
                                       'indices': append_accessor(document, binary, lods['accessors'][primitive['indices']],
                                                                  accessor_bytes(lods, payload, primitive['indices'])),
                                       'material': materials[lods['materials'][primitive['material']]['name']]})
        lod_indices.append(len(document['meshes']))
        document['meshes'].append(mesh)
    shadows = []
    for index in [mesh_index] + lod_indices:
        shadows.append(len(document['meshes']))
        document['meshes'].append(merge_shadow(document, binary, document['meshes'][index]))
    document['meshes'][mesh_index].setdefault('extras', {}).update(openyamm_lods=lod_indices,
                                                                   openyamm_shadow_lods=shadows)
    counts = [sum(document['accessors'][p['indices']]['count'] // 3 for p in document['meshes'][i]['primitives'])
              for i in [mesh_index] + lod_indices]
    if not all(a > b for a, b in zip(counts, counts[1:])):
        raise ValueError('LOD triangle counts must decrease')
    write_glb(destination, document, binary)
    (destination.parent / 'lods.json').write_text(json.dumps({
        'triangles': counts, 'colour_meshes': [mesh_index] + lod_indices, 'shadow_meshes': shadows,
        'source': str(source), 'authored': str(authored), 'destination': str(destination),
        'original_geometry_rig_clips_images_retained': True}, indent=2) + '\n')
    print('LOD triangles:', counts)


if __name__ == '__main__':
    main()
