"""Render only the listed parts, four views. Args: <blend> <out prefix> <comma ids> [cx,cy,cz,scale]"""
import bpy, bmesh, sys
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
BL, PNG, ids = a[0], a[1], set(int(x) for x in a[2].split(','))
cx, cy, cz, s = [float(x) for x in a[3].split(',')] if len(a) > 3 else (0, .02, .22, .42)
bpy.ops.wm.open_mainfile(filepath=BL)
o = bpy.data.objects['Meshy']; me = o.data
pa = next(x for x in me.attributes if x.data_type == 'INT' and x.name.startswith('part'))
p = np.zeros(len(me.vertices), int); pa.data.foreach_get('value', p)
bm = bmesh.new(); bm.from_mesh(me)
bmesh.ops.delete(bm, geom=[v for v in bm.verts if int(p[v.index]) not in ids], context='VERTS'); bm.to_mesh(me); bm.free()
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'
sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'VERTEX'; sc.display.shading.show_backface_culling = False
sc.render.resolution_x = sc.render.resolution_y = 800
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.clip_end = 100; cd.ortho_scale = s
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
c = Vector((cx, cy, cz))
for v, d in dict(front=(0, -1, 0), back=(0, 1, 0), right=(-1, 0, 0), q=(1, 1, .3)).items():
    cam.location = c + Vector(d).normalized() * 5
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{PNG}_{v}.png'; bpy.ops.render.render(write_still=True)
