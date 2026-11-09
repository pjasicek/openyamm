"""Solid (studio-lit) orthographic renders of the 'Body' of a blend or the meshes of a GLB. The body faces -Y.
Args: <blend|glb> <out prefix> <size> <ortho> <cx,cy,cz> <views: front,back,left,right,top,q34,below,...>"""
import bpy, sys
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
src, out, size, ortho, cen, views = a[0], a[1], int(a[2]), float(a[3]), a[4], a[5].split(',')
if src.endswith('.blend'):
    bpy.ops.wm.open_mainfile(filepath=src)
else:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=src)
sc = bpy.context.scene
for o in sc.objects:
    if o.type == 'MESH' and o.name not in ('Body',) and src.endswith('.blend'):
        o.hide_render = True
c = Vector([float(x) for x in cen.split(',')])
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading
sh.light = 'STUDIO'; sh.color_type = 'SINGLE'; sh.single_color = (0.75, 0.72, 0.68); sh.show_backface_culling = True
sh.show_cavity = False
sc.render.resolution_x = sc.render.resolution_y = size
cd = bpy.data.cameras.new('cam'); cd.type = 'ORTHO'; cd.ortho_scale = ortho; cd.clip_end = 100
cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam
D = {'front': (0, -1, 0.0), 'back': (0, 1, 0), 'left': (1, 0, 0), 'right': (-1, 0, 0), 'top': (0, 0.0001, 1),
     'q34': (-1, -1.25, 0.4), 'q34l': (1, -1.25, 0.4), 'below': (0, -0.3, -1), 'party': (0, -1, 0.4)}
for v in views:
    d = Vector(D[v]).normalized()
    cam.location = c + d * 10
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{out}_{v}.png'
    bpy.ops.render.render(write_still=True)
print('RENDERED', out)
