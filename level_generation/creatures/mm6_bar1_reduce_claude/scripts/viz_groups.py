"""Clay renders of the source body (work/source.blend, rest pose) coloured by the selections of face_groups.py:
green face kept, red hair, blue gloves, yellow small pieces kept, grey rest. -> review/groups_<view>.png"""
import os, math, bpy, numpy as np
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
body = bpy.data.objects['Body']; me = body.data
face = np.load(f'{HERE}/work/face_keep.npy'); groups = np.load(f'{HERE}/work/groups.npy')
small = np.load(f'{HERE}/work/small_keep.npy')
d = np.load(f'{HERE}/work/mesh_in.npz')
assert len(me.polygons) == len(face), (len(me.polygons), len(face))
col = np.tile([.6, .6, .6, 1.], (len(face), 1))
col[groups == 1] = [.8, .1, .1, 1]; col[groups == 2] = [.15, .3, .9, 1]; col[small] = [.95, .85, .1, 1]; col[face] = [.1, .8, .2, 1]
attr = me.color_attributes.new('Sel', 'FLOAT_COLOR', 'CORNER')
for p in me.polygons:
    for li in p.loop_indices: attr.data[li].color = col[p.index]
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'
sc.display.shading.color_type = 'VERTEX'; sc.display.shading.light = 'STUDIO'
me.color_attributes.active_color = attr
rig = bpy.data.objects['Rig']
if rig.animation_data: rig.animation_data.action = None
for pb in rig.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; sc.render.resolution_x = sc.render.resolution_y = 700
pts = [body.matrix_world @ v.co for v in body.data.vertices]
zmax = max(p.z for p in pts)
for name, (c, size, dv) in {'whole_front': (Vector((0, 0, zmax / 2)), 1.9, (0, -1, .1)),
                            'whole_back': (Vector((0, 0, zmax / 2)), 1.9, (0, 1, .1)),
                            'head_front': (Vector((0, 0, zmax - .15)), .45, (0, -1, .05)),
                            'head_side': (Vector((0, 0, zmax - .15)), .45, (1, 0, .05)),
                            'head_back': (Vector((0, 0, zmax - .15)), .45, (0, 1, .05))}.items():
    dv = Vector(dv).normalized(); cam.location = c + dv * 4
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler(); cam.data.ortho_scale = size
    sc.render.filepath = f'{HERE}/review/groups_{name}.png'; bpy.ops.render.render(write_still=True)
