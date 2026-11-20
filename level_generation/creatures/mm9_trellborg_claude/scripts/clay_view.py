"""Clay views of a glb or blend, montage out. Args: <in> <out png> [size] [views csv] ; env CENTER=x,y,z ORTHO=s OBJ=name"""
import bpy, sys, os, math
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
IN, OUT = a[0], a[1]; S = int(a[2]) if len(a) > 2 else 640
VIEWS = (a[3] if len(a) > 3 else 'front,q34,left,back').split(',')
if IN.endswith('.blend'): bpy.ops.wm.open_mainfile(filepath=IN)
else:
    bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=IN)
sc = bpy.context.scene
ms = [o for o in sc.objects if o.type == 'MESH' and (not os.environ.get('OBJ') or o.name == os.environ['OBJ'])]
for o in sc.objects:
    if o.type == 'MESH' and o not in ms: o.hide_render = True
dg = bpy.context.evaluated_depsgraph_get()
pts = [o.matrix_world @ Vector(b) for o in ms for b in o.bound_box]
lo = [min(p[i] for p in pts) for i in range(3)]; hi = [max(p[i] for p in pts) for i in range(3)]
c = Vector([(l + h) / 2 for l, h in zip(lo, hi)])
if os.environ.get('CENTER'): c = Vector([float(x) for x in os.environ['CENTER'].split(',')])
print('BOUNDS', lo, hi)
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'SINGLE'; sh.single_color = (0.75, 0.72, 0.68); sh.show_cavity = True; sh.show_backface_culling = False
sc.render.resolution_x = sc.render.resolution_y = S
w = bpy.data.worlds.new('w'); sc.world = w; w.color = (0.2, 0.2, 0.22); sh.background_type = 'WORLD'
cd = bpy.data.cameras.new('cam'); cd.type = 'ORTHO'; cd.ortho_scale = float(os.environ.get('ORTHO', max(h - l for l, h in zip(lo, hi)) * 1.08)); cd.clip_end = 100; cd.clip_start = 0.01
cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam
D = {'q34': (-1, -1.25, 0.3), 'q34l': (1, -1.25, 0.3), 'front': (0, -1, 0.05), 'left': (1, 0, 0.05), 'back': (0, 1, 0.05), 'right': (-1, 0, 0.05), 'top': (0, 0.001, 1), 'below': (0, -0.3, -1), 'backq': (-1, 1, 0.3)}
fs = []
for v in VIEWS:
    d = Vector(D[v]).normalized(); cam.location = c + d * 10
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    f = OUT[:-4] + '_' + v + '.png'; sc.render.filepath = f; bpy.ops.render.render(write_still=True); fs.append(f)
print('VIEWS', fs)
