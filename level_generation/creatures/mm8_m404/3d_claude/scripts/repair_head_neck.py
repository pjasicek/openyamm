"""Adopt Meshy's cleaned 18-triangle neck seam while retaining the selected head shape, weights and rig."""
from pathlib import Path
import json
import bpy
import bmesh
import numpy as np
from mathutils import Matrix, Vector, kdtree
p = Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p / 'work/rig_uv_master.blend'))
rig, body = bpy.data.objects['Rig'], bpy.data.objects['Body']
rig.animation_data.action = None
for bone in rig.pose.bones:
    bone.matrix_basis = Matrix()
bpy.context.view_layer.update()
assert np.max(np.abs(np.array(body.matrix_world) - np.eye(4))) < 1e-6
head_faces = [face for face in body.data.polygons if body.data.attributes['head'].data[face.index].value]
head_vertices = sorted({v for face in head_faces for v in face.vertices})
old_points = np.array([body.data.vertices[i].co[:] for i in head_vertices])
weights = {i: [(body.vertex_groups[g.group].name, g.weight) for g in body.data.vertices[i].groups]
           for i in head_vertices}
lookup = kdtree.KDTree(len(head_vertices))
for i in head_vertices:
    lookup.insert(body.data.vertices[i].co, i)
lookup.balance()
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=str(p.parent / 'meshy/head_retexture_v1/model_urls_glb.glb'))
head = max((o for o in set(bpy.data.objects) - before if o.type == 'MESH'), key=lambda o: len(o.data.polygons))
world = head.matrix_world.copy()
head.parent = None
head.matrix_world = world
for obj in bpy.data.objects:
    obj.select_set(obj == head)
bpy.context.view_layer.objects.active = head
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
points = np.array([v.co[:] for v in head.data.vertices])
scale = np.ptp(old_points, axis=0).max() / np.ptp(points, axis=0).max()
offset = (old_points.max(0) + old_points.min(0)) / 2 - (points.max(0) + points.min(0)) / 2 * scale
head.scale = Vector((scale, scale, scale))
head.location = Vector(offset)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
assert len(head_faces) - len(head.data.polygons) == 18
maximum = 0
for group in body.vertex_groups:
    head.vertex_groups.new(name=group.name)
for vertex in head.data.vertices:
    _, index, distance = lookup.find(vertex.co)
    maximum = max(maximum, distance)
    assert distance < .0006, ('Head shape changed', distance)
    for name, weight in weights[index]:
        head.vertex_groups[name].add([vertex.index], weight, 'REPLACE')
head.data.uv_layers.active.name = 'HeadUV'
head.data.uv_layers.new(name='UVMap')
head.data.attributes.new('piece', 'INT', 'POINT').data.foreach_set('value', [7] * len(head.data.vertices))
head.data.attributes.new('head', 'INT', 'FACE').data.foreach_set('value', [1] * len(head.data.polygons))
mesh = bmesh.new()
mesh.from_mesh(body.data)
layer = mesh.faces.layers.int['head']
bmesh.ops.delete(mesh, geom=[f for f in mesh.faces if f[layer]], context='FACES')
bmesh.ops.delete(mesh, geom=[v for v in mesh.verts if not v.link_faces], context='VERTS')
mesh.to_mesh(body.data)
mesh.free()
for obj in bpy.data.objects:
    obj.select_set(obj in (head, body))
bpy.context.view_layer.objects.active = body
bpy.ops.object.join()
for obj in list(bpy.data.objects):
    if obj not in before:
        bpy.data.objects.remove(obj, do_unlink=True)
body.data.uv_layers.active = body.data.uv_layers['UVMap']
assert len(body.data.polygons) == 11229
assert sum(v.value for v in body.data.attributes['head'].data) == 3182
report = {'removed_neck_triangles': 18, 'maximum_head_vertex_change_m': maximum,
          'body_triangles': len(body.data.polygons), 'head_triangles': 3182,
          'source': '../meshy/head_retexture_v1/model_urls_glb.glb',
          'weights': 'Nearest original head vertex, bounded to 0.6 mm; no rig or clip changes.'}
(p / 'work/head_neck_cleanup.json').write_text(json.dumps(report, indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(p / 'work/rig_uv_master.blend'))
print('HEAD_NECK_CLEANUP', report, flush=True)
