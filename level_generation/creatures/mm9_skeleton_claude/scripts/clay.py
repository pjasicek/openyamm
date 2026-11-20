"""Clay close-ups of a blend's mesh object. Args: <blend> <object> <out prefix> <size> <ortho> <cx,cy,cz> [views: name=dx,dy,dz ...]; HIDEPARTS=a,b drops parts by int attribute `part`"""
import bpy, sys, os
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
o = bpy.data.objects[a[1]]
for x in bpy.data.objects:
    x.hide_render = x is not o and x.type == 'MESH'
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'
sc.display.shading.light = 'MATCAP' if os.environ.get('MATCAP') else 'STUDIO'
sc.display.shading.color_type = os.environ.get('COLOR', 'SINGLE'); sc.display.shading.single_color = (.75, .72, .65)
sc.display.shading.show_cavity = True
sc.display.shading.show_backface_culling = False
sc.render.resolution_x = sc.render.resolution_y = int(a[3])
w = bpy.data.worlds.new('w'); sc.world = w; w.color = (.1, .1, .12); sc.display.shading.background_type = 'WORLD'
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = float(a[4]); cd.clip_end = 100; cd.clip_start = float(os.environ.get('NEAR', 0.01))
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
c = Vector([float(x) for x in a[5].split(',')])
for v in a[6:]:
    n, d = v.split('='); d = Vector([float(x) for x in d.split(',')]).normalized()
    cam.location = c + d * float(os.environ.get('DIST', 5))
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{a[2]}_{n}.png'
    bpy.ops.render.render(write_still=True)
