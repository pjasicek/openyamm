"""Workbench views of the rest source (work/source.blend) with per-face labels as colours (work/groups*.npy int labels,
keep masks drawn white), to check the ladder masks before a run.
Usage: blender -b -P mask_view.py -- <groups.npy> <keep.npy> <out prefix>  -> review/masks/<prefix>_<view>.png"""
import os, sys, bpy, numpy as np
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
g_path, k_path, prefix = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'source.blend'))
sc = bpy.context.scene; o = bpy.data.objects['Body']; me = o.data
rig = bpy.data.objects['Rig']; rig.animation_data.action = None   # rest pose (hvm source.blend was saved on Dead)
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
g = np.load(os.path.join(HERE, g_path)); k = np.load(os.path.join(HERE, k_path))
PAL = [(.55, .5, .45), (.9, .3, .2), (.2, .7, .3), (.25, .4, .9), (.9, .8, .2), (.7, .3, .8), (.2, .8, .8), (.95, .55, .1), (.5, .2, .1)]
me.calc_loop_triangles()
assert len(me.loop_triangles) == len(g) == len(me.polygons), 'triangulated source expected'
col = me.color_attributes.new('lab', 'FLOAT_COLOR', 'CORNER')
for p in me.polygons:
    c = (1, 1, 1) if k[p.index] else PAL[int(g[p.index]) % len(PAL)]
    for li in p.loop_indices:
        col.data[li].color = (*c, 1)
for ob in bpy.data.objects:
    if ob.type == 'MESH' and ob is not o:
        ob.hide_render = True
sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'VERTEX'
sc.render.resolution_x = sc.render.resolution_y = 520
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'
# humanoid (faces -y, 1.70 m): MV_HAND = right hand centre x,y,z (rest)
HX, HY, HZ = (float(x) for x in os.environ.get('MV_HAND', '-0.5,0,0.8').split(','))
VIEWS = {'head_front': ((0, -.03, 1.55), .4, (0, -1, .1)), 'head_q34': ((0, -.03, 1.55), .4, (-.7, -.7, .2)),
         'head_side': ((0, 0, 1.55), .4, (-1, 0, .05)), 'head_back': ((0, 0, 1.55), .4, (0, 1, .2)),
         'body_front': ((0, 0, .85), 1.9, (0, -1, .1)), 'body_side': ((0, 0, .85), 1.9, (-1, 0, .05)),
         'body_back': ((0, 0, .85), 1.9, (0, 1, .2)), 'feet': ((0, -.05, .08), .7, (-.4, -.9, .4)),
         'hand_r': ((HX, HY, HZ), .4, (-.6, -.7, .2))}
os.makedirs(os.path.join(HERE, 'review', 'masks'), exist_ok=True)
MW = o.matrix_world   # spots are in mesh space (hvm: the mesh node is rotated in the GLB)
for name, (c, size, d) in VIEWS.items():
    c = MW @ Vector(c); d = MW.to_3x3().normalized() @ Vector(d); cam.location = c + d.normalized() * 5
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler(); cam.data.ortho_scale = size
    sc.render.filepath = os.path.join(HERE, 'review', 'masks', f'{prefix}_{name}.png'); bpy.ops.render.render(write_still=True)
print('MASKVIEW', prefix)
