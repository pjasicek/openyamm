"""Repair the selected Pirate geometry, label its parts, and export the provisional rig upload."""
from pathlib import Path
import bpy
import bmesh
import json
import math
import sys
import numpy as np
from mathutils import Vector

project = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project / 'scripts'))
import common

bpy.ops.wm.open_mainfile(filepath=str(project / 'work/st_v1_parts.blend'))
for name in ['P08', 'P15', 'P16']:
    bpy.data.objects.remove(bpy.data.objects[name], do_unlink=True)

# Close the two generated hand holes before separating the middle/ring fingertip bridge.
hand_mesh = bpy.data.objects['P03'].data
bm = bmesh.new()
bm.from_mesh(hand_mesh)

def cap_hand_holes():
    edges = {e for e in bm.edges if e.is_boundary and all(v.co.z < 0.9 for v in e.verts)}
    while edges:
        first = edges.pop()
        order = list(first.verts)
        while order[-1] is not order[0]:
            choices = [e for e in edges if order[-1] in e.verts]
            assert len(choices) == 1, 'Hand boundary must form a closed simple loop'
            edge = choices[0]
            edges.remove(edge)
            order.append(edge.other_vert(order[-1]))
        face = bm.faces.new(order[:-1])
        bmesh.ops.triangulate(bm, faces=[face], quad_method='BEAUTY', ngon_method='BEAUTY')

cap_hand_holes()
cut = bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:],
                            plane_co=(-0.505, 0, 0.803), plane_no=(1, 0, -0.4), dist=1e-7)
seam = [e for e in cut['geom_cut'] if isinstance(e, bmesh.types.BMEdge)
        and all(v.co.z < 0.83 for v in e.verts)]
assert len(seam) >= 3
bmesh.ops.split_edges(bm, edges=seam)
normal = Vector((1, 0, -0.4)).normalized()
distance = lambda co: co.x + 0.505 - 0.4 * (co.z - 0.803)
for vertex in bm.verts:
    if vertex.co.z < 0.83 and abs(distance(vertex.co)) < 1e-6:
        side = sum(distance(f.calc_center_median()) for f in vertex.link_faces)
        vertex.co += normal * (0.003 if side > 0 else -0.003)
cap_hand_holes()
assert not [e for e in bm.edges if e.is_boundary and all(v.co.z < 0.9 for v in e.verts)]
palm = [v for v in bm.verts if (v.co - Vector((-0.456, -0.036, 0.846))).length < 0.024]
for _ in range(3):
    bmesh.ops.smooth_vert(bm, verts=palm, factor=0.4, use_axis_x=True, use_axis_y=True, use_axis_z=True)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
bm.to_mesh(hand_mesh)
bm.free()

# The generated right boot points backward; mirror the matching, correctly oriented left boot.
left, right = bpy.data.objects['P05'], bpy.data.objects['P06']
top = lambda obj: np.array([v.co[:] for v in obj.data.vertices if v.co.z > 0.40]).mean(0)
target = top(right)
right.data = left.data.copy()
for vertex in right.data.vertices:
    vertex.co.x *= -1
shift = Vector(target - top(right))
for vertex in right.data.vertices:
    vertex.co += shift
bm = bmesh.new()
bm.from_mesh(right.data)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
bm.to_mesh(right.data)
bm.free()

# The right eyepatch is absent from the generated head; its underlying eye supplies the position.
eye = bpy.data.objects['P14']
centre = sum((v.co for v in eye.data.vertices), Vector()) / len(eye.data.vertices)
bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8,
                                   location=(centre.x, centre.y - 0.012, centre.z))
patch = bpy.context.object
patch.name = 'P24'
patch.scale = (0.028, 0.009, 0.020)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

labels = {0: 'shirt', 1: 'head_neck_chest', 2: 'trousers_sash', 3: 'right_hand',
          4: 'bandanna', 5: 'left_boot', 6: 'right_boot', 7: 'left_hook_socket',
          9: 'right_cuff', 10: 'left_cuff', 11: 'sash_knot', 12: 'sash_tail_long',
          13: 'left_eye', 14: 'right_eye_under_patch', 17: 'left_earring', 18: 'right_earring',
          19: 'sash_tail_short', 20: 'belt_loop', 21: 'left_ear_detail',
          22: 'belt_loop', 23: 'right_ear_detail', 24: 'right_eyepatch'}
palette = {'skin': (0.55, 0.33, 0.20, 1), 'cloth': (0.70, 0.70, 0.68, 1),
           'green': (0.17, 0.34, 0.035, 1), 'leather': (0.16, 0.08, 0.035, 1),
           'steel': (0.22, 0.23, 0.24, 1), 'gold': (0.6, 0.38, 0.07, 1), 'black': (0.015, 0.012, 0.01, 1)}
materials = {}
for name, colour in palette.items():
    material = bpy.data.materials.new('Pirate_' + name)
    material.diffuse_color = colour
    material.use_nodes = True
    shader = material.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value = colour
    shader.inputs['Roughness'].default_value = 0.85
    texture = bpy.data.images.new('Provisional_' + name, 8, 8)
    texture.generated_color = colour
    texture.pack()
    node = material.node_tree.nodes.new('ShaderNodeTexImage')
    node.image = texture
    material.node_tree.links.new(node.outputs['Color'], shader.inputs['Base Color'])
    materials[name] = material

parts = [o for o in bpy.data.objects if o.type == 'MESH']
for obj in parts:
    part = int(obj.name[1:])
    assert part in labels, obj.name
    kind = ('skin' if part in [1, 3, 21, 23] else 'green' if part in [4, 11, 12, 19] else
            'leather' if part in [5, 6] else 'steel' if part == 7 else 'gold' if part in [17, 18] else
            'black' if part in [13, 14, 24] else 'cloth')
    obj.data.materials.clear()
    obj.data.materials.append(materials[kind])
    obj.data.attributes.new('piece', 'INT', 'POINT').data.foreach_set('value', [part] * len(obj.data.vertices))
    for face in obj.data.polygons:
        face.use_smooth = True
    if not obj.data.uv_layers:
        uv = obj.data.uv_layers.new(name='ProvisionalUV')
        for face in obj.data.polygons:
            for loop in face.loop_indices:
                v = obj.data.vertices[obj.data.loops[loop].vertex_index].co
                uv.data[loop].uv = (v.x / 2 + 0.5, v.z / 1.7)
for obj in bpy.data.objects:
    obj.select_set(obj in parts)
bpy.context.view_layer.objects.active = bpy.data.objects['P00']
bpy.ops.object.join()
body = bpy.context.object
body.name = body.data.name = 'Body'
body.data.validate(verbose=True)
assert not body.data.validate()
coordinates = [x for vertex in body.data.vertices for x in vertex.co]
body.data.attributes.new('orig_co', 'FLOAT_VECTOR', 'POINT').data.foreach_set('vector', coordinates)
(project / 'work/parts_labels.json').write_text(json.dumps(labels, indent=2))
assert len(body.data.vertices) > 5000
assert not body.modifiers
bpy.ops.wm.save_as_mainfile(filepath=str(project / 'work/step1.blend'))
bpy.ops.export_scene.gltf(filepath=str(project / 'work/body_for_rig_clean.glb'), use_selection=True,
                          export_format='GLB', export_animations=False, export_skins=False, export_attributes=False)
common.workbench_clay(bpy.context.scene)
common.render_views(str(project / 'review/clean_v1'), 0.86, 1.9,
                    views=('front', 'left', 'back', 'three_quarter'), resolution=(600, 900))
common.render_views(str(project / 'review/clean_head'), 1.55, 0.37,
                    views=('front', 'left', 'three_quarter'), resolution=(500, 500))
common.render_views(str(project / 'review/clean_hand'), 0.88, 0.30,
                    views=('front', 'back'), resolution=(500, 500), target=(-0.47, -0.04))
print('CLEAN', len(body.data.vertices), 'vertices', len(body.data.polygons), 'faces')
