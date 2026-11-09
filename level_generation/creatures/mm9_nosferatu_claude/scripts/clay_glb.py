"""Clay views of any GLB (static). Args: glb out_prefix size [ortho] ; CENTER=x,y,z env"""
import bpy, sys, os
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
glb, pre, size = a[0], a[1], int(a[2]); ortho = float(a[3]) if len(a) > 3 else 0
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
sc = bpy.context.scene
ms = [o for o in sc.objects if o.type == 'MESH']
pts = [o.matrix_world @ v.co for o in ms for v in o.data.vertices]
lo = [min(p[i] for p in pts) for i in range(3)]; hi = [max(p[i] for p in pts) for i in range(3)]
print('BOUNDS', lo, hi, 'V', len(pts), 'F', sum(len(o.data.polygons) for o in ms))
for o in ms:
    for s in o.data.polygons: s.use_smooth = False
c = Vector([(lo[i] + hi[i]) / 2 for i in range(3)])
if os.environ.get('CENTER'): c = Vector([float(x) for x in os.environ['CENTER'].split(',')])
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'SINGLE'; sh.single_color = (0.75, 0.72, 0.68); sh.show_cavity = True; sh.cavity_type = 'BOTH'; sh.show_backface_culling = bool(os.environ.get('CULL'))
sc.render.resolution_x = sc.render.resolution_y = size
w = bpy.data.worlds.new('w'); sc.world = w; w.color = (0.35, 0.38, 0.42); sc.display.shading.background_type = 'WORLD'
cd = bpy.data.cameras.new('cam'); cd.type = 'ORTHO'; cd.ortho_scale = ortho or max(hi[i] - lo[i] for i in range(3)) * 1.1; cd.clip_end = 100
cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam
Vs = {'q': (-1, -1.25, .3), 'f': (0, -1, 0.02), 'l': (1, 0, .02), 'b': (0, 1, .02), 'r': (-1, 0, .02), 'u': (0.3, -0.5, -1)}
for k, d in Vs.items():
    d = Vector(d).normalized(); cam.location = c + d * 10
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{pre}_{k}.png'; bpy.ops.render.render(write_still=True)
