#!/usr/bin/env python3
"""Offline Blender LOD export. Keep the original rig, clips, images and level-zero samples byte-for-byte."""
import argparse
import copy
import json
from pathlib import Path
import struct
import sys


def read_glb(path):
    raw = path.read_bytes()
    magic, version, length = struct.unpack_from('<III', raw)
    if magic != 0x46546c67 or version != 2 or length != len(raw):
        raise ValueError('Expected a complete GLB 2 file')
    size, kind = struct.unpack_from('<II', raw, 12)
    if kind != 0x4e4f534a:
        raise ValueError('Expected JSON followed by an embedded BIN chunk')
    return json.loads(raw[20:20 + size]), raw[28 + size:]


def write_glb(path, document, binary):
    document['buffers'][0]['byteLength'] = len(binary)
    encoded = json.dumps(document, separators=(',', ':')).encode()
    encoded += b' ' * (-len(encoded) % 4)
    binary += b'\0' * (-len(binary) % 4)
    path.write_bytes(struct.pack('<III', 0x46546c67, 2, 28 + len(encoded) + len(binary))
                     + struct.pack('<II', len(encoded), 0x4e4f534a) + encoded
                     + struct.pack('<II', len(binary), 0x004e4942) + binary)


def accessor_bytes(document, binary, index):
    accessor = document['accessors'][index]
    if 'sparse' in accessor:
        raise ValueError('Offline LOD export expects dense accessors')
    view = document['bufferViews'][accessor['bufferView']]
    offset = view.get('byteOffset', 0) + accessor.get('byteOffset', 0)
    components = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}[accessor['type']]
    size = {5121: 1, 5123: 2, 5125: 4, 5126: 4}[accessor['componentType']] * components
    stride = view.get('byteStride', size)
    return b''.join(binary[offset + i * stride:offset + i * stride + size] for i in range(accessor['count']))


def append_accessor(document, binary, source, packed):
    binary.extend(b'\0' * (-len(binary) % 4))
    view = len(document['bufferViews'])
    document['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(packed)})
    binary.extend(packed)
    accessor = copy.deepcopy(source)
    accessor['bufferView'] = view
    accessor.pop('byteOffset', None)
    document['accessors'].append(accessor)
    return len(document['accessors']) - 1


def merge_shadow(document, binary, mesh):
    primitives = mesh['primitives']
    materials = [document['materials'][p['material']] for p in primitives]
    if any(m.get('alphaMode', 'OPAQUE') != 'OPAQUE' for m in materials):
        raise ValueError('Merged shadow geometry requires opaque materials')
    if len({m.get('doubleSided', False) for m in materials}) != 1:
        raise ValueError('Merged shadow geometry requires identical face culling')
    semantics = set().union(*(p['attributes'] for p in primitives))
    required = semantics - {'JOINTS_1', 'WEIGHTS_1'}
    if any(not required.issubset(p['attributes']) for p in primitives):
        raise ValueError('Merged shadow geometry requires matching vertex attributes')
    attributes = {}
    for semantic in sorted(semantics):
        sources = [document['accessors'][p['attributes'][semantic]] for p in primitives
                   if semantic in p['attributes']]
        if len({(a['componentType'], a['type'], a.get('normalized', False)) for a in sources}) != 1:
            raise ValueError('Mismatched shadow attribute encoding')
        element_size = len(accessor_bytes(document, binary,
            next(p['attributes'][semantic] for p in primitives if semantic in p['attributes']))) // sources[0]['count']
        # glTF omits the second influence set when all four additional weights are zero.
        packed = b''.join(accessor_bytes(document, binary, p['attributes'][semantic])
                         if semantic in p['attributes'] else b'\0' * (
                             document['accessors'][p['attributes']['POSITION']]['count'] * element_size)
                         for p in primitives)
        source = copy.deepcopy(sources[0])
        source['count'] = sum(document['accessors'][p['attributes']['POSITION']]['count'] for p in primitives)
        source.pop('min', None); source.pop('max', None)
        attributes[semantic] = append_accessor(document, binary, source, packed)
    indices = []
    offset = 0
    for primitive in primitives:
        accessor = document['accessors'][primitive['indices']]
        code = {5121: 'B', 5123: 'H', 5125: 'I'}[accessor['componentType']]
        indices.extend(i[0] + offset for i in struct.iter_unpack('<' + code,
                       accessor_bytes(document, binary, primitive['indices'])))
        offset += document['accessors'][primitive['attributes']['POSITION']]['count']
    index = append_accessor(document, binary, {'componentType': 5125, 'type': 'SCALAR', 'count': len(indices)},
                            struct.pack('<' + 'I' * len(indices), *indices))
    return {'name': mesh['name'] + '_Shadow', 'primitives': [
        {'attributes': attributes, 'indices': index, 'material': primitives[0]['material']}]}


def weld_skin_seams(bm):
    """Join UV duplicates without joining independently moving armour pieces."""
    import bmesh
    deform = bm.verts.layers.deform.active
    classes = {}
    for vertex in bm.verts:
        weights = tuple(sorted((joint, round(weight, 6)) for joint, weight in vertex[deform].items()
                               if weight > 0)) if deform else ()
        classes.setdefault(weights, []).append(vertex)
    for vertices in classes.values():
        if len(vertices) > 1:
            bmesh.ops.remove_doubles(bm, verts=vertices, dist=1e-6)


def generate(source, destination, node_name, ratios=(0.5, 0.18, 0.06), max_influences=8, protected_points=(),
             material_ratios=None):
    import bpy
    import bmesh
    from mathutils import Matrix
    from mathutils.kdtree import KDTree
    protected = KDTree(len(protected_points)) if len(protected_points) else None
    if protected is not None:
        for index, point in enumerate(protected_points):
            protected.insert(point, index)
        protected.balance()
    before, original = read_glb(source)
    node = next(n for n in before['nodes'] if n.get('name') == node_name)
    mesh_index = node['mesh']
    if before['meshes'][mesh_index].get('extras', {}).get('openyamm_lods'):
        raise ValueError('Generate from the original level-zero runtime export')
    joint_names = [before['nodes'][i]['name'] for i in before['skins'][node['skin']]['joints']]
    bind_matrices = list(struct.iter_unpack('<16f', accessor_bytes(
        before, original, before['skins'][node['skin']]['inverseBindMatrices'])))
    bpy.ops.import_scene.gltf(filepath=str(source))
    body = bpy.data.objects[node_name]
    armature = next(m.object for m in body.modifiers if m.type == 'ARMATURE')
    armature.animation_data_clear()
    for bone in armature.pose.bones:
        bone.matrix_basis = Matrix.Identity(4)
    objects = []
    budgets = material_ratios or {}
    if set(budgets) - {material.name for material in body.data.materials}:
        raise ValueError('LOD budget names an unknown material')
    for budget in (ratios, *budgets.values()):
        if len(budget) != 3 or not 1 > budget[0] > budget[1] > budget[2] > 0:
            raise ValueError('Choose three decreasing LOD ratios between zero and one')
    for level in range(1, 4):
        for slot in range(len(body.data.materials)):
            obj = body.copy(); obj.data = body.data.copy(); obj.animation_data_clear()
            obj.name = f'LOD{level}_{slot}'
            bpy.context.collection.objects.link(obj)
            bm = bmesh.new(); bm.from_mesh(obj.data)
            bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index != slot], context='FACES')
            bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
            # glTF splits vertices at UV/normal seams. Decimate the connected surface;
            # BMesh keeps the distinct per-corner UVs when joining coincident vertices.
            weld_skin_seams(bm)
            faces = len(bm.faces)
            bm.to_mesh(obj.data); bm.free()
            if not faces:
                bpy.data.objects.remove(obj, do_unlink=True)
                continue
            bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
            modifier = obj.modifiers.new('Offline_LOD', 'DECIMATE')
            slot_ratio = budgets.get(body.data.materials[slot].name, ratios)[level - 1]
            modifier.ratio = min(1.0, max(24 / faces, slot_ratio))
            modifier.use_collapse_triangulate = True
            allowance_name = None
            contact_weights = {}
            if protected is not None:
                # Preserve authored contact vertices in model-space Z-up coordinates.
                allowance = obj.vertex_groups.new(name='LOD_ReductionAllowance')
                allowance.add(list(range(len(obj.data.vertices))), 1.0, 'REPLACE')
                for vertex in obj.data.vertices:
                    _, point_index, distance = protected.find(obj.matrix_world @ vertex.co)
                    if distance < 1e-5:
                        weights = {g.group: g.weight for g in vertex.groups if g.group != allowance.index}
                        if point_index in contact_weights and contact_weights[point_index] != weights:
                            raise ValueError('A protected contact identifies different skin weights')
                        contact_weights[point_index] = weights
                        allowance.add([vertex.index], 0.0, 'REPLACE')
                modifier.vertex_group = allowance.name
                modifier.vertex_group_factor = 1.0
                allowance_name = allowance.name
            while obj.modifiers[0] != modifier:
                bpy.ops.object.modifier_move_up(modifier=modifier.name)
            bpy.ops.object.modifier_apply(modifier=modifier.name)
            if allowance_name is not None:
                obj.vertex_groups.remove(obj.vertex_groups[allowance_name])
                found = set()
                for vertex in obj.data.vertices:
                    _, point_index, distance = protected.find(obj.matrix_world @ vertex.co)
                    if distance < 1e-5 and point_index in contact_weights:
                        for group in list(vertex.groups):
                            obj.vertex_groups[group.group].remove([vertex.index])
                        for group, weight in contact_weights[point_index].items():
                            obj.vertex_groups[group].add([vertex.index], weight, 'REPLACE')
                        found.add(point_index)
                if found != contact_weights.keys():
                    raise ValueError('LOD reduction moved a protected contact')
            # Collapsing vertices combines joint sets; preserve the requested influence budget.
            bpy.ops.object.vertex_group_limit_total(limit=max_influences)
            bpy.ops.object.vertex_group_normalize_all(lock_active=False)
            objects.append(obj)
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects + [armature]: obj.select_set(True)
    temporary = destination.with_suffix('.geometry.glb')
    bpy.ops.export_scene.gltf(filepath=str(temporary), use_selection=True, export_format='GLB',
        export_animations=False, export_skins=True, export_all_influences=True)
    exported, payload = read_glb(temporary)
    document = copy.deepcopy(before); binary = bytearray(original)
    material_indices = {m['name']: i for i, m in enumerate(document['materials'])}
    lod_indices = []
    for level in range(1, 4):
        mesh = {'name': f'{node_name}_LOD{level}', 'primitives': []}
        for lower_node in exported['nodes']:
            if not lower_node.get('name', '').startswith(f'LOD{level}_') or 'mesh' not in lower_node:
                continue
            # Names identify joints; exporting a selected armature can change their glTF order.
            skin = exported['skins'][lower_node['skin']]
            remap = [joint_names.index(exported['nodes'][i]['name']) for i in skin['joints']]
            matrices = list(struct.iter_unpack('<16f', accessor_bytes(exported, payload, skin['inverseBindMatrices'])))
            if any(abs(a - b) > 1e-4 for index, matrix in zip(remap, matrices)
                   for a, b in zip(bind_matrices[index], matrix)):
                raise ValueError('Blender changed the LOD bind space')
            for key, default in [('translation', [0, 0, 0]), ('rotation', [0, 0, 0, 1]), ('scale', [1, 1, 1])]:
                if any(abs(a - b) > 1e-4 for a, b in zip(node.get(key, default), lower_node.get(key, default))):
                    raise ValueError('Blender changed the LOD mesh transform')
            for primitive in exported['meshes'][lower_node['mesh']]['primitives']:
                attributes = {}
                for semantic, index in primitive['attributes'].items():
                    accessor = exported['accessors'][index]
                    packed = accessor_bytes(exported, payload, index)
                    if semantic.startswith('JOINTS_'):
                        code = {5121: 'B', 5123: 'H'}[accessor['componentType']]
                        values = [remap[v[0]] for v in struct.iter_unpack('<' + code, packed)]
                        packed = struct.pack('<' + code * len(values), *values)
                    attributes[semantic] = append_accessor(document, binary, accessor, packed)
                index = primitive['indices']
                mesh['primitives'].append({'attributes': attributes,
                    'indices': append_accessor(document, binary, exported['accessors'][index],
                                               accessor_bytes(exported, payload, index)),
                    'material': material_indices[exported['materials'][primitive['material']]['name']]})
        if not mesh['primitives']:
            raise ValueError('Blender did not export the selected LOD')
        lod_indices.append(len(document['meshes'])); document['meshes'].append(mesh)
    shadows = []
    for index in [mesh_index] + lod_indices:
        shadow = merge_shadow(document, binary, document['meshes'][index])
        shadows.append(len(document['meshes'])); document['meshes'].append(shadow)
    document['meshes'][mesh_index].setdefault('extras', {}).update(
        openyamm_lods=lod_indices, openyamm_shadow_lods=shadows)
    counts = [sum(document['accessors'][p['indices']]['count'] // 3 for p in document['meshes'][i]['primitives'])
              for i in [mesh_index] + lod_indices]
    if not all(a > b for a, b in zip(counts, counts[1:])):
        raise ValueError('LOD triangle counts must decrease')
    write_glb(destination, document, binary)
    (destination.parent / 'lods.json').write_text(json.dumps({'triangles': counts, 'colour_meshes': [mesh_index] + lod_indices,
        'shadow_meshes': shadows, 'source': str(source), 'destination': str(destination),
        'original_geometry_rig_clips_images_retained': True}, indent=2) + '\n')
    print('LOD triangles:', counts)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path); parser.add_argument('destination', type=Path)
    parser.add_argument('--mesh-node', required=True)
    parser.add_argument('--max-influences', type=int, choices=(4, 8), default=8)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else None)
    args.destination.parent.mkdir(parents=True, exist_ok=True)
    generate(args.source.resolve(), args.destination.resolve(), args.mesh_node, max_influences=args.max_influences)
