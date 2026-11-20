"""Clay render of the Parts/Body object. Args: <blend> <object> <out prefix> <cx,cy,cz,scale> [views comma]"""
import bpy, sys
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
BL, OB, PNG = a[:3]; cx, cy, cz, s = [float(x) for x in a[3].split(',')]
views = a[4].split(',') if len(a) > 4 else ['front', 'back', 'right', 'q']
bpy.ops.wm.open_mainfile(filepath=BL)
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'
sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'MATERIAL'; sc.display.shading.show_backface_culling = False
sc.display.shading.show_cavity = True
sc.render.resolution_x = sc.render.resolution_y = 900
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.clip_end = 100; cd.ortho_scale = s
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
c = Vector((cx, cy, cz))
V = dict(front=(0, -1, 0), back=(0, 1, 0), right=(-1, 0, 0), left=(1, 0, 0), q=(-1, -1.25, .4), qb=(1, 1, .3))
for v in views:
    cam.location = c + Vector(V[v]).normalized() * 6
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{PNG}_{v}.png'; bpy.ops.render.render(write_still=True)
