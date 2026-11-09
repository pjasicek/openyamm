"""Clay views of 'Body' in a blend, with the MM9 mesh ghost optional. Args: <blend> <outdir> <prefix> [size]. VIEWS env as clay.py; MM9=<glb> overlays MM9 in red wire"""
import bpy, sys, os
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
blend, out, pre = argv[:3]; size = int(argv[3]) if len(argv) > 3 else 900
os.makedirs(out, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=blend)
sc = bpy.context.scene
body = bpy.data.objects['Body']
for o in list(bpy.data.objects):
    if o.type == 'MESH' and o is not body and o.name not in os.environ.get('KEEP', '').split(','): o.hide_render = True
for p in body.data.polygons: p.use_smooth = True
if os.environ.get('MM9'):
    ex = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.environ['MM9'])
    for o in set(bpy.data.objects) - ex:
        if o.type == 'MESH' and not o.name.startswith('Icosphere'):
            mat = bpy.data.materials.new('r'); mat.diffuse_color = (1, 0.2, 0.2, 1)
            o.data.materials.clear(); o.data.materials.append(mat)
        elif o.type == 'MESH': o.hide_render = True
    if not os.environ.get('NOBODY'):
        mat = bpy.data.materials.new('b'); mat.diffuse_color = (0.7, 0.7, 0.66, 0.35)
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'MATERIAL'; sh.show_cavity = True; sh.show_backface_culling = False
sh.show_xray = bool(os.environ.get('XRAY')); sh.xray_alpha = 0.55
sc.render.resolution_x = sc.render.resolution_y = size
w = bpy.data.worlds.new('w'); sc.world = w; w.color = (0.3, 0.3, 0.32); sh.background_type = 'WORLD'
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.clip_end = 100
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
c = Vector((0, 0, 0.14)); ext = 2.0
views = {'front': (c, (0, -1, 0.05), ext), 'back': (c, (0, 1, 0.05), ext), 'left': (c, (1, 0, 0.05), ext), 'q34': (c, (-1, -1.2, 0.4), ext)}
if os.environ.get('VIEWS'):
    views = {}
for s in os.environ.get('VIEWS', '').split(';'):
    if s:
        n, v = s.split('='); f = [float(x) for x in v.split(',')]
        views[n] = (Vector(f[:3]), f[3:6], f[6])
for n, (ce, d, e) in views.items():
    d = Vector(d).normalized(); cd.ortho_scale = e; cam.location = ce + d * 10
    cam.rotation_euler = (ce - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{out}/{pre}_{n}.png'; bpy.ops.render.render(write_still=True)
