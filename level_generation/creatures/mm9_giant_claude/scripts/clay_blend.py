"""Diagnosis clay renders of objects in a blend. Args: <blend> <out png> <objects comma> [ortho] [center x,y,z] [views comma: front,left,back,right,q34,below,top] [cut_y]"""
import bpy, sys, numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
names = a[2].split(',')
for o in list(bpy.data.objects):
    if o.type == 'MESH' and o.name not in names: bpy.data.objects.remove(o)
    elif o.type == 'MESH':
        for m in o.modifiers:
            if m.type != 'ARMATURE': m.show_render = False
obs = [o for o in bpy.data.objects if o.type == 'MESH']
dg = bpy.context.evaluated_depsgraph_get()
pts = np.concatenate([np.array([(o.matrix_world @ v.co)[:] for v in o.evaluated_get(dg).to_mesh().vertices]) for o in obs])
c = Vector(pts.min(0) / 2 + pts.max(0) / 2)
if len(a) > 4 and a[4]: c = Vector([float(x) for x in a[4].split(',')])
ortho = float(a[3]) if len(a) > 3 and a[3] else float(np.ptp(pts, 0).max()) * 1.1
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'SINGLE'
sh.single_color = (.78, .76, .72); sh.show_cavity = True; sh.show_backface_culling = True
sc.render.resolution_x = sc.render.resolution_y = 700
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = ortho; cd.clip_end = 100
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
D = {'front': (0, -1, 0), 'left': (1, 0, 0), 'back': (0, 1, 0), 'right': (-1, 0, 0), 'q34': (-1, -1.2, 0.3), 'below': (0, -0.3, -1), 'top': (0, -0.0001, 1), 'q34l': (1, -1.2, 0.3)}
views = a[5].split(',') if len(a) > 5 and a[5] else ['front', 'left', 'back', 'q34']
tiles = []
for v in views:
    d = Vector(D[v]).normalized(); cam.location = c + d * 10; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    f = a[1].replace('.png', f'_{v}.png'); sc.render.filepath = f; bpy.ops.render.render(write_still=True); tiles.append(f)
print('TILES', ','.join(tiles))
