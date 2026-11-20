"""Workbench views of a blend's meshes. Args: blend outdir prefix ortho cx,cy,cz [wire]"""
import bpy, sys, os
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
blend, out, pre, ortho = a[0], a[1], a[2], float(a[3])
c = Vector([float(x) for x in a[4].split(',')])
os.makedirs(out, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=blend)
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'OBJECT' if len(a) < 6 else 'SINGLE'; sh.show_backface_culling = True
sh.show_xray = False
if len(a) > 5:
    sh.show_object_outline = False
    for o in sc.objects:
        if o.type == 'MESH':
            m = o.modifiers.new('w', 'WIREFRAME'); m.thickness = 0.0015; m.use_replace = False; m.use_even_offset = False
sc.render.resolution_x = 900; sc.render.resolution_y = 900
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = ortho; cd.clip_end = 100
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
for n, d in {'front': (0, -1, .02), 'left': (1, 0, .02), 'back': (0, 1, .02), 'q34': (-1, -1.25, .35), 'below': (0, -.25, -1), 'top': (0, -.25, 1)}.items():
    d = Vector(d).normalized(); cam.location = c + d * 10
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(out, f'{pre}_{n}.png'); bpy.ops.render.render(write_still=True)
