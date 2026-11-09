"""Clay renders (workbench, matcap-free studio light, grey) of a GLB or a blend's 'Body' at bind: views front, q34, left, back, right.
Args: <glb|blend> <out png prefix> [ortho] [center x,y,z]. Prints components and bounds."""
import bpy, sys, os, bmesh
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
src, out = a[0], a[1]; ortho = float(a[2]) if len(a) > 2 else 3.0
if src.endswith('.blend'):
    bpy.ops.wm.open_mainfile(filepath=src)
    for o in bpy.data.objects:
        if o.type == 'ARMATURE':
            if o.animation_data: o.animation_data.action = None
            for pb in o.pose.bones: pb.matrix_basis.identity()
else:
    bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=src)
sc = bpy.context.scene; bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get(); pts = []
for o in sc.objects:
    if o.type == 'MESH' and not o.hide_render:
        me = o.evaluated_get(dg).to_mesh(); pts += [tuple(o.matrix_world @ v.co) for v in me.vertices]
        bm = bmesh.new(); bm.from_mesh(me)
        import collections
        print('OBJ', o.name, len(me.vertices), 'tris', sum(len(p.vertices) - 2 for p in me.polygons))
        bm.free(); o.evaluated_get(dg).to_mesh_clear()
P = np.array(pts); print('BOUNDS', P.min(0).round(3), P.max(0).round(3))
c = Vector(((P.min(0) + P.max(0)) / 2).tolist()) if len(a) < 4 else Vector([float(x) for x in a[3].split(',')])
import os
PAL = [(0.7, 0.7, 0.7), (0.3, 0.5, 0.9), (0.9, 0.8, 0.2), (0.6, 0.3, 0.8), (0.3, 0.8, 0.3), (0.9, 0.4, 0.2), (0.5, 0.9, 0.9), (0.9, 0.5, 0.7)]
if os.environ.get('PARTCOL'):
    for o in sc.objects:
        if o.type != 'MESH' or 'part' not in o.data.attributes: continue
        me = o.data; pa = [0] * len(me.vertices); me.attributes['part'].data.foreach_get('value', pa)
        ca = me.color_attributes.new('pc', 'FLOAT_COLOR', 'POINT')
        CM = {0: (0.7, 0.7, 0.7), 1: (0.3, 0.5, 0.9), 2: (0.9, 0.8, 0.2), 4: (0.3, 0.8, 0.3), 5: (0.9, 0.4, 0.2), 10: (0.9, 0.55, 0.7), 12: (1, 1, 1), 13: (1, 0.2, 0.1), 14: (0.6, 0.1, 0.5)}
        for i, p in enumerate(pa): ca.data[i].color = (*CM.get(p, (0.2, 0.9, 0.9)), 1)
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'VERTEX' if os.environ.get('PARTCOL') else 'SINGLE'; sh.single_color = (0.7, 0.7, 0.7); sh.show_backface_culling = False
sh.show_cavity = True
sc.render.resolution_x = sc.render.resolution_y = 768
w = bpy.data.worlds.new('w'); sc.world = w; w.color = (0.25, 0.3, 0.35); sh.background_type = 'WORLD'
cd = bpy.data.cameras.new('cam'); cd.type = 'ORTHO'; cd.ortho_scale = ortho; cd.clip_end = 100
cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam
dirs = {'front': (0, -1, 0.05), 'q34': (-1.0, -1.25, 0.55), 'left': (1, 0, 0.05), 'back': (0, 1, 0.05), 'right': (-1, 0, 0.05)}
for v, d in dirs.items():
    d = Vector(d).normalized(); cam.location = c + d * 10
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{out}_{v}.png'; bpy.ops.render.render(write_still=True)
