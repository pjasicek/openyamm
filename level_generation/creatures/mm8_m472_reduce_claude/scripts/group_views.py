"""Rest-pose renders of the source coloured by work/groups.npy (red face, white hair, blue hands, black lining,
green cords, yellow kept) -> review/groups_<view>.png. Usage: blender -b -P group_views.py"""
import os, math, bpy, numpy as np
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'source.blend'))
o = bpy.data.objects['Body']; me = o.data; rig = bpy.data.objects['Rig']; rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
g = np.load(os.path.join(HERE, 'work/groups.npy')); keep = np.load(os.path.join(HERE, 'work/keep_base.npy'))
cols = [(.5, .5, .5), (.9, .2, .2), (.95, .95, .95), (.2, .4, .95), (.05, .05, .05), (.2, .8, .2), (.95, .85, .1)]
me.materials.clear()
for k, col in enumerate(cols):
    m = bpy.data.materials.new(f'G{k}'); m.diffuse_color = (*col, 1); me.materials.append(m)
me.calc_loop_triangles()
tri_poly = np.array([t.polygon_index for t in me.loop_triangles])
for ti, p in enumerate(tri_poly):
    me.polygons[p].material_index = 6 if keep[ti] else int(g[ti])
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.color_type = 'MATERIAL'
sc.render.resolution_x = sc.render.resolution_y = 500
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'
for name, ctr, size, d in (('head_front', (0, 0, 1.55), .4, (0, -1, .1)), ('head_side', (0, 0, 1.55), .4, (1, 0, .1)),
                           ('body_front', (0, 0, .9), 1.9, (0, -1, .1)), ('body_back', (0, 0, .9), 1.9, (0, 1, .1))):
    c = Vector(ctr); cam.location = c + Vector(d).normalized() * 3; cam.data.ortho_scale = size
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(HERE, 'review', f'groups_{name}.png'); bpy.ops.render.render(write_still=True)
