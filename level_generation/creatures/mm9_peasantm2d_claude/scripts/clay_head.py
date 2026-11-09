"""Clay head views of a master blend at rest: face shell skin, hair straw, ears red (attribute part 22), studio light.
Args: <blend> <out prefix> [size] [ortho] [cx,cy,cz] [views]   views: comma list of front,left,q34,right,back,below,q34b"""
import bpy, sys, numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
IN, PRE = a[0], a[1]; size = int(a[2]) if len(a) > 2 else 512; ortho = float(a[3]) if len(a) > 3 else 0.42
c = Vector([float(x) for x in (a[4] if len(a) > 4 else '0,0.03,0.78').split(',')])
views = (a[5] if len(a) > 5 else 'front,left,q34,right,back').split(',')
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; rig = body.parent; me = body.data
if rig.animation_data: rig.animation_data.action = None
for b in rig.pose.bones: b.matrix_basis.identity()
for o in bpy.data.objects:
    if o.type == 'MESH' and o is not body: o.hide_render = True
part = np.zeros(len(me.polygons), np.int32); me.attributes['part'].data.foreach_get('value', part)
import os
cols = {20: (0.85, 0.62, 0.5, 1), 21: (0.8, 0.7, 0.35, 1), 22: (0.85, 0.2, 0.15, 1)}
if os.environ.get('GREY'): cols = {22: (0.85, 0.2, 0.15, 1)}
me.materials.clear()
for k in (0, 20, 21, 22):
    m = bpy.data.materials.new(f'c{k}'); m.diffuse_color = cols.get(k, (0.5, 0.5, 0.55, 1)); me.materials.append(m)
idx = {0: 0, 20: 1, 21: 2, 22: 3}
me.polygons.foreach_set('material_index', [idx.get(int(p), 0) for p in part])
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'MATERIAL'; sh.show_backface_culling = True
sc.render.resolution_x = sc.render.resolution_y = size
w = bpy.data.worlds.new('w'); sc.world = w; w.color = (0.3, 0.3, 0.32)
cd = bpy.data.cameras.new('cam'); cd.type = 'ORTHO'; cd.ortho_scale = ortho; cd.clip_end = 100
cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam
D = {'front': (0, -1, 0.05), 'left': (1, 0, 0.05), 'q34': (-1, -1.25, 0.3), 'right': (-1, 0, 0.05), 'back': (0, 1, 0.05),
     'below': (0.3, -0.6, -1), 'q34b': (1, 1.2, 0.2), 'top': (0, 0.0001, 1)}
for v in views:
    d = Vector(D[v]).normalized(); cam.location = c + d * 5
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{PRE}_{v}.png'; bpy.ops.render.render(write_still=True)
print('CLAY', PRE)
