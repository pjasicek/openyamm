"""Clay views of Body (q34, front, side, back) for diagnosis. Args: <blend> <out prefix> [cx,cy,cz] [ortho] [object]"""
import bpy, sys
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
name = a[4] if len(a) > 4 else 'Body'
for o in list(bpy.data.objects):
    if o.type == 'MESH' and o.name != name: bpy.data.objects.remove(o)
C = Vector([float(x) for x in a[2].split(',')]) if len(a) > 2 else Vector((0, 0, 0))
S = float(a[3]) if len(a) > 3 else 2.4
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'SINGLE'; sh.single_color = (.72, .72, .7); sh.show_cavity = True; sh.show_backface_culling = True
sc.render.resolution_x = sc.render.resolution_y = 800
sc.world = bpy.data.worlds.new('W'); sc.world.color = (0.2, 0.2, 0.22)
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = S
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
for v, d in {'q34': (-1, -1.2, 0.35), 'front': (0, -1, 0.05), 'side': (-1, 0, 0.05), 'back': (0.3, 1, 0.2)}.items():
    d = Vector(d).normalized(); cam.location = C + d * 10; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{a[1]}_{v}.png'; bpy.ops.render.render(write_still=True)
