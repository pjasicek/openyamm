#!/usr/bin/env python3
"""Blender regression: UV islands must not puncture a closed skinned surface at lower LODs."""
from collections import Counter
from pathlib import Path
import struct
from tempfile import TemporaryDirectory

from build_actor_lods import accessor_bytes, generate, read_glb, weld_skin_seams


def check_independent_skin_seams():
    import bmesh
    bm = bmesh.new()
    deform = bm.verts.layers.deform.new()
    for joint in (0, 0, 1, 1):
        vertex = bm.verts.new((0, 0, 0))
        vertex[deform][joint] = 1.0
    weld_skin_seams(bm)
    assert len(bm.verts) == 2, 'Coincident armour pieces with different bones must stay separate'
    assert {tuple(v[deform].items()) for v in bm.verts} == {((0, 1.0),), ((1, 1.0),)}
    bm.free()


def main():
    import bpy
    check_independent_skin_seams()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16)
    body = bpy.context.object
    body.name = 'SeamFixture'
    triangulate = body.modifiers.new('Triangles', 'TRIANGULATE')
    bpy.ops.object.modifier_apply(modifier=triangulate.name)
    uv = body.data.uv_layers.active.data
    for index, face in enumerate(body.data.polygons):
        # One separate UV island per triangle forces an exported vertex split at every edge.
        for corner, loop in enumerate(face.loop_indices):
            x, y = ((0, 0), (.8, 0), (0, .8))[corner]
            uv[loop].uv = ((index % 32 + x) / 32, (index // 32 + y) / 32)
    material = bpy.data.materials.new('FixtureMaterial')
    material.use_nodes = True
    body.data.materials.append(material)
    armature = bpy.data.armatures.new('FixtureRig')
    rig = bpy.data.objects.new('FixtureRig', armature)
    bpy.context.collection.objects.link(rig)
    bpy.context.view_layer.objects.active = rig
    rig.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    for index in range(12):
        bone = armature.edit_bones.new(f'Joint{index}')
        bone.head = (0, 0, 0)
        bone.tail = (0, 0, 1)
    bpy.ops.object.mode_set(mode='OBJECT')
    groups = [body.vertex_groups.new(name=f'Joint{index}') for index in range(12)]
    for vertex in body.data.vertices:
        for offset in range(4):
            groups[(vertex.index + offset) % 12].add([vertex.index], .25, 'REPLACE')
    body.modifiers.new('Skin', 'ARMATURE').object = rig
    body.parent = rig
    protected = [tuple(body.data.vertices[index].co) for index in (11, 33, 99)]
    bpy.ops.object.select_all(action='DESELECT')
    body.select_set(True)
    rig.select_set(True)
    with TemporaryDirectory(prefix='openyamm-lod-seams-') as directory:
        source, result = Path(directory) / 'source.glb', Path(directory) / 'result.glb'
        bpy.ops.export_scene.gltf(filepath=str(source), use_selection=True, export_animations=False)
        bpy.ops.wm.read_factory_settings(use_empty=True)
        material_ratios = (.4, .16, .06)
        generate(source, result, 'SeamFixture', ratios=(.8, .5, .3), protected_points=protected,
                 material_ratios={'FixtureMaterial': material_ratios})
        document, binary = read_glb(result)
        levels = [0] + document['meshes'][0]['extras']['openyamm_lods']
        for level in levels:
            primitive = document['meshes'][level]['primitives'][0]
            attributes = primitive['attributes']
            weight_sets = [list(struct.iter_unpack('<4f', accessor_bytes(document, binary, index)))
                           for name, index in attributes.items() if name.startswith('WEIGHTS_')]
            assert len(weight_sets) <= 2, f'LOD {level} exceeds eight runtime joint influences'
            for values in zip(*weight_sets):
                weights = [weight for group in values for weight in group]
                assert all(weight >= 0 for weight in weights) and abs(sum(weights) - 1) < 1e-5
            positions = list(struct.iter_unpack('<3f', accessor_bytes(
                document, binary, primitive['attributes']['POSITION'])))
            joint_sets = [list(struct.iter_unpack(
                '<4H' if document['accessors'][index]['componentType'] == 5123 else '<4B',
                accessor_bytes(document, binary, index)))
                for name, index in attributes.items() if name.startswith('JOINTS_')]
            joint_names = [document['nodes'][i]['name'] for i in document['skins'][0]['joints']]
            for source_index, (x, y, z) in zip((11, 33, 99), protected):
                distances = [sum((a-b)**2 for a, b in zip(position, (x, z, -y))) for position in positions]
                vertex = min(range(len(distances)), key=distances.__getitem__)
                assert distances[vertex] < 1e-10, f'LOD {level} moved a protected contact'
                actual = {joint_names[j]: w for joints, weights in zip(joint_sets, weight_sets)
                          for j, w in zip(joints[vertex], weights[vertex]) if w > 1e-6}
                expected = {f'Joint{(source_index+offset)%12}': .25 for offset in range(4)}
                assert actual.keys() == expected.keys() and all(abs(actual[k]-v) < 1e-5
                       for k, v in expected.items()), f'LOD {level} changed protected skin weights'
            vertices = [tuple(round(value, 5) for value in position) for position in positions]
            accessor = document['accessors'][primitive['indices']]
            if level:
                assert accessor['count'] // 3 <= 960 * material_ratios[level - 1], 'Material budget was ignored'
            code = {5123: 'H', 5125: 'I'}[accessor['componentType']]
            indices = [row[0] for row in struct.iter_unpack('<' + code, accessor_bytes(
                document, binary, primitive['indices']))]
            edges = Counter()
            for start in range(0, len(indices), 3):
                triangle = [vertices[i] for i in indices[start:start + 3]]
                for a, b in ((0, 1), (1, 2), (2, 0)):
                    edges[tuple(sorted((triangle[a], triangle[b])))] += 1
            assert all(count == 2 for count in edges.values()), f'LOD {level} punctures the closed source'
    print('UV-seam closed-surface LOD regression passes')


if __name__ == '__main__':
    main()
