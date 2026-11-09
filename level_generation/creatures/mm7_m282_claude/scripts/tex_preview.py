"""Textured preview renders of the master (rest pose or an action frame): body faces get <body png>, head faces (face
attribute head) <head png>; props keep their own materials. Workbench (flat studio light, texture colour), several
views tiled into <out png>.
Args: <blend> <body png> <head png> <out png> [views] [action] [frame] [target x,y,z] [ortho scale]"""
import bpy, sys, os
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
blend, bodyp, headp, out = a[:4]
views = (a[4] if len(a) > 4 else 'front,tq,side,back').split(',')
action = a[5] if len(a) > 5 and a[5] != '-' else None
frame = float(a[6]) if len(a) > 6 else 0
tgt = Vector([float(x) for x in a[7].split(',')]) if len(a) > 7 else Vector((0, 0.1, 0.95))
oscale = float(a[8]) if len(a) > 8 else 2.6
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
sc = bpy.context.scene; body = bpy.data.objects['Body']; me = body.data; rig = bpy.data.objects['Rig']
rig.animation_data_create()
if action:
    act = bpy.data.actions[action]; rig.animation_data.action = act
    if len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    sc.frame_set(int(frame))
else:
    rig.animation_data.action = None
    for pb in rig.pose.bones:
        pb.matrix_basis.identity()
hd = np.zeros(len(me.polygons), np.int32); me.attributes['head'].data.foreach_get('value', hd)
me.materials.clear()
for name, path in (('B', bodyp), ('H', headp)):
    m = bpy.data.materials.new(name); m.use_nodes = True
    bsdf = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    t = m.node_tree.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(os.path.abspath(path))
    m.node_tree.links.new(t.outputs['Color'], bsdf.inputs['Base Color']); me.materials.append(m)
me.polygons.foreach_set('material_index', hd)
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'TEXTURE'
R = int(os.environ.get('RES', '600')); sc.render.resolution_x = sc.render.resolution_y = R
if sc.world is None:
    sc.world = bpy.data.worlds.new('w')
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = oscale
D = {'front': (0, -1, 0.05), 'side': (1, 0, 0.05), 'rside': (-1, 0, 0.05), 'back': (0, 1, 0.05),
     'tq': (0.7, -0.7, 0.3), 'tqr': (-0.7, -0.7, 0.3), 'top': (0, -0.01, 1)}
tiles = []
for v in views:
    d = Vector(D[v]).normalized(); cam.location = tgt + d * 6; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    p = out + f'.{v}.png'; sc.render.filepath = p; bpy.ops.render.render(write_still=True); tiles.append(p)
imgs = [bpy.data.images.load(p) for p in tiles]
big = np.zeros((R, R * len(imgs), 4), np.float32)
for k, i in enumerate(imgs):
    big[:, k * R:(k + 1) * R] = np.array(i.pixels[:], np.float32).reshape(R, R, 4)
o = bpy.data.images.new('o', R * len(imgs), R); o.pixels = big.ravel(); o.filepath_raw = out; o.file_format = 'PNG'; o.save()
for p in tiles:
    os.remove(p)
print('PREVIEW', out)
